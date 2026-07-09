import random

from core.parser import load_all_lists, weighted_choice


DEFAULT_STYLE = "universal"


ENTITY_ALIASES = {
    "npc": "persona",
    "npcs": "persona",
    "character": "persona",
    "characters": "persona",

    "location": "lugar",
    "locations": "lugar",

    "kingdom": "lugar",
    "kingdoms": "lugar",
    "realm": "lugar",
    "realms": "lugar",
    "city": "lugar",
    "cities": "lugar",
    "settlement": "lugar",
    "settlements": "lugar",

    "weapon": "arma",
    "weapons": "arma",

    "armor": "armadura",
    "armors": "armadura",

    "creature": "bestia",
    "creatures": "bestia",

    "faction": "faccion",
    "factions": "faccion",

    "relic": "artefacto",
    "relics": "artefacto",
    "artifact": "artefacto",
    "artifacts": "artefacto",

    "loot": "artefacto"
}


STYLE_ALIASES = {
    "universal": "Universal",
    "fantasy": "Fantasia",
    "dark_fantasy": "FantasiaOscura",
    "cyberpunk": "Cyberpunk",
    "modern": "Moderno",
    "cosmic": "Cosmico"
}


def normalize_entity_type(entity_type):
    key = str(entity_type or "").lower().strip()
    return ENTITY_ALIASES.get(key, key or "persona")


def normalize_style(style):
    key = str(style or DEFAULT_STYLE).lower().strip()
    return STYLE_ALIASES.get(key, "Universal")


def clean_value(value):
    return str(value).split("|")[0].strip()


def roll_from_list(list_name, fallback=None):
    for oracle in load_all_lists():
        if oracle.get("name") != list_name:
            continue

        data = oracle.get("data", {})
        options = []

        if "Resultados" in data:
            options = data["Resultados"]
        else:
            for values in data.values():
                options.extend(values)

        if options:
            return clean_value(weighted_choice(options))

    return fallback or "Sin nombre"


def roll_styled(entity_type, part, style=None, fallback_style="Universal"):
    style_name = normalize_style(style)

    styled_list = f"Nombres-{entity_type}-{part}-{style_name}"
    value = roll_from_list(styled_list, None)

    if value:
        return value

    fallback_list = f"Nombres-{entity_type}-{part}-{fallback_style}"
    return roll_from_list(fallback_list, "Sin nombre")


def generate_entity_name(entity_type, style="universal", gender="Aleatorio"):
    entity_type = normalize_entity_type(entity_type)

    generators = {
        "persona": generate_person_name,
        "lugar": generate_location_name,
        "arma": generate_weapon_name,
        "armadura": generate_armor_name,
        "bestia": generate_creature_name,
        "faccion": generate_faction_name,
        "artefacto": generate_artifact_name
    }

    generator = generators.get(entity_type, generate_generic_name)

    return generator(
        style=style,
        gender=gender
    )


def generate_person_name(style="universal", gender="Aleatorio"):
    gender = str(gender or "Aleatorio").lower().strip()

    if gender in ["male", "masculino", "hombre"]:
        first = roll_styled("Persona", "Masculino", style)
        title = roll_styled("Persona", "Titulo-Masculino", style) or "Señor"

    elif gender in ["female", "femenino", "mujer"]:
        first = roll_styled("Persona", "Femenino", style)
        title = roll_styled("Persona", "Titulo-Femenino", style) or "Señora"

    elif gender in ["neutral", "neutro", "no binario"]:
        first = roll_styled("Persona", "Neutro", style)
        title = roll_styled("Persona", "Titulo-Neutro", style) or "Viajero"

    else:
        option = random.choice(["male", "female", "neutral"])
        return generate_person_name(style=style, gender=option)

    last = roll_styled("Persona", "Apellido", style) or "Sinapellido"
    epithet = roll_styled("Persona", "Epiteto", style) or "sin epíteto"

    pattern = random.choice([
        "{first} {last}",
        "{title} {first} {last}",
        "{first} {last}, {epithet}"
    ])

    return pattern.format(
        first=first,
        last=last,
        title=title,
        epithet=epithet
    ).strip()


def generate_location_name(style="universal", gender="Aleatorio"):
    place_type = roll_styled("Lugar", "Tipo", style)
    root = roll_styled("Lugar", "Raiz", style)
    trait = roll_styled("Lugar", "Rasgo", style)

    pattern = random.choice([
        "{place_type} de {root}",
        "{place_type} {trait}",
        "{place_type} de {root} {trait}"
    ])

    return pattern.format(
        place_type=place_type,
        root=root,
        trait=trait
    )


def generate_weapon_name(style="universal", gender="Aleatorio"):
    weapon_type = roll_styled("Arma", "Tipo", style)
    root = roll_styled("Arma", "Raiz", style)
    epithet = roll_styled("Arma", "Epiteto", style)

    pattern = random.choice([
        "{weapon_type} de {root}",
        "{weapon_type} {epithet}",
        "{weapon_type} de {root}, {epithet}"
    ])

    return pattern.format(
        weapon_type=weapon_type,
        root=root,
        epithet=epithet
    )


def generate_armor_name(style="universal", gender="Aleatorio"):
    armor_type = roll_styled("Armadura", "Tipo", style)
    material = roll_styled("Armadura", "Material", style)
    trait = roll_styled("Armadura", "Rasgo", style)

    pattern = random.choice([
        "{armor_type} de {material}",
        "{armor_type} {trait}",
        "{armor_type} de {material} {trait}"
    ])

    return pattern.format(
        armor_type=armor_type,
        material=material,
        trait=trait
    )


def generate_creature_name(style="universal", gender="Aleatorio"):
    root = roll_styled("Bestia", "Raiz", style)
    trait = roll_styled("Bestia", "Rasgo", style)
    creature_type = roll_styled("Bestia", "Tipo", style)

    pattern = random.choice([
        "{root} {trait}",
        "{creature_type} {trait}",
        "{root}, {creature_type} {trait}"
    ])

    return pattern.format(
        root=root,
        trait=trait,
        creature_type=creature_type
    )


def generate_faction_name(style="universal", gender="Aleatorio"):
    faction_type = roll_styled("Faccion", "Tipo", style)
    symbol = roll_styled("Faccion", "Simbolo", style)
    ideal = roll_styled("Faccion", "Ideal", style)

    pattern = random.choice([
        "{faction_type} de {symbol}",
        "{faction_type} del {ideal}",
        "{faction_type} de {symbol} {ideal}"
    ])

    return pattern.format(
        faction_type=faction_type,
        symbol=symbol,
        ideal=ideal
    )


def generate_artifact_name(style="universal", gender="Aleatorio"):
    artifact_type = roll_styled("Artefacto", "Tipo", style)
    root = roll_styled("Artefacto", "Raiz", style)
    epithet = roll_styled("Artefacto", "Epiteto", style)

    pattern = random.choice([
        "{artifact_type} de {root}",
        "{artifact_type} {epithet}",
        "{artifact_type} de {root}, {epithet}"
    ])

    return pattern.format(
        artifact_type=artifact_type,
        root=root,
        epithet=epithet
    )


def generate_generic_name(style="universal", gender="Aleatorio"):
    prefix = roll_styled("General", "Prefijo", style, fallback_style="Universal")
    root = roll_styled("General", "Raiz", style, fallback_style="Universal")
    suffix = roll_styled("General", "Sufijo", style, fallback_style="Universal")

    parts = [
        part for part in [prefix, root, suffix]
        if part and part.lower().replace(" ", "") != "sinnombre"
    ]

    if not parts:
        return random.choice([
            "Entidad sin registrar",
            "Nombre desconocido",
            "Registro incompleto"
        ])

    return "".join(parts)