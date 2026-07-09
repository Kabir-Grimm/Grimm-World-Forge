import random


def get_context_value(result, key, default=0):
    modifiers = result.get("context_modifiers", {})

    if not isinstance(modifiers, dict):
        return default

    return modifiers.get(key, default)


def classify_margin(margin):
    abs_margin = abs(margin)

    if margin == 0:
        return "empate"

    if abs_margin <= 3:
        return "victoria ajustada"

    if abs_margin <= 8:
        return "victoria clara"

    return "victoria aplastante"


def calculate_danger_score(result):
    risk = result.get("risk", "Moderado")
    margin = abs(result.get("margin", 0))

    score = 0

    if risk == "Moderado":
        score += 2
    elif risk == "Alto":
        score += 5
    elif risk == "Mortal":
        score += 8

    if margin <= 3:
        score += 1
    elif margin <= 8:
        score += 3
    else:
        score += 5

    score += get_context_value(result, "risk", 0)
    score += get_context_value(result, "death_risk", 0)
    score += get_context_value(result, "injury_risk", 0)

    return score


def calculate_mutual_damage_chance(result):
    margin = abs(result.get("margin", 0))
    risk = result.get("risk", "Moderado")

    chance = 0

    if margin == 0:
        chance += 45
    elif margin <= 3:
        chance += 30
    elif margin <= 8:
        chance += 15
    else:
        chance += 5

    if risk == "Alto":
        chance += 10
    elif risk == "Mortal":
        chance += 20

    chance += get_context_value(result, "mutual_damage", 0) * 8

    return max(0, min(90, chance))


def resolve_encounter_outcome(result):
    margin = result.get("margin", 0)
    risk = result.get("risk", "Moderado")

    classification = classify_margin(margin)
    danger_score = calculate_danger_score(result)

    mutual_chance = calculate_mutual_damage_chance(result)
    mutual_roll = random.randint(1, 100)

    mutual_damage = mutual_roll <= mutual_chance

    if margin == 0:
        if danger_score >= 14:
            outcome_type = "aniquilación mutua"
        elif mutual_damage:
            outcome_type = "empate con heridas"
        else:
            outcome_type = "empate"
    else:
        if mutual_damage and danger_score >= 16:
            outcome_type = "victoria devastadora con daño mutuo"
        elif mutual_damage:
            outcome_type = "victoria costosa"
        else:
            outcome_type = classification

    return {
        "outcome_type": outcome_type,
        "margin_classification": classification,
        "danger_score": danger_score,
        "mutual_damage": mutual_damage,
        "mutual_damage_chance": mutual_chance,
        "mutual_damage_roll": mutual_roll,
        "risk": risk,
        "margin": margin
    }


def should_apply_mutual_consequence(resolution):
    return resolution.get("mutual_damage") is True