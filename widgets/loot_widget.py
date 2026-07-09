from widgets.base_generator_widget import BaseGeneratorWidget

from PySide6.QtWidgets import (
    QLabel,
    QComboBox,
    QHBoxLayout,
    QCheckBox
)

from core.parser import load_all_lists, weighted_choice
from utils.ui_helpers import sort_combobox


class LootWidget(BaseGeneratorWidget):

    ENTITY_PREFIX = "LOOT-"
    ENTITY_TYPE = "loot"
    ENTITY_LABEL = "Loot"

    def __init__(self, history_widget):
        super().__init__(history_widget)

        meta_layout = QHBoxLayout()

        meta_layout.addWidget(QLabel("Enfoque:"))

        self.focus_combo = QComboBox()
        self.focus_combo.addItems([
            "Aleatorio",
            "Recompensa menor",
            "Recompensa importante",
            "Botín común",
            "Hallazgo extraño",
            "Objeto narrativo",
            "Objeto peligroso",
            "Objeto valioso"
        ])
        sort_combobox(self.focus_combo)
        self.focus_combo.setCurrentText("Aleatorio")

        meta_layout.addWidget(self.focus_combo)

        meta_layout.addWidget(QLabel("Cantidad:"))

        self.amount_combo = QComboBox()
        self.amount_combo.addItems(["1", "2", "3", "5"])
        self.amount_combo.setCurrentText("1")

        meta_layout.addWidget(self.amount_combo)

        self.include_story_checkbox = QCheckBox("Agregar historia")
        self.include_story_checkbox.setChecked(True)
        meta_layout.addWidget(self.include_story_checkbox)

        self.include_complication_checkbox = QCheckBox("Agregar complicación")
        self.include_complication_checkbox.setChecked(True)
        meta_layout.addWidget(self.include_complication_checkbox)

        self.layout().insertLayout(1, meta_layout)

    def generate_entity(self):
        self.result.clear()
        self.generated_data = {}

        amount = int(self.amount_combo.currentText())
        generated_loot = []

        self.result.append("💎 LOOT GENERADO\n")

        for index in range(amount):
            loot = self.generate_single_loot()
            generated_loot.append(loot)

            self.result.append(
                self.format_loot_result(loot, index + 1)
            )

        if amount == 1:
            self.generated_data = generated_loot[0]
        else:
            self.generated_data = {
                f"Loot {i + 1}": loot
                for i, loot in enumerate(generated_loot)
            }

    def generate_single_loot(self):
        loot = {
            "Enfoque": self.get_focus(),
            "Categoría": self.roll_from_list("Loot-Categoria"),
            "Forma": self.roll_from_list("Loot-Forma-General"),
            "Rareza": self.roll_from_list("Loot-Rareza"),
            "Estado": self.roll_from_list("Loot-Estado"),
            "Origen": self.roll_from_list("Loot-Origen"),
            "Propiedad": self.roll_from_list("Loot-Propiedad")
        }

        if self.include_story_checkbox.isChecked():
            loot["Historia"] = self.roll_from_list("Loot-Historia")

        if self.include_complication_checkbox.isChecked():
            loot["Complicación"] = self.roll_from_list("Loot-Complicacion")

        loot["Nombre sugerido"] = self.build_loot_name(loot)

        return loot

    def get_focus(self):
        selected = self.focus_combo.currentText()

        if selected != "Aleatorio":
            return selected

        return weighted_choice([
            ("Recompensa menor", 6),
            ("Botín común", 6),
            ("Recompensa importante", 3),
            ("Hallazgo extraño", 3),
            ("Objeto narrativo", 3),
            ("Objeto peligroso", 2),
            ("Objeto valioso", 4)
        ])

    def roll_from_list(self, list_name):
        for oracle in load_all_lists():
            if oracle["name"] != list_name:
                continue

            data = oracle.get("data", {})
            options = []

            if "Resultados" in data:
                options = data["Resultados"]
            else:
                for values in data.values():
                    options.extend(values)

            if options:
                return weighted_choice(options).split("|")[0].strip()

        return "No encontrado"

    def build_loot_name(self, loot):
        category = loot.get("Categoría", "")
        rarity = loot.get("Rareza", "")
        state = loot.get("Estado", "")
        form = loot.get("Forma", "")

        if rarity in [
            "Legendario",
            "Único",
            "Último conocido",
            "Prohibido",
            "Irrepetible"
        ]:
            return f"{category} {rarity.lower()}"

        if state in [
            "Sellado",
            "Inestable",
            "Corrupto",
            "Casi destruido",
            "Dañado gravemente"
        ]:
            return f"{category} {state.lower()}"

        return f"{category} - {form}"

    def format_loot_result(self, loot, number):
        lines = [
            "══════════════════",
            f"💎 HALLAZGO {number}",
            "══════════════════"
        ]

        for key, value in loot.items():
            lines.append(f"{key}: {value}")

        lines.append("")
        return "\n".join(lines)

    def save_entity_data(self):
        if not self.generated_data:
            return

        name = (
            self.name_input.text().strip()
            or self.get_default_name()
        )

        entity = {
            "name": name,
            "type": self.ENTITY_TYPE,
            "meta": self.generate_loot_meta(),
            "data": self.generated_data
        }

        from services.entity_service import save_entity
        from services.world_service import add_entity_to_world
        from core.system_log import add_system_log

        entity_id = save_entity(
            self.ENTITY_TYPE,
            entity
        )

        entity["id"] = entity_id

        world_id = self.world_combo.currentData()

        if world_id:
            add_entity_to_world(world_id, entity)

        self.result.append(
            "\n"
            "💾 LOOT GUARDADO\n"
            f"ID: {entity_id}\n"
            f"Nombre: {name}\n"
            f"Rareza: {entity['meta'].get('rarity')}\n"
        )

        add_system_log(
            self.history,
            f"💾 Loot guardado → {name} ({entity_id})"
        )

    def save_current_entity(self):
        self.save_entity_data()

    def generate_loot_meta(self):
        if isinstance(self.generated_data, dict):
            if "Rareza" in self.generated_data:
                return {
                    "focus": self.generated_data.get("Enfoque", "Desconocido"),
                    "category": self.generated_data.get("Categoría", "Desconocida"),
                    "rarity": self.generated_data.get("Rareza", "Desconocida"),
                    "state": self.generated_data.get("Estado", "Desconocido"),
                    "active": True
                }

        return {
            "focus": self.focus_combo.currentText(),
            "category": "Múltiple",
            "rarity": "Variable",
            "state": "Variable",
            "active": True
        }

    def get_default_name(self):
        if isinstance(self.generated_data, dict):
            if "Nombre sugerido" in self.generated_data:
                return self.generated_data["Nombre sugerido"]

        return "Loot sin nombre"