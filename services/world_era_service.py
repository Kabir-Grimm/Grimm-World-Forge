import json
import os
from datetime import datetime

from services.world_time_service import load_world_time


WORLD_ERAS_PATH = "entities/world_eras.json"


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return fallback

    return data


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_eras():
    data = load_json(WORLD_ERAS_PATH, [])

    if not isinstance(data, list):
        return []

    return data


def save_eras(eras):
    save_json(WORLD_ERAS_PATH, eras)


def get_current_era():
    eras = load_eras()

    if not eras:
        return {
            "id": "era_1",
            "name": "Primera Era",
            "started_at": {
                "turn": 0,
                "day": 1,
                "month": 1,
                "year": 1
            },
            "created_at": datetime.now().isoformat()
        }

    eras.sort(
        key=lambda era: era.get("started_at", {}).get("turn", 0),
        reverse=True
    )

    return eras[0]


def create_new_era(name):
    world_time = load_world_time()
    eras = load_eras()

    era = {
        "id": f"era_{len(eras) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name": name.strip() or f"Era {len(eras) + 1}",
        "started_at": {
            "turn": world_time.get("turn", 0),
            "day": world_time.get("day", 1),
            "month": world_time.get("month", 1),
            "year": world_time.get("year", 1)
        },
        "created_at": datetime.now().isoformat()
    }

    eras.append(era)
    save_eras(eras)

    return era