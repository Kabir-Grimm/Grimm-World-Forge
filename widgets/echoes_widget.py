from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit
)

from services.world_service import load_worlds
from services.echoes_service import (
    generate_echo,
    save_echo_as_event
)

from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class EchoesWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.current_echo = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("✦ Ecos Narrativos"))

        world_layout = QHBoxLayout()

        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        self.load_worlds()

        world_layout.addWidget(self.world_combo)

        self.refresh_btn = QPushButton("Refrescar mundos")
        world_layout.addWidget(self.refresh_btn)

        layout.addLayout(world_layout)

        buttons = QHBoxLayout()

        self.generate_btn = QPushButton("✦ Generar eco")
        self.save_btn = QPushButton("💾 Guardar como evento")

        buttons.addWidget(self.generate_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        self.result = QTextEdit()
        layout.addWidget(self.result)

        self.refresh_btn.clicked.connect(self.load_worlds)
        self.generate_btn.clicked.connect(self.generate)
        self.save_btn.clicked.connect(self.save)

    def load_worlds(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

    def generate(self):
        world_id = self.world_combo.currentData()

        self.current_echo = generate_echo(world_id)

        echo = self.current_echo

        text = (
            "\n══════════════════════\n"
            "✦ ECO NARRATIVO\n"
            "══════════════════════\n\n"
            f"Mundo: {echo.get('world_name') or 'Sin mundo'}\n"
            f"Caos: {echo.get('chaos')}\n"
            f"Foco: {echo.get('focus')}\n"
            f"Acción: {echo.get('action')}\n"
            f"Tono: {echo.get('tone')}\n"
            f"Alcance: {echo.get('scope')}\n"
            f"Impacto: {echo.get('impact')}\n"
            f"Objetivo: {echo.get('target', {}).get('name')}\n\n"
            f"Interpretación:\n{echo.get('description')}\n"
        )

        self.result.append(text)

        add_system_log(
            self.history,
            f"✦ Eco generado → {echo.get('focus')}"
        )

    def save(self):
        if not self.current_echo:
            self.result.append("⚠ No hay eco generado para guardar.")
            return

        event_id = save_echo_as_event(self.current_echo)

        self.result.append(
            "\n"
            "💾 ECO GUARDADO COMO EVENTO\n"
            f"ID: {event_id}\n"
        )

        add_system_log(
            self.history,
            f"💾 Eco guardado como evento → {event_id}"
        )

        self.current_echo = None