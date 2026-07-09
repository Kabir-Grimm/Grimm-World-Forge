import math

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsLineItem,
    QGraphicsItem,
    QSplitter,
    QTextEdit,
    QLineEdit,
    QSizePolicy
)

from PySide6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QFont
)

from PySide6.QtCore import (
    Qt,
    QPointF,
    QRectF
)

from services.graph_layout_service import (
    load_graph_positions,
    save_graph_positions
)

from services.relation_service import load_relations
from services.entity_registry_service import load_registry_entities
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox
from core.display_names import (
    display_entity_type,
    display_stat,
    display_reputation,
    display_meta
)


class GraphView(QGraphicsView):

    def __init__(self, scene):
        super().__init__(scene)

        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setMinimumWidth(300)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in

        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)


class GraphNode(QGraphicsEllipseItem):

    def __init__(
        self,
        entity,
        x,
        y,
        radius,
        color,
        is_root=False,
        on_select=None
    ):
        super().__init__(
            -radius,
            -radius,
            radius * 2,
            radius * 2
        )

        self.entity = entity
        self.edges = []
        self.radius = radius
        self.on_select = on_select

        self.setPos(x, y)
        self.setBrush(QBrush(color))

        border_color = QColor("#C8A45D")

        if is_root:
            border_color = QColor("#B8860B")

        self.setPen(QPen(border_color, 2))

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        name = entity.get("name", "Sin nombre")
        entity_type = entity.get("type", "entity")
        entity_id = entity.get("id", "sin_id")

        self.setToolTip(
            f"{name}\n"
            f"Tipo: {display_entity_type(entity_type)}\n"
            f"ID: {entity_id}"
        )

        self.label = QGraphicsTextItem(name, self)

        self.label.setFont(
            QFont("Segoe UI",10,QFont.Bold )
        )
        self.label.setDefaultTextColor(
            QColor("#F3E7BB")
        )

        label_rect = self.label.boundingRect()

        self.label.setPos(
            -label_rect.width() / 2,
            radius + 4
        )

    def mousePressEvent(self, event):
        if self.on_select:
            self.on_select(self.entity)

        super().mousePressEvent(event)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()

        return super().itemChange(change, value)


class GraphEdge(QGraphicsLineItem):

    def __init__(self, source_node, target_node, relation, direction="out"):
        super().__init__()

        self.source_node = source_node
        self.target_node = target_node
        self.relation = relation
        self.direction = direction

        self.setPen(
            QPen(
                QColor("#C8A45D"),
                2
            )
        )

        self.label = QGraphicsTextItem()

        self.label.setFont(
            QFont(
                "Segoe UI",
                9,
                QFont.Bold
            )
        )

        self.label.setDefaultTextColor(
            QColor("#FFD987")
        )

        source_node.add_edge(self)
        target_node.add_edge(self)

        self.update_tooltip()
        self.update_position()

    def update_tooltip(self):
        source = self.relation.get("source", {}).get("name", "Origen")
        target = self.relation.get("target", {}).get("name", "Destino")
        relation_type = self.relation.get("relation_type", "relación")
        notes = self.relation.get("notes", "")

        tooltip = f"{source} → {relation_type} → {target}"

        if notes:
            tooltip += f"\nNotas: {notes}"

        self.setToolTip(tooltip)
        self.label.setToolTip(tooltip)

    def update_position(self):
        p1 = self.source_node.pos()
        p2 = self.target_node.pos()

        self.setLine(
            p1.x(),
            p1.y(),
            p2.x(),
            p2.y()
        )

        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2

        relation_type = self.relation.get("relation_type", "relación")

        if self.direction == "in":
            label_text = f"{relation_type} ←"
        elif self.direction == "out":
            label_text = f"→ {relation_type}"
        else:
            label_text = relation_type

        self.label.setPlainText(label_text)

        rect = self.label.boundingRect()

        self.label.setPos(
            mid_x - rect.width() / 2,
            mid_y - rect.height() / 2
        )


class RelationGraphWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.relations = []
        self.entities = {}
        self.nodes = []
        self.edges = []
        self.saved_positions = load_graph_positions()

        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # =========================
        # CONTROLES - FILA 1
        # =========================

        controls_top = QHBoxLayout()

        controls_top.addWidget(QLabel("Tipo:"))

        self.type_combo = QComboBox()
        self.type_combo.setMinimumWidth(130)
        self.type_combo.setMaximumWidth(200)
        controls_top.addWidget(self.type_combo)

        controls_top.addWidget(QLabel("Buscar:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre...")
        self.search_input.setMinimumWidth(160)
        self.search_input.setMaximumWidth(260)
        controls_top.addWidget(self.search_input)

        controls_top.addWidget(QLabel("Entidad raíz:"))

        self.entity_combo = QComboBox()
        self.entity_combo.setMinimumWidth(260)
        self.entity_combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        controls_top.addWidget(self.entity_combo)

        layout.addLayout(controls_top)


        # =========================
        # CONTROLES - FILA 2
        # =========================

        controls_bottom = QHBoxLayout()

        controls_bottom.addWidget(QLabel("Profundidad:"))

        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["1", "2"])
        self.depth_combo.setMinimumWidth(80)
        self.depth_combo.setMaximumWidth(100)
        controls_bottom.addWidget(self.depth_combo)

        self.refresh_btn = QPushButton("Refrescar")
        self.draw_btn = QPushButton("Mostrar red")
        self.center_btn = QPushButton("Centrar")
        self.save_layout_btn = QPushButton("Guardar layout")

        self.refresh_btn.setMinimumWidth(110)
        self.draw_btn.setMinimumWidth(120)
        self.center_btn.setMinimumWidth(90)
        self.save_layout_btn.setMinimumWidth(130)

        controls_bottom.addWidget(self.refresh_btn)
        controls_bottom.addWidget(self.draw_btn)
        controls_bottom.addWidget(self.center_btn)
        controls_bottom.addWidget(self.save_layout_btn)

        controls_bottom.addStretch()

        layout.addLayout(controls_bottom)

        self.scene = QGraphicsScene()

        self.scene.setBackgroundBrush(
            QColor("#050A14")
        )

        self.view = GraphView(self.scene)

        self.detail_panel = QTextEdit()
        self.detail_panel.setReadOnly(True)
        self.detail_panel.setMinimumWidth(180)
        self.detail_panel.setMaximumWidth(300)
        self.detail_panel.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding
        )

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.detail_panel)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([620, 220])

        layout.addWidget(splitter)

        self.refresh_btn.clicked.connect(self.load_data)
        self.draw_btn.clicked.connect(self.draw_graph)
        self.center_btn.clicked.connect(self.center_view)
        self.save_layout_btn.clicked.connect(self.save_current_layout)

        self.entity_combo.currentIndexChanged.connect(self.draw_graph)
        self.type_combo.currentIndexChanged.connect(self.populate_entity_combo)
        self.depth_combo.currentIndexChanged.connect(self.draw_graph)
        self.search_input.textChanged.connect(self.populate_entity_combo)

        self.load_data()

    def load_data(self):
        self.relations = load_relations()
        self.entities = {}

        self.load_full_entities()

        for relation in self.relations:
            source = relation.get("source", {})
            target = relation.get("target", {})

            if source.get("id") and source["id"] not in self.entities:
                self.entities[source["id"]] = source

            if target.get("id") and target["id"] not in self.entities:
                self.entities[target["id"]] = target

        self.populate_type_combo()
        self.populate_entity_combo()

        add_system_log(
            self.history,
            "🕸 Mapa de relaciones actualizado"
        )

        self.draw_graph()

    def load_full_entities(self):
        for entity in load_registry_entities():
            entity_id = entity.get("id")

            if entity_id:
                self.entities[entity_id] = entity

    def populate_type_combo(self):
        current_type = self.type_combo.currentData()

        types = sorted({
            entity.get("type", "entity")
            for entity in self.entities.values()
        })

        self.type_combo.blockSignals(True)
        self.type_combo.clear()

        self.type_combo.addItem("Todos", None)

        for entity_type in types:
            self.type_combo.addItem(
                display_entity_type(entity_type),
                entity_type
            )

        sort_combobox(self.type_combo)
        self.type_combo.blockSignals(False)

        if current_type:
            index = self.type_combo.findData(current_type)

            if index >= 0:
                self.type_combo.setCurrentIndex(index)

    def populate_entity_combo(self):
        selected_type = self.type_combo.currentData()
        search = self.search_input.text().lower().strip()
        current_entity = self.entity_combo.currentData()

        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()

        filtered = []

        for entity_id, entity in self.entities.items():
            if selected_type and entity.get("type") != selected_type:
                continue

            name = entity.get("name", "")

            if search and search not in name.lower():
                continue

            filtered.append((entity_id, entity))

        filtered.sort(
            key=lambda item: (
                display_entity_type(item[1].get("type", "")).lower(),
                item[1].get("name", "").lower()
            )
        )

        for entity_id, entity in filtered:
            self.entity_combo.addItem(
                self.format_entity_label(entity),
                entity_id
            )

        sort_combobox(self.entity_combo)
        self.entity_combo.blockSignals(False)

        if current_entity:
            index = self.entity_combo.findData(current_entity)

            if index >= 0:
                self.entity_combo.setCurrentIndex(index)

        self.draw_graph()

    def format_entity_label(self, entity):
        name = entity.get("name", "Sin nombre")
        entity_type = entity.get("type", "entity")
        entity_id = entity.get("id", "sin_id")

        return (
            f"{name} "
            f"[{display_entity_type(entity_type)}] "
            f"({entity_id})"
        )

    def draw_graph(self):
        self.scene.clear()
        self.nodes = []
        self.edges = []

        root_id = self.entity_combo.currentData()

        if not root_id:
            self.detail_panel.clear()
            return

        depth = int(self.depth_combo.currentText())

        visible_relations = self.collect_relations(root_id, depth)
        visible_entities = self.collect_entities(root_id, visible_relations)

        node_positions = self.calculate_positions(
            root_id,
            list(visible_entities.keys())
        )

        for entity_id, entity in visible_entities.items():
            is_root = entity_id == root_id

            position = node_positions.get(
                entity_id,
                QPointF(0, 0)
            )

            node = GraphNode(
                entity=entity,
                x=position.x(),
                y=position.y(),
                radius=58 if is_root else 46,
                color=QColor("#FFD166")
                if is_root
                else self.color_for_type(entity.get("type", "entity")),
                is_root=is_root,
                on_select=self.show_entity_details
            )

            self.scene.addItem(node)
            self.nodes.append(node)

        node_map = {
            node.entity.get("id"): node
            for node in self.nodes
        }

        for relation in visible_relations:
            source = relation.get("source", {})
            target = relation.get("target", {})

            source_id = source.get("id")
            target_id = target.get("id")

            source_node = node_map.get(source_id)
            target_node = node_map.get(target_id)

            if not source_node or not target_node:
                continue

            direction = "out"

            if target_id == root_id:
                direction = "in"

            edge = GraphEdge(
                source_node,
                target_node,
                relation,
                direction
            )

            self.scene.addItem(edge)
            self.scene.addItem(edge.label)
            self.edges.append(edge)

        root_entity = self.entities.get(root_id)

        if root_entity:
            self.show_entity_details(root_entity)

        self.center_view()

    def save_current_layout(self):
        for node in self.nodes:
            entity_id = node.entity.get("id")

            if not entity_id:
                continue

            pos = node.pos()

            self.saved_positions[entity_id] = {
                "x": pos.x(),
                "y": pos.y()
            }

        save_graph_positions(self.saved_positions)

        add_system_log(
            self.history,
            "💾 Layout del mapa guardado"
        )

    def collect_relations(self, root_id, depth):
        collected = []
        visited_entities = {root_id}
        frontier = {root_id}

        for _ in range(depth):
            next_frontier = set()

            for relation in self.relations:
                source_id = relation.get("source", {}).get("id")
                target_id = relation.get("target", {}).get("id")

                if source_id in frontier or target_id in frontier:
                    if relation not in collected:
                        collected.append(relation)

                    if source_id and source_id not in visited_entities:
                        next_frontier.add(source_id)
                        visited_entities.add(source_id)

                    if target_id and target_id not in visited_entities:
                        next_frontier.add(target_id)
                        visited_entities.add(target_id)

            frontier = next_frontier

        return collected

    def collect_entities(self, root_id, relations):
        visible = {}

        if root_id in self.entities:
            visible[root_id] = self.entities[root_id]

        for relation in relations:
            source = relation.get("source", {})
            target = relation.get("target", {})

            source_id = source.get("id")
            target_id = target.get("id")

            if source_id:
                visible[source_id] = self.entities.get(source_id, source)

            if target_id:
                visible[target_id] = self.entities.get(target_id, target)

        return visible

    def calculate_positions(self, root_id, entity_ids):
        positions = {}

        others = [
            entity_id
            for entity_id in entity_ids
            if entity_id != root_id
        ]

        for entity_id in entity_ids:
            saved = self.saved_positions.get(entity_id)

            if saved:
                positions[entity_id] = QPointF(
                    saved.get("x", 0),
                    saved.get("y", 0)
                )

        if root_id not in positions:
            positions[root_id] = QPointF(0, 0)

        radius = 300
        total = max(len(others), 1)

        for index, entity_id in enumerate(others):
            if entity_id in positions:
                continue

            angle = (2 * math.pi * index) / total

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            positions[entity_id] = QPointF(x, y)

        return positions

    def center_view(self):
        rect = self.scene.itemsBoundingRect()

        if rect.isNull():
            rect = QRectF(-300, -300, 600, 600)

        self.view.fitInView(
            rect.adjusted(-40, -40, 40, 40),
            Qt.KeepAspectRatio
        )

    def show_entity_details(self, entity):
        self.detail_panel.setText(
            self.format_entity_details(entity)
        )

    def format_entity_details(self, entity):
        name = entity.get("name", "Sin nombre")
        entity_type = entity.get("type", "entity")
        entity_id = entity.get("id", "sin_id")

        lines = []

        lines.append("══════════════════════")
        lines.append(f"📌 {name}")
        lines.append("══════════════════════")
        lines.append(f"Tipo: {display_entity_type(entity_type)}")
        lines.append(f"ID: {entity_id}")
        lines.append("")

        meta = entity.get("meta", {})

        if isinstance(meta, dict) and meta:
            lines.append("Metadata:")

            for key in [
                "importance",
                "role",
                "power_rank",
                "status",
                "age",
                "life_stage",
                "gender",
                "reputation",
                "personal_goal",
                "fear",
                "desire"
            ]:
                value = meta.get(key)

                if value:
                    lines.append(f"- {display_meta(key)}: {value}")

            traits = meta.get("traits", [])

            if isinstance(traits, list) and traits:
                lines.append("")
                lines.append("Rasgos / Capacidades:")

                for trait in traits:
                    lines.append(f"- {trait}")

            lines.append("")

        reputation = entity.get("reputation", {})

        if isinstance(reputation, dict) and reputation:
            lines.append("Renombre:")

            for key, value in sorted(reputation.items()):
                sign = "+" if value >= 0 else ""
                lines.append(f"- {display_reputation(key)}: {sign}{value}")

            lines.append("")

        memory = entity.get("memory", [])

        if isinstance(memory, list) and memory:
            lines.append("Memorias importantes:")

            sorted_memory = sorted(
                memory,
                key=lambda item: item.get("importance", 1),
                reverse=True
            )

            for item in sorted_memory[:8]:
                importance = item.get("importance", 1)
                description = item.get("description", "Sin descripción")
                year = item.get("year")

                if year:
                    lines.append(
                        f"- [★{importance}] Año {year}: {description}"
                    )
                else:
                    lines.append(
                        f"- [★{importance}] {description}"
                    )

            lines.append("")

        data = entity.get("data", {})

        if isinstance(data, dict):
            race = data.get("Raza")
            profession = data.get("Profesión")

            if race or profession:
                lines.append("Resumen:")

                if race:
                    lines.append(f"- Especie / Origen: {race}")

                if profession:
                    lines.append(f"- Rol / Oficio: {profession}")

                lines.append("")

        lines.append("Datos:")

        if isinstance(data, dict) and data:
            shown_keys = set()

            for key, value in data.items():
                if self.should_skip_data_key(key, shown_keys):
                    continue

                display_key = self.display_data_key(key)
                formatted_value = self.format_complex_value(key, value)

                lines.append(f"- {display_key}: {formatted_value}")
        else:
            lines.append("- Sin datos registrados")

        effects = entity.get("effects", {})

        if isinstance(effects, dict) and effects:
            lines.append("")
            lines.append("Efectos:")

            for key, value in sorted(effects.items()):
                sign = "+" if value >= 0 else ""
                lines.append(f"- {display_stat(key)}: {sign}{value}")

        lines.append("")
        lines.append("Relaciones:")

        related = self.get_entity_relations(entity_id)

        if related:
            for relation in related:
                source = relation.get("source", {})
                target = relation.get("target", {})
                relation_type = relation.get("relation_type", "relación")

                if source.get("id") == entity_id:
                    objective = target.get("name", "Destino")
                    lines.append(
                        f"- {entity.get('name')} → {relation_type} → {objective}"
                    )
                else:
                    objective = source.get("name", "Origen")
                    lines.append(
                        f"- {objective} → {relation_type} → {entity.get('name')}"
                    )
        else:
            lines.append("- Sin relaciones")

        return "\n".join(lines)

    def get_entity_relations(self, entity_id):
        found = []

        for relation in self.relations:
            source_id = relation.get("source", {}).get("id")
            target_id = relation.get("target", {}).get("id")

            if source_id == entity_id or target_id == entity_id:
                found.append(relation)

        return found

    def color_for_type(self, entity_type):
        colors = {
            "npcs": QColor("#A8DADC"),
            "npc": QColor("#A8DADC"),
            "locations": QColor("#B7E4C7"),
            "location": QColor("#B7E4C7"),
            "cities": QColor("#B7E4C7"),
            "kingdoms": QColor("#CDB4DB"),
            "factions": QColor("#FFC8DD"),
            "gods": QColor("#F4D35E"),
            "creatures": QColor("#FFADAD"),
            "armies": QColor("#BDB2FF"),
            "items": QColor("#D9D9D9"),
            "loot": QColor("#E9C46A"),
            "weapons": QColor("#FFB4A2"),
            "armors": QColor("#BDE0FE"),
            "relics": QColor("#D9D9D9"),
            "magic_systems": QColor("#B8C0FF"),
            "spells": QColor("#D0BFFF"),
            "spell": QColor("#D0BFFF"),
            "foods": QColor("#CAFFBF")
        }

        return colors.get(
            entity_type,
            QColor("#E5E5E5")
        )
    

    def should_skip_data_key(self, key, shown_keys):
        normalized = str(key).lower().strip()

        gender_keys = {
            "genero",
            "género",
            "gender"
        }

        if normalized in gender_keys:
            return True

        return False


    def display_data_key(self, key):
        corrections = {
            "Razgo Dominante": "Rasgo Dominante",
            "Genero": "Género",
            "gender": "Género"
        }

        return corrections.get(key, key)


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