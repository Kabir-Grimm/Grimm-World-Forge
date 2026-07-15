import json
import os
import uuid
import random
from datetime import datetime

from core.parser import weighted_choice


SPECIES_PATH = "entities/species.json"
SPECIES_ORACLES_PATH = "data/species_oracles.json"
SPECIES_PREFIX = "Raza-"


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except Exception:
            return fallback


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_species():
    data = load_json(SPECIES_PATH, [])
    return data if isinstance(data, list) else []


def save_species_list(species_list):
    save_json(SPECIES_PATH, species_list)


def load_species_oracles():
    possible_paths = [
        "data/species_oracles.json",
        "entities/species_oracles.json",
        "species_oracles.json"
    ]

    raw = None
    used_path = None

    for path in possible_paths:
        if os.path.exists(path):
            raw = load_json(path, {})
            used_path = path
            break

    if not isinstance(raw, dict):
        print("⚠ No se encontró species_oracles.json válido")
        return {}

    print(f"🧬 Oráculos de especie cargados desde: {used_path}")

    oracles = raw.get("oracles", raw)

    if not isinstance(oracles, dict):
        print("⚠ El archivo no contiene un bloque 'oracles' válido")
        return {}

    normalized = {}

    for key, options in oracles.items():
        clean_key = (
            key.replace(SPECIES_PREFIX, "")
            .replace("Características", "Caracteristicas")
            .strip()
        )

        normalized[clean_key] = options

    print("🧬 Oráculos disponibles:", list(normalized.keys()))

    return normalized


def choose_from_options(options):
    if not options:
        return "SIN RESULTADOS"

    normalized = []

    for item in options:
        if isinstance(item, dict):
            value = item.get("value", "SIN RESULTADOS")
            weight = item.get("weight", 1)
            normalized.append((value, weight))

        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            normalized.append((item[0], item[1]))

        else:
            normalized.append((item, 1))

    try:
        return weighted_choice(normalized)
    except Exception:
        return random.choice([item[0] for item in normalized])


def generate_species_name():
    oracles = load_species_oracles()
    origins = oracles.get("Origen", [])

    origin = choose_from_options(origins)

    prefixes = [
        "Vael", "Mor", "Tha", "Zha", "Ely",
        "Kor", "Nyx", "Ara", "Vel", "Orr"
    ]

    suffixes = [
        "thari", "vanni", "rhael", "mora", "keth",
        "dren", "lune", "sari", "nox", "ari"
    ]

    base_name = random.choice(prefixes) + random.choice(suffixes)

    if origin and origin != "SIN RESULTADOS":
        return f"{base_name} de {origin}"

    return base_name


def generate_species_from_oracles(name=None):
    oracles = load_species_oracles()

    data = {
        "Cabeza": choose_from_options(oracles.get("Cabeza", [])),
        "Torso": choose_from_options(oracles.get("Torso", [])),
        "Piernas": choose_from_options(oracles.get("Piernas", [])),
        "Brazos": choose_from_options(oracles.get("Brazos", [])),
        "Características": choose_from_options(oracles.get("Caracteristicas", [])),
        "Origen": choose_from_options(oracles.get("Origen", []))
    }

    species_name = name.strip() if name else generate_species_name()

    species = {
        "id": f"species_{uuid.uuid4().hex[:8]}",
        "name": species_name,
        "type": "species",
        "meta": {
            "created_at": datetime.now().isoformat(),
            "source": "species_oracles"
        },
        "data": data,
        "effects": infer_species_effects(data)
    }

    return species


def infer_species_effects(data):
    text = json.dumps(data, ensure_ascii=False).lower()
    effects = {}

    if "mágic" in text or "magia" in text or "arcano" in text or "rúnic" in text:
        effects["magic"] = effects.get("magic", 0) + 1

    if "fuerte" in text or "musculoso" in text or "golem" in text or "roca" in text:
        effects["strength"] = effects.get("strength", 0) + 1

    if "ágil" in text or "rápido" in text or "veloz" in text or "alas" in text:
        effects["speed"] = effects.get("speed", 0) + 1

    if "sombra" in text or "fantasm" in text or "camuflaje" in text:
        effects["stealth"] = effects.get("stealth", 0) + 1

    if "ojos" in text or "runas" in text or "luminos" in text:
        effects["perception"] = effects.get("perception", 0) + 1

    if "venenos" in text or "hielo" in text or "fuego" in text or "cristal" in text:
        effects["resistance"] = effects.get("resistance", 0) + 1

    if "frágil" in text or "translúcido" in text:
        effects["resistance"] = effects.get("resistance", 0) - 1

    return effects


def save_species(species):
    species_list = load_species()
    species_list.append(species)
    save_species_list(species_list)
    return species.get("id")


def get_species_by_id(species_id):
    for species in load_species():
        if species.get("id") == species_id:
            return species

    return None


def get_random_species():
    species_list = load_species()

    if not species_list:
        species = generate_species_from_oracles()
        save_species(species)
        return species

    return random.choice(species_list)