import json
import os

FAV_PATH = "favorites.json"


def load_favorites():
    if not os.path.exists(FAV_PATH):
        return []

    with open(FAV_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_favorites(favorites):
    with open(FAV_PATH, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=4)