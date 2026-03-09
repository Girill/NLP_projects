# -*- coding: utf-8 -*-
"""
Чанкинг документов с учётом структуры (заголовки, разделы).
Стратегия: рекурсивное разбиение по разделителям с лимитом размера и перекрытием.
Заголовок раздела выводится из первой строки чанка (эвристика: короткая строка без точки).
"""

import re
from pathlib import Path
from typing import Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Импорт конфига — при необходимости можно передавать параметры явно
try:
    import config
    CHUNK_SIZE = config.CHUNK_SIZE
    CHUNK_OVERLAP = config.CHUNK_OVERLAP
    SEPARATORS = config.SEPARATORS
except ImportError:
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 50
    SEPARATORS = ["\n\n## ", "\n\n### ", "\n\n", "\n", " "]


def _infer_section(first_line: str, max_len: int = 100) -> str:
    """
    Эвристика: считаем первую строку заголовком раздела, если она короткая
    и не заканчивается на . ! ?
    """
    line = (first_line or "").strip()
    if not line or len(line) > max_len:
        return ""
    if line and line[-1] in ".!?":
        return ""
    return line


def chunk_documents(
    documents: Sequence[Document],
    *,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: list[str] | None = None,
) -> list[Document]:
    """
    Разбивает документы на чанки, сохраняя source, page и добавляя section.
    Section — первая строка чанка, если она похожа на заголовок.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators or SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )
    out: list[Document] = []
    for doc in documents:
        chunks = splitter.split_text(doc.page_content)
        meta = dict(doc.metadata)
        for i, text in enumerate(chunks):
            first_line, _, _ = text.partition("\n")
            section = _infer_section(first_line)
            chunk_meta = {**meta, "section": section}
            out.append(Document(page_content=text.strip(), metadata=chunk_meta))
    return out
