def parse_modifier_line(raw_text):
    parts = str(raw_text).split("|")

    name = parts[0].strip()
    modifiers = {}

    for part in parts[1:]:
        part = part.strip()

        if ":" not in part:
            continue

        key, value = part.split(":", 1)

        key = key.strip()
        value = value.strip()

        if value.lower() == "false":
            modifiers[key] = False

        elif value.lower() == "true":
            modifiers[key] = True

        else:
            try:
                modifiers[key] = int(value)
            except:
                modifiers[key] = value

    return name, modifiers


def clean_modifier_text(raw_text):
    name, _modifiers = parse_modifier_line(raw_text)
    return name


def apply_modifiers(base_scores, modifiers):
    scores = dict(base_scores)

    for key, value in modifiers.items():
        if key == "active":
            continue

        if isinstance(value, int):
            scores[key] = scores.get(key, 0) + value

    return scores


def merge_modifiers(*modifier_dicts):
    result = {}

    for modifiers in modifier_dicts:
        for key, value in modifiers.items():
            if isinstance(value, int):
                result[key] = result.get(key, 0) + value

    return result