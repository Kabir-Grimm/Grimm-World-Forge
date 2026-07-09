import json
import os
import random


DEFAULT_ITEMS_PATH = "entities/default_items.json"
MAGIC_SYSTEMS_PATH = "entities/magic_systems.json"
SPELLS_PATH = "entities/spells.json"


def load_json_list(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return []

    return data if isinstance(data, list) else []


def load_default_items():
    return load_json_list(DEFAULT_ITEMS_PATH)


def load_magic_systems():
    return load_json_list(MAGIC_SYSTEMS_PATH)


def load_spells():
    return load_json_list(SPELLS_PATH)


def get_tags(item):
    tags = item.get("data", {}).get("tags", [])

    if not isinstance(tags, list):
        return []

    return [str(tag).lower().strip() for tag in tags]


def has_any_tag(item, tags):
    return bool(set(get_tags(item)).intersection({
        str(tag).lower().strip()
        for tag in tags
    }))


def filter_items(items, item_type=None, tags=None):
    results = []

    for item in items:
        if item_type and item.get("type") != item_type:
            continue

        if tags and not has_any_tag(item, tags):
            continue

        results.append(item)

    return results


def pick_one(items):
    return random.choice(items) if items else None


def pick_many(items, min_count=0, max_count=2):
    if not items:
        return []

    count = random.randint(min_count, max_count)
    count = min(count, len(items))

    return random.sample(items, count)


def simplify_item(item):
    if not item:
        return None

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": item.get("type"),
        "category": item.get("data", {}).get("Categoría"),
        "description": item.get("data", {}).get("Descripción"),
        "tags": item.get("data", {}).get("tags", []),
        "effects": item.get("effects", {})
    }


def tags_for_role(role):
    role = str(role or "").lower()

    if "mercenario" in role:
        return ["soldier", "medium", "melee", "ranged"]

    if "enemigo" in role or "rival" in role:
        return ["dangerous", "combat", "stealth", "soldier"]

    if "gobernante" in role or "líder" in role or "lider" in role:
        return ["noble", "social", "authority", "relic"]

    if "guardián" in role or "guardian" in role:
        return ["defensive", "soldier", "armor", "shield"]

    if "profeta" in role or "mentor" in role:
        return ["arcane", "knowledge", "book", "relic"]

    if "agente" in role:
        return ["stealth", "tech", "access", "light"]

    if "aliado" in role:
        return ["support", "medical", "defensive"]

    return ["common", "light", "survival"]


def tags_for_power_rank(power_rank):
    power_rank = str(power_rank or "").lower()

    if "débil" in power_rank or "debil" in power_rank:
        return ["common", "light", "improvised"]

    if "común" in power_rank or "comun" in power_rank:
        return ["common", "light", "medium"]

    if "competente" in power_rank:
        return ["soldier", "medium", "tool"]

    if "fuerte" in power_rank:
        return ["soldier", "heavy", "advanced"]

    if "excepcional" in power_rank:
        return ["advanced", "rare", "relic", "arcane"]

    if "legendario" in power_rank:
        return ["rare", "relic", "dangerous", "advanced", "arcane"]

    return ["common", "medium"]


def generate_abilities(role, power_rank):
    role = str(role or "").lower()
    power_rank = str(power_rank or "").lower()

    pool = [
        "Percepción aguda",
        "Resistencia práctica",
        "Instinto de supervivencia",
        "Lectura de intenciones",
        "Improvisación rápida",
        "Conocimiento local",
        "Disciplina básica"
    ]

    if any(key in role for key in ["enemigo", "rival", "mercenario", "guardián", "guardian"]):
        pool.extend([
            "Combate cuerpo a cuerpo",
            "Uso de armas",
            "Defensa táctica",
            "Ataque oportunista",
            "Intimidación",
            "Reflejos entrenados"
        ])

    if any(key in role for key in ["agente", "oculto"]):
        pool.extend([
            "Sigilo",
            "Infiltración",
            "Robo menor",
            "Evasión",
            "Disfraz",
            "Emboscada"
        ])

    if any(key in role for key in ["gobernante", "líder", "lider", "aliado"]):
        pool.extend([
            "Negociación",
            "Persuasión",
            "Etiqueta",
            "Manipulación social",
            "Mando",
            "Lectura política"
        ])

    if any(key in role for key in ["mentor", "profeta"]):
        pool.extend([
            "Conocimiento antiguo",
            "Investigación",
            "Historia local",
            "Interpretación de símbolos",
            "Rituales básicos",
            "Análisis de amenazas"
        ])

    count = 2

    if "competente" in power_rank:
        count = 3
    elif "fuerte" in power_rank:
        count = 4
    elif "excepcional" in power_rank:
        count = 5
    elif "legendario" in power_rank:
        count = 6

    pool = list(dict.fromkeys(pool))

    return random.sample(pool, min(count, len(pool)))


def should_know_magic(role, power_rank, importance):
    role = str(role or "").lower()
    power_rank = str(power_rank or "").lower()
    importance = str(importance or "").lower()

    chance = 15

    if any(key in role for key in ["mentor", "profeta", "gobernante", "agente oculto"]):
        chance += 25

    if any(key in power_rank for key in ["fuerte", "excepcional", "legendario"]):
        chance += 25

    if any(key in importance for key in [
        "protagonista",
        "antagonista",
        "líder",
        "lider",
        "héroe",
        "heroe",
        "villano",
        "entidad clave"
    ]):
        chance += 20

    return random.randint(1, 100) <= chance


def generate_npc_loadout(
    role,
    power_rank,
    importance,
    include_equipment=True,
    include_abilities=True,
    include_magic=True
):
    items = load_default_items()
    magic_systems = load_magic_systems()
    spells = load_spells()

    role_tags = tags_for_role(role)
    rank_tags = tags_for_power_rank(power_rank)
    combined_tags = list(set(role_tags + rank_tags))

    loadout = {
        "equipment": {
            "weapon": None,
            "armor": None,
            "items": [],
            "relics": []
        },
        "abilities": [],
        "magic": {
            "knows_magic": False,
            "known_systems": [],
            "known_spells": []
        }
    }

    if include_equipment:
        weapons = (
            filter_items(items, item_type="weapons", tags=combined_tags)
            or filter_items(items, item_type="weapons")
        )

        armors = (
            filter_items(items, item_type="armors", tags=combined_tags)
            or filter_items(items, item_type="armors")
        )

        useful_items = (
            filter_items(items, item_type="items", tags=combined_tags)
            or filter_items(items, item_type="items")
        )

        relics = filter_items(
            items,
            item_type="relics",
            tags=combined_tags
        )

        loadout["equipment"]["weapon"] = simplify_item(pick_one(weapons))
        loadout["equipment"]["armor"] = simplify_item(pick_one(armors))

        loadout["equipment"]["items"] = [
            simplify_item(item)
            for item in pick_many(useful_items, 1, 3)
        ]

        important = any(key in str(importance).lower() for key in [
            "protagonista",
            "antagonista",
            "líder",
            "lider",
            "héroe",
            "heroe",
            "villano",
            "entidad clave"
        ])

        if important:
            loadout["equipment"]["relics"] = [
                simplify_item(item)
                for item in pick_many(relics, 0, 1)
            ]

    if include_abilities:
        loadout["abilities"] = generate_abilities(role, power_rank)

    if include_magic:
        knows_magic = should_know_magic(role, power_rank, importance)

        has_magic_data = bool(magic_systems or spells)

        loadout["magic"]["knows_magic"] = knows_magic and has_magic_data

        if loadout["magic"]["knows_magic"]:
            selected_systems = pick_many(
                magic_systems,
                1,
                1
            )

            selected_spells = pick_many(
                spells,
                1,
                3
            )

            loadout["magic"]["known_systems"] = [
                simplify_item(item)
                for item in selected_systems
            ]

            loadout["magic"]["known_spells"] = [
                simplify_item(item)
                for item in selected_spells
            ]

    return loadout