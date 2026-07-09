from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QCheckBox,
    QListWidget, QTabWidget, QScrollArea, QGroupBox
)

from services.entity_editor_service import (
    load_all_entities,
    save_entity_update
)

from services.world_service import (
    load_worlds,
    add_entity_to_world
)

from core.system_log import add_system_log
from core.parser import load_all_lists
from utils.ui_helpers import sort_combobox
from core.display_names import display_entity_type


DEFAULT_EFFECT_STATS = [
    "combat",
    "defense",
    "damage",
    "resistance",
    "social",
    "arcane",
    "control",
    "stealth",
    "knowledge",
    "influence",
    "initiative",
    "risk",
    "death_risk",
    "injury_risk",
    "mutual_damage",
    "escape"
]


class EntityEditorWidget(QWidget):

    NPC_TYPES = {"npcs", "npc"}

    EFFECT_TYPES = {
        "weapons", "weapon",
        "armors", "armor",
        "relics", "relic",
        "items", "item",
        "magic_systems", "magic_system",
        "spells", "spell",
        "foods", "food",
        "armies", "army",
        "kingdoms", "kingdom",
        "creatures", "creature",
        "factions", "faction",
        "npcs", "npc"
    }

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []
        self.current_entity = None
        self.available_traits = []
        self.available_statuses = []
        self.field_cards = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        selector_layout = QHBoxLayout()

        selector_layout.addWidget(QLabel("Tipo:"))

        self.type_combo = QComboBox()
        selector_layout.addWidget(self.type_combo)

        selector_layout.addWidget(QLabel("Entidad:"))

        self.entity_combo = QComboBox()
        selector_layout.addWidget(self.entity_combo)

        self.refresh_btn = QPushButton("Refrescar")
        selector_layout.addWidget(self.refresh_btn)

        layout.addLayout(selector_layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.main_tab = QWidget()
        self.fields_tab = QWidget()
        self.effects_tab = QWidget()

        self.tabs.addTab(self.main_tab, "📝 Identidad")
        self.tabs.addTab(self.fields_tab, "📋 Campos generados")
        self.tabs.addTab(self.effects_tab, "⚙ Efectos")

        self.setup_main_tab()
        self.setup_fields_tab()
        self.setup_effects_tab()

        buttons = QHBoxLayout()

        self.save_btn = QPushButton("Guardar cambios")
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        self.refresh_btn.clicked.connect(self.load_entities)
        self.type_combo.currentIndexChanged.connect(self.populate_entity_combo)
        self.entity_combo.currentIndexChanged.connect(self.load_selected_entity)
        self.save_btn.clicked.connect(self.save_changes)

        self.load_worlds()
        self.load_statuses()
        self.load_traits()
        self.load_entities()
        self.clear_editor()

    # =========================
    # UI tabs
    # =========================

    def setup_main_tab(self):
        layout = QVBoxLayout()
        self.main_tab.setLayout(layout)

        self.id_label = QLabel("ID: -")
        self.type_label = QLabel("Tipo: -")

        layout.addWidget(self.id_label)
        layout.addWidget(self.type_label)

        layout.addWidget(QLabel("Nombre:"))

        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Notas:"))

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)
        layout.addWidget(self.notes_input)

        layout.addWidget(QLabel("Asignar a mundo:"))

        self.world_combo = QComboBox()
        layout.addWidget(self.world_combo)

        self.map_enabled_checkbox = QCheckBox("🗺 Mostrar en mapa")
        self.map_enabled_checkbox.setToolTip(
            "Permite que esta entidad aparezca disponible en el Mapa de Mundo."
        )
        layout.addWidget(self.map_enabled_checkbox)

        self.npc_meta_label = QLabel("Metadata NPC:")
        layout.addWidget(self.npc_meta_label)

        npc_meta_layout = QHBoxLayout()

        npc_meta_layout.addWidget(QLabel("Importancia:"))

        self.importance_combo = QComboBox()
        self.importance_combo.addItems([
            "Común",
            "Importante",
            "Protagonista",
            "Antagonista",
            "Líder",
            "Héroe",
            "Villano",
            "Entidad clave"
        ])
        sort_combobox(self.importance_combo)
        npc_meta_layout.addWidget(self.importance_combo)

        npc_meta_layout.addWidget(QLabel("Rol:"))

        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Neutral",
            "Aliado",
            "Rival",
            "Mentor",
            "Enemigo",
            "Gobernante",
            "Mercenario",
            "Guardián",
            "Profeta",
            "Agente oculto"
        ])
        sort_combobox(self.role_combo)
        npc_meta_layout.addWidget(self.role_combo)

        npc_meta_layout.addWidget(QLabel("Poder:"))

        self.power_rank_combo = QComboBox()
        self.power_rank_combo.addItems([
            "Aleatorio",
            "Débil",
            "Común",
            "Competente",
            "Fuerte",
            "Excepcional",
            "Legendario"
        ])
        sort_combobox(self.power_rank_combo)
        npc_meta_layout.addWidget(self.power_rank_combo)

        npc_meta_layout.addWidget(QLabel("Género:"))

        self.gender_combo = QComboBox()
        self.gender_combo.addItems([
            "Desconocido",
            "Masculino",
            "Femenino",
            "Neutro"
        ])
        sort_combobox(self.gender_combo)
        npc_meta_layout.addWidget(self.gender_combo)

        npc_meta_layout.addWidget(QLabel("Estado:"))

        self.status_combo = QComboBox()
        npc_meta_layout.addWidget(self.status_combo)

        self.active_checkbox = QCheckBox("Activo")
        self.active_checkbox.setChecked(True)
        npc_meta_layout.addWidget(self.active_checkbox)

        layout.addLayout(npc_meta_layout)

        self.narrative_label = QLabel("Datos narrativos:")
        layout.addWidget(self.narrative_label)

        narrative_layout_1 = QHBoxLayout()

        narrative_layout_1.addWidget(QLabel("Edad:"))

        self.age_input = QLineEdit()
        narrative_layout_1.addWidget(self.age_input)

        narrative_layout_1.addWidget(QLabel("Etapa:"))

        self.life_stage_combo = QComboBox()
        self.life_stage_combo.addItems([
            "Desconocida",
            "Infancia",
            "Adolescencia",
            "Juventud",
            "Adultez",
            "Madurez",
            "Vejez",
            "Antigua",
            "Inmortal"
        ])
        sort_combobox(self.life_stage_combo)
        narrative_layout_1.addWidget(self.life_stage_combo)

        narrative_layout_1.addWidget(QLabel("Reputación:"))

        self.reputation_input = QLineEdit()
        narrative_layout_1.addWidget(self.reputation_input)

        layout.addLayout(narrative_layout_1)

        narrative_layout_2 = QHBoxLayout()

        narrative_layout_2.addWidget(QLabel("Objetivo:"))

        self.goal_input = QLineEdit()
        narrative_layout_2.addWidget(self.goal_input)

        narrative_layout_2.addWidget(QLabel("Miedo:"))

        self.fear_input = QLineEdit()
        narrative_layout_2.addWidget(self.fear_input)

        narrative_layout_2.addWidget(QLabel("Deseo:"))

        self.desire_input = QLineEdit()
        narrative_layout_2.addWidget(self.desire_input)

        layout.addLayout(narrative_layout_2)

        self.traits_label = QLabel("Rasgos / Poderes:")
        layout.addWidget(self.traits_label)

        traits_layout = QHBoxLayout()

        self.trait_search = QLineEdit()
        self.trait_search.setPlaceholderText("Buscar rasgo...")
        traits_layout.addWidget(self.trait_search)

        self.trait_combo = QComboBox()
        traits_layout.addWidget(self.trait_combo)

        self.add_trait_btn = QPushButton("Agregar rasgo")
        traits_layout.addWidget(self.add_trait_btn)

        self.remove_trait_btn = QPushButton("Quitar rasgo")
        traits_layout.addWidget(self.remove_trait_btn)

        layout.addLayout(traits_layout)

        self.traits_list = QListWidget()
        self.traits_list.setMaximumHeight(120)
        layout.addWidget(self.traits_list)

        self.trait_search.textChanged.connect(self.populate_trait_combo)
        self.add_trait_btn.clicked.connect(self.add_trait)
        self.remove_trait_btn.clicked.connect(self.remove_selected_trait)

    def setup_fields_tab(self):
        layout = QVBoxLayout()
        self.fields_tab.setLayout(layout)

        top = QHBoxLayout()

        self.new_field_name_input = QLineEdit()
        self.new_field_name_input.setPlaceholderText("Nombre del campo")

        self.new_field_value_input = QLineEdit()
        self.new_field_value_input.setPlaceholderText("Valor inicial")

        self.add_field_card_btn = QPushButton("Agregar campo")
        self.clear_fields_btn = QPushButton("Limpiar campos")

        top.addWidget(QLabel("Campo:"))
        top.addWidget(self.new_field_name_input)
        top.addWidget(QLabel("Valor:"))
        top.addWidget(self.new_field_value_input)
        top.addWidget(self.add_field_card_btn)
        top.addWidget(self.clear_fields_btn)

        layout.addLayout(top)

        self.fields_scroll = QScrollArea()
        self.fields_scroll.setWidgetResizable(True)

        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout()
        self.fields_container.setLayout(self.fields_layout)

        self.fields_scroll.setWidget(self.fields_container)
        layout.addWidget(self.fields_scroll)

        self.add_field_card_btn.clicked.connect(self.add_field_from_inputs)
        self.clear_fields_btn.clicked.connect(self.clear_field_cards)

    def setup_effects_tab(self):
        layout = QVBoxLayout()
        self.effects_tab.setLayout(layout)

        self.effects_label = QLabel("Efectos mecánicos:")
        layout.addWidget(self.effects_label)

        self.effects_table = QTableWidget()
        self.effects_table.setColumnCount(2)
        self.effects_table.setHorizontalHeaderLabels([
            "Stat",
            "Valor"
        ])

        layout.addWidget(self.effects_table)

        effects_buttons = QHBoxLayout()

        self.add_effect_btn = QPushButton("Agregar efecto")
        self.delete_effect_btn = QPushButton("Eliminar efecto")

        effects_buttons.addWidget(self.add_effect_btn)
        effects_buttons.addWidget(self.delete_effect_btn)

        layout.addLayout(effects_buttons)

        self.add_effect_btn.clicked.connect(self.add_effect)
        self.delete_effect_btn.clicked.connect(self.delete_selected_effect)

    # =========================
    # Mundos / estados / rasgos
    # =========================

    def load_worlds(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin asignar", None)

        worlds = load_worlds()
        worlds.sort(key=lambda world: world.get("name", "").lower())

        for world in worlds:
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

        sort_combobox(self.world_combo)

    def load_statuses(self):
        self.available_statuses = ["Sano"]

        for oracle in load_all_lists():
            if oracle["name"] != "Entidades-Estados":
                continue

            data = oracle.get("data", {})
            options = []

            if "Resultados" in data:
                options = data["Resultados"]
            else:
                for values in data.values():
                    options.extend(values)

            for raw_text, _weight in options:
                name = raw_text.split("|")[0].strip()

                if name and name not in self.available_statuses:
                    self.available_statuses.append(name)

        self.available_statuses.sort(key=str.lower)

        self.status_combo.clear()
        self.status_combo.addItems(self.available_statuses)
        sort_combobox(self.status_combo)

    def load_traits(self):
        self.available_traits = []

        allowed_lists = {
            "Entidades-Rasgos",
            "Entidades-Rasgos-Poderes"
        }

        for oracle in load_all_lists():
            if oracle["name"] not in allowed_lists:
                continue

            data = oracle.get("data", {})
            options = []

            if "Resultados" in data:
                options = data["Resultados"]
            else:
                for values in data.values():
                    options.extend(values)

            for raw_text, _weight in options:
                name = raw_text.split("|")[0].strip()

                if name and name not in self.available_traits:
                    self.available_traits.append(name)

        self.available_traits.sort(key=str.lower)
        self.populate_trait_combo()

    def populate_trait_combo(self):
        search = self.trait_search.text().lower().strip()
        current = self.trait_combo.currentText()

        self.trait_combo.clear()

        for trait in self.available_traits:
            if search and search not in trait.lower():
                continue

            self.trait_combo.addItem(trait)

        sort_combobox(self.trait_combo)

        if current:
            index = self.trait_combo.findText(current)

            if index >= 0:
                self.trait_combo.setCurrentIndex(index)

    # =========================
    # Entidades
    # =========================

    def load_entities(self):
        self.entities = load_all_entities()

        self.populate_type_combo()
        self.populate_entity_combo()

        add_system_log(
            self.history,
            "📝 Editor de entidades actualizado"
        )

    def populate_type_combo(self):
        current_type = self.type_combo.currentData()

        types = sorted({
            entity.get("type", "entity")
            for entity in self.entities
        }, key=str.lower)

        self.type_combo.blockSignals(True)
        self.type_combo.clear()

        self.type_combo.addItem("Todos", None)

        for entity_type in types:
            self.type_combo.addItem(entity_type, entity_type)

        sort_combobox(self.type_combo)
        self.type_combo.blockSignals(False)

        if current_type:
            index = self.type_combo.findData(current_type)

            if index >= 0:
                self.type_combo.setCurrentIndex(index)

    def populate_entity_combo(self):
        selected_type = self.type_combo.currentData()
        current_entity_id = self.entity_combo.currentData()

        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()

        filtered = []

        for entity in self.entities:
            if selected_type and entity.get("type") != selected_type:
                continue

            filtered.append(entity)

        filtered.sort(
            key=lambda item: (
                item.get("type", "").lower(),
                item.get("name", "").lower()
            )
        )

        for entity in filtered:
            self.entity_combo.addItem(
                self.format_entity_label(entity),
                entity.get("id")
            )

        sort_combobox(self.entity_combo)
        self.entity_combo.blockSignals(False)

        if current_entity_id:
            index = self.entity_combo.findData(current_entity_id)

            if index >= 0:
                self.entity_combo.setCurrentIndex(index)

        self.load_selected_entity()

    def format_entity_label(self, entity):
        return (
            f"{entity.get('name', 'Sin nombre')} "
            f"[{display_entity_type(entity.get('type', 'entity'))}] "
            f"({entity.get('id', 'sin_id')})"
        )

    def load_selected_entity(self):
        entity_id = self.entity_combo.currentData()

        self.current_entity = None

        for entity in self.entities:
            if entity.get("id") == entity_id:
                self.current_entity = entity
                break

        if not self.current_entity:
            self.clear_editor()
            return

        self.id_label.setText(
            f"ID: {self.current_entity.get('id', '-')}"
        )

        self.type_label.setText(
            f"Tipo: {self.current_entity.get('type', '-')}"
        )

        self.name_input.setText(
            self.current_entity.get("name", "")
        )

        self.notes_input.setText(
            self.current_entity.get("notes", "")
        )

        self.map_enabled_checkbox.setChecked(
            self.current_entity.get("map_enabled", False)
        )

        self.load_npc_meta()
        self.load_traits_for_entity()
        self.load_field_cards(
            self.current_entity.get("data", {})
        )
        self.load_effects_table(
            self.current_entity.get("effects", {})
        )

    # =========================
    # NPC meta
    # =========================

    def load_npc_meta(self):
        entity_type = self.current_entity.get("type", "")
        is_npc = entity_type in self.NPC_TYPES

        self.set_npc_widgets_visible(is_npc)

        if not is_npc:
            return

        meta = self.current_entity.get("meta", {})

        self.set_combo_value(
            self.importance_combo,
            meta.get("importance", "Común")
        )

        self.set_combo_value(
            self.role_combo,
            meta.get("role", "Neutral")
        )

        self.set_combo_value(
            self.power_rank_combo,
            meta.get("power_rank", "Aleatorio")
        )

        self.set_combo_value(
            self.gender_combo,
            meta.get("gender", "Desconocido")
        )

        self.set_combo_value(
            self.status_combo,
            meta.get("status", "Sano")
        )

        self.active_checkbox.setChecked(
            meta.get("active", True)
        )

        self.age_input.setText(str(meta.get("age", "")))

        self.set_combo_value(
            self.life_stage_combo,
            meta.get("life_stage", "Desconocida")
        )

        self.reputation_input.setText(
            meta.get("reputation", "")
        )

        self.goal_input.setText(
            meta.get("personal_goal", "")
        )

        self.fear_input.setText(
            meta.get("fear", "")
        )

        self.desire_input.setText(
            meta.get("desire", "")
        )

    def set_combo_value(self, combo, value):
        if not combo:
            return

        index = combo.findText(str(value))

        if index >= 0:
            combo.setCurrentIndex(index)

    def set_npc_widgets_visible(self, visible):
        widgets = [
            self.npc_meta_label,
            self.importance_combo,
            self.role_combo,
            self.power_rank_combo,
            self.gender_combo,
            self.status_combo,
            self.active_checkbox,
            self.narrative_label,
            self.age_input,
            self.life_stage_combo,
            self.reputation_input,
            self.goal_input,
            self.fear_input,
            self.desire_input,
            self.traits_label,
            self.trait_search,
            self.trait_combo,
            self.add_trait_btn,
            self.remove_trait_btn,
            self.traits_list
        ]

        for widget in widgets:
            if widget:
                widget.setVisible(visible)

    # =========================
    # Rasgos
    # =========================

    def load_traits_for_entity(self):
        self.traits_list.clear()

        if not self.current_entity:
            return

        meta = self.current_entity.get("meta", {})
        traits = meta.get("traits", [])

        if not isinstance(traits, list):
            traits = []

        for trait in sorted(traits, key=str.lower):
            self.traits_list.addItem(trait)

    def add_trait(self):
        if not self.current_entity:
            return

        trait = self.trait_combo.currentText().strip()

        if not trait:
            return

        existing = self.get_current_traits_from_ui()

        if trait in existing:
            return

        self.traits_list.addItem(trait)

    def remove_selected_trait(self):
        row = self.traits_list.currentRow()

        if row >= 0:
            self.traits_list.takeItem(row)

    def get_current_traits_from_ui(self):
        return [
            self.traits_list.item(i).text()
            for i in range(self.traits_list.count())
        ]

    # =========================
    # Campos generados visuales
    # =========================

    def clear_field_cards(self):
        for card in self.field_cards:
            card.setParent(None)
            card.deleteLater()

        self.field_cards = []

    def load_field_cards(self, data):
        self.clear_field_cards()

        if not isinstance(data, dict):
            return

        for key, value in sorted(data.items()):
            self.add_field_card(key, value)

    def add_field_from_inputs(self):
        key = self.new_field_name_input.text().strip()
        value = self.new_field_value_input.text().strip()

        if not key:
            key = "Nuevo campo"

        if not value:
            value = "Nuevo valor"

        self.add_field_card(key, value)

        self.new_field_name_input.clear()
        self.new_field_value_input.clear()

    def add_field_card(self, key="", value=""):
        card = QGroupBox(str(key))
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)

        key_input = QLineEdit()
        key_input.setText(str(key))
        key_input.setPlaceholderText("Campo")

        value_input = QTextEdit()

        if isinstance(value, (dict, list)):
            import json
            value_input.setText(
                json.dumps(
                    value,
                    indent=4,
                    ensure_ascii=False
                )
            )
        else:
            value_input.setText(str(value))

        value_input.setMaximumHeight(100)

        delete_btn = QPushButton("Eliminar campo")

        card_layout.addWidget(QLabel("Campo:"))
        card_layout.addWidget(key_input)
        card_layout.addWidget(QLabel("Valor:"))
        card_layout.addWidget(value_input)
        card_layout.addWidget(delete_btn)

        card.key_input = key_input
        card.value_input = value_input

        delete_btn.clicked.connect(
            lambda: self.remove_field_card(card)
        )

        key_input.textChanged.connect(
            lambda text, c=card: c.setTitle(text or "Campo sin nombre")
        )

        self.fields_layout.addWidget(card)
        self.field_cards.append(card)

    def remove_field_card(self, card):
        if card in self.field_cards:
            self.field_cards.remove(card)

        card.setParent(None)
        card.deleteLater()

    def get_fields_from_cards(self):
        data = {}

        for card in self.field_cards:
            key = card.key_input.text().strip()
            value = card.value_input.toPlainText().strip()

            if not key:
                continue

            data[key] = self.parse_field_value(value)

        return data

    def parse_field_value(self, value):
        text = str(value).strip()

        if not text:
            return ""

        if (
            text.startswith("{")
            and text.endswith("}")
        ) or (
            text.startswith("[")
            and text.endswith("]")
        ):
            try:
                import json
                return json.loads(text)
            except Exception:
                return text

        return text

    # =========================
    # Efectos
    # =========================

    def load_effects_table(self, effects):
        self.effects_tab.setEnabled(True)
        self.effects_table.setRowCount(0)

        if not isinstance(effects, dict):
            effects = {}

        normalized = {}

        for stat in DEFAULT_EFFECT_STATS:
            normalized[stat] = int(effects.get(stat, 0))

        for key, value in effects.items():
            if key not in normalized:
                normalized[key] = value

        for key, value in sorted(normalized.items()):
            row = self.effects_table.rowCount()
            self.effects_table.insertRow(row)

            self.effects_table.setItem(
                row,
                0,
                QTableWidgetItem(str(key))
            )

            self.effects_table.setItem(
                row,
                1,
                QTableWidgetItem(str(value))
            )

    def add_effect(self):
        row = self.effects_table.rowCount()
        self.effects_table.insertRow(row)

        self.effects_table.setItem(
            row,
            0,
            QTableWidgetItem("combat")
        )

        self.effects_table.setItem(
            row,
            1,
            QTableWidgetItem("1")
        )

    def delete_selected_effect(self):
        row = self.effects_table.currentRow()

        if row >= 0:
            self.effects_table.removeRow(row)

    def get_effects_from_ui(self):
        effects = {}

        for row in range(self.effects_table.rowCount()):
            key_item = self.effects_table.item(row, 0)
            value_item = self.effects_table.item(row, 1)

            if not key_item:
                continue

            key = key_item.text().strip()

            if not key:
                continue

            try:
                value = int(value_item.text().strip()) if value_item else 0
            except Exception:
                value = 0

            effects[key] = value

        return effects

    # =========================
    # Guardar
    # =========================

    def save_changes(self):
        if not self.current_entity:
            return

        self.current_entity["name"] = (
            self.name_input.text().strip()
            or "Sin nombre"
        )

        self.current_entity["notes"] = (
            self.notes_input.toPlainText().strip()
        )

        self.current_entity["map_enabled"] = (
            self.map_enabled_checkbox.isChecked()
        )

        self.current_entity["data"] = self.get_fields_from_cards()

        entity_type = self.current_entity.get("type", "")

        if entity_type in self.NPC_TYPES:
            old_meta = self.current_entity.get("meta", {})

            self.current_entity["meta"] = {
                **old_meta,
                "importance": self.importance_combo.currentText(),
                "role": self.role_combo.currentText(),
                "power_rank": self.power_rank_combo.currentText(),
                "gender": self.gender_combo.currentText(),
                "status": self.status_combo.currentText(),
                "active": self.active_checkbox.isChecked(),
                "age": self.age_input.text().strip(),
                "life_stage": self.life_stage_combo.currentText(),
                "reputation": self.reputation_input.text().strip(),
                "personal_goal": self.goal_input.text().strip(),
                "fear": self.fear_input.text().strip(),
                "desire": self.desire_input.text().strip(),
                "traits": self.get_current_traits_from_ui()
            }

        self.current_entity["effects"] = self.get_effects_from_ui()

        ok = save_entity_update(self.current_entity)

        world_id = self.world_combo.currentData()

        if ok and world_id:
            add_entity_to_world(
                world_id,
                self.current_entity
            )

        if ok:
            QMessageBox.information(
                self,
                "Guardado",
                "Entidad actualizada correctamente."
            )

            add_system_log(
                self.history,
                f"📝 Entidad editada → {self.current_entity['name']}"
            )

            self.load_entities()

        else:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo guardar la entidad."
            )

    # =========================
    # Limpiar
    # =========================

    def clear_editor(self):
        self.id_label.setText("ID: -")
        self.type_label.setText("Tipo: -")
        self.name_input.clear()
        self.notes_input.clear()
        self.map_enabled_checkbox.setChecked(False)
        self.traits_list.clear()
        self.clear_field_cards()
        self.effects_table.setRowCount(0)

        self.set_npc_widgets_visible(False)
        self.effects_tab.setEnabled(False)