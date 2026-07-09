import random
from datetime import datetime

from core.parser import load_all_lists, weighted_choice
from services.world_service import load_worlds
from services.entity_editor_service import load_all_entities
from services.entity_service import save_entity
from services.chaos_service import get_chaos
from services.timeline_service import save_timeline_event


LIST_NAMES = {
    "focus": "Ecos-Foco",
    "action": "Ecos-Accion",
    "tone": "Ecos-Tono",
    "impact": "Ecos-Impacto",
    "scope": "Ecos-Alcance"
}


def find_oracle(name):
    for oracle in load_all_lists():
        if oracle["name"] == name:
            return oracle

    return None


def roll_oracle(name):
    oracle = find_oracle(name)

    if not oracle:
        return "NO ENCONTRADO"

    data = oracle.get("data", {})

    if "Resultados" in data:
        return weighted_choice(data["Resultados"])

    options = []

    for values in data.values():
        options.extend(values)

    if not options:
        return "SIN RESULTADOS"

    return weighted_choice(options)


def get_world(world_id):
    for world in load_worlds():
        if world.get("id") == world_id:
            return world

    return None


def get_world_entities(world_id):
    world = get_world(world_id)

    if not world:
        return []

    ids = {
        entity.get("id")
        for entity in world.get("entities", [])
    }

    return [
        entity for entity in load_all_entities()
        if entity.get("id") in ids
    ]


def choose_target(world_id, focus):
    entities = get_world_entities(world_id)

    if not entities:
        return None

    focus_map = {
        "NPC": ["npcs", "npc"],
        "Ubicación": ["locations", "location", "cities"],
        "Facción": ["factions"],
        "Mundo": ["world"],
        "Objeto importante": ["items", "relics", "weapons", "armors"],
    }

    allowed_types = focus_map.get(focus)

    if allowed_types:
        candidates = [
            entity for entity in entities
            if entity.get("type") in allowed_types
        ]

        if candidates:
            return random.choice(candidates)

    return random.choice(entities)


def build_echo_interpretation(echo):
    target_name = echo.get("target", {}).get("name", "algo importante")

    return (
        f"Un eco de tono {echo['tone'].lower()} surge con alcance "
        f"{echo['scope'].lower()}: {echo['action'].lower()} "
        f"afecta a {target_name}. Consecuencia: "
        f"{echo['impact'].lower()}."
    )


def generate_echo(world_id=None):
    chaos = get_chaos()

    world = get_world(world_id) if world_id else None

    focus = roll_oracle(LIST_NAMES["focus"])
    action = roll_oracle(LIST_NAMES["action"])
    tone = roll_oracle(LIST_NAMES["tone"])
    impact = roll_oracle(LIST_NAMES["impact"])
    scope = roll_oracle(LIST_NAMES["scope"])

    target = choose_target(world_id, focus) if world_id else None

    if not target and world:
        target = {
            "id": world.get("id"),
            "name": world.get("name"),
            "type": "world"
        }

    echo = {
        "world_id": world_id,
        "world_name": world.get("name") if world else None,
        "chaos": chaos,
        "focus": focus,
        "action": action,
        "tone": tone,
        "impact": impact,
        "scope": scope,
        "target": {
            "id": target.get("id") if target else None,
            "name": target.get("name") if target else "Sin objetivo",
            "type": target.get("type") if target else "unknown"
        },
        "created_at": datetime.now().isoformat()
    }

    echo["description"] = build_echo_interpretation(echo)

    return echo


def save_echo_as_event(echo):
    entity = {
        "name": echo.get("description", "Eco Sin Nombre"),
        "type": "events",
        "data": echo
    }

    event_id = save_entity(
        "events",
        entity
    )

    echo["entity_id"] = event_id

    if echo.get("world_id"):
        timeline_event = {
            "world_id": echo.get("world_id"),
            "world_name": echo.get("world_name"),
            "year": echo.get("year", 1),
            "event_type": "Eco",
            "target": echo.get("target"),
            "description": echo.get("description"),
            "data": echo,
            "created_at": echo.get("created_at")
        }

        save_timeline_event(timeline_event)

    return event_id