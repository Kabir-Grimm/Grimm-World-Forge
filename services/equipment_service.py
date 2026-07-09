import json
import os

from services.entity_editor_service import load_all_entities
from services.relation_service import load_relations


DEFAULT_ITEMS_PATH = "entities/default_items.json"

EQUIPMENT_RELATIONS = [
    "posee",
    "porta",
    "usa",
    "equipa",
    "empuña",
    "viste",
    "lleva",
    "conoce",
    "estudió",
    "bendecido por"
]


DEFAULT_ITEMS = [
    {
        "id": "default_weapon_1",
        "name": "Espada corta",
        "type": "weapons",
        "data": {
            "Categoría": "Arma",
            "Descripción": "Hoja ligera y común."
        },
        "effects": {
            "combat": 2,
            "damage": 1,
            "initiative": 1
        }
    },
    {
        "id": "default_weapon_2",
        "name": "Hacha pesada",
        "type": "weapons",
        "data": {
            "Categoría": "Arma",
            "Descripción": "Arma lenta pero brutal."
        },
        "effects": {
            "combat": 2,
            "damage": 3,
            "initiative": -1
        }
    },
    {
        "id": "default_armor_1",
        "name": "Armadura de cuero",
        "type": "armors",
        "data": {
            "Categoría": "Armadura",
            "Descripción": "Protección ligera y flexible."
        },
        "effects": {
            "defense": 2,
            "resistance": 1
        }
    },
    {
        "id": "default_armor_2",
        "name": "Cota de malla",
        "type": "armors",
        "data": {
            "Categoría": "Armadura",
            "Descripción": "Buena defensa, algo pesada."
        },
        "effects": {
            "defense": 3,
            "resistance": 2,
            "initiative": -1
        }
    },
    {
        "id": "default_relic_1",
        "name": "Amuleto de ceniza",
        "type": "relics",
        "data": {
            "Categoría": "Reliquia",
            "Descripción": "Protege contra corrupción espiritual."
        },
        "effects": {
            "arcane": 1,
            "defense": 1,
            "resistance": 2
        }
    },
    {
        "id": "default_magic_1",
        "name": "Rudimentos de magia ígnea",
        "type": "magic_systems",
        "data": {
            "Categoría": "Conocimiento mágico",
            "Descripción": "Control básico del fuego."
        },
        "effects": {
            "arcane": 3,
            "control": 1,
            "risk": 1
        }
    }
]


def ensure_default_items():
    os.makedirs("entities", exist_ok=True)

    if os.path.exists(DEFAULT_ITEMS_PATH):
        return

    with open(DEFAULT_ITEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            DEFAULT_ITEMS,
            f,
            indent=4,
            ensure_ascii=False
        )


def load_default_items():
    ensure_default_items()

    with open(DEFAULT_ITEMS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def load_all_equipment():
    """
    Carga equipo por defecto + entidades creadas que tengan effects.
    """

    equipment = []

    equipment.extend(load_default_items())

    for entity in load_all_entities():
        if not isinstance(entity, dict):
            continue

        if "effects" in entity:
            equipment.append(entity)

    return equipment


def get_equipment_by_id(entity_id):
    for item in load_all_equipment():
        if item.get("id") == entity_id:
            return item

    return None


def get_equipment_for_entity(entity_id):
    """
    Devuelve objetos relacionados a una entidad.
    Ej:
    Claude -> posee -> Espada corta
    Claude -> equipa -> Cota de malla
    """

    equipment = []

    relations = load_relations()

    for relation in relations:
        source = relation.get("source", {})
        target = relation.get("target", {})
        relation_type = relation.get("relation_type", "").lower()

        if source.get("id") != entity_id:
            continue

        if relation_type not in EQUIPMENT_RELATIONS:
            continue

        item = get_equipment_by_id(target.get("id"))

        if item:
            equipment.append({
                "relation": relation_type,
                "item": item
            })

    return equipment


def get_equipment_effects(entity_id):
    totals = {
        "combat": 0,
        "defense": 0,
        "damage": 0,
        "resistance": 0,
        "arcane": 0,
        "control": 0,
        "stealth": 0,
        "knowledge": 0,
        "social": 0,
        "influence": 0,
        "initiative": 0,
        "risk": 0
    }

    for entry in get_equipment_for_entity(entity_id):
        item = entry.get("item", {})
        effects = item.get("effects", {})

        for key, value in effects.items():
            if key not in totals:
                totals[key] = 0

            try:
                totals[key] += int(value)
            except:
                pass

    return totals