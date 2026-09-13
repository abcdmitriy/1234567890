# core/report_generator.py
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime


class ReportGenerator:
    def generate_report(
        self,
        file_paths: List[str],
        mapping: Dict[str, Dict],
        file_replacements: Dict[str, List[Dict]],
        errors: List[Tuple[str, str]],
        output_dir: str,
        total_replacements_by_category: Dict[str, int],
        map_filename: str = "anonymization-map.json"
    ) -> str:
        total_files = len(file_paths)
        success_files = total_files - len(errors)

        lines = []
        lines.append("Обработано файлов: {}".format(total_files))
        lines.append("Успешно обработано: {}".format(success_files))
        lines.append("Не удалось обработать: {}".format(len(errors)))

        if errors:
            for file_path, err_msg in errors:
                lines.append("  - {}: {}".format(os.path.basename(file_path), err_msg))

        lines.append("")

        if total_replacements_by_category:
            for category, count in sorted(total_replacements_by_category.items()):
                lines.append("  {}: {}".format(category, count))
        else:
            lines.append("  (ничего не найдено)")

        total_replacements = sum(total_replacements_by_category.values()) if total_replacements_by_category else 0
        lines.append("")
        lines.append("Всего замен: {}".format(total_replacements))

        if mapping:
            lines.append("Создана карта соответствия: {}".format(map_filename))
        else:
            lines.append("Карта соответствия не создана (ничего не найдено)")

        lines.append("Обработанные файлы сохранены в папке: {}".format(output_dir))

        return "\n".join(lines)

    def save_report(self, report_text: str, output_path: str) -> None:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

    def save_map(self, mapping: Dict[str, Dict], output_path: str, fmt: str = 'json') -> None:
        """
        Сохраняет карту соответствия в указанном формате.
        Поддерживаемые форматы: json, xlsx, csv.
        Для xlsx требуется openpyxl.
        """
        if fmt == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        elif fmt == 'xlsx':
            try:
                from openpyxl import Workbook
            except ImportError:
                raise ImportError("Для сохранения в XLSX установите openpyxl: pip install openpyxl")
            wb = Workbook()
            ws = wb.active
            ws.title = "Карта соответствия"
            ws.append(["Псевдоним", "Исходное значение", "Категория", "Документы"])
            for alias, info in mapping.items():
                ws.append([
                    alias,
                    info['original'],
                    info['category'],
                    ", ".join(info['files'])
                ])
            wb.save(output_path)
        elif fmt == 'csv':
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Псевдоним", "Исходное значение", "Категория", "Документы"])
                for alias, info in mapping.items():
                    writer.writerow([
                        alias,
                        info['original'],
                        info['category'],
                        ", ".join(info['files'])
                    ])
        else:
            raise ValueError("Неизвестный формат: {}".format(fmt))