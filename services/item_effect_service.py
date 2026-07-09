import random


EFFECT_STATS = [
    "combat",
    "defense",
    "damage",
    "resistance",
    "arcane",
    "control",
    "stealth",
    "knowledge",
    "social",
    "influence",
    "initiative"
]


CURSED_DEBUFFS = [
    "risk",
    "control",
    "social",
    "initiative",
    "resistance"
]


RARITY_WEIGHTS = [
    ("Común", 55),
    ("Poco común", 25),
    ("Raro", 12),
    ("Épico", 5),
    ("Legendario", 2),
    ("Maldito", 1)
]


ITEM_TYPE_BIASES = {
    "weapons": [
        "combat",
        "damage",
        "initiative"
    ],

    "armors": [
        "defense",
        "resistance",
        "initiative"
    ],

    "relics": [
        "arcane",
        "influence",
        "control",
        "risk"
    ],

    "magic_systems": [
        "arcane",
        "knowledge",
        "control",
        "risk"
    ],

    "spells": [
        "arcane",
        "damage",
        "control",
        "knowledge",
        "risk"
    ],

    "foods": [
        "resistance",
        "social",
        "risk"
    ],

    "armies": [
        "combat",
        "defense",
        "damage",
        "resistance",
        "initiative",
        "influence",
        "risk"
    ],

    "kingdoms": [
        "influence",
        "social",
        "knowledge",
        "resistance",
        "risk"
    ],

    "creatures": [
        "combat",
        "damage",
        "defense",
        "resistance",
        "stealth",
        "initiative",
        "arcane",
        "risk"
    ]
}


def weighted_choice(options):
    total = sum(weight for _, weight in options)
    roll = random.uniform(0, total)

    current = 0

    for value, weight in options:
        current += weight

        if roll <= current:
            return value

    return options[-1][0]


def choose_rarity():
    return weighted_choice(RARITY_WEIGHTS)


def get_effect_count(rarity):
    if rarity == "Común":
        return 1

    if rarity == "Poco común":
        return random.choice([1, 2])

    if rarity == "Raro":
        return random.choice([2, 2, 3])

    if rarity == "Épico":
        return random.choice([2, 3])

    if rarity == "Legendario":
        return random.choice([3, 4])

    if rarity == "Maldito":
        return random.choice([2, 3, 4])

    return 1


def choose_stat(entity_type):
    biased = ITEM_TYPE_BIASES.get(entity_type, EFFECT_STATS)

    if random.random() < 0.75:
        return random.choice(biased)

    return random.choice(EFFECT_STATS)


def generate_item_effects(entity_type):
    rarity = choose_rarity()
    effect_count = get_effect_count(rarity)

    effects = {}

    for _ in range(effect_count):
        stat = choose_stat(entity_type)

        if stat in effects:
            continue

        if rarity == "Común":
            value = random.choice([1, 1, 2])

        elif rarity == "Poco común":
            value = random.choice([1, 2])

        elif rarity == "Raro":
            value = random.choice([2, 2, 3])

        elif rarity == "Épico":
            value = random.choice([2, 3, 4])

        elif rarity == "Legendario":
            value = random.choice([3, 4, 5])

        elif rarity == "Maldito":
            value = random.choice([3, 4, 5])

        else:
            value = 1

        effects[stat] = value

    # Poco común: a veces trae costo menor
    if rarity == "Poco común" and random.random() < 0.35:
        debuff = random.choice(CURSED_DEBUFFS)
        effects[debuff] = effects.get(debuff, 0) + random.choice([1, 2])

    # Maldito: siempre trae costo fuerte
    if rarity == "Maldito":
        debuff_count = random.choice([1, 2])

        for _ in range(debuff_count):
            debuff = random.choice(CURSED_DEBUFFS)

            if debuff in ["risk"]:
                effects[debuff] = effects.get(debuff, 0) + random.choice([3, 4, 5])
            else:
                effects[debuff] = effects.get(debuff, 0) - random.choice([1, 2, 3])

    # Legendario: casi siempre trae riesgo narrativo
    if rarity == "Legendario" and random.random() < 0.65:
        effects["risk"] = effects.get("risk", 0) + random.choice([1, 2, 3])

    return rarity, effects