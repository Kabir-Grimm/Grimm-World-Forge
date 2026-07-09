import random

from services.entity_registry_service import get_entity_by_id
from services.relation_service import load_relations
from services.equipment_service import get_equipment_effects
from services.modifier_service import parse_modifier_line, apply_modifiers
from core.parser import load_all_lists


POWER_RANKS = {
    "Débil": 4,
    "Común": 8,
    "Competente": 12,
    "Fuerte": 16,
    "Excepcional": 22,
    "Legendario": 30
}


RELATION_BONUS_TYPES = {
    "sirve a": {"influence": 1},
    "lidera": {"influence": 3, "social": 2},
    "aliado con": {"influence": 2},
    "entrenó en": {"combat": 2},
    "estudió": {"knowledge": 2, "arcane": 1},
    "bendecido por": {"arcane": 2, "influence": 2, "resistance": 1}
}


def get_power_rank_value(rank):
    return POWER_RANKS.get(rank, POWER_RANKS["Común"])


def get_base_power(entity):
    meta = entity.get("meta", {})
    rank = meta.get("power_rank", "Aleatorio")

    if rank and rank != "Aleatorio":
        value = get_power_rank_value(rank)
    else:
        value = random.randint(6, 14)
        importance = meta.get("importance", "Común")

        if importance in ["Protagonista", "Antagonista", "Entidad clave"]:
            value += 6
        elif importance in ["Importante", "Líder", "Héroe", "Villano"]:
            value += 3

    return {
        "base": value,
        "combat": value,
        "defense": value,
        "damage": max(0, value // 4),
        "resistance": value,
        "social": max(1, value - random.randint(0, 4)),
        "arcane": max(0, value // random.randint(2, 4)),
        "control": max(0, value // 4),
        "stealth": max(1, value - random.randint(0, 6)),
        "knowledge": max(0, value // 3),
        "influence": max(0, value // random.randint(2, 3)),
        "initiative": random.randint(-1, 2),
        "risk": 0
    }


def get_relation_bonuses(entity_id):
    bonuses = {}

    for relation in load_relations():
        source = relation.get("source", {})
        relation_type = relation.get("relation_type", "").lower()

        if source.get("id") != entity_id:
            continue

        relation_bonus = RELATION_BONUS_TYPES.get(relation_type)

        if not relation_bonus:
            continue

        for key, value in relation_bonus.items():
            bonuses[key] = bonuses.get(key, 0) + value

    return bonuses


def get_modifier_from_lists(target_name, list_names):
    for oracle in load_all_lists():
        if oracle["name"] not in list_names:
            continue

        data = oracle.get("data", {})
        options = []

        if "Resultados" in data:
            options = data["Resultados"]
        else:
            for values in data.values():
                options.extend(values)

        for raw_text, _weight in options:
            name, modifiers = parse_modifier_line(raw_text)

            if name == target_name:
                return modifiers

    return {}


def get_status_modifiers(entity):
    status = entity.get("meta", {}).get("status", "Sano")

    return get_modifier_from_lists(
        status,
        ["Entidades-Estados"]
    )


def get_traits_modifiers(entity):
    traits = entity.get("meta", {}).get("traits", [])

    if not isinstance(traits, list):
        return {}

    total = {}

    for trait in traits:
        modifiers = get_modifier_from_lists(
            trait,
            [
                "Entidades-Rasgos",
                "Entidades-Rasgos-Poderes"
            ]
        )

        for key, value in modifiers.items():
            if isinstance(value, int):
                total[key] = total.get(key, 0) + value

    return total


def merge_scores(*score_dicts):
    result = {}

    for scores in score_dicts:
        for key, value in scores.items():
            if isinstance(value, int):
                result[key] = result.get(key, 0) + value

    return result


def calculate_entity_power(entity_id):
    entity = get_entity_by_id(entity_id)

    if not entity:
        return None

    meta = entity.get("meta", {})

    if meta.get("active") is False:
        return None

    base_power = get_base_power(entity)
    relation_bonuses = get_relation_bonuses(entity_id)
    equipment_effects = get_equipment_effects(entity_id)
    status_modifiers = get_status_modifiers(entity)
    traits_modifiers = get_traits_modifiers(entity)

    total = merge_scores(
        base_power,
        relation_bonuses,
        equipment_effects,
        status_modifiers,
        traits_modifiers
    )

    total["total"] = (
        total.get("combat", 0)
        + total.get("defense", 0)
        + total.get("damage", 0)
        + total.get("resistance", 0)
        + total.get("social", 0)
        + total.get("arcane", 0)
        + total.get("control", 0)
        + total.get("stealth", 0)
        + total.get("knowledge", 0)
        + total.get("influence", 0)
        + total.get("initiative", 0)
        - total.get("risk", 0)
    )

    return {
        "entity": {
            "id": entity.get("id"),
            "name": entity.get("name"),
            "type": entity.get("type")
        },
        "power": total,
        "base": base_power,
        "relation_bonuses": relation_bonuses,
        "equipment_effects": equipment_effects,
        "status_modifiers": status_modifiers,
        "traits_modifiers": traits_modifiers
    }


def roll_power_check(entity_id, domain="combat", external_modifiers=None):
    power_data = calculate_entity_power(entity_id)

    if not power_data:
        return None

    scores = power_data["power"]

    if external_modifiers:
        scores = apply_modifiers(scores, external_modifiers)

    score = scores.get(domain, 0)
    roll = random.randint(1, 20)

    return {
        "entity": power_data["entity"],
        "domain": domain,
        "score": score,
        "roll": roll,
        "total": score + roll,
        "breakdown": power_data,
        "external_modifiers": external_modifiers or {}
    }