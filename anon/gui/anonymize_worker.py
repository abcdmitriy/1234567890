# gui/anonymize_worker.py
import os
from PyQt5.QtCore import QThread, pyqtSignal

from core.pipeline import run_pipeline

class AnonymizeWorker(QThread):
    progress = pyqtSignal(int, str, int)
    finished = pyqtSignal(dict)

    def __init__(self, files, settings, save_folder=None, preserve_structure=False):
        super().__init__()
        self.files = files
        self.settings = settings
        self.save_folder = save_folder or "./output"
        self.preserve_structure = preserve_structure

    def run(self):
        try:
            mapping, file_replacements, errors, total_by_category = run_pipeline(
                file_paths=self.files,
                output_dir=self.save_folder,
                settings=self.settings,
                map_formats=[],
                output_format='txt',
                keep_structure=self.preserve_structure
            )

            result = {
                "mapping": mapping,
                "file_replacements": file_replacements,
                "errors": errors,
                "total_by_category": total_by_category,
                "files_processed": len(self.files),
                "save_folder": self.save_folder,
                "preserve_structure": self.preserve_structure
            }

            self.progress.emit(100, "Обработка завершена", len(self.files))

        except Exception as e:
            self.finished.emit({
                "error": str(e),
                "files_processed": 0,
                "mapping": {},
                "file_replacements": {},
                "errors": [(f"Ошибка: {e}", "")]
            })
            return

        self.finished.emit(result)
