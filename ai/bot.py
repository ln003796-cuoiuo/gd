import json
from typing import List, Optional
from level_parser import parse_objects
from physics_sim import GDSimulator, Action, simulate_macro
from pathfinder import Pathfinder, check_solvability, SearchResult


class AIBot:
    """Главный класс бота. Управляет циклом: анализ → поиск → мутация."""
    
    def __init__(self):
        self.objects: List = []
        self.current_macro: List[Action] = []
        self.attempts = 0
        self.max_attempts = 50
    
    def load_level(self, level_string: str):
        """Шаг 1: ИИ анализирует уровень."""
        print("[AI] Парсинг уровня...")
        self.objects = parse_objects(level_string)
        print(f"[AI] Загружено {len(self.objects)} объектов")
        
        # Шаг 4: проверка на безвыходные места
        ok, msg = check_solvability(self.objects)
        if not ok:
            print(f"[AI] ⚠ УРОВЕНЬ НЕПРОХОДИМ: {msg}")
            return False
        print(f"[AI] ✓ {msg}")
        return True
    
    def generate_macro(self) -> Optional[List[Action]]:
        """Шаг 2: ИИ делает предположительный макрос."""
        print("[AI] Запуск A* поиска...")
        pf = Pathfinder(self.objects)
        result = pf.find()
        
        if result.success:
            print(f"[AI] ✓ Макрос найден! Длина: {result.frames} кадров")
            self.current_macro = result.macro
            return result.macro
        else:
            print(f"[AI] ✗ A* не справился: {result.reason}")
            return None
    
    def on_death(self, death_frame: int, death_x: float, death_y: float):
        """
        Шаг 3: Когда умирает — делает изменения в макросе.
        Пока что — заглушка. На следующем шаге добавим мутации.
        """
        self.attempts += 1
        print(f"[AI] Смерть #{self.attempts} на кадре {death_frame} (x={death_x:.0f})")
        
        if self.attempts >= self.max_attempts:
            print(f"[AI] Превышен лимит попыток ({self.max_attempts}). Сдаюсь.")
            return None
        
        # TODO: здесь будет мутация макроса вокруг точки смерти
        return self.current_macro
    
    def verify_macro_in_sim(self) -> bool:
        """Проверяет макрос в симуляторе перед отправкой в игру."""
        if not self.current_macro:
            return False
        state, death_frame = simulate_macro(self.objects, self.current_macro)
        if death_frame == -1:
            print("[AI] ✓ Симуляция прошла макрос без смертей")
            return True
        else:
            print(f"[AI] ✗ Симуляция умерла на кадре {death_frame}")
            return False
    
    def export_macro_json(self) -> str:
        """Экспортирует макрос в формат, понятный Geode моду."""
        actions = []
        for i, a in enumerate(self.current_macro):
            if a.click:
                actions.append({"frame": i, "action": "click"})
        return json.dumps({"macro": actions, "frames": len(self.current_macro)}, indent=2)


if __name__ == "__main__":
    # Демонстрация работы
    bot = AIBot()
    
    # Тестовый уровень
    from level_parser import GameObject
    bot.objects = [
        GameObject(id=1, x=0, y=105, is_solid=True),
        GameObject(id=8, x=400, y=120, is_hazard=True),
        GameObject(id=8, x=700, y=120, is_hazard=True),
        GameObject(id=8, x=1000, y=120, is_hazard=True),
    ]
    
    macro = bot.generate_macro()
    if macro:
        bot.verify_macro_in_sim()
        print("\nЭкспорт в JSON:")
        print(bot.export_macro_json()[:200] + "...")