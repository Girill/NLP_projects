# -*- coding: utf-8 -*-
"""
ChromaDB: создание коллекции, персистентное хранение, загрузка эмбеддингов.

Схема:
- persist_directory: локальная папка для хранения на диске
- collection_name: имя коллекции (kb_docs)
- Метаданные чанков: source, page, section — сохраняются в Chroma (str, int, str)

ChromaDB работает полностью локально, без сервера. Совместим с LangChain через
langchain_community.vectorstores.Chroma.
"""

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import torch
import config

from langchain_community.embeddings import OllamaEmbeddings
# Singleton для избежания повторной инициализации
_chroma_store: Chroma | None = None


def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=config.EMBEDDING_MODEL,
        show_progress=True
    )

# TODO: Раскомментировать, если используется HuggingFaceEmbeddings
#  from langchain_community.embeddings import HuggingFaceEmbeddings

# def _get_embeddings() -> HuggingFaceEmbeddings:
# return HuggingFaceEmbeddings(
#     model_name=config.EMBEDDING_MODEL,
#     model_kwargs={"device": "cpu"},
# )


def _normalize_metadata_for_chroma(metadata: dict) -> dict:
    """
    ChromaDB принимает только str, int, float, bool в метаданных.
    Конвертируем при необходимости (например, None -> пустая строка).
    """
    out = {}
    for k, v in metadata.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def build_and_fill_store(
    documents: list[Document],
    *,
    recreate: bool = False,
) -> Chroma:
    """
    Создаёт коллекцию Chroma, строит эмбеддинги и загружает чанки.
    recreate=True — удаляет существующую коллекцию и создаёт заново.
    """
    if recreate:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=config.CHROMA_PATH)
            client.delete_collection(name=config.COLLECTION_NAME)
        except Exception:
            pass

    embeddings = _get_embeddings()

    # Нормализация метаданных для Chroma (source, page, section)
    normalized_docs = [
        Document(
            page_content=doc.page_content,
            metadata=_normalize_metadata_for_chroma(doc.metadata),
        )
        for doc in documents
    ]

    vs = Chroma.from_documents(
        documents=normalized_docs,
        embedding=embeddings,
        persist_directory=config.CHROMA_PATH,
        collection_name=config.COLLECTION_NAME,
    )
    return vs


def get_vectorstore() -> Chroma:
    """
    Подключается к существующей коллекции Chroma для retrieval.
    Требует предварительного вызова build_and_fill_store.
    """
    global _chroma_store
    if _chroma_store is not None:
        return _chroma_store

    embeddings = _get_embeddings()
    _chroma_store = Chroma(
        persist_directory=config.CHROMA_PATH,
        embedding_function=embeddings,
        collection_name=config.COLLECTION_NAME,
    )
    return _chroma_store
