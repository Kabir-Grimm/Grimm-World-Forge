import json
import os

from services.display_profile_service import get_active_profile_name


PROFILE_DIR = "data/display_profiles"


UNIVERSAL_FALLBACK = {
    "entity_types": {},
    "stats": {},
    "reputation": {},
    "meta": {}
}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def merge_dicts(base, override):
    result = dict(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def load_display_profile():
    universal_path = os.path.join(PROFILE_DIR, "universal.json")
    active_name = get_active_profile_name()
    active_path = os.path.join(PROFILE_DIR, f"{active_name}.json")

    universal = load_json(universal_path)

    if not universal:
        universal = UNIVERSAL_FALLBACK

    if active_name == "universal":
        return universal

    active = load_json(active_path)

    return merge_dicts(universal, active)


def display_entity_type(entity_type):
    profile = load_display_profile()

    #print(
    #    "PERFIL ACTIVO:",
    #    get_active_profile_name(),
    #    "TIPO:",
    #    entity_type,
    #    "MOSTRANDO:",
    #    profile.get("entity_types", {}).get(entity_type)
    #)

    return profile.get("entity_types", {}).get(
        entity_type,
        entity_type or "Entidad"
    )


def display_stat(stat):
    profile = load_display_profile()

    return profile.get("stats", {}).get(
        stat,
        stat
    )


def display_reputation(key):
    profile = load_display_profile()

    return profile.get("reputation", {}).get(
        key,
        key
    )


def display_meta(key):
    profile = load_display_profile()

    return profile.get("meta", {}).get(
        key,
        key
    )

def display_ui(key):
    profile = load_display_profile()

    return profile.get("ui", {}).get(
        key,
        key
    )