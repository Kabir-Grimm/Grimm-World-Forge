from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QTextEdit,
    QLabel
)

from core.parser import weighted_choice

from datetime import datetime
from utils.ui_helpers import sort_combobox


class OracleWidget(QWidget):

    def __init__(self, oracle, history_widget=None):

        super().__init__()

        self.oracle = oracle

        self.history = history_widget

        self.checkboxes = {}

        self.generation_count = 0

        # =========================
        # Layout
        # =========================

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel(f"🧩 {self.oracle['name']}")
        )

        # =========================
        # Checkboxes
        # =========================

        for cat in self.oracle["data"]:

            cb = QCheckBox(cat)

            cb.setChecked(True)

            self.checkboxes[cat] = cb

            layout.addWidget(cb)

        # =========================
        # Botón generar
        # =========================

        self.generate_btn = QPushButton(
            "Generar"
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

        output = []

        for cat, options in self.oracle["data"].items():

            if self.checkboxes[cat].isChecked():

                choice = weighted_choice(options)

                output.append(
                    f"{cat}: {choice}"
                )

        self.generation_count += 1

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        separator = (
            "\n"
            "══════════════════════════\n"
            f"🎲 GENERACIÓN #{self.generation_count}\n"
            f"🕒 {timestamp}\n"
            f"📚 {self.oracle['name']}\n"
            "══════════════════════════\n\n"
        )

        text = separator + "\n".join(output)

        self.result.append(text)

        # =========================
        # Autoscroll
        # =========================

        scrollbar = self.result.verticalScrollBar()

        scrollbar.setValue(
            scrollbar.maximum()
        )