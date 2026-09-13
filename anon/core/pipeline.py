# core/pipeline.py
"""
Единый пайплайн обработки документов.
Используется как CLI (main.py), так и GUI (gui/anonymize_worker.py).
"""
import os
import sys
from typing import List, Dict, Tuple

from core.parsers.docx_parser import DOCXParser
from core.parsers.pdf_parser import PDFParser
from core.parsers.image_parser import ImageParser
from core.detectors.detector_manager import DetectorManager
from core.processors.mapper import GlobalMapper
from core.processors.replacer import Replacer
from core.report_generator import ReportGenerator
from core.utils import (
    get_file_type,
    get_filename,
    get_output_path,
    ensure_directory,
    list_files_in_folder,
    is_supported_format,
)

def _build_output_path(file_path: str, output_dir: str, output_format: str, keep_structure: bool, all_files: List[str]) -> str:
    base_name = get_filename(file_path)
    ext = '.' + output_format if output_format != 'image' else os.path.splitext(file_path)[1]
    if output_format == 'image':
        ext = os.path.splitext(file_path)[1]

    if keep_structure and all_files:
        root = os.path.commonpath(all_files)
        rel_path = os.path.relpath(file_path, root)
        rel_dir = os.path.dirname(rel_path)
        target_dir = os.path.join(output_dir, rel_dir) if rel_dir and rel_dir != '.' else output_dir
        os.makedirs(target_dir, exist_ok=True)
        name = os.path.splitext(os.path.basename(file_path))[0]
        unique_name = f"{name}_anon{ext}"
        candidate = os.path.join(target_dir, unique_name)
        index = 1
        while os.path.exists(candidate):
            candidate = os.path.join(target_dir, f"{name}_anon_{index}{ext}")
            index += 1
        return candidate

    candidate = os.path.join(output_dir, f"{base_name}_anon{ext}")
    index = 1
    while os.path.exists(candidate):
        candidate = os.path.join(output_dir, f"{base_name}_anon_{index}{ext}")
        index += 1
    return candidate


def run_pipeline(
    file_paths: List[str],
    output_dir: str,
    settings: Dict,
    map_formats: List[str] = None,
    output_format: str = 'txt',
    keep_structure: bool = False
) -> Tuple[Dict, Dict, List[Tuple[str, str]], Dict[str, int]]:
    """
    Основной пайплайн обработки.
    Возвращает: (mapping, file_replacements, errors, total_by_category)
    """
    if map_formats is None:
        map_formats = ['json']

    # Инициализация
    detector_manager = DetectorManager(settings)
    mapper = GlobalMapper()
    replacer = Replacer()
    report_gen = ReportGenerator()

    # Сбор всех файлов (поддерживаемые форматы)
    all_files = []
    for path in file_paths:
        if os.path.isdir(path):
            all_files.extend(list_files_in_folder(path, recursive=settings.get('recursive', True)))
        else:
            if is_supported_format(path):
                all_files.append(path)
            else:
                print(f"Предупреждение: неподдерживаемый формат: {path}")

    if not all_files:
        print("Нет поддерживаемых файлов для обработки.")
        return {}, {}, [], {}

    # Обработка
    errors = []
    try:
        mapping, file_replacements, file_docs = mapper.build_mapping(
            all_files,
            detector_manager,
            settings
        )
    except Exception as e:
        print(f"Критическая ошибка в маппере: {e}")
        raise

    # Создаём выходную папку
    ensure_directory(output_dir)

    # Сохраняем обработанные файлы
    for file_path, replacements in file_replacements.items():
        try:
            file_type = get_file_type(file_path)
            if file_type not in ['docx', 'pdf', 'jpg', 'jpeg', 'png']:
                continue

            model = file_docs.get(file_path)
            if model is None:
                parser = mapper.parsers.get('.' + file_type)
                if not parser:
                    continue
                model = parser.parse(file_path)

            output_path = _build_output_path(file_path, output_dir, output_format, keep_structure, all_files)

            replacer.replace(
                model=model,
                replacements=replacements,
                original_path=file_path,
                output_path=output_path,
                output_format=output_format
            )
        except Exception as e:
            errors.append((file_path, str(e)))

    # Сохраняем карту соответствия
    for fmt in map_formats:
        try:
            map_path = os.path.join(output_dir, f"anonymization-map.{fmt}")
            report_gen.save_map(mapping, map_path, fmt=fmt)
        except Exception as e:
            print(f"Не удалось сохранить карту в {fmt}: {e}")

    # Генерация и сохранение отчёта
    total_by_category = {}
    for fpath, reps in file_replacements.items():
        for r in reps:
            cat = r['category']
            total_by_category[cat] = total_by_category.get(cat, 0) + 1

    report_text = report_gen.generate_report(
        file_paths=all_files,
        mapping=mapping,
        file_replacements=file_replacements,
        errors=errors,
        output_dir=output_dir,
        total_replacements_by_category=total_by_category,
        map_filename="anonymization-map.json"
    )

    report_path = os.path.join(output_dir, "report.txt")
    report_gen.save_report(report_text, report_path)

    return mapping, file_replacements, errors, total_by_category
