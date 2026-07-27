import socket
import json
import threading
from bot import AIBot

HOST = '127.0.0.1'
PORT = 42069  # 🌿

bot = AIBot()


def handle_client(conn: socket.socket):
    """Обрабатывает команды от Geode мода."""
    print(f"[IPC] Подключился Geode мод")
    buffer = ""
    
    try:
        while True:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data
            
            # Сообщения разделены символом новой строки
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                
                try:
                    msg = json.loads(line)
                    response = process_message(msg)
                    conn.sendall((json.dumps(response) + '\n').encode('utf-8'))
                except json.JSONDecodeError:
                    print(f"[IPC] Битый JSON: {line[:50]}")
    except ConnectionResetError:
        pass
    finally:
        print("[IPC] Geode отключился")
        conn.close()


def process_message(msg: dict) -> dict:
    """Диспетчер команд."""
    cmd = msg.get("cmd")
    
    if cmd == "load_level":
        ok = bot.load_level(msg["level_string"])
        return {"status": "ok" if ok else "error", "msg": "Уровень загружен" if ok else "Уровень непроходим"}
    
    elif cmd == "generate_macro":
        macro = bot.generate_macro()
        if macro:
            bot.verify_macro_in_sim()
            return {"status": "ok", "macro_json": bot.export_macro_json()}
        return {"status": "error", "msg": "Не удалось найти путь"}
    
    elif cmd == "death":
        new_macro = bot.on_death(msg["frame"], msg["x"], msg["y"])
        if new_macro:
            return {"status": "ok", "macro_json": bot.export_macro_json()}
        return {"status": "give_up"}
    
    elif cmd == "ping":
        return {"status": "pong"}
    
    return {"status": "unknown_cmd"}


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[IPC] Сервер запущен на {HOST}:{PORT}")
    print("[IPC] Ожидание подключения Geode мода...")
    
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[IPC] Остановка...")
    finally:
        server.close()


if __name__ == "__main__":
    main()