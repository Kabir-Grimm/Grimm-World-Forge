from services.entity_registry_service import get_entity_by_id
from services.entity_editor_service import save_entity_update


REPUTATION_KEYS = [
    "military",
    "social",
    "arcane",
    "criminal",
    "heroic",
    "political",
    "monstrous"
]


METHOD_REPUTATION_MAP = {
    "Fuerza": "military",
    "Magia": "arcane",
    "Estrategia": "military",
    "Diplomacia": "political",
    "Sigilo": "criminal",
    "Manipulación": "political",
    "Conocimiento": "social",
    "Fe": "heroic",
    "Tecnología": "social",
    "Recursos": "political",
    "Intimidación": "monstrous",
    "Engaño": "criminal"
}


def get_reputation(entity_id):
    entity = get_entity_by_id(entity_id)

    if not entity:
        return {}

    reputation = entity.get("reputation", {})

    if not isinstance(reputation, dict):
        return {}

    return reputation


def modify_reputation(entity_id, key, amount):
    entity = get_entity_by_id(entity_id)

    if not entity:
        return False

    reputation = entity.get("reputation", {})

    if not isinstance(reputation, dict):
        reputation = {}

    reputation[key] = reputation.get(key, 0) + amount

    entity["reputation"] = reputation

    return save_entity_update(entity)


def apply_reputation_changes(changes):
    results = []

    for change in changes:
        entity_id = change.get("entity_id")
        key = change.get("key")
        amount = change.get("amount", 0)

        if not entity_id or not key or amount == 0:
            continue

        ok = modify_reputation(
            entity_id,
            key,
            amount
        )

        results.append({
            "entity_id": entity_id,
            "key": key,
            "amount": amount,
            "applied": ok
        })

    return results


def reputation_key_from_method(method):
    return METHOD_REPUTATION_MAP.get(
        method,
        "social"
    )


def calculate_encounter_reputation_changes(result):
    """
    Crea cambios de reputación basados en un encuentro.
    """

    if not result:
        return []

    winner = result.get("winner")
    loser = result.get("loser")

    if not winner or not loser:
        return []

    winner_entity = winner.get("entity", {})
    loser_entity = loser.get("entity", {})

    winner_id = winner_entity.get("id")
    loser_id = loser_entity.get("id")

    method_a = result.get("method_a")
    method_b = result.get("method_b")

    actor_a = result.get("actor_a", {}).get("entity", {})
    actor_b = result.get("actor_b", {}).get("entity", {})

    margin = abs(result.get("margin", 0))
    risk = result.get("risk", "Moderado")

    winner_method = method_a

    if winner_id == actor_b.get("id"):
        winner_method = method_b

    rep_key = reputation_key_from_method(
        winner_method
    )

    winner_gain = 1
    loser_loss = -1

    if risk == "Alto":
        winner_gain += 1
    elif risk == "Mortal":
        winner_gain += 2
        loser_loss -= 1

    if margin > 8:
        winner_gain += 1
        loser_loss -= 1

    changes = [
        {
            "entity_id": winner_id,
            "key": rep_key,
            "amount": winner_gain
        },
        {
            "entity_id": loser_id,
            "key": rep_key,
            "amount": loser_loss
        }
    ]

    # Riesgos oscuros o violentos pueden aumentar reputación monstruosa/criminal
    if result.get("risk") in ["Alto", "Mortal"]:
        if winner_method in ["Intimidación", "Fuerza"]:
            changes.append({
                "entity_id": winner_id,
                "key": "monstrous",
                "amount": 1
            })

        if winner_method in ["Sigilo", "Engaño", "Manipulación"]:
            changes.append({
                "entity_id": winner_id,
                "key": "criminal",
                "amount": 1
            })

    return changes


def apply_encounter_reputation(result):
    changes = calculate_encounter_reputation_changes(result)

    return apply_reputation_changes(changes)