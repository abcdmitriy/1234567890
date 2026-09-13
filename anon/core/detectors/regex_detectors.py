import re
from core.base_parser import InternalDocument

class SensitiveDataDetector:
    def __init__(self):
        self.patterns = {
            'PHONE': r'(?<!\d)(?:телефон[ауоме]?\s*|тел\.?\s*)?(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)',
            'EMAIL': r'(?<!\w)(?:email|эл\.?\s*почта|почта)?\s*[:.]?\s*[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            'PASSPORT': r'(?<!\d)(?:(?:сери[яиею]|сер\.?)\s*)?(?P<series>\d{2}\s?\d{2}|\d{4})(?:\s+|[,.]\s*)(?:номер|№|N\.?)?\s*(?P<number>\d{3}\s?\d{3}|\d{6})(?!\d)',
            'DEPT_CODE': r'(?<!\d)(?:код[ауоме]?\s+(?:подр\.|подразд\.|подразделени[яюеемй]?\s*)?|КП\s+|подр\.|подразд\.|подразделени[яюеемй]?\s*)\s*(?P<code>\d{3}[-./\s]?\d{3}|\d{6})(?!\d)',
            'INN': r'(?<!\d)(?:ИНН|УНП)?\s*[:.]?\s*(?:\d{10}|\d{12})(?!\d)',
            'BANK_ACCOUNT': r'(?<!\d)(?:расчетный\s*счет|р/сч|р/с|счет[ауоме]?)?\s*[:.]?\s*40[0-9]{18}(?!\d)',
            'BIC': r'(?<!\d)(?:БИК)?\s*[:.]?\s*\d{9}(?!\d)'
        }

    def detect(self, document: InternalDocument):
        full_text = ""
        for page in document.pages:
            for para in page.paragraphs:
                full_text += " ".join(f.text for f in para.fragments) + " "

        results = []
        for category, pattern in self.patterns.items():
            flags = re.IGNORECASE if category in ('PASSPORT', 'DEPT_CODE', 'EMAIL', 'INN', 'BANK_ACCOUNT', 'BIC') else 0
            for match in re.finditer(pattern, full_text, flags):
                results.append({
                    'start': match.start(),
                    'end': match.end(),
                    'value': match.group(),
                    'category': category
                })
        results.sort(key=lambda x: x['start'])
        return results