import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from core.base_parser import (
    Parser, InternalDocument, Page, Paragraph, TextFragment
)


class PDFParser(Parser):
    def parse(self, file_path: str) -> InternalDocument:
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Не удалось открыть PDF-файл: {e}")

        internal_doc = InternalDocument()

        for page_num, pdf_page in enumerate(doc):
            page = Page(
                number=page_num + 1,
                width=pdf_page.rect.width,
                height=pdf_page.rect.height
            )

            blocks = pdf_page.get_text("blocks")
            text_extracted = False

            for b in blocks:
                text = b[4].strip()
                if text:
                    text_extracted = True
                    fragment = TextFragment(
                        text=text,
                        bbox=(b[0], b[1], b[2], b[3])
                    )
                    page.paragraphs.append(Paragraph(fragments=[fragment]))

            # Если текстовый слой пуст, запускаем OCR (Fallback)
            if not text_extracted:
                self._apply_ocr_to_page(pdf_page, page)

            internal_doc.pages.append(page)

        doc.close()
        return internal_doc

    def _apply_ocr_to_page(self, pdf_page, internal_page: Page):
        # Рендерим страницу PDF в изображение с высоким разрешением (zoom=2)
        matrix = fitz.Matrix(2, 2)
        pix = pdf_page.get_pixmap(matrix=matrix)

        # Конвертируем в PIL Image
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

        # Обработка изображения (по аналогии с ImageParser)
        img = img.convert('L')
        img = img.point(lambda p: 255 if p > 128 else 0)

        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(
            img, lang='rus+eng', config=custom_config, output_type=pytesseract.Output.DICT
        )

        paragraph = Paragraph(fragments=[])
        tokens = []

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if not text:
                continue

            try:
                conf = int(data['conf'][i])
            except (TypeError, ValueError):
                conf = None

            if conf is not None and conf < 10:
                continue

            x = data['left'][i] / 2
            y = data['top'][i] / 2
            w = data['width'][i] / 2
            h = data['height'][i] / 2
            tokens.append({
                'text': text,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'bbox': (x, y, x + w, y + h)
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

            paragraph.fragments.append(TextFragment(text='\n'.join(lines), bbox=(0, 0, pdf_page.rect.width, pdf_page.rect.height)))
            internal_page.paragraphs.append(paragraph)