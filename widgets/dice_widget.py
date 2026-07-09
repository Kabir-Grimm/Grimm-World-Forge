from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QComboBox,
    QSpinBox
)

from datetime import datetime

import random
import requests

from core.audit import log_roll
from core.system_log import add_system_log
from utils.ui_helpers import sort_combobox


class DiceWidget(QWidget):

    def __init__(
        self,
        config,
        history_widget,
        audit_toggle,
        player_input,
        category_select,
        context_input
    ):

        super().__init__()

        self.config = config

        self.history = history_widget

        self.audit_toggle = audit_toggle

        self.player_input = player_input

        self.category_select = category_select

        self.context_input = context_input

        # =========================
        # Layout principal
        # =========================

        layout = QVBoxLayout()

        # =========================
        # Dados rápidos
        # =========================

        quick_layout = QHBoxLayout()

        quick_dice = [
            3, 4, 6, 8,
            10, 12, 20, 100
        ]

        for sides in quick_dice:

            btn = QPushButton(f"D{sides}")

            btn.clicked.connect(
                lambda checked=False, s=sides:
                self.quick_roll(s)
            )

            quick_layout.addWidget(btn)

        layout.addLayout(quick_layout)

        # =========================
        # Controles
        # =========================

        controls = QHBoxLayout()

        self.dice_type = QComboBox()

        self.dice_type.addItems([
            "D3", "D4", "D6", "D8",
            "D10", "D12", "D20", "D100"
        ])

        self.dice_amount = QSpinBox()

        self.dice_amount.setMinimum(1)

        self.dice_amount.setMaximum(100)

        self.dice_amount.setValue(1)

        self.roll_btn = QPushButton(
            "Lanzar"
        )

        controls.addWidget(
            QLabel("Dado:")
        )

        controls.addWidget(
            self.dice_type
        )

        controls.addWidget(
            QLabel("Cantidad:")
        )

        controls.addWidget(
            self.dice_amount
        )

        controls.addWidget(
            self.roll_btn
        )

        layout.addLayout(controls)

        # =========================
        # Resultado
        # =========================

        self.result_area = QTextEdit()

        layout.addWidget(
            self.result_area
        )

        # =========================
        # Eventos
        # =========================

        self.roll_btn.clicked.connect(
            self.roll_dice
        )

        self.setLayout(layout)

    # =====================================
    # Quick Roll
    # =====================================

    def quick_roll(self, sides):

        result = random.randint(1, sides)

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        text = (
            "\n"
            "══════════════════════\n"
            f"🕒 {timestamp}\n"
            f"🎲 D{sides}: {result}\n"
            "══════════════════════\n"
        )

        self.result_area.append(text)

    # =====================================
    # Roll Dice
    # =====================================

    def roll_dice(self):

        dice = self.dice_type.currentText()

        sides = int(
            dice.replace("D", "")
        )

        amount = self.dice_amount.value()

        results = []

        for _ in range(amount):

            results.append(
                random.randint(1, sides)
            )

        total = sum(results)

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        text = (
            "\n"
            "══════════════════════\n"
            f"🕒 {timestamp}\n"
            f"🎲 {dice} x{amount}\n"
            f"Resultados: {results}\n"
            f"Total: {total}\n"
        )

        # =========================
        # Auditoría
        # =========================

        if self.audit_toggle.isChecked():

            player = (
                self.player_input.text()
                or "Unknown"
            )

            category = (
                self.category_select.currentText()
            )

            context = (
                self.context_input.text()
                or "N/A"
            )

            # =====================
            # Hash local
            # =====================

            roll_id, hash_value = log_roll(
                player,
                category,
                context,
                dice,
                {
                    "results": results,
                    "total": total
                }
            )

            text += (
                "\n"
                "🔥 TIRADA IMPORTANTE\n"
                f"ID: {roll_id}\n"
                f"Hash: {hash_value[:12]}...\n"
            )

            # =====================
            # API
            # =====================

            try:

                response = requests.post(
                    self.config["server_url"],
                    json={
                        "user": self.config["user"],
                        "api_key": self.config["api_key"],
                        "roll": {
                            "dice": dice,
                            "results": results,
                            "total": total,
                            "context": context,
                            "timestamp": timestamp
                        }
                    },
                    timeout=3
                )

                if response.status_code == 200:

                    server_hash = (
                        response.json()["hash"]
                    )

                    text += (
                        f"🌐 Server OK → "
                        f"{server_hash[:12]}...\n"
                    )

                else:

                    text += (
                        "❌ Server Error\n"
                    )

            except Exception:

                text += (
                    "⚠ Sin conexión API\n"
                )

            # =====================
            # Historial global
            # =====================

            add_system_log(
                self.history,
                (
                    f"🔥 Tirada importante → "
                    f"{player} | "
                    f"{dice}={results} "
                    f"(Total={total})"
                )
            )

        text += (
            "══════════════════════\n"
        )

        self.result_area.append(text)

        scrollbar = (
            self.result_area.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )