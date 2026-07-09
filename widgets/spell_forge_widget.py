import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QMessageBox, QCheckBox, QListWidget,
    QListWidgetItem, QGroupBox, QTabWidget, QLineEdit,
    QApplication, QSplitter, QScrollArea
)

from PySide6.QtCore import Qt

from services.spell_component_service import (
    load_component,
    generate_modular_spell,
    format_spell_for_display
)

from core.system_log import add_system_log


GENERATED_SPELLS_PATH = "entities/generated_spells.json"


class SpellForgeWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.current_spell = None
        self.saved_spells = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_tab = QWidget()
        self.library_tab = QWidget()

        self.tabs.addTab(self.create_tab, "🜂 Crear técnica")
        self.tabs.addTab(self.library_tab, "📚 Biblioteca")

        self.setup_create_tab()
        self.setup_library_tab()

        self.load_library()

    # =========================
    # Crear técnica
    # =========================

    def setup_create_tab(self):
        layout = QVBoxLayout()
        self.create_tab.setLayout(layout)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # =========================
        # Panel izquierdo con scroll
        # =========================

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(420)

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        left_scroll.setWidget(left_panel)

        splitter.addWidget(left_scroll)

        title = QLabel("🜂 Forja de Técnicas / Hechizos")
        left_layout.addWidget(title)

        # =========================
        # Opciones
        # =========================

        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        blueprint_layout = QHBoxLayout()
        blueprint_layout.addWidget(QLabel("Tipo:"))

        self.blueprint_combo = QComboBox()
        self.load_blueprints()
        blueprint_layout.addWidget(self.blueprint_combo)

        options_layout.addLayout(blueprint_layout)

        self.include_effects_checkbox = QCheckBox("Efectos mecánicos")
        self.include_effects_checkbox.setChecked(True)

        self.include_intentions_checkbox = QCheckBox("Intención")
        self.include_intentions_checkbox.setChecked(True)

        self.include_modifiers_checkbox = QCheckBox("Modificadores")
        self.include_modifiers_checkbox.setChecked(True)

        self.include_costs_checkbox = QCheckBox("Costos")
        self.include_costs_checkbox.setChecked(True)

        self.include_limitations_checkbox = QCheckBox("Limitaciones")
        self.include_limitations_checkbox.setChecked(True)

        self.include_manifestation_checkbox = QCheckBox("Manifestación")
        self.include_manifestation_checkbox.setChecked(True)

        self.include_side_effects_checkbox = QCheckBox("Efectos secundarios")
        self.include_side_effects_checkbox.setChecked(True)

        self.allow_dangerous_checkbox = QCheckBox("Componentes peligrosos")
        self.allow_dangerous_checkbox.setChecked(True)

        options_layout.addWidget(self.include_effects_checkbox)
        options_layout.addWidget(self.include_intentions_checkbox)
        options_layout.addWidget(self.include_modifiers_checkbox)
        options_layout.addWidget(self.include_costs_checkbox)
        options_layout.addWidget(self.include_limitations_checkbox)
        options_layout.addWidget(self.include_manifestation_checkbox)
        options_layout.addWidget(self.include_side_effects_checkbox)
        options_layout.addWidget(self.allow_dangerous_checkbox)

        left_layout.addWidget(options_group)

        # =========================
        # Componentes principales
        # =========================

        main_components = QGroupBox("Componentes principales")
        main_components_layout = QVBoxLayout()
        main_components.setLayout(main_components_layout)

        self.source_combo = self.create_component_combo("sources", "Fuente aleatoria")
        self.action_combo = self.create_component_combo("actions", "Acción aleatoria")
        self.target_combo = self.create_component_combo("targets", "Objetivo aleatorio")
        self.form_combo = self.create_component_combo("forms", "Forma aleatoria")
        self.manifestation_combo = self.create_component_combo(
            "manifestations",
            "Manifestación aleatoria"
        )

        main_components_layout.addWidget(QLabel("Fuente:"))
        main_components_layout.addWidget(self.source_combo)

        main_components_layout.addWidget(QLabel("Acción:"))
        main_components_layout.addWidget(self.action_combo)

        main_components_layout.addWidget(QLabel("Objetivo:"))
        main_components_layout.addWidget(self.target_combo)

        main_components_layout.addWidget(QLabel("Forma:"))
        main_components_layout.addWidget(self.form_combo)

        main_components_layout.addWidget(QLabel("Manifestación:"))
        main_components_layout.addWidget(self.manifestation_combo)

        left_layout.addWidget(main_components)

        # =========================
        # Componentes opcionales en pestañas
        # =========================

        optional_tabs = QTabWidget()

        self.intentions_list = self.create_component_list("intentions")
        self.modifiers_list = self.create_component_list("modifiers")
        self.costs_list = self.create_component_list("costs")
        self.limitations_list = self.create_component_list("limitations")
        self.side_effects_list = self.create_component_list("side_effects")

        optional_tabs.addTab(
            self.build_list_box(self.intentions_list),
            "Intenciones"
        )
        optional_tabs.addTab(
            self.build_list_box(self.modifiers_list),
            "Modificadores"
        )
        optional_tabs.addTab(
            self.build_list_box(self.costs_list),
            "Costos"
        )
        optional_tabs.addTab(
            self.build_list_box(self.limitations_list),
            "Limitaciones"
        )
        optional_tabs.addTab(
            self.build_list_box(self.side_effects_list),
            "Efectos secundarios"
        )

        left_layout.addWidget(optional_tabs)

        # =========================
        # Botones
        # =========================

        self.generate_btn = QPushButton("Generar técnica")
        self.save_btn = QPushButton("Guardar en biblioteca")
        self.clear_btn = QPushButton("Limpiar")

        left_layout.addWidget(self.generate_btn)
        left_layout.addWidget(self.save_btn)
        left_layout.addWidget(self.clear_btn)

        left_layout.addStretch()

        # =========================
        # Panel derecho: resultado siempre visible
        # =========================

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Nombre:"))

        self.spell_name_input = QLineEdit()
        self.spell_name_input.setPlaceholderText("Si lo dejas vacío, se usa el nombre generado")
        name_layout.addWidget(self.spell_name_input)

        right_layout.addLayout(name_layout)

        right_layout.addWidget(QLabel("Resultado generado:"))

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setMinimumWidth(520)

        right_layout.addWidget(self.result)

        splitter.addWidget(right_panel)

        splitter.setSizes([440, 850])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.generate_btn.clicked.connect(self.generate_spell)
        self.save_btn.clicked.connect(self.save_spell)
        self.clear_btn.clicked.connect(self.clear_result)

    # =========================
    # Biblioteca
    # =========================

    def setup_library_tab(self):
        layout = QVBoxLayout()
        self.library_tab.setLayout(layout)

        layout.addWidget(QLabel("📚 Biblioteca de Técnicas / Hechizos Generados"))

        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Buscar:"))

        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText(
            "Buscar por nombre, descripción, componente o tag..."
        )

        self.refresh_library_btn = QPushButton("Refrescar")

        search_layout.addWidget(self.library_search)
        search_layout.addWidget(self.refresh_library_btn)

        layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.library_list = QListWidget()
        splitter.addWidget(self.library_list)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.library_detail = QTextEdit()
        self.library_detail.setReadOnly(True)
        right_layout.addWidget(self.library_detail)

        buttons = QHBoxLayout()

        self.use_as_current_btn = QPushButton("Usar como actual")
        self.copy_description_btn = QPushButton("Copiar descripción")
        self.delete_spell_btn = QPushButton("Eliminar")

        buttons.addWidget(self.use_as_current_btn)
        buttons.addWidget(self.copy_description_btn)
        buttons.addWidget(self.delete_spell_btn)

        right_layout.addLayout(buttons)

        splitter.addWidget(right_panel)
        splitter.setSizes([360, 900])

        self.library_search.textChanged.connect(self.populate_library_list)
        self.refresh_library_btn.clicked.connect(self.load_library)
        self.library_list.currentRowChanged.connect(self.show_selected_spell)
        self.delete_spell_btn.clicked.connect(self.delete_selected_spell)
        self.copy_description_btn.clicked.connect(self.copy_selected_description)
        self.use_as_current_btn.clicked.connect(self.use_selected_as_current)

    # =========================
    # Carga de datos UI
    # =========================

    def load_blueprints(self):
        self.blueprint_combo.clear()

        blueprints = load_component("blueprints")

        if not blueprints:
            self.blueprint_combo.addItem("Técnica libre", None)
            return

        self.blueprint_combo.addItem("Tipo aleatorio", None)

        for blueprint in blueprints:
            self.blueprint_combo.addItem(
                blueprint.get("name", "Sin nombre"),
                blueprint.get("id")
            )

    def create_component_combo(self, component_type, random_label):
        combo = QComboBox()
        combo.addItem(random_label, None)

        for item in load_component(component_type):
            label = item.get("name", "Sin nombre")
            risk = item.get("risk", 0)

            if risk:
                label = f"{label} | Riesgo {risk}"

            combo.addItem(label, item.get("id"))

        return combo

    def create_component_list(self, component_type):
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        list_widget.setMinimumHeight(220)

        for item in load_component(component_type):
            label = item.get("name", "Sin nombre")
            risk = item.get("risk", 0)

            if risk:
                label = f"{label} | Riesgo {risk}"

            list_item = QListWidgetItem(label)
            list_item.setData(256, item.get("id"))
            list_widget.addItem(list_item)

        return list_widget

    def build_list_box(self, list_widget):
        box = QWidget()
        layout = QVBoxLayout()
        box.setLayout(layout)

        layout.addWidget(
            QLabel("Selecciona 0 o más. Si no eliges nada, será aleatorio.")
        )
        layout.addWidget(list_widget)

        return box

    # =========================
    # Selección
    # =========================

    def get_selected_ids_from_list(self, list_widget):
        return [
            item.data(256)
            for item in list_widget.selectedItems()
            if item.data(256)
        ]

    def get_selected_components(self):
        return {
            "source": self.source_combo.currentData(),
            "action": self.action_combo.currentData(),
            "target": self.target_combo.currentData(),
            "form": self.form_combo.currentData(),
            "manifestation": self.manifestation_combo.currentData(),
            "intentions": self.get_selected_ids_from_list(self.intentions_list),
            "modifiers": self.get_selected_ids_from_list(self.modifiers_list),
            "costs": self.get_selected_ids_from_list(self.costs_list),
            "limitations": self.get_selected_ids_from_list(self.limitations_list),
            "side_effects": self.get_selected_ids_from_list(self.side_effects_list)
        }

    # =========================
    # Acciones crear
    # =========================

    def generate_spell(self):
        self.current_spell = generate_modular_spell(
            blueprint_id=self.blueprint_combo.currentData(),
            include_effects=self.include_effects_checkbox.isChecked(),
            include_intentions=self.include_intentions_checkbox.isChecked(),
            include_modifiers=self.include_modifiers_checkbox.isChecked(),
            include_costs=self.include_costs_checkbox.isChecked(),
            include_limitations=self.include_limitations_checkbox.isChecked(),
            include_manifestation=self.include_manifestation_checkbox.isChecked(),
            include_side_effects=self.include_side_effects_checkbox.isChecked(),
            allow_dangerous=self.allow_dangerous_checkbox.isChecked(),
            selected_components=self.get_selected_components()
        )

        self.spell_name_input.setText(
            self.current_spell.get("name", "")
        )

        self.result.setPlainText(
            format_spell_for_display(self.current_spell)
        )

        add_system_log(
            self.history,
            f"🜂 Técnica generada → {self.current_spell.get('name')}"
        )

    def save_spell(self):
        if not self.current_spell:
            QMessageBox.warning(
                self,
                "Sin técnica",
                "Primero genera una técnica."
            )
            return
        
        custom_name = self.spell_name_input.text().strip()

        if custom_name:
            self.current_spell["name"] = custom_name

        spells = self.read_saved_spells()
        spells.append(self.current_spell)

        self.write_saved_spells(spells)
        self.load_library()

        QMessageBox.information(
            self,
            "Guardado",
            "Técnica guardada correctamente."
        )

    def clear_result(self):
        self.current_spell = None
        self.spell_name_input.clear()
        self.result.clear()

    # =========================
    # Biblioteca
    # =========================

    def read_saved_spells(self):
        if not os.path.exists(GENERATED_SPELLS_PATH):
            return []

        with open(GENERATED_SPELLS_PATH, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except Exception:
                return []

        return data if isinstance(data, list) else []

    def write_saved_spells(self, spells):
        os.makedirs("entities", exist_ok=True)

        with open(GENERATED_SPELLS_PATH, "w", encoding="utf-8") as file:
            json.dump(spells, file, indent=4, ensure_ascii=False)

    def load_library(self):
        self.saved_spells = self.read_saved_spells()
        self.populate_library_list()

    def populate_library_list(self):
        search = self.library_search.text().lower().strip()

        self.library_list.blockSignals(True)
        self.library_list.clear()

        for index, spell in enumerate(self.saved_spells):
            searchable = json.dumps(spell, ensure_ascii=False).lower()

            if search and search not in searchable:
                continue

            name = spell.get("name", "Sin nombre")
            risk = spell.get("risk", 0)
            blueprint = spell.get("blueprint", {}).get("name", "Libre")

            item = QListWidgetItem(
                f"{name} | {blueprint} | Riesgo {risk}"
            )
            item.setData(256, index)
            self.library_list.addItem(item)

        self.library_list.blockSignals(False)

        if self.library_list.count() > 0:
            self.library_list.setCurrentRow(0)
        else:
            self.library_detail.clear()

    def get_selected_library_spell(self):
        item = self.library_list.currentItem()

        if not item:
            return None, None

        index = item.data(256)

        if index is None:
            return None, None

        if index < 0 or index >= len(self.saved_spells):
            return None, None

        return self.saved_spells[index], index

    def show_selected_spell(self):
        spell, _index = self.get_selected_library_spell()

        if not spell:
            self.library_detail.clear()
            return

        self.library_detail.setPlainText(
            format_spell_for_display(spell)
        )

    def delete_selected_spell(self):
        spell, index = self.get_selected_library_spell()

        if not spell:
            return

        confirm = QMessageBox.question(
            self,
            "Eliminar técnica",
            f"¿Eliminar '{spell.get('name', 'Sin nombre')}'?"
        )

        if confirm != QMessageBox.Yes:
            return

        del self.saved_spells[index]
        self.write_saved_spells(self.saved_spells)
        self.populate_library_list()

    def copy_selected_description(self):
        spell, _index = self.get_selected_library_spell()

        if not spell:
            return

        QApplication.clipboard().setText(
            spell.get("description", "")
        )

        QMessageBox.information(
            self,
            "Copiado",
            "Descripción copiada al portapapeles."
        )

    def use_selected_as_current(self):
        spell, _index = self.get_selected_library_spell()

        if not spell:
            return

        self.current_spell = spell
        self.tabs.setCurrentWidget(self.create_tab)

        self.spell_name_input.setText(
            spell.get("name", "")
        )

        self.result.setPlainText(
            format_spell_for_display(spell)
        )