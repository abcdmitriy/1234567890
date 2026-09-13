import pytesseract
from PIL import Image, ImageOps
from core.base_parser import (
    Parser, InternalDocument, Page, Paragraph, TextFragment
)

# Укажите здесь свой путь, если он отличается
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ImageParser(Parser):
    def parse(self, file_path: str) -> InternalDocument:
        try:
            # 1. Открываем и конвертируем в ч/б для улучшения распознавания
            img = Image.open(file_path).convert('L')

            # 2. Бинаризация: превращаем в чистый ч/б (убирает артефакты JPG)
            # Порог 128 можно менять: от 0 до 255
            img = img.point(lambda p: 255 if p > 128 else 0)

        except Exception as e:
            raise ValueError(f"Не удалось открыть изображение: {e}")

        # 3. Настройки для Tesseract
        custom_config = r'--oem 3 --psm 6 preserve_interword_spaces=1'

        data = pytesseract.image_to_data(
            img,
            lang='rus+eng',
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )

        page = Page(number=1, width=img.width, height=img.height)
        paragraph = Paragraph(fragments=[])
        tokens = []

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if not text:
                continue

            conf_value = data['conf'][i]
            try:
                conf = int(conf_value)
            except (TypeError, ValueError):
                conf = None

            if conf is not None and conf < 10:
                continue

            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            tokens.append({
                'text': text,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
            })

        if tokens:
            tokens.sort(key=lambda item: (item['y'], item['x']))
            line_map = {}
            for token in tokens:
                line_key = round(token['y'] / 10)
                line_map.setdefault(line_key, []).append(token)

            lines = []
            for key in sorted(line_map.keys()):
                line_tokens = sorted(line_map[key], key=lambda item: item['x'])
                line_parts = []
                last_x = None
                for token in line_tokens:
                    if last_x is not None and token['x'] - last_x > max(12, token['w'] * 0.6):
                        line_parts.append(' ')
                    line_parts.append(token['text'])
                    last_x = token['x'] + token['w']
                lines.append(''.join(line_parts))

            full_text = '\n'.join(lines)
            paragraph.fragments.append(TextFragment(text=full_text, bbox=(0, 0, img.width, img.height)))
            page.paragraphs.append(paragraph)

        return InternalDocument(pages=[page])