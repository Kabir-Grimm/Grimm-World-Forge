import json
import os

CHAOS_PATH = "data/worlds/chaos.json"


# =========================================
# Asegurar archivo
# =========================================

def ensure_chaos():

    os.makedirs(
        "data/worlds",
        exist_ok=True
    )

    if not os.path.exists(CHAOS_PATH):

        data = {
            "global_chaos": 5
        }

        with open(
            CHAOS_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )


# =========================================
# Obtener caos
# =========================================

def get_chaos():

    ensure_chaos()

    with open(
        CHAOS_PATH,
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data.get(
        "global_chaos",
        5
    )


# =========================================
# Ajustar caos
# =========================================

def modify_chaos(amount):

    ensure_chaos()

    with open(
        CHAOS_PATH,
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    current = data.get(
        "global_chaos",
        5
    )

    current += amount

    current = max(
        1,
        min(9, current)
    )

    data["global_chaos"] = current

    with open(
        CHAOS_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    return current


# =========================================
# Escena estable
# =========================================

def stable_scene():

    return modify_chaos(-1)


# =========================================
# Escena caótica
# =========================================

def chaotic_scene():

    return modify_chaos(1)