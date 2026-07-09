import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QComboBox
)

from PySide6.QtCore import Qt

from services.world_service import save_world
from services.entity_registry_service import load_registry_entities
from core.system_log import add_system_log
from core.display_names import display_entity_type


WORLD_ENTITY_TYPES = {
    "npcs": "NPCs",
    "locations": "Lugares",
    "kingdoms": "Reinos / Ciudades",
    "factions": "Facciones",
    "creatures": "Criaturas",
    "armies": "Ejércitos",
    "relics": "Reliquias",
    "items": "Objetos importantes",
    "weapons": "Armas importantes",
    "armors": "Armaduras importantes",
    "foods": "Recursos / Consumibles"
}


TYPE_ICONS = {
    "npcs": "👤",
    "locations": "📍",
    "kingdoms": "🏰",
    "factions": "⚑",
    "creatures": "🐾",
    "armies": "⚔",
    "relics": "💎",
    "items": "📦",
    "weapons": "🗡",
    "armors": "🛡",
    "foods": "🍖"
}


class WorldWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []
        self.filtered_entities = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🌍 Crear mundo persistente"))

        # =========================
        # Nombre
        # =========================

        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Nombre del mundo:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej. El Reino de Ceniza")

        name_layout.addWidget(self.name_input)

        layout.addLayout(name_layout)

        # =========================
        # Descripción
        # =========================

        layout.addWidget(QLabel("Descripción / notas:"))

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(90)

        layout.addWidget(self.description_input)

        # =========================
        # Filtros
        # =========================

        filters_layout = QHBoxLayout()

        filters_layout.addWidget(QLabel("Tipo:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos los tipos del mundo", None)

        for entity_type, label in WORLD_ENTITY_TYPES.items():
            self.type_combo.addItem(label, entity_type)

        filters_layout.addWidget(self.type_combo)

        filters_layout.addWidget(QLabel("Buscar:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, tipo, ID o contenido...")
        filters_layout.addWidget(self.search_input)

        layout.addLayout(filters_layout)

        # =========================
        # Lista de entidades
        # =========================

        layout.addWidget(QLabel("Entidades disponibles:"))

        self.entity_list = QListWidget()
        self.entity_list.setSelectionMode(QListWidget.MultiSelection)

        layout.addWidget(self.entity_list)

        # =========================
        # Botones
        # =========================

        buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("Refrescar entidades")
        self.clear_selection_btn = QPushButton("Limpiar selección")
        self.save_btn = QPushButton("Guardar mundo")

        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.clear_selection_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        # =========================
        # Resultado
        # =========================

        self.result = QTextEdit()
        self.result.setReadOnly(True)

        layout.addWidget(self.result)

        # =========================
        # Eventos
        # =========================

        self.refresh_btn.clicked.connect(self.load_entities)
        self.clear_selection_btn.clicked.connect(self.entity_list.clearSelection)
        self.save_btn.clicked.connect(self.save_current_world)

        self.type_combo.currentIndexChanged.connect(self.apply_filters)
        self.search_input.textChanged.connect(self.apply_filters)

        self.load_entities()

    # =========================
    # Carga / filtros
    # =========================

    def load_entities(self):
        self.entities = load_registry_entities(
            profile="world",
            include_default=False
        )

        self.entities = [
            entity for entity in self.entities
            if entity.get("type") in WORLD_ENTITY_TYPES
        ]

        self.entities.sort(
            key=lambda item: (
                str(item.get("type", "")).lower(),
                str(item.get("name", "")).lower()
            )
        )

        self.apply_filters()

        add_system_log(
            self.history,
            "🌍 Entidades cargadas para crear mundo"
        )

    def apply_filters(self):
        selected_type = self.type_combo.currentData()
        search = self.search_input.text().lower().strip()

        self.filtered_entities = []

        for entity in self.entities:
            entity_type = entity.get("type", "")

            if selected_type and entity_type != selected_type:
                continue

            searchable = json.dumps(
                entity,
                ensure_ascii=False
            ).lower()

            if search and search not in searchable:
                continue

            self.filtered_entities.append(entity)

        self.populate_entity_list()

    def populate_entity_list(self):
        self.entity_list.blockSignals(True)
        self.entity_list.clear()

        for entity in self.filtered_entities:
            entity_type = entity.get("type", "entity")
            icon = TYPE_ICONS.get(entity_type, "●")
            type_label = display_entity_type(entity_type)

            name = entity.get("name", "Sin nombre")
            entity_id = entity.get("id", "sin_id")

            item = QListWidgetItem(
                f"{icon} {name} [{type_label}] ({entity_id})"
            )

            item.setData(Qt.UserRole, entity)

            self.entity_list.addItem(item)

        self.entity_list.blockSignals(False)

    # =========================
    # Guardar
    # =========================

    def save_current_world(self):
        name = self.name_input.text().strip()

        if not name:
            self.result.append("⚠ El mundo necesita un nombre.")
            return

        selected_entities = []

        for item in self.entity_list.selectedItems():
            entity = item.data(Qt.UserRole)

            selected_entities.append({
                "id": entity.get("id"),
                "name": entity.get("name"),
                "type": entity.get("type")
            })

        world = {
            "name": name,
            "type": "world",
            "description": self.description_input.toPlainText().strip(),
            "entities": selected_entities
        }

        world_id = save_world(world)

        self.result.append(
            "\n"
            "🌍 MUNDO GUARDADO\n"
            f"ID: {world_id}\n"
            f"Nombre: {name}\n"
            f"Entidades incluidas: {len(selected_entities)}\n"
        )

        add_system_log(
            self.history,
            f"🌍 Mundo creado → {name} ({world_id})"
        )