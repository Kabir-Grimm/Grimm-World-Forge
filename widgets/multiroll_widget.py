from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QCheckBox,
    QScrollArea
)

from core.parser import weighted_choice
from utils.ui_helpers import sort_combobox

from datetime import datetime


class MultiRollWidget(QWidget):

    def __init__(self, oracles, history_widget):

        super().__init__()

        self.oracles = oracles

        self.history = history_widget

        self.checkboxes = {}

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("🎲 Tirada Múltiple")
        )

        # =========================
        # Scroll
        # =========================

        scroll = QScrollArea()

        scroll_widget = QWidget()

        scroll_layout = QVBoxLayout()

        scroll_widget.setLayout(scroll_layout)

        # =========================
        # Checkboxes
        # =========================

        for oracle in self.oracles:

            cb = QCheckBox(oracle["name"])

            self.checkboxes[oracle["name"]] = cb

            scroll_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)

        scroll.setWidgetResizable(True)

        layout.addWidget(scroll)

        # =========================
        # Botón
        # =========================

        self.generate_btn = QPushButton(
            "Generar Tirada"
        )

        self.generate_btn.clicked.connect(
            self.generate
        )

        layout.addWidget(self.generate_btn)

        # =========================
        # Resultado
        # =========================

        self.result = QTextEdit()

        layout.addWidget(self.result)

        self.setLayout(layout)

    # =====================================

    def generate(self):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        output = []

        output.append(
            "══════════════════════"
        )

        output.append(
            f"🎲 MULTIROLL"
        )

        output.append(
            f"🕒 {timestamp}"
        )

        output.append(
            "══════════════════════\n"
        )

        for oracle in self.oracles:

            name = oracle["name"]

            if self.checkboxes[name].isChecked():

                output.append(
                    f"📚 {name}"
                )

                for cat, options in oracle["data"].items():

                    result = weighted_choice(options)

                    output.append(
                        f"   {cat}: {result}"
                    )

                output.append("")

        self.result.append(
            "\n".join(output)
        )