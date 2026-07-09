import json
import os


ENTITIES_DIR = "entities"


IGNORED_FILES = {
    "relations.json",
    "graph_positions.json",
    "timeline.json",
    "world_time.json",
    "world_map.json",
    "relation_layout.json"
}


IGNORED_TYPES = {
    "events",
    "event",
    "echoes",
    "echo",
    "timeline"
}


ENTITY_PROFILES = {
    "all": None,

    "editor": [
        "npcs.json",
        "locations.json",
        "kingdoms.json",
        "factions.json",
        "creatures.json",
        "armies.json",
        "relics.json",
        "items.json",
        "weapons.json",
        "armors.json",
        "foods.json",
        "magic_systems.json",
        "spells.json",
        "generated_spells.json"
    ],

    "world": [
        "npcs.json",
        "locations.json",
        "kingdoms.json",
        "factions.json",
        "creatures.json",
        "armies.json",
        "relics.json",
        "items.json",
        "weapons.json",
        "armors.json",
        "foods.json",
        "default_items.json"
    ],

    "relations": [
        "npcs.json",
        "locations.json",
        "kingdoms.json",
        "factions.json",
        "creatures.json",
        "armies.json",
        "relics.json"
    ],

    "encounters": [
        "npcs.json",
        "locations.json",
        "creatures.json",
        "factions.json",
        "armies.json",
        "relics.json",
        "items.json"
    ]
}


_registry_cache = {}


def clear_registry_cache():
    global _registry_cache
    _registry_cache = {}


def load_json_list(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return []

    return data if isinstance(data, list) else []


def get_files_for_profile(profile):
    if not os.path.exists(ENTITIES_DIR):
        return []

    profile_files = ENTITY_PROFILES.get(profile)

    if profile_files is None:
        return [
            file for file in os.listdir(ENTITIES_DIR)
            if file.endswith(".json")
            and file not in IGNORED_FILES
        ]

    return profile_files


def load_registry_entities(
    include_hidden=False,
    profile="editor",
    include_default=False
):
    cache_key = (
        profile,
        include_hidden,
        include_default
    )

    if cache_key in _registry_cache:
        return [
            dict(entity)
            for entity in _registry_cache[cache_key]
        ]

    entities = []

    if not os.path.exists(ENTITIES_DIR):
        return entities

    for file in get_files_for_profile(profile):
        path = os.path.join(ENTITIES_DIR, file)

        if not os.path.exists(path):
            continue

        data = load_json_list(path)

        for entity in data:
            if not isinstance(entity, dict):
                continue

            if not entity.get("id"):
                continue

            entity_type = entity.get("type")
            entity_id = str(entity.get("id", ""))

            if (
                not include_hidden
                and entity_type in IGNORED_TYPES
            ):
                continue

            if (
                not include_default
                and entity_id.startswith("default_")
                and not entity.get("map_enabled", False)
                and profile in ["world", "relations", "encounters"]
            ):
                continue

            clean_entity = dict(entity)
            clean_entity["_source_file"] = file

            entities.append(clean_entity)

    entities.sort(
        key=lambda e: (
            str(e.get("type", "")),
            str(e.get("name", ""))
        )
    )

    _registry_cache[cache_key] = [
        dict(entity)
        for entity in entities
    ]

    return entities


def get_entity_by_id(
    entity_id,
    profile="all"
):
    for entity in load_registry_entities(
        include_hidden=True,
        profile=profile,
        include_default=True
    ):
        if entity.get("id") == entity_id:
            return entity

    return None


def get_entities_by_type(
    entity_type,
    profile="editor"
):
    return [
        entity
        for entity in load_registry_entities(profile=profile)
        if entity.get("type") == entity_type
    ]