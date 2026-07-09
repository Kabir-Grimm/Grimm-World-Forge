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

from services.simulation_service import (
    generate_world_event,
    get_entities_for_world
)

from services.timeline_service import (
    save_timeline_event,
    load_timeline,
    get_current_world_year,
    advance_world_year
)

from services.consequences_service import apply_echo_consequences
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class SimulationWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.generated_events = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🌌 Simulación de Mundo"))

        world_layout = QHBoxLayout()

        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        world_layout.addWidget(self.world_combo)

        self.refresh_btn = QPushButton("Refrescar mundos")
        world_layout.addWidget(self.refresh_btn)

        layout.addLayout(world_layout)

        self.world_info = QLabel("Estado: -")
        layout.addWidget(self.world_info)

        buttons = QHBoxLayout()

        self.generate_btn = QPushButton("✦ Generar evento")
        self.save_last_btn = QPushButton("💾 Guardar último")
        self.save_all_btn = QPushButton("💾 Guardar todos")
        self.advance_year_btn = QPushButton("⏭ Avanzar año")
        self.timeline_btn = QPushButton("📜 Ver timeline")

        buttons.addWidget(self.generate_btn)
        buttons.addWidget(self.save_last_btn)
        buttons.addWidget(self.save_all_btn)
        buttons.addWidget(self.advance_year_btn)
        buttons.addWidget(self.timeline_btn)

        layout.addLayout(buttons)

        self.result = QTextEdit()
        layout.addWidget(self.result)

        self.refresh_btn.clicked.connect(self.load_worlds)
        self.world_combo.currentIndexChanged.connect(self.update_world_info)
        self.generate_btn.clicked.connect(self.generate_event)
        self.save_last_btn.clicked.connect(self.save_last_event)
        self.save_all_btn.clicked.connect(self.save_all_events)
        self.advance_year_btn.clicked.connect(self.advance_year)
        self.timeline_btn.clicked.connect(self.show_timeline)

        self.load_worlds()

    def load_worlds(self):
        self.world_combo.clear()

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

        self.generated_events = []
        self.update_world_info()

        add_system_log(
            self.history,
            "🌌 Simulación: mundos actualizados"
        )

    def update_world_info(self):
        world_id = self.world_combo.currentData()

        if not world_id:
            self.world_info.setText("Estado: sin mundo seleccionado")
            return

        entities = get_entities_for_world(world_id)
        year = get_current_world_year(world_id)

        pending = len(self.generated_events)

        self.world_info.setText(
            f"Estado: Año {year} | Entidades: {len(entities)} | Eventos pendientes: {pending}"
        )

    def generate_event(self):
        world_id = self.world_combo.currentData()

        if not world_id:
            self.result.append("⚠ No hay mundo seleccionado.")
            return

        event = generate_world_event(world_id)

        if not event:
            self.result.append("⚠ No se pudo generar evento.")
            return

        self.generated_events.append(event)

        echo = event.get("data", {})

        text = (
            "\n"
            "══════════════════════\n"
            f"✦ EVENTO PENDIENTE #{len(self.generated_events)}\n"
            f"Año: {event.get('year')}\n"
            f"Mundo: {event.get('world_name')}\n"
            "══════════════════════\n\n"
            f"Foco: {echo.get('focus')}\n"
            f"Acción: {echo.get('action')}\n"
            f"Tono: {echo.get('tone')}\n"
            f"Alcance: {echo.get('scope')}\n"
            f"Impacto: {echo.get('impact')}\n"
            f"Objetivo: {echo.get('target', {}).get('name')}\n\n"
            f"Interpretación:\n{event.get('description')}\n"
        )

        self.result.append(text)

        add_system_log(
            self.history,
            f"✦ Evento pendiente generado → {echo.get('focus')}"
        )

        self.update_world_info()

    def save_last_event(self):
        if not self.generated_events:
            self.result.append("⚠ No hay eventos pendientes.")
            return

        event = self.generated_events.pop()

        self.save_event_with_consequences(event)

        self.update_world_info()

    def save_all_events(self):
        if not self.generated_events:
            self.result.append("⚠ No hay eventos pendientes.")
            return

        total = len(self.generated_events)

        while self.generated_events:
            event = self.generated_events.pop(0)
            self.save_event_with_consequences(event)

        self.result.append(
            f"\n💾 {total} EVENTOS GUARDADOS EN TIMELINE\n"
        )

        self.update_world_info()

    def save_event_with_consequences(self, event):
        event_id = save_timeline_event(event)

        self.result.append(
            "\n"
            "💾 EVENTO GUARDADO EN TIMELINE\n"
            f"ID: {event_id}\n"
        )

        consequences = apply_echo_consequences(
            event.get("data", {})
        )

        if consequences:
            self.result.append("⚙ CONSECUENCIAS APLICADAS")
            for consequence in consequences:
                self.result.append(f"- {consequence}")

        add_system_log(
            self.history,
            f"💾 Evento guardado en timeline → {event_id}"
        )

    def advance_year(self):
        world_id = self.world_combo.currentData()

        if not world_id:
            self.result.append("⚠ No hay mundo seleccionado.")
            return

        new_year = advance_world_year(world_id, 1)

        self.generated_events = []

        self.result.append(
            "\n"
            "⏭ AÑO AVANZADO\n"
            f"Nuevo año: {new_year}\n"
            "Los eventos pendientes fueron limpiados.\n"
        )

        add_system_log(
            self.history,
            f"⏭ Mundo avanzado al año {new_year}"
        )

        self.update_world_info()

    def show_timeline(self):
        world_id = self.world_combo.currentData()

        if not world_id:
            self.result.append("⚠ No hay mundo seleccionado.")
            return

        timeline = [
            event for event in load_timeline()
            if event.get("world_id") == world_id
        ]

        if not timeline:
            self.result.append("📜 Este mundo aún no tiene timeline.")
            return

        timeline.sort(
            key=lambda e: e.get("year", 0)
        )

        lines = [
            "\n══════════════════════",
            "📜 TIMELINE DEL MUNDO",
            "══════════════════════\n"
        ]

        for event in timeline:
            lines.append(
                f"Año {event.get('year')} → {event.get('description')}"
            )

        self.result.append(
            "\n".join(lines)
        )