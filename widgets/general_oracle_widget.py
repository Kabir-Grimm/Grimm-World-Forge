from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QLineEdit,
    QComboBox
)

from datetime import datetime

from core.parser import load_all_lists, weighted_choice
from services.entity_service import save_entity
from services.world_service import load_worlds, add_entity_to_world
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class GeneralOracleWidget(QWidget):

    ACTION_LIST_NAME = "Oraculo General - Accion"
    SUBJECT_LIST_NAME = "Oraculo General - Sujeto"

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.generated_data = {}

        all_lists = load_all_lists()

        self.action_oracle = self.find_oracle(
            all_lists,
            self.ACTION_LIST_NAME
        )

        self.subject_oracle = self.find_oracle(
            all_lists,
            self.SUBJECT_LIST_NAME
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🎲 Oráculo General"))

        # Nombre
        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Nombre del evento/escena:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej. La ruptura del pacto")

        name_layout.addWidget(self.name_input)

        layout.addLayout(name_layout)

        # Mundo
        world_layout = QHBoxLayout()

        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        self.load_world_options()

        world_layout.addWidget(self.world_combo)

        layout.addLayout(world_layout)

        # Botones
        buttons = QHBoxLayout()

        self.roll_btn = QPushButton("🎲 Consultar oráculo")
        self.save_event_btn = QPushButton("💾 Guardar como evento")
        self.save_scene_btn = QPushButton("🎭 Guardar como escena")

        buttons.addWidget(self.roll_btn)
        buttons.addWidget(self.save_event_btn)
        buttons.addWidget(self.save_scene_btn)

        layout.addLayout(buttons)

        # Resultado
        self.result = QTextEdit()
        layout.addWidget(self.result)

        self.roll_btn.clicked.connect(self.roll_oracle)
        self.save_event_btn.clicked.connect(
            lambda: self.save_generated("events", "event")
        )
        self.save_scene_btn.clicked.connect(
            lambda: self.save_generated("scenes", "scene")
        )

    def find_oracle(self, all_lists, name):
        for oracle in all_lists:
            if oracle["name"] == name:
                return oracle

        return None

    def load_world_options(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

    def roll_from_oracle(self, oracle):
        if not oracle:
            return "NO ENCONTRADO"

        data = oracle.get("data", {})

        if "Resultados" in data:
            return weighted_choice(data["Resultados"])

        # fallback por si alguna lista viene estructurada
        all_options = []

        for options in data.values():
            all_options.extend(options)

        if not all_options:
            return "SIN RESULTADOS"

        return weighted_choice(all_options)

    def roll_oracle(self):
        action = self.roll_from_oracle(self.action_oracle)
        subject = self.roll_from_oracle(self.subject_oracle)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interpretation = (
            f"Algo relacionado con '{subject}' debe "
            f"'{action.lower()}' o ser afectado por esa acción."
        )

        self.generated_data = {
            "Acción": action,
            "Objetivo": subject,
            "Interpretación": interpretation,
            "timestamp": timestamp
        }

        text = (
            "\n"
            "══════════════════════\n"
            "🎲 ORÁCULO GENERAL\n"
            f"🕒 {timestamp}\n"
            "══════════════════════\n\n"
            f"Acción: {action}\n"
            f"Objetivo: {subject}\n\n"
            f"Interpretación:\n{interpretation}\n"
        )

        self.result.append(text)

        add_system_log(
            self.history,
            f"🎲 Oráculo general → {action} / {subject}"
        )

    def save_generated(self, entity_type, label):
        if not self.generated_data:
            return

        name = (
            self.name_input.text().strip()
            or f"{label.capitalize()} Sin Nombre"
        )

        entity = {
            "name": name,
            "type": entity_type,
            "data": self.generated_data
        }

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
            f"💾 GUARDADO COMO {label.upper()}\n"
            f"ID: {entity_id}\n"
        )

        add_system_log(
            self.history,
            f"💾 Oráculo guardado como {label} → {name} ({entity_id})"
        )