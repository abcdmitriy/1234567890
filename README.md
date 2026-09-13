# Anonymizer

**Локальное приложение для анонимизации документов** перед загрузкой в ИИ.
Заменяет персональные данные на псевдонимы вида [Person_1], [Phone_2],
[Address_3] и сохраняет карту соответствий для обратной деанонимизации.

---

## Возможности

- **Форматы файлов:** DOCX, PDF, JPG/PNG (OCR через Tesseract)
- **Что находит и заменяет:**
  - ФИО физических лиц (NER через Natasha)
  - Названия организаций (NER)
  - Телефоны, email
  - Адреса (эвристики по маркерам: г., ул., д., кв. и т.д.)
  - Паспортные данные, код подразделения
  - ИНН, БИК, расчётный счёт
- **Карта соответствий** сохраняется в JSON / CSV / XLSX
- **Обратная операция** — деанонимизация по сохранённой карте
- **Гибкая настройка** — можно включать/выключать отдельные категории
- **Два интерфейса:** CLI (командная строка) и GUI (PyQt5)

---

## Установка

### 1. Python-зависимости

    pip install -r anon/requirements.txt

### 2. Tesseract OCR (только для изображений и сканов PDF)

- Windows: https://github.com/UB-Mannheim/tesseract/wiki — установить,
  добавить путь в anon/core/parsers/image_parser.py
- Linux: sudo apt install tesseract-ocr tesseract-ocr-rus
- macOS: brew install tesseract tesseract-lang

### 3. Модели Natasha

Скачиваются автоматически при первом запуске NER.

---

## Запуск

### GUI

    cd anon
    python gui_main.py

### CLI

    cd anon
    python main.py path/to/document.docx -o ./output

---

## Пример использования

**Входной документ:**

    Иванов Иван Иванович, паспорт серия 4508 № 123456,
    тел. +7 (495) 123-45-67, email: ivanov@example.com

**Выходной документ:**

    [Person_1], паспорт [Passport_1],
    тел. [Phone_1], email: [Email_1]

**Карта соответствий** (anonymization-map.json):

    {
      "[Person_1]":   { "original": "Иванов Иван Иванович", "category": "PERSON"   },
      "[Passport_1]": { "original": "серия 4508 № 123456",  "category": "PASSPORT" },
      "[Phone_1]":    { "original": "+7 (495) 123-45-67",   "category": "PHONE"    },
      "[Email_1]":    { "original": "ivanov@example.com",   "category": "EMAIL"    }
    }

Карту можно сохранить отдельно и позже выполнить **обратную замену** —
восстановить оригинальные данные из анонимизированного текста.

---

## Требования

- Python 3.10+
- PyQt5 5.15+
- Tesseract OCR (опционально, для изображений)
