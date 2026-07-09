import json
import os
import random
from datetime import datetime


SPELL_COMPONENTS_DIR = "entities/spell_components"


COMPONENT_FILES = {
    "sources": "sources.json",
    "actions": "actions.json",
    "targets": "targets.json",
    "forms": "forms.json",
    "modifiers": "modifiers.json",
    "costs": "costs.json",
    "limitations": "limitations.json",
    "manifestations": "manifestations.json",
    "intentions": "intentions.json",
    "side_effects": "side_effects.json",
    "blueprints": "spell_blueprints.json"
}


def load_json_list(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return []

    return data if isinstance(data, list) else []


def load_component(component_type):
    filename = COMPONENT_FILES.get(component_type)

    if not filename:
        return []

    path = os.path.join(SPELL_COMPONENTS_DIR, filename)

    return load_json_list(path)


def get_component_by_id(component_type, component_id):
    if not component_id:
        return None

    for item in load_component(component_type):
        if item.get("id") == component_id:
            return item

    return None


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def weighted_choice(items, allow_dangerous=True):
    if not items:
        return None

    filtered = []

    for item in items:
        risk = safe_int(item.get("risk", 0))

        if not allow_dangerous and risk >= 3:
            continue

        filtered.append(item)

    if not filtered:
        filtered = items

    weighted_items = []

    for item in filtered:
        try:
            weight = float(item.get("weight", 1))
        except Exception:
            weight = 1

        if weight > 0:
            weighted_items.append((item, weight))

    if not weighted_items:
        return random.choice(filtered)

    total = sum(weight for _item, weight in weighted_items)
    roll = random.uniform(0, total)

    current = 0

    for item, weight in weighted_items:
        current += weight

        if roll <= current:
            return item

    return weighted_items[-1][0]


def pick_component(component_type, allow_dangerous=True):
    return weighted_choice(
        load_component(component_type),
        allow_dangerous=allow_dangerous
    )


def pick_many(component_type, min_count=0, max_count=1, allow_dangerous=True):
    items = load_component(component_type)

    if not items:
        return []

    if not allow_dangerous:
        safe_items = [
            item for item in items
            if safe_int(item.get("risk", 0)) < 3
        ]

        if safe_items:
            items = safe_items

    count = random.randint(min_count, max_count)
    count = min(count, len(items))

    picked = []
    available = list(items)

    for _ in range(count):
        selected = weighted_choice(
            available,
            allow_dangerous=allow_dangerous
        )

        if not selected:
            continue

        picked.append(selected)
        available.remove(selected)

    return picked


def parse_count_rule(rule, default_min=0, default_max=1):
    if isinstance(rule, list) and len(rule) >= 2:
        return safe_int(rule[0], default_min), safe_int(rule[1], default_max)

    if isinstance(rule, int):
        return rule, rule

    return default_min, default_max


def merge_effects(*components):
    effects = {}

    for component in components:
        if not component:
            continue

        component_effects = component.get("effects", {})

        if not isinstance(component_effects, dict):
            continue

        for key, value in component_effects.items():
            try:
                value = int(value)
            except Exception:
                continue

            effects[key] = effects.get(key, 0) + value

    return effects


def calculate_risk(*components):
    risk = 0

    for component in components:
        if not component:
            continue

        risk += safe_int(component.get("risk", 0))

        effects = component.get("effects", {})

        if isinstance(effects, dict):
            risk += safe_int(effects.get("risk", 0))

    return risk


def simplify(component):
    if not component:
        return None

    return {
        "id": component.get("id"),
        "name": component.get("name"),
        "description": component.get("description", ""),
        "tags": component.get("tags", []),
        "effects": component.get("effects", {}),
        "risk": component.get("risk", 0)
    }


def build_tags(*components):
    tags = []

    for component in components:
        if not component:
            continue

        for tag in component.get("tags", []):
            if tag not in tags:
                tags.append(tag)

    return tags


def get_selected_or_random_single(
    component_type,
    selected_components,
    key,
    allow_dangerous=True
):
    selected_id = selected_components.get(key)

    return (
        get_component_by_id(component_type, selected_id)
        or pick_component(component_type, allow_dangerous=allow_dangerous)
    )


def get_selected_or_random_many(
    component_type,
    selected_components,
    key,
    blueprint,
    include=True,
    allow_dangerous=True
):
    if not include:
        return []

    selected_ids = selected_components.get(key, [])

    if selected_ids:
        selected_items = [
            get_component_by_id(component_type, item_id)
            for item_id in selected_ids
        ]

        return [
            item for item in selected_items
            if item
        ]

    component_rules = blueprint.get("components", {})
    rule = component_rules.get(key, [0, 1])

    min_count, max_count = parse_count_rule(rule)

    return pick_many(
        component_type,
        min_count,
        max_count,
        allow_dangerous=allow_dangerous
    )


def generate_spell_name(source, action, target, form, intention=None):
    source_name = source.get("name", "Arcano") if source else "Arcano"
    action_name = action.get("name", "Eco") if action else "Eco"
    target_name = target.get("name", "Misterio") if target else "Misterio"
    form_name = form.get("name", "Forma") if form else "Forma"
    intention_name = intention.get("name", "") if intention else ""

    patterns = [
        f"{form_name} de {target_name}",
        f"{action_name} de {target_name}",
        f"{target_name} {source_name}",
        f"{form_name} del {source_name}",
        f"{action_name} {target_name}",
        f"{form_name} de {target_name} {source_name}"
    ]

    if intention_name:
        patterns.extend([
            f"{form_name} para {intention_name}",
            f"{intention_name} de {target_name}",
            f"{action_name} para {intention_name}"
        ])

    return random.choice(patterns)


def build_spell_description(
    source,
    action,
    target,
    form,
    intentions=None,
    modifiers=None,
    costs=None,
    limitations=None,
    manifestation=None,
    side_effects=None
):
    intentions = intentions or []
    modifiers = modifiers or []
    costs = costs or []
    limitations = limitations or []
    side_effects = side_effects or []

    source_name = source.get("name", "una fuente desconocida") if source else "una fuente desconocida"
    action_name = action.get("name", "alterar").lower() if action else "alterar"
    target_name = target.get("name", "algo indefinido").lower() if target else "algo indefinido"
    form_name = form.get("name", "forma indefinida").lower() if form else "forma indefinida"

    text = (
        f"Usa {source_name} para {action_name} "
        f"{target_name} mediante una forma de {form_name}."
    )

    if intentions:
        names = ", ".join(item.get("name", "") for item in intentions)
        text += f" Intención principal: {names}."

    if modifiers:
        names = ", ".join(item.get("name", "") for item in modifiers)
        text += f" Se ve alterado por: {names}."

    if costs:
        names = ", ".join(item.get("name", "") for item in costs)
        text += f" Su precio principal es: {names}."

    if limitations:
        names = ", ".join(item.get("name", "") for item in limitations)
        text += f" Limitaciones: {names}."

    if manifestation:
        text += f" Se manifiesta como: {manifestation.get('name')}."

    if side_effects:
        names = ", ".join(item.get("name", "") for item in side_effects)
        text += f" Efectos secundarios posibles: {names}."

    return text


def get_blueprint(blueprint_id=None, allow_dangerous=True):
    blueprints = load_component("blueprints")

    if blueprint_id:
        for item in blueprints:
            if item.get("id") == blueprint_id:
                return item

    selected = weighted_choice(
        blueprints,
        allow_dangerous=allow_dangerous
    )

    if selected:
        return selected

    return {
        "id": "manual_basic",
        "name": "Técnica libre",
        "components": {
            "intentions": [0, 1],
            "modifiers": [0, 1],
            "costs": [0, 1],
            "limitations": [0, 1],
            "manifestations": 1,
            "side_effects": [0, 1]
        }
    }


def generate_modular_spell(
    blueprint_id=None,
    forced_power_level=None,
    include_effects=True,
    include_intentions=True,
    include_modifiers=True,
    include_costs=True,
    include_limitations=True,
    include_manifestation=True,
    include_side_effects=True,
    allow_dangerous=True,
    selected_components=None
):
    selected_components = selected_components or {}
    blueprint = get_blueprint(
        blueprint_id=blueprint_id,
        allow_dangerous=allow_dangerous
    )

    source = get_selected_or_random_single(
        "sources",
        selected_components,
        "source",
        allow_dangerous=allow_dangerous
    )

    action = get_selected_or_random_single(
        "actions",
        selected_components,
        "action",
        allow_dangerous=allow_dangerous
    )

    target = get_selected_or_random_single(
        "targets",
        selected_components,
        "target",
        allow_dangerous=allow_dangerous
    )

    form = get_selected_or_random_single(
        "forms",
        selected_components,
        "form",
        allow_dangerous=allow_dangerous
    )

    manifestation = None

    if include_manifestation:
        manifestation = get_selected_or_random_single(
            "manifestations",
            selected_components,
            "manifestation",
            allow_dangerous=allow_dangerous
        )

    intentions = get_selected_or_random_many(
        "intentions",
        selected_components,
        "intentions",
        blueprint,
        include=include_intentions,
        allow_dangerous=allow_dangerous
    )

    modifiers = get_selected_or_random_many(
        "modifiers",
        selected_components,
        "modifiers",
        blueprint,
        include=include_modifiers,
        allow_dangerous=allow_dangerous
    )

    costs = get_selected_or_random_many(
        "costs",
        selected_components,
        "costs",
        blueprint,
        include=include_costs,
        allow_dangerous=allow_dangerous
    )

    limitations = get_selected_or_random_many(
        "limitations",
        selected_components,
        "limitations",
        blueprint,
        include=include_limitations,
        allow_dangerous=allow_dangerous
    )

    side_effects = get_selected_or_random_many(
        "side_effects",
        selected_components,
        "side_effects",
        blueprint,
        include=include_side_effects,
        allow_dangerous=allow_dangerous
    )

    all_components = [
        source,
        action,
        target,
        form,
        manifestation
    ] + intentions + modifiers + costs + limitations + side_effects

    effects = merge_effects(*all_components) if include_effects else {}
    risk = calculate_risk(*all_components)

    main_intention = intentions[0] if intentions else None

    name = generate_spell_name(
        source,
        action,
        target,
        form,
        main_intention
    )

    description = build_spell_description(
        source,
        action,
        target,
        form,
        intentions,
        modifiers,
        costs,
        limitations,
        manifestation,
        side_effects
    )

    tags = build_tags(*all_components)

    spell = {
        "id": f"spell_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
        "name": name,
        "type": "generated_spell",
        "created_at": datetime.now().isoformat(),
        "blueprint": {
            "id": blueprint.get("id"),
            "name": blueprint.get("name")
        },
        "components": {
            "intentions": [simplify(item) for item in intentions],
            "source": simplify(source),
            "action": simplify(action),
            "target": simplify(target),
            "form": simplify(form),
            "modifiers": [simplify(item) for item in modifiers],
            "costs": [simplify(item) for item in costs],
            "limitations": [simplify(item) for item in limitations],
            "manifestation": simplify(manifestation),
            "side_effects": [simplify(item) for item in side_effects]
        },
        "description": description,
        "effects": effects,
        "risk": risk,
        "data": {
            "Categoría": "Técnica modular",
            "Descripción": description,
            "Riesgo": str(risk),
            "tags": tags
        }
    }

    if forced_power_level:
        spell["data"]["Nivel"] = forced_power_level

    return spell


def format_spell_for_display(spell):
    lines = []

    lines.append("══════════════════════")
    lines.append("🜂 TÉCNICA / HECHIZO MODULAR")
    lines.append("══════════════════════")
    lines.append("")
    lines.append(f"Nombre: {spell.get('name')}")
    lines.append(f"Tipo: {spell.get('blueprint', {}).get('name', 'Libre')}")
    lines.append(f"Riesgo: {spell.get('risk', 0)}")
    lines.append("")

    components = spell.get("components", {})

    intentions = components.get("intentions", [])

    if intentions:
        lines.append("Intenciones:")
        for item in intentions:
            lines.append(f"- {item.get('name')}")
        lines.append("")

    lines.append("Componentes:")

    labels = [
        ("Fuente", "source"),
        ("Acción", "action"),
        ("Objetivo", "target"),
        ("Forma", "form"),
        ("Manifestación", "manifestation")
    ]

    for label, key in labels:
        component = components.get(key)

        if component:
            lines.append(f"- {label}: {component.get('name')}")

    sections = [
        ("Modificadores", "modifiers"),
        ("Costos", "costs"),
        ("Limitaciones", "limitations"),
        ("Efectos secundarios", "side_effects")
    ]

    for label, key in sections:
        values = components.get(key, [])

        if values:
            lines.append(f"- {label}:")
            for item in values:
                lines.append(f"  • {item.get('name')}")

    lines.append("")
    lines.append("Descripción:")
    lines.append(spell.get("description", ""))

    effects = spell.get("effects", {})

    if effects:
        lines.append("")
        lines.append("Efectos:")
        for key, value in effects.items():
            lines.append(f"- {key}: {value}")

    tags = spell.get("data", {}).get("tags", [])

    if tags:
        lines.append("")
        lines.append("Tags:")
        lines.append(", ".join(tags))

    return "\n".join(lines)