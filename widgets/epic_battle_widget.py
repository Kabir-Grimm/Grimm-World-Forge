from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QSpinBox,
    QLineEdit,
    QCheckBox
)

from services.entity_registry_service import load_registry_entities
from services.epic_battle_service import (
    start_epic_battle,
    advance_battle_turn,
    apply_epic_battle_aftermath
)
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox
from core.display_names import display_entity_type


VALID_TYPES = {
    "npcs",
    "npc",
    "creatures",
    "creature"
}


class EpicBattleWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []
        self.session = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🔥 Batallas Épicas"))

        row_a = QHBoxLayout()

        row_a.addWidget(QLabel("Buscar A:"))

        self.search_a = QLineEdit()
        self.search_a.setPlaceholderText("NPC o criatura...")
        row_a.addWidget(self.search_a)

        row_a.addWidget(QLabel("Combatiente A:"))

        self.actor_a_combo = QComboBox()
        row_a.addWidget(self.actor_a_combo)

        layout.addLayout(row_a)

        row_b = QHBoxLayout()

        row_b.addWidget(QLabel("Buscar B:"))

        self.search_b = QLineEdit()
        self.search_b.setPlaceholderText("NPC o criatura...")
        row_b.addWidget(self.search_b)

        row_b.addWidget(QLabel("Combatiente B:"))

        self.actor_b_combo = QComboBox()
        row_b.addWidget(self.actor_b_combo)

        layout.addLayout(row_b)

        config = QHBoxLayout()

        config.addWidget(QLabel("Turnos máximos:"))

        self.turns_spin = QSpinBox()
        self.turns_spin.setMinimum(1)
        self.turns_spin.setMaximum(50)
        self.turns_spin.setValue(10)

        config.addWidget(self.turns_spin)

        self.loot_checkbox = QCheckBox("Permitir botín")
        self.loot_checkbox.setChecked(True)
        config.addWidget(self.loot_checkbox)

        self.refresh_btn = QPushButton("Refrescar")
        self.start_btn = QPushButton("Preparar batalla")
        self.next_turn_btn = QPushButton("Avanzar turno")
        self.aftermath_btn = QPushButton("Aplicar consecuencias finales")

        config.addWidget(self.refresh_btn)
        config.addWidget(self.start_btn)
        config.addWidget(self.next_turn_btn)
        config.addWidget(self.aftermath_btn)

        layout.addLayout(config)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result)

        self.refresh_btn.clicked.connect(self.load_entities)
        self.start_btn.clicked.connect(self.prepare_battle)
        self.next_turn_btn.clicked.connect(self.advance_turn)
        self.aftermath_btn.clicked.connect(self.apply_aftermath)

        self.search_a.textChanged.connect(self.populate_actor_a)
        self.search_b.textChanged.connect(self.populate_actor_b)

        self.load_entities()

    def load_entities(self):
        all_entities = load_registry_entities()

        self.entities = [
            entity for entity in all_entities
            if entity.get("type") in VALID_TYPES
            and entity.get("meta", {}).get("active", True) is not False
        ]

        self.entities.sort(
            key=lambda entity: (
                entity.get("type", "").lower(),
                entity.get("name", "").lower()
            )
        )

        self.populate_actor_a()
        self.populate_actor_b()

        add_system_log(
            self.history,
            f"🔥 Combatientes cargados: {len(self.entities)}"
        )

    def populate_actor_a(self):
        self.populate_combo(
            self.actor_a_combo,
            self.search_a.text()
        )

    def populate_actor_b(self):
        self.populate_combo(
            self.actor_b_combo,
            self.search_b.text()
        )

    def populate_combo(self, combo, search_text):
        current_id = None

        if combo.currentData():
            current_id = combo.currentData().get("id")

        search = search_text.lower().strip()

        combo.blockSignals(True)
        combo.clear()

        for entity in self.entities:
            name = entity.get("name", "")

            if search and search not in name.lower():
                continue

            combo.addItem(
                self.format_entity(entity),
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

    def format_entity(self, entity):
        return (
            f"{entity.get('name', 'Sin nombre')} "
            f"[{display_entity_type(entity.get('type', 'entity'))}]"
        )

    def prepare_battle(self):

        self.aftermath_btn.setEnabled(False)
        self.next_turn_btn.setEnabled(True)
        
        actor_a = self.actor_a_combo.currentData()
        actor_b = self.actor_b_combo.currentData()

        if not actor_a or not actor_b:
            self.result.append("⚠ Selecciona dos combatientes.")
            return

        if actor_a.get("id") == actor_b.get("id"):
            if actor_a.get("type") not in {"creatures", "creature"}:
                self.result.append("⚠ Solo las criaturas pueden pelear contra otra de su misma especie.")
                return

        self.session = start_epic_battle(
            actor_a.get("id"),
            actor_b.get("id"),
            max_turns=self.turns_spin.value()
        )

        if not self.session:
            self.result.append("⚠ No se pudo preparar la batalla.")
            return

        self.result.clear()

        self.result.append("══════════════════════")
        self.result.append("🔥 BATALLA PREPARADA")
        self.result.append("══════════════════════")
        self.result.append(
            f"{self.session['actor_a']['entity']['name']} "
            f"HP {self.session['actor_a']['hp']}/{self.session['actor_a']['max_hp']}"
        )
        self.result.append(
            f"{self.session['actor_b']['entity']['name']} "
            f"HP {self.session['actor_b']['hp']}/{self.session['actor_b']['max_hp']}"
        )
        self.result.append(
            f"Iniciativa: "
            f"{self.session['actor_a']['entity']['name']} {self.session['initiative_a']} / "
            f"{self.session['actor_b']['entity']['name']} {self.session['initiative_b']}"
        )
        self.result.append("")
        self.result.append("Presiona 'Avanzar turno' para continuar.")

    def advance_turn(self):
        if not self.session:
            self.result.append("⚠ Primero prepara una batalla.")
            return

        if self.session.get("finished"):
            self.next_turn_btn.setEnabled(False)
            self.aftermath_btn.setEnabled(True)
            self.result.append("⚠ La batalla ya terminó.")
            return

        self.session, text = advance_battle_turn(
            self.session
        )

        self.result.append("")
        self.result.append(text)

        if self.session.get("finished"):
            self.result.append("")
            self.result.append("══════════════════════")
            self.result.append("RESULTADO")
            self.result.append("══════════════════════")

            winner = self.session.get("winner")
            loser = self.session.get("loser")

            if winner and loser:
                self.result.append(
                    f"{winner['entity']['name']} vence a {loser['entity']['name']}."
                )
            else:
                self.result.append("La batalla termina sin vencedor claro.")

    def apply_aftermath(self):

        self.aftermath_btn.setEnabled(False)

        if not self.session:
            self.result.append("⚠ No hay batalla preparada.")
            return

        if not self.session.get("finished"):
            self.result.append("⚠ La batalla aún no ha terminado.")
            return

        result = apply_epic_battle_aftermath(
            self.session,
            allow_loot=self.loot_checkbox.isChecked()
        )

        self.result.append("")
        self.result.append("══════════════════════")
        self.result.append("CONSECUENCIAS FINALES")
        self.result.append("══════════════════════")

        for message in result.get("messages", []):
            self.result.append(f"- {message}")

        add_system_log(
            self.history,
            "🔥 Consecuencias de batalla épica aplicadas"
        )