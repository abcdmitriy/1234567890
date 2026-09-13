# gui/deanon_window.py
import html
import os
import re
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent, QTextCursor
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
    QFileDialog, QPushButton
)

from core.processors.deanon import Deanon
from storage.map_manager import MapManager


class DeanonWindow(QDialog):
    def __init__(self, parent=None, map_manager=None, last_mapping=None, last_map_path=None, stylesheet_fn=None):
        super().__init__(parent)
        self.setWindowTitle("Деанонимизация")
        self.resize(1200, 700)

        self.map_manager = map_manager or MapManager()
        self.stylesheet_fn = stylesheet_fn or (lambda: "")
        self.setStyleSheet(self.stylesheet_fn())

        self.last_mapping = last_mapping or {}
        self.last_map_path = last_map_path
        self.reverse_map = {}
        self.map_source_name = "Карта не загружена"
        self.loaded_file_path = None

        self.create_ui()
        self._load_last_map()
        self.setup_drag_drop()

    def create_ui(self):
        main_layout = QVBoxLayout(self)

        top_buttons = QHBoxLayout()
        self.btn_load_map = QPushButton("Загрузить карту")
        self.btn_deanon = QPushButton("Деанонимизировать")
        self.btn_save = QPushButton("Сохранить результат")
        self.btn_save.setEnabled(False)

        self.btn_load_map.clicked.connect(self.load_map_dialog)
        self.btn_deanon.clicked.connect(self.process_deanon)
        self.btn_save.clicked.connect(self.save_result)

        top_buttons.addWidget(self.btn_load_map)
        top_buttons.addWidget(self.btn_deanon)
        top_buttons.addWidget(self.btn_save)
        main_layout.addLayout(top_buttons)

        self.status_label = QLabel("Карта не загружена")
        self.status_label.setStyleSheet("color: #475569; margin-bottom: 8px; font-weight: 500;")
        main_layout.addWidget(self.status_label)

        fields_container = QWidget()
        fields_layout = QHBoxLayout(fields_container)
        fields_layout.setContentsMargins(0, 0, 0, 0)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Перетащите файл (txt, docx, pdf) или начните печатать")
        self.text_input.setStyleSheet(
            "QTextEdit { color: #111827; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px; }"
        )
        left_layout.addWidget(self.text_input)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Результат после деанонимизации")
        self.result_text.setStyleSheet(
            "QTextEdit { color: #111827; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px; }"
        )
        right_layout.addWidget(self.result_text)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        fields_layout.addWidget(splitter)
        main_layout.addWidget(fields_container, stretch=1)

        self.text_input.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextEditable | Qt.TextSelectableByKeyboard)
        self.result_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.text_input.installEventFilter(self)
        self.result_text.installEventFilter(self)
        self.text_input.textChanged.connect(self._on_source_changed)

        self._scroll_sync_lock = False
        self.text_input.verticalScrollBar().valueChanged.connect(
            lambda value: self._sync_vertical_scroll(self.text_input, self.result_text)
        )
        self.result_text.verticalScrollBar().valueChanged.connect(
            lambda value: self._sync_vertical_scroll(self.result_text, self.text_input)
        )

        self.current_masked_text = ""
        self.current_decoded_text = ""
        self.entity_pairs = []
        self.entity_occurrences = {}
        self.active_pair_id = None

    def setup_drag_drop(self):
        self.text_input.setAcceptDrops(True)
        self.text_input.viewport().setAcceptDrops(True)
        self.text_input.dragEnterEvent = self.drag_enter_event
        self.text_input.dragMoveEvent = self.drag_move_event
        self.text_input.dropEvent = self.drop_event

    def eventFilter(self, obj, event):
        if obj not in (self.text_input, self.result_text):
            return super().eventFilter(obj, event)

        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            return super().eventFilter(obj, event)

        if event.type() == QEvent.MouseButtonRelease:
            if not self.entity_pairs:
                return super().eventFilter(obj, event)

            anchor = obj.anchorAt(event.pos())
            if anchor.startswith('entity:'):
                pair_id = anchor.split(':', 1)[1]
                if self.active_pair_id != pair_id:
                    self.active_pair_id = pair_id
                    self._render_entity_highlights()
                return True

            if self.active_pair_id is not None:
                self.active_pair_id = None
                self._render_entity_highlights()

        return super().eventFilter(obj, event)

    def _sync_vertical_scroll(self, source_editor, target_editor):
        if self._scroll_sync_lock:
            return

        source_scrollbar = source_editor.verticalScrollBar()
        target_scrollbar = target_editor.verticalScrollBar()

        source_max = source_scrollbar.maximum()
        target_max = target_scrollbar.maximum()
        if source_max <= 0 or target_max <= 0:
            return

        ratio = source_scrollbar.value() / source_max
        target_value = int(round(ratio * target_max))

        self._scroll_sync_lock = True
        target_scrollbar.setValue(target_value)
        self._scroll_sync_lock = False

    def _on_source_changed(self):
        if getattr(self, '_suspend_source_change', False):
            return

        self._suspend_source_change = True
        try:
            self.entity_pairs = []
            self.entity_occurrences = {}
            self.active_pair_id = None
            self.current_masked_text = self.text_input.toPlainText()
            self.result_text.setReadOnly(True)
            current_result = self.current_decoded_text or self.result_text.toPlainText()
            self.result_text.setHtml(self._render_plain_text(current_result))
            self.btn_save.setEnabled(bool(current_result.strip()))
            self.loaded_file_path = None
        finally:
            self._suspend_source_change = False

    def drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()
            event.accept()
            self.text_input.setStyleSheet(
                "QTextEdit { color: #111827; border: 2px solid #3b82f6; background: #eff6ff; border-radius: 10px; padding: 8px; }"
            )
        else:
            event.ignore()

    def drag_move_event(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()
            event.accept()
            self.text_input.setStyleSheet(
                "QTextEdit { color: #111827; border: 2px solid #3b82f6; background: #eff6ff; border-radius: 10px; padding: 8px; }"
            )
        else:
            event.ignore()

    def drop_event(self, event: QDropEvent):
        self.text_input.setStyleSheet(
            "QTextEdit { color: #111827; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px; }"
        )
        urls = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        if urls:
            self.load_files(urls)
            event.acceptProposedAction()
            event.accept()
        else:
            event.ignore()

    def _read_file_text(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        if ext == '.docx':
            from core.parsers.docx_parser import DOCXParser
            parser = DOCXParser()
            doc = parser.parse(file_path)
            chunks = []
            for page in doc.pages:
                for para in page.paragraphs:
                    text = ''.join(fragment.text for fragment in para.fragments)
                    if text.strip():
                        chunks.append(text.strip())
                for table in page.tables:
                    for row in table.rows:
                        for cell in row:
                            for para in cell.paragraphs:
                                text = ''.join(fragment.text for fragment in para.fragments)
                                if text.strip():
                                    chunks.append(text.strip())
            return '\n'.join(chunks)

        if ext == '.pdf':
            from core.parsers.pdf_parser import PDFParser
            parser = PDFParser()
            doc = parser.parse(file_path)
            chunks = []
            for page in doc.pages:
                for para in page.paragraphs:
                    text = ''.join(fragment.text for fragment in para.fragments)
                    if text.strip():
                        chunks.append(text.strip())
            return '\n'.join(chunks)

        raise ValueError(f"Неподдерживаемый формат файла: {ext or 'без расширения'}")

    def load_files(self, file_paths):
        if not file_paths:
            return

        file_path = file_paths[0]
        if not os.path.isfile(file_path):
            QMessageBox.warning(self, "Ошибка", "Указанный файл не найден.")
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in {'.txt', '.docx', '.pdf'}:
            QMessageBox.warning(self, "Ошибка", "Поддерживаются только файлы .txt, .docx и .pdf")
            return

        try:
            text = self._read_file_text(file_path)
            self.loaded_file_path = file_path
            self.text_input.setPlainText(text)
            self.result_text.clear()
            self.btn_save.setEnabled(False)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка чтения файла", str(exc))

    def _load_last_map(self):
        try:
            if self.last_mapping:
                self.reverse_map = Deanon().load_map_from_data(self.last_mapping)
                self.map_source_name = "последняя созданная"
                self.update_status_label()
                return

            if self.last_map_path and os.path.exists(self.last_map_path):
                self.reverse_map = Deanon().load_map(self.last_map_path)
                self.map_source_name = "последняя созданная"
                self.update_status_label()
                return

            maps = self.map_manager.list_maps()
            if maps:
                latest_path = maps[0].get('path')
                if latest_path and os.path.exists(latest_path):
                    self.reverse_map = Deanon().load_map(latest_path)
                    self.map_source_name = "последняя созданная"
                    self.update_status_label()
                    return
        except Exception:
            pass

        self.reverse_map = {}
        self.map_source_name = "Карта не загружена"
        self.update_status_label()

    def update_status_label(self):
        if self.reverse_map:
            self.status_label.setText(f"Карта: {self.map_source_name}")
        else:
            self.status_label.setText("Карта не загружена")

    def load_map_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите карту соответствия",
            "",
            "JSON файлы (*.json)"
        )
        if not file_path:
            return

        try:
            self.reverse_map = Deanon().load_map(file_path)
            self.map_source_name = os.path.basename(file_path)
            self.update_status_label()
            QMessageBox.information(self, "Карта загружена", f"Выбрана карта: {os.path.basename(file_path)}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка карты", f"Не удалось загрузить карту: {exc}")


    def _build_entity_pairs(self, masked_text, decoded_text, reverse_map):
        pairs = []
        seen = set()
        for alias, original in sorted(reverse_map.items(), key=lambda item: len(str(item[0])), reverse=True):
            alias_text = str(alias)
            original_text = str(original)
            if not alias_text or not original_text or alias_text not in masked_text:
                continue
            key = (alias_text, original_text)
            if key in seen:
                continue
            seen.add(key)
            pairs.append({
                'id': f'entity_{len(pairs) + 1}',
                'mask': alias_text,
                'original': original_text,
            })
        return pairs

    def _build_entity_occurrences(self, masked_text, decoded_text, pairs):
        occurrences = {}
        for pair in pairs:
            occurrences[pair['id']] = {'left': [], 'right': []}
            for field_name, token, text in [
                ('left', pair['mask'], masked_text),
                ('right', pair['original'], decoded_text),
            ]:
                start = 0
                while True:
                    index = text.find(token, start)
                    if index == -1:
                        break
                    occurrences[pair['id']][field_name].append((index, index + len(token)))
                    start = index + len(token)
        return occurrences

    def _render_plain_text(self, raw_text):
        if not raw_text:
            return ""
        return f"<span style='color:#111827;'>{html.escape(raw_text).replace(chr(10), '<br>')}</span>"

    def _entity_style(self, pair_id):
        if self.active_pair_id == pair_id:
            return "background:#dbeafe; color:#1e3a8a; border:1px solid #93c5fd; border-radius:6px; padding:0 3px; font-weight:700; display:inline; text-decoration:none;"
        return "background:#fef3c7; color:#78350f; border-radius:6px; padding:0 3px; font-weight:700; display:inline; text-decoration:none;"

    def _render_plain_text(self, raw_text):
        if raw_text is None:
            return ""
        escaped = html.escape(raw_text).replace(' ', '&nbsp;').replace('\n', '<br>')
        return f"<span style='color:#111827;'>{escaped}</span>"

    def _render_side_html(self, raw_text, side):
        if not raw_text:
            return ""

        relevant_tokens = []
        for pair in self.entity_pairs:
            token = pair['mask'] if side == 'left' else pair['original']
            if token and token in raw_text:
                relevant_tokens.append((token, pair['id']))

        if not relevant_tokens:
            return self._render_plain_text(raw_text)

        pattern = re.compile('|'.join(re.escape(token) for token, _ in sorted(relevant_tokens, key=lambda item: len(item[0]), reverse=True)))
        parts = []
        cursor = 0
        for match in pattern.finditer(raw_text):
            start, end = match.span()
            if start > cursor:
                parts.append(self._render_plain_text(raw_text[cursor:start]))

            token = match.group(0)
            pair_id = None
            for candidate_token, candidate_id in relevant_tokens:
                if token == candidate_token:
                    pair_id = candidate_id
                    break

            if pair_id is None:
                parts.append(self._render_plain_text(token))
            else:
                style = self._entity_style(pair_id)
                parts.append(f"<a href='entity:{pair_id}' style='text-decoration:none; color:inherit;'><span style='{style}'>{html.escape(token)}</span></a>")
            cursor = end

        if cursor < len(raw_text):
            parts.append(self._render_plain_text(raw_text[cursor:]))

        return ''.join(parts)

    def _render_entity_highlights(self):
        if not self.current_masked_text and not self.current_decoded_text:
            self.text_input.clear()
            self.result_text.clear()
            return

        self.text_input.setHtml(self._render_side_html(self.current_masked_text, 'left'))
        self.result_text.setHtml(self._render_side_html(self.current_decoded_text, 'right'))

    def process_deanon(self):
        source_text = self.text_input.toPlainText().strip()
        if not source_text:
            QMessageBox.warning(self, "Внимание", "Загрузите файл или введите текст для деанонимизации.")
            return

        map_to_use = self.reverse_map
        if not map_to_use and self.last_mapping:
            map_to_use = Deanon().load_map_from_data(self.last_mapping)
        
        if not map_to_use:
            try:
                maps = self.map_manager.list_maps()
                if maps:
                    latest_map = self.map_manager.load_map(maps[0].get('path'))
                    map_to_use = Deanon().load_map_from_data(latest_map)
                    self.reverse_map = map_to_use
                    self.map_source_name = "последняя созданная"
                    self.update_status_label()
            except Exception:
                pass

        if not map_to_use:
            QMessageBox.warning(self, "Внимание", "Карта соответствия не загружена.")
            return

        try:
            decoded_text = Deanon().deanon_text(source_text, map_to_use)
            self.current_masked_text = source_text
            self.current_decoded_text = decoded_text
            self.entity_pairs = self._build_entity_pairs(source_text, decoded_text, map_to_use)
            self.entity_occurrences = self._build_entity_occurrences(source_text, decoded_text, self.entity_pairs)
            self.active_pair_id = None
            self.result_text.setReadOnly(True)

            self._suspend_source_change = True
            try:
                self._render_entity_highlights()
            finally:
                self._suspend_source_change = False

            self.btn_save.setEnabled(bool(decoded_text.strip()))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Ошибка деанонимизации: {exc}")

    def save_result(self):
        result_text = self.result_text.toPlainText().strip()
        if not result_text:
            self.btn_save.setEnabled(False)
            QMessageBox.warning(self, "Внимание", "Сначала выполните деанонимизацию.")
            return

        self.btn_save.setEnabled(True)

        default_name = "deanon_result.txt"
        if self.loaded_file_path:
            default_name = f"{os.path.splitext(os.path.basename(self.loaded_file_path))[0]}_deanon.txt"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат деанонимизации",
            default_name,
            "Текстовые файлы (*.txt)"
        )
        if not save_path:
            return

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(result_text)
            QMessageBox.information(self, "Успех", f"Файл сохранён:\n{save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {exc}")

