from widgets.base_generator_widget import BaseGeneratorWidget

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QPushButton
)

from core.parser import weighted_choice
from utils.ui_helpers import sort_combobox
from core.parser import load_all_lists
from services.name_generator_service import generate_entity_name
from services.npc_loadout_service import generate_npc_loadout
from services.species_service import (
    load_species,
    get_random_species,
    generate_species_from_oracles,
    save_species,
    get_species_by_id
)


class NPCWidget(BaseGeneratorWidget):

    ENTITY_PREFIX = "NPC-"
    ENTITY_TYPE = "npcs"
    ENTITY_LABEL = "NPC"

    def __init__(self, history_widget):
        super().__init__(history_widget)

        self.generated_meta = {}
        self.generated_species = None

        meta_layout = QHBoxLayout()

        meta_layout.addWidget(QLabel("Importancia:"))

        self.importance_combo = QComboBox()
        self.importance_combo.addItems([
            "Común",
            "Importante",
            "Protagonista",
            "Antagonista",
            "Líder",
            "Héroe",
            "Villano",
            "Entidad clave"
        ])
        sort_combobox(self.importance_combo)

        meta_layout.addWidget(self.importance_combo)

        meta_layout.addWidget(QLabel("Rango de poder:"))

        self.power_rank_combo = QComboBox()
        self.power_rank_combo.addItems([
            "Aleatorio",
            "Débil",
            "Común",
            "Competente",
            "Fuerte",
            "Excepcional",
            "Legendario"
        ])
        sort_combobox(self.power_rank_combo)
        self.power_rank_combo.setCurrentText("Aleatorio")

        meta_layout.addWidget(self.power_rank_combo)

        meta_layout.addWidget(QLabel("Rol narrativo:"))

        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Neutral",
            "Aliado",
            "Rival",
            "Mentor",
            "Enemigo",
            "Gobernante",
            "Mercenario",
            "Guardián",
            "Profeta",
            "Agente oculto"
        ])
        sort_combobox(self.role_combo)

        meta_layout.addWidget(self.role_combo)

        meta_layout.addWidget(QLabel("Género:"))

        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Aleatorio")

        for oracle in load_all_lists():
            if oracle["name"] == "NPC-Genero":
                data = oracle.get("data", {})
                options = data.get("Resultados", [])

                for raw, _weight in options:
                    gender = raw.split("|")[0].strip()

                    if self.gender_combo.findText(gender) < 0:
                        self.gender_combo.addItem(gender)

        sort_combobox(self.gender_combo)
        self.gender_combo.setCurrentText("Aleatorio")

        meta_layout.addWidget(self.gender_combo)

        meta_layout.addWidget(QLabel("Raza / Especie:"))

        self.species_combo = QComboBox()
        self.load_species_options()
        meta_layout.addWidget(self.species_combo)

        self.refresh_species_btn = QPushButton("🔄")
        self.refresh_species_btn.setToolTip("Recargar especies guardadas")
        self.refresh_species_btn.clicked.connect(self.load_species_options)
        meta_layout.addWidget(self.refresh_species_btn)

        self.layout().insertLayout(1, meta_layout)

        self.hero_checkbox = QCheckBox("🌟 NPC Héroe")
        self.layout().insertWidget(2, self.hero_checkbox)

        self.auto_equipment_checkbox = QCheckBox("⚔ Equipo automático")
        self.auto_equipment_checkbox.setChecked(True)
        self.layout().insertWidget(3, self.auto_equipment_checkbox)

        self.auto_abilities_checkbox = QCheckBox("🧠 Habilidades automáticas")
        self.auto_abilities_checkbox.setChecked(True)
        self.layout().insertWidget(4, self.auto_abilities_checkbox)

        self.auto_magic_checkbox = QCheckBox("✨ Magia/Poderes automáticos")
        self.auto_magic_checkbox.setChecked(True)
        self.layout().insertWidget(5, self.auto_magic_checkbox)

    # =====================================
    # Especies / razas
    # =====================================

    def load_species_options(self):
        current = None

        if hasattr(self, "species_combo"):
            current = self.species_combo.currentData()
            self.species_combo.clear()

        self.species_combo.addItem("Aleatoria guardada", "random_saved")
        self.species_combo.addItem("Generar nueva especie", "generate_new")
        self.species_combo.addItem("Usar oráculo antiguo", "legacy_oracle")

        for species in load_species():
            self.species_combo.addItem(
                f"{species.get('name')} ({species.get('id')})",
                species.get("id")
            )

        if current:
            index = self.species_combo.findData(current)

            if index >= 0:
                self.species_combo.setCurrentIndex(index)

    def resolve_species_for_npc(self):
        selected = self.species_combo.currentData()

        if selected == "random_saved":
            return get_random_species()

        if selected == "generate_new":
            species = generate_species_from_oracles()
            save_species(species)
            self.load_species_options()
            return species

        if selected == "legacy_oracle":
            return None

        return get_species_by_id(selected)

    def apply_species_to_generated_data(self, species):
        if not species:
            return

        species_name = species.get("name", "Especie desconocida")

        self.generated_data["Raza"] = species_name
        self.generated_data["Especie"] = species_name
        self.generated_data["species"] = {
            "id": species.get("id"),
            "name": species_name,
            "type": "species"
        }

        species_data = species.get("data", {})

        if species_data:
            self.generated_data["Datos de especie"] = species_data

        species_effects = species.get("effects", {})

        if species_effects:
            self.generated_data["Efectos de especie"] = species_effects

    def append_species_to_result(self, species):
        if not species:
            return

        self.result.append("\n🧬 RAZA / ESPECIE")
        self.result.append(f"Nombre: {species.get('name', 'Especie desconocida')}")

        data = species.get("data", {})

        for key in ["Origen", "Cabeza", "Torso", "Piernas", "Brazos", "Características"]:
            value = data.get(key)

            if value:
                self.result.append(f"{key}: {value}")

        effects = species.get("effects", {})

        if effects:
            self.result.append("Efectos inferidos:")

            for key, value in effects.items():
                sign = "+" if value >= 0 else ""
                self.result.append(f"- {key}: {sign}{value}")

    # =====================================
    # Generar
    # =====================================

    def generate_entity(self):
        super().generate_entity()

        self.generated_meta = self.generate_default_npc_meta()
        self.generated_species = self.resolve_species_for_npc()

        selected_gender = self.generated_meta.get(
            "gender",
            "Desconocido"
        )

        self.generated_data["Género"] = selected_gender
        self.generated_data["Genero"] = selected_gender
        self.generated_data["gender"] = selected_gender

        self.apply_species_to_generated_data(self.generated_species)
        self.append_species_to_result(self.generated_species)

        if self.hero_checkbox.isChecked():
            heroic_gift = weighted_choice([
                ("Arma consagrada", 1),
                ("Vínculo con una montura", 1),
                ("Sangre antigua", 1),
                ("Protección sobrenatural", 1),
                ("Visión profética", 1),
                ("Voluntad indomable", 1),
                ("Marca de destino", 1)
            ])

            self.generated_data["Don Heroico"] = heroic_gift
            self.result.append(f"\n🌟 Don Heroico: {heroic_gift}")

        loadout = generate_npc_loadout(
            role=self.generated_meta.get("role"),
            power_rank=self.generated_meta.get("power_rank"),
            importance=self.generated_meta.get("importance"),
            include_equipment=self.auto_equipment_checkbox.isChecked(),
            include_abilities=self.auto_abilities_checkbox.isChecked(),
            include_magic=self.auto_magic_checkbox.isChecked()
        )

        self.generated_data["Equipo inicial"] = loadout.get("equipment", {})
        self.generated_data["Habilidades"] = loadout.get("abilities", [])
        self.generated_data["Magia/Poderes"] = loadout.get("magic", {})

        self.append_loadout_to_result(loadout)

    def append_loadout_to_result(self, loadout):
        self.result.append("\n🎒 EQUIPO / CAPACIDADES INICIALES")

        equipment = loadout.get("equipment", {})

        weapon = equipment.get("weapon")
        armor = equipment.get("armor")
        items = equipment.get("items", [])
        relics = equipment.get("relics", [])

        if weapon:
            self.result.append(f"Arma: {weapon.get('name')}")

        if armor:
            self.result.append(f"Armadura: {armor.get('name')}")

        if items:
            self.result.append("Items:")
            for item in items:
                self.result.append(f"- {item.get('name')}")

        if relics:
            self.result.append("Reliquias:")
            for relic in relics:
                self.result.append(f"- {relic.get('name')}")

        abilities = loadout.get("abilities", [])

        if abilities:
            self.result.append("Habilidades:")
            for ability in abilities:
                self.result.append(f"- {ability}")

        magic = loadout.get("magic", {})

        if magic.get("knows_magic"):
            self.result.append("Magia/Poderes:")
            for system in magic.get("known_systems", []):
                self.result.append(f"- {system.get('name')}")
        else:
            self.result.append("Magia/Poderes: No conoce")

    # =====================================
    # Metadata
    # =====================================

    def generate_default_npc_meta(self):
        age = self.generate_age()

        meta = {
            "importance": self.importance_combo.currentText(),
            "role": self.role_combo.currentText(),
            "power_rank": self.power_rank_combo.currentText(),
            "status": "Sano",
            "active": True,
            "age": str(age),
            "life_stage": self.life_stage_from_age(age),
            "gender": self.generate_gender(),
            "traits": []
        }

        if self.generated_species:
            meta["species"] = {
                "id": self.generated_species.get("id"),
                "name": self.generated_species.get("name"),
                "type": "species"
            }

        return meta

    def generate_age(self):
        import random
        return random.randint(16, 80)

    def life_stage_from_age(self, age):
        if age < 18:
            return "Adolescencia"
        if age < 30:
            return "Juventud"
        if age < 50:
            return "Adultez"
        if age < 70:
            return "Madurez"

        return "Vejez"

    # =====================================
    # Guardar
    # =====================================

    def save_entity_data(self):
        if not self.generated_data:
            return

        name = (
            self.name_input.text().strip()
            or "NPC Sin Nombre"
        )

        if not self.generated_species:
            self.generated_species = self.resolve_species_for_npc()
            self.apply_species_to_generated_data(self.generated_species)

        meta = (
            self.generated_meta
            if self.generated_meta
            else self.generate_default_npc_meta()
        )

        selected_gender = meta.get(
            "gender",
            "Desconocido"
        )

        self.generated_data["Género"] = selected_gender
        self.generated_data["Genero"] = selected_gender
        self.generated_data["gender"] = selected_gender

        if self.generated_species:
            meta["species"] = {
                "id": self.generated_species.get("id"),
                "name": self.generated_species.get("name"),
                "type": "species"
            }

        entity = {
            "name": name,
            "type": self.ENTITY_TYPE,
            "meta": meta,
            "data": self.generated_data
        }

        from services.entity_service import save_entity
        from services.world_service import add_entity_to_world
        from core.system_log import add_system_log

        entity_id = save_entity(
            self.ENTITY_TYPE,
            entity
        )

        entity["id"] = entity_id

        world_id = self.world_combo.currentData()

        if world_id:
            add_entity_to_world(world_id, entity)

        species_name = (
            self.generated_species.get("name")
            if self.generated_species
            else self.generated_data.get("Raza", "Sin especie")
        )

        self.result.append(
            "\n"
            "💾 NPC GUARDADO\n"
            f"ID: {entity_id}\n"
            f"Importancia: {entity['meta']['importance']}\n"
            f"Rol: {entity['meta']['role']}\n"
            f"Poder: {entity['meta']['power_rank']}\n"
            f"Estado: {entity['meta']['status']}\n"
            f"Edad: {entity['meta']['age']}\n"
            f"Etapa: {entity['meta']['life_stage']}\n"
            f"Género: {entity['meta']['gender']}\n"
            f"Raza / Especie: {species_name}\n"
        )

        add_system_log(
            self.history,
            f"💾 NPC guardado → {name} ({entity_id})"
        )

    def save_current_entity(self):
        self.save_entity_data()

    # =====================================
    # Género / nombre
    # =====================================

    def generate_gender(self):
        if self.gender_combo.currentText() != "Aleatorio":
            return self.gender_combo.currentText()

        for oracle in load_all_lists():
            if oracle["name"] == "NPC-Genero":
                data = oracle.get("data", {})
                options = data.get("Resultados", [])

                if options:
                    return weighted_choice(options).split("|")[0].strip()

        return "Desconocido"

    def generate_random_name(self):
        style = "universal"

        if hasattr(self, "name_style_combo"):
            style = self.name_style_combo.currentText()

        gender = self.gender_combo.currentText()

        name = generate_entity_name(
            entity_type=self.ENTITY_TYPE,
            style=style,
            gender=gender
        )

        self.name_input.setText(name)
