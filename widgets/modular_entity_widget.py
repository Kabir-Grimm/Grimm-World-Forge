from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QGridLayout,
    QComboBox
)

from datetime import datetime

from core.parser import load_all_lists, weighted_choice
from services.entity_service import save_entity
from services.world_service import load_worlds, add_entity_to_world
from services.item_effect_service import generate_item_effects
from services.name_generator_service import generate_entity_name
from services.modifier_service import (
    parse_modifier_line,
    clean_modifier_text,
    merge_modifiers
)
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class ModularEntityWidget(QWidget):

    EFFECT_ENTITY_TYPES = {
        "weapons",
        "armors",
        "relics",
        "magic_systems",
        "foods",
        "armies",
        "kingdoms",
        "creatures"
    }

    def __init__(
        self,
        history_widget,
        prefix,
        entity_type,
        entity_label
    ):
        super().__init__()

        self.history = history_widget
        self.prefix = prefix
        self.entity_type = entity_type
        self.entity_label = entity_label

        self.generated_data = {}
        self.generated_effects = {}
        self.generated_rarity = None

        self.checkboxes = {}
        self.selected_order = []

        all_lists = load_all_lists()

        self.oracles = [
            oracle for oracle in all_lists
            if oracle["name"].startswith(self.prefix)
        ]

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            QLabel(f"🧩 Generador de {self.entity_label}")
        )

        # =========================
        # Nombre
        # =========================

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            f"Nombre de {self.entity_label}"
        )

        name_layout.addWidget(self.name_input)

        self.name_style_combo = QComboBox()
        self.name_style_combo.addItems([
            "universal",
            "fantasy",
            "dark_fantasy",
            "cyberpunk",
            "modern",
            "cosmic"
        ])

        name_layout.addWidget(self.name_style_combo)

        self.random_name_btn = QPushButton("🎲")
        self.random_name_btn.setToolTip(
            "Generar nombre aleatorio"
        )
        self.random_name_btn.clicked.connect(
            self.generate_random_name
        )

        name_layout.addWidget(self.random_name_btn)

        layout.addLayout(name_layout)

        # =========================
        # Mundo
        # =========================

        world_layout = QHBoxLayout()
        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        self.load_world_options()

        world_layout.addWidget(self.world_combo)
        layout.addLayout(world_layout)

        layout.addWidget(QLabel("Categorías:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(180)

        scroll_widget = QWidget()
        grid = QGridLayout()
        scroll_widget.setLayout(grid)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        row = 0
        col = 0

        for oracle in self.oracles:
            clean_name = self.clean_category_name(
                oracle["name"]
            )

            cb = QCheckBox(clean_name)
            cb.setChecked(True)

            self.checkboxes[clean_name] = {
                "checkbox": cb,
                "oracle": oracle
            }

            self.selected_order.append(clean_name)

            cb.stateChanged.connect(
                lambda state, n=clean_name:
                self.update_selection_order(n, state)
            )

            grid.addWidget(cb, row, col)

            col += 1

            if col >= 2:
                col = 0
                row += 1

        buttons = QHBoxLayout()

        self.select_all_btn = QPushButton("✔ Todo")
        self.clear_all_btn = QPushButton("✖ Nada")
        self.generate_btn = QPushButton(
            f"🎲 Generar {self.entity_label}"
        )
        self.save_btn = QPushButton(
            f"💾 Guardar {self.entity_label}"
        )

        buttons.addWidget(self.select_all_btn)
        buttons.addWidget(self.clear_all_btn)
        buttons.addWidget(self.generate_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        self.result = QTextEdit()
        layout.addWidget(self.result)

        self.select_all_btn.clicked.connect(self.select_all)
        self.clear_all_btn.clicked.connect(self.clear_all)
        self.generate_btn.clicked.connect(self.generate_entity)
        self.save_btn.clicked.connect(self.save_current_entity)

    # =====================================
    # Generador de nombres
    # =====================================

    def generate_random_name(self):
        style = self.name_style_combo.currentText()

        generated_name = generate_entity_name(
            entity_type=self.entity_type,
            style=style,
            gender="Aleatorio"
        )

        self.name_input.setText(generated_name)

        add_system_log(
            self.history,
            f"🎲 Nombre generado → {generated_name}"
        )

    def clean_category_name(self, name):
        return name.replace(self.prefix, "").strip()

    def load_world_options(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

        sort_combobox(self.world_combo)

    def update_selection_order(self, name, state):
        if state:
            if name not in self.selected_order:
                self.selected_order.append(name)
        else:
            if name in self.selected_order:
                self.selected_order.remove(name)

    def select_all(self):
        self.selected_order = []

        for name, data in self.checkboxes.items():
            cb = data["checkbox"]
            cb.setChecked(True)

            if name not in self.selected_order:
                self.selected_order.append(name)

    def clear_all(self):
        self.selected_order = []

        for data in self.checkboxes.values():
            data["checkbox"].setChecked(False)

    def supports_effects(self):
        return self.entity_type in self.EFFECT_ENTITY_TYPES

    def add_generated_result(self, category, raw_result, output):
        visible_result = clean_modifier_text(raw_result)
        _name, modifiers = parse_modifier_line(raw_result)

        self.generated_data[category] = visible_result
        output.append(f"{category}: {visible_result}")

        if modifiers:
            self.generated_effects = merge_modifiers(
                self.generated_effects,
                modifiers
            )

    def generate_entity(self):
        self.generated_data = {}
        self.generated_effects = {}
        self.generated_rarity = None

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        output = [
            "\n══════════════════════",
            f"🧩 {self.entity_label.upper()} GENERADO",
            f"🕒 {timestamp}",
            "══════════════════════\n"
        ]

        for category in self.selected_order:
            item = self.checkboxes.get(category)

            if not item:
                continue

            oracle = item["oracle"]
            data = oracle["data"]

            if "Resultados" in data:
                options = data["Resultados"]

                raw_result = (
                    weighted_choice(options)
                    if options
                    else "SIN RESULTADOS"
                )

                self.add_generated_result(
                    category,
                    raw_result,
                    output
                )

            else:
                for subcat, options in data.items():
                    raw_result = (
                        weighted_choice(options)
                        if options
                        else "SIN RESULTADOS"
                    )

                    key = f"{category} - {subcat}"

                    self.add_generated_result(
                        key,
                        raw_result,
                        output
                    )

        if self.supports_effects():
            rarity, random_effects = generate_item_effects(
                self.entity_type
            )

            self.generated_rarity = rarity

            self.generated_effects = merge_modifiers(
                self.generated_effects,
                random_effects
            )

            self.generated_data["Rareza"] = rarity

            output.append("")
            output.append("✦ Propiedades mecánicas:")
            output.append(f"Rareza: {rarity}")

            if self.generated_effects:
                output.append("Efectos:")

                for stat, value in self.generated_effects.items():
                    sign = "+" if value >= 0 else ""
                    output.append(
                        f"- {stat}: {sign}{value}"
                    )

        text = "\n".join(output)

        self.result.append(text)

        add_system_log(
            self.history,
            f"🧩 {self.entity_label} generado"
        )

        scrollbar = self.result.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def save_current_entity(self):
        if not self.generated_data:
            return

        name = (
            self.name_input.text().strip()
            or f"{self.entity_label} Sin Nombre"
        )

        entity = {
            "name": name,
            "type": self.entity_type,
            "data": self.generated_data
        }

        if self.generated_rarity:
            entity["rarity"] = self.generated_rarity

        if self.generated_effects:
            entity["effects"] = self.generated_effects

        entity_id = save_entity(
            self.entity_type,
            entity
        )

        entity["id"] = entity_id

        world_id = self.world_combo.currentData()

        if world_id:
            add_entity_to_world(
                world_id,
                entity
            )

        self.result.append(
            "\n"
            f"💾 {self.entity_label.upper()} GUARDADO\n"
            f"ID: {entity_id}"
        )

        if self.generated_rarity:
            self.result.append(
                f"Rareza: {self.generated_rarity}"
            )

        if self.generated_effects:
            self.result.append("Efectos:")

            for stat, value in self.generated_effects.items():
                sign = "+" if value >= 0 else ""
                self.result.append(
                    f"- {stat}: {sign}{value}"
                )

        self.result.append("")

        add_system_log(
            self.history,
            (
                f"💾 {self.entity_label} guardado → "
                f"{name} ({entity_id})"
            )
        )