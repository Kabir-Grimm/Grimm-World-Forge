import json
import os


ENTITIES_DIR = "entities"


from services.entity_registry_service import (
    load_registry_entities,
    clear_registry_cache
)


def load_all_entities():
    return load_registry_entities(profile="editor")


def save_entity_update(updated_entity):
    source_file = updated_entity.get("_source_file")

    if not source_file:
        return False

    path = os.path.join(ENTITIES_DIR, source_file)

    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = []

    if not isinstance(data, list):
        return False

    entity_id = updated_entity.get("id")

    for index, entity in enumerate(data):
        if entity.get("id") == entity_id:
            clean_entity = dict(updated_entity)
            clean_entity.pop("_source_file", None)

            data[index] = clean_entity

            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            clear_registry_cache()
            return True

    return False