# core/detectors/address_detector.py
import re
from typing import List, Dict

class AddressDetector:
    def __init__(self):
        # 1. Список маркеров
        markers = [
            r"республика", r"респ\.", r"край", r"область", r"обл\.", r"автономный округ", r"а\.окр\.",
            r"район", r"р-н", r"город", r"г\.", r"поселок", r"пос\.", r"село", r"с\.", r"деревня", r"д\.",
            r"улица", r"ул\.", r"проспект", r"пр\.", r"пр-кт", r"просп\.", r"переулок", r"пер\.",
            r"бульвар", r"б-р", r"бул\.", r"шоссе", r"ш\.", r"набережная", r"наб\.", r"площадь", r"пл\.",
            r"проезд", r"пр-д", r"дом", r"корпус", r"корп\.", r"строение", r"стр\.", r"квартира", r"кв\.",
            r"офис", r"оф\.", r"помещение", r"помещ\.", r"владение", r"влд\.", r"а/я"
        ]

        # Вспомогательная функция: делает регулярное выражение нечувствительным к регистру
        def make_ci(word):
            res = []
            for char in word:
                if char.isalpha():
                    res.append(f"[{char.upper()}{char.lower()}]")
                else:
                    res.append(char)
            return "".join(res)

        # Сортируем маркеры по убыванию длины
        markers_sorted = sorted(markers, key=lambda x: len(x.replace('\\', '')), reverse=True)
        markers_ci = [make_ci(m) for m in markers_sorted]
        self.markers_pattern = r"(?:" + r"|".join(markers_ci) + r")"

        # 2. Правила для слов, которые могут входить в адрес
        cap_word_pattern = r"[А-ЯЁA-Z][а-яёa-zA-Z]*(?:-[А-ЯЁA-Zа-яёa-zA-Z]+)*"
        number_pattern = r"\d+(?:[/-]\d+)?(?:-[А-Яа-яЁё]{1,2})?[А-Яа-яЁёA-Za-z]?"
        short_word_pattern = r"[А-Яа-яЁёA-Za-z]{1,2}"

        allowed_word = (
            r"(?:" + self.markers_pattern + r"|" +
            cap_word_pattern + r"|" +
            number_pattern + r"|" +
            short_word_pattern + r")"
        )

        # 3. Итоговое регулярное выражение
        self.address_regex = r"\b" + self.markers_pattern + r"(?:[\s,.]+" + allowed_word + r")*"
        self.number_pattern = number_pattern

    def find_addresses(self, text: str) -> List[Dict]:
        """
        Находит адреса с маркерами (г., ул., д. и т.д.).
        Возвращает список словарей с полями start, end, value, category='ADDRESS'.
        """
        results = []
        matches = re.finditer(self.address_regex, text)

        for match in matches:
            raw_match = match.group(0)
            # Находим числа в захваченном фрагменте
            num_matches = list(re.finditer(self.number_pattern, raw_match))
            if not num_matches:
                continue  # нет числа — пропускаем
            # Берем последнее найденное число
            last_num = num_matches[-1]
            # Обрезаем адрес до конца последнего числа
            valid_addr = raw_match[:last_num.end()]
            start_idx = match.start()
            end_idx = match.start() + last_num.end()
            results.append({
                'start': start_idx,
                'end': end_idx,
                'value': valid_addr,
                'category': 'ADDRESS'
            })

        return results