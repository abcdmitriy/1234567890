from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QCheckBox, QWidget)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, initial_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки анонимизации")
        self.resize(400, 550)
        self.setStyleSheet(self._build_stylesheet())

        if initial_settings:
            self.settings = initial_settings.copy()
        else:
            self.settings = {
                "fio": True,
                "passport_series": True,
                "passport_code": True,
                "addresses": True,
                "phones": True,
                "emails": True,
                "org": True,
                "inn": True,
                "bank_account": True,
                "bic": True
            }

        self.checkboxes = {}  # все чекбоксы по ключу
        self.create_ui()

    def _build_stylesheet(self):
        return """
        QDialog {
            background: #f5f7fb;
            color: #111827;
            font-family: 'Segoe UI', sans-serif;
        }
        QWidget {
            font-family: 'Segoe UI', sans-serif;
        }
        QCheckBox {
            color: #334155;
            spacing: 10px;
            padding: 5px 4px;
            font-size: 13px;
            font-weight: normal;
        }
        QPushButton {
            background: #ffffff;
            color: #111827;
            border: 1px solid #dfe3ec;
            border-radius: 10px;
            padding: 8px 14px;
            min-height: 32px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #f3f6ff;
            border-color: #bfd1ff;
        }
        QPushButton:pressed {
            background: #eaf0ff;
        }
        """

    def create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(8)

        # Структура: (текст для родительского, список ключей, флаг группы)
        items = [
            {"label": "ФИО физических лиц", "keys": ["fio"], "group": False},
            {"label": "Паспортные данные", "keys": ["passport_series", "passport_code"], "group": True},
            {"label": "Адреса", "keys": ["addresses"], "group": False},
            {"label": "Телефоны", "keys": ["phones"], "group": False},
            {"label": "Email", "keys": ["emails"], "group": False},
            {"label": "Названия организаций", "keys": ["org"], "group": False},
            {"label": "ИНН", "keys": ["inn"], "group": False},
            {"label": "Банковские реквизиты", "keys": ["bank_account", "bic"], "group": True}
        ]

        for item in items:
            if item["group"]:
                # Родительский чекбокс
                parent_cb = QCheckBox(item["label"])
                parent_cb.setChecked(True)  # по умолчанию включена
                main_layout.addWidget(parent_cb)

                # Контейнер для дочерних с отступом
                child_container = QWidget()
                child_layout = QVBoxLayout(child_container)
                child_layout.setContentsMargins(25, 0, 0, 0)  # отступ слева
                child_layout.setSpacing(2)

                child_keys = []
                for key in item["keys"]:
                    if key == "passport_series":
                        label = "Серия и номер"
                    elif key == "passport_code":
                        label = "Код подразделения"
                    elif key == "bank_account":
                        label = "Расчётный счёт"
                    elif key == "bic":
                        label = "БИК"
                    else:
                        label = key.capitalize()

                    child_cb = QCheckBox(label)
                    child_cb.setChecked(self.settings.get(key, True))
                    child_layout.addWidget(child_cb)
                    self.checkboxes[key] = child_cb
                    child_keys.append(key)

                main_layout.addWidget(child_container)

                # Связываем родительский с дочерними
                def on_parent_toggled(checked, keys=child_keys):
                    for k in keys:
                        self.checkboxes[k].setChecked(checked)

                parent_cb.toggled.connect(on_parent_toggled)

                # При изменении дочерних обновляем родительский
                def update_parent(keys=child_keys, parent=parent_cb):
                    all_checked = all(self.checkboxes[k].isChecked() for k in keys)
                    parent.blockSignals(True)
                    parent.setChecked(all_checked)
                    parent.blockSignals(False)

                for k in child_keys:
                    self.checkboxes[k].stateChanged.connect(lambda state, keys=child_keys, parent=parent_cb: update_parent())

                # Инициализация родительского
                all_checked = all(self.checkboxes[k].isChecked() for k in child_keys)
                parent_cb.setChecked(all_checked)

                # Сохраняем родительский чекбокс для доступа к его состоянию при сохранении (необязательно)
                self.checkboxes[item["label"]] = parent_cb  # но мы не будем его сохранять

            else:
                # Одиночная категория — обычный чекбокс
                cb = QCheckBox(item["label"])
                cb.setChecked(self.settings.get(item["keys"][0], True))
                main_layout.addWidget(cb)
                self.checkboxes[item["keys"][0]] = cb

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Отмена")
        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self.accept_settings)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def accept_settings(self):
        for key, checkbox in self.checkboxes.items():
            # Пропускаем родительские (их ключи — это строки без подкатегорий, но мы их не сохраняем)
            if key in ["Паспортные данные", "Банковские реквизиты"]:
                continue
            self.settings[key] = checkbox.isChecked()
        super().accept()

    def get_settings(self):
        return self.settings