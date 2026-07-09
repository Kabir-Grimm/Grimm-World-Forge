import json
import os
from datetime import datetime


def save_entity(entity_type, entity_data):

    os.makedirs("entities", exist_ok=True)

    path = f"entities/{entity_type}.json"

    entities = []

    # =========================
    # Cargar existentes
    # =========================

    if os.path.exists(path):

        with open(path, "r", encoding="utf-8") as f:

            try:
                entities = json.load(f)

            except:
                entities = []

    # =========================
    # Metadata automática
    # =========================

    entity_data["created_at"] = (
        datetime.now().isoformat()
    )

    entity_data["id"] = (
        f"{entity_type}_{len(entities)+1}"
    )

    # =========================
    # Guardar
    # =========================

    entities.append(entity_data)

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            entities,
            f,
            indent=4,
            ensure_ascii=False
        )

    return entity_data["id"]