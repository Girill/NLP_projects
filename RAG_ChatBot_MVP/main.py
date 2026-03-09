# -*- coding: utf-8 -*-
"""
Точка входа: индексация PDF (ingest), запросы к RAG (CLI или Telegram).

Режимы (через RUN_MODE в .env или переменной окружения):
  cli     — ответы в терминал (по умолчанию)
  telegram — запуск Telegram-бота при команде run/telegram

Использование:
  python main.py ingest                # загрузить PDF в ChromaDB
  python main.py ask "Текст вопроса"   # ответ в терминал (CLI)
  python main.py run                  # режим из RUN_MODE: telegram → бот, cli → подсказка
  python main.py telegram             # запуск Telegram-бота (независимо от RUN_MODE)
"""

import sys
from pathlib import Path

# Корень проекта в PYTHONPATH для импортов
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from ingest import load_pdfs_from_folder, chunk_documents
from store import build_and_fill_store
from rag import LLM_answer, build_rag_chain


def run_telegram_bot() -> None:
    """Запуск Telegram-бота (Aiogram)."""
    from telegram_bot import run_bot
    run_bot()


def run_ingest(*, recreate: bool = False) -> None:
    """
    Загрузка PDF из data/pdf, чанкинг, эмбеддинг и загрузка в ChromaDB.
    """
    pdf_dir = config.PDF_DIR
    if not pdf_dir.is_dir():
        pdf_dir.mkdir(parents=True, exist_ok=True)
    pdfs = list(pdf_dir.glob("*.pdf"))

    if not pdfs:
        print("Положите PDF-файлы в папку:", pdf_dir)
        return
    print("Загрузка PDF...")
    docs = list(load_pdfs_from_folder(pdf_dir))

    if not docs:
        print("Не удалось извлечь текст из PDF.")
        return
    print("Чанкинг...")
    chunks = chunk_documents(docs)
    print("Эмбеддинги и загрузка в ChromaDB (recreate=%s)..." % recreate)
    build_and_fill_store(chunks, recreate=recreate)
    print("Готово. Чанков:", len(chunks))


def run_ask(question: str) -> None:
    """Ответ на вопрос."""
    out = LLM_answer(question)
    print(out)


def main() -> None:
    if len(sys.argv) < 2:
        if config.RUN_MODE == "telegram":
            run_telegram_bot()
            return
        print(__doc__)
        return
    cmd = sys.argv[1].lower()

    if cmd == "ingest":
        run_ingest()
    elif cmd == "ask":
        if len(sys.argv) < 3:
            print('Использование: python main.py ask "Вопрос"')
            return
        run_ask(" ".join(sys.argv[2:]))
    elif cmd == "telegram":
        run_telegram_bot()
    elif cmd == "run":
        if config.RUN_MODE == "telegram":
            run_telegram_bot()
        else:
            print("Режим CLI. Для запуска бота задайте RUN_MODE=telegram в .env и выполните: python main.py run")
            print("Либо: python main.py telegram")
    else:
        print("Команды: ingest | ask | run | telegram")
        print(__doc__)


if __name__ == "__main__":
    main()
