# -*- coding: utf-8 -*-
"""
Пакет загрузки и разбиения документов (ingestion).
"""

from .pdf_loader import load_pdfs_from_folder
from .chunker import chunk_documents

__all__ = ["load_pdfs_from_folder", "chunk_documents"]
