import json
import os
from datetime import datetime

WORLDS_PATH = "entities/worlds.json"


def load_worlds():
    if not os.path.exists(WORLDS_PATH):
        return []

    with open(WORLDS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def save_world(world):
    os.makedirs("entities", exist_ok=True)

    worlds = load_worlds()

    world["id"] = f"world_{len(worlds) + 1}"
    world["created_at"] = datetime.now().isoformat()
    world.setdefault("entities", [])

    worlds.append(world)

    save_worlds(worlds)

    return world["id"]


def save_worlds(worlds):
    os.makedirs("entities", exist_ok=True)

    with open(WORLDS_PATH, "w", encoding="utf-8") as f:
        json.dump(worlds, f, indent=4, ensure_ascii=False)


def add_entity_to_world(world_id, entity):
    worlds = load_worlds()

    for world in worlds:
        if world.get("id") == world_id:
            world.setdefault("entities", [])

            exists = any(
                e.get("id") == entity.get("id")
                for e in world["entities"]
            )

            if not exists:
                world["entities"].append({
                    "id": entity.get("id"),
                    "name": entity.get("name"),
                    "type": entity.get("type")
                })

            save_worlds(worlds)
            return True

    return False