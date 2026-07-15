import json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem,
    QTextEdit, QSplitter, QMessageBox, QComboBox, QLineEdit,
    QTabWidget, QMenu, QDialog, QFormLayout, QSpinBox,
    QDoubleSpinBox
)

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter

from services.world_map_service import (
    get_map_nodes,
    save_map_nodes
)

from services.world_simulation_service import (
    advance_world_turn,
    format_events_for_display,
    load_world_events,
    save_world_events,
    create_event
)

from services.world_time_service import load_world_time
from widgets.world_registry_widget import WorldRegistryWidget
from core.system_log import add_system_log
from core.display_names import display_entity_type


MAP_ENTITY_FILES = [
    "npcs.json",
    "locations.json",
    "kingdoms.json",
    "factions.json",
    "species.json",
    "creatures.json",
    "armies.json",
    "relics.json",
    "items.json",
    "weapons.json",
    "armors.json",
    "foods.json",
    "default_items.json"
]


MAP_ENTITY_TYPES = {
    "npcs": "NPCs",
    "locations": "Lugares",
    "kingdoms": "Reinos / Ciudades",
    "factions": "Facciones",
    "species": "Razas / Especies",
    "creatures": "Criaturas",
    "armies": "Ejércitos",
    "relics": "Reliquias",
    "items": "Objetos importantes",
    "weapons": "Armas importantes",
    "armors": "Armaduras importantes",
    "foods": "Recursos / Consumibles"
}


TYPE_COLORS = {
    "npcs": QColor("#3FA7D6"),
    "locations": QColor("#55B867"),
    "kingdoms": QColor("#D6A43F"),
    "factions": QColor("#B66DD6"),
    "species": QColor("#9AD0C2"),
    "creatures": QColor("#C44D58"),
    "armies": QColor("#D64545"),
    "relics": QColor("#E6D450"),
    "items": QColor("#AAAAAA"),
    "weapons": QColor("#D68A3F"),
    "armors": QColor("#7B9ACC"),
    "foods": QColor("#7CCB8A")
}


TYPE_ICONS = {
    "npcs": "👤",
    "locations": "📍",
    "kingdoms": "🏰",
    "factions": "⚑",
    "species": "🧬",
    "creatures": "🐾",
    "armies": "⚔",
    "relics": "💎",
    "items": "📦",
    "weapons": "🗡",
    "armors": "🛡",
    "foods": "🍖"
}


def load_map_entities_fast():
    entities = []

    for filename in MAP_ENTITY_FILES:
        path = os.path.join("entities", filename)

        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except Exception:
                continue

        if not isinstance(data, list):
            continue

        for entity in data:
            if not isinstance(entity, dict):
                continue

            entity_type = entity.get("type", "")
            entity_id = entity.get("id", "")

            if entity_type not in MAP_ENTITY_TYPES:
                continue

            if entity_id.startswith("default_") and not entity.get("map_enabled", False):
                continue

            entities.append(entity)

    return entities


class ZoomableGraphicsView(QGraphicsView):

    def __init__(self, scene, on_empty_context_menu=None):
        super().__init__(scene)

        self.zoom_level = 1.0
        self.on_empty_context_menu = on_empty_context_menu

        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        scene_pos = self.mapToScene(event.pos())

        if item:
            return super().contextMenuEvent(event)

        if self.on_empty_context_menu:
            self.on_empty_context_menu(
                event.globalPos(),
                scene_pos
            )

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.apply_zoom(1.15)

    def zoom_out(self):
        self.apply_zoom(1 / 1.15)

    def apply_zoom(self, factor):
        new_zoom = self.zoom_level * factor

        if new_zoom < 0.25 or new_zoom > 3.5:
            return

        self.zoom_level = new_zoom
        self.scale(factor, factor)

    def reset_zoom(self):
        self.resetTransform()
        self.zoom_level = 1.0


class MapNodeItem(QGraphicsEllipseItem):

    def __init__(
        self,
        node,
        on_position_changed,
        on_selected,
        on_context_menu=None
    ):
        super().__init__(-28, -28, 56, 56)

        self.node = node
        self.on_position_changed = on_position_changed
        self.on_selected = on_selected
        self.on_context_menu = on_context_menu

        entity_type = node.get("type", "entity")
        color = TYPE_COLORS.get(entity_type, QColor("#3FA7D6"))
        icon = TYPE_ICONS.get(entity_type, "●")

        if node.get("state", {}).get("paused"):
            color = QColor("#555555")

        self.setPos(
            float(node.get("x", 100)),
            float(node.get("y", 100))
        )

        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#F3DFA2"), 2))

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.icon_label = QGraphicsTextItem(icon, self)
        self.icon_label.setDefaultTextColor(Qt.white)
        self.icon_label.setPos(-12, -18)
        self.icon_label.setFlag(QGraphicsItem.ItemIsSelectable, False)

        label_text = node.get("name", "Entidad")

        if node.get("state", {}).get("paused"):
            label_text = f"⏸ {label_text}"

        self.label = QGraphicsTextItem(label_text, self)
        self.label.setDefaultTextColor(QColor("#F7F1D1"))
        self.label.setTextWidth(150)
        self.label.setPos(-72, 34)
        self.label.setFlag(QGraphicsItem.ItemIsSelectable, False)

    def contextMenuEvent(self, event):
        if self.on_context_menu:
            self.on_context_menu(
                self.node.get("entity_id"),
                event.screenPos()
            )
            event.accept()
            return

        super().contextMenuEvent(event)

    def mousePressEvent(self, event):
        if self.on_selected:
            self.on_selected(self.node.get("entity_id"))

        return super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = self.pos()

            self.node["x"] = pos.x()
            self.node["y"] = pos.y()

            if self.on_position_changed:
                self.on_position_changed(
                    self.node.get("entity_id"),
                    pos.x(),
                    pos.y()
                )

        return super().itemChange(change, value)


class WorldMapWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []
        self.filtered_entities = []
        self.nodes = []
        self.node_items = {}
        self.selected_node_id = None
        self.world_events = []
        self.filtered_world_events = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.map_tab = QWidget()
        self.registry_tab = QWidget()

        self.tabs.addTab(self.map_tab, "🗺 Mapa")
        self.tabs.addTab(self.registry_tab, "📜 Registro del Mundo")

        self.setup_map_tab()
        self.setup_registry_tab()

        self.load_entities()
        self.load_map()
        self.world_registry_widget.load_events()

    def setup_map_tab(self):
        layout = QVBoxLayout()
        self.map_tab.setLayout(layout)

        title = QLabel("🗺 Mapa de Mundo")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.refresh_btn = QPushButton("Refrescar entidades")
        left_layout.addWidget(self.refresh_btn)

        left_layout.addWidget(QLabel("Tipo de entidad:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos los tipos del mapa", None)

        for entity_type, label in MAP_ENTITY_TYPES.items():
            self.type_combo.addItem(label, entity_type)

        left_layout.addWidget(self.type_combo)

        left_layout.addWidget(QLabel("Buscar:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, tipo o ID...")
        left_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("Agregar entidad al mapa")
        self.remove_btn = QPushButton("Quitar seleccionado del mapa")
        self.save_btn = QPushButton("Guardar mapa")
        self.advance_turn_btn = QPushButton("▶ Avanzar turno")

        left_layout.addWidget(self.add_btn)
        left_layout.addWidget(self.remove_btn)
        left_layout.addWidget(self.save_btn)
        left_layout.addWidget(self.advance_turn_btn)

        left_layout.addWidget(QLabel("Entidades disponibles:"))

        self.entity_list = QListWidget()
        left_layout.addWidget(self.entity_list)

        left_layout.addWidget(QLabel("Detalle / resultado del turno:"))

        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        left_layout.addWidget(self.detail)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        zoom_layout = QHBoxLayout()

        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.reset_zoom_btn = QPushButton("100%")
        self.center_btn = QPushButton("Centrar")
        self.fit_btn = QPushButton("Ajustar todo")

        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.reset_zoom_btn)
        zoom_layout.addWidget(self.center_btn)
        zoom_layout.addWidget(self.fit_btn)
        zoom_layout.addStretch()

        right_layout.addLayout(zoom_layout)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(QRectF(-2500, -2500, 5000, 5000))

        self.view = ZoomableGraphicsView(
            self.scene,
            on_empty_context_menu=self.show_empty_map_context_menu
        )

        right_layout.addWidget(self.view)

        splitter.addWidget(right_panel)

        splitter.setSizes([360, 1000])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.refresh_btn.clicked.connect(self.load_entities)
        self.add_btn.clicked.connect(self.add_selected_entity_to_map)
        self.remove_btn.clicked.connect(self.remove_selected_node)
        self.save_btn.clicked.connect(self.save_current_map)
        self.advance_turn_btn.clicked.connect(self.advance_turn)

        self.type_combo.currentIndexChanged.connect(self.apply_entity_filters)
        self.search_input.textChanged.connect(self.apply_entity_filters)
        self.entity_list.currentRowChanged.connect(self.show_selected_entity_detail)

        self.zoom_in_btn.clicked.connect(self.view.zoom_in)
        self.zoom_out_btn.clicked.connect(self.view.zoom_out)
        self.reset_zoom_btn.clicked.connect(self.view.reset_zoom)
        self.center_btn.clicked.connect(self.center_on_selected_node)
        self.fit_btn.clicked.connect(self.fit_all_nodes)

    def setup_registry_tab(self):
        layout = QVBoxLayout()
        self.registry_tab.setLayout(layout)

        self.world_registry_widget = WorldRegistryWidget(
            on_advance_turn=self.advance_turn
        )

        layout.addWidget(self.world_registry_widget)

    def load_entities(self):
        self.entities = load_map_entities_fast()

        self.entities.sort(
            key=lambda item: (
                item.get("type", "").lower(),
                item.get("name", "").lower()
            )
        )

        self.apply_entity_filters()

        add_system_log(
            self.history,
            "🗺 Entidades del mapa cargadas"
        )

    def apply_entity_filters(self):
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

            label = (
                f"{icon} {entity.get('name', 'Sin nombre')} "
                f"[{display_entity_type(entity_type)}] "
                f"({entity.get('id', 'sin_id')})"
            )

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, entity.get("id"))

            self.entity_list.addItem(item)

        self.entity_list.blockSignals(False)

        if self.entity_list.count() > 0:
            self.entity_list.setCurrentRow(0)
        else:
            self.detail.clear()

    def get_selected_entity(self):
        item = self.entity_list.currentItem()

        if not item:
            return None

        entity_id = item.data(Qt.UserRole)

        for entity in self.filtered_entities:
            if entity.get("id") == entity_id:
                return entity

        return None

    def get_entity_by_id(self, entity_id):
        for entity in self.entities:
            if entity.get("id") == entity_id:
                return entity

        return None

    def get_node_by_id(self, entity_id):
        for node in self.nodes:
            if node.get("entity_id") == entity_id:
                return node

        return None

    def show_selected_entity_detail(self):
        entity = self.get_selected_entity()

        if not entity:
            self.detail.clear()
            return

        self.show_entity_detail(entity)

    def show_entity_detail(self, entity):
        lines = []

        lines.append(f"Nombre: {entity.get('name', 'Sin nombre')}")
        lines.append(f"ID: {entity.get('id', '-')}")
        lines.append(f"Tipo: {display_entity_type(entity.get('type', 'entity'))}")
        lines.append("")

        meta = entity.get("meta", {})

        if isinstance(meta, dict) and meta:
            lines.append("Meta:")
            for key, value in meta.items():
                lines.append(f"- {key}: {self.format_complex_value(key, value)}")
            lines.append("")

        data = entity.get("data", {})

        if isinstance(data, dict) and data:
            lines.append("Data:")
            for key, value in data.items():
                formatted_value = self.format_complex_value(key, value)
                lines.append(f"- {key}: {formatted_value}")
            lines.append("")

        zone = entity.get("zone", {})

        if isinstance(zone, dict) and zone:
            lines.append("Zona:")
            for key, value in zone.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        effects = entity.get("effects", {})

        if isinstance(effects, dict) and effects:
            lines.append("Efectos:")
            for key, value in effects.items():
                lines.append(f"- {key}: {value}")

        self.detail.setPlainText("\n".join(lines))

    def format_complex_value(self, key, value):
        if key == "Equipo inicial" and isinstance(value, dict):
            return self.format_loadout(value)

        if key == "Magia/Poderes" and isinstance(value, dict):
            return self.format_magic_data(value)

        if isinstance(value, list):
            if not value:
                return "Ninguno"

            return "\n" + "\n".join(
                f"  • {item}" if not isinstance(item, dict)
                else f"  • {item.get('name', str(item))}"
                for item in value
            )

        if isinstance(value, dict):
            return "\n" + "\n".join(
                f"  • {sub_key}: {self.format_complex_value(sub_key, sub_value)}"
                for sub_key, sub_value in value.items()
            )

        return str(value)

    def format_loadout(self, loadout):
        lines = []

        weapon = loadout.get("weapon")
        armor = loadout.get("armor")
        items = loadout.get("items", [])
        relics = loadout.get("relics", [])

        if weapon:
            lines.append(f"  • Arma: {weapon.get('name', 'Sin arma')}")

        if armor:
            lines.append(f"  • Armadura: {armor.get('name', 'Sin armadura')}")

        if items:
            lines.append("  • Items:")
            for item in items:
                if isinstance(item, dict):
                    lines.append(f"    - {item.get('name', 'Item sin nombre')}")
                else:
                    lines.append(f"    - {item}")

        if relics:
            lines.append("  • Reliquias:")
            for relic in relics:
                if isinstance(relic, dict):
                    lines.append(f"    - {relic.get('name', 'Reliquia sin nombre')}")
                else:
                    lines.append(f"    - {relic}")

        if not lines:
            return "Ninguno"

        return "\n" + "\n".join(lines)

    def format_magic_data(self, magic_data):
        if not magic_data.get("knows_magic"):
            return "No conoce magia"

        systems = magic_data.get("known_systems", [])

        if not systems:
            return "Conoce magia, pero sin sistemas registrados"

        lines = ["Conoce magia:"]

        for system in systems:
            if isinstance(system, dict):
                lines.append(f"  • {system.get('name', 'Sistema sin nombre')}")
            else:
                lines.append(f"  • {system}")

        return "\n" + "\n".join(lines)

    def extract_zone_from_entity(self, entity):
        data = entity.get("data", {}) or {}

        biome = (
            data.get("Bioma")
            or data.get("Terreno")
            or data.get("Ubicación - Terreno")
            or "indefinido"
        )

        terrain = (
            data.get("Terreno")
            or data.get("Tipo de terreno")
            or "normal"
        )

        climate = (
            data.get("Clima")
            or data.get("Ubicación - Clima")
            or "templado"
        )

        danger_text = str(
            data.get("Nivel de peligro")
            or data.get("Peligro")
            or ""
        ).lower()

        danger = 15

        if "bajo" in danger_text:
            danger = 10
        elif "medio" in danger_text or "moderado" in danger_text:
            danger = 30
        elif "alto" in danger_text:
            danger = 55
        elif "extremo" in danger_text or "mortal" in danger_text:
            danger = 80

        travel_cost = 1.0

        terrain_lower = str(terrain).lower()
        biome_lower = str(biome).lower()

        hard_words = [
            "montaña",
            "pantano",
            "selva",
            "ruinas"
        ]

        medium_words = [
            "bosque",
            "desierto",
            "nieve"
        ]

        easy_words = [
            "camino",
            "llanura",
            "pradera"
        ]

        if any(word in terrain_lower or word in biome_lower for word in hard_words):
            travel_cost = 1.6
        elif any(word in terrain_lower or word in biome_lower for word in medium_words):
            travel_cost = 1.3
        elif any(word in terrain_lower or word in biome_lower for word in easy_words):
            travel_cost = 0.9

        return {
            "biome": biome,
            "terrain": terrain,
            "climate": climate,
            "danger": danger,
            "travel_cost": travel_cost,
            "encounter_chance": max(5, min(60, danger // 2))
        }

    def load_map(self):
        loaded_nodes = get_map_nodes()
        self.nodes = []

        for node in loaded_nodes:
            entity_type = node.get("type", "")
            entity_id = node.get("entity_id", "")

            if entity_type not in MAP_ENTITY_TYPES:
                continue

            if entity_id.startswith("default_") and not node.get("map_enabled", False):
                continue

            self.nodes.append(node)

        self.redraw_map()

    def redraw_map(self):
        self.scene.clear()
        self.node_items = {}
        self.selected_node_id = None

        self.draw_background_grid()

        for node in self.nodes:
            self.create_node_item(node)

    def draw_background_grid(self):
        pen = QPen(QColor("#32384A"), 1)

        step = 100
        min_value = -2500
        max_value = 2500

        for x in range(min_value, max_value + step, step):
            self.scene.addLine(x, min_value, x, max_value, pen)

        for y in range(min_value, max_value + step, step):
            self.scene.addLine(min_value, y, max_value, y, pen)

    def create_node_item(self, node):
        item = MapNodeItem(
            node,
            self.on_node_position_changed,
            self.on_node_selected,
            self.show_node_context_menu
        )

        self.scene.addItem(item)
        self.node_items[node.get("entity_id")] = item

    def on_node_selected(self, entity_id):
        self.selected_node_id = entity_id

        node = self.get_node_by_id(entity_id)
        entity = self.get_entity_by_id(entity_id)

        if node:
            self.show_entity_detail(node)
        elif entity:
            self.show_entity_detail(entity)

        item = self.node_items.get(entity_id)

        if item:
            item.setSelected(True)

    def on_node_position_changed(self, entity_id, x, y):
        for node in self.nodes:
            if node.get("entity_id") == entity_id:
                node["x"] = x
                node["y"] = y
                break

    def show_node_context_menu(self, entity_id, global_pos):
        node = self.get_node_by_id(entity_id)

        if not node:
            return

        self.selected_node_id = entity_id

        menu = QMenu(self)

        pause_action = menu.addAction("⏸ Pausar / reanudar entidad")
        event_action = menu.addAction("⚡ Causar evento aquí")
        clear_destination_action = menu.addAction("🧭 Quitar destino actual")
        edit_zone_action = menu.addAction("🌍 Editar terreno / zona")
        delete_action = menu.addAction("🗑 Quitar del mapa")

        selected_action = menu.exec(global_pos)

        if selected_action == pause_action:
            self.toggle_node_paused(node)

        elif selected_action == event_action:
            self.create_manual_event_for_node(node)

        elif selected_action == clear_destination_action:
            self.clear_node_destination(node)

        elif selected_action == edit_zone_action:
            self.open_zone_dialog_for_node(node)

        elif selected_action == delete_action:
            self.selected_node_id = entity_id
            self.remove_selected_node()

    def show_empty_map_context_menu(self, global_pos, scene_pos):
        menu = QMenu(self)

        create_zone_action = menu.addAction("🌍 Crear terreno / zona aquí")
        create_event_action = menu.addAction("⚡ Crear evento en este sector")

        selected_action = menu.exec(global_pos)

        if selected_action == create_zone_action:
            self.create_zone_at_position(scene_pos)

        elif selected_action == create_event_action:
            self.create_manual_event_at_position(scene_pos)

    def toggle_node_paused(self, node):
        state = node.setdefault("state", {})
        paused = bool(state.get("paused", False))

        state["paused"] = not paused

        status = "pausada" if state["paused"] else "reactivada"

        self.save_current_map_silent()
        self.redraw_map()

        add_system_log(
            self.history,
            f"⏸ Entidad {status} → {node.get('name', 'Entidad')}"
        )

    def clear_node_destination(self, node):
        state = node.setdefault("state", {})
        state.pop("destination", None)

        self.save_current_map_silent()

        add_system_log(
            self.history,
            f"🧭 Destino eliminado → {node.get('name', 'Entidad')}"
        )

    def create_manual_event_for_node(self, node):
        world_time = load_world_time()
        events = load_world_events()

        event = create_event(
            "manual_event",
            f"Evento provocado en {node.get('name', 'Entidad')}",
            f"Ocurrió un evento provocado manualmente sobre {node.get('name', 'Entidad')}.",
            world_time,
            node,
            [],
            extra={
                "manual": True
            }
        )

        events.append(event)
        save_world_events(events)

        self.world_registry_widget.load_events()

        add_system_log(
            self.history,
            f"⚡ Evento manual creado → {node.get('name', 'Entidad')}"
        )

    def create_manual_event_at_position(self, scene_pos):
        temp_node = {
            "entity_id": f"sector_{int(scene_pos.x())}_{int(scene_pos.y())}",
            "name": "Sector sin nombre",
            "type": "sector",
            "x": scene_pos.x(),
            "y": scene_pos.y()
        }

        world_time = load_world_time()
        events = load_world_events()

        event = create_event(
            "manual_sector_event",
            "Evento provocado en un sector vacío",
            "Ocurrió un evento provocado manualmente en un sector vacío del mapa.",
            world_time,
            temp_node,
            [],
            extra={
                "manual": True,
                "x": scene_pos.x(),
                "y": scene_pos.y()
            }
        )

        events.append(event)
        save_world_events(events)

        self.world_registry_widget.load_events()

        add_system_log(
            self.history,
            "⚡ Evento manual creado en sector vacío"
        )

    def open_zone_dialog_for_node(self, node):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar terreno / zona")

        layout = QFormLayout()
        dialog.setLayout(layout)

        zone = node.get("zone", {}) or {}

        name_input = QLineEdit()
        name_input.setText(node.get("name", "Zona sin nombre"))

        biome_combo = QComboBox()
        biome_combo.addItems([
            "indefinido",
            "bosque",
            "pantano",
            "montaña",
            "desierto",
            "llanura",
            "ruinas",
            "costa",
            "ciudad",
            "subterráneo",
            "zona maldita"
        ])
        biome_combo.setCurrentText(str(zone.get("biome", "indefinido")))

        terrain_combo = QComboBox()
        terrain_combo.addItems([
            "normal",
            "fácil",
            "difícil",
            "denso",
            "rocoso",
            "inestable",
            "peligroso",
            "camino"
        ])
        terrain_combo.setCurrentText(str(zone.get("terrain", "normal")))

        climate_combo = QComboBox()
        climate_combo.addItems([
            "templado",
            "frío",
            "caluroso",
            "húmedo",
            "seco",
            "tormentoso",
            "nevado",
            "mágico",
            "tóxico"
        ])
        climate_combo.setCurrentText(str(zone.get("climate", "templado")))

        danger_spin = QSpinBox()
        danger_spin.setRange(0, 100)
        danger_spin.setValue(int(zone.get("danger", 15)))

        travel_cost_spin = QDoubleSpinBox()
        travel_cost_spin.setRange(0.3, 5.0)
        travel_cost_spin.setSingleStep(0.1)
        travel_cost_spin.setValue(float(zone.get("travel_cost", 1.0)))

        encounter_spin = QSpinBox()
        encounter_spin.setRange(0, 100)
        encounter_spin.setValue(int(zone.get("encounter_chance", 10)))

        save_btn = QPushButton("Guardar zona")

        layout.addRow("Nombre:", name_input)
        layout.addRow("Bioma:", biome_combo)
        layout.addRow("Terreno:", terrain_combo)
        layout.addRow("Clima:", climate_combo)
        layout.addRow("Peligro:", danger_spin)
        layout.addRow("Costo de viaje:", travel_cost_spin)
        layout.addRow("Encuentros %:", encounter_spin)
        layout.addRow(save_btn)

        def save_zone():
            node["name"] = (
                name_input.text().strip()
                or node.get("name", "Zona sin nombre")
            )

            node["zone"] = {
                "biome": biome_combo.currentText(),
                "terrain": terrain_combo.currentText(),
                "climate": climate_combo.currentText(),
                "danger": danger_spin.value(),
                "travel_cost": travel_cost_spin.value(),
                "encounter_chance": encounter_spin.value()
            }

            node.setdefault("state", {})
            node["state"]["zone_enabled"] = True

            self.save_current_map_silent()
            self.redraw_map()

            add_system_log(
                self.history,
                f"🌍 Zona actualizada → {node.get('name', 'Zona')}"
            )

            dialog.accept()

        save_btn.clicked.connect(save_zone)

        dialog.exec()

    def create_zone_at_position(self, scene_pos):
        node = {
            "entity_id": f"zone_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": "Zona sin nombre",
            "type": "locations",
            "x": scene_pos.x(),
            "y": scene_pos.y(),
            "map_enabled": True,
            "location_role": "wild_zone",
            "tags": ["zone", "wild_zone"],
            "data": {
                "Tipo de creación": "Zona del mapa"
            },
            "meta": {
                "created_from_map": True
            },
            "effects": {},
            "state": {},
            "resources": {},
            "zone": {
                "biome": "indefinido",
                "terrain": "normal",
                "climate": "templado",
                "danger": 15,
                "travel_cost": 1.0,
                "encounter_chance": 10
            }
        }

        self.nodes.append(node)
        self.create_node_item(node)
        self.open_zone_dialog_for_node(node)

        add_system_log(
            self.history,
            "🌍 Nueva zona creada desde el mapa"
        )

    def add_selected_entity_to_map(self):
        entity = self.get_selected_entity()

        if not entity:
            QMessageBox.warning(
                self,
                "Sin entidad",
                "Selecciona una entidad primero."
            )
            return

        entity_id = entity.get("id")

        for node in self.nodes:
            if node.get("entity_id") == entity_id:
                QMessageBox.information(
                    self,
                    "Ya existe",
                    "Esta entidad ya está en el mapa."
                )
                self.center_on_entity(entity_id)
                return

        offset = len(self.nodes) * 40

        zone = None

        if entity.get("type") in ["locations", "kingdoms"]:
            zone = self.extract_zone_from_entity(entity)

        node = {
            "entity_id": entity_id,
            "name": entity.get("name", "Sin nombre"),
            "type": entity.get("type", "entity"),
            "x": 100 + offset,
            "y": 100 + offset,
            "map_enabled": bool(entity.get("map_enabled", False)),
            "location_role": entity.get("location_role"),
            "tags": entity.get("tags", []),
            "data": entity.get("data", {}),
            "meta": entity.get("meta", {}),
            "effects": entity.get("effects", {}),
            "state": entity.get("state", {}),
            "resources": entity.get("resources", {}),
            "zone": zone
        }

        self.nodes.append(node)
        self.create_node_item(node)
        self.center_on_entity(entity_id)

        add_system_log(
            self.history,
            f"🗺 Entidad agregada al mapa sin guardar → {entity.get('name')}"
        )

    def remove_selected_node(self):
        entity_id = self.selected_node_id

        if not entity_id:
            selected_items = self.scene.selectedItems()

            for item in selected_items:
                if isinstance(item, MapNodeItem):
                    entity_id = item.node.get("entity_id")
                    break

                parent = item.parentItem()

                if isinstance(parent, MapNodeItem):
                    entity_id = parent.node.get("entity_id")
                    break

        if not entity_id:
            QMessageBox.information(
                self,
                "Sin selección",
                "Selecciona un nodo directamente en el mapa."
            )
            return

        node = next(
            (
                item for item in self.nodes
                if item.get("entity_id") == entity_id
            ),
            None
        )

        if not node:
            QMessageBox.information(
                self,
                "No está en el mapa",
                "La entidad seleccionada no está colocada en el mapa."
            )
            return

        self.nodes = [
            item for item in self.nodes
            if item.get("entity_id") != entity_id
        ]

        self.selected_node_id = None
        self.redraw_map()

        add_system_log(
            self.history,
            f"🗑 Entidad quitada del mapa sin guardar → {node.get('name')}"
        )

    def save_current_map_silent(self):
        clean_nodes = self.build_clean_nodes()
        save_map_nodes(clean_nodes)

    def save_current_map(self):
        clean_nodes = self.build_clean_nodes()
        save_map_nodes(clean_nodes)

        QMessageBox.information(
            self,
            "Guardado",
            "Mapa guardado correctamente."
        )

        add_system_log(
            self.history,
            "💾 Mapa de mundo guardado"
        )

    def build_clean_nodes(self):
        clean_nodes = []

        for node in self.nodes:
            clean_nodes.append({
                "entity_id": node.get("entity_id"),
                "name": node.get("name"),
                "type": node.get("type"),
                "x": float(node.get("x", 0)),
                "y": float(node.get("y", 0)),
                "map_enabled": bool(node.get("map_enabled", False)),

                "location_role": node.get("location_role"),
                "tags": node.get("tags", []),
                "data": node.get("data", {}),
                "meta": node.get("meta", {}),
                "effects": node.get("effects", {}),
                "zone": node.get("zone"),

                "state": node.get("state", {}),
                "resources": node.get("resources", {}),
                "party_id": node.get("party_id"),
                "relations": node.get("relations", {}),
                "knowledge": node.get("knowledge", []),
                "inventory_notes": node.get("inventory_notes", []),
                "memory": node.get("memory", [])
            })

        return clean_nodes

    def advance_turn(self):
        self.save_current_map_silent()

        result = advance_world_turn()

        self.nodes = result.get("nodes", [])
        self.redraw_map()

        text = (
            "▶ TURNO AVANZADO\n"
            f"Fecha: {result.get('world_date', 'Sin fecha')}\n"
            f"Entidades movidas: {result.get('moved_count', 0)}\n"
            f"Eventos generados: {result.get('events_count', 0)}\n\n"
            f"{format_events_for_display(result.get('events', []))}"
        )

        self.detail.setPlainText(text)
        self.world_registry_widget.load_events()

        add_system_log(
            self.history,
            f"▶ Turno avanzado → {result.get('events_count', 0)} eventos"
        )

    def center_on_selected_node(self):
        if self.selected_node_id:
            self.center_on_entity(self.selected_node_id)
            return

        entity = self.get_selected_entity()

        if entity:
            self.center_on_entity(entity.get("id"))

    def center_on_entity(self, entity_id):
        item = self.node_items.get(entity_id)

        if not item:
            return

        self.view.centerOn(item)
        item.setSelected(True)
        self.selected_node_id = entity_id

    def fit_all_nodes(self):
        if not self.node_items:
            self.view.centerOn(0, 0)
            return

        rect = QRectF()

        for item in self.node_items.values():
            scene_rect = item.sceneBoundingRect()

            if rect.isNull():
                rect = scene_rect
            else:
                rect = rect.united(scene_rect)

        if rect.isValid():
            self.view.fitInView(
                rect.adjusted(-200, -200, 200, 200),
                Qt.KeepAspectRatio
            )

            self.view.zoom_level = 1.0