import random

from core.parser import load_all_lists, weighted_choice
from services.entity_registry_service import get_entity_by_id
from services.entity_editor_service import save_entity_update
from services.encounter_resolution_service import (
    resolve_encounter_outcome,
    should_apply_mutual_consequence
)


RISK_LIST_MAP = {
    "Bajo": "Encuentros-Consecuencia-Bajo",
    "Moderado": "Encuentros-Consecuencia-Moderado",
    "Alto": "Encuentros-Consecuencia-Alto",
    "Mortal": "Encuentros-Consecuencia-Mortal"
}


DANGEROUS_DEATH_CONSEQUENCES = {
    "Muerte posible",
    "Derrota irreversible",
    "Sacrificio involuntario",
    "Muerte",
    "Ejecución",
    "Aniquilación"
}


IMPORTANT_VALUES = {
    "Importante",
    "Protagonista",
    "Antagonista",
    "Líder",
    "Héroe",
    "Villano",
    "Entidad clave"
}


CRITICAL_STATES = {
    "Moribundo",
    "Gravemente herido",
    "Mutilado"
}


STATUS_MAP = {
    "Cansancio menor": "Agotado",
    "Herida superficial": "Herido leve",
    "Herida leve": "Herido",
    "Herida grave": "Gravemente herido",
    "Debilitamiento físico": "Debilitado",
    "Trauma psicológico": "Traumatizado",
    "Pérdida de reputación": "Humillado",
    "Humillación pública": "Humillado",
    "Corrupción menor": "Corrupto",
    "Corrupción severa": "Corrupto severo",
    "Captura": "Capturado",
    "Captura definitiva": "Capturado",
    "Desaparición": "Desaparecido",
    "Mutilación": "Mutilado",
    "Colapso mental": "Quebrado",
    "Muerte posible": "Muerto",
    "Muerte": "Muerto",
    "Ejecución": "Muerto",
    "Aniquilación": "Muerto",
    "Derrota irreversible": "Muerto",
    "Sacrificio involuntario": "Muerto"
}


NON_LETHAL_FALLBACKS = {
    "Bajo": ["Herido leve", "Agotado", "Humillado"],
    "Moderado": ["Herido", "Agotado", "Traumatizado"],
    "Alto": ["Gravemente herido", "Capturado", "Mutilado", "Moribundo"],
    "Mortal": ["Moribundo", "Mutilado", "Desaparecido", "Gravemente herido"]
}


def roll_from_list(list_name, fallback):
    for oracle in load_all_lists():
        if oracle["name"] == list_name:
            data = oracle.get("data", {})

            if "Resultados" in data:
                if data["Resultados"]:
                    return weighted_choice(data["Resultados"])

            options = []

            for values in data.values():
                options.extend(values)

            if options:
                return weighted_choice(options)

    return fallback


def get_consequence_list_name(risk):
    return RISK_LIST_MAP.get(
        risk,
        "Encuentros-Consecuencia-Moderado"
    )


def get_severity(risk):
    if risk == "Bajo":
        return "menor"

    if risk == "Moderado":
        return "media"

    if risk == "Alto":
        return "alta"

    if risk == "Mortal":
        return "crítica"

    return "media"


def get_margin_modifier(margin):
    abs_margin = abs(margin)

    if margin == 0:
        return "empate"

    if abs_margin <= 3:
        return "victoria ajustada"

    if abs_margin <= 8:
        return "victoria clara"

    return "victoria aplastante"


def get_context_value(result, key, default=0):
    modifiers = result.get("context_modifiers", {})

    if not isinstance(modifiers, dict):
        return default

    return modifiers.get(key, default)


def generate_encounter_consequence(risk, margin, encounter_result=None):
    """
    Genera una consecuencia sugerida.
    Si recibe encounter_result, también calcula resolución avanzada.
    """

    base_result = encounter_result or {
        "risk": risk,
        "margin": margin,
        "context_modifiers": {}
    }

    resolution = resolve_encounter_outcome(base_result)

    list_name = get_consequence_list_name(risk)

    consequence = roll_from_list(
        list_name,
        "Consecuencia narrativa abierta"
    )

    severity = get_severity(risk)
    modifier = get_margin_modifier(margin)

    danger_score = resolution.get("danger_score", 0)

    if resolution.get("outcome_type") == "aniquilación mutua":
        consequence = "Muerte posible"
    elif danger_score >= 18 and risk == "Mortal":
        if random.randint(1, 100) <= 35:
            consequence = "Muerte posible"
    elif danger_score >= 14 and risk in ["Alto", "Mortal"]:
        if consequence not in STATUS_MAP:
            consequence = random.choice([
                "Herida grave",
                "Mutilación",
                "Captura",
                "Trauma psicológico"
            ])

    return {
        "risk": risk,
        "margin": margin,
        "severity": severity,
        "modifier": modifier,
        "consequence": consequence,
        "resolution": resolution,
        "description": (
            f"{consequence} "
            f"({severity}, {modifier}; "
            f"{resolution.get('outcome_type')})"
        )
    }


def is_important_entity(entity):
    meta = entity.get("meta", {})

    if not isinstance(meta, dict):
        return False

    importance = meta.get("importance", "Común")

    return importance in IMPORTANT_VALUES


def get_entity_status(entity):
    meta = entity.get("meta", {})

    if not isinstance(meta, dict):
        return "Sano"

    return meta.get("status", "Sano")


def get_death_probability(status, risk, margin, danger_score, entity):
    abs_margin = abs(margin)
    important = is_important_entity(entity)

    probability = 0

    if risk == "Bajo":
        probability = 0
    elif risk == "Moderado":
        probability = 0
    elif risk == "Alto":
        probability = 5
    elif risk == "Mortal":
        probability = 20

    if abs_margin > 8:
        probability += 20
    elif abs_margin > 3:
        probability += 8

    if danger_score >= 18:
        probability += 20
    elif danger_score >= 14:
        probability += 10

    if status in CRITICAL_STATES:
        probability += 25

    if important:
        probability -= 25

    if status == "Moribundo" and risk == "Mortal":
        probability += 20

    return max(0, min(90, probability))


def should_die(status, risk, margin, danger_score, entity):
    probability = get_death_probability(
        status,
        risk,
        margin,
        danger_score,
        entity
    )

    roll = random.randint(1, 100)

    return roll <= probability, probability, roll


def choose_protected_state(risk, margin, entity):
    status = get_entity_status(entity)
    abs_margin = abs(margin)

    if status in {"Gravemente herido", "Mutilado"}:
        return "Moribundo"

    if risk == "Bajo":
        return random.choice(NON_LETHAL_FALLBACKS["Bajo"])

    if risk == "Moderado":
        return random.choice(NON_LETHAL_FALLBACKS["Moderado"])

    if risk == "Alto":
        if abs_margin <= 3:
            return "Herido"
        if abs_margin <= 8:
            return random.choice(["Gravemente herido", "Capturado"])
        return random.choice(NON_LETHAL_FALLBACKS["Alto"])

    if risk == "Mortal":
        if abs_margin <= 3:
            return random.choice(["Gravemente herido", "Moribundo"])
        if abs_margin <= 8:
            return random.choice(["Moribundo", "Mutilado", "Desaparecido"])
        return random.choice(NON_LETHAL_FALLBACKS["Mortal"])

    return "Herido"


def apply_status_to_entity(entity, status):
    meta = entity.get("meta", {})

    if not isinstance(meta, dict):
        meta = {}

    meta["status"] = status

    if status in {
        "Muerto",
        "Desaparecido",
        "Derrotado"
    }:
        meta["active"] = False

    entity["meta"] = meta

    return save_entity_update(entity)


def apply_consequence_to_entity(consequence_data, target):
    if not target:
        return None

    entity_summary = target.get("entity", {})
    entity_id = entity_summary.get("id")

    if not entity_id:
        return None

    full_entity = get_entity_by_id(entity_id)

    if not full_entity:
        return None

    consequence = consequence_data.get("consequence")
    risk = consequence_data.get("risk", "Moderado")
    margin = consequence_data.get("margin", 0)
    resolution = consequence_data.get("resolution", {})
    danger_score = resolution.get("danger_score", 0)

    status = STATUS_MAP.get(consequence)

    if not status:
        return {
            "applied": False,
            "entity": full_entity.get("name"),
            "reason": "La consecuencia no modifica estado directamente."
        }

    if status == "Muerto":
        current_status = get_entity_status(full_entity)

        dies, probability, roll = should_die(
            current_status,
            risk,
            margin,
            danger_score,
            full_entity
        )

        if not dies:
            status = choose_protected_state(
                risk,
                margin,
                full_entity
            )

            reason = (
                f"Muerte evitada. Tirada {roll}/100 "
                f"contra probabilidad {probability}%. "
                f"Estado alternativo: {status}."
            )
        else:
            reason = (
                f"Muerte aplicada. Tirada {roll}/100 "
                f"contra probabilidad {probability}%."
            )
    else:
        reason = "Consecuencia aplicada."

    ok = apply_status_to_entity(full_entity, status)

    if not ok:
        return {
            "applied": False,
            "entity": full_entity.get("name"),
            "reason": "No se pudo guardar la entidad."
        }

    return {
        "applied": True,
        "entity": full_entity.get("name"),
        "status": status,
        "reason": reason
    }


def apply_consequence_to_loser(consequence_data, loser):
    return apply_consequence_to_entity(
        consequence_data,
        loser
    )


def apply_mutual_consequence_if_needed(consequence_data, result):
    resolution = consequence_data.get("resolution", {})

    if not should_apply_mutual_consequence(resolution):
        return []

    applications = []

    actor_a = result.get("actor_a")
    actor_b = result.get("actor_b")

    risk = consequence_data.get("risk", "Moderado")

    mutual_consequence = {
        **consequence_data,
        "consequence": random.choice([
            "Herida leve",
            "Herida grave",
            "Trauma psicológico",
            "Debilitamiento físico"
        ])
    }

    if risk == "Mortal" and resolution.get("danger_score", 0) >= 18:
        mutual_consequence["consequence"] = random.choice([
            "Herida grave",
            "Mutilación",
            "Muerte posible"
        ])

    for actor in [actor_a, actor_b]:
        application = apply_consequence_to_entity(
            mutual_consequence,
            actor
        )

        if application:
            applications.append(application)

    return applications