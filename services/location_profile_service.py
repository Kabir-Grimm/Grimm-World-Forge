# services/location_profile_service.py

import json
from pathlib import Path


class LocationProfileService:
    DEFAULT_PROFILES = {
        "port": {
            "display_name": "Puerto",
            "produces": {"fish": 5, "trade_goods": 3, "rumors": 2, "travelers": 2},
            "tags": ["port", "sea", "commerce", "travel"]
        },
        "university": {
            "display_name": "Universidad",
            "produces": {"knowledge": 5, "books": 3, "magic_research": 2, "scholars": 1},
            "tags": ["university", "knowledge", "magic", "research"]
        },
        "fortress": {
            "display_name": "Fortaleza",
            "produces": {"soldiers": 4, "weapons": 3, "recruits": 3, "security": 2},
            "tags": ["fortress", "military", "defense", "war"]
        },
        "village": {
            "display_name": "Villa",
            "produces": {"food": 5, "wood": 3, "livestock": 2, "workers": 2},
            "tags": ["village", "rural", "survival", "community"]
        },
        "ruins": {
            "display_name": "Ruinas",
            "produces": {"relics": 2, "ancient_knowledge": 2, "magic_residue": 3, "danger": 4},
            "tags": ["ruins", "ancient", "danger", "mystery"]
        }
    }

    RESOURCE_LABELS_ES = {
        "fish": "pescado",
        "trade_goods": "bienes comerciales",
        "rumors": "rumores",
        "travelers": "viajeros",
        "knowledge": "conocimiento",
        "books": "libros",
        "magic_research": "investigación mágica",
        "scholars": "eruditos",
        "soldiers": "soldados",
        "weapons": "armas",
        "recruits": "reclutas",
        "security": "seguridad",
        "food": "alimentos",
        "wood": "madera",
        "livestock": "ganado",
        "workers": "trabajadores",
        "relics": "reliquias",
        "ancient_knowledge": "conocimiento antiguo",
        "magic_residue": "residuo mágico",
        "danger": "peligro"
    }

    def __init__(self, profiles_path="data/location_profiles.json"):
        self.profiles_path = Path(profiles_path)
        self.profiles = self.load_profiles()

    def load_profiles(self):
        if not self.profiles_path.exists():
            self.save_profiles(self.DEFAULT_PROFILES)
            return self.DEFAULT_PROFILES.copy()

        try:
            with open(self.profiles_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return self.DEFAULT_PROFILES.copy()

    def save_profiles(self, profiles=None):
        self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
        data = profiles if profiles is not None else self.profiles

        with open(self.profiles_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def normalize_text(self, value):
        if not value:
            return ""
        return str(value).lower().strip().replace(" ", "_")

    def detect_location_role(self, node):
        """
        Detecta el rol productivo de un nodo del mapa.

        Compatible con nodos tipo:
        {
            "entity_id": "...",
            "name": "...",
            "type": "location",
            "x": 0,
            "y": 0,
            "state": {},
            "resources": {}
        }
        """

        if not node:
            return None

        data = node.get("data", {}) or {}
        meta = node.get("meta", {}) or {}

        direct_candidates = [
            node.get("location_role"),
            node.get("location_type"),
            node.get("role"),
            data.get("location_role"),
            data.get("location_type"),
            data.get("role"),
            data.get("category"),
            meta.get("location_role"),
            meta.get("location_type"),
            meta.get("role"),
            meta.get("category"),
        ]

        for candidate in direct_candidates:
            key = self.normalize_text(candidate)
            if key in self.profiles:
                return key

        node_tags = []
        node_tags.extend(node.get("tags", []) or [])
        node_tags.extend(data.get("tags", []) or [])
        node_tags.extend(meta.get("tags", []) or [])

        normalized_tags = {self.normalize_text(tag) for tag in node_tags}

        for profile_key, profile in self.profiles.items():
            profile_tags = {
                self.normalize_text(tag)
                for tag in profile.get("tags", [])
            }

            if profile_key in normalized_tags:
                return profile_key

            if normalized_tags.intersection(profile_tags):
                return profile_key

        return None

    def get_profile_for_node(self, node):
        role = self.detect_location_role(node)

        if not role:
            return None

        return self.profiles.get(role)

    def get_production_for_node(self, node):
        profile = self.get_profile_for_node(node)

        if not profile:
            return {}

        return profile.get("produces", {})

    def apply_basic_production_to_node(self, node):
        """
        Aplica producción real al nodo del mapa.

        Usa:
        node["state"]["resources"]

        También mantiene compatibilidad si ya existía:
        node["resources"]
        """

        if not node:
            return None

        production = self.get_production_for_node(node)

        if not production:
            return node

        node.setdefault("state", {})
        node["state"].setdefault("resources", {})

        for resource_name, amount in production.items():
            current_amount = node["state"]["resources"].get(resource_name, 0)
            node["state"]["resources"][resource_name] = current_amount + amount

        node["resources"] = node["state"]["resources"]

        return node

    def build_production_event_for_node(self, world_time, node):
        """
        Crea evento compatible con el Registro del Mundo.
        Usa entity_id, no id.
        """

        production = self.get_production_for_node(node)

        if not production:
            return None

        node_name = node.get("name", "Ubicación desconocida")

        produced_text = ", ".join(
            f"{self.RESOURCE_LABELS_ES.get(resource, resource)} +{amount}"
            for resource, amount in production.items()
        )

        return {
            "world_date": world_time,
            "event_type": "location_production",
            "title": f"{node_name} produjo recursos",
            "description": f"{node_name} generó {produced_text}.",
            "source": {
                "entity_id": node.get("entity_id"),
                "name": node_name,
                "type": node.get("type"),
                "location_role": self.detect_location_role(node)
            },
            "related": []
        }