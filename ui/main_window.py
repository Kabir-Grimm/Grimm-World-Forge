import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QLabel,
    QCheckBox,
    QComboBox,
    QSplitter,
    QMenu
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.config import CONFIG
from core.parser import load_all_lists
from core.favorites import load_favorites, save_favorites
from core.system_log import add_system_log
from core.display_names import display_ui

from ui.config_dialog import ConfigDialog

from widgets.multiroll_widget import MultiRollWidget
from widgets.oracle_widget import OracleWidget
from widgets.dice_widget import DiceWidget
from widgets.npc_widget import NPCWidget
from widgets.location_widget import LocationWidget
from widgets.relation_widget import RelationWidget
from widgets.relation_graph_widget import RelationGraphWidget
from widgets.entity_editor_widget import EntityEditorWidget
from widgets.world_widget import WorldWidget
from widgets.modular_entity_widget import ModularEntityWidget
from widgets.general_oracle_widget import GeneralOracleWidget
from widgets.simulation_widget import SimulationWidget
from widgets.echoes_widget import EchoesWidget
from widgets.encounter_widget import EncounterWidget
from widgets.equipment_widget import EquipmentWidget
from widgets.epic_battle_widget import EpicBattleWidget
from widgets.maintenance_widget import MaintenanceWidget
from widgets.loot_widget import LootWidget
from widgets.spell_forge_widget import SpellForgeWidget
from widgets.world_map_widget import WorldMapWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Grimm Worlds Forge")

        icon_path = os.path.join(
            "assets",
            "icons",
            "app_icon.ico"
        )

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(1400, 850)
        self.showMaximized()

        self.config = CONFIG

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # =========================
        # TOOLBAR SUPERIOR
        # =========================

        toolbar = QHBoxLayout()

        self.refresh_btn = QPushButton("Refrescar")
        self.export_btn = QPushButton("Exportar")
        self.config_btn = QPushButton("⚙ Config")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar...")

        self.audit_toggle = QCheckBox("Modo Tirada Importante 🔒")

        self.player_input = QLineEdit()
        self.player_input.setPlaceholderText("Jugador")

        self.context_input = QLineEdit()
        self.context_input.setPlaceholderText("Contexto")

        self.category_select = QComboBox()
        self.category_select.addItems([
            "Combate",
            "Generación",
            "Mundo"
        ])

        self.verify_btn = QPushButton("Verificar tirada")

        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.config_btn)

        toolbar.addStretch()

        toolbar.addWidget(self.audit_toggle)
        toolbar.addWidget(self.player_input)
        toolbar.addWidget(self.category_select)
        toolbar.addWidget(self.context_input)

        toolbar.addWidget(QLabel("Buscar:"))
        toolbar.addWidget(self.search)
        toolbar.addWidget(self.verify_btn)

        main_layout.addLayout(toolbar)

        # =========================
        # SPLITTER PRINCIPAL
        # =========================

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # =========================
        # MENÚ LATERAL
        # =========================

        self.oracle_list = QListWidget()
        self.oracle_list.setContextMenuPolicy(Qt.CustomContextMenu)

        self.oracle_list.setMinimumWidth(190)
        self.oracle_list.setMaximumWidth(240)

        splitter.addWidget(self.oracle_list)

        # =========================
        # PANEL DERECHO
        # =========================

        right_panel = QWidget()
        right_panel.setMinimumWidth(850)

        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        splitter.addWidget(right_panel)

        # =========================
        # SPLITTER VERTICAL
        # Tabs arriba / Historial abajo
        # =========================

        vertical_splitter = QSplitter(Qt.Vertical)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        vertical_splitter.addWidget(self.tabs)

        history_panel = QWidget()
        history_layout = QVBoxLayout()
        history_panel.setLayout(history_layout)

        history_layout.addWidget(QLabel("Historial"))

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setMinimumHeight(80)

        history_layout.addWidget(self.history)

        vertical_splitter.addWidget(history_panel)

        vertical_splitter.setSizes([520, 160])
        vertical_splitter.setStretchFactor(0, 5)
        vertical_splitter.setStretchFactor(1, 1)

        right_layout.addWidget(vertical_splitter)

        splitter.setSizes([220, 980])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 10)

        # =========================
        # DATOS INICIALES
        # =========================

        self.oracles = load_all_lists()
        self.favorites = load_favorites()

        self.load_default_oracles()
        self.setup_events()
        self.apply_main_style()

    # =========================
    # ESTILO
    # =========================

    def apply_main_style(self):
        style_path = os.path.join(
            "styles",
            "main_style.qss"
        )

        if not os.path.exists(style_path):
            return

        with open(style_path, "r", encoding="utf-8") as file:
            self.setStyleSheet(file.read())

    # =========================
    # MENÚ BASE
    # =========================

    def get_base_items(self):
        return [
            ("general_oracle", "🎲 Oráculo General"),
            ("dice", "🎲 Lanzar Dados"),
            ("multiroll", "🎲 Tirada Múltiple"),
            ("characters", display_ui("characters")),
            ("equipment", display_ui("equipment")),
            ("loot", "💎 Loot"),
            ("locations", display_ui("locations")),
            ("relations", display_ui("relations")),
            ("relation_graph", display_ui("relation_graph")),
            ("entity_editor", display_ui("entity_editor")),
            ("worlds", display_ui("worlds")),
            ("world_map", "🗺 Mapa de Mundo"),
            ("power_systems", display_ui("power_systems")),
            ("spell_forge", "🜂 Forja de Hechizos"),
            ("powers", display_ui("powers")),
            ("consumables", display_ui("consumables")),
            ("weapons", display_ui("weapons")),
            ("armors", display_ui("armors")),
            ("artifacts", display_ui("artifacts")),
            ("factions", display_ui("factions")),
            ("creatures", display_ui("creatures")),
            ("forces", display_ui("forces")),
            ("simulation", display_ui("simulation")),
            ("echoes", display_ui("echoes")),
            ("encounters", display_ui("encounters")),
            ("dramatic_battles", display_ui("dramatic_battles")),
            ("maintenance", "🧹 Mantenimiento")
        ]

    def load_default_oracles(self):
        self.oracle_list.clear()

        for key, label in self.get_base_items():
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.oracle_list.addItem(item)

        self.oracle_list.addItem("────────────")

        favorites = []
        normal = []

        for oracle in self.oracles:
            if oracle["name"] in self.favorites:
                favorites.append(oracle)
            else:
                normal.append(oracle)

        for oracle in favorites:
            self.oracle_list.addItem(f"⭐ {oracle['name']}")

        for oracle in normal:
            self.oracle_list.addItem(oracle["name"])

    # =========================
    # EVENTOS
    # =========================

    def setup_events(self):
        self.oracle_list.itemClicked.connect(self.open_tab)
        self.verify_btn.clicked.connect(self.verify_last_roll)
        self.config_btn.clicked.connect(self.open_config)
        self.search.textChanged.connect(self.filter_oracles)
        self.oracle_list.customContextMenuRequested.connect(
            self.show_context_menu
        )

    def open_config(self):
        dialog = ConfigDialog(self.config)

        if dialog.exec():
            self.config = dialog.config
            self.load_default_oracles()
            self.history.append("⚙ Configuración actualizada")

    # =========================
    # TABS
    # =========================

    def open_tab(self, item):
        key = item.data(Qt.UserRole)
        name = item.text().replace("⭐ ", "")

        if "────" in name:
            return

        tab_id = key if key else name

        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
                self.tabs.setCurrentIndex(i)
                return

        tab = self.create_tab_by_key(tab_id)

        if not tab:
            return

        self.tabs.addTab(tab, name)
        self.tabs.setCurrentWidget(tab)

        add_system_log(
            self.history,
            f"📂 Herramienta abierta → {name}"
        )

    def close_tab(self, index):
        name = self.tabs.tabText(index)

        protected = [
            "🎲 Lanzar Dados"
        ]

        if name in protected:
            return

        self.tabs.removeTab(index)

    def create_tab_by_key(self, key):
        if key == "general_oracle":
            return GeneralOracleWidget(self.history)

        if key == "dice":
            return DiceWidget(
                self.config,
                self.history,
                self.audit_toggle,
                self.player_input,
                self.category_select,
                self.context_input
            )

        if key == "multiroll":
            return MultiRollWidget(
                self.oracles,
                self.history
            )

        if key == "characters":
            return NPCWidget(self.history)

        if key == "equipment":
            return EquipmentWidget(self.history)

        if key == "loot":
            return LootWidget(self.history)

        if key == "locations":
            return LocationWidget(self.history)

        if key == "relations":
            return RelationWidget(self.history)

        if key == "relation_graph":
            return RelationGraphWidget(self.history)

        if key == "entity_editor":
            return EntityEditorWidget(self.history)

        if key == "worlds":
            return WorldWidget(self.history)
        
        if key == "world_map":
            return WorldMapWidget(self.history)

        if key == "power_systems":
            return ModularEntityWidget(
                self.history,
                prefix="Magia-",
                entity_type="magic_systems",
                entity_label="Sistema de Poder"
            )
        
        if key == "spell_forge":
            return SpellForgeWidget(self.history)

        if key == "powers":
            return ModularEntityWidget(
                self.history,
                prefix="Hechizo-",
                entity_type="spells",
                entity_label="Poder / Técnica"
            )

        if key == "consumables":
            return ModularEntityWidget(
                self.history,
                prefix="Objetos-Comida-",
                entity_type="foods",
                entity_label="Recurso / Consumible"
            )

        if key == "weapons":
            return ModularEntityWidget(
                self.history,
                prefix="Objetos-Armas-",
                entity_type="weapons",
                entity_label="Arma"
            )

        if key == "armors":
            return ModularEntityWidget(
                self.history,
                prefix="Objetos-Armadura-",
                entity_type="armors",
                entity_label="Armadura / Protección"
            )

        if key == "artifacts":
            return ModularEntityWidget(
                self.history,
                prefix="Objetos-Reliquia-",
                entity_type="relics",
                entity_label="Artefacto"
            )

        if key == "factions":
            return ModularEntityWidget(
                self.history,
                prefix="Faccion-",
                entity_type="factions",
                entity_label="Facción / Organización"
            )

        if key == "creatures":
            return ModularEntityWidget(
                self.history,
                prefix="Criaturas-",
                entity_type="creatures",
                entity_label="Ser / Criatura"
            )

        if key == "forces":
            return ModularEntityWidget(
                self.history,
                prefix="Ejercito-",
                entity_type="armies",
                entity_label="Fuerza"
            )

        if key == "simulation":
            return SimulationWidget(self.history)

        if key == "echoes":
            return EchoesWidget(self.history)

        if key == "encounters":
            return EncounterWidget(self.history)

        if key == "dramatic_battles":
            return EpicBattleWidget(self.history)

        if key == "maintenance":
            return MaintenanceWidget(self.history)

        oracle_data = next(
            (
                oracle for oracle in self.oracles
                if oracle["name"] == key
            ),
            None
        )

        if not oracle_data:
            return None

        return OracleWidget(
            oracle_data,
            self.history
        )

    # =========================
    # VERIFICACIÓN
    # =========================

    def verify_last_roll(self):
        from core.verifier import verify_line

        try:
            with open(
                "data/logs/important_rolls.log",
                "r",
                encoding="utf-8"
            ) as f:
                lines = f.readlines()

            if not lines:
                self.history.append("⚠ No hay tiradas para verificar")
                return

            last_line = lines[-1]
            valid = verify_line(last_line)

            if valid:
                self.history.append("✅ Tirada válida (no manipulada)")
            else:
                self.history.append("❌ Tirada ALTERADA o corrupta")

        except FileNotFoundError:
            self.history.append("⚠ Archivo de registros no encontrado")

    # =========================
    # FILTRO
    # =========================

    def filter_oracles(self):
        text = self.search.text().lower().strip()

        self.oracle_list.clear()

        for key, label in self.get_base_items():
            if text in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, key)
                self.oracle_list.addItem(item)

        self.oracle_list.addItem("────────────")

        favorites = []
        normal = []

        for oracle in self.oracles:
            if text and text not in oracle["name"].lower():
                continue

            if oracle["name"] in self.favorites:
                favorites.append(oracle)
            else:
                normal.append(oracle)

        for oracle in favorites:
            self.oracle_list.addItem(f"⭐ {oracle['name']}")

        for oracle in normal:
            self.oracle_list.addItem(oracle["name"])

    # =========================
    # FAVORITOS
    # =========================

    def show_context_menu(self, pos):
        item = self.oracle_list.itemAt(pos)

        if not item:
            return

        key = item.data(Qt.UserRole)
        name = item.text().replace("⭐ ", "")

        if "────" in name:
            return

        if key:
            return

        menu = QMenu()

        if name in self.favorites:
            action = menu.addAction("Quitar de favoritos")
        else:
            action = menu.addAction("Agregar a favoritos")

        chosen = menu.exec(
            self.oracle_list.mapToGlobal(pos)
        )

        if chosen == action:
            if name in self.favorites:
                self.favorites.remove(name)
            else:
                self.favorites.append(name)

            save_favorites(self.favorites)
            self.load_default_oracles()

            add_system_log(
                self.history,
                f"⭐ Favorito actualizado → {name}"
            )