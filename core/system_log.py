from datetime import datetime


def add_system_log(history_widget, message):

    timestamp = datetime.now().strftime("%H:%M:%S")

    text = f"[{timestamp}] {message}"

    history_widget.append(text)