import json
import os

PROFILE_FILE = "data/settings/display_profile.json"
PROFILE_DIR = "data/display_profiles"


def get_active_profile_name():
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("active_profile", "universal")
    except Exception:
        return "universal"


def set_active_profile(profile_name):
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"active_profile": profile_name},
            f,
            ensure_ascii=False,
            indent=4
        )


def get_available_profiles():
    if not os.path.exists(PROFILE_DIR):
        return []

    return sorted([
        filename.replace(".json", "")
        for filename in os.listdir(PROFILE_DIR)
        if filename.endswith(".json")
    ])

def set_active_profile(profile_name):
    print("GUARDANDO PERFIL:", profile_name)

    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"active_profile": profile_name},
            f,
            ensure_ascii=False,
            indent=4
        )