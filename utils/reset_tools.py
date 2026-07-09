import json
import os
import shutil
from datetime import datetime


ENTITIES_DIR = "entities"
BACKUP_DIR = "backups/entities"


CORE_FILES_TO_KEEP = {
    "default_items.json",
    "magic_systems.json",
    "spells.json"
}


GENERATED_FILES_TO_CLEAR = {
    "npcs.json",
    "worlds.json",
    "relations.json",
    "relation_layout.json",
    "locations.json",
    "kingdoms.json",
    "factions.json",
    "creatures.json",
    "armies.json",
    "foods.json"
}


RESET_FILES_TO_CLEAR = {
    "npcs.json",
    "worlds.json",
    "relations.json",
    "relation_layout.json",
    "locations.json",
    "kingdoms.json",
    "factions.json",
    "creatures.json",
    "armies.json",
    "foods.json",
    "weapons.json",
    "armors.json",
    "relics.json",
    "items.json"
}


def ensure_dirs():
    os.makedirs(ENTITIES_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def backup_entities():
    ensure_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        BACKUP_DIR,
        f"backup_{timestamp}"
    )

    os.makedirs(backup_path, exist_ok=True)

    copied = []

    if not os.path.exists(ENTITIES_DIR):
        return {
            "backup_dir": backup_path,
            "copied": copied
        }

    for filename in os.listdir(ENTITIES_DIR):
        source = os.path.join(ENTITIES_DIR, filename)

        if not os.path.isfile(source):
            continue

        target = os.path.join(backup_path, filename)

        shutil.copy2(source, target)
        copied.append(filename)

    return {
        "backup_dir": backup_path,
        "copied": copied
    }


def load_json_list(path):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return []

    if isinstance(data, list):
        return data

    return []


def save_json_list(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def is_default_entity(entity):
    entity_id = str(entity.get("id", ""))
    name = str(entity.get("name", ""))

    return (
        entity_id.startswith("default_")
        or name.startswith("[DEFAULT]")
    )


def preserve_default_entries(path):
    data = load_json_list(path)

    if not data:
        return []

    preserved = [
        entity
        for entity in data
        if isinstance(entity, dict)
        and is_default_entity(entity)
    ]

    if preserved:
        save_json_list(path, preserved)
    else:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    return preserved


def should_keep_entire_file(filename):
    return filename in CORE_FILES_TO_KEEP


def clean_entities(create_backup=True):
    ensure_dirs()

    result = {
        "backup": None,
        "deleted": [],
        "preserved": []
    }

    if create_backup:
        result["backup"] = backup_entities()

    if not os.path.exists(ENTITIES_DIR):
        return result

    for filename in os.listdir(ENTITIES_DIR):
        path = os.path.join(ENTITIES_DIR, filename)

        if not os.path.isfile(path):
            continue

        if should_keep_entire_file(filename):
            result["preserved"].append(filename)
            continue

        if filename not in GENERATED_FILES_TO_CLEAR:
            continue

        preserved_entries = preserve_default_entries(path)

        if preserved_entries:
            result["preserved"].append(
                f"{filename} ({len(preserved_entries)} default)"
            )
        else:
            result["deleted"].append(filename)

    return result


def reset_world_data(create_backup=True):
    ensure_dirs()

    result = {
        "backup": None,
        "deleted": [],
        "preserved": []
    }

    if create_backup:
        result["backup"] = backup_entities()

    if not os.path.exists(ENTITIES_DIR):
        return result

    for filename in os.listdir(ENTITIES_DIR):
        path = os.path.join(ENTITIES_DIR, filename)

        if not os.path.isfile(path):
            continue

        if should_keep_entire_file(filename):
            result["preserved"].append(filename)
            continue

        if filename not in RESET_FILES_TO_CLEAR:
            continue

        preserved_entries = preserve_default_entries(path)

        if preserved_entries:
            result["preserved"].append(
                f"{filename} ({len(preserved_entries)} default)"
            )
        else:
            result["deleted"].append(filename)

    return result