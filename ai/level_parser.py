import gzip
import base64
from dataclasses import dataclass
from typing import List


@dataclass
class GameObject:
    id: int
    x: float
    y: float
    rotation: float = 0.0
    scale: float = 1.0
    is_solid: bool = False
    is_hazard: bool = False
    is_portal: bool = False
    is_orb: bool = False
    gamemode: int = -1


# Упрощённые списки ID. В реальной GD 2.2 их сотни.
# Для старта используем основные.
HAZARD_IDS = {
    6, 7, 8, 9, 35, 39, 51, 52, 61, 62, 66,
    101, 130, 133, 142, 144, 189, 200,
    248, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260,
    365, 366, 396, 420, 421, 422, 423,
    456, 457, 458, 459, 460, 461, 462, 463, 464, 465,
    466, 467, 468, 469, 470, 471, 472, 473, 474, 475,
    476, 477, 478, 479, 480, 481, 482, 483, 484, 485,
}

PORTAL_IDS = {
    10, 11, 12, 13, 52, 53, 54, 55,
    133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143,
    286, 287, 288,
}

SOLID_IDS = {
    1, 2, 3, 4, 5, 32, 33, 34, 36, 37, 38,
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
    81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
    96, 97, 98, 99, 100,
}

ORB_IDS = {36, 84, 1017, 1018, 1019, 1020, 1021}

# Геймоды порталов
GAMEMODE_PORTALS = {12: 0, 13: 1, 54: 2, 55: 3, 53: 4, 52: 5, 133: 6}
GRAVITY_PORTALS = {10: 1, 11: -1}


def decode_level_string(raw: str) -> str:
    """Распаковывает level string из GD."""
    try:
        # GD использует свой Base64 алфавит (заменяет +/ на -/)
        raw = raw.replace("-", "+").replace("_", "/")
        decoded = base64.b64decode(raw + "==")
        return gzip.decompress(decoded).decode('utf-8', errors='ignore')
    except Exception:
        return raw


def parse_objects(level_string: str) -> List[GameObject]:
    """Парсит распакованную строку уровня в список объектов."""
    decoded = decode_level_string(level_string)
    objects = []
    
    for obj_str in decoded.split(';'):
        if not obj_str:
            continue
        parts = obj_str.split(',')
        if len(parts) < 5:
            continue
        
        data = {}
        for i in range(0, len(parts) - 1, 2):
            try:
                data[int(parts[i])] = parts[i + 1]
            except ValueError:
                continue
        
        obj_id = int(data.get(1, 0))
        x = float(data.get(2, 0))
        y = float(data.get(3, 0))
        rot = float(data.get(6, 0))
        scale = float(data.get(32, 1))
        
        obj = GameObject(
            id=obj_id, x=x, y=y,
            rotation=rot, scale=scale,
            is_solid=(obj_id in SOLID_IDS),
            is_hazard=(obj_id in HAZARD_IDS),
            is_portal=(obj_id in PORTAL_IDS),
            is_orb=(obj_id in ORB_IDS),
        )
        
        if obj_id in GAMEMODE_PORTALS:
            obj.gamemode = GAMEMODE_PORTALS[obj_id]
        
        objects.append(obj)
    
    return objects


if __name__ == "__main__":
    sample = input("Вставьте level string: ")
    objs = parse_objects(sample)
    print(f"Загружено объектов: {len(objs)}")
    hazards = [o for o in objs if o.is_hazard]
    print(f"Опасных объектов: {len(hazards)}")