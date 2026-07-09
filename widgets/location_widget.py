from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QScrollArea,
    QGridLayout
)

from datetime import datetime

from core.parser import load_all_lists, weighted_choice
from services.entity_service import save_entity
from services.world_service import load_worlds, add_entity_to_world
from services.name_generator_service import generate_entity_name
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class LocationWidget(QWidget):

    PREFIX = "Ubicación-"

    LOCATION_ROLES = {
        "Sin rol definido": None,

        # Asentamientos / civilización
        "Villa": "village",
        "Ciudad": "city",
        "Puerto": "port",
        "Fortaleza": "fortress",
        "Universidad": "university",
        "Mercado": "market",
        "Templo": "temple",
        "Santuario": "sanctuary",

        # Lugares salvajes / recursos
        "Bosque": "forest",
        "Montaña": "mountain",
        "Mina": "mine",
        "Granja": "farm",
        "Río / Lago": "water_source",

        # Exploración / peligro
        "Ruinas": "ruins",
        "Mazmorra": "dungeon",
        "Cueva": "cave",
        "Torre": "tower",
        "Laboratorio": "laboratory",
        "Zona maldita": "cursed_zone",

        # Universal / moderno / futurista
        "Base militar": "military_base",
        "Centro comercial": "trade_hub",
        "Distrito industrial": "industrial_zone",
        "Estación de transporte": "transport_hub",
        "Archivo / Biblioteca": "archive",
        "Hospital / Clínica": "medical_site"
    }

    PRESETS = {
        "Asentamiento": [
            "Tamaño población",
            "Tipo de gobierno",
            "Control de ubicación",
            "Distintivo de población",
            "Nivel tecnológico",
            "Religión",
            "Estado del lugar",
            "Nivel de peligro",
            "Elementos llamativos",
            "Peculiaridad",
            "Particularidades del mundo"
        ],
        "Reino": [
            "Tamaño población",
            "Tipo de gobierno",
            "Control de ubicación",
            "Distintivo de población",
            "Nivel tecnológico",
            "Religión",
            "Estado del lugar",
            "Nivel de peligro",
            "Elementos llamativos",
            "Peculiaridad",
            "Particularidades del mundo"
        ],
        "Terreno salvaje": [
            "Terreno",
            "Clima",
            "Nivel de peligro",
            "Peligro natural",
            "Elementos llamativos",
            "Peculiaridad",
            "Particularidades del mundo"
        ],
        "Estructura": [
            "Estado del lugar",
            "Control de ubicación",
            "Nivel de peligro",
            "Elementos llamativos",
            "Peculiaridad",
            "Religión",
            "Particularidades del mundo"
        ]
    }

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.generated_data = {}
        self.checkboxes = {}

        all_lists = load_all_lists()

        self.oracles = [
            oracle for oracle in all_lists
            if oracle["name"].startswith(self.PREFIX)
        ]

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🌍 Creador de Ubicaciones"))

        # =========================
        # Nombre
        # =========================

        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Nombre:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Nombre de la ubicación / reino"
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

        # =========================
        # Preset
        # =========================

        preset_layout = QHBoxLayout()

        preset_layout.addWidget(QLabel("Tipo de creación:"))

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Asentamiento",
            "Reino",
            "Terreno salvaje",
            "Estructura",
            "Personalizado"
        ])
        sort_combobox(self.preset_combo)

        preset_layout.addWidget(self.preset_combo)

        layout.addLayout(preset_layout)

        # =========================
        # Rol del lugar
        # =========================

        role_layout = QHBoxLayout()

        role_layout.addWidget(QLabel("Rol del lugar:"))

        self.location_role_combo = QComboBox()

        for label, value in self.LOCATION_ROLES.items():
            self.location_role_combo.addItem(label, value)

        role_layout.addWidget(self.location_role_combo)

        layout.addLayout(role_layout)

        # =========================
        # Categorías
        # =========================

        layout.addWidget(QLabel("Categorías:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(210)

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
            cb.setChecked(False)

            self.checkboxes[clean_name] = {
                "checkbox": cb,
                "oracle": oracle
            }

            grid.addWidget(cb, row, col)

            col += 1

            if col >= 2:
                col = 0
                row += 1

        # =========================
        # Botones
        # =========================

        buttons = QHBoxLayout()

        self.apply_preset_btn = QPushButton("Aplicar preset")
        self.select_all_btn = QPushButton("✔ Todo")
        self.clear_all_btn = QPushButton("✖ Nada")
        self.generate_btn = QPushButton("🎲 Generar")
        self.save_btn = QPushButton("💾 Guardar")

        buttons.addWidget(self.apply_preset_btn)
        buttons.addWidget(self.select_all_btn)
        buttons.addWidget(self.clear_all_btn)
        buttons.addWidget(self.generate_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        # =========================
        # Resultado
        # =========================

        self.result = QTextEdit()
        layout.addWidget(self.result)

        # =========================
        # Eventos
        # =========================

        self.preset_combo.currentIndexChanged.connect(
            self.apply_preset
        )

        self.apply_preset_btn.clicked.connect(
            self.apply_preset
        )

        self.select_all_btn.clicked.connect(
            self.select_all
        )

        self.clear_all_btn.clicked.connect(
            self.clear_all
        )

        self.generate_btn.clicked.connect(
            self.generate_location
        )

        self.save_btn.clicked.connect(
            self.save_location
        )

        self.apply_preset()

    # =====================================
    # Generador de nombres
    # =====================================

    def generate_random_name(self):
        style = self.name_style_combo.currentText()

        entity_type = self.get_entity_type()

        generated_name = generate_entity_name(
            entity_type=entity_type,
            style=style,
            gender="Aleatorio"
        )

        self.name_input.setText(generated_name)

        add_system_log(
            self.history,
            f"🎲 Nombre generado → {generated_name}"
        )

    # =====================================
    # Utilidades
    # =====================================

    def clean_category_name(self, name):
        return name.replace(self.PREFIX, "").strip()

    def load_world_options(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

        sort_combobox(self.world_combo)

    def get_entity_type(self):
        preset = self.preset_combo.currentText()

        if preset == "Reino":
            return "kingdoms"

        return "locations"

    def get_entity_label(self):
        preset = self.preset_combo.currentText()

        if preset == "Reino":
            return "Reino"

        return "Ubicación"

    def get_selected_location_role(self):
        return self.location_role_combo.currentData()

    def get_selected_location_role_label(self):
        return self.location_role_combo.currentText()

    def get_default_effects(self):
        entity_type = self.get_entity_type()

        if entity_type == "kingdoms":
            return {
                "influence": 3,
                "social": 2,
                "knowledge": 1,
                "resistance": 1,
                "risk": 1
            }

        return {}

    # =====================================
    # Presets
    # =====================================

    def apply_preset(self):
        preset = self.preset_combo.currentText()

        if preset == "Personalizado":
            return

        allowed = self.PRESETS.get(preset, [])

        for category, data in self.checkboxes.items():
            cb = data["checkbox"]
            cb.setChecked(category in allowed)

        self.apply_default_role_for_preset(preset)

    def apply_default_role_for_preset(self, preset):
        if preset == "Reino":
            self.set_location_role("city")
        elif preset == "Asentamiento":
            self.set_location_role("village")
        elif preset == "Terreno salvaje":
            self.set_location_role("forest")
        elif preset == "Estructura":
            self.set_location_role("ruins")

    def set_location_role(self, role_value):
        index = self.location_role_combo.findData(role_value)

        if index >= 0:
            self.location_role_combo.setCurrentIndex(index)

    def select_all(self):
        for data in self.checkboxes.values():
            data["checkbox"].setChecked(True)

    def clear_all(self):
        for data in self.checkboxes.values():
            data["checkbox"].setChecked(False)

    # =====================================
    # Generar
    # =====================================

    def generate_location(self):
        self.generated_data = {}

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        label = self.get_entity_label()
        location_role = self.get_selected_location_role()
        location_role_label = self.get_selected_location_role_label()

        output = [
            "\n══════════════════════",
            f"🌍 {label.upper()} GENERADO",
            f"🕒 {timestamp}",
            f"Tipo: {self.preset_combo.currentText()}",
            f"Rol del lugar: {location_role_label}",
            "══════════════════════\n"
        ]

        for category, item in self.checkboxes.items():
            cb = item["checkbox"]

            if not cb.isChecked():
                continue

            oracle = item["oracle"]
            data = oracle.get("data", {})

            if "Resultados" in data:
                options = data["Resultados"]

                result = (
                    weighted_choice(options)
                    if options
                    else "SIN RESULTADOS"
                )

                self.generated_data[category] = result
                output.append(f"{category}: {result}")

            else:
                for subcat, options in data.items():
                    result = (
                        weighted_choice(options)
                        if options
                        else "SIN RESULTADOS"
                    )

                    key = f"{category} - {subcat}"

                    self.generated_data[key] = result
                    output.append(f"{key}: {result}")

        self.generated_data["Tipo de creación"] = (
            self.preset_combo.currentText()
        )

        self.generated_data["Rol del lugar"] = location_role_label

        if location_role:
            self.generated_data["location_role"] = location_role

        if self.get_entity_type() == "kingdoms":
            self.generated_data["Clasificación"] = "Reino"

        self.result.append(
            "\n".join(output)
        )

        add_system_log(
            self.history,
            f"🌍 {label} generado"
        )

    # =====================================
    # Guardar
    # =====================================

    def save_location(self):
        if not self.generated_data:
            return

        label = self.get_entity_label()
        entity_type = self.get_entity_type()

        name = (
            self.name_input.text().strip()
            or f"{label} Sin Nombre"
        )

        location_role = self.get_selected_location_role()
        location_role_label = self.get_selected_location_role_label()

        entity = {
            "name": name,
            "type": entity_type,
            "data": self.generated_data
        }

        if location_role:
            entity["location_role"] = location_role

            entity.setdefault("meta", {})
            entity["meta"]["location_role"] = location_role
            entity["meta"]["location_role_label"] = location_role_label

            entity["data"]["location_role"] = location_role
            entity["data"]["Rol del lugar"] = location_role_label

            entity["tags"] = [
                location_role
            ]

        effects = self.get_default_effects()

        if effects:
            entity["effects"] = effects

        entity_id = save_entity(
            entity_type,
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
            f"💾 {label.upper()} GUARDADO\n"
            f"ID: {entity_id}\n"
            f"Tipo interno: {entity_type}\n"
            f"Rol del lugar: {location_role_label}\n"
        )

        if effects:
            self.result.append("Efectos:")

            for stat, value in effects.items():
                sign = "+" if value >= 0 else ""
                self.result.append(
                    f"- {stat}: {sign}{value}"
                )

        add_system_log(
            self.history,
            (
                f"💾 {label} guardado → "
                f"{name} ({entity_id})"
            )
        )