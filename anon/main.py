#!/usr/bin/env python3
# main.py
import os
import sys
import argparse

from core.pipeline import run_pipeline
from core.utils import ensure_directory


def main():
    parser = argparse.ArgumentParser(description="Анонимизация документов перед загрузкой в ИИ")
    parser.add_argument("paths", nargs="+", help="Пути к файлам или папкам")
    parser.add_argument("-o", "--output", default="./output", help="Папка для сохранения результатов")
    parser.add_argument("-f", "--format", default="txt", choices=["docx", "txt", "pdf", "image"],
                        help="Формат выходных файлов (по умолчанию txt)")
    parser.add_argument("--map-formats", nargs="+", default=["json", "xlsx", "csv"],
                        help="Форматы для сохранения карты (json, xlsx, csv)")
    parser.add_argument("--no-recursive", action="store_true", help="Не обрабатывать подпапки")
    parser.add_argument("--no-ner", action="store_true", help="Отключить NER")
    parser.add_argument("--no-address", action="store_true", help="Отключить поиск адресов")
    parser.add_argument("--no-tables", action="store_true", help="Игнорировать таблицы (пока не реализовано)")
    args = parser.parse_args()

    settings = {
        'recursive': not args.no_recursive,
        'use_ner': not args.no_ner,
        'use_address': not args.no_address,
    }

    mapping, file_replacements, errors, total_by_category = run_pipeline(
        file_paths=args.paths,
        output_dir=args.output,
        settings=settings,
        map_formats=args.map_formats,
        output_format=args.format,
        keep_structure=True
    )

    print(f"\nОбработка завершена. Отчёт сохранён в {os.path.join(args.output, 'report.txt')}")
    print(f"Всего файлов: {len(args.paths)}, успешно: {len(args.paths) - len(errors)}, ошибок: {len(errors)}")
    if errors:
        print("Список ошибок:")
        for f, e in errors:
            print(f"  - {os.path.basename(f)}: {e}")


if __name__ == "__main__":
    main()