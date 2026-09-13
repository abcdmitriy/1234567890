from core.detectors.regex_detectors import SensitiveDataDetector
from core.detectors.ner_detector import NERDetector
from core.detectors.address_detector import AddressDetector
from core.base_parser import InternalDocument, Page, Paragraph, TextFragment
from typing import List, Dict

class DetectorManager:
    def __init__(self, settings: dict = None):
        self.settings = settings or {}
        self.regex_detector = SensitiveDataDetector()
        self.ner_detector = NERDetector()
        self.address_detector = AddressDetector()

    def detect(self, text: str):
        page = Page(number=0)
        page.paragraphs.append(Paragraph(fragments=[TextFragment(text=text)]))
        doc = InternalDocument(pages=[page])

        all_results = []

        regex_results = self.regex_detector.detect(doc)
        all_results.extend(regex_results)

        ner_results = self.ner_detector.find_entities(text)
        all_results.extend(ner_results)

        address_results = self.address_detector.find_addresses(text)
        all_results.extend(address_results)

        # ---- ФИЛЬТРАЦИЯ ПО НАСТРОЙКАМ (НОВЫЙ МАППИНГ) ----
        if self.settings:
            category_mapping = {
                'PHONE': 'phones',
                'EMAIL': 'emails',
                'PASSPORT': 'passport_series',
                'DEPT_CODE': 'passport_code',
                'INN': 'inn',
                'BANK_ACCOUNT': 'bank_account',
                'BIC': 'bic',
                'PERSON': 'fio',
                'ORG': 'org',
                'ADDRESS': 'addresses',
            }
            filtered = []
            for item in all_results:
                cat = item.get('category')
                if cat in category_mapping:
                    settings_key = category_mapping[cat]
                    if self.settings.get(settings_key, True):
                        filtered.append(item)
                else:
                    # Если категория не маппится (например, USER), оставляем
                    filtered.append(item)
            all_results = filtered

        all_results.sort(key=lambda x: x['start'])
        return self._merge_results(all_results)

    def _merge_results(self, results: List[Dict]) -> List[Dict]:
        if not results:
            return []

        results = sorted(results, key=lambda item: (item['start'], item['end']))
        merged = []

        for r in results:
            if not merged:
                merged.append(r.copy())
                continue

            last = merged[-1]
            if r['start'] >= last['end']:
                merged.append(r.copy())
                continue

            overlap = min(r['end'], last['end']) - max(r['start'], last['start'])
            if overlap <= 0:
                merged.append(r.copy())
                continue

            if r['category'] == last['category']:
                longer = r if (r['end'] - r['start']) >= (last['end'] - last['start']) else last
                merged[-1] = longer
                continue

            if r['value'] in last['value'] or last['value'] in r['value']:
                longer = r if (r['end'] - r['start']) >= (last['end'] - last['start']) else last
                merged[-1] = longer
                continue

            merged.append(r.copy())

        # Remove exact duplicates while preserving order
        unique = []
        for item in merged:
            if not any(
                other['start'] == item['start'] and other['end'] == item['end'] and other['value'] == item['value'] and other['category'] == item['category']
                for other in unique
            ):
                unique.append(item)

        return unique