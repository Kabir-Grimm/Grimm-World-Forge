APP_NAME = "Grimm Worlds Forge"
SECRET_KEY = "GWF_SECRET_2026"

LOG_FILE = "data/logs/important_rolls.log"
SESSION_FILE = "data/logs/session.json"

import json
import os

CONFIG_PATH = "config.json"

CONFIG = {
    "server_url": "http://127.0.0.1:5000/roll",
    "user": "Kabir",
    "api_key": "CHANGE_ME",
    "secret_key": "GWF_SECRET_KEY"
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(CONFIG)
        return CONFIG

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)