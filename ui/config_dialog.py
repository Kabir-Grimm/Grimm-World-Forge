from PySide6.QtWidgets import (
    QComboBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from core.config import save_config
from services.display_profile_service import (
    get_available_profiles,
    get_active_profile_name,
    set_active_profile
)
from services.display_profile_service import set_active_profile


class ConfigDialog(QDialog):
    def __init__(self, config):
        super().__init__()

        self.setWindowTitle("Configuración")

        self.config = config

        layout = QVBoxLayout()

        # 🔹 Inputs
        self.user_input = QLineEdit(config.get("user", ""))
        self.api_input = QLineEdit(config.get("api_key", ""))
        self.url_input = QLineEdit(config.get("server_url", ""))

        layout.addWidget(QLabel("Usuario"))
        layout.addWidget(self.user_input)

        layout.addWidget(QLabel("API Key"))
        layout.addWidget(self.api_input)

        layout.addWidget(QLabel("Server URL"))
        layout.addWidget(self.url_input)

        # 🔘 Botón guardar
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save)

        layout.addWidget(save_btn)

        self.setLayout(layout)

        
        layout.addWidget(
            QLabel("Perfil visual:")
        )

        self.profile_combo = QComboBox()

        self.profile_combo.addItems(
            get_available_profiles()
        )

        self.profile_combo.setCurrentText(
            get_active_profile_name()
        )
    
        layout.addWidget(
            self.profile_combo
        )

        set_active_profile(
            self.profile_combo.currentText()
        )

    def save(self):
        self.config["user"] = self.user_input.text()
        self.config["api_key"] = self.api_input.text()
        self.config["server_url"] = self.url_input.text()

        save_config(self.config)
        set_active_profile(
            self.profile_combo.currentText()
        )

        self.accept()