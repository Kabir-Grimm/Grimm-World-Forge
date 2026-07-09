from services.entity_registry_service import get_entity_by_id
from services.entity_editor_service import save_entity_update


POWER_ORDER = [
    "Débil",
    "Común",
    "Competente",
    "Fuerte",
    "Excepcional",
    "Legendario"
]


EVOLUTION_TRAITS = {
    "veteran": "Veterano",
    "survivor": "Sobreviviente",
    "infamous": "Infame",
    "heroic": "Famoso",
    "traumatized": "Traumatizado",
    "hardened": "Endurecido",
    "chosen": "Elegido",
    "corrupted": "Corrupto",
    "vengeful": "Vengativo"
}


def get_meta(entity):
    meta = entity.get("meta", {})

    if not isinstance(meta, dict):
        meta = {}

    return meta


def get_memory(entity):
    memory = entity.get("memory", [])

    if not isinstance(memory, list):
        return []

    return memory


def get_reputation(entity):
    reputation = entity.get("reputation", {})

    if not isinstance(reputation, dict):
        return {}

    return reputation


def get_traits(meta):
    traits = meta.get("traits", [])

    if not isinstance(traits, list):
        traits = []

    return traits


def add_trait(meta, trait):
    traits = get_traits(meta)

    if trait not in traits:
        traits.append(trait)

    meta["traits"] = traits

    return meta


def increase_power_rank(meta):
    current = meta.get("power_rank", "Común")

    if current == "Aleatorio":
        current = "Común"

    if current not in POWER_ORDER:
        current = "Común"

    index = POWER_ORDER.index(current)

    if index >= len(POWER_ORDER) - 1:
        return meta, False

    meta["power_rank"] = POWER_ORDER[index + 1]

    return meta, True


def count_memories(memory, memory_type):
    return len([
        item for item in memory
        if item.get("type") == memory_type
    ])


def count_memory_contains(memory, text):
    text = text.lower()

    return len([
        item for item in memory
        if text in item.get("description", "").lower()
    ])


def apply_entity_evolution(entity_id):
    """
    Aplica evolución automática según memoria, reputación y estado.

    Devuelve un resumen de cambios.
    """

    entity = get_entity_by_id(entity_id)

    if not entity:
        return {
            "applied": False,
            "reason": "Entidad no encontrada",
            "changes": []
        }

    meta = get_meta(entity)
    memory = get_memory(entity)
    reputation = get_reputation(entity)

    changes = []

    wins = count_memories(memory, "encounter_winner")
    losses = count_memories(memory, "encounter_loser")

    status = meta.get("status", "Sano")

    # =========================
    # Evolución por victorias
    # =========================

    if wins >= 3:
        before = meta.get("power_rank", "Común")
        meta, increased = increase_power_rank(meta)

        if increased:
            changes.append(
                f"Rango de poder aumentado: {before} → {meta.get('power_rank')}"
            )

    if wins >= 5:
        trait = EVOLUTION_TRAITS["veteran"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado: {trait}")

    # =========================
    # Evolución por derrotas
    # =========================

    if losses >= 3:
        trait = EVOLUTION_TRAITS["traumatized"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado: {trait}")

    if losses >= 5:
        trait = EVOLUTION_TRAITS["hardened"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado: {trait}")

    # =========================
    # Evolución por reputación
    # =========================

    if reputation.get("military", 0) >= 5:
        trait = EVOLUTION_TRAITS["veteran"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por reputación militar: {trait}")

    if reputation.get("criminal", 0) >= 4:
        trait = EVOLUTION_TRAITS["infamous"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por reputación criminal: {trait}")

    if reputation.get("heroic", 0) >= 4:
        trait = EVOLUTION_TRAITS["heroic"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por reputación heroica: {trait}")

    if reputation.get("arcane", 0) >= 5:
        trait = EVOLUTION_TRAITS["chosen"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por reputación arcana: {trait}")

    if reputation.get("monstrous", 0) >= 4:
        trait = EVOLUTION_TRAITS["vengeful"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por reputación monstruosa: {trait}")

    # =========================
    # Evolución por estados
    # =========================

    if status in ["Corrupto", "Corrupto severo"]:
        trait = EVOLUTION_TRAITS["corrupted"]

        if trait not in get_traits(meta):
            meta = add_trait(meta, trait)
            changes.append(f"Rasgo ganado por corrupción: {trait}")

    if status == "Moribundo":
        meta["active"] = True

        if "Sobreviviente" not in get_traits(meta):
            meta = add_trait(meta, "Sobreviviente")
            changes.append("Rasgo ganado: Sobreviviente")

    # =========================
    # Guardar
    # =========================

    if not changes:
        return {
            "applied": False,
            "entity": entity.get("name"),
            "changes": []
        }

    entity["meta"] = meta

    ok = save_entity_update(entity)

    return {
        "applied": ok,
        "entity": entity.get("name"),
        "changes": changes
    }


def apply_evolution_to_entities(entity_ids):
    results = []

    for entity_id in entity_ids:
        result = apply_entity_evolution(entity_id)
        results.append(result)

    return results