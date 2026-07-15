import json
import os
import random
from datetime import datetime

from services.world_time_service import (
    advance_world_time,
    format_world_date
)

from services.location_profile_service import LocationProfileService
from services.relation_service import create_relation_if_missing


WORLD_MAP_PATH = "entities/world_map.json"
WORLD_EVENTS_PATH = "entities/world_events.json"

MOVEMENT_RULES = {
    "npcs": {"chance": 65, "distance": 90},
    "creatures": {"chance": 75, "distance": 130},
    "armies": {"chance": 45, "distance": 55},
    "factions": {"chance": 20, "distance": 35},
    "relics": {"chance": 5, "distance": 20},
    "items": {"chance": 5, "distance": 20},
    "weapons": {"chance": 5, "distance": 20},
    "armors": {"chance": 5, "distance": 20},
    "foods": {"chance": 5, "distance": 20},
    "locations": {"chance": 0, "distance": 0},
    "kingdoms": {"chance": 0, "distance": 0}
}


REACTION_DISTANCE = 220


NPC_LOCATION_REACTIONS = [
    {
        "key": "rest",
        "title": "{actor} descansó en {target}",
        "description": "{actor} se recuperó en {target}.",
        "effects": {"actor_status": "Recuperado"}
    },
    {
        "key": "mission",
        "title": "{actor} recibió una misión en {target}",
        "description": "{actor} encontró una oportunidad de trabajo o una petición local en {target}.",
        "effects": {"actor_goal": "Misión local"}
    },
    {
        "key": "trade",
        "title": "{actor} compró provisiones en {target}",
        "description": "{actor} consiguió recursos básicos en {target}.",
        "effects": {"actor_inventory_note": "Provisiones adquiridas"}
    },
    {
        "key": "learn",
        "title": "{actor} aprendió rumores útiles en {target}",
        "description": "{actor} obtuvo información sobre conflictos, rutas o peligros cercanos en {target}.",
        "effects": {"actor_knowledge": "Rumores locales"}
    }
]


NPC_NPC_REACTIONS = [
    {
        "key": "meet",
        "title": "{actor} conoció a {target}",
        "description": "{actor} y {target} tuvieron una interacción social significativa.",
        "effects": {"relation": "conocido"}
    },
    {
        "key": "group",
        "title": "{actor} formó un grupo con {target}",
        "description": "{actor} y {target} decidieron viajar o colaborar juntos por ahora.",
        "effects": {"party": True}
    },
    {
        "key": "rivalry",
        "title": "{actor} tuvo tensión con {target}",
        "description": "La interacción entre {actor} y {target} dejó una rivalidad o incomodidad latente.",
        "effects": {"relation": "rivalidad"}
    },
    {
        "key": "trade",
        "title": "{actor} intercambió recursos con {target}",
        "description": "{actor} y {target} realizaron un intercambio menor.",
        "effects": {"relation": "trato"}
    }
]


CREATURE_LOCATION_REACTIONS = [
    {
        "key": "stalk",
        "title": "{actor} acechó las cercanías de {target}",
        "description": "{actor} dejó rastros o señales peligrosas cerca de {target}.",
        "effects": {"target_threat": "Criatura cercana"}
    },
    {
        "key": "attack",
        "title": "{actor} atacó los alrededores de {target}",
        "description": "{actor} causó daños o miedo en las cercanías de {target}.",
        "effects": {"target_status": "Amenazado"}
    },
    {
        "key": "avoid",
        "title": "{actor} evitó {target}",
        "description": "{actor} percibió actividad civilizada y se alejó de {target}.",
        "effects": {"actor_status": "Evitando civilización"}
    }
]


ARMY_LOCATION_REACTIONS = [
    {
        "key": "occupy",
        "title": "{actor} ocupó una posición cerca de {target}",
        "description": "{actor} tomó control estratégico de una zona cercana a {target}.",
        "effects": {"target_status": "Ocupación militar cercana"}
    },
    {
        "key": "recruit",
        "title": "{actor} reclutó fuerzas en {target}",
        "description": "{actor} consiguió apoyo, suministros o reclutas en {target}.",
        "effects": {"actor_status": "Reforzado"}
    },
    {
        "key": "defend",
        "title": "{actor} reforzó la defensa de {target}",
        "description": "{actor} se posicionó para proteger {target}.",
        "effects": {"target_status": "Defendido"}
    },
    {
        "key": "raid",
        "title": "{actor} saqueó recursos cerca de {target}",
        "description": "{actor} tomó suministros o presionó a la población cercana a {target}.",
        "effects": {"target_status": "Saqueado"}
    }
]


DISCOVERY_REACTIONS = [
    {
        "key": "discover",
        "title": "{actor} descubrió {target}",
        "description": "{actor} encontró señales claras de {target}.",
        "effects": {"target_status": "Descubierto"}
    },
    {
        "key": "take",
        "title": "{actor} reclamó {target}",
        "description": "{actor} tomó posesión o custodia de {target}.",
        "effects": {"target_status": "Reclamado"}
    },
    {
        "key": "study",
        "title": "{actor} estudió {target}",
        "description": "{actor} investigó el origen, valor o peligro de {target}.",
        "effects": {"actor_knowledge": "Objeto estudiado"}
    }
]


location_profile_service = LocationProfileService()


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            return fallback

    return data


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_world_map():
    data = load_json(
        WORLD_MAP_PATH,
        {
            "nodes": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    )

    if not isinstance(data, dict):
        data = {"nodes": []}

    data.setdefault("nodes", [])
    data.setdefault("created_at", datetime.now().isoformat())
    data["updated_at"] = datetime.now().isoformat()

    return data


def save_world_map(data):
    data["updated_at"] = datetime.now().isoformat()
    save_json(WORLD_MAP_PATH, data)


def load_world_events():
    data = load_json(WORLD_EVENTS_PATH, [])
    return data if isinstance(data, list) else []


def save_world_events(events):
    save_json(WORLD_EVENTS_PATH, events)


def add_generated_events(new_events, generated):
    if not generated:
        return

    if isinstance(generated, list):
        new_events.extend(
            event for event in generated
            if isinstance(event, dict)
        )
        return

    if isinstance(generated, dict):
        new_events.append(generated)


def distance_between(a, b):
    ax = float(a.get("x", 0))
    ay = float(a.get("y", 0))
    bx = float(b.get("x", 0))
    by = float(b.get("y", 0))

    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def find_nearby_nodes(node, nodes, max_distance=REACTION_DISTANCE):
    nearby = []

    for other in nodes:
        if other.get("entity_id") == node.get("entity_id"):
            continue

        distance = distance_between(node, other)

        if distance <= max_distance:
            nearby.append((other, distance))

    nearby.sort(key=lambda item: item[1])

    return [item[0] for item in nearby]


def get_node_id(node):
    return node.get("entity_id") or node.get("id")


def is_mobile_node(node):
    return node.get("type") in ["npcs", "creatures", "armies", "factions"]


def is_location_node(node):
    return node.get("type") in ["locations", "kingdoms"]


def get_speed_for_node(node):
    speeds = {
        "npcs": 45,
        "creatures": 65,
        "armies": 28,
        "factions": 18
    }

    return speeds.get(node.get("type"), 35)


def get_arrival_distance(node):
    arrival_distances = {
        "npcs": 45,
        "creatures": 55,
        "armies": 70,
        "factions": 80
    }

    return arrival_distances.get(node.get("type"), 45)


def choose_destination_for_node(node, nodes):
    """
    Elige un destino lógico.
    Por ahora:
    - NPCs buscan ubicaciones/reinos.
    - Criaturas también pueden rondar ubicaciones.
    - Ejércitos buscan ubicaciones/reinos.
    """

    possible_targets = [
        target for target in nodes
        if is_location_node(target)
        and get_node_id(target) != get_node_id(node)
    ]

    if not possible_targets:
        return None

    node_state = node.setdefault("state", {})
    current_goal = str(node_state.get("goal", "")).lower()
    current_status = str(node_state.get("status", "")).lower()

    preferred_roles = []

    if node.get("type") == "npcs":
        if "misión" in current_goal or "trabajo" in current_goal:
            preferred_roles = ["village", "city", "port", "market"]

        elif "rumor" in current_goal or "conocimiento" in current_goal:
            preferred_roles = ["university", "archive", "ruins", "temple"]

        elif "recuperado" not in current_status:
            preferred_roles = ["village", "city", "fortress", "temple", "medical_site"]

    elif node.get("type") == "armies":
        preferred_roles = ["fortress", "military_base", "city", "kingdom"]

    elif node.get("type") == "creatures":
        preferred_roles = ["forest", "ruins", "cave", "cursed_zone", "village"]

    role_matches = []

    for target in possible_targets:
        role = location_profile_service.detect_location_role(target)

        if role in preferred_roles:
            role_matches.append(target)

    candidates = role_matches if role_matches else possible_targets

    candidates = sorted(
        candidates,
        key=lambda target: distance_between(node, target)
    )

    top_candidates = candidates[:5]

    return random.choice(top_candidates)


def assign_destination(node, target, reason="travel"):
    if not target:
        return None

    node_state = node.setdefault("state", {})

    destination = {
        "entity_id": get_node_id(target),
        "name": target.get("name", "Destino desconocido"),
        "type": target.get("type"),
        "x": float(target.get("x", 0)),
        "y": float(target.get("y", 0)),
        "reason": reason,
        "assigned_at": datetime.now().isoformat()
    }

    node_state["destination"] = destination

    return destination


def get_destination_target(node, nodes):
    destination = node.get("state", {}).get("destination")

    if not isinstance(destination, dict):
        return None

    destination_id = destination.get("entity_id")

    for target in nodes:
        if get_node_id(target) == destination_id:
            return target

    return None


def move_towards_destination(node, destination, nodes):
    base_speed = get_speed_for_node(node)
    travel_cost, zone_node = get_zone_travel_cost(node, nodes)
    speed = base_speed / travel_cost

    current_x = float(node.get("x", 0))
    current_y = float(node.get("y", 0))

    target_x = float(destination.get("x", current_x))
    target_y = float(destination.get("y", current_y))

    dx = target_x - current_x
    dy = target_y - current_y

    distance = (dx ** 2 + dy ** 2) ** 0.5

    if distance <= 0:
        return {
            "moved": True,
            "arrived": False,
            "destination": destination,
            "zone": zone_node.get("zone") if zone_node else None,
            "zone_name": zone_node.get("name") if zone_node else None,
            "travel_cost": travel_cost
        }

    arrival_distance = get_arrival_distance(node)

    if distance <= arrival_distance:
        node["x"] = target_x
        node["y"] = target_y

        node.setdefault("state", {})
        node["state"]["current_location"] = {
            "entity_id": destination.get("entity_id"),
            "name": destination.get("name"),
            "type": destination.get("type")
        }

        node["state"].pop("destination", None)

        return {
            "moved": True,
            "arrived": True,
            "destination": destination,
            "zone": zone_node.get("zone") if zone_node else None,
            "zone_name": zone_node.get("name") if zone_node else None,
            "travel_cost": travel_cost
        }

    step = min(speed, distance)

    node["x"] = current_x + (dx / distance) * step
    node["y"] = current_y + (dy / distance) * step

    return {
        "moved": True,
        "arrived": False,
        "destination": destination
    }


def move_node(node, nodes):
    entity_type = node.get("type", "")
    if node.get("state", {}).get("paused"):
        return {
            "moved": False,
            "arrived": False,
            "destination": None
        }

    if not is_mobile_node(node):
        return {
            "moved": False,
            "arrived": False,
            "destination": None
        }

    rule = MOVEMENT_RULES.get(entity_type, {"chance": 20, "distance": 50})

    if random.randint(1, 100) > rule["chance"]:
        return {
            "moved": False,
            "arrived": False,
            "destination": None
        }

    node.setdefault("state", {})

    destination_target = get_destination_target(node, nodes)

    should_choose_new_destination = (
        destination_target is None
        or random.randint(1, 100) <= 8
    )

    if should_choose_new_destination:
        destination_target = choose_destination_for_node(node, nodes)

        if destination_target:
            assign_destination(
                node,
                destination_target,
                reason="world_travel"
            )

    destination = node.get("state", {}).get("destination")

    if not destination:
        return {
            "moved": False,
            "arrived": False,
            "destination": None
        }

    return move_towards_destination(node, destination, nodes)


def apply_node_effects(actor, target, reaction):
    effects = reaction.get("effects", {})

    if not effects:
        return

    actor.setdefault("state", {})
    target.setdefault("state", {})

    if "actor_status" in effects:
        actor["state"]["status"] = effects["actor_status"]

    if "actor_goal" in effects:
        actor["state"]["goal"] = effects["actor_goal"]

    if "actor_inventory_note" in effects:
        actor.setdefault("inventory_notes", [])
        actor["inventory_notes"].append(effects["actor_inventory_note"])

    if "actor_knowledge" in effects:
        actor.setdefault("knowledge", [])
        actor["knowledge"].append(effects["actor_knowledge"])

    if "target_status" in effects:
        target["state"]["status"] = effects["target_status"]

    if "target_threat" in effects:
        target["state"]["threat"] = effects["target_threat"]

    if effects.get("party"):
        party_id = actor.get("party_id") or target.get("party_id")

        if not party_id:
            party_id = (
                f"party_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                f"{random.randint(100, 999)}"
            )

        actor["party_id"] = party_id
        target["party_id"] = party_id

    if "relation" in effects:
        relation_type = effects["relation"]

        actor.setdefault("relations", {})
        target.setdefault("relations", {})

        actor["relations"][target.get("entity_id")] = relation_type
        target["relations"][actor.get("entity_id")] = relation_type

        create_relation_if_missing(
            source={
                "id": actor.get("entity_id"),
                "name": actor.get("name"),
                "type": actor.get("type")
            },
            relation_type=relation_type,
            target={
                "id": target.get("entity_id"),
                "name": target.get("name"),
                "type": target.get("type")
            },
            notes="Relación generada automáticamente por la simulación del mundo."
        )


def create_event(
    event_type,
    title,
    description,
    world_time,
    node=None,
    related_nodes=None,
    extra=None
):
    event = {
        "id": f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
        "created_at": datetime.now().isoformat(),
        "world_date": format_world_date(world_time),
        "world_time": {
            "turn": world_time.get("turn"),
            "day": world_time.get("day"),
            "month": world_time.get("month"),
            "year": world_time.get("year")
        },
        "event_type": event_type,
        "title": title,
        "description": description,
        "source": {
            "entity_id": node.get("entity_id"),
            "name": node.get("name"),
            "type": node.get("type")
        } if node else None,
        "related": [
            {
                "entity_id": item.get("entity_id"),
                "name": item.get("name"),
                "type": item.get("type")
            }
            for item in (related_nodes or [])
        ]
    }

    if extra:
        event["extra"] = extra

    return event


def build_reaction_event(actor, target, reaction, world_time, event_type):
    actor_name = actor.get("name", "Entidad")
    target_name = target.get("name", "Entidad")

    title = reaction["title"].format(
        actor=actor_name,
        target=target_name
    )

    description = reaction["description"].format(
        actor=actor_name,
        target=target_name
    )

    apply_node_effects(actor, target, reaction)

    return create_event(
        event_type,
        title,
        description,
        world_time,
        actor,
        [target],
        extra={
            "reaction_key": reaction.get("key"),
            "effects": reaction.get("effects", {})
        }
    )


def choose_reaction(actor, target):
    actor_type = actor.get("type")
    target_type = target.get("type")

    if actor_type == "npcs" and target_type in ["locations", "kingdoms"]:
        return random.choice(NPC_LOCATION_REACTIONS), "npc_location_reaction"

    if actor_type == "npcs" and target_type == "npcs":
        return random.choice(NPC_NPC_REACTIONS), "npc_social_reaction"

    if actor_type == "creatures" and target_type in ["locations", "kingdoms"]:
        return random.choice(CREATURE_LOCATION_REACTIONS), "creature_location_reaction"

    if actor_type == "armies" and target_type in ["locations", "kingdoms"]:
        return random.choice(ARMY_LOCATION_REACTIONS), "army_location_reaction"

    if actor_type in ["npcs", "creatures", "armies"] and target_type in [
        "relics",
        "items",
        "weapons",
        "armors",
        "foods"
    ]:
        return random.choice(DISCOVERY_REACTIONS), "discovery_reaction"

    return None, None


def generate_reaction_events(nodes, world_time):
    events = []
    mobile_types = {"npcs", "creatures", "armies"}

    for actor in nodes:
        if actor.get("type") not in mobile_types:
            continue

        nearby = find_nearby_nodes(actor, nodes)

        if not nearby:
            continue

        if random.randint(1, 100) > 55:
            continue

        target = random.choice(nearby[:4])
        reaction, event_type = choose_reaction(actor, target)

        if not reaction:
            continue

        events.append(
            build_reaction_event(
                actor,
                target,
                reaction,
                world_time,
                event_type
            )
        )

    return events


def generate_location_production_events(nodes, world_time):
    events = []

    for node in nodes:
        if node.get("type") not in ["locations", "kingdoms"]:
            continue

        production = location_profile_service.get_production_for_node(node)

        if not production:
            continue

        if random.randint(1, 100) > 65:
            continue

        before_resources = dict(
            node.get("state", {}).get("resources", node.get("resources", {}))
        )

        location_profile_service.apply_basic_production_to_node(node)

        after_resources = node.get("state", {}).get("resources", {})

        applied_resources = {}

        for resource, new_amount in after_resources.items():
            old_amount = before_resources.get(resource, 0)
            gained = new_amount - old_amount

            if gained > 0:
                applied_resources[resource] = gained

        if not applied_resources:
            continue

        resource_text = ", ".join(
            f"{location_profile_service.RESOURCE_LABELS_ES.get(resource, resource)} +{amount}"
            for resource, amount in applied_resources.items()
        )

        location_role = location_profile_service.detect_location_role(node)
        profile = location_profile_service.get_profile_for_node(node) or {}
        display_role = profile.get("display_name", location_role or "Ubicación")

        events.append(
            create_event(
                "location_production",
                f"{node.get('name', 'Lugar')} produjo recursos",
                f"{node.get('name', 'Lugar')} produjo {resource_text}.",
                world_time,
                node,
                [],
                extra={
                    "location_role": location_role,
                    "location_role_display": display_role,
                    "resources": applied_resources,
                    "resources_total": after_resources
                }
            )
        )

    return events


def advance_world_turn():
    world_time = advance_world_time(days=1)

    world_map = load_world_map()
    nodes = world_map.get("nodes", [])

    events = load_world_events()
    new_events = []

    moved_count = 0

    for node in nodes:
        movement_result = move_node(node, nodes)

        if not movement_result.get("moved"):
            continue

        moved_count += 1

        destination = movement_result.get("destination") or {}
        destination_name = destination.get("name", "un destino desconocido")
        zone_name = movement_result.get("zone_name")

        if movement_result.get("arrived"):
            add_generated_events(
                new_events,
                create_event(
                    "arrival",
                    f"{node.get('name', 'Entidad')} llegó a {destination_name}",
                    f"{node.get('name', 'Entidad')} llegó a {destination_name}.",
                    world_time,
                    node,
                    [],
                    extra={
                        "destination": destination,
                        "zone_name": zone_name,
                        "travel_cost": movement_result.get("travel_cost")
                    }
                )
            )
        else:
            zone_text = f" atravesando {zone_name}" if zone_name else ""

            add_generated_events(
                new_events,
                create_event(
                    "movement",
                    f"{node.get('name', 'Entidad')} viajó hacia {destination_name}",
                    f"{node.get('name', 'Entidad')} avanzó hacia {destination_name}{zone_text}.",
                    world_time,
                    node,
                    [],
                    extra={
                        "destination": destination,
                        "zone_name": zone_name,
                        "travel_cost": movement_result.get("travel_cost")
                    }
                )
            )

            side_events = generate_travel_side_events(
                node,
                nodes,
                world_time
            )

            add_generated_events(new_events, side_events)

    production_events = generate_location_production_events(
        nodes,
        world_time
    )

    reaction_events = generate_reaction_events(
        nodes,
        world_time
    )

    add_generated_events(new_events, production_events)
    add_generated_events(new_events, reaction_events)

    world_map["nodes"] = nodes
    save_world_map(world_map)

    events.extend(new_events)
    save_world_events(events)

    return {
        "world_date": format_world_date(world_time),
        "moved_count": moved_count,
        "events_count": len(new_events),
        "events": new_events,
        "nodes": nodes
    }


def format_events_for_display(events):
    if not events:
        return "No ocurrieron eventos relevantes este turno."

    lines = []

    for event in events:
        lines.append("────────────────────")
        lines.append(f"📅 {event.get('world_date', 'Fecha desconocida')}")
        lines.append(f"📜 {event.get('title', 'Evento')}")
        lines.append(event.get("description", ""))

        extra = event.get("extra", {})

        if extra:
            effects = extra.get("effects", {})

            if effects:
                lines.append(f"Efectos aplicados: {effects}")

            resources = extra.get("resources", {})

            if resources:
                readable_resources = ", ".join(
                    f"{location_profile_service.RESOURCE_LABELS_ES.get(resource, resource)} +{amount}"
                    for resource, amount in resources.items()
                )
                lines.append(f"Recursos generados: {readable_resources}")

        related = event.get("related", [])

        if related:
            names = ", ".join(
                item.get("name", "Entidad")
                for item in related
            )
            lines.append(f"Relacionados: {names}")

    return "\n".join(lines)

def get_nearest_zone_node(node, nodes, max_distance=350):
    nearest = None
    nearest_distance = None

    for other in nodes:
        if other.get("entity_id") == node.get("entity_id"):
            continue

        if not other.get("zone"):
            continue

        distance = distance_between(node, other)

        if distance > max_distance:
            continue

        if nearest is None or distance < nearest_distance:
            nearest = other
            nearest_distance = distance

    return nearest


def get_zone_travel_cost(node, nodes):
    zone_node = get_nearest_zone_node(node, nodes)

    if not zone_node:
        return 1.0, None

    zone = zone_node.get("zone", {}) or {}
    travel_cost = float(zone.get("travel_cost", 1.0))

    if travel_cost <= 0:
        travel_cost = 1.0

    return travel_cost, zone_node


def maybe_generate_travel_reflection(node, world_time):
    if node.get("type") != "npcs":
        return None

    if random.randint(1, 100) > 10:
        return None

    reflections = [
        {
            "title": "{name} reflexionó durante el viaje",
            "description": "{name} empezó a cuestionar el rumbo que estaba tomando.",
            "goal": "Buscar propósito"
        },
        {
            "title": "{name} recordó una promesa",
            "description": "{name} recordó una deuda, promesa o deseo que aún no ha cumplido.",
            "goal": "Cumplir una promesa"
        },
        {
            "title": "{name} reafirmó su determinación",
            "description": "{name} decidió continuar a pesar del cansancio y la incertidumbre.",
            "status": "Determinado"
        },
        {
            "title": "{name} empezó a temer el camino",
            "description": "{name} sintió que el viaje podía ser más peligroso de lo esperado.",
            "status": "Inquieto"
        }
    ]

    reflection = random.choice(reflections)
    name = node.get("name", "Entidad")

    node.setdefault("memory", [])
    node["memory"].append({
        "description": reflection["description"].format(name=name),
        "importance": 1,
        "created_at": datetime.now().isoformat()
    })

    node.setdefault("state", {})

    if reflection.get("goal"):
        node["state"]["goal"] = reflection["goal"]

    if reflection.get("status"):
        node["state"]["status"] = reflection["status"]

    return create_event(
        "travel_reflection",
        reflection["title"].format(name=name),
        reflection["description"].format(name=name),
        world_time,
        node,
        [],
        extra={
            "reflection": True
        }
    )


def maybe_generate_travel_encounter(node, nodes, world_time):
    if node.get("type") not in ["npcs", "armies"]:
        return None

    zone_node = get_nearest_zone_node(node, nodes)

    if not zone_node:
        return None

    zone = zone_node.get("zone", {}) or {}
    encounter_chance = int(zone.get("encounter_chance", 5))

    if random.randint(1, 100) > encounter_chance:
        return None

    encounters = [
        "escuchó algo moviéndose cerca",
        "encontró rastros recientes de criaturas",
        "fue observado desde la distancia",
        "detectó señales de una posible emboscada",
        "encontró restos de un campamento abandonado"
    ]

    description = random.choice(encounters)

    node.setdefault("state", {})
    node["state"]["status"] = "Alerta"

    return create_event(
        "travel_encounter",
        f"{node.get('name', 'Entidad')} tuvo un encuentro durante el viaje",
        f"{node.get('name', 'Entidad')} {description} cerca de {zone_node.get('name', 'una zona desconocida')}.",
        world_time,
        node,
        [zone_node],
        extra={
            "zone": zone,
            "zone_name": zone_node.get("name")
        }
    )


def generate_travel_side_events(node, nodes, world_time):
    events = []

    state = node.get("state", {})

    if not state.get("destination"):
        return events

    reflection = maybe_generate_travel_reflection(node, world_time)

    if reflection:
        events.append(reflection)

    encounter = maybe_generate_travel_encounter(node, nodes, world_time)

    if encounter:
        events.append(encounter)

    return events
