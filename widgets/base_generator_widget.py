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
    QGridLayout
)

from datetime import datetime

from core.parser import (
    load_all_lists,
    weighted_choice
)

from services.entity_service import save_entity
from core.system_log import add_system_log
from PySide6.QtWidgets import QComboBox
from services.world_service import load_worlds, add_entity_to_world
from utils.ui_helpers import sort_combobox
from services.name_generator_service import generate_entity_name



class BaseGeneratorWidget(QWidget):

    ENTITY_PREFIX = ""
    ENTITY_TYPE = "entity"
    ENTITY_LABEL = "Entidad"

    def __init__(self, history_widget):

        super().__init__()

        self.history = history_widget

        self.generated_data = {}

        self.checkboxes = {}

        self.selected_order = []

        # =========================
        # Cargar listas
        # =========================

        all_lists = load_all_lists()

        self.oracles = []

        for oracle in all_lists:

            if oracle["name"].startswith(
                self.ENTITY_PREFIX
            ):

                self.oracles.append(
                    oracle
                )

        # =========================
        # Layout principal
        # =========================

        layout = QVBoxLayout()

        # =========================
        # Nombre automático
        # =========================

        name_layout = QHBoxLayout()


        name_layout.addWidget(
            QLabel("Nombre:")
        )


        self.name_input = QLineEdit()

        self.name_input.setPlaceholderText(
            f"Nombre de {self.ENTITY_LABEL}"
        )

        name_layout.addWidget(
            self.name_input
        )


        self.name_style_combo = QComboBox()

        self.name_style_combo.addItems([
            "universal",
            "fantasy",
            "dark_fantasy",
            "cyberpunk",
            "modern",
            "cosmic"
        ])

        name_layout.addWidget(
            self.name_style_combo
        )


        self.random_name_btn = QPushButton(
            "🎲"
        )

        self.random_name_btn.setToolTip(
            "Generar nombre aleatorio"
        )

        self.random_name_btn.clicked.connect(
            self.generate_random_name
        )

        name_layout.addWidget(
            self.random_name_btn
        )


        layout.addLayout(name_layout)

        # =========================
        # Asignacion de mundo
        # =========================

        world_layout = QHBoxLayout()

        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        self.load_world_options()

        world_layout.addWidget(self.world_combo)

        layout.addLayout(world_layout)

        # =========================
        # Categorías
        # =========================

        layout.addWidget(
            QLabel("Categorías:")
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setMaximumHeight(180)

        scroll_widget = QWidget()

        grid = QGridLayout()

        scroll_widget.setLayout(grid)

        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)

        # =========================
        # Checkboxes
        # =========================

        row = 0
        col = 0

        for oracle in self.oracles:

            cb = QCheckBox(
                oracle["name"]
            )

            cb.setChecked(True)

            self.checkboxes[
                oracle["name"]
            ] = cb

            cb.stateChanged.connect(
                lambda state,
                n=oracle["name"]:
                self.update_selection_order(
                    n,
                    state
                )
            )

            grid.addWidget(
                cb,
                row,
                col
            )

            if oracle["name"] not in self.selected_order:

                self.selected_order.append(
                    oracle["name"]
                )

            col += 1

            if col >= 2:

                col = 0
                row += 1

        # =========================
        # Botones
        # =========================

        buttons = QHBoxLayout()

        self.select_all_btn = QPushButton(
            "✔ Todo"
        )

        self.clear_all_btn = QPushButton(
            "✖ Nada"
        )

        self.generate_btn = QPushButton(
            f"Generar {self.ENTITY_LABEL}"
        )

        self.save_btn = QPushButton(
            f"Guardar {self.ENTITY_LABEL}"
        )

        buttons.addWidget(
            self.select_all_btn
        )

        buttons.addWidget(
            self.clear_all_btn
        )

        buttons.addWidget(
            self.generate_btn
        )

        buttons.addWidget(
            self.save_btn
        )

        layout.addLayout(buttons)

        # =========================
        # Resultado
        # =========================

        self.result = QTextEdit()

        layout.addWidget(
            self.result
        )

        self.setLayout(layout)

        # =========================
        # Eventos
        # =========================

        self.generate_btn.clicked.connect(
            self.generate_entity
        )

        self.save_btn.clicked.connect(
            self.save_entity_data
        )

        self.select_all_btn.clicked.connect(
            self.select_all
        )

        self.clear_all_btn.clicked.connect(
            self.clear_all
        )

    # =====================================
    # Orden dinámico
    # =====================================

    def update_selection_order(
        self,
        name,
        state
    ):

        if state:

            if name not in self.selected_order:

                self.selected_order.append(
                    name
                )

        else:

            if name in self.selected_order:

                self.selected_order.remove(
                    name
                )
    # =====================================
    # Generador de nombres
    # =====================================

    def generate_random_name(self):

        entity_type = self.ENTITY_TYPE

        style = (
            self.name_style_combo
            .currentText()
            .strip()
        )

        gender = "Aleatorio"

        if hasattr(self, "gender_combo"):
            gender = (
                self.gender_combo
                .currentText()
                .strip()
            )

        # Normalizar género visual de la app
        gender_map = {
            "Masculino": "male",
            "Hombre": "male",
            "Femenino": "female",
            "Mujer": "female",
            "Neutro": "neutral",
            "No binario": "neutral",
            "Aleatorio": "random"
        }

        gender = gender_map.get(gender, gender)

        generated_name = generate_entity_name(
            entity_type=entity_type,
            style=style,
            gender=gender
        )

        self.name_input.setText(generated_name)

        add_system_log(
            self.history,
            f"🎲 Nombre generado → {generated_name}"
        )


    # =====================================
    # Generación
    # =====================================

    def generate_entity(self):

        self.generated_data = {}

        output = []

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        output.append(
            "\n══════════════════════"
        )

        output.append(
            f"🎲 {self.ENTITY_LABEL.upper()} GENERADO"
        )

        output.append(
            f"🕒 {timestamp}"
        )

        output.append(
            "══════════════════════\n"
        )

        for selected_name in self.selected_order:

            oracle = next(
                (
                    o for o in self.oracles
                    if o["name"] == selected_name
                ),
                None
            )

            if not oracle:
                continue

            data = oracle["data"]

            category = (
                selected_name.replace(
                    self.ENTITY_PREFIX,
                    ""
                )
            )

            if "Resultados" in data:

                result = weighted_choice(
                    data["Resultados"]
                )

                self.generated_data[
                    category
                ] = result

                output.append(
                    f"{category}: {result}"
                )

            else:

                for subcat, options in data.items():

                    result = weighted_choice(
                        options
                    )

                    key = (
                        f"{category} - {subcat}"
                    )

                    self.generated_data[
                        key
                    ] = result

                    output.append(
                        f"{key}: {result}"
                    )

        text = "\n".join(output)

        self.result.append(text)

        add_system_log(
            self.history,
            f"🎲 {self.ENTITY_LABEL} generado"
        )

    # =====================================
    # Guardar entidad
    # =====================================

    def save_entity_data(self):

        if not self.generated_data:
            return

        name = (
            self.name_input.text()
            or f"{self.ENTITY_LABEL} Sin Nombre"
        )

        entity = {
            "name": name,
            "type": self.ENTITY_TYPE,
            "data": self.generated_data
        }

        entity_id = save_entity(
            self.ENTITY_TYPE,
            entity
        )

        entity["id"] = entity_id

        world_id = self.world_combo.currentData()

        if world_id:
            add_entity_to_world(world_id, entity)

        add_system_log(
            self.history,
            (
                f"💾 {self.ENTITY_LABEL} guardado → "
                f"{name} ({entity_id})"
            )
        )

        self.result.append(
            (
                "\n"
                f"💾 GUARDADO\n"
                f"ID: {entity_id}\n"
            )
        )

    # =====================================
    # Seleccionar todo
    # =====================================

    def select_all(self):

        self.selected_order = []

        for name, cb in self.checkboxes.items():

            cb.setChecked(True)

            if name not in self.selected_order:

                self.selected_order.append(
                    name
                )

    # =====================================
    # Limpiar
    # =====================================

    def clear_all(self):

        self.selected_order = []

        for cb in self.checkboxes.values():

            cb.setChecked(False)

    # =====================================
    # Asignación de mundo
    # =====================================
    
    def load_world_options(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )
        sort_combobox(self.world_combo)