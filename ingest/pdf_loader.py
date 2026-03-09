# -*- coding: utf-8 -*-
"""
Загрузка PDF-документов.
Используется PdfReader из библиотеки pypdf.
Постраничный вывод с метаданными source, page для совместимости с чанкингом и индексацией.
"""

from pathlib import Path
from typing import Generator

import re
from pypdf import PdfReader

import pymupdf
import pymupdf4llm

from langchain_core.documents import Document

def _extract_text_from_pdf(path: Path) -> list[tuple[int, str]]:
    """
    Извлекает текст постранично из PDF.
    Возвращает список пар (номер_страницы, текст).
    """
    reader = PdfReader(str(path))
    result = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # Убираем лишние пробелы, сохраняем переносы
        text = re.sub(r"[ \t]+", " ", text).strip()
        result.append((i, text))
    return result

def _extract_markdown_from_pdf(path: Path) -> list[tuple[int, str]]:
    """
    Извлекает содержимое PDF постранично в формате Markdown.
    Возвращает список пар (номер_страницы_1-based, markdown_текст).
    """
    doc = pymupdf.open(path)
    result = []
    try:
        for i in range(len(doc)):
            md = pymupdf4llm.to_markdown(doc, pages=[i])
            text = (md or "").strip()
            if text:
                result.append((i + 1, text))
    finally:
        doc.close()
    return result


def load_pdfs_from_folder(
    folder: Path,
    *,
    glob: str = "*.pdf",
) -> Generator[Document, None, None]:
    """
    Загружает все PDF из папки и возвращает итератор LangChain Document.
    Каждый документ = одна страница.
    Метаданные: source (имя файла), page.
    """
    folder = Path(folder)
    if not folder.is_dir():
        return

    for p in sorted(folder.glob(glob)):
        if not p.is_file():
            continue
        try:
            for page_num, text in _extract_text_from_pdf(p):
                if not text.strip():
                    continue
                yield Document(
                    page_content=text,
                    metadata={"source": p.name, "page": page_num},
                )
                
            # for page_num, markdown_text in _extract_markdown_from_pdf(p):
            #     yield Document(
            #         page_content=markdown_text,
            #         metadata={"source": p.name, "page": page_num},
            #     )
        except Exception as e:
            import sys
            print(f"Ошибка загрузки {p}: {e}", file=sys.stderr)
