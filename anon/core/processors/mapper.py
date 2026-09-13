# core/mapper.py
import os
from typing import List, Dict, Tuple, DefaultDict
from collections import defaultdict

from core.base_parser import InternalDocument
from core.parsers.docx_parser import DOCXParser
from core.parsers.pdf_parser import PDFParser
from core.parsers.image_parser import ImageParser
from core.detectors.detector_manager import DetectorManager


class GlobalMapper:
    def __init__(self):
        self.parsers = {
            '.docx': DOCXParser(),
            '.pdf': PDFParser(),
            '.jpg': ImageParser(),
            '.jpeg': ImageParser(),
            '.png': ImageParser(),
        }

    def build_mapping(
        self,
        file_paths: List[str],
        detector_manager: DetectorManager,
        settings: dict
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Возвращает:
        - mapping: {псевдоним: {'original': str, 'category': str, 'files': List[str]}}
        - file_replacements: {file_path: [{'start': int, 'end': int, 'value': str, 'category': str, 'alias': str}]}
        - file_docs: {file_path: InternalDocument}
        """
        all_entities = []
        file_docs = {}

        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()
            parser = self.parsers.get(ext)
            if not parser:
                continue

            try:
                doc = parser.parse(file_path)
                file_docs[file_path] = doc
                entities = self._detect_entities_in_document(doc, detector_manager)
                for ent in entities:
                    all_entities.append({
                        'file': file_path,
                        'value': ent['value'],
                        'category': ent['category'],
                        'start': ent['start'],
                        'end': ent['end']
                    })
            except Exception:
                continue

        groups: DefaultDict[tuple, dict] = defaultdict(lambda: {'files': set(), 'values': [], 'category': None})
        for ent in all_entities:
            norm_val = self._normalize(ent['value'])
            key = (norm_val, ent['category'])
            groups[key]['files'].add(ent['file'])
            groups[key]['values'].append(ent)
            groups[key]['category'] = ent['category']

        counters = defaultdict(int)
        mapping = {}
        file_replacements = defaultdict(list)

        for (norm_val, category), data in groups.items():
            counters[category] += 1
            alias = self._make_alias(category, counters[category])
            original = data['values'][0]['value']
            mapping[alias] = {
                'original': original,
                'category': category,
                'files': list(data['files'])
            }

            for ent in data['values']:
                file_replacements[ent['file']].append({
                    'start': ent['start'],
                    'end': ent['end'],
                    'value': ent['value'],
                    'category': category,
                    'alias': alias
                })

        return mapping, dict(file_replacements), file_docs

    def _detect_entities_in_document(self, doc: InternalDocument, detector_manager: DetectorManager):
        entities = []
        for page in doc.pages:
            for para in page.paragraphs:
                text = ''.join(f.text for f in para.fragments)
                if not text:
                    continue
                for ent in detector_manager.detect(text):
                    entities.append({
                        'value': ent['value'],
                        'category': ent['category'],
                        'start': ent['start'],
                        'end': ent['end'],
                    })
            for table in page.tables:
                for row in table.rows:
                    for cell in row:
                        for para in cell.paragraphs:
                            text = ''.join(f.text for f in para.fragments)
                            if not text:
                                continue
                            for ent in detector_manager.detect(text):
                                entities.append({
                                    'value': ent['value'],
                                    'category': ent['category'],
                                    'start': ent['start'],
                                    'end': ent['end'],
                                })
        return entities

    def _extract_text(self, doc: InternalDocument) -> str:
        full = ""
        for page in doc.pages:
            for para in page.paragraphs:
                full += " ".join(f.text for f in para.fragments) + " "
            for table in page.tables:
                for row in table.rows:  # row — список Cell
                    for cell in row:  # просто итерируем по row
                        for para in cell.paragraphs:
                            full += " ".join(f.text for f in para.fragments) + " "
        return full

    def _normalize(self, text: str) -> str:
        # Удаляем лишние пробелы, приводим к нижнему регистру
        return ' '.join(text.lower().split())

    def _make_alias(self, category: str, number: int) -> str:
        mapping = {
            'PHONE': 'Phone',
            'EMAIL': 'Email',
            'PASSPORT': 'Passport',
            'INN': 'INN',
            'BANK_ACCOUNT': 'BankAccount',
            'BIC': 'BIC',
            'DEPT_CODE': 'DeptCode',
            'PERSON': 'Person',
            'ORG': 'Org',
            'ADDRESS': 'Address'
        }
        prefix = mapping.get(category, category.capitalize())
        return f"[{prefix}_{number}]"