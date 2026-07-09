from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QLineEdit
)

from PySide6.QtCore import Qt
from utils.ui_helpers import sort_combobox

from services.entity_registry_service import (
    load_registry_entities
)
from core.display_names import display_entity_type
from services.relation_service import (
    create_relation,
    delete_relation,
    get_outgoing_relations,
    ensure_relation_ids
)

from services.equipment_service import (
    ensure_default_items,
    EQUIPMENT_RELATIONS
)

from core.system_log import add_system_log


EQUIPMENT_TYPES = {
    "weapons",
    "armors",
    "relics",
    "items",
    "spells"
}


OWNER_TYPES = {
    "npcs",
    "npc",
    "creatures",
    "creature",
    "factions",
    "armies",
    "kingdoms"
}


class EquipmentWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget

        self.entities = []
        self.owners = []
        self.equipment = []

        ensure_default_items()
        ensure_relation_ids()

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🎒 Equipamiento"))

        # =====================================
        # Entidad
        # =====================================

        owner_filter_layout = QHBoxLayout()

        owner_filter_layout.addWidget(QLabel("Tipo entidad:"))

        self.owner_type_combo = QComboBox()
        owner_filter_layout.addWidget(self.owner_type_combo)

        owner_filter_layout.addWidget(QLabel("Buscar:"))

        self.owner_search = QLineEdit()
        self.owner_search.setPlaceholderText("Nombre...")
        owner_filter_layout.addWidget(self.owner_search)

        layout.addLayout(owner_filter_layout)

        owner_layout = QHBoxLayout()

        owner_layout.addWidget(QLabel("Entidad:"))

        self.owner_combo = QComboBox()
        owner_layout.addWidget(self.owner_combo)

        self.refresh_btn = QPushButton("Refrescar")
        owner_layout.addWidget(self.refresh_btn)

        layout.addLayout(owner_layout)

        # =====================================
        # Equipo
        # =====================================

        equipment_filter_layout = QHBoxLayout()

        equipment_filter_layout.addWidget(QLabel("Tipo equipo:"))

        self.equipment_type_combo = QComboBox()
        equipment_filter_layout.addWidget(self.equipment_type_combo)

        equipment_filter_layout.addWidget(QLabel("Buscar:"))

        self.equipment_search = QLineEdit()
        self.equipment_search.setPlaceholderText("Nombre...")
        equipment_filter_layout.addWidget(self.equipment_search)

        layout.addLayout(equipment_filter_layout)

        equip_layout = QHBoxLayout()

        equip_layout.addWidget(QLabel("Relación:"))

        self.relation_combo = QComboBox()
        self.relation_combo.addItems(
            sorted(EQUIPMENT_RELATIONS)
        )

        sort_combobox(self.relation_combo)

        equip_layout.addWidget(self.relation_combo)

        equip_layout.addWidget(QLabel("Equipo:"))

        self.equipment_combo = QComboBox()
        equip_layout.addWidget(self.equipment_combo)

        self.assign_btn = QPushButton("Asignar")
        equip_layout.addWidget(self.assign_btn)

        layout.addLayout(equip_layout)

        # =====================================
        # Equipo actual
        # =====================================

        layout.addWidget(QLabel("Equipo actual:"))

        self.current_list = QListWidget()
        layout.addWidget(self.current_list)

        buttons = QHBoxLayout()

        self.remove_btn = QPushButton("Quitar seleccionado")
        self.details_btn = QPushButton("Ver detalles")

        buttons.addWidget(self.remove_btn)
        buttons.addWidget(self.details_btn)

        layout.addLayout(buttons)

        # =====================================
        # Resultado
        # =====================================

        self.result = QTextEdit()
        self.result.setReadOnly(True)

        layout.addWidget(self.result)

        # =====================================
        # Eventos
        # =====================================

        self.refresh_btn.clicked.connect(
            self.load_data
        )

        self.owner_combo.currentIndexChanged.connect(
            self.load_current_equipment
        )

        self.assign_btn.clicked.connect(
            self.assign_equipment
        )

        self.remove_btn.clicked.connect(
            self.remove_selected_equipment
        )

        self.details_btn.clicked.connect(
            self.show_selected_details
        )

        self.owner_type_combo.currentIndexChanged.connect(
            self.populate_owner_combo
        )

        self.owner_search.textChanged.connect(
            self.populate_owner_combo
        )

        self.equipment_type_combo.currentIndexChanged.connect(
            self.populate_equipment_combo
        )

        self.equipment_search.textChanged.connect(
            self.populate_equipment_combo
        )

        self.load_data()

    # =====================================
    # Datos
    # =====================================

    def load_data(self):

        self.entities = load_registry_entities()

        self.owners = [
            entity for entity in self.entities
            if entity.get("type") in OWNER_TYPES
        ]

        self.equipment = [
            entity for entity in self.entities
            if entity.get("type") in EQUIPMENT_TYPES
        ]

        self.populate_type_filters()

        self.populate_owner_combo()
        self.populate_equipment_combo()

        self.load_current_equipment()

        add_system_log(
            self.history,
            (
                "🎒 Equipamiento actualizado → "
                f"{len(self.owners)} entidades / "
                f"{len(self.equipment)} objetos"
            )
        )

    # =====================================
    # Filtros
    # =====================================

    def populate_type_filters(self):

        owner_types = sorted({
            entity.get("type")
            for entity in self.owners
        })

        equipment_types = sorted({
            entity.get("type")
            for entity in self.equipment
        })

        self.owner_type_combo.blockSignals(True)
        self.equipment_type_combo.blockSignals(True)

        self.owner_type_combo.clear()
        self.equipment_type_combo.clear()

        self.owner_type_combo.addItem("Todos", None)
        self.equipment_type_combo.addItem("Todos", None)

        for entity_type in owner_types:
            self.owner_type_combo.addItem(
                entity_type,
                entity_type
            )

        for entity_type in equipment_types:
            self.equipment_type_combo.addItem(
                entity_type,
                entity_type
            )
        sort_combobox(self.owner_type_combo)
        sort_combobox(self.equipment_type_combo)
        self.owner_type_combo.blockSignals(False)
        self.equipment_type_combo.blockSignals(False)

    # =====================================
    # Poblar combos
    # =====================================

    def populate_owner_combo(self):

        self.populate_combo(
            combo=self.owner_combo,
            entities=self.owners,
            selected_type=self.owner_type_combo.currentData(),
            search_text=self.owner_search.text()
        )

    def populate_equipment_combo(self):

        self.populate_combo(
            combo=self.equipment_combo,
            entities=self.equipment,
            selected_type=self.equipment_type_combo.currentData(),
            search_text=self.equipment_search.text()
        )

    def populate_combo(
        self,
        combo,
        entities,
        selected_type,
        search_text
    ):

        current_id = None

        if combo.currentData():
            current_id = combo.currentData().get("id")

        search_text = search_text.lower().strip()

        filtered = []

        for entity in entities:

            if (
                selected_type
                and entity.get("type") != selected_type
            ):
                continue

            name = entity.get("name", "")

            if (
                search_text
                and search_text not in name.lower()
            ):
                continue

            filtered.append(entity)

        filtered.sort(
            key=lambda e: (
                e.get("type", ""),
                e.get("name", "")
            )
        )

        combo.blockSignals(True)

        combo.clear()

        for entity in filtered:

            combo.addItem(
                self.format_entity(entity),
                entity
            )
        sort_combobox(combo)

        combo.blockSignals(False)

        if current_id:

            for i in range(combo.count()):

                entity = combo.itemData(i)

                if (
                    entity
                    and entity.get("id") == current_id
                ):
                    combo.setCurrentIndex(i)
                    break

    # =====================================
    # Formato
    # =====================================

    def format_entity(self, entity):

        return (
            f"{entity.get('name', 'Sin nombre')} "
            f"[{display_entity_type(entity.get('type', 'entity'))}] "
            f"({entity.get('id', '-')})"
        )

    # =====================================
    # Equipo actual
    # =====================================

    def load_current_equipment(self):

        self.current_list.clear()

        owner = self.owner_combo.currentData()

        if not owner:
            return

        owner_id = owner.get("id")

        relations = get_outgoing_relations(
            owner_id,
            relation_types=EQUIPMENT_RELATIONS
        )

        if not relations:

            item = QListWidgetItem(
                "Sin equipo registrado."
            )

            item.setData(Qt.UserRole, None)

            self.current_list.addItem(item)

            return

        for relation in relations:

            target = relation.get("target", {})

            relation_type = relation.get(
                "relation_type",
                ""
            )

            label = (
                f"{relation_type} → "
                f"{target.get('name', 'Sin nombre')} "
                f"[{target.get('type', 'entity')}]"
            )

            item = QListWidgetItem(label)

            item.setData(
                Qt.UserRole,
                relation
            )

            self.current_list.addItem(item)

    # =====================================
    # Asignar
    # =====================================

    def assign_equipment(self):

        owner = self.owner_combo.currentData()
        equipment = self.equipment_combo.currentData()

        if not owner or not equipment:
            self.result.append(
                "⚠ Selecciona entidad y equipo."
            )
            return

        relation_type = (
            self.relation_combo.currentText()
            .strip()
        )

        relation = create_relation(
            source={
                "id": owner.get("id"),
                "name": owner.get("name"),
                "type": owner.get("type")
            },
            relation_type=relation_type,
            target={
                "id": equipment.get("id"),
                "name": equipment.get("name"),
                "type": equipment.get("type")
            },
            notes="Asignado desde equipamiento."
        )

        self.result.append(
            (
                f"🎒 {owner.get('name')} "
                f"→ {relation_type} → "
                f"{equipment.get('name')}"
            )
        )

        self.load_current_equipment()

    # =====================================
    # Quitar
    # =====================================

    def remove_selected_equipment(self):

        item = self.current_list.currentItem()

        if not item:
            return

        relation = item.data(Qt.UserRole)

        if not relation:
            return

        relation_id = relation.get("id")

        ok = delete_relation(relation_id)

        if ok:

            self.result.append(
                f"🗑 Relación eliminada → {relation_id}"
            )

            self.load_current_equipment()

    # =====================================
    # Detalles
    # =====================================

    def show_selected_details(self):

        item = self.current_list.currentItem()

        if not item:
            return

        relation = item.data(Qt.UserRole)

        if not relation:
            return

        target_id = (
            relation.get("target", {})
            .get("id")
        )

        equipment = next(
            (
                entity for entity in self.equipment
                if entity.get("id") == target_id
            ),
            None
        )

        if not equipment:
            return

        data = equipment.get("data", {})
        effects = equipment.get("effects", {})

        lines = [
            "",
            "══════════════════════",
            f"🎒 {equipment.get('name')}",
            "══════════════════════",
            f"Tipo: {equipment.get('type')}",
            ""
        ]

        lines.append("Datos:")

        if data:

            for key, value in data.items():
                lines.append(f"- {key}: {value}")

        else:
            lines.append("- Sin datos")

        lines.append("")
        lines.append("Efectos:")

        if effects:

            for key, value in effects.items():
                lines.append(f"- {key}: {value}")

        else:
            lines.append("- Sin efectos")

        self.result.append("\n".join(lines))