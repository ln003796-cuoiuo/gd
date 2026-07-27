from dataclasses import dataclass, field
from typing import List, Tuple
from level_parser import GameObject


# Константы физики GD 2.2 (куб, скорость x1)
GRAVITY = 0.889
JUMP_VELOCITY = 11.18
PLAYER_SPEED = 0.396 * 60  # пикселей за кадр при 60fps
PLAYER_SIZE = 30.0
HALF_SIZE = PLAYER_SIZE / 2
GROUND_Y = 105.0


@dataclass
class PlayerState:
    x: float = 0.0
    y: float = GROUND_Y + HALF_SIZE
    vy: float = 0.0
    on_ground: bool = True
    gamemode: int = 0
    gravity_dir: int = 1
    is_holding: bool = False
    frame: int = 0
    dead: bool = False
    
    def copy(self) -> 'PlayerState':
        return PlayerState(
            self.x, self.y, self.vy, self.on_ground,
            self.gamemode, self.gravity_dir, self.is_holding,
            self.frame, self.dead
        )


@dataclass
class Action:
    click: bool = False
    release: bool = False


class GDSimulator:
    """Симулирует физику GD кадр за кадром."""
    
    def __init__(self, objects: List[GameObject]):
        self.objects = sorted(objects, key=lambda o: o.x)
        self._obj_idx = 0
    
    def reset(self) -> PlayerState:
        self._obj_idx = 0
        return PlayerState()
    
    def step(self, state: PlayerState, action: Action) -> PlayerState:
        """Один кадр симуляции."""
        s = state.copy()
        s.frame += 1
        
        # Горизонтальное движение
        s.x += PLAYER_SPEED
        
        # Ввод (только куб)
        if s.gamemode == 0:
            if action.click and s.on_ground:
                s.vy = JUMP_VELOCITY * s.gravity_dir
                s.on_ground = False
        
        # Гравитация
        if not s.on_ground:
            s.vy -= GRAVITY * s.gravity_dir
            s.y += s.vy
        
        # Коллизия с землёй
        if s.gravity_dir == 1 and s.y <= GROUND_Y + HALF_SIZE:
            s.y = GROUND_Y + HALF_SIZE
            s.vy = 0
            s.on_ground = True
        elif s.gravity_dir == -1:
            ceiling = GROUND_Y + 300 - HALF_SIZE
            if s.y >= ceiling:
                s.y = ceiling
                s.vy = 0
                s.on_ground = True
        
        # Коллизии с объектами
        self._check_collisions(s)
        
        return s
    
    def _check_collisions(self, s: PlayerState):
        px1, py1 = s.x - HALF_SIZE, s.y - HALF_SIZE
        px2, py2 = s.x + HALF_SIZE, s.y + HALF_SIZE
        
        for obj in self.objects[self._obj_idx:]:
            if obj.x < s.x - 100:
                self._obj_idx += 1
                continue
            if obj.x > s.x + 200:
                break
            
            ox1, oy1 = obj.x - HALF_SIZE, obj.y - HALF_SIZE
            ox2, oy2 = obj.x + HALF_SIZE, obj.y + HALF_SIZE
            
            if px2 < ox1 or px1 > ox2 or py2 < oy1 or py1 > oy2:
                continue
            
            if obj.is_hazard:
                s.dead = True
                return
            elif obj.is_solid:
                if s.vy <= 0 and py1 < oy2 and py1 > oy2 - 10:
                    s.y = oy2 + HALF_SIZE
                    s.vy = 0
                    s.on_ground = True
            elif obj.is_portal and obj.gamemode >= 0:
                s.gamemode = obj.gamemode
    
    def is_dead(self, state: PlayerState) -> bool:
        return state.dead


def simulate_macro(objects: List[GameObject], macro: List[Action]) -> Tuple[PlayerState, int]:
    """Прогоняет макрос. Возвращает (состояние, кадр смерти или -1)."""
    sim = GDSimulator(objects)
    state = sim.reset()
    
    for frame_idx, action in enumerate(macro):
        state = sim.step(state, action)
        if sim.is_dead(state):
            return state, frame_idx
    
    return state, -1