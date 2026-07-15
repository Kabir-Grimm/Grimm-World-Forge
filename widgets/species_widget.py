from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit
)

from services.species_service import (
    generate_species_from_oracles,
    save_species,
    load_species
)

from core.system_log import add_system_log


class SpeciesWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget
        self.generated_species = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🧬 Creador de Razas / Especies"))

        name_layout = QHBoxLayout()

        name_layout.addWidget(QLabel("Nombre:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre opcional de la raza / especie")

        name_layout.addWidget(self.name_input)

        layout.addLayout(name_layout)

        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🎲 Generar especie")
        self.save_btn = QPushButton("💾 Guardar especie")
        self.refresh_btn = QPushButton("🔄 Ver especies guardadas")

        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        self.result = QTextEdit()
        self.result.setReadOnly(True)

        layout.addWidget(self.result)

        self.generate_btn.clicked.connect(self.generate_species)
        self.save_btn.clicked.connect(self.save_current_species)
        self.refresh_btn.clicked.connect(self.show_saved_species)

    def generate_species(self):
        custom_name = self.name_input.text().strip()

        self.generated_species = generate_species_from_oracles(
            name=custom_name or None
        )

        if not custom_name:
            self.name_input.setText(self.generated_species.get("name", ""))

        self.render_species()

        add_system_log(
            self.history,
            f"🧬 Especie generada → {self.generated_species.get('name')}"
        )

    def render_species(self):
        if not self.generated_species:
            return

        species = self.generated_species

        lines = [
            "══════════════════════",
            f"🧬 ESPECIE GENERADA: {species.get('name')}",
            "══════════════════════",
            f"ID provisional: {species.get('id')}",
            ""
        ]

        data = species.get("data", {})

        if data:
            lines.append("Características:")

            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"- {key}:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  • {sub_key}: {sub_value}")
                else:
                    lines.append(f"- {key}: {value}")

        effects = species.get("effects", {})

        if effects:
            lines.append("")
            lines.append("Efectos inferidos:")

            for key, value in effects.items():
                sign = "+" if value >= 0 else ""
                lines.append(f"- {key}: {sign}{value}")

        self.result.setPlainText("\n".join(lines))

    def save_current_species(self):
        if not self.generated_species:
            self.result.append("\n⚠ No hay especie generada para guardar.")
            return

        custom_name = self.name_input.text().strip()

        if custom_name:
            self.generated_species["name"] = custom_name

        species_id = save_species(self.generated_species)

        self.result.append(
            "\n"
            "💾 ESPECIE GUARDADA\n"
            f"ID: {species_id}"
        )

        add_system_log(
            self.history,
            f"💾 Especie guardada → {self.generated_species.get('name')} ({species_id})"
        )

    def show_saved_species(self):
        species_list = load_species()

        if not species_list:
            self.result.setPlainText("No hay especies guardadas todavía.")
            return

        lines = [
            "══════════════════════",
            "🧬 ESPECIES GUARDADAS",
            "══════════════════════",
            ""
        ]

        for species in species_list:
            lines.append(f"- {species.get('name', 'Sin nombre')} ({species.get('id')})")

        self.result.setPlainText("\n".join(lines))
