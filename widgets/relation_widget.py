from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QLineEdit
)

from services.relation_service import (
    load_relations,
    create_relation,
    update_relation,
    delete_relation,
    ensure_relation_ids
)

from core.system_log import add_system_log
from core.parser import load_all_lists
from services.entity_registry_service import load_registry_entities
from utils.ui_helpers import sort_combobox


class RelationWidget(QWidget):

    DEFAULT_RELATIONS = [
        "posee",
        "equipa",
        "usa",
        "conoce",
        "vive en",
        "sirve a",
        "lidera",
        "aliado con",
        "enemigo de"
    ]

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []

        self.relations = []
        self.selected_relation_id = None

        ensure_relation_ids()

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🔗 Crear relación entre entidades"))

        # =========================
        # Origen
        # =========================

        source_type_layout = QHBoxLayout()

        source_type_layout.addWidget(QLabel("Tipo origen:"))

        self.source_type_combo = QComboBox()
        source_type_layout.addWidget(self.source_type_combo)

        source_type_layout.addWidget(QLabel("Buscar origen:"))

        self.source_search = QLineEdit()
        self.source_search.setPlaceholderText("Nombre...")
        source_type_layout.addWidget(self.source_search)

        layout.addLayout(source_type_layout)

        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Origen:"))

        self.source_combo = QComboBox()
        source_layout.addWidget(self.source_combo)

        layout.addLayout(source_layout)

        # =========================
        # Relación
        # =========================

        relation_layout = QHBoxLayout()
        relation_layout.addWidget(QLabel("Relación:"))

        self.relation_combo = QComboBox()
        self.relation_combo.setEditable(True)

        relation_layout.addWidget(self.relation_combo)
        layout.addLayout(relation_layout)

        # =========================
        # Destino
        # =========================

        target_type_layout = QHBoxLayout()

        target_type_layout.addWidget(QLabel("Tipo destino:"))

        self.target_type_combo = QComboBox()
        target_type_layout.addWidget(self.target_type_combo)

        target_type_layout.addWidget(QLabel("Buscar destino:"))

        self.target_search = QLineEdit()
        self.target_search.setPlaceholderText("Nombre...")
        target_type_layout.addWidget(self.target_search)

        layout.addLayout(target_type_layout)

        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Destino:"))

        self.target_combo = QComboBox()
        target_layout.addWidget(self.target_combo)

        layout.addLayout(target_layout)

        # =========================
        # Notas
        # =========================

        layout.addWidget(QLabel("Notas:"))

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(90)

        layout.addWidget(self.notes_input)

        # =========================
        # Botones
        # =========================

        buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("Refrescar entidades")
        self.save_btn = QPushButton("Guardar relación")

        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        # =========================
        # Relaciones existentes
        # =========================

        layout.addWidget(QLabel("Relaciones registradas:"))

        self.relation_list = QComboBox()
        layout.addWidget(self.relation_list)

        relation_buttons = QHBoxLayout()

        self.load_relation_btn = QPushButton("Cargar relación")
        self.update_relation_btn = QPushButton("Actualizar relación")
        self.delete_relation_btn = QPushButton("Borrar relación")
        self.clear_selection_btn = QPushButton("Nueva relación")

        relation_buttons.addWidget(self.load_relation_btn)
        relation_buttons.addWidget(self.update_relation_btn)
        relation_buttons.addWidget(self.delete_relation_btn)
        relation_buttons.addWidget(self.clear_selection_btn)

        layout.addLayout(relation_buttons)

        self.result = QTextEdit()
        self.result.setReadOnly(True)

        layout.addWidget(self.result)

        # =========================
        # Eventos
        # =========================

        self.refresh_btn.clicked.connect(self.refresh_all)
        self.save_btn.clicked.connect(self.save_current_relation)
        self.load_relation_btn.clicked.connect(self.load_selected_relation_for_edit)
        self.update_relation_btn.clicked.connect(self.update_current_relation)
        self.delete_relation_btn.clicked.connect(self.delete_current_relation)
        self.clear_selection_btn.clicked.connect(self.clear_relation_selection)

        self.source_type_combo.currentIndexChanged.connect(
            self.populate_source_combo
        )
        self.target_type_combo.currentIndexChanged.connect(
            self.populate_target_combo
        )
        self.source_search.textChanged.connect(
            self.populate_source_combo
        )
        self.target_search.textChanged.connect(
            self.populate_target_combo
        )

        self.refresh_all()

    # =====================================
    # Refresh general
    # =====================================

    def refresh_all(self):
        self.entities = load_registry_entities()

        self.load_relation_types()
        self.populate_type_filters()
        self.populate_source_combo()
        self.populate_target_combo()
        self.load_existing_relations()

        add_system_log(
            self.history,
            f"🔄 Relaciones: {len(self.entities)} entidades cargadas"
        )

    # =====================================
    # Tipos de relación
    # =====================================

    def load_relation_types(self):
        relation_types = []

        for oracle in load_all_lists():
            if oracle["name"] == "Relaciones-Tipos":
                data = oracle.get("data", {})

                if "Resultados" in data:
                    relation_types = [
                        item[0]
                        for item in data["Resultados"]
                    ]
                else:
                    for values in data.values():
                        relation_types.extend(
                            item[0]
                            for item in values
                        )

                break

        if not relation_types:
            relation_types = self.DEFAULT_RELATIONS

        relation_types = sorted(
            set(relation_types),
            key=str.lower
        )

        current = self.relation_combo.currentText()

        self.relation_combo.clear()
        self.relation_combo.addItems(relation_types)
        sort_combobox(self.relation_combo)

        if current:
            index = self.relation_combo.findText(current)
            if index >= 0:
                self.relation_combo.setCurrentIndex(index)

    # =====================================
    # Filtros por tipo
    # =====================================

    def populate_type_filters(self):
        types = sorted({
            entity.get("type", "entity")
            for entity in self.entities
        })

        current_source_type = self.source_type_combo.currentData()
        current_target_type = self.target_type_combo.currentData()

        self.source_type_combo.blockSignals(True)
        self.target_type_combo.blockSignals(True)

        self.source_type_combo.clear()
        self.target_type_combo.clear()

        self.source_type_combo.addItem("Todos", None)
        self.target_type_combo.addItem("Todos", None)

        for entity_type in types:
            self.source_type_combo.addItem(entity_type, entity_type)
            self.target_type_combo.addItem(entity_type, entity_type)

        sort_combobox(self.source_type_combo)
        sort_combobox(self.target_type_combo)


        self.source_type_combo.blockSignals(False)
        self.target_type_combo.blockSignals(False)

        if current_source_type:
            index = self.source_type_combo.findData(current_source_type)
            if index >= 0:
                self.source_type_combo.setCurrentIndex(index)

        if current_target_type:
            index = self.target_type_combo.findData(current_target_type)
            if index >= 0:
                self.target_type_combo.setCurrentIndex(index)

    # =====================================
    # Poblar combos filtrados
    # =====================================

    def populate_source_combo(self):
        self.populate_entity_combo(
            combo=self.source_combo,
            selected_type=self.source_type_combo.currentData(),
            search_text=self.source_search.text()
        )

    def populate_target_combo(self):
        self.populate_entity_combo(
            combo=self.target_combo,
            selected_type=self.target_type_combo.currentData(),
            search_text=self.target_search.text()
        )

    def populate_entity_combo(self, combo, selected_type, search_text):
        current_id = None

        if combo.currentData():
            current_id = combo.currentData().get("id")

        search_text = search_text.lower().strip()

        filtered = []

        for entity in self.entities:
            if selected_type and entity.get("type") != selected_type:
                continue

            name = entity.get("name", "")

            if search_text and search_text not in name.lower():
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
                self.format_entity_label(entity),
                entity
            )
        
        sort_combobox(combo)
        combo.blockSignals(False)

        if current_id:
            for i in range(combo.count()):
                entity = combo.itemData(i)

                if entity and entity.get("id") == current_id:
                    combo.setCurrentIndex(i)
                    break

    # =====================================
    # Formato
    # =====================================

    def format_entity_label(self, entity):
        entity_id = entity.get("id", "sin_id")
        name = entity.get("name", "Sin nombre")
        entity_type = entity.get("type", "entity")

        return f"{name} [{entity_type}] ({entity_id})"

    # =====================================
    # Guardar relación
    # =====================================

    def save_current_relation(self):
        source = self.source_combo.currentData()
        target = self.target_combo.currentData()

        if not source or not target:
            self.result.append("⚠ Necesitas origen y destino.")
            return

        if source.get("id") == target.get("id"):
            self.result.append(
                "⚠ Origen y destino no pueden ser la misma entidad."
            )
            return

        relation_type = self.relation_combo.currentText().strip()

        if not relation_type:
            self.result.append(
                "⚠ Escribe o selecciona un tipo de relación."
            )
            return

        notes = self.notes_input.toPlainText().strip()

        relation = create_relation(
            source={
                "id": source.get("id"),
                "name": source.get("name"),
                "type": source.get("type")
            },
            relation_type=relation_type,
            target={
                "id": target.get("id"),
                "name": target.get("name"),
                "type": target.get("type")
            },
            notes=notes
        )

        text = (
            f"🔗 {relation['source']['name']} "
            f"→ {relation['relation_type']} → "
            f"{relation['target']['name']}"
        )

        self.result.append(text)

        add_system_log(
            self.history,
            text
        )

        self.notes_input.clear()
        self.load_existing_relations()

    # =====================================
    # Relaciones existentes
    # =====================================

    def load_existing_relations(self):
        self.result.clear()
        self.relation_list.blockSignals(True)
        self.relation_list.clear()

        self.relations = ensure_relation_ids()

        if not self.relations:
            self.relation_list.addItem("No hay relaciones registradas", None)
            self.result.append("No hay relaciones registradas todavía.")
            self.relation_list.blockSignals(False)
            return

        self.relations = sorted(
            self.relations,
            key=lambda r: (
                r.get("source", {}).get("name", ""),
                r.get("relation_type", ""),
                r.get("target", {}).get("name", "")
            )
        )

        for relation in self.relations:
            relation_id = relation.get("id", "-")
            source = relation.get("source", {}).get("name", "Origen")
            relation_type = relation.get("relation_type", "relación")
            target = relation.get("target", {}).get("name", "Destino")

            label = (
                f"{source} → {relation_type} → {target} "
                f"[{relation_id}]"
            )

            self.relation_list.addItem(label, relation_id)

            self.result.append(f"🔗 {label}")

        self.relation_list.blockSignals(False)
    
    def get_relation_by_id(self, relation_id):
        if not relation_id:
            return None

        for relation in self.relations:
            if relation.get("id") == relation_id:
                return relation

        return None


    def find_entity_by_id(self, entity_id):
        for entity in self.entities:
            if entity.get("id") == entity_id:
                return entity

        return None


    def set_combo_entity_by_id(self, combo, entity_id):
        for index in range(combo.count()):
            entity = combo.itemData(index)

            if entity and entity.get("id") == entity_id:
                combo.setCurrentIndex(index)
                return True

        return False


    def load_selected_relation_for_edit(self):
        relation_id = self.relation_list.currentData()
        relation = self.get_relation_by_id(relation_id)

        if not relation:
            self.result.append("⚠ Selecciona una relación válida.")
            return

        self.selected_relation_id = relation_id

        source = relation.get("source", {})
        target = relation.get("target", {})

        source_type = source.get("type")
        target_type = target.get("type")

        if source_type:
            index = self.source_type_combo.findData(source_type)
            if index >= 0:
                self.source_type_combo.setCurrentIndex(index)

        if target_type:
            index = self.target_type_combo.findData(target_type)
            if index >= 0:
                self.target_type_combo.setCurrentIndex(index)

        self.source_search.clear()
        self.target_search.clear()

        self.populate_source_combo()
        self.populate_target_combo()

        self.set_combo_entity_by_id(
            self.source_combo,
            source.get("id")
        )

        self.set_combo_entity_by_id(
            self.target_combo,
            target.get("id")
        )

        self.relation_combo.setCurrentText(
            relation.get("relation_type", "")
        )

        self.notes_input.setText(
            relation.get("notes", "")
        )

        self.result.append(
            f"✏ Relación cargada para edición: {relation_id}"
        )


    def update_current_relation(self):
        if not self.selected_relation_id:
            self.result.append(
                "⚠ Primero carga una relación para editar."
            )
            return

        source = self.source_combo.currentData()
        target = self.target_combo.currentData()

        if not source or not target:
            self.result.append("⚠ Necesitas origen y destino.")
            return

        if source.get("id") == target.get("id"):
            self.result.append(
                "⚠ Origen y destino no pueden ser la misma entidad."
            )
            return

        relation_type = self.relation_combo.currentText().strip()

        if not relation_type:
            self.result.append(
                "⚠ Escribe o selecciona un tipo de relación."
            )
            return

        notes = self.notes_input.toPlainText().strip()

        ok = update_relation(
            relation_id=self.selected_relation_id,
            source={
                "id": source.get("id"),
                "name": source.get("name"),
                "type": source.get("type")
            },
            relation_type=relation_type,
            target={
                "id": target.get("id"),
                "name": target.get("name"),
                "type": target.get("type")
            },
            notes=notes
        )

        if not ok:
            self.result.append("❌ No se pudo actualizar la relación.")
            return

        text = (
            f"✏ Relación actualizada → "
            f"{source.get('name')} → {relation_type} → {target.get('name')}"
        )

        add_system_log(self.history, text)

        self.result.append(text)
        self.clear_relation_selection()
        self.load_existing_relations()


    def delete_current_relation(self):
        relation_id = self.relation_list.currentData()

        if not relation_id:
            self.result.append("⚠ Selecciona una relación para borrar.")
            return

        relation = self.get_relation_by_id(relation_id)

        if not relation:
            self.result.append("⚠ Relación no encontrada.")
            return

        ok = delete_relation(relation_id)

        if not ok:
            self.result.append("❌ No se pudo borrar la relación.")
            return

        source = relation.get("source", {}).get("name", "Origen")
        relation_type = relation.get("relation_type", "relación")
        target = relation.get("target", {}).get("name", "Destino")

        text = (
            f"🗑 Relación borrada → "
            f"{source} → {relation_type} → {target}"
        )

        add_system_log(self.history, text)

        self.result.append(text)
        self.clear_relation_selection()
        self.load_existing_relations()


    def clear_relation_selection(self):
        self.selected_relation_id = None
        self.notes_input.clear()

        self.source_search.clear()
        self.target_search.clear()

        if self.source_type_combo.count() > 0:
            self.source_type_combo.setCurrentIndex(0)

        if self.target_type_combo.count() > 0:
            self.target_type_combo.setCurrentIndex(0)

        self.populate_source_combo()
        self.populate_target_combo()

        self.result.append("🆕 Modo nueva relación activado.")