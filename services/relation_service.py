import json
import os
import uuid
from datetime import datetime


RELATIONS_PATH = "entities/relations.json"


def load_relations():
    if not os.path.exists(RELATIONS_PATH):
        return []

    with open(RELATIONS_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            return []

    if not isinstance(data, list):
        return []

    return data


def save_relations(relations):
    os.makedirs("entities", exist_ok=True)

    with open(RELATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            relations,
            f,
            indent=4,
            ensure_ascii=False
        )


def ensure_relation_ids():
    relations = load_relations()
    changed = False

    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            continue

        if not relation.get("id"):
            relation["id"] = f"relation_{index + 1}_{uuid.uuid4().hex[:8]}"
            changed = True

        if not relation.get("created_at"):
            relation["created_at"] = datetime.now().isoformat()
            changed = True

    if changed:
        save_relations(relations)

    return relations


def create_relation(source, relation_type, target, notes=""):
    relations = ensure_relation_ids()

    relation = {
        "id": f"relation_{len(relations) + 1}_{uuid.uuid4().hex[:8]}",
        "source": source,
        "relation_type": relation_type,
        "target": target,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }

    relations.append(relation)
    save_relations(relations)

    return relation


def save_relation(source, relation_type, target, notes=""):
    """
    Alias de compatibilidad para código viejo.
    """
    return create_relation(
        source=source,
        relation_type=relation_type,
        target=target,
        notes=notes
    )


def delete_relation(relation_id):
    relations = ensure_relation_ids()

    new_relations = [
        relation
        for relation in relations
        if relation.get("id") != relation_id
    ]

    if len(new_relations) == len(relations):
        return False

    save_relations(new_relations)
    return True

def update_relation(relation_id, source, relation_type, target, notes=""):
    relations = ensure_relation_ids()

    for relation in relations:
        if relation.get("id") != relation_id:
            continue

        relation["source"] = source
        relation["relation_type"] = relation_type
        relation["target"] = target
        relation["notes"] = notes
        relation["updated_at"] = datetime.now().isoformat()

        save_relations(relations)
        return True

    return False


def get_relations_for_entity(entity_id):
    relations = ensure_relation_ids()
    results = []

    for relation in relations:
        source = relation.get("source", {})
        target = relation.get("target", {})

        if (
            source.get("id") == entity_id
            or target.get("id") == entity_id
        ):
            results.append(relation)

    return results


def get_outgoing_relations(entity_id, relation_types=None):
    relations = ensure_relation_ids()
    results = []

    normalized_types = None

    if relation_types:
        normalized_types = {
            item.lower()
            for item in relation_types
        }

    for relation in relations:
        source = relation.get("source", {})
        relation_type = relation.get("relation_type", "")

        if source.get("id") != entity_id:
            continue

        if normalized_types and relation_type.lower() not in normalized_types:
            continue

        results.append(relation)

    return results

def create_relation_if_missing(source, relation_type, target, notes=""):
    relations = ensure_relation_ids()

    source_id = source.get("id")
    target_id = target.get("id")

    for relation in relations:
        existing_source = relation.get("source", {})
        existing_target = relation.get("target", {})

        if (
            existing_source.get("id") == source_id
            and existing_target.get("id") == target_id
            and relation.get("relation_type") == relation_type
        ):
            return relation

    return create_relation(
        source=source,
        relation_type=relation_type,
        target=target,
        notes=notes
    )