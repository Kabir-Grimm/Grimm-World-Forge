from services.memory_service import add_encounter_memory
from services.reputation_service import apply_encounter_reputation
from services.encounter_consequence_service import apply_consequence_to_loser


def apply_encounter_persistence(result):
    """
    Aplica consecuencias persistentes de un encuentro:
    - memoria para ganador/perdedor
    - reputación
    - estado/consecuencia al perdedor
    """

    if not result:
        return {
            "memories": [],
            "reputation": [],
            "consequence": None
        }

    applied_memories = []

    winner = result.get("winner")
    loser = result.get("loser")

    if winner:
        winner_entity = winner.get("entity", {})
        winner_id = winner_entity.get("id")

        if winner_id:
            ok = add_encounter_memory(
                winner_id,
                result,
                "winner"
            )

            applied_memories.append({
                "entity": winner_entity.get("name"),
                "perspective": "winner",
                "applied": ok
            })

    if loser:
        loser_entity = loser.get("entity", {})
        loser_id = loser_entity.get("id")

        if loser_id:
            ok = add_encounter_memory(
                loser_id,
                result,
                "loser"
            )

            applied_memories.append({
                "entity": loser_entity.get("name"),
                "perspective": "loser",
                "applied": ok
            })

    reputation_results = apply_encounter_reputation(
        result
    )

    consequence_result = apply_consequence_to_loser(
        result.get("consequence"),
        loser
    )

    return {
        "memories": applied_memories,
        "reputation": reputation_results,
        "consequence": consequence_result
    }