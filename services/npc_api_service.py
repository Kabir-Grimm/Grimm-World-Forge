import random
from contextlib import redirect_stdout
from io import StringIO

from core.parser import load_all_lists, weighted_choice
from services.entity_registry_service import (
    clear_registry_cache,
    load_registry_entities,
)
from services.entity_service import save_entity
from services.name_generator_service import generate_entity_name
from services.npc_loadout_service import generate_npc_loadout
from services.species_service import (
    generate_species_from_oracles,
    get_random_species,
    get_species_by_id,
    load_species,
    save_species,
)
from services.world_service import add_entity_to_world, load_worlds


NPC_PREFIX = "NPC-"

IMPORTANCE_OPTIONS = [
    "Comun",
    "Importante",
    "Protagonista",
    "Antagonista",
    "Lider",
    "Heroe",
    "Villano",
    "Entidad clave",
]

POWER_RANK_OPTIONS = [
    "Aleatorio",
    "Debil",
    "Comun",
    "Competente",
    "Fuerte",
    "Excepcional",
    "Legendario",
]

ROLE_OPTIONS = [
    "Neutral",
    "Aliado",
    "Rival",
    "Mentor",
    "Enemigo",
    "Gobernante",
    "Mercenario",
    "Guardian",
    "Profeta",
    "Agente oculto",
]

STYLE_OPTIONS = [
    "universal",
    "fantasy",
    "dark_fantasy",
    "cyberpunk",
    "modern",
    "cosmic",
]


def clean_roll(value):
    return str(value or "").split("|")[0].strip()


def get_npc_oracles():
    return [
        oracle
        for oracle in load_all_lists()
        if oracle.get("name", "").startswith(NPC_PREFIX)
    ]


def roll_oracle(oracle):
    data = oracle.get("data", {})

    if "Resultados" in data:
        return clean_roll(weighted_choice(data["Resultados"]))

    results = {}

    for subcategory, options in data.items():
        results[subcategory] = clean_roll(weighted_choice(options))

    return results


def generate_oracle_data(selected_categories=None):
    selected = set(selected_categories or [])
    generated_data = {}

    for oracle in get_npc_oracles():
        name = oracle.get("name", "")

        if selected and name not in selected:
            continue

        category = name.replace(NPC_PREFIX, "")
        rolled = roll_oracle(oracle)

        if isinstance(rolled, dict):
            for key, value in rolled.items():
                generated_data[f"{category} - {key}"] = value
        else:
            generated_data[category] = rolled

    return generated_data


def generate_gender(requested_gender=None):
    if requested_gender and requested_gender != "Aleatorio":
        return requested_gender

    for oracle in load_all_lists():
        if oracle.get("name") != "NPC-Genero":
            continue

        options = oracle.get("data", {}).get("Resultados", [])

        if options:
            return clean_roll(weighted_choice(options))

    return "Desconocido"


def generate_age():
    age = random.randint(16, 80)

    if age < 18:
        life_stage = "Adolescencia"
    elif age < 30:
        life_stage = "Juventud"
    elif age < 50:
        life_stage = "Adultez"
    elif age < 70:
        life_stage = "Madurez"
    else:
        life_stage = "Vejez"

    return age, life_stage


def resolve_species(selection):
    def quiet_call(fn, *args):
        with redirect_stdout(StringIO()):
            return fn(*args)

    if selection == "none":
        return None

    if selection == "generate_new":
        species = quiet_call(generate_species_from_oracles)
        save_species(species)
        return species

    if selection and selection not in ["random_saved", "legacy_oracle"]:
        return get_species_by_id(selection)

    return quiet_call(get_random_species)


def species_to_summary(species):
    if not species:
        return None

    return {
        "id": species.get("id"),
        "name": species.get("name"),
        "type": "species",
        "data": species.get("data", {}),
        "effects": species.get("effects", {}),
    }


def generate_npc(payload=None):
    payload = payload or {}

    importance = payload.get("importance") or "Comun"
    role = payload.get("role") or "Neutral"
    power_rank = payload.get("power_rank") or "Aleatorio"
    style = payload.get("style") or "universal"
    gender = generate_gender(payload.get("gender") or "Aleatorio")
    species = resolve_species(payload.get("species_id") or "random_saved")
    age, life_stage = generate_age()

    name = payload.get("name") or generate_entity_name(
        entity_type="npcs",
        style=style,
        gender=gender,
    )

    data = generate_oracle_data(payload.get("categories"))

    if species:
        species_name = species.get("name", "Especie desconocida")
        data["Raza"] = species_name
        data["Especie"] = species_name
        data["Datos de especie"] = species.get("data", {})
        data["Efectos de especie"] = species.get("effects", {})

    loadout = generate_npc_loadout(
        role=role,
        power_rank=power_rank,
        importance=importance,
        include_equipment=payload.get("include_equipment", True),
        include_abilities=payload.get("include_abilities", True),
        include_magic=payload.get("include_magic", True),
    )

    data["Equipo inicial"] = loadout.get("equipment", {})
    data["Habilidades"] = loadout.get("abilities", [])
    data["Magia/Poderes"] = loadout.get("magic", {})

    meta = {
        "importance": importance,
        "role": role,
        "power_rank": power_rank,
        "status": payload.get("status") or "Sano",
        "active": True,
        "age": str(age),
        "life_stage": life_stage,
        "gender": gender,
        "traits": payload.get("traits") or [],
    }

    if species:
        meta["species"] = species_to_summary(species)

    return {
        "name": name,
        "type": "npcs",
        "meta": meta,
        "data": data,
        "effects": species.get("effects", {}) if species else {},
    }


def save_npc(entity, world_id=None):
    entity = dict(entity or {})
    entity.setdefault("type", "npcs")
    entity.setdefault("data", {})
    entity.setdefault("meta", {})

    entity_id = save_entity("npcs", entity)
    entity["id"] = entity_id
    clear_registry_cache()

    if world_id:
        add_entity_to_world(world_id, entity)

    return entity


def list_npcs():
    return [
        entity
        for entity in load_registry_entities(profile="editor", include_default=True)
        if entity.get("type") == "npcs"
    ]


def get_options():
    return {
        "categories": [
            {"id": oracle.get("name"), "label": oracle.get("name", "").replace(NPC_PREFIX, "")}
            for oracle in get_npc_oracles()
        ],
        "genders": ["Aleatorio", "Masculino", "Femenino", "Neutro"],
        "importance": IMPORTANCE_OPTIONS,
        "power_ranks": POWER_RANK_OPTIONS,
        "roles": ROLE_OPTIONS,
        "styles": STYLE_OPTIONS,
        "species": [
            {"id": "random_saved", "name": "Aleatoria guardada"},
            {"id": "generate_new", "name": "Generar nueva especie"},
            {"id": "none", "name": "Sin especie"},
        ] + [
            {"id": species.get("id"), "name": species.get("name")}
            for species in load_species()
        ],
        "worlds": [
            {"id": world.get("id"), "name": world.get("name")}
            for world in load_worlds()
        ],
    }
