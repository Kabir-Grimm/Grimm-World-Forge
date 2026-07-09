from services.chaos_service import modify_chaos
from services.relation_service import save_relation


def apply_echo_consequences(echo):
    """
    Aplica consecuencias simples al mundo según un eco narrativo.
    Por ahora modifica caos y crea relaciones narrativas.
    """

    if not echo:
        return []

    consequences = []

    action = echo.get("action", "")
    impact = echo.get("impact", "")
    target = echo.get("target", {})
    world_id = echo.get("world_id")
    world_name = echo.get("world_name", "Mundo")

    target_name = target.get("name", "Entidad desconocida")
    target_id = target.get("id")
    target_type = target.get("type", "entity")

    # =========================
    # Caos
    # =========================

    chaos_change = calculate_chaos_change(
        action,
        impact
    )

    if chaos_change != 0:
        new_chaos = modify_chaos(
            chaos_change
        )

        consequences.append(
            f"☍ Caos modificado: {chaos_change:+} → {new_chaos}"
        )

    # =========================
    # Relaciones narrativas
    # =========================

    if target_id and world_id:
        relation_type = relation_from_action(
            action,
            impact
        )

        if relation_type:
            save_relation(
                source={
                    "id": world_id,
                    "name": world_name,
                    "type": "world"
                },
                relation_type=relation_type,
                target={
                    "id": target_id,
                    "name": target_name,
                    "type": target_type
                },
                notes=f"Consecuencia automática de eco: {action} / {impact}"
            )

            consequences.append(
                f"🔗 Relación creada: {world_name} → {relation_type} → {target_name}"
            )

    return consequences


def calculate_chaos_change(action, impact):
    """
    Define cuánto cambia el caos según acción/impacto.
    """

    negative_keywords = [
        "Romper",
        "Corromper",
        "Invadir",
        "Destruir",
        "Traicionar",
        "Sabotear",
        "Infectar",
        "Reprimir",
        "Usurpar",
        "Desatar",
        "Aumenta la tensión",
        "Introduce una amenaza",
        "Provoca violencia",
        "Escala una guerra",
        "Aumenta el caos",
        "Desestabiliza",
        "Destruye confianza"
    ]

    positive_keywords = [
        "Proteger",
        "Purificar",
        "Reconstruir",
        "Negociar",
        "Fortalecer",
        "Preservar",
        "Inspirar",
        "Crea una oportunidad",
        "Fortalece una relación",
        "Genera resistencia organizada"
    ]

    for keyword in negative_keywords:
        if keyword.lower() in action.lower() or keyword.lower() in impact.lower():
            return 1

    for keyword in positive_keywords:
        if keyword.lower() in action.lower() or keyword.lower() in impact.lower():
            return -1

    return 0


def relation_from_action(action, impact):
    """
    Convierte una acción/impacto en relación narrativa.
    """

    mapping = {
        "Invadir": "amenaza",
        "Proteger": "protege",
        "Traicionar": "traiciona",
        "Corromper": "corrompe",
        "Purificar": "purifica",
        "Conquistar": "domina",
        "Perseguir": "persigue",
        "Vigilar": "vigila",
        "Observar": "observa",
        "Negociar": "negocia con",
        "Fortalecer": "fortalece",
        "Debilitar": "debilita",
        "Destruir": "daña",
        "Recuperar": "busca recuperar",
        "Ocultar": "oculta",
        "Revelar": "revela",
        "Sabotear": "sabotea",
        "Controlar": "controla",
        "Inspirar": "inspira",
        "Reprimir": "reprime",
        "Usurpar": "usurpa",
    }

    for key, relation in mapping.items():
        if key.lower() in action.lower():
            return relation

    if "Rompe una alianza".lower() in impact.lower():
        return "rompe alianza con"

    if "Fortalece una relación".lower() in impact.lower():
        return "fortalece relación con"

    if "Introduce una amenaza".lower() in impact.lower():
        return "amenaza"

    return None