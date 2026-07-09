import json
import os

GRAPH_POSITIONS_PATH = "entities/graph_positions.json"


def load_graph_positions():
    if not os.path.exists(GRAPH_POSITIONS_PATH):
        return {}

    with open(GRAPH_POSITIONS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_graph_positions(positions):
    os.makedirs("entities", exist_ok=True)

    with open(GRAPH_POSITIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            positions,
            f,
            indent=4,
            ensure_ascii=False
        )