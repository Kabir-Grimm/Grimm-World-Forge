from services.entity_registry_service import load_registry_entities


def load_world_entities():
    return load_registry_entities(profile="world")


def load_relation_entities():
    return load_registry_entities(profile="relations")


def load_encounter_entities():
    return load_registry_entities(profile="encounters")


def load_editor_entities():
    return load_registry_entities(profile="editor")