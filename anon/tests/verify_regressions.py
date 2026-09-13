from unittest.mock import Mock

from core.detectors.detector_manager import DetectorManager
from core.processors.replacer import Replacer


text = "Contact: +7 999 123 45 67; email test@example.com"
phone = "+7 999 123 45 67"
email = "test@example.com"
replacements = [
    {"start": text.index(phone), "end": text.index(phone) + len(phone), "value": phone, "alias": "[Phone_1]"},
    {"start": text.index(email), "end": text.index(email) + len(email), "value": email, "alias": "[Email_1]"},
]
result = Replacer.apply_replacements_to_text(text, replacements)
assert result == "Contact: [Phone_1]; email [Email_1]", result

detector_manager = DetectorManager({})
detector_manager.regex_detector.detect = Mock(return_value=[])
detector_manager.address_detector.find_addresses = Mock(return_value=[])
detector_manager.ner_detector.find_entities = Mock(return_value=[
    {"start": 0, "end": 4, "value": "Иван", "category": "PERSON"},
    {"start": 10, "end": 20, "value": "Лаборатория", "category": "ORG"},
])

results = detector_manager.detect("Иван работает в Лаборатории")
assert any(item["category"] == "PERSON" for item in results), results
assert any(item["category"] == "ORG" for item in results), results
detector_manager.ner_detector.find_entities.assert_called_once_with("Иван работает в Лаборатории")

print("verification: 2 regression checks passed")
