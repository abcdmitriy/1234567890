# storage/map_manager.py
"""
Управление картами соответствия (псевдоним ↔ оригинал).
Позволяет сохранять, загружать, искать и удалять карты.
"""
import os
import json
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.utils import ensure_directory, get_absolute_path, get_filename

class MapManager:
    """
    Менеджер карт анонимизации.
    Хранит карты в папке storage/maps/ (или другой, указанной при инициализации).
    Каждая карта — JSON-файл с метаданными.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        """
        :param storage_dir: папка для хранения карт (по умолчанию ./storage/maps)
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), "storage", "maps")
        self.storage_dir = get_absolute_path(storage_dir)
        ensure_directory(self.storage_dir)

    def save_map(self, mapping: Dict[str, Dict], name: Optional[str] = None,
                 metadata: Optional[Dict] = None, fmt: str = "json") -> str:
        """
        Сохраняет карту в storage с указанным именем.
        :param mapping: словарь {псевдоним: {'original': ..., 'category': ..., 'files': [...]}}
        :param name: имя карты (без расширения). Если не указано, генерируется по времени.
        :param metadata: дополнительные метаданные (например, дата обработки, список файлов)
        :param fmt: формат сохранения (json, xlsx, csv) — пока только json.
        :return: путь к сохранённому файлу
        """
        if name is None:
            name = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if metadata is None:
            metadata = {}

        # Собираем полный объект
        data = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "name": name,
                **metadata
            },
            "mapping": mapping
        }

        # Сохраняем как JSON
        if fmt.lower() != "json":
            raise ValueError("Пока поддерживается только формат JSON для хранения в storage")

        filename = f"{name}.json"
        filepath = os.path.join(self.storage_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def load_map(self, name_or_path: str) -> Dict[str, Dict]:
        """
        Загружает карту по имени (без расширения) или полному пути.
        Возвращает словарь mapping (без метаданных).
        """
        # Если передан полный путь
        if os.path.isfile(name_or_path):
            filepath = name_or_path
        else:
            # Ищем файл с таким именем в storage_dir
            candidates = [f for f in os.listdir(self.storage_dir)
                          if f.startswith(name_or_path) and f.endswith('.json')]
            if not candidates:
                raise FileNotFoundError(f"Карта с именем '{name_or_path}' не найдена в {self.storage_dir}")
            if len(candidates) > 1:
                # Если несколько, возьмём первый (можно уточнить)
                filepath = os.path.join(self.storage_dir, candidates[0])
            else:
                filepath = os.path.join(self.storage_dir, candidates[0])

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ожидаем структуру: {"metadata": {...}, "mapping": {...}}
        if "mapping" in data:
            return data["mapping"]
        else:
            # Если файл старого формата (просто mapping)
            return data

    def list_maps(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех сохранённых карт с метаданными.
        """
        result = []
        for fname in os.listdir(self.storage_dir):
            if fname.endswith('.json'):
                path = os.path.join(self.storage_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    meta = data.get("metadata", {})
                    result.append({
                        "name": meta.get("name", get_filename(fname)),
                        "file": fname,
                        "path": path,
                        "created": meta.get("created"),
                        "size": os.path.getsize(path),
                        "files_count": len(data.get("mapping", {}))
                    })
                except Exception:
                    # Если файл повреждён, пропускаем
                    continue
        return sorted(result, key=lambda x: x.get("created", ""), reverse=True)

    def delete_map(self, name_or_path: str) -> bool:
        """
        Удаляет карту.
        """
        if os.path.isfile(name_or_path):
            filepath = name_or_path
        else:
            # Поиск по имени
            candidates = [f for f in os.listdir(self.storage_dir)
                          if f.startswith(name_or_path) and f.endswith('.json')]
            if not candidates:
                return False
            filepath = os.path.join(self.storage_dir, candidates[0])

        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def get_map_for_file(self, file_path: str) -> Optional[Dict[str, Dict]]:
        """
        Ищет карту, которая содержит записи для данного файла.
        Возвращает mapping или None.
        """
        # Сканируем все карты и проверяем, есть ли упоминание файла
        for fname in os.listdir(self.storage_dir):
            if fname.endswith('.json'):
                path = os.path.join(self.storage_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    mapping = data.get("mapping", {})
                    # Проверяем, есть ли файл в files
                    for alias, info in mapping.items():
                        if file_path in info.get("files", []):
                            return mapping
                except Exception:
                    continue
        return None
