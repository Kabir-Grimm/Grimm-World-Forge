import json
import os

from services.entity_service import save_entity


TIMELINE_PATH = "entities/timeline.json"


def load_timeline():
    if not os.path.exists(TIMELINE_PATH):
        return []

    with open(TIMELINE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def save_timeline(timeline):
    os.makedirs("entities", exist_ok=True)

    with open(TIMELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            timeline,
            f,
            indent=4,
            ensure_ascii=False
        )


def save_timeline_event(event):
    timeline = load_timeline()

    event["id"] = f"timeline_{len(timeline) + 1}"

    timeline.append(event)

    save_timeline(timeline)

    save_entity(
        "events",
        {
            "name": event.get("description", "Evento Sin Nombre"),
            "type": "events",
            "data": event
        }
    )

    return event["id"]


def get_world_timeline(world_id):
    events = [
        event for event in load_timeline()
        if event.get("world_id") == world_id
    ]

    events.sort(
        key=lambda event: event.get("year", 0)
    )

    return events


def get_current_world_year(world_id):
    return get_world_year(world_id)

    

WORLD_TIME_PATH = "entities/world_time.json"


def load_world_time():
    if not os.path.exists(WORLD_TIME_PATH):
        return {}

    with open(WORLD_TIME_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_world_time(data):
    os.makedirs("entities", exist_ok=True)

    with open(WORLD_TIME_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_world_year(world_id):
    data = load_world_time()

    if world_id not in data:
        data[world_id] = 1
        save_world_time(data)

    return data[world_id]


def advance_world_year(world_id, amount=1):
    data = load_world_time()

    current = data.get(world_id, 1)
    current += amount

    data[world_id] = current

    save_world_time(data)

    return current