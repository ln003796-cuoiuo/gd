import pymem
import pymem.process
import pyautogui
import time
import json
import socket
import threading
from ai.ipc_server import process_message

# Константы для Geometry Dash 2.2 (могут меняться с обновлениями)
# Эти адреса нужно найти для твоей версии GD
PLAYER_X_OFFSET = 0x320  # Примерный адрес X координаты
PLAYER_Y_OFFSET = 0x324  # Примерный адрес Y координаты
PLAYER_DEAD_OFFSET = 0x330  # Адрес статуса "мертв"

class GDMemoryReader:
    def __init__(self):
        self.pm = None
        self.base_address = None
        
    def connect(self):
        """Подключается к процессу Geometry Dash."""
        try:
            self.pm = pymem.Pymem("GeometryDash.exe")
            self.base_address = self.pm.base_address
            print("[Memory] Подключился к Geometry Dash")
            return True
        except pymem.exception.ProcessNotFound:
            print("[Memory] Geometry Dash не запущен!")
            return False
    
    def get_player_x(self) -> float:
        """Читает X координату игрока."""
        if not self.pm:
            return 0.0
        try:
            # Читаем указатель на объект игрока
            player_ptr = self.pm.read_int(self.base_address + 0x01B8C3A0)  # Примерный адрес
            if player_ptr:
                x = self.pm.read_float(player_ptr + PLAYER_X_OFFSET)
                return x
        except:
            pass
        return 0.0
    
    def get_player_y(self) -> float:
        """Читает Y координату игрока."""
        if not self.pm:
            return 0.0
        try:
            player_ptr = self.pm.read_int(self.base_address + 0x01B8C3A0)
            if player_ptr:
                y = self.pm.read_float(player_ptr + PLAYER_Y_OFFSET)
                return y
        except:
            pass
        return 0.0
    
    def is_dead(self) -> bool:
        """Проверяет, мертв ли игрок."""
        if not self.pm:
            return False
        try:
            player_ptr = self.pm.read_int(self.base_address + 0x01B8C3A0)
            if player_ptr:
                dead = self.pm.read_int(player_ptr + PLAYER_DEAD_OFFSET)
                return dead == 1
        except:
            pass
        return False
    
    def press_jump(self):
        """Нажимает пробел."""
        pyautogui.press('space')


class AIClient:
    def __init__(self):
        self.sock = None
        self.connected = False
        
    def connect_to_server(self):
        """Подключается к Python AI серверу."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('127.0.0.1', 42069))
            self.connected = True
            print("[AI Client] Подключился к AI серверу")
            return True
        except:
            print("[AI Client] Не удалось подключиться к AI серверу. Запусти ipc_server.py!")
            return False
    
    def send_level(self, level_data: str):
        """Отправляет уровень на анализ."""
        if not self.connected:
            return
        msg = json.dumps({"cmd": "load_level", "level_string": level_data}) + "\n"
        self.sock.send(msg.encode())
        response = self.sock.recv(4096).decode()
        print(f"[AI Client] AI ответ: {response[:100]}")
    
    def get_macro(self):
        """Запрашивает макрос от AI."""
        if not self.connected:
            return None
        msg = json.dumps({"cmd": "generate_macro"}) + "\n"
        self.sock.send(msg.encode())
        response = self.sock.recv(4096).decode()
        data = json.loads(response)
        if data.get("status") == "ok":
            return json.loads(data["macro_json"])
        return None
    
    def report_death(self, frame: int, x: float, y: float):
        """Сообщает о смерти."""
        if not self.connected:
            return
        msg = json.dumps({"cmd": "death", "frame": frame, "x": x, "y": y}) + "\n"
        self.sock.send(msg.encode())
        response = self.sock.recv(4096).decode()
        print(f"[AI Client] AI после смерти: {response[:100]}")


def main():
    print("=" * 50)
    print("GD AI Bot - Python Version")
    print("=" * 50)
    
    # Подключаемся к памяти GD
    memory = GDMemoryReader()
    if not memory.connect():
        print("Запусти Geometry Dash и попробуй снова!")
        return
    
    # Подключаемся к AI серверу
    ai = AIClient()
    if not ai.connect_to_server():
        print("Запусти ai/ipc_server.py в другом терминале!")
        return
    
    print("\n[Bot] Бот запущен! Нажми Ctrl+C для остановки.")
    print("[Bot] Зайди в уровень в GD и нажми F6 для старта бота.")
    
    frame = 0
    macro = None
    macro_index = 0
    running = False
    
    try:
        while True:
            # Проверяем, нажат ли F6 (через pyautogui)
            # Для простоты используем клавишу 'b' для старта/стопа
            if pyautogui.isPressed('b'):
                if not running:
                    running = True
                    print("[Bot] Бот включен!")
                    time.sleep(0.5)  # Анти-дребезг
                else:
                    running = False
                    print("[Bot] Бот выключен!")
                    time.sleep(0.5)
            
            if not running:
                time.sleep(0.1)
                continue
            
            # Читаем состояние игрока
            x = memory.get_player_x()
            y = memory.get_player_y()
            dead = memory.is_dead()
            
            if dead:
                print(f"[Bot] Смерть на кадре {frame} (x={x:.0f}, y={y:.0f})")
                ai.report_death(frame, x, y)
                time.sleep(1)  # Ждем рестарта
                frame = 0
                macro = None
                macro_index = 0
                continue
            
            # Если нет макроса, запрашиваем
            if macro is None:
                print("[Bot] Запрашиваю макрос от AI...")
                macro = ai.get_macro()
                if macro:
                    print(f"[Bot] Получен макрос на {len(macro)} кадров")
                else:
                    print("[Bot] AI не смог создать макрос")
                    time.sleep(1)
                    continue
            
            # Выполняем макрос
            if frame < len(macro):
                action = macro[frame]
                if action.get("action") == "click":
                    memory.press_jump()
            
            frame += 1
            time.sleep(1/240)  # ~240 FPS
            
    except KeyboardInterrupt:
        print("\n[Bot] Остановка...")
    finally:
        if ai.sock:
            ai.sock.close()


if __name__ == "__main__":
    main()