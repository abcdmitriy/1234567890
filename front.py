import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QLabel,
                             QListWidget, QFileDialog, QDialog, QCheckBox, QMessageBox, QGroupBox,
                             QTableWidget, QTableWidgetItem, QProgressBar, QStatusBar, QHeaderView,
                             QTabWidget, QLineEdit, QTextEdit, QMenuBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


# --- ОКНО НАСТРОЕК (ИСПРАВЛЕНО) ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None, initial_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки анонимизации")
        self.resize(400, 500)

        # Загружаем настройки или используем значения по умолчанию
        if initial_settings:
            self.settings = initial_settings.copy()
        else:
            self.settings = {
                "fio": True, "org": True, "phones": True, "emails": True,
                "addresses": True, "passport": True, "banking": True,
                "court_cases": True, "dates": False, "amounts": False
            }

        self.categories = [
            ("ФИО физических лиц", "fio"),
            ("Названия организаций", "org"),
            ("Телефоны", "phones"),
            ("Email", "emails"),
            ("Адреса", "addresses"),
            ("Паспортные данные", "passport"),
            ("Банковские реквизиты", "banking"),
            ("Номера судебных дел", "court_cases"),
            ("Даты (опционально)", "dates"),
            ("Суммы (опционально)", "amounts")
        ]

        # Настройки сохранения результатов (Week 3)
        self.save_folder = ""
        self.preserve_structure = True

        # Сохраняем ссылки на виджеты для доступа извне
        self.category_checkboxes = []
        self.save_folder_btn = None
        self.preserve_structure_cb = None

        self.create_ui()

    def create_ui(self):
        layout = QVBoxLayout(self)

        # --- КАТЕГОРИИ ДЛЯ ПОИСКА И ЗАМЕНЫ ---
        groups_layout = QVBoxLayout()

        for text, key in self.categories:
            checkbox = QCheckBox(text)
            # Важно: проверяем значение в settings, а не используем get с дефолтом
            checkbox.setChecked(self.settings.get(key, True))
            groups_layout.addWidget(checkbox)
            self.category_checkboxes.append(checkbox)

        group_box = QGroupBox("Категории для поиска и замены")
        group_box.setLayout(groups_layout)
        layout.addWidget(group_box)

        # --- НАСТРОЙКИ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ (Week 3) ---
        save_options_layout = QVBoxLayout()

        self.save_folder_btn = QPushButton("Папка для сохранений...")
        if self.save_folder:
            folder_name = os.path.basename(self.save_folder)
            self.save_folder_btn.setText(f"Папка: {folder_name}")
        else:
            self.save_folder_btn.setText("Выберите папку")

        # Важно: подключаем только к кнопке, а не ко всем элементам
        self.save_folder_btn.clicked.connect(self.select_save_folder)
        save_options_layout.addWidget(self.save_folder_btn)

        self.preserve_structure_cb = QCheckBox("Сохранять структуру папок")
        self.preserve_structure_cb.setChecked(self.preserve_structure)
        save_options_layout.addWidget(self.preserve_structure_cb)

        group_box2 = QGroupBox("Настройки сохранения результатов")
        group_box2.setLayout(save_options_layout)
        layout.addWidget(group_box2)

        # --- КНОПКИ ОКНА НАСТРОЕК ---
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить настройки")
        cancel_btn = QPushButton("Отмена")

        save_btn.clicked.connect(self.accept_settings)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def accept_settings(self):
        """Сохраняем настройки чекбоксов категорий"""
        for i in range(len(self.categories)):
            checkbox = self.category_checkboxes[i]
            key = self.categories[i][1]
            self.settings[key] = checkbox.isChecked()

        super().accept()

    def get_settings(self):
        """Возвращаем настройки категорий"""
        return self.settings

    def select_save_folder(self):
        """Выбор папки для сохранений (вызывается только по клику на кнопку)"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранений результатов"
        )
        if folder_path:
            self.save_folder = folder_path
            folder_name = os.path.basename(folder_path)
            self.save_folder_btn.setText(f"Папка: {folder_name}")

    def get_save_settings(self):
        """Возвращает настройки сохранения (Folder + Structure)"""
        return {
            "save_folder": self.save_folder,
            "preserve_structure": self.preserve_structure_cb.isChecked()
        }


# --- ФОНОВАЯ ЗАДАЧА (МОК для тестов) ---
class AnonymizeWorker(QThread):
    progress = pyqtSignal(int, str, int)
    finished = pyqtSignal(dict)

    def __init__(self, files, settings, save_folder=None, preserve_structure=False):
        super().__init__()
        self.files = files
        self.settings = settings
        self.save_folder = save_folder or (os.path.dirname(files[0]) if files else None)
        self.preserve_structure = preserve_structure

    def run(self):
        total_files = len(self.files) if self.files else 1

        for i, file_path in enumerate(self.files):
            self.progress.emit(
                int((i / max(total_files, 1)) * 100),
                f"Обработка {i + 1}/{total_files}: {os.path.basename(file_path)}",
                i + 1
            )
            import time
            time.sleep(0.3)

        # MOCK-данные для демонстрации
        mock_mapping = [
            {"pseudonym": "Физическое лицо 1", "original": "Иванов Иван Иванович",
             "category": "ФИО", "file": os.path.basename(self.files[0]) if self.files else ""},
            {"pseudonym": "Компания 1", "original": "ООО Ромашка",
             "category": "ORG", "file": os.path.basename(self.files[0]) if self.files else ""},
        ]

        self.finished.emit({
            "mapping": mock_mapping,
            "files_processed": len(self.files),
            "save_folder": self.save_folder,
            "preserve_structure": self.preserve_structure
        })


# --- ГЛАВНОЕ ОКНО ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Анонимизатор документов [FRONTEND]")
        self.setGeometry(100, 100, 1400, 900)

        # Основные настройки категорий
        self.settings = {
            "fio": True, "org": True, "phones": True, "emails": True,
            "addresses": True, "passport": True, "banking": True,
            "court_cases": True, "dates": False, "amounts": False
        }

        # Настройки сохранения (Week 3)
        self.save_folder = None
        self.preserve_structure = True

        self.selected_files = []
        self.worker = None
        self.current_mapping = {}

        # Создаём табы для левой панели
        self.left_tabs = QTabWidget()
        self.files_tab = QWidget()
        self.mapping_tab = QWidget()
        self.create_left_tabs_ui()

        self.create_main_layout()
        self.setup_menu_bar()

    def create_left_tabs_ui(self):
        # --- ВКЛАДКА "ФАЙЛЫ" ---
        file_upload_layout = QVBoxLayout(self.files_tab)
        file_upload_layout.setAlignment(Qt.AlignTop)

        load_btn_frame = QHBoxLayout()
        self.btn_load_file = QPushButton("Загрузить файл")
        self.btn_load_folder = QPushButton("Загрузить папку")

        self.btn_load_file.clicked.connect(self.load_single_file)
        self.btn_load_folder.clicked.connect(self.load_folder)

        load_btn_frame.addWidget(self.btn_load_file)
        load_btn_frame.addWidget(self.btn_load_folder)
        file_upload_layout.addLayout(load_btn_frame)

        clear_btn = QPushButton("Очистить список")
        clear_btn.clicked.connect(lambda: self.file_list_widget.clear())
        load_btn_frame.addWidget(clear_btn)

        self.file_list_widget = QListWidget()
        file_upload_layout.addWidget(self.file_list_widget, stretch=2)

        info_label = QLabel("Загружено файлов: 0")
        info_label.setAlignment(Qt.AlignLeft)
        self.info_label = info_label
        file_upload_layout.addWidget(info_label)

        # --- ВКЛАДКА "КАРТА СООТВЕТСТВИЙ" ---
        mapping_layout = QVBoxLayout(self.mapping_tab)
        mapping_layout.setAlignment(Qt.AlignTop)

        tab_label = QLabel("Карта соответствий (будет заполнена после обработки)")
        tab_label.setAlignment(Qt.AlignCenter)
        tab_label.setStyleSheet("color: gray; font-style: italic;")
        mapping_layout.addWidget(tab_label)

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(5)
        self.mapping_table.setHorizontalHeaderLabels([
            "Псевдоним", "Исходное значение", "Категория",
            "Файлы", "Действие"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mapping_table.setEditTriggers(QTableWidget.EditKeyPressed)

        mapping_layout.addWidget(self.mapping_table, stretch=3)

        map_btn_frame = QHBoxLayout()
        btn_save_map = QPushButton("Сохранить карту (.json)")
        btn_save_map.clicked.connect(self.save_mapping_json)

        btn_export_excel = QPushButton("Экспорт в Excel")
        btn_export_excel.clicked.connect(self.export_to_excel)

        map_btn_frame.addWidget(btn_save_map)
        map_btn_frame.addWidget(btn_export_excel)
        mapping_layout.addLayout(map_btn_frame, stretch=1)

        self.left_tabs.addTab(self.files_tab, "Файлы")
        self.left_tabs.addTab(self.mapping_tab, "Карта соответствий")

    def create_main_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(main_splitter)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QWidget()
        main_left_layout = QVBoxLayout(left_panel)

        btn_frame = QSplitter(Qt.Vertical)
        self.btn_anonymize = QPushButton("Анонимизировать документы")
        self.btn_deanonymize = QPushButton("Деанонимизировать текст")
        self.btn_settings = QPushButton("Настройки")

        for btn in [self.btn_anonymize, self.btn_deanonymize, self.btn_settings]:
            btn_frame.addWidget(btn)

        main_left_layout.addWidget(btn_frame, stretch=1)
        main_left_layout.addWidget(self.left_tabs, stretch=2)

        main_splitter.addWidget(left_panel)

        # --- ПРАВАЯ ОБЛАСТЬ ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        doc_viewer = QWidget()
        doc_viewer.setStyleSheet("background-color: white;")
        doc_label = QLabel("Окно просмотра документа\n(будет здесь)")
        layout_doc = QVBoxLayout(doc_viewer)
        layout_doc.setAlignment(Qt.AlignCenter)
        layout_doc.addWidget(doc_label)

        right_layout.addWidget(doc_viewer, stretch=8)

        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: gray;")
        right_layout.addWidget(separator)

        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        progress_label = QLabel("Статус обработки:")
        progress_file_label = QLabel("Файл: -")
        self.progress_file_label = progress_file_label

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(progress_file_label)

        right_layout.addLayout(progress_layout, stretch=2)

        main_splitter.addWidget(right_container)
        main_splitter.setStretchFactor(0, 35)
        main_splitter.setStretchFactor(1, 65)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов к работе. Загрузите файлы для обработки.")

        # Подключение сигналов
        self.btn_anonymize.clicked.connect(self.start_anonymization)
        self.btn_deanonymize.clicked.connect(self.deanonymize_window)
        self.btn_settings.clicked.connect(self.show_settings)

    def setup_menu_bar(self):
        menubar = QMenuBar()
        file_menu = menubar.addMenu("Файл")

        select_save_folder_action = file_menu.addAction("Выбрать папку сохранений...")
        select_save_folder_action.triggered.connect(self.select_save_folder_from_main)

        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
        self.setMenuBar(menubar)

    def load_single_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "",
            "Все файлы (*.docx *.pdf *.jpg *.png);;DOCX (*.docx);;PDF (*.pdf);;Изображения (*.jpg *.jpeg *.png)"
        )

        if file_path:
            self.add_file_to_list(file_path)

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")

        if folder_path:
            files_in_folder = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.docx', '.pdf', '.jpg', '.png')):
                        full_path = os.path.join(root, file)
                        files_in_folder.append(full_path)

            self.file_list_widget.clear()
            self.selected_files.clear()

            for f in files_in_folder:
                self.add_file_to_list(f)

    def add_file_to_list(self, file_path):
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self.file_list_widget.addItem(file_path)
            self.update_file_count()
            self.statusbar.showMessage(f"Файл загружен: {file_path}")

    def update_file_count(self):
        self.info_label.setText(f"Загружено файлов: {len(self.selected_files)}")

    # Выбор папки сохранений из главного меню
    def select_save_folder_from_main(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранений результатов"
        )
        if folder_path:
            self.save_folder = folder_path
            QMessageBox.information(self, "Папка", f"Папка сохранений установлена: {folder_path}")

    def start_anonymization(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Внимание",
                                "Выберите файлы для обработки перед запуском!")
            return

        save_info = f"Папка сохранений: {self.save_folder or 'не выбрана'}"

        self.statusbar.showMessage("Начало обработки файлов...")
        self.btn_anonymize.setEnabled(False)

        self.worker = AnonymizeWorker(
            self.selected_files,
            self.settings,
            save_folder=self.save_folder,
            preserve_structure=self.preserve_structure
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_anonymization_finished)
        self.worker.start()

    def update_progress(self, value, text, file_index):
        self.progress_bar.setValue(value)
        self.statusbar.showMessage(text)

        if self.selected_files and file_index <= len(self.selected_files):
            current_file = os.path.basename(self.selected_files[file_index - 1])
            self.progress_file_label.setText(f"Файл: {current_file}")

    def on_anonymization_finished(self, result_data):
        self.progress_bar.setValue(100)
        self.statusbar.showMessage("Обработка завершена")
        self.btn_anonymize.setEnabled(True)

        mapping = result_data.get("mapping", [])

        old_mapping = self.current_mapping.copy()
        self.mapping_table.clearContents()
        self.mapping_table.setRowCount(len(mapping))

        for i, item in enumerate(mapping):
            row = self.mapping_table.rowCount() - 1

            pseudonym_item = QTableWidgetItem(item["pseudonym"])
            if item["pseudonym"] in old_mapping:
                pseudonym_item.setText(old_mapping[item["pseudonym"]])
            self.mapping_table.setItem(row, 0, pseudonym_item)

            original_item = QTableWidgetItem(item["original"])
            original_item.setFlags(original_item.flags() & ~Qt.ItemIsEditable)
            self.mapping_table.setItem(row, 1, original_item)

            category_item = QTableWidgetItem(item["category"])
            self.mapping_table.setItem(row, 2, category_item)

            file_item = QTableWidgetItem(item.get("file", ""))
            self.mapping_table.setItem(row, 3, file_item)

        QMessageBox.information(self, "Готово",
                                f"Обработано файлов: {result_data.get('files_processed', 0)}\n"
                                f"Найдено сущностей: {len(mapping)}")

    def save_mapping_json(self):
        rows = self.mapping_table.rowCount()
        if rows == 0:
            QMessageBox.warning(self, "Внимание", "Нет данных для сохранения.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить карту", "",
            "JSON файл (*.json)"
        )

        if file_path:
            data = []
            for i in range(rows):
                row_data = {
                    "pseudonym": self.mapping_table.item(i, 0).text() if self.mapping_table.item(i, 0) else "",
                    "original": self.mapping_table.item(i, 1).text() if self.mapping_table.item(i, 1) else "",
                    "category": self.mapping_table.item(i, 2).text() if self.mapping_table.item(i, 2) else ""
                }
                data.append(row_data)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "Успех", f"Карта сохранена в: {file_path}")

    def export_to_excel(self):
        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(
                self, "Ошибка",
                "Модуль openpyxl не установлен. Установите: pip install openpyxl"
            )
            return

        rows = self.mapping_table.rowCount()
        if rows == 0:
            QMessageBox.warning(self, "Внимание", "Нет данных для экспорта.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в Excel", "",
            "Excel файл (*.xlsx)"
        )

        if file_path:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Карта соответствий"

            headers = ["Псевдоним", "Исходное значение", "Категория"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = openpyxl.styles.Font(bold=True)

            for i in range(rows):
                row_num = i + 2
                ws.cell(row=row_num, column=1,
                        value=self.mapping_table.item(i, 0).text() if self.mapping_table.item(i, 0) else "")
                ws.cell(row=row_num, column=2,
                        value=self.mapping_table.item(i, 1).text() if self.mapping_table.item(i, 1) else "")
                ws.cell(row=row_num, column=3,
                        value=self.mapping_table.item(i, 2).text() if self.mapping_table.item(i, 2) else "")

            wb.save(file_path)
            QMessageBox.information(self, "Успех", f"Экспорт в Excel выполнен: {file_path}")

    def deanonymize_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Деанонимизация текста")
        dialog.resize(1200, 900)

        layout = QVBoxLayout(dialog)

        text_input = QTextEdit()
        text_input.setPlaceholderText("Вставьте текст для деанонимизации...")
        layout.addWidget(text_input)

        btn_process = QPushButton("Обработать")
        layout.addWidget(btn_process)

        result_label = QLabel("Результат:")
        result_text = QTextEdit()
        result_text.setReadOnly(True)
        layout.addWidget(result_text)

        def process_text():
            text = text_input.toPlainText()
            result_text.setText(f"Текст для обработки: {text}")
            QMessageBox.information(self, "Инфо",
                                    "Модуль деанонимизации будет подключен после интеграции с бэкендом")

        btn_process.clicked.connect(process_text)
        dialog.exec_()

    def show_settings(self):
        """Открытие окна настроек (ИСПРАВЛЕНО)"""
        # Важно: передаем текущие настройки в диалог
        dialog = SettingsDialog(self, initial_settings=self.settings.copy())

        # Устанавливаем сохраненные значения из предыдущих настроек
        if self.save_folder:
            folder_name = os.path.basename(self.save_folder)
            dialog.save_folder_btn.setText(f"Папка: {folder_name}")

        if hasattr(dialog, 'preserve_structure_cb'):
            dialog.preserve_structure_cb.setChecked(self.preserve_structure)

        if dialog.exec_() == QDialog.Accepted:
            # Получаем настройки категорий из диалога
            self.settings = dialog.get_settings()

            # Получаем настройки сохранения
            save_settings = dialog.get_save_settings()
            self.save_folder = save_settings["save_folder"]
            self.preserve_structure = save_settings["preserve_structure"]

            QMessageBox.information(self, "Настройки",
                                    f"Сохранены настройки для категорий: {list(self.settings.keys())}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
