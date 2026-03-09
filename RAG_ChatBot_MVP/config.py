# -*- coding: utf-8 -*-
"""
Конфигурация прототипа RAG-чат-бота.
Все пути и параметры собраны в одном месте для простоты настройки.
Переменные окружения загружаются из .env (python-dotenv).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта (рядом с config.py)
load_dotenv(Path(__file__).resolve().parent / ".env")

# --- Пути ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"           # Папка с PDF-документами
PDF_DIR = DATA_DIR / "pdf"                 # Исходные PDF
CHROMA_DIR = PROJECT_ROOT / "chroma_data"  # Локальное хранилище ChromaDB
COLLECTION_NAME = "kb_docs"

# --- Модели ---
# Эмбеддинги: qwen3-embedding:0.6b
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
EMBEDDING_DIM = 1024

# Генерация ответов и классификация вопросов: LLM: Ollama + qwen2.5:7b-instruct.
LLM_MODEL = "qwen2.5:7b-instruct"

# --- Chunking ---
# Стратегия: рекурсивное разбиение по разделителям (\\n\\n## , \\n\\n### , \\n\\n, \\n)
# с ограничением размера. Сохраняем контекст заголовка в чанке.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
SEPARATORS = ["\n\n## ", "\n\n### ", "\n\n", "\n", " "]

# --- RAG ---
TOP_K = 4              # число чанков для retrieval
SCORE_THRESHOLD = 0.5  # порог релевантности (при использовании score)

# --- ChromaDB ---
CHROMA_PATH = str(CHROMA_DIR)  # persist_directory для локального хранения на диске

# --- Режим запуска и Telegram ---
# RUN_MODE: "cli" — ответы в терминал (python main.py ask "..."); "telegram" — бот в Telegram.
RUN_MODE = os.getenv("RUN_MODE", "cli").strip().lower()
if RUN_MODE not in ("cli", "telegram"):
    RUN_MODE = "cli"

# Токен Telegram-бота. Задаётся в .env: TELEGRAM_BOT_TOKEN=123:ABC...
TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()

# Создание нужных директорий при импорте
DATA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
