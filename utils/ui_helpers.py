from PySide6.QtWidgets import QComboBox


def sort_combobox(combo: QComboBox):
    current_data = combo.currentData()
    current_text = combo.currentText()

    items = []

    for i in range(combo.count()):
        items.append({
            "text": combo.itemText(i),
            "data": combo.itemData(i)
        })

    items.sort(
        key=lambda item: item["text"].lower()
    )

    combo.blockSignals(True)
    combo.clear()

    for item in items:
        combo.addItem(
            item["text"],
            item["data"]
        )

    if current_data is not None:
        index = combo.findData(current_data)

        if index >= 0:
            combo.setCurrentIndex(index)

    elif current_text:
        index = combo.findText(current_text)

        if index >= 0:
            combo.setCurrentIndex(index)

    combo.blockSignals(False)