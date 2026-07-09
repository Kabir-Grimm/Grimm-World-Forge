import random

from core.parser import load_all_lists, weighted_choice

from services.power_service import calculate_entity_power
from services.entity_registry_service import get_entity_by_id
from services.entity_editor_service import save_entity_update

from services.relation_service import (
    create_relation,
    delete_relation,
    get_outgoing_relations
)

from services.equipment_service import EQUIPMENT_RELATIONS
from services.memory_service import add_memory
from services.reputation_service import modify_reputation
from services.modifier_service import parse_modifier_line


# =====================================
# Lectura de listas
# =====================================

def roll_from_list(list_name):
    for oracle in load_all_lists():
        if oracle["name"] != list_name:
            continue

        data = oracle.get("data", {})

        if "Resultados" in data and data["Resultados"]:
            return weighted_choice(data["Resultados"])

        options = []

        for values in data.values():
            options.extend(values)

        if options:
            return weighted_choice(options)

    return f"[Falta lista: {list_name}]"


def render_template(text, values):
    try:
        return text.format(**values)
    except:
        return text


def get_score(power, key):
    try:
        return int(power.get(key, 0))
    except:
        return 0


# =====================================
# Equipo / hechizos / rasgos
# =====================================

def get_entity_equipment(entity_id):
    relations = get_outgoing_relations(
        entity_id,
        relation_types=EQUIPMENT_RELATIONS
    )

    equipment = []

    for relation in relations:
        target = relation.get("target", {})
        target_id = target.get("id")

        full_item = get_entity_by_id(target_id)

        if full_item:
            equipment.append({
                "relation": relation,
                "item": full_item
            })

    return equipment


def get_equipped_weapons(participant):
    return [
        entry["item"]
        for entry in participant.get("equipment", [])
        if entry["item"].get("type") in ["weapons", "weapon"]
    ]


def get_equipped_spells(participant):
    return [
        entry["item"]
        for entry in participant.get("equipment", [])
        if entry["item"].get("type") in ["spells", "spell"]
    ]


def get_traits(participant):
    traits = (
        participant
        .get("full_entity", {})
        .get("meta", {})
        .get("traits", [])
    )

    if isinstance(traits, list):
        return traits

    return []


def choose_weapon_name(participant):
    weapons = get_equipped_weapons(participant)

    if weapons:
        return random.choice(weapons).get("name", "arma")

    return roll_from_list("BatallaEpica-Arma-Improvisada")


def choose_spell_name(participant):
    spells = get_equipped_spells(participant)

    if not spells:
        return None

    spell = random.choice(spells)
    spell_name = spell.get("name", "hechizo desconocido")

    data = spell.get("data", {})

    effect = (
        data.get("Efecto")
        or data.get("Hechizo-Efecto")
        or data.get("Efecto principal")
        or data.get("Efecto mágico")
    )

    if effect:
        return f"{spell_name} ({effect})"

    return spell_name


def choose_trait_name(participant):
    traits = get_traits(participant)

    if not traits:
        return None

    return random.choice(traits)


def choose_power_technique(participant):
    """
    Los rasgos/poderes no son un cuarto modo.
    Son una capa que puede acompañar ataques físicos, mágicos o híbridos.
    """

    trait = choose_trait_name(participant)

    if trait:
        return trait

    spell = choose_spell_name(participant)

    if spell:
        return spell

    return ""


# =====================================
# Cuerpo / amputaciones
# =====================================

def get_lost_limbs(entity):
    meta = entity.get("meta", {})

    lost = meta.get("lost_limbs", [])

    if isinstance(lost, list):
        return [item.lower() for item in lost]

    if isinstance(lost, str):
        return [lost.lower()]

    return []


def choose_body_part(entity):
    options = []

    for oracle in load_all_lists():
        if oracle["name"] != "BatallaEpica-Parte-Cuerpo":
            continue

        data = oracle.get("data", {})

        if "Resultados" in data:
            options = [
                item[0]
                for item in data["Resultados"]
            ]
        else:
            for values in data.values():
                options.extend(
                    item[0]
                    for item in values
                )

    if not options:
        return "cuerpo"

    lost_limbs = get_lost_limbs(entity)
    valid_options = []

    for option in options:
        lower = option.lower()

        blocked = False

        for limb in lost_limbs:
            if limb and limb in lower:
                blocked = True
                break

        if not blocked:
            valid_options.append(option)

    if not valid_options:
        valid_options = options

    return random.choice(valid_options)


# =====================================
# Participantes
# =====================================

def create_participant(entity_id):
    power_data = calculate_entity_power(entity_id)
    entity = get_entity_by_id(entity_id)

    if not power_data or not entity:
        return None

    power = power_data.get("power", {})
    equipment = get_entity_equipment(entity_id)

    hp = (
        20
        + get_score(power, "resistance")
        + get_score(power, "defense")
    )

    return {
        "entity": power_data.get("entity", {}),
        "full_entity": entity,
        "power": power,
        "equipment": equipment,
        "hp": max(10, hp),
        "max_hp": max(10, hp),
        "defeated": False
    }


def roll_initiative(participant):
    power = participant["power"]

    return (
        random.randint(1, 20)
        + get_score(power, "initiative")
        + get_score(power, "stealth") // 3
    )


def start_epic_battle(entity_a_id, entity_b_id, max_turns=10):
    actor_a = create_participant(entity_a_id)
    actor_b = create_participant(entity_b_id)

    if not actor_a or not actor_b:
        return None

    initiative_a = roll_initiative(actor_a)
    initiative_b = roll_initiative(actor_b)

    first_actor = "a" if initiative_a >= initiative_b else "b"

    return {
        "actor_a": actor_a,
        "actor_b": actor_b,
        "initiative_a": initiative_a,
        "initiative_b": initiative_b,
        "first_actor": first_actor,
        "turn": 1,
        "max_turns": max_turns,
        "active": True,
        "finished": False,
        "winner": None,
        "loser": None,
        "log": [],
        "aftermath_applied": False,
        "same_creature_template": entity_a_id == entity_b_id
    }


def get_turn_actors(session):
    odd_turn = session["turn"] % 2 == 1

    if session["first_actor"] == "a":
        if odd_turn:
            return session["actor_a"], session["actor_b"]

        return session["actor_b"], session["actor_a"]

    if odd_turn:
        return session["actor_b"], session["actor_a"]

    return session["actor_a"], session["actor_b"]


# =====================================
# Modo de ataque
# =====================================

def choose_attack_mode(attacker):
    """
    Solo existen 3 modos:
    - physical
    - magic
    - hybrid

    Los rasgos/poderes pueden acompañar cualquier modo.
    """

    power = attacker["power"]

    physical_score = (
        get_score(power, "combat")
        + get_score(power, "damage")
    )

    magic_score = (
        get_score(power, "arcane")
        + get_score(power, "control")
    )

    difference = abs(physical_score - magic_score)

    if difference <= 3:
        return "hybrid"

    if magic_score > physical_score:
        return "magic"

    return "physical"


def get_attack_components(attacker, defender, mode):
    attacker_power = attacker["power"]
    defender_power = defender["power"]

    if mode == "magic":
        attack_score = (
            get_score(attacker_power, "arcane")
            + get_score(attacker_power, "control") // 2
            + get_score(attacker_power, "knowledge") // 3
        )

        defense_score = (
            get_score(defender_power, "resistance")
            + get_score(defender_power, "control") // 2
            + get_score(defender_power, "arcane") // 3
        )

    elif mode == "hybrid":
        attack_score = (
            get_score(attacker_power, "combat") // 2
            + get_score(attacker_power, "damage") // 2
            + get_score(attacker_power, "arcane") // 2
            + get_score(attacker_power, "control") // 2
        )

        defense_score = (
            get_score(defender_power, "defense")
            + get_score(defender_power, "resistance") // 2
            + get_score(defender_power, "control") // 2
        )

    else:
        attack_score = (
            get_score(attacker_power, "combat")
            + get_score(attacker_power, "damage")
            + get_score(attacker_power, "initiative") // 2
        )

        defense_score = (
            get_score(defender_power, "defense")
            + get_score(defender_power, "resistance") // 2
            + get_score(defender_power, "stealth") // 3
        )

    return attack_score, defense_score


def calculate_damage(attacker, defender, mode, margin, technique_used):
    attacker_power = attacker["power"]
    defender_power = defender["power"]

    if mode == "magic":
        base_damage = (
            get_score(attacker_power, "arcane") // 3
            + get_score(attacker_power, "control") // 3
            + max(0, margin // 2)
            + random.randint(1, 6)
        )

    elif mode == "hybrid":
        base_damage = (
            get_score(attacker_power, "damage") // 2
            + get_score(attacker_power, "arcane") // 3
            + max(0, margin // 2)
            + random.randint(1, 6)
        )

    else:
        base_damage = (
            get_score(attacker_power, "damage")
            + max(0, margin // 2)
            + random.randint(1, 6)
        )

    if technique_used:
        base_damage += random.choice([0, 1, 1, 2])

    mitigation = max(
        0,
        get_score(defender_power, "defense") // 5
    )

    return max(1, base_damage - mitigation)


def calculate_attack(attacker, defender):
    mode = choose_attack_mode(attacker)

    technique = choose_power_technique(attacker)

    attack_score, defense_score = get_attack_components(
        attacker,
        defender,
        mode
    )

    if technique:
        attack_score += random.choice([0, 1, 1, 2])

    attack_roll = random.randint(1, 20)
    defense_roll = random.randint(1, 20)

    total_attack = attack_score + attack_roll
    total_defense = defense_score + defense_roll

    hit = total_attack >= total_defense
    margin = total_attack - total_defense

    damage = 0

    if hit:
        damage = calculate_damage(
            attacker,
            defender,
            mode,
            margin,
            technique
        )

    return {
        "mode": mode,
        "technique": technique,
        "hit": hit,
        "attack_roll": attack_roll,
        "defense_roll": defense_roll,
        "attack_score": attack_score,
        "defense_score": defense_score,
        "total_attack": total_attack,
        "total_defense": total_defense,
        "margin": margin,
        "damage": damage
    }


# =====================================
# Narración
# =====================================

def choose_attack_template(mode, technique):
    if mode == "magic":
        return roll_from_list("BatallaEpica-Ataque-Magico")

    if mode == "hybrid":
        return roll_from_list("BatallaEpica-Ataque-Hibrido")

    if technique:
        return roll_from_list("BatallaEpica-Ataque-Con-Habilidad")

    return roll_from_list("BatallaEpica-Ataque")


def describe_turn(session, attacker, defender, attack):
    attacker_entity = attacker["full_entity"]
    defender_entity = defender["full_entity"]

    weapon = choose_weapon_name(attacker)
    spell = choose_spell_name(attacker)

    values = {
        "turn": session["turn"],
        "attacker": attacker["entity"].get("name", "Atacante"),
        "defender": defender["entity"].get("name", "Defensor"),
        "weapon": weapon,
        "spell": spell or "magia instintiva",
        "technique": attack.get("technique") or "",
        "body_part": choose_body_part(attacker_entity),
        "target_part": choose_body_part(defender_entity),
        "damage": attack["damage"],
        "attack_total": attack["total_attack"],
        "defense_total": attack["total_defense"],
        "mode": attack.get("mode", "physical")
    }

    lines = []
    lines.append(f"Turno {session['turn']}")

    template = choose_attack_template(
        attack.get("mode"),
        attack.get("technique")
    )

    lines.append(render_template(template, values))

    if attack["hit"]:
        hit_text = roll_from_list("BatallaEpica-Impacto")
        lines.append(render_template(hit_text, values))
    else:
        miss_text = roll_from_list("BatallaEpica-Fallo")
        lines.append(render_template(miss_text, values))

    feeling_text = roll_from_list("BatallaEpica-Mentalidad")
    rival_text = roll_from_list("BatallaEpica-Pensamiento-Rival")

    lines.append(render_template(feeling_text, values))
    lines.append(render_template(rival_text, values))

    lines.append(
        f"Tirada: ataque {attack['total_attack']} "
        f"vs defensa {attack['total_defense']}."
    )

    return "\n".join(lines)


# =====================================
# Avance de turnos
# =====================================

def advance_battle_turn(session):
    if not session or session.get("finished"):
        return session, "La batalla ya terminó."

    if session["turn"] > session["max_turns"]:
        finish_battle(session)
        return session, "La batalla queda inconclusa por límite de turnos."

    attacker, defender = get_turn_actors(session)

    attack = calculate_attack(attacker, defender)

    if attack["hit"]:
        defender["hp"] -= attack["damage"]

        if defender["hp"] <= 0:
            defender["hp"] = 0
            defender["defeated"] = True

    turn_text = describe_turn(
        session,
        attacker,
        defender,
        attack
    )

    hp_text = (
        f"HP: {session['actor_a']['entity']['name']} "
        f"{session['actor_a']['hp']}/{session['actor_a']['max_hp']} | "
        f"{session['actor_b']['entity']['name']} "
        f"{session['actor_b']['hp']}/{session['actor_b']['max_hp']}"
    )

    full_text = f"{turn_text}\n{hp_text}\n"

    session["log"].append(full_text)

    if defender["defeated"]:
        finish_battle(session)
    else:
        session["turn"] += 1

        if session["turn"] > session["max_turns"]:
            finish_battle(session)

    return session, full_text


def finish_battle(session):
    actor_a = session["actor_a"]
    actor_b = session["actor_b"]

    session["finished"] = True
    session["active"] = False

    if actor_a["hp"] <= 0 and actor_b["hp"] <= 0:
        session["winner"] = None
        session["loser"] = None
        return session

    if actor_a["hp"] <= 0:
        session["winner"] = actor_b
        session["loser"] = actor_a
        return session

    if actor_b["hp"] <= 0:
        session["winner"] = actor_a
        session["loser"] = actor_b
        return session

    if actor_a["hp"] > actor_b["hp"]:
        session["winner"] = actor_a
        session["loser"] = actor_b
    elif actor_b["hp"] > actor_a["hp"]:
        session["winner"] = actor_b
        session["loser"] = actor_a
    else:
        session["winner"] = None
        session["loser"] = None

    return session


# =====================================
# Consecuencias finales
# =====================================

def apply_reputation_from_list(entity_id, list_name):
    raw = roll_from_list(list_name)
    _name, modifiers = parse_modifier_line(raw)

    for key, value in modifiers.items():
        if isinstance(value, int):
            modify_reputation(entity_id, key, value)


def apply_final_status(entity, list_name):
    status = roll_from_list(list_name)

    full_entity = get_entity_by_id(entity["entity"]["id"])

    if not full_entity:
        return None

    meta = full_entity.get("meta", {})

    if not isinstance(meta, dict):
        meta = {}

    meta["status"] = status

    if status in ["Muerto", "Desaparecido"]:
        meta["active"] = False

    full_entity["meta"] = meta

    save_entity_update(full_entity)

    return status


def transfer_random_equipment(winner, loser):
    loser_equipment = loser.get("equipment", [])

    if not loser_equipment:
        return None

    selected = random.choice(loser_equipment)

    relation = selected["relation"]
    item = selected["item"]

    relation_id = relation.get("id")

    if relation_id:
        delete_relation(relation_id)

    create_relation(
        source={
            "id": winner["entity"]["id"],
            "name": winner["entity"]["name"],
            "type": winner["entity"]["type"]
        },
        relation_type=relation.get("relation_type", "posee"),
        target={
            "id": item.get("id"),
            "name": item.get("name"),
            "type": item.get("type")
        },
        notes="Obtenido como botín en una batalla épica."
    )

    return item.get("name")


def is_creature_participant(participant):
    entity_type = participant.get("entity", {}).get("type")

    return entity_type in {"creatures", "creature"}


def should_save_relationships_for_battle(winner, loser, session):
    if session.get("same_creature_template"):
        return False

    if is_creature_participant(winner) or is_creature_participant(loser):
        return False

    return True


def apply_epic_battle_aftermath(session, allow_loot=True):
    if not session or not session.get("finished"):
        return {
            "applied": False,
            "messages": ["La batalla aún no ha terminado."]
        }

    if session.get("aftermath_applied"):
        return {
            "applied": False,
            "messages": ["Las consecuencias finales ya fueron aplicadas."]
        }

    messages = []

    winner = session.get("winner")
    loser = session.get("loser")

    if not winner or not loser:
        messages.append("La batalla terminó sin ganador claro.")
        session["aftermath_applied"] = True

        return {
            "applied": True,
            "messages": messages
        }

    winner_id = winner["entity"]["id"]
    loser_id = loser["entity"]["id"]

    winner_name = winner["entity"]["name"]
    loser_name = loser["entity"]["name"]

    if session.get("same_creature_template"):
        messages.append(
            f"La batalla representa a dos individuos de la especie {winner_name}; no se guardan memoria, reputación ni relaciones permanentes."
        )

        session["aftermath_applied"] = True

        return {
            "applied": True,
            "messages": messages
        }

    add_memory(
        winner_id,
        "epic_battle_winner",
        f"Venció a {loser_name} en una batalla épica.",
        importance=5,
        source="epic_battle"
    )

    add_memory(
        loser_id,
        "epic_battle_loser",
        f"Fue derrotado por {winner_name} en una batalla épica.",
        importance=5,
        source="epic_battle"
    )

    apply_reputation_from_list(
        winner_id,
        "BatallaEpica-Reputacion-Ganador"
    )

    apply_reputation_from_list(
        loser_id,
        "BatallaEpica-Reputacion-Perdedor"
    )

    winner_relation = roll_from_list(
        "BatallaEpica-Relacion-Ganador"
    )

    loser_relation = roll_from_list(
        "BatallaEpica-Relacion-Perdedor"
    )

    save_relationships = should_save_relationships_for_battle(
        winner,
        loser,
        session
    )

    if save_relationships:
        create_relation(
            source={
                "id": winner_id,
                "name": winner_name,
                "type": winner["entity"]["type"]
            },
            relation_type=winner_relation,
            target={
                "id": loser_id,
                "name": loser_name,
                "type": loser["entity"]["type"]
            },
            notes="Relación creada por batalla épica."
        )

        create_relation(
            source={
                "id": loser_id,
                "name": loser_name,
                "type": loser["entity"]["type"]
            },
            relation_type=loser_relation,
            target={
                "id": winner_id,
                "name": winner_name,
                "type": winner["entity"]["type"]
            },
            notes="Relación creada por batalla épica."
        )

    winner_status = apply_final_status(
        winner,
        "BatallaEpica-Estado-Ganador"
    )

    loser_status = apply_final_status(
        loser,
        "BatallaEpica-Estado-Perdedor"
    )

    messages.append(f"{winner_name} gana la batalla.")
    messages.append(f"{winner_name} queda en estado: {winner_status}.")
    messages.append(f"{loser_name} queda en estado: {loser_status}.")

    if save_relationships:
        messages.append(
            f"Relación guardada: {winner_name} → {winner_relation} → {loser_name}."
        )
        messages.append(
            f"Relación guardada: {loser_name} → {loser_relation} → {winner_name}."
        )
    else:
        messages.append(
            f"Relación sugerida, no guardada: {winner_name} → {winner_relation} → {loser_name}."
        )
        messages.append(
            f"Relación sugerida, no guardada: {loser_name} → {loser_relation} → {winner_name}."
        )

    if allow_loot and not is_creature_participant(loser):
        loot = transfer_random_equipment(winner, loser)

        if loot:
            messages.append(f"{winner_name} toma como botín: {loot}.")

    session["aftermath_applied"] = True

    return {
        "applied": True,
        "messages": messages
    }