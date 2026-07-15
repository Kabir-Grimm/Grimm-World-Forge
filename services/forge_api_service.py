from datetime import datetime
import json
import os
import random

from core.parser import load_all_lists, weighted_choice
from services.entity_editor_service import save_entity_update
from services.entity_registry_service import clear_registry_cache, get_entity_by_id, load_registry_entities
from services.entity_service import save_entity
from services.equipment_service import EQUIPMENT_RELATIONS, get_equipment_for_entity, load_all_equipment
from services.echoes_service import generate_echo, save_echo_as_event
from services.name_generator_service import generate_entity_name
from services.relation_service import create_relation, delete_relation, load_relations, update_relation
from services.species_service import generate_species_from_oracles, load_species, save_species
from services.spell_component_service import COMPONENT_FILES, format_spell_for_display, generate_modular_spell, load_component
from services.world_map_service import add_or_update_node, load_world_map, remove_node, save_map_nodes, update_node_position
from services.world_service import add_entity_to_world, load_worlds, save_world, save_worlds
from services.world_simulation_service import advance_world_turn


MODULES = [
    {"key": "general_oracle", "label": "Oraculo General", "icon": "dice", "kind": "oracle"},
    {"key": "dice", "label": "Lanzar Dados", "icon": "dice", "kind": "tool"},
    {"key": "characters", "label": "Personajes", "icon": "user", "kind": "special", "entity_type": "npcs", "prefix": "NPC-"},
    {"key": "species", "label": "Razas / Especies", "icon": "sparkles", "kind": "special", "entity_type": "species", "prefix": "Raza-"},
    {"key": "equipment", "label": "Equipo / Artefactos", "icon": "shield", "kind": "generator", "entity_type": "items", "prefix": "Objetos-"},
    {"key": "loot", "label": "Loot", "icon": "gem", "kind": "generator", "entity_type": "loot", "prefix": "Loot-"},
    {"key": "locations", "label": "Ubicaciones / Territorios", "icon": "map-pin", "kind": "generator", "entity_type": "locations", "prefix": ["Ubicacion-", "Ubicación-", "Creador de ubicaciones"]},
    {"key": "relations", "label": "Relaciones", "icon": "link", "kind": "generator", "entity_type": "relations", "prefix": "Relaciones-"},
    {"key": "relation_graph", "label": "Mapa de Relaciones", "icon": "network", "kind": "view"},
    {"key": "entity_editor", "label": "Editor de Entidades", "icon": "edit", "kind": "editor"},
    {"key": "worlds", "label": "Mundos", "icon": "globe", "kind": "editor", "entity_type": "worlds"},
    {"key": "world_map", "label": "Mapa de Mundo", "icon": "map", "kind": "view"},
    {"key": "power_systems", "label": "Sistemas de Poder", "icon": "wand", "kind": "generator", "entity_type": "magic_systems", "prefix": "Magia-"},
    {"key": "spell_forge", "label": "Forja de Hechizos", "icon": "triangle", "kind": "generator", "entity_type": "generated_spells"},
    {"key": "powers", "label": "Poderes / Tecnicas", "icon": "bolt", "kind": "generator", "entity_type": "spells", "prefix": "Hechizo-"},
    {"key": "consumables", "label": "Recursos / Consumibles", "icon": "leaf", "kind": "generator", "entity_type": "foods", "prefix": "Objetos-Comida-"},
    {"key": "weapons", "label": "Armas", "icon": "swords", "kind": "generator", "entity_type": "weapons", "prefix": "Objetos-Armas-"},
    {"key": "armors", "label": "Armaduras / Proteccion", "icon": "shield", "kind": "generator", "entity_type": "armors", "prefix": "Objetos-Armadura-"},
    {"key": "artifacts", "label": "Artefactos", "icon": "archive", "kind": "generator", "entity_type": "relics", "prefix": "Objetos-Reliquia-"},
    {"key": "factions", "label": "Facciones / Organizaciones", "icon": "flag", "kind": "generator", "entity_type": "factions", "prefix": "Faccion-"},
    {"key": "creatures", "label": "Seres / Criaturas", "icon": "sparkles", "kind": "generator", "entity_type": "creatures", "prefix": "Criaturas-"},
    {"key": "forces", "label": "Fuerzas", "icon": "swords", "kind": "generator", "entity_type": "armies", "prefix": "Ejercito-"},
    {"key": "simulation", "label": "Simulacion", "icon": "activity", "kind": "view"},
    {"key": "echoes", "label": "Ecos Narrativos", "icon": "sparkles", "kind": "generator", "entity_type": "echoes", "prefix": "Ecos-"},
    {"key": "encounters", "label": "Confrontaciones", "icon": "swords", "kind": "generator", "entity_type": "events", "prefix": "Encuentros-"},
    {"key": "dramatic_battles", "label": "Confrontaciones Dramaticas", "icon": "swords", "kind": "generator", "entity_type": "events", "prefix": "BatallaEpica-"},
    {"key": "maintenance", "label": "Mantenimiento", "icon": "settings", "kind": "tool"},
]


NAME_TYPES = {
    "locations": "locations",
    "weapons": "weapons",
    "armors": "armors",
    "creatures": "creatures",
    "factions": "factions",
    "relics": "relics",
    "magic_systems": "artefacto",
    "spells": "artefacto",
    "foods": "artefacto",
    "items": "artefacto",
    "loot": "artefacto",
    "armies": "factions",
}


GENERAL_ORACLE_ACTION = "Oraculo General - Accion"
GENERAL_ORACLE_SUBJECT = "Oraculo General - Sujeto"
DICE_SIDES = [3, 4, 6, 8, 10, 12, 20, 100]
LOOT_FOCUS_OPTIONS = [
    "Aleatorio",
    "Recompensa menor",
    "Recompensa importante",
    "Botin comun",
    "Hallazgo extraño",
    "Objeto narrativo",
    "Objeto peligroso",
    "Objeto valioso",
]


def get_module(key):
    for module in MODULES:
        if module["key"] == key:
            return module

    return None


def clean_roll(value):
    return str(value or "").split("|")[0].strip()


def get_all_oracles():
    return load_all_lists()


def get_oracles_for_module(module):
    prefix = module.get("prefix")

    if module.get("kind") == "oracle" and not prefix:
        return get_all_oracles()

    if not prefix:
        return []

    prefixes = prefix if isinstance(prefix, list) else [prefix]

    return [
        oracle
        for oracle in get_all_oracles()
        if any(oracle.get("name", "").startswith(item) for item in prefixes)
    ]


def roll_oracle(oracle):
    data = oracle.get("data", {})

    if "Resultados" in data:
        return clean_roll(weighted_choice(data["Resultados"]))

    rolled = {}

    for key, options in data.items():
        rolled[key] = clean_roll(weighted_choice(options))

    return rolled


def find_oracle(name):
    for oracle in get_all_oracles():
        if oracle.get("name") == name:
            return oracle

    return None


def roll_named_oracle(name):
    oracle = find_oracle(name)

    if not oracle:
        return "NO ENCONTRADO"

    rolled = roll_oracle(oracle)

    if isinstance(rolled, dict):
        values = [value for value in rolled.values() if value]
        return values[0] if values else "SIN RESULTADOS"

    return rolled


def format_general_oracle(oracle_data):
    return (
        "══════════════════════\n"
        "🎲 ORÁCULO GENERAL\n"
        f"🕒 {oracle_data.get('timestamp')}\n"
        "══════════════════════\n\n"
        f"Acción: {oracle_data.get('Acción')}\n"
        f"Objetivo: {oracle_data.get('Objetivo')}\n\n"
        "Interpretación:\n"
        f"{oracle_data.get('Interpretación')}"
    )


def consult_general_oracle():
    action = roll_named_oracle(GENERAL_ORACLE_ACTION)
    subject = roll_named_oracle(GENERAL_ORACLE_SUBJECT)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    interpretation = (
        f"Algo relacionado con '{subject}' debe "
        f"'{str(action).lower()}' o ser afectado por esa acción."
    )
    data = {
        "Acción": action,
        "Objetivo": subject,
        "Interpretación": interpretation,
        "timestamp": timestamp,
    }

    return {
        "ok": True,
        "data": data,
        "display": format_general_oracle(data),
    }


def format_dice_roll(dice_data):
    return (
        "══════════════════════\n"
        f"🕒 {dice_data.get('timestamp')}\n"
        f"🎲 D{dice_data.get('sides')} x{dice_data.get('count')}\n"
        f"Resultados: {dice_data.get('results')}\n"
        f"Total: {dice_data.get('total')}\n"
        "══════════════════════"
    )


def roll_dice_payload(payload):
    sides = int(payload.get("sides") or 20)
    if sides not in DICE_SIDES:
        sides = 20

    count = max(1, min(int(payload.get("count") or 1), 100))
    results = [random.randint(1, sides) for _ in range(count)]
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sides": sides,
        "count": count,
        "results": results,
        "total": sum(results),
    }

    return {
        "ok": True,
        "data": data,
        "display": format_dice_roll(data),
    }


def format_species(species):
    lines = [
        "══════════════════════",
        f"🧬 ESPECIE GENERADA: {species.get('name')}",
        "══════════════════════",
        f"ID provisional: {species.get('id')}",
        "",
        "Características:",
    ]

    for key, value in species.get("data", {}).items():
        lines.append(f"- {key}: {value}")

    effects = species.get("effects", {})
    if effects:
        lines.extend(["", "Efectos inferidos:"])
        for key, value in effects.items():
            sign = "+" if isinstance(value, int) and value >= 0 else ""
            lines.append(f"- {key}: {sign}{value}")

    return "\n".join(lines)


def generate_loot_name(loot):
    category = loot.get("Categoría", "")
    rarity = loot.get("Rareza", "")
    state = loot.get("Estado", "")
    form = loot.get("Forma", "")

    if rarity in ["Legendario", "Único", "Último conocido", "Prohibido", "Irrepetible"]:
        return f"{category} {str(rarity).lower()}"

    if state in ["Sellado", "Inestable", "Corrupto", "Casi destruido", "Dañado gravemente"]:
        return f"{category} {str(state).lower()}"

    return f"{category} - {form}"


def get_loot_focus(selected):
    if selected and selected != "Aleatorio":
        return selected

    return weighted_choice([
        ("Recompensa menor", 6),
        ("Botín común", 6),
        ("Recompensa importante", 3),
        ("Hallazgo extraño", 3),
        ("Objeto narrativo", 3),
        ("Objeto peligroso", 2),
        ("Objeto valioso", 4),
    ])


def generate_single_loot(payload):
    loot = {
        "Enfoque": get_loot_focus(payload.get("focus") or "Aleatorio"),
        "Categoría": roll_named_oracle("Loot-Categoria"),
        "Forma": roll_named_oracle("Loot-Forma-General"),
        "Rareza": roll_named_oracle("Loot-Rareza"),
        "Estado": roll_named_oracle("Loot-Estado"),
        "Origen": roll_named_oracle("Loot-Origen"),
        "Propiedad": roll_named_oracle("Loot-Propiedad"),
    }

    if payload.get("include_story", True):
        loot["Historia"] = roll_named_oracle("Loot-Historia")

    if payload.get("include_complication", True):
        loot["Complicación"] = roll_named_oracle("Loot-Complicacion")

    loot["Nombre sugerido"] = generate_loot_name(loot)
    return loot


def format_loot(generated):
    lines = ["💎 LOOT GENERADO", ""]

    for index, loot in enumerate(generated, start=1):
        lines.extend([
            "══════════════════",
            f"💎 HALLAZGO {index}",
            "══════════════════",
        ])
        for key, value in loot.items():
            lines.append(f"{key}: {value}")
        lines.append("")

    return "\n".join(lines)


def loot_meta(generated_data, focus):
    if isinstance(generated_data, dict) and "Rareza" in generated_data:
        return {
            "focus": generated_data.get("Enfoque", "Desconocido"),
            "category": generated_data.get("Categoría", "Desconocida"),
            "rarity": generated_data.get("Rareza", "Desconocida"),
            "state": generated_data.get("Estado", "Desconocido"),
            "active": True,
        }

    return {
        "focus": focus,
        "category": "Múltiple",
        "rarity": "Variable",
        "state": "Variable",
        "active": True,
    }


def generate_module_entity(key, payload=None):
    payload = payload or {}
    module = get_module(key)

    if not module:
        raise ValueError("Modulo no encontrado")

    if key == "dice":
        return generate_dice_result(payload)

    if key == "spell_forge":
        spell = generate_modular_spell()
        return {
            "name": spell.get("name", "Hechizo sin nombre"),
            "type": "generated_spells",
            "meta": {
                "module": key,
                "label": module["label"],
                "generated_at": datetime.now().isoformat(),
                "risk": spell.get("risk", 0),
            },
            "data": {
                **spell.get("data", {}),
                "Componentes": spell.get("components", {}),
                "Blueprint": spell.get("blueprint", {}),
            },
            "effects": spell.get("effects", {}),
        }

    if key == "worlds":
        world_name = payload.get("name") or f"Mundo {datetime.now().strftime('%H%M%S')}"
        return {
            "name": world_name,
            "type": "worlds",
            "meta": {
                "module": key,
                "generated_at": datetime.now().isoformat(),
            },
            "data": {
                "Descripcion": payload.get("description") or "Mundo creado desde la interfaz web integrada.",
                "entities": [],
            },
        }

    if key == "world_map":
        world_map = load_world_map()
        entities = load_registry_entities(profile="world", include_default=True)
        return {
            "name": "Mapa de Mundo",
            "type": "world_map",
            "meta": {
                "module": key,
                "generated_at": datetime.now().isoformat(),
            },
            "data": {
                "Nodos": world_map.get("nodes", []),
                "Entidades disponibles": [
                    {"id": item.get("id"), "name": item.get("name"), "type": item.get("type")}
                    for item in entities[:60]
                ],
                "created_at": world_map.get("created_at"),
                "updated_at": world_map.get("updated_at"),
            },
        }

    if key in ["relation_graph", "relations"]:
        relations = load_relations()
        return {
            "name": module["label"],
            "type": "relations",
            "meta": {
                "module": key,
                "generated_at": datetime.now().isoformat(),
            },
            "data": {
                "Relaciones": relations,
                "Total": len(relations),
            },
        }

    if key == "simulation":
        result = advance_world_turn()
        return {
            "name": "Turno de simulacion",
            "type": "simulation",
            "meta": {
                "module": key,
                "generated_at": datetime.now().isoformat(),
                "world_date": result.get("world_date"),
            },
            "data": result,
        }

    if key == "entity_editor":
        entities = load_registry_entities(profile="editor", include_default=True)
        return {
            "name": "Editor de Entidades",
            "type": "entity_editor",
            "meta": {
                "module": key,
                "generated_at": datetime.now().isoformat(),
            },
            "data": {
                "Entidades": [
                    {"id": item.get("id"), "name": item.get("name"), "type": item.get("type")}
                    for item in entities[:100]
                ],
                "Total": len(entities),
            },
        }

    if key == "maintenance":
        return generate_maintenance_report()

    selected = set(payload.get("categories") or [])
    generated_data = {}

    for oracle in get_oracles_for_module(module):
        oracle_name = oracle.get("name", "")

        if selected and oracle_name not in selected:
            continue

        prefix = module.get("prefix", "")
        prefixes = prefix if isinstance(prefix, list) else [prefix]
        label = oracle_name

        for item in prefixes:
            label = label.replace(item, "")
        rolled = roll_oracle(oracle)

        if isinstance(rolled, dict):
            for subkey, value in rolled.items():
                generated_data[f"{label} - {subkey}"] = value
        else:
            generated_data[label] = rolled

    entity_type = module.get("entity_type", key)
    name = payload.get("name") or generate_name(entity_type)

    return {
        "name": name,
        "type": entity_type,
        "meta": {
            "module": key,
            "label": module["label"],
            "generated_at": datetime.now().isoformat(),
        },
        "data": generated_data,
    }


def generate_dice_result(payload):
    sides = int(payload.get("sides") or 20)
    count = int(payload.get("count") or 1)
    modifier = int(payload.get("modifier") or 0)
    rolls = [random.randint(1, sides) for _ in range(max(1, min(count, 100)))]
    total = sum(rolls) + modifier

    return {
        "name": f"Tirada {count}d{sides}",
        "type": "roll",
        "meta": {
            "module": "dice",
            "generated_at": datetime.now().isoformat(),
        },
        "data": {
            "Dado": f"d{sides}",
            "Cantidad": count,
            "Modificador": modifier,
            "Resultados": rolls,
            "Total": total,
        },
    }


def generate_maintenance_report():
    report = {}

    for root, _dirs, files in os.walk("entities"):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    count = len(data.keys())
                else:
                    count = 1

                report[path] = {
                    "estado": "ok",
                    "registros": count,
                }
            except Exception as exc:
                report[path] = {
                    "estado": "error",
                    "error": str(exc),
                }

    return {
        "name": "Reporte de mantenimiento",
        "type": "maintenance",
        "meta": {
            "module": "maintenance",
            "generated_at": datetime.now().isoformat(),
        },
        "data": report,
    }


def generate_name(entity_type):
    name_type = NAME_TYPES.get(entity_type, entity_type)

    try:
        return generate_entity_name(name_type, style="universal", gender="Aleatorio")
    except Exception:
        return f"{entity_type}_sin_nombre"


def save_module_entity(entity, world_id=None):
    entity = dict(entity or {})
    entity_type = entity.get("type") or "entity"

    if entity_type == "worlds":
        world_data = {
            "name": entity.get("name", "Mundo sin nombre"),
            "description": entity.get("data", {}).get("Descripcion", ""),
            "entities": entity.get("data", {}).get("entities", []),
        }
        entity_id = save_world(world_data)
        entity["id"] = entity_id
        clear_registry_cache()
        return entity

    entity_id = save_entity(entity_type, entity)
    entity["id"] = entity_id
    clear_registry_cache()

    if world_id:
        add_entity_to_world(world_id, entity)

    return entity


def list_module_entities(entity_type=None):
    entities = load_registry_entities(profile="editor", include_default=True)

    if entity_type:
        return [
            entity
            for entity in entities
            if entity.get("type") == entity_type
        ]

    return entities


def get_module_options(key):
    module = get_module(key)

    if not module:
        raise ValueError("Modulo no encontrado")

    oracles = get_oracles_for_module(module)

    return {
        "module": module,
        "categories": [
            {
                "id": oracle.get("name"),
                "label": clean_module_label(oracle.get("name", ""), module.get("prefix", "")),
            }
            for oracle in oracles
        ],
        "worlds": [
            {"id": world.get("id"), "name": world.get("name")}
            for world in load_worlds()
        ],
    }


def clean_module_label(name, prefix):
    prefixes = prefix if isinstance(prefix, list) else [prefix]
    label = name

    for item in prefixes:
        label = label.replace(item, "")

    return label


def get_shell_options():
    return {
        "modules": MODULES,
        "worlds": [
            {"id": world.get("id"), "name": world.get("name")}
            for world in load_worlds()
        ],
    }


def compact_entity(entity):
    return {
        "id": entity.get("id"),
        "name": entity.get("name", "Sin nombre"),
        "type": entity.get("type", "entity"),
        "meta": entity.get("meta", {}),
        "data": entity.get("data", {}),
        "effects": entity.get("effects", {}),
        "_source_file": entity.get("_source_file"),
        "map_enabled": entity.get("map_enabled", False),
    }


def filter_entities(entities, entity_type=None, search=""):
    text = str(search or "").lower().strip()

    if entity_type and entity_type != "all":
        entities = [
            entity for entity in entities
            if entity.get("type") == entity_type
        ]

    if text:
        entities = [
            entity for entity in entities
            if text in str(entity.get("name", "")).lower()
            or text in str(entity.get("id", "")).lower()
            or text in str(entity.get("type", "")).lower()
        ]

    return entities


def relation_label(relation):
    source = relation.get("source", {})
    target = relation.get("target", {})

    return (
        f"{source.get('name', 'Origen')} -> "
        f"{relation.get('relation_type', 'relacion')} -> "
        f"{target.get('name', 'Destino')}"
    )


def read_json_list(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return []

    return data if isinstance(data, list) else []


def write_json_list(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_spell_library():
    spells = read_json_list("entities/generated_spells.json")

    return [
        {
            **spell,
            "display": format_spell_for_display(spell),
        }
        for spell in spells
        if isinstance(spell, dict)
    ]


def get_workbench(module_key, query=None):
    query = query or {}
    module = get_module(module_key)

    if not module:
        raise ValueError("Modulo no encontrado")

    entities = [
        compact_entity(entity)
        for entity in load_registry_entities(profile="editor", include_default=True)
    ]
    world_entities = [
        compact_entity(entity)
        for entity in load_registry_entities(profile="world", include_default=True)
    ]
    relation_entities = [
        compact_entity(entity)
        for entity in load_registry_entities(profile="relations", include_default=True)
    ]

    base = {
        "module": module,
        "entities": entities[:300],
        "worlds": load_worlds(),
        "relations": [
            {**relation, "label": relation_label(relation)}
            for relation in load_relations()
        ],
        "relation_types": sorted(set(EQUIPMENT_RELATIONS + ["conocido", "rivalidad", "aliado", "enemigo", "sirve a", "protege", "amenaza", "bendecido por"])),
    }

    if module_key == "general_oracle":
        base.update({
            "worlds": load_worlds(),
        })

    elif module_key == "dice":
        base.update({
            "dice_sides": DICE_SIDES,
        })

    elif module_key == "species":
        base.update({
            "species": load_species(),
        })

    elif module_key == "loot":
        base.update({
            "focus_options": LOOT_FOCUS_OPTIONS,
        })

    elif module_key == "equipment":
        owner_types = {"npcs", "npc", "creatures", "creature", "factions", "armies", "kingdoms"}
        equipment_types = {"weapons", "armors", "relics", "items", "loot", "foods", "spells", "generated_spell", "generated_spells"}
        registry_equipment = [
            entity for entity in entities
            if entity.get("type") in equipment_types
        ]
        equipment_by_id = {
            item.get("id"): compact_entity(item)
            for item in load_all_equipment()
            if item.get("id")
        }

        for item in registry_equipment:
            equipment_by_id[item.get("id")] = item

        base.update({
            "owners": [
                entity for entity in entities
                if entity.get("type") in owner_types
            ],
            "owner_types": ["Todos", "armies", "npcs", "kingdoms"],
            "equipment": sorted(
                equipment_by_id.values(),
                key=lambda item: (str(item.get("type", "")), str(item.get("name", ""))),
            ),
            "equipment_types": ["Todos", "relics", "weapons", "armors", "items", "loot", "foods", "spells", "generated_spells"],
            "equipment_relations": sorted(EQUIPMENT_RELATIONS),
        })

    elif module_key in ["relations", "relation_graph"]:
        base.update({
            "entities": relation_entities,
        })

    elif module_key == "world_map":
        world_map = load_world_map()
        base.update({
            "map": world_map,
            "nodes": world_map.get("nodes", []),
            "entities": world_entities,
        })

    elif module_key == "entity_editor":
        base.update({
            "entities": entities,
            "types": sorted({entity.get("type") for entity in entities if entity.get("type")}),
        })

    elif module_key == "worlds":
        base.update({
            "entities": world_entities,
        })

    elif module_key == "spell_forge":
        base.update({
            "components": {
                key: load_component(key)
                for key in COMPONENT_FILES.keys()
            },
            "library": load_spell_library(),
        })

    elif module_key == "simulation":
        base.update({
            "map": load_world_map(),
        })

    elif module_key == "maintenance":
        base.update(generate_maintenance_report())

    return base


def format_general_oracle(oracle_data):
    return (
        "══════════════════════\n"
        "🎲 ORÁCULO GENERAL\n"
        f"🕒 {oracle_data.get('timestamp')}\n"
        "══════════════════════\n\n"
        f"Acción: {oracle_data.get('Acción')}\n"
        f"Objetivo: {oracle_data.get('Objetivo')}\n\n"
        "Interpretación:\n"
        f"{oracle_data.get('Interpretación')}"
    )


def consult_general_oracle():
    action = roll_named_oracle(GENERAL_ORACLE_ACTION)
    subject = roll_named_oracle(GENERAL_ORACLE_SUBJECT)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    interpretation = (
        f"Algo relacionado con '{subject}' debe "
        f"'{str(action).lower()}' o ser afectado por esa acción."
    )
    data = {
        "Acción": action,
        "Objetivo": subject,
        "Interpretación": interpretation,
        "timestamp": timestamp,
    }

    return {
        "ok": True,
        "data": data,
        "display": format_general_oracle(data),
    }


def format_dice_roll(dice_data):
    return (
        "══════════════════════\n"
        f"🕒 {dice_data.get('timestamp')}\n"
        f"🎲 D{dice_data.get('sides')} x{dice_data.get('count')}\n"
        f"Resultados: {dice_data.get('results')}\n"
        f"Total: {dice_data.get('total')}\n"
        "══════════════════════"
    )


def format_species(species):
    lines = [
        "══════════════════════",
        f"🧬 ESPECIE GENERADA: {species.get('name')}",
        "══════════════════════",
        f"ID provisional: {species.get('id')}",
        "",
        "Características:",
    ]

    for key, value in species.get("data", {}).items():
        lines.append(f"- {key}: {value}")

    effects = species.get("effects", {})
    if effects:
        lines.extend(["", "Efectos inferidos:"])
        for key, value in effects.items():
            sign = "+" if isinstance(value, int) and value >= 0 else ""
            lines.append(f"- {key}: {sign}{value}")

    return "\n".join(lines)


def format_loot(generated):
    lines = ["💎 LOOT GENERADO", ""]

    for index, loot in enumerate(generated, start=1):
        lines.extend([
            "══════════════════",
            f"💎 HALLAZGO {index}",
            "══════════════════",
        ])
        for key, value in loot.items():
            lines.append(f"{key}: {value}")
        lines.append("")

    return "\n".join(lines)


def run_workbench_action(module_key, action, payload=None):
    payload = payload or {}

    if module_key == "general_oracle":
        if action == "consult":
            return consult_general_oracle()

        if action in ["save_event", "save_scene"]:
            generated = payload.get("generated") or {}
            if not generated:
                return {"ok": False, "error": "No hay consulta generada"}

            entity_type = "events" if action == "save_event" else "scenes"
            label = "event" if action == "save_event" else "scene"
            name = payload.get("name") or f"{label.capitalize()} Sin Nombre"
            entity = {
                "name": name,
                "type": entity_type,
                "data": generated,
            }
            entity_id = save_entity(entity_type, entity)
            entity["id"] = entity_id
            clear_registry_cache()

            world_id = payload.get("world_id")
            if world_id:
                add_entity_to_world(world_id, entity)

            return {
                "ok": True,
                "entity": entity,
                "display": f"💾 GUARDADO COMO {label.upper()}\nID: {entity_id}",
            }

    if module_key == "dice":
        if action == "roll":
            return roll_dice_payload(payload)

    if module_key == "species":
        if action == "generate":
            species = generate_species_from_oracles(name=payload.get("name") or None)
            return {
                "ok": True,
                "species": species,
                "display": format_species(species),
            }

        if action == "save":
            species = payload.get("species") or {}
            if not species:
                return {"ok": False, "error": "No hay especie generada"}

            custom_name = payload.get("name")
            if custom_name:
                species["name"] = custom_name

            species_id = save_species(species)
            clear_registry_cache()
            return {
                "ok": True,
                "id": species_id,
                "species": species,
                "display": f"💾 ESPECIE GUARDADA\nID: {species_id}",
                "saved": load_species(),
            }

        if action == "list":
            saved = load_species()
            lines = ["══════════════════════", "🧬 ESPECIES GUARDADAS", "══════════════════════", ""]
            lines.extend(f"- {item.get('name', 'Sin nombre')} ({item.get('id')})" for item in saved)
            return {"ok": True, "species": saved, "display": "\n".join(lines)}

    if module_key == "loot":
        if action == "generate":
            amount = max(1, min(int(payload.get("amount") or 1), 100))
            generated = [generate_single_loot(payload) for _ in range(amount)]
            data = generated[0] if amount == 1 else {
                f"Loot {index + 1}": loot
                for index, loot in enumerate(generated)
            }
            return {
                "ok": True,
                "loot": generated,
                "entity_data": data,
                "display": format_loot(generated),
            }

        if action == "save":
            generated_data = payload.get("entity_data") or {}
            if not generated_data:
                return {"ok": False, "error": "No hay loot generado"}

            name = payload.get("name")
            if not name and isinstance(generated_data, dict):
                name = generated_data.get("Nombre sugerido")
            name = name or "Loot sin nombre"

            entity = {
                "name": name,
                "type": "loot",
                "meta": loot_meta(generated_data, payload.get("focus") or "Aleatorio"),
                "data": generated_data,
            }
            entity_id = save_entity("loot", entity)
            entity["id"] = entity_id
            clear_registry_cache()

            world_id = payload.get("world_id")
            if world_id:
                add_entity_to_world(world_id, entity)

            return {
                "ok": True,
                "entity": entity,
                "display": (
                    "💾 LOOT GUARDADO\n"
                    f"ID: {entity_id}\n"
                    f"Nombre: {name}\n"
                    f"Rareza: {entity['meta'].get('rarity')}"
                ),
            }

    if module_key == "equipment":
        if action == "assign":
            owner = get_entity_by_id(payload.get("owner_id"), profile="all")
            item = get_entity_by_id(payload.get("item_id"), profile="all")

            if not owner or not item:
                return {"ok": False, "error": "Entidad o equipo no encontrado"}

            relation = create_relation(
                source=compact_entity(owner),
                relation_type=payload.get("relation_type") or "porta",
                target=compact_entity(item),
                notes=payload.get("notes", ""),
            )

            return {
                "ok": True,
                "relation": relation,
                "current": get_equipment_for_entity(owner.get("id")),
                "display": f"🎒 {owner.get('name')} → {relation.get('relation_type')} → {item.get('name')}",
            }

        if action == "remove":
            return {"ok": delete_relation(payload.get("relation_id"))}

        if action == "current":
            return {"ok": True, "current": get_equipment_for_entity(payload.get("owner_id"))}

        if action == "details":
            item = get_entity_by_id(payload.get("item_id"), profile="all")
            if not item:
                return {"ok": False, "error": "Equipo no encontrado"}

            lines = [
                "══════════════════════",
                f"🎒 {item.get('name', 'Sin nombre')}",
                "══════════════════════",
                f"Tipo: {item.get('type')}",
                "",
                "Datos:",
            ]
            for key, value in item.get("data", {}).items():
                lines.append(f"- {key}: {value}")

            effects = item.get("effects", {})
            if effects:
                lines.extend(["", "Efectos:"])
                for key, value in effects.items():
                    lines.append(f"- {key}: {value}")

            return {"ok": True, "item": item, "display": "\n".join(lines)}

    if module_key == "relations":
        if action == "create":
            source = get_entity_by_id(payload.get("source_id"), profile="all")
            target = get_entity_by_id(payload.get("target_id"), profile="all")

            if not source or not target:
                return {"ok": False, "error": "Origen o destino no encontrado"}

            relation = create_relation(
                compact_entity(source),
                payload.get("relation_type") or "conocido",
                compact_entity(target),
                payload.get("notes", ""),
            )

            return {"ok": True, "relation": relation}

        if action == "update":
            source = get_entity_by_id(payload.get("source_id"), profile="all")
            target = get_entity_by_id(payload.get("target_id"), profile="all")

            ok = update_relation(
                payload.get("relation_id"),
                compact_entity(source or {}),
                payload.get("relation_type") or "conocido",
                compact_entity(target or {}),
                payload.get("notes", ""),
            )

            return {"ok": ok}

        if action == "delete":
            return {"ok": delete_relation(payload.get("relation_id"))}

    if module_key == "world_map":
        if action == "add":
            entity = get_entity_by_id(payload.get("entity_id"), profile="all")
            if not entity:
                return {"ok": False, "error": "Entidad no encontrada"}

            node = add_or_update_node(
                entity,
                x=float(payload.get("x") or random.randint(80, 900)),
                y=float(payload.get("y") or random.randint(80, 520)),
            )
            return {"ok": True, "node": node, "map": load_world_map()}

        if action == "remove":
            return {"ok": remove_node(payload.get("entity_id")), "map": load_world_map()}

        if action == "move":
            ok = update_node_position(
                payload.get("entity_id"),
                float(payload.get("x") or 0),
                float(payload.get("y") or 0),
            )
            return {"ok": ok, "map": load_world_map()}

        if action == "save":
            save_map_nodes(payload.get("nodes") or [])
            return {"ok": True, "map": load_world_map()}

        if action == "advance":
            return {"ok": True, "result": advance_world_turn(), "map": load_world_map()}

    if module_key == "entity_editor":
        if action == "save":
            entity = payload.get("entity") or {}
            ok = save_entity_update(entity)
            clear_registry_cache()
            return {"ok": ok, "entity": entity}

    if module_key == "worlds":
        if action == "save":
            world = {
                "name": payload.get("name") or "Mundo sin nombre",
                "description": payload.get("description", ""),
                "entities": payload.get("entities") or [],
            }
            world_id = save_world(world)
            clear_registry_cache()
            return {"ok": True, "id": world_id, "worlds": load_worlds()}

        if action == "delete":
            worlds = [
                world for world in load_worlds()
                if world.get("id") != payload.get("world_id")
            ]
            save_worlds(worlds)
            return {"ok": True, "worlds": worlds}

    if module_key == "spell_forge":
        if action == "generate":
            spell = generate_modular_spell(
                blueprint_id=payload.get("blueprint_id") or None,
                include_effects=payload.get("include_effects", True),
                include_intentions=payload.get("include_intentions", True),
                include_modifiers=payload.get("include_modifiers", True),
                include_costs=payload.get("include_costs", True),
                include_limitations=payload.get("include_limitations", True),
                include_manifestation=payload.get("include_manifestation", True),
                include_side_effects=payload.get("include_side_effects", True),
                allow_dangerous=payload.get("allow_dangerous", True),
                selected_components=payload.get("selected_components") or {},
            )
            return {"ok": True, "spell": spell, "display": format_spell_for_display(spell)}

        if action == "save":
            spell = payload.get("spell") or {}
            spells = read_json_list("entities/generated_spells.json")
            spells.append(spell)
            write_json_list("entities/generated_spells.json", spells)
            clear_registry_cache()
            return {"ok": True, "library": load_spell_library()}

        if action == "delete":
            spell_id = payload.get("spell_id")
            spells = [
                spell for spell in read_json_list("entities/generated_spells.json")
                if spell.get("id") != spell_id
            ]
            write_json_list("entities/generated_spells.json", spells)
            clear_registry_cache()
            return {"ok": True, "library": load_spell_library()}

    if module_key == "echoes":
        if action == "generate":
            echo = generate_echo(payload.get("world_id") or None)
            return {"ok": True, "echo": echo}

        if action == "save":
            event_id = save_echo_as_event(payload.get("echo") or {})
            return {"ok": True, "id": event_id}

    if module_key in ["simulation", "world_map"] and action == "advance":
        return {"ok": True, "result": advance_world_turn(), "map": load_world_map()}

    return {"ok": False, "error": "Accion no soportada"}
