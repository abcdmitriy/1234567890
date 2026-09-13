# storage/file_handler.py
"""
Работа с файлами в процессе анонимизации: копирование, перемещение,
сохранение структуры папок, создание бекапов.
"""
import os
import shutil
from typing import List, Optional

from core.utils import ensure_directory, get_absolute_path, get_basename, get_file_extension

class FileHandler:
    """
    Обрабатывает операции с файлами: копирование с сохранением структуры,
    проверка поддерживаемых форматов, создание резервных копий.
    """
    SUPPORTED_EXTENSIONS = {'.docx', '.pdf', '.jpg', '.jpeg', '.png', '.txt'}

    def __init__(self, base_dir: Optional[str] = None):
        """
        :param base_dir: корневая папка для операций (если требуется)
        """
        self.base_dir = get_absolute_path(base_dir) if base_dir else None

    def copy_with_structure(self, src: str, dst_root: str, preserve_path: bool = True) -> str:
        """
        Копирует файл в dst_root, сохраняя относительную структуру папок,
        если preserve_path=True.
        :param src: исходный путь
        :param dst_root: корень назначения
        :param preserve_path: сохранять ли относительный путь от base_dir (если задан)
        :return: путь к скопированному файлу
        """
        src_abs = get_absolute_path(src)
        if not os.path.isfile(src_abs):
            raise FileNotFoundError(f"Файл не найден: {src_abs}")

        if preserve_path and self.base_dir:
            # Относительный путь от base_dir
            rel_path = os.path.relpath(src_abs, self.base_dir)
            dst_path = os.path.join(dst_root, rel_path)
        else:
            # Копируем прямо в корень
            dst_path = os.path.join(dst_root, get_basename(src_abs))

        # Создаём папки
        ensure_directory(os.path.dirname(dst_path))

        # Копируем
        shutil.copy2(src_abs, dst_path)
        return dst_path

    def move_to_processed(self, src: str, processed_root: str, preserve_path: bool = True) -> str:
        """
        Перемещает файл в папку обработанных (например, после анонимизации).
        """
        src_abs = get_absolute_path(src)
        if not os.path.isfile(src_abs):
            raise FileNotFoundError(f"Файл не найден: {src_abs}")

        if preserve_path and self.base_dir:
            rel_path = os.path.relpath(src_abs, self.base_dir)
            dst_path = os.path.join(processed_root, rel_path)
        else:
            dst_path = os.path.join(processed_root, get_basename(src_abs))

        ensure_directory(os.path.dirname(dst_path))
        shutil.move(src_abs, dst_path)
        return dst_path

    def create_backup(self, src: str, backup_root: str) -> str:
        """
        Создаёт резервную копию файла с добавлением временной метки.
        """
        src_abs = get_absolute_path(src)
        if not os.path.isfile(src_abs):
            raise FileNotFoundError(f"Файл не найден: {src_abs}")

        base = get_basename(src_abs)
        name, ext = os.path.splitext(base)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_root, backup_name)

        ensure_directory(os.path.dirname(backup_path))
        shutil.copy2(src_abs, backup_path)
        return backup_path

    def get_supported_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Возвращает список файлов с поддерживаемыми расширениями в указанной папке.
        """
        results = []
        if recursive:
            for root, _, files in os.walk(directory):
                for f in files:
                    ext = get_file_extension(f)
                    if ext in self.SUPPORTED_EXTENSIONS:
                        results.append(os.path.join(root, f))
        else:
            for f in os.listdir(directory):
                full = os.path.join(directory, f)
                if os.path.isfile(full):
                    ext = get_file_extension(f)
                    if ext in self.SUPPORTED_EXTENSIONS:
                        results.append(full)
        return results

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Проверяет, поддерживается ли расширение файла."""
        ext = get_file_extension(file_path)
        return ext in cls.SUPPORTED_EXTENSIONS
