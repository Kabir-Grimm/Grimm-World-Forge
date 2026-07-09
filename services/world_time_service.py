import json
import os
from datetime import datetime


WORLD_TIME_PATH = "entities/world_time.json"


DEFAULT_WORLD_TIME = {
    "calendar_name": "Calendario del Mundo",
    "turn": 0,
    "day": 1,
    "month": 1,
    "year": 1,
    "days_per_month": 30,
    "months_per_year": 12,
    "created_at": "",
    "updated_at": ""
}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_world_time():
    if not os.path.exists(WORLD_TIME_PATH):
        data = dict(DEFAULT_WORLD_TIME)
        now = datetime.now().isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        save_json(WORLD_TIME_PATH, data)
        return data

    with open(WORLD_TIME_PATH, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            data = dict(DEFAULT_WORLD_TIME)

    for key, value in DEFAULT_WORLD_TIME.items():
        data.setdefault(key, value)

    return data


def save_world_time(data):
    data["updated_at"] = datetime.now().isoformat()

    if not data.get("created_at"):
        data["created_at"] = datetime.now().isoformat()

    save_json(WORLD_TIME_PATH, data)


def advance_world_time(days=1):
    data = load_world_time()

    data["turn"] = int(data.get("turn", 0)) + 1
    data["day"] = int(data.get("day", 1)) + days

    days_per_month = int(data.get("days_per_month", 30))
    months_per_year = int(data.get("months_per_year", 12))

    while data["day"] > days_per_month:
        data["day"] -= days_per_month
        data["month"] = int(data.get("month", 1)) + 1

    while data["month"] > months_per_year:
        data["month"] -= months_per_year
        data["year"] = int(data.get("year", 1)) + 1

    save_world_time(data)
    return data


def format_world_date(data=None):
    if data is None:
        data = load_world_time()

    return (
        f"Año {data.get('year', 1)}, "
        f"Mes {data.get('month', 1)}, "
        f"Día {data.get('day', 1)} "
        f"— Turno {data.get('turn', 0)}"
    )