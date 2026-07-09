import json
from collections import Counter, defaultdict
from warnings import filters

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QComboBox, QLineEdit, QGroupBox, QSpinBox, QInputDialog
)
from PySide6.QtCore import Qt

from services.world_simulation_service import load_world_events
from services.world_time_service import load_world_time
from services.world_era_service import get_current_era, create_new_era


EVENT_LABELS = {
    "movement": "Movimiento",
    "npc_location_reaction": "Interacción",
    "npc_social_reaction": "Relación",
    "location_production": "Producción",
    "discovery_reaction": "Descubrimiento",
    "creature_location_reaction": "Criatura",
    "army_location_reaction": "Ejército",
}


EVENT_ICONS = {
    "movement": "👣",
    "npc_location_reaction": "🤝",
    "npc_social_reaction": "🔗",
    "location_production": "💰",
    "discovery_reaction": "🔎",
    "creature_location_reaction": "🐾",
    "army_location_reaction": "⚔",
}


class WorldRegistryWidget(QWidget):

    def __init__(self, on_advance_turn=None):
        super().__init__()

        self.on_advance_turn = on_advance_turn

        self.events = []
        self.filtered_events = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.status_box = QGroupBox("🌍 Estado del Mundo")
        self.status_box.setMaximumHeight(95)

        status_layout = QHBoxLayout()
        self.status_box.setLayout(status_layout)

        self.world_status_label = QLabel()
        status_layout.addWidget(self.world_status_label)

        status_layout.addStretch()

        self.new_era_btn = QPushButton("🏛 Nueva era")
        status_layout.addWidget(self.new_era_btn)

        layout.addWidget(self.status_box)

        filters = QHBoxLayout()

        filters.addWidget(QLabel("Tipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos los eventos", None)
        filters.addWidget(self.type_combo)

        filters.addWidget(QLabel("Entidad:"))
        self.entity_search = QLineEdit()
        self.entity_search.setPlaceholderText("Buscar entidad...")
        filters.addWidget(self.entity_search)

        filters.addWidget(QLabel("Desde turno:"))
        self.turn_from = QSpinBox()
        self.turn_from.setRange(0, 999999)
        self.turn_from.setValue(0)
        filters.addWidget(self.turn_from)

        filters.addWidget(QLabel("Hasta turno:"))
        self.turn_to = QSpinBox()
        self.turn_to.setRange(0, 999999)
        self.turn_to.setValue(999999)
        filters.addWidget(self.turn_to)

        self.advance_turn_btn = QPushButton("▶ Avanzar turno")
        filters.addWidget(self.advance_turn_btn)
        self.advance_turn_btn.clicked.connect(self.advance_turn_from_registry)

        self.refresh_btn = QPushButton("Refrescar")
        self.clear_btn = QPushButton("🧹 Limpiar filtros")
        

        filters.addWidget(self.refresh_btn)
        filters.addWidget(self.clear_btn)

        layout.addLayout(filters)

        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)

        self.event_list = QListWidget()
        main_splitter.addWidget(self.event_list)

        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        main_splitter.addWidget(self.detail)

        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        main_splitter.addWidget(self.summary)

        main_splitter.setSizes([420, 520, 420])

        self.refresh_btn.clicked.connect(self.load_events)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.new_era_btn.clicked.connect(self.create_era_dialog)

        self.type_combo.currentIndexChanged.connect(self.apply_filters)
        self.entity_search.textChanged.connect(self.apply_filters)
        self.turn_from.valueChanged.connect(self.apply_filters)
        self.turn_to.valueChanged.connect(self.apply_filters)
        self.event_list.currentRowChanged.connect(self.show_selected_event)

        self.load_events()

    def update_world_status(self):
        world_time = load_world_time()
        current_era = get_current_era()

        total_events = len(self.events)

        source_entities = set()
        npc_count = 0
        city_count = 0
        army_count = 0
        death_count = 0

        for event in self.events:
            event_type = event.get("event_type", "")

            if "death" in event_type or "muerte" in event_type:
                death_count += 1

            source = event.get("source")
            if source:
                entity_id = source.get("entity_id")
                entity_type = source.get("type")

                if entity_id:
                    source_entities.add(entity_id)

                if entity_type == "npcs":
                    npc_count += 1
                elif entity_type in ["locations", "kingdoms"]:
                    city_count += 1
                elif entity_type == "armies":
                    army_count += 1

        event_types_count = len({
            event.get("event_type", "unknown")
            for event in self.events
        })

        text = (
            f"📅 Año {world_time.get('year', 1)} "
            f"Mes {world_time.get('month', 1)} "
            f"Día {world_time.get('day', 1)} "
            f"| Era: {current_era.get('name', 'Primera Era')}\n"
            f"⏳ Turno {world_time.get('turn', 0)}   "
            f"👥 NPC activos en eventos: {npc_count}   "
            f"🏘 Lugares activos: {city_count}   "
            f"⚔ Ejércitos activos: {army_count}   "
            f"💀 Muertes: {death_count}   "
            f"🌍 Eventos: {total_events}   "
            f"📚 Tipos de evento: {event_types_count}"
        )

        self.world_status_label.setText(text)

    def create_era_dialog(self):
        name, ok = QInputDialog.getText(
            self,
            "Nueva era",
            "Nombre de la nueva era:"
        )

        if not ok:
            return

        if not name.strip():
            return

        create_new_era(name)
        self.load_events()

    def load_events(self):
        self.events = load_world_events()

        self.events.sort(
            key=lambda event: (
                event.get("world_time", {}).get("year", 0),
                event.get("world_time", {}).get("month", 0),
                event.get("world_time", {}).get("day", 0),
                event.get("world_time", {}).get("turn", 0),
                event.get("created_at", "")
            ),
            reverse=True
        )

        max_turn = 0

        for event in self.events:
            turn = int(event.get("world_time", {}).get("turn", 0))
            max_turn = max(max_turn, turn)

        self.turn_to.blockSignals(True)
        self.turn_to.setValue(max(max_turn, 999999))
        self.turn_to.blockSignals(False)

        self.populate_type_filter()
        self.update_world_status()
        self.apply_filters()

    def populate_type_filter(self):
        current = self.type_combo.currentData()

        event_types = sorted({
            event.get("event_type", "unknown")
            for event in self.events
        })

        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        self.type_combo.addItem("Todos los eventos", None)

        for event_type in event_types:
            label = EVENT_LABELS.get(event_type, event_type)
            self.type_combo.addItem(label, event_type)

        index = self.type_combo.findData(current)

        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.type_combo.blockSignals(False)

    def clear_filters(self):
        self.type_combo.setCurrentIndex(0)
        self.entity_search.clear()
        self.turn_from.setValue(0)

        max_turn = 0
        for event in self.events:
            turn = int(event.get("world_time", {}).get("turn", 0))
            max_turn = max(max_turn, turn)

        self.turn_to.setValue(max(max_turn, 999999))
        self.apply_filters()

    def event_matches_entity_search(self, event, search):
        if not search:
            return True

        searchable = json.dumps(event, ensure_ascii=False).lower()
        return search in searchable

    def event_matches_turn(self, event):
        turn = int(event.get("world_time", {}).get("turn", 0))
        return self.turn_from.value() <= turn <= self.turn_to.value()

    def apply_filters(self):
        selected_type = self.type_combo.currentData()
        search = self.entity_search.text().lower().strip()

        self.filtered_events = []

        for event in self.events:
            if selected_type and event.get("event_type") != selected_type:
                continue

            if not self.event_matches_entity_search(event, search):
                continue

            if not self.event_matches_turn(event):
                continue

            self.filtered_events.append(event)

        self.populate_event_list()
        self.populate_summary()

    def populate_event_list(self):
        self.event_list.blockSignals(True)
        self.event_list.clear()

        for index, event in enumerate(self.filtered_events):
            event_type = event.get("event_type", "unknown")
            icon = EVENT_ICONS.get(event_type, "📜")
            label = EVENT_LABELS.get(event_type, event_type)

            title = event.get("title", "Evento")
            date = event.get("world_date", "Fecha desconocida")

            item = QListWidgetItem(
                f"{icon} {title}\n{date}     [{label}]"
            )

            item.setData(Qt.UserRole, index)
            self.event_list.addItem(item)

        self.event_list.blockSignals(False)

        if self.event_list.count() > 0:
            self.event_list.setCurrentRow(0)
        else:
            self.detail.clear()

    def show_selected_event(self):
        item = self.event_list.currentItem()

        if not item:
            self.detail.clear()
            return

        index = item.data(Qt.UserRole)

        if index is None or index >= len(self.filtered_events):
            self.detail.clear()
            return

        event = self.filtered_events[index]
        self.detail.setPlainText(self.format_event_detail(event))

    def format_event_detail(self, event):
        lines = []

        event_type = event.get("event_type", "unknown")
        label = EVENT_LABELS.get(event_type, event_type)

        lines.append("DETALLE DEL EVENTO")
        lines.append("")
        lines.append(event.get("title", "Evento"))
        lines.append(f"Tipo: {label}")
        lines.append(f"Fecha: {event.get('world_date', 'Fecha desconocida')}")
        lines.append("")
        lines.append(event.get("description", ""))
        lines.append("")

        source = event.get("source")

        if source:
            lines.append("ORIGEN")
            lines.append(f"- Entidad: {source.get('name', 'Entidad')}")
            lines.append(f"- Tipo: {source.get('type', '-')}")
            lines.append(f"- ID: {source.get('entity_id', '-')}")
            lines.append("")

        related = event.get("related", [])

        if related:
            lines.append("RELACIONADOS")
            for item in related:
                lines.append(
                    f"- {item.get('name', 'Entidad')} "
                    f"({item.get('type', '-')})"
                )
            lines.append("")

        extra = event.get("extra", {})

        if extra:
            effects = extra.get("effects", {})

            if effects:
                lines.append("EFECTOS APLICADOS")
                for key, value in effects.items():
                    lines.append(f"- {key}: {value}")
                lines.append("")

        return "\n".join(lines)

    def populate_summary(self):
        total = len(self.filtered_events)
        all_total = len(self.events)

        type_counter = Counter(
            event.get("event_type", "unknown")
            for event in self.filtered_events
        )

        entity_counter = defaultdict(int)

        for event in self.filtered_events:
            source = event.get("source")

            if source:
                name = source.get("name", "Entidad")
                entity_id = source.get("entity_id", "-")
                entity_counter[(name, entity_id)] += 1

            for related in event.get("related", []):
                name = related.get("name", "Entidad")
                entity_id = related.get("entity_id", "-")
                entity_counter[(name, entity_id)] += 1

        latest_time = None

        if self.events:
            latest_time = self.events[0].get("world_time", {})

        lines = []

        lines.append("RESUMEN DEL EVENTO")
        lines.append("")
        lines.append(f"Eventos filtrados: {total}")
        lines.append(f"Eventos totales: {all_total}")

        if latest_time:
            lines.append(f"Turno actual: {latest_time.get('turn', 0)}")
            lines.append(
                "Fecha actual: "
                f"{latest_time.get('day', 1)}/"
                f"{latest_time.get('month', 1)}/"
                f"{latest_time.get('year', 1)}"
            )

        lines.append("")
        lines.append("EVENTOS POR TIPO")

        if type_counter:
            for event_type, count in type_counter.most_common():
                label = EVENT_LABELS.get(event_type, event_type)
                percent = round((count / max(total, 1)) * 100)
                lines.append(f"- {label}: {percent}% ({count})")
        else:
            lines.append("- Sin eventos")

        lines.append("")
        lines.append("ENTIDADES MÁS ACTIVAS")

        if entity_counter:
            for (name, entity_id), count in sorted(
                entity_counter.items(),
                key=lambda item: item[1],
                reverse=True
            )[:8]:
                lines.append(f"- {name} ({entity_id}): {count} eventos")
        else:
            lines.append("- Sin entidades activas")

        self.summary.setPlainText("\n".join(lines))
    
    def advance_turn_from_registry(self):
        if self.on_advance_turn:
            self.on_advance_turn()
            self.load_events()