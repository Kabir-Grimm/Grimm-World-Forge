from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QLineEdit
)

from core.parser import load_all_lists
from core.system_log import add_system_log

from services.entity_registry_service import load_registry_entities
from services.power_service import roll_power_check
from services.timeline_service import save_timeline_event, get_current_world_year
from services.world_service import load_worlds
from services.modifier_service import parse_modifier_line
from services.encounter_service import apply_encounter_persistence
from utils.ui_helpers import sort_combobox
from core.display_names import display_entity_type

from services.encounter_consequence_service import (
    generate_encounter_consequence
)


METHOD_DOMAINS = {
    "Fuerza": "combat",
    "Magia": "arcane",
    "Estrategia": "knowledge",
    "Diplomacia": "social",
    "Sigilo": "stealth",
    "Manipulación": "influence",
    "Conocimiento": "knowledge",
    "Fe": "arcane",
    "Tecnología": "knowledge",
    "Recursos": "influence",
    "Intimidación": "combat",
    "Engaño": "social",
}


class EncounterWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.entities = []
        self.current_result = None
        self.context_modifiers = {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("⚔ Encuentros"))

        world_layout = QHBoxLayout()
        world_layout.addWidget(QLabel("Mundo:"))

        self.world_combo = QComboBox()
        world_layout.addWidget(self.world_combo)

        layout.addLayout(world_layout)

        actor_a_filter_layout = QHBoxLayout()
        actor_a_filter_layout.addWidget(QLabel("Tipo A:"))

        self.actor_a_type_combo = QComboBox()
        actor_a_filter_layout.addWidget(self.actor_a_type_combo)

        actor_a_filter_layout.addWidget(QLabel("Buscar A:"))

        self.actor_a_search = QLineEdit()
        self.actor_a_search.setPlaceholderText("Nombre...")
        actor_a_filter_layout.addWidget(self.actor_a_search)

        layout.addLayout(actor_a_filter_layout)

        actor_b_filter_layout = QHBoxLayout()
        actor_b_filter_layout.addWidget(QLabel("Tipo B:"))

        self.actor_b_type_combo = QComboBox()
        actor_b_filter_layout.addWidget(self.actor_b_type_combo)

        actor_b_filter_layout.addWidget(QLabel("Buscar B:"))

        self.actor_b_search = QLineEdit()
        self.actor_b_search.setPlaceholderText("Nombre...")
        actor_b_filter_layout.addWidget(self.actor_b_search)

        layout.addLayout(actor_b_filter_layout)

        actors_layout = QHBoxLayout()

        actors_layout.addWidget(QLabel("Actor A:"))

        self.actor_a_combo = QComboBox()
        actors_layout.addWidget(self.actor_a_combo)

        actors_layout.addWidget(QLabel("Actor B:"))

        self.actor_b_combo = QComboBox()
        actors_layout.addWidget(self.actor_b_combo)

        layout.addLayout(actors_layout)

        encounter_layout = QHBoxLayout()

        encounter_layout.addWidget(QLabel("Tipo:"))

        self.type_combo = QComboBox()
        encounter_layout.addWidget(self.type_combo)

        encounter_layout.addWidget(QLabel("Riesgo:"))

        self.risk_combo = QComboBox()
        encounter_layout.addWidget(self.risk_combo)

        encounter_layout.addWidget(QLabel("Contexto:"))

        self.context_combo = QComboBox()
        encounter_layout.addWidget(self.context_combo)

        layout.addLayout(encounter_layout)

        methods_layout = QHBoxLayout()

        methods_layout.addWidget(QLabel("Método A:"))

        self.method_a_combo = QComboBox()
        methods_layout.addWidget(self.method_a_combo)

        methods_layout.addWidget(QLabel("Método B:"))

        self.method_b_combo = QComboBox()
        methods_layout.addWidget(self.method_b_combo)

        layout.addLayout(methods_layout)

        buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("Refrescar entidades")
        self.randomize_btn = QPushButton("🎲 Aleatorizar contexto")
        self.resolve_btn = QPushButton("⚔ Resolver encuentro")
        self.save_btn = QPushButton("💾 Guardar como evento")

        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.randomize_btn)
        buttons.addWidget(self.resolve_btn)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        self.result = QTextEdit()
        layout.addWidget(self.result)

        self.refresh_btn.clicked.connect(self.load_entities)
        self.randomize_btn.clicked.connect(self.randomize_context)
        self.resolve_btn.clicked.connect(self.resolve_encounter)
        self.save_btn.clicked.connect(self.save_as_event)

        self.actor_a_type_combo.currentIndexChanged.connect(
            self.populate_actor_a_combo
        )

        self.actor_b_type_combo.currentIndexChanged.connect(
            self.populate_actor_b_combo
        )

        self.actor_a_search.textChanged.connect(
            self.populate_actor_a_combo
        )

        self.actor_b_search.textChanged.connect(
            self.populate_actor_b_combo
        )

        self.load_worlds()
        self.load_lists()
        self.load_entities()

    def load_worlds(self):
        self.world_combo.clear()
        self.world_combo.addItem("Sin mundo", None)

        for world in load_worlds():
            self.world_combo.addItem(
                f"{world.get('name')} ({world.get('id')})",
                world.get("id")
            )

    def get_list_values(self, name, fallback):
        values = []

        for oracle in load_all_lists():
            if oracle["name"] != name:
                continue

            data = oracle.get("data", {})

            if "Resultados" in data:
                values = [
                    item[0]
                    for item in data["Resultados"]
                ]
            else:
                for options in data.values():
                    values.extend(
                        item[0]
                        for item in options
                    )

            break

        return values or fallback

    def load_lists(self):
        self.type_combo.clear()
        self.risk_combo.clear()
        self.context_combo.clear()
        self.method_a_combo.clear()
        self.method_b_combo.clear()

        self.type_combo.addItems(
            self.get_list_values(
                "Encuentros-Tipo",
                [
                    "Combate",
                    "Duelo",
                    "Negociación",
                    "Investigación",
                    "Infiltración",
                    "Cacería",
                    "Persecución",
                    "Ritual",
                    "Supervivencia",
                    "Guerra",
                    "Exploración"
                ]
            )
        )

        methods = self.get_list_values(
            "Encuentros-Metodo",
            list(METHOD_DOMAINS.keys())
        )

        self.method_a_combo.addItems(methods)
        self.method_b_combo.addItems(methods)

        sort_combobox(self.method_a_combo)
        sort_combobox(self.method_b_combo)

        self.risk_combo.addItems(
            self.get_list_values(
                "Encuentros-Riesgo",
                [
                    "Bajo",
                    "Moderado",
                    "Alto",
                    "Mortal"
                ]
            )
        )

        context_values = self.get_list_values(
            "Encuentros-Contexto",
            [
                "Terreno neutral",
                "Emboscada|initiative:+3|stealth:+2|defense:-1",
                "Oscuridad|stealth:+3|knowledge:-1|combat:-1",
                "Lugar sagrado|arcane:+2|influence:+1|risk:+1",
                "Magia inestable|arcane:+3|control:-2|risk:+3"
            ]
        )

        self.context_combo.clear()
        self.context_modifiers = {}

        for raw_context in context_values:
            name, modifiers = parse_modifier_line(raw_context)

            self.context_modifiers[name] = modifiers
            self.context_combo.addItem(name)
            sort_combobox(self.context_combo)

    def load_entities(self):
        self.entities = load_registry_entities()

        self.entities.sort(
            key=lambda e: (
                e.get("type", ""),
                e.get("name", "")
            )
        )

        self.populate_type_filters()
        self.populate_actor_a_combo()
        self.populate_actor_b_combo()

        add_system_log(
            self.history,
            (
                "⚔ Entidades actualizadas "
                f"para encuentros: {len(self.entities)}"
            )
        )

    def populate_type_filters(self):
        entity_types = sorted({
            entity.get("type", "entity")
            for entity in self.entities
        })

        current_a_type = self.actor_a_type_combo.currentData()
        current_b_type = self.actor_b_type_combo.currentData()

        self.actor_a_type_combo.blockSignals(True)
        self.actor_b_type_combo.blockSignals(True)

        self.actor_a_type_combo.clear()
        self.actor_b_type_combo.clear()

        self.actor_a_type_combo.addItem("Todos", None)
        self.actor_b_type_combo.addItem("Todos", None)

        for entity_type in entity_types:
            self.actor_a_type_combo.addItem(
                entity_type,
                entity_type
            )
            sort_combobox(self.actor_a_type_combo)

            self.actor_b_type_combo.addItem(
                entity_type,
                entity_type
            )
            sort_combobox(self.actor_b_type_combo)

        self.actor_a_type_combo.blockSignals(False)
        self.actor_b_type_combo.blockSignals(False)

        if current_a_type:
            index = self.actor_a_type_combo.findData(current_a_type)

            if index >= 0:
                self.actor_a_type_combo.setCurrentIndex(index)

        if current_b_type:
            index = self.actor_b_type_combo.findData(current_b_type)

            if index >= 0:
                self.actor_b_type_combo.setCurrentIndex(index)

    def populate_actor_a_combo(self):
        self.populate_actor_combo(
            combo=self.actor_a_combo,
            selected_type=self.actor_a_type_combo.currentData(),
            search_text=self.actor_a_search.text()
        )

    def populate_actor_b_combo(self):
        self.populate_actor_combo(
            combo=self.actor_b_combo,
            selected_type=self.actor_b_type_combo.currentData(),
            search_text=self.actor_b_search.text()
        )

    def populate_actor_combo(
        self,
        combo,
        selected_type,
        search_text
    ):
        current_id = combo.currentData()
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
                self.format_entity(entity),
                entity.get("id")
            )
        sort_combobox(combo)

        combo.blockSignals(False)

        if current_id:
            index = combo.findData(current_id)

            if index >= 0:
                combo.setCurrentIndex(index)

    def format_entity(self, entity):
        return (
            f"{entity.get('name', 'Sin nombre')} "
            f"[{display_entity_type(entity.get('type', 'entity'))}]"
        )

    def randomize_context(self):
        import random

        combos = [
            self.type_combo,
            self.risk_combo,
            self.context_combo,
            self.method_a_combo,
            self.method_b_combo
        ]

        for combo in combos:
            if combo.count() > 0:
                combo.setCurrentIndex(
                    random.randint(0, combo.count() - 1)
                )

    def resolve_encounter(self):
        actor_a_id = self.actor_a_combo.currentData()
        actor_b_id = self.actor_b_combo.currentData()

        if not actor_a_id or not actor_b_id:
            self.result.append(
                "⚠ Selecciona dos entidades."
            )
            return

        if actor_a_id == actor_b_id:
            self.result.append(
                "⚠ Elige dos entidades distintas."
            )
            return

        method_a = self.method_a_combo.currentText()
        method_b = self.method_b_combo.currentText()

        domain_a = METHOD_DOMAINS.get(method_a, "combat")
        domain_b = METHOD_DOMAINS.get(method_b, "combat")

        context_name = self.context_combo.currentText()
        context_modifiers = self.context_modifiers.get(
            context_name,
            {}
        )

        roll_a = roll_power_check(
            actor_a_id,
            domain_a,
            external_modifiers=context_modifiers
        )

        roll_b = roll_power_check(
            actor_b_id,
            domain_b,
            external_modifiers=context_modifiers
        )

        if not roll_a or not roll_b:
            self.result.append(
                "⚠ No se pudo calcular el poder de una o ambas entidades."
            )
            return

        margin = roll_a["total"] - roll_b["total"]

        if margin > 0:
            winner = roll_a
            loser = roll_b
        elif margin < 0:
            winner = roll_b
            loser = roll_a
        else:
            winner = None
            loser = None

        interpretation = self.interpret_result(
            margin,
            roll_a,
            roll_b
        )

        temp_result = {
            "risk": self.risk_combo.currentText(),
            "margin": margin,
            "context_modifiers": context_modifiers
        }

        consequence = generate_encounter_consequence(
            self.risk_combo.currentText(),
            margin,
            temp_result
        )

        self.current_result = {
            "type": "encounter",
            "encounter_type": self.type_combo.currentText(),
            "risk": self.risk_combo.currentText(),
            "context": context_name,
            "context_modifiers": context_modifiers,
            "actor_a": roll_a,
            "actor_b": roll_b,
            "method_a": method_a,
            "method_b": method_b,
            "domain_a": domain_a,
            "domain_b": domain_b,
            "margin": margin,
            "winner": winner,
            "loser": loser,
            "interpretation": interpretation,
            "consequence": consequence,
            "created_at": datetime.now().isoformat()
        }

        context_lines = []

        for key, value in context_modifiers.items():
            context_lines.append(f"{key}: {value:+}")

        context_text = (
            "\n".join(context_lines)
            if context_lines
            else "Sin modificadores"
        )

        text = (
            "\n══════════════════════\n"
            "⚔ ENCUENTRO RESUELTO\n"
            "══════════════════════\n\n"
            f"Tipo: {self.type_combo.currentText()}\n"
            f"Riesgo: {self.risk_combo.currentText()}\n"
            f"Contexto: {context_name}\n"
            f"Modificadores de contexto:\n{context_text}\n\n"
            f"{roll_a['entity']['name']} usa {method_a} ({domain_a})\n"
            f"Valor: {roll_a['score']} + d20({roll_a['roll']}) = {roll_a['total']}\n\n"
            f"{roll_b['entity']['name']} usa {method_b} ({domain_b})\n"
            f"Valor: {roll_b['score']} + d20({roll_b['roll']}) = {roll_b['total']}\n\n"
            f"Resultado:\n{interpretation}\n\n"
            f"Consecuencia sugerida:\n{consequence.get('description')}\n"
        )

        self.result.append(text)

        add_system_log(
            self.history,
            "⚔ Encuentro resuelto"
        )

    def interpret_result(self, margin, roll_a, roll_b):
        if margin == 0:
            return "Empate tenso. Nadie obtiene una victoria clara."

        abs_margin = abs(margin)

        winner = roll_a if margin > 0 else roll_b
        loser = roll_b if margin > 0 else roll_a

        winner_name = winner["entity"]["name"]
        loser_name = loser["entity"]["name"]

        if abs_margin <= 3:
            return (
                f"{winner_name} supera por muy poco a {loser_name}. "
                "La victoria tiene costo, duda o consecuencia."
            )

        if abs_margin <= 8:
            return (
                f"{winner_name} vence a {loser_name} con claridad, "
                "aunque el resultado aún deja secuelas."
            )

        return (
            f"{winner_name} domina ampliamente a {loser_name}. "
            "El resultado puede alterar su posición en el mundo."
        )

    def save_as_event(self):
        if not self.current_result:
            self.result.append(
                "⚠ No hay encuentro resuelto para guardar."
            )
            return

        world_id = self.world_combo.currentData()

        year = (
            get_current_world_year(world_id)
            if world_id
            else 1
        )

        description = self.current_result["interpretation"]

        event = {
            "world_id": world_id,
            "world_name": self.world_combo.currentText()
            if world_id
            else None,
            "year": year,
            "event_type": "Encuentro",
            "target": self.current_result.get("winner", {}).get("entity")
            if self.current_result.get("winner")
            else None,
            "description": description,
            "data": self.current_result,
            "created_at": datetime.now().isoformat()
        }

        event_id = save_timeline_event(event)

        self.result.append(
            "\n"
            "💾 ENCUENTRO GUARDADO COMO EVENTO\n"
            f"ID: {event_id}\n"
        )

        persistence = apply_encounter_persistence(
    self.current_result
)

        self.result.append("\n🧠 MEMORIA / REPUTACIÓN / CONSECUENCIA")

        for memory in persistence.get("memories", []):
            status = "ok" if memory.get("applied") else "falló"

            self.result.append(
                f"- Memoria {status}: "
                f"{memory.get('entity')} "
                f"({memory.get('perspective')})"
            )

        for rep in persistence.get("reputation", []):
            status = "ok" if rep.get("applied") else "falló"
            amount = rep.get("amount", 0)
            sign = "+" if amount >= 0 else ""

            self.result.append(
                f"- Reputación {status}: "
                f"{rep.get('key')} {sign}{amount}"
            )

        application = persistence.get("consequence")

        if application and application.get("applied"):
            self.result.append(
                f"- Estado aplicado: "
                f"{application.get('entity')} → "
                f"{application.get('status')}"
            )

        elif application:
            self.result.append(
                f"- Consecuencia sin estado directo: "
                f"{application.get('reason')}"
            )