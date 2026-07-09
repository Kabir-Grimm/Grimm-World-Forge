from datetime import datetime

from services.entity_registry_service import get_entity_by_id
from services.entity_editor_service import save_entity_update


MAX_MEMORIES = 40


def get_entity_memory(entity_id):
    entity = get_entity_by_id(entity_id)

    if not entity:
        return []

    memory = entity.get("memory", [])

    if not isinstance(memory, list):
        return []

    return memory


def add_memory(
    entity_id,
    memory_type,
    description,
    importance=1,
    year=None,
    source=None
):
    entity = get_entity_by_id(entity_id)

    if not entity:
        return False

    memories = entity.get("memory", [])

    if not isinstance(memories, list):
        memories = []

    memory = {
        "type": memory_type,
        "description": description,
        "importance": importance,
        "year": year,
        "source": source,
        "created_at": datetime.now().isoformat()
    }

    memories.append(memory)

    memories = trim_memories(memories)

    entity["memory"] = memories

    return save_entity_update(entity)


def trim_memories(memories):
    """
    Conserva memorias importantes y recientes.
    """

    memories.sort(
        key=lambda memory: (
            memory.get("importance", 1),
            memory.get("created_at", "")
        ),
        reverse=True
    )

    return memories[:MAX_MEMORIES]


def add_encounter_memory(entity_id, result, perspective):
    """
    Guarda un recuerdo basado en un encuentro.

    perspective:
    - winner
    - loser
    - neutral
    """

    if not entity_id or not result:
        return False

    encounter_type = result.get("encounter_type", "Encuentro")
    risk = result.get("risk", "Moderado")
    context = result.get("context", "")
    year = result.get("year")

    interpretation = result.get(
        "interpretation",
        "Participó en un encuentro importante."
    )

    importance = calculate_memory_importance(
        result,
        perspective
    )

    description = (
        f"{perspective.upper()} en {encounter_type}. "
        f"Riesgo: {risk}. Contexto: {context}. "
        f"{interpretation}"
    )

    return add_memory(
        entity_id=entity_id,
        memory_type=f"encounter_{perspective}",
        description=description,
        importance=importance,
        year=year,
        source="encounter"
    )


def calculate_memory_importance(result, perspective):
    risk = result.get("risk", "Moderado")
    margin = abs(result.get("margin", 0))

    importance = 1

    if risk == "Moderado":
        importance += 1
    elif risk == "Alto":
        importance += 2
    elif risk == "Mortal":
        importance += 3

    if margin > 8:
        importance += 1

    if perspective in ["winner", "loser"]:
        importance += 1

    return min(5, importance)