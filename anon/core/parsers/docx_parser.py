from docx import Document as DocxDocument
from docx.oxml import CT_P, CT_Tbl
from docx.oxml.text.paragraph import CT_P as CT_Para
from docx.table import Table as DocxTable, _Cell as DocxCell
from docx.text.paragraph import Paragraph as DocxParagraph
from typing import Optional, List, Union

from core.base_parser import (
    Parser, InternalDocument, Page, Paragraph, TextFragment, Table, Cell
)


class DOCXParser(Parser):
    def parse(self, file_path: str) -> InternalDocument:
        try:
            doc = DocxDocument(file_path)
        except Exception as e:
            raise ValueError(f"Не удалось открыть DOCX-файл: {e}")

        page = Page(number=1)

        for block in doc.element.body:
            if isinstance(block, CT_P):
                para = DocxParagraph(block, doc)
                internal_para = self._convert_paragraph(para)
                if internal_para:
                    page.paragraphs.append(internal_para)

            elif isinstance(block, CT_Tbl):
                table = DocxTable(block, doc)
                internal_table = self._convert_table(table)
                if internal_table:
                    page.tables.append(internal_table)

        return InternalDocument(pages=[page])

    def _convert_paragraph(self, para: DocxParagraph) -> Optional[Paragraph]:
        fragments = []
        for run in para.runs:
            if run.text:
                fragments.append(TextFragment(
                    text=run.text,
                    bold=bool(run.bold),
                    italic=bool(run.italic),
                    underline=bool(run.underline),
                    size=run.font.size.pt if (run.font and run.font.size) else None,
                    font=run.font.name if run.font else None
                ))
        # гиперссылки
        for hl in para.hyperlinks:
            if hl.text and (not fragments or fragments[-1].text != hl.text):
                fragments.append(TextFragment(text=hl.text))
        return Paragraph(fragments=fragments) if fragments else None

    def _convert_table(self, table: DocxTable) -> Optional[Table]:
        internal_table = Table()
        for row in table.rows:
            row_cells = []
            for cell in row.cells:
                cell_texts = self._extract_cell_text(cell)
                if cell_texts:
                    # каждая строка из ячейки становится отдельным параграфом
                    cell_pars = []
                    for line in cell_texts:
                        if line.strip():
                            cell_pars.append(Paragraph(fragments=[TextFragment(text=line.strip())]))
                    row_cells.append(Cell(paragraphs=cell_pars))
                else:
                    row_cells.append(Cell(paragraphs=[]))
            internal_table.rows.append(row_cells)
        return internal_table if internal_table.rows else None

    def _extract_cell_text(self, cell: DocxCell) -> List[str]:
        """Извлекает текст из ячейки, включая вложенные таблицы."""
        lines = []
        if cell.paragraphs:
            for para in cell.paragraphs:
                text = para.text.strip()
                if text:
                    lines.append(text)
        # если в ячейке нет параграфов, пробуем через cell.text
        if not lines and cell.text:
            lines = [cell.text.strip()]
        # дополнительно: обход вложенных таблиц
        # в python-docx нет прямого доступа к вложенным таблицам через cell,
        # но можно получить их через XML
        tbls = cell._element.xpath('.//w:tbl')
        for tbl in tbls:
            # рекурсивно создаём временную таблицу и извлекаем текст
            sub_table = DocxTable(tbl, cell.part)
            sub_cells = self._extract_subtable_text(sub_table)
            if sub_cells:
                lines.extend(sub_cells)
        return lines

    def _extract_subtable_text(self, table: DocxTable) -> List[str]:
        """Извлекает текст из вложенной таблицы, возвращает список строк."""
        lines = []
        for row in table.rows:
            for cell in row.cells:
                cell_texts = self._extract_cell_text(cell)
                if cell_texts:
                    lines.extend(cell_texts)
        return lines