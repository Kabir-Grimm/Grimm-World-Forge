import json
import os
from datetime import datetime


WORLD_MAP_PATH = "entities/world_map.json"


def ensure_world_map_file():
    os.makedirs("entities", exist_ok=True)

    if not os.path.exists(WORLD_MAP_PATH):
        data = {
            "nodes": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        save_world_map(data)


def load_world_map():
    ensure_world_map_file()

    with open(WORLD_MAP_PATH, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            data = {}

    if not isinstance(data, dict):
        data = {}

    data.setdefault("nodes", [])
    data.setdefault("created_at", datetime.now().isoformat())
    data.setdefault("updated_at", datetime.now().isoformat())

    return data


def save_world_map(data):
    os.makedirs("entities", exist_ok=True)

    data["updated_at"] = datetime.now().isoformat()

    if not data.get("created_at"):
        data["created_at"] = datetime.now().isoformat()

    with open(WORLD_MAP_PATH, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_map_nodes():
    data = load_world_map()
    return data.get("nodes", [])


def save_map_nodes(nodes):
    data = load_world_map()
    data["nodes"] = nodes
    save_world_map(data)


def add_or_update_node(entity, x=100, y=100):
    data = load_world_map()
    nodes = data.get("nodes", [])

    entity_id = entity.get("id")

    if not entity_id:
        return None

    for node in nodes:
        if node.get("entity_id") == entity_id:
            node["name"] = entity.get("name", "Sin nombre")
            node["type"] = entity.get("type", "entity")
            node["x"] = x
            node["y"] = y
            save_world_map(data)
            return node

    node = {
        "entity_id": entity_id,
        "name": entity.get("name", "Sin nombre"),
        "type": entity.get("type", "entity"),
        "x": x,
        "y": y
    }

    nodes.append(node)
    data["nodes"] = nodes

    save_world_map(data)

    return node


def remove_node(entity_id):
    data = load_world_map()
    nodes = data.get("nodes", [])

    new_nodes = [
        node for node in nodes
        if node.get("entity_id") != entity_id
    ]

    data["nodes"] = new_nodes
    save_world_map(data)

    return len(new_nodes) != len(nodes)


def update_node_position(entity_id, x, y):
    data = load_world_map()
    nodes = data.get("nodes", [])

    for node in nodes:
        if node.get("entity_id") == entity_id:
            node["x"] = x
            node["y"] = y
            save_world_map(data)
            return True

    return False