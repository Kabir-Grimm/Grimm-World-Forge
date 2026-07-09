from services.world_service import load_worlds
from services.entity_editor_service import load_all_entities
from services.echoes_service import generate_echo
from services.timeline_service import (
    get_current_world_year,
    save_timeline_event
)


def get_world_by_id(world_id):
    for world in load_worlds():
        if world.get("id") == world_id:
            return world

    return None


def get_entities_for_world(world_id):
    world = get_world_by_id(world_id)

    if not world:
        return []

    world_entity_ids = {
        entity.get("id")
        for entity in world.get("entities", [])
    }

    all_entities = load_all_entities()

    return [
        entity for entity in all_entities
        if entity.get("id") in world_entity_ids
    ]


def advance_world_time(world_id, years=1):
    current_year = get_current_world_year(world_id)
    return current_year + years


def generate_world_event(world_id):
    world = get_world_by_id(world_id)

    if not world:
        return None

    year = get_current_world_year(world_id)

    echo = generate_echo(world_id)
    echo["year"] = year

    event = {
        "world_id": world_id,
        "world_name": world.get("name", "Mundo"),
        "year": year,
        "event_type": "Eco",
        "target": echo.get("target"),
        "description": echo.get("description"),
        "data": echo,
        "created_at": echo.get("created_at")
    }

    return event


def generate_and_save_world_event(world_id):
    event = generate_world_event(world_id)

    if not event:
        return None

    save_timeline_event(event)

    return event