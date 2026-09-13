# core/utils.py
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def normalize_text(text: str) -> str:
    """
    Приводит текст к нормализованному виду:
    - убирает лишние пробелы
    - приводит к нижнему регистру
    - удаляет символы пунктуации (опционально)
    """
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    # Приводим к нижнему регистру
    text = text.lower()
    return text


def get_file_extension(file_path: str) -> str:
    """Возвращает расширение файла в нижнем регистре (с точкой)."""
    return os.path.splitext(file_path)[1].lower()


def get_file_type(file_path: str) -> Optional[str]:
    """
    Определяет тип файла по расширению.
    Возвращает: 'docx', 'pdf', 'jpg', 'jpeg', 'png' или None.
    """
    ext = get_file_extension(file_path)
    mapping = {
        '.docx': 'docx',
        '.pdf': 'pdf',
        '.jpg': 'jpg',
        '.jpeg': 'jpeg',
        '.png': 'png',
        '.txt': 'txt',
        '.rtf': 'rtf',
    }
    return mapping.get(ext)


def ensure_directory(path: str) -> None:
    """Создаёт все папки по указанному пути, если их нет."""
    os.makedirs(path, exist_ok=True)


def safe_open_file(file_path: str, mode: str = 'r', encoding: str = 'utf-8'):
    """
    Безопасно открывает файл, обрабатывая ошибки.
    Возвращает файловый объект или выбрасывает исключение с понятным сообщением.
    """
    try:
        return open(file_path, mode, encoding=encoding)
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    except PermissionError:
        raise PermissionError(f"Нет доступа к файлу: {file_path}")
    except Exception as e:
        raise IOError(f"Ошибка открытия файла {file_path}: {e}")


def load_json(file_path: str) -> Dict[str, Any]:
    """Загружает JSON-файл и возвращает словарь."""
    with safe_open_file(file_path, 'r') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """Сохраняет данные в JSON-файл с красивым форматированием."""
    ensure_directory(os.path.dirname(file_path))
    with safe_open_file(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def get_absolute_path(path: str) -> str:
    """Преобразует относительный путь в абсолютный."""
    return os.path.abspath(path)


def join_paths(*paths: str) -> str:
    """Склеивает части пути."""
    return os.path.join(*paths)


def get_filename(file_path: str) -> str:
    """Возвращает имя файла без расширения."""
    return os.path.splitext(os.path.basename(file_path))[0]


def get_basename(file_path: str) -> str:
    """Возвращает имя файла с расширением."""
    return os.path.basename(file_path)


def is_supported_format(file_path: str) -> bool:
    """Проверяет, поддерживается ли формат файла."""
    return get_file_type(file_path) is not None


def list_files_in_folder(folder_path: str, recursive: bool = False, supported_only: bool = True) -> List[str]:
    """
    Возвращает список файлов в папке (и подпапках, если recursive=True).
    Если supported_only=True, то возвращает только поддерживаемые форматы.
    """
    files = []
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Папка не найдена: {folder_path}")

    if recursive:
        for root, _, filenames in os.walk(folder_path):
            for f in filenames:
                full_path = os.path.join(root, f)
                if supported_only and not is_supported_format(full_path):
                    continue
                files.append(full_path)
    else:
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                if supported_only and not is_supported_format(full_path):
                    continue
                files.append(full_path)
    return files


def get_output_path(input_path: str, output_dir: str, suffix: str = '_anon') -> str:
    """
    Генерирует путь для сохранения обработанного файла.
    Добавляет суффикс к имени файла перед расширением.
    """
    basename = get_filename(input_path)
    ext = get_file_extension(input_path)
    new_name = f"{basename}{suffix}{ext}"
    return os.path.join(output_dir, new_name)