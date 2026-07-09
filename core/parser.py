import os
import random


# ==========================================
# Parsear archivo
# ==========================================
def parse_file(path):

    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    config = {}
    data = {}

    current_category = None
    in_config = False

    for line in lines:

        # =========================
        # CONFIG
        # =========================

        if line == "#CONFIG":
            in_config = True
            continue

        elif line == "#ENDCONFIG":
            in_config = False
            continue

        if in_config:

            if ":" in line:

                key, value = line.split(":", 1)

                config[key.strip()] = value.strip()

            continue

        # =========================
        # [Categoria]
        # =========================

        if line.startswith("[") and line.endswith("]"):

            current_category = line[1:-1].strip()

            data[current_category] = []

            continue

        # =========================
        # Categoria;
        # =========================

        if line.endswith(";"):

            current_category = line[:-1].strip()

            data[current_category] = []

            continue

        # =========================
        # Contenido
        # =========================

        if current_category:

            text = line
            weight = 1.0

            # Peso custom

            if "|" in line:
                parts = line.rsplit("|", 1)

                try:
                    weight = float(parts[1].strip())
                    text = parts[0].strip()
                except:
                    text = line.strip()
                    weight = 1.0
            else:
                text = line.strip()
                weight = 1.0

            data[current_category].append((text, weight))

    # =========================
    # Lista simple
    # =========================

    if not data:

        simple_entries = []

        for line in lines:

            if not line.startswith("#"):

                text = line
                weight = 1.0

                if "|" in line:

                    try:

                        parts = line.rsplit("|", 1)

                        text = parts[0].strip()

                        weight = float(parts[1].strip())

                    except:

                        text = line
                        weight = 1.0

                simple_entries.append(
                    (text, weight)
                )

        data["Resultados"] = simple_entries

    return config, data


# ==========================================
# Cargar todas las listas
# ==========================================
def load_all_lists(path="data/listas"):

    os.makedirs(path, exist_ok=True)

    results = []

    for file in os.listdir(path):

        if file.endswith(".txt"):

            full_path = os.path.join(path, file)

            config, data = parse_file(full_path)

            results.append({
                "name": config.get(
                    "Nombre",
                    file.replace(".txt", "")
                ),
                "type": config.get(
                    "Tipo",
                    "simple"
                ),
                "data": data
            })

    return results


# ==========================================
# Selección ponderada
# ==========================================
def weighted_choice(options):

    total = sum(w for _, w in options)

    r = random.uniform(0, total)

    upto = 0

    for text, weight in options:

        if upto + weight >= r:
            return text

        upto += weight

    return options[-1][0]