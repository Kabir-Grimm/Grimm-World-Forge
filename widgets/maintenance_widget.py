from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QCheckBox
)

from utils.reset_tools import (
    backup_entities,
    clean_entities,
    reset_world_data
)

from core.system_log import add_system_log


class MaintenanceWidget(QWidget):

    def __init__(self, history_widget):
        super().__init__()

        self.history = history_widget

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🧹 Mantenimiento"))

        self.info_label = QLabel(
            "La limpieza conservará contenido base como:\n"
            "- default_items.json\n"
            "- magic_systems.json\n"
            "- spells.json\n"
            "- archivos con registros default_"
        )
        layout.addWidget(self.info_label)

        self.backup_checkbox = QCheckBox("Crear backup antes de limpiar")
        self.backup_checkbox.setChecked(True)
        layout.addWidget(self.backup_checkbox)

        self.backup_btn = QPushButton("💾 Crear backup")
        self.clean_btn = QPushButton("🧹 Limpiar entidades de prueba")
        self.reset_btn = QPushButton("♻ Reiniciar mundo completo")

        layout.addWidget(self.backup_btn)
        layout.addWidget(self.clean_btn)
        layout.addWidget(self.reset_btn)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result)

        self.backup_btn.clicked.connect(self.create_backup)
        self.clean_btn.clicked.connect(self.clean_entities_data)
        self.reset_btn.clicked.connect(self.reset_world)

    def create_backup(self):
        result = backup_entities()

        self.result.append("💾 Backup creado:")
        self.result.append(result.get("backup_dir", "Sin ruta"))

        for item in result.get("copied", []):
            self.result.append(f"- {item}")

        self.result.append("")

        add_system_log(
            self.history,
            "💾 Backup creado desde mantenimiento"
        )

    def clean_entities_data(self):
        confirm = QMessageBox.question(
            self,
            "Confirmar limpieza",
            (
                "Esto borrará entidades generadas, relaciones y layout del mapa.\n\n"
                "Se conservarán archivos base como:\n"
                "- default_items.json\n"
                "- magic_systems.json\n"
                "- spells.json\n"
                "- registros con id default_\n\n"
                "¿Continuar?"
            )
        )

        if confirm != QMessageBox.Yes:
            return

        result = clean_entities(
            create_backup=self.backup_checkbox.isChecked()
        )

        self.result.append("🧹 Entidades limpiadas.")

        backup = result.get("backup")

        if backup:
            self.result.append(f"Backup: {backup.get('backup_dir')}")

        preserved = result.get("preserved", [])
        deleted = result.get("deleted", [])

        if preserved:
            self.result.append("Conservado:")
            for item in preserved:
                self.result.append(f"- {item}")

        if deleted:
            self.result.append("Borrado:")
            for item in deleted:
                self.result.append(f"- {item}")

        self.result.append("")

        add_system_log(
            self.history,
            "🧹 Entidades limpiadas desde mantenimiento"
        )

    def reset_world(self):
        confirm = QMessageBox.question(
            self,
            "Confirmar reinicio completo",
            (
                "Esto reiniciará mundos, NPCs, relaciones y layouts.\n\n"
                "Se conservarán bibliotecas base:\n"
                "- default_items.json\n"
                "- magic_systems.json\n"
                "- spells.json\n"
                "- registros con id default_\n\n"
                "¿Continuar?"
            )
        )

        if confirm != QMessageBox.Yes:
            return

        result = reset_world_data(
            create_backup=self.backup_checkbox.isChecked()
        )

        self.result.append("♻ Mundo reiniciado.")

        backup = result.get("backup")

        if backup:
            self.result.append(f"Backup: {backup.get('backup_dir')}")

        preserved = result.get("preserved", [])
        deleted = result.get("deleted", [])

        if preserved:
            self.result.append("Conservado:")
            for item in preserved:
                self.result.append(f"- {item}")

        if deleted:
            self.result.append("Borrado:")
            for item in deleted:
                self.result.append(f"- {item}")

        self.result.append("")

        add_system_log(
            self.history,
            "♻ Mundo reiniciado desde mantenimiento"
        )