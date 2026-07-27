import heapq
from typing import List, Tuple, Dict
from dataclasses import dataclass
from level_parser import GameObject
from physics_sim import GDSimulator, PlayerState, Action, PLAYER_SPEED


@dataclass(frozen=True)
class SearchNode:
    x: int
    y: int
    vy: int
    on_ground: bool
    gravity_dir: int
    
    @classmethod
    def from_state(cls, s: PlayerState) -> 'SearchNode':
        return cls(
            x=int(s.x),
            y=int(s.y),
            vy=int(s.vy * 10),
            on_ground=s.on_ground,
            gravity_dir=s.gravity_dir,
        )


@dataclass
class SearchResult:
    macro: List[Action]
    frames: int
    success: bool
    stuck_at_x: float = 0.0
    reason: str = ""


class Pathfinder:
    """A* поиск макроса через уровень."""
    
    def __init__(self, objects: List[GameObject], max_frames: int = 10000):
        self.objects = objects
        self.max_frames = max_frames
        self.finish_x = max((o.x for o in objects), default=0) + 300
    
    def find(self) -> SearchResult:
        sim = GDSimulator(self.objects)
        start_state = sim.reset()
        start_node = SearchNode.from_state(start_state)
        
        counter = 0
        open_set: List[Tuple[float, int, PlayerState, List[Action]]] = []
        g_score: Dict[SearchNode, int] = {start_node: 0}
        
        def h(state: PlayerState) -> float:
            dist = self.finish_x - state.x
            return dist / PLAYER_SPEED
        
        start_f = h(start_state)
        heapq.heappush(open_set, (start_f, counter, start_state, []))
        counter += 1
        
        max_nodes = 500_000
        nodes_explored = 0
        best_x_reached = 0.0
        
        while open_set and nodes_explored < max_nodes:
            f, _, state, path = heapq.heappop(open_set)
            nodes_explored += 1
            
            if state.x > best_x_reached:
                best_x_reached = state.x
            
            if state.x >= self.finish_x:
                return SearchResult(
                    macro=path,
                    frames=len(path),
                    success=True,
                    reason="Финиш достигнут!"
                )
            
            if len(path) >= self.max_frames:
                continue
            
            for click in (True, False):
                action = Action(click=click)
                new_state = sim.step(state, action)
                
                if sim.is_dead(new_state):
                    continue
                
                new_node = SearchNode.from_state(new_state)
                new_g = len(path) + 1
                
                if new_node in g_score and g_score[new_node] <= new_g:
                    continue
                
                g_score[new_node] = new_g
                new_f = new_g + h(new_state)
                new_path = path + [action]
                
                heapq.heappush(open_set, (new_f, counter, new_state, new_path))
                counter += 1
        
        return SearchResult(
            macro=[],
            frames=0,
            success=False,
            stuck_at_x=best_x_reached,
            reason=f"Застряли на X={best_x_reached:.0f}. Рассмотрено {nodes_explored} состояний."
        )


def check_solvability(objects: List[GameObject]) -> Tuple[bool, str]:
    """Проверка на безвыходные места."""
    hazards = sorted([o for o in objects if o.is_hazard], key=lambda o: o.x)
    
    for i in range(len(hazards) - 1):
        h1, h2 = hazards[i], hazards[i + 1]
        gap = h2.x - h1.x
        
        if gap < 20 and abs(h1.y - h2.y) < 15:
            return False, f"Безвыходное место на X={h1.x:.0f}: шипы в {gap:.0f}px"
    
    return True, "Явных тупиков не найдено"