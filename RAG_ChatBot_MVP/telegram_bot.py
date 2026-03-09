# -*- coding: utf-8 -*-
"""
Telegram-интерфейс чат-бота на Aiogram.
Транспортный слой: приём сообщений и отправка ответов.
Бизнес-логика (RAG) вызывается через rag.LLM_answer() — общий слой для CLI и Telegram.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

import config
from rag import LLM_answer

logger = logging.getLogger(__name__)

router = Router()


async def _answer_question_sync(question: str) -> str:
    """
    Вызов синхронного RAG в executor, чтобы не блокировать event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: LLM_answer(question))


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветствие по команде /start."""
    await message.answer(
        """
        Привет! Я бот по внутренней документации.\n
        Напиши вопрос — постараюсь ответить по базе знаний.\n\n

        Общие рекомендации по использованию:\n
        1. Старайтесь явно и конкретно формулировать вопрос.\n
        2. По возможности, указывайте, что вас интересует как сделать что-то согласно ГОСТ (например, Согласно ГОСТ как правильно оформить...)\n
        3. Помните, что нейросеть может ошибаться, проверяйте критически важную информацию.
        """
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка по команде /help."""
    await message.answer(
        "Отправь текстовое сообщение с вопросом — я найду ответ в базе документации и отвечу с указанием источников.\n"
        "Команды: /start, /help"
    )


@router.message()
async def handle_message(message: Message) -> None:
    """
    Обработка текстовых сообщений: вызов RAG и отправка ответа.
    Пустые сообщения и не-текст игнорируем.
    """
    text = (message.text or "").strip()
    if not text:
        await message.answer("Отправьте, пожалуйста, текстовый вопрос.")
        return

    # "Печатает..." пока генерируем ответ
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        reply = await _answer_question_sync(text)
    except Exception as e:
        logger.exception("Ошибка при генерации ответа RAG")
        await message.answer(
            "Произошла ошибка при обработке вопроса. Попробуйте позже или перефразируйте."
        )
        return

    # Telegram ограничивает длину сообщения (4096). Разбиваем при необходимости.
    max_len = 4096
    if len(reply) <= max_len:
        await message.answer(reply)
    else:
        for i in range(0, len(reply), max_len):
            await message.answer(reply[i : i + max_len])


def run_bot() -> None:
    """
    Запуск Telegram-бота (polling).
    Токен берётся из config.TELEGRAM_BOT_TOKEN (загружается из .env).
    """
    if not config.TELEGRAM_BOT_TOKEN:
        print(
            "Ошибка: не задан TELEGRAM_BOT_TOKEN. "
            "Создайте файл .env в корне проекта и добавьте строку:\n"
            "  TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather\n"
            "См. .env.example"
        )
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def main() -> None:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        try:
            await dp.start_polling(bot)
        finally:
            await bot.session.close()

    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Ошибка при работе бота")
        print("Ошибка подключения к Telegram. Проверьте токен и сеть.", file=sys.stderr)
        sys.exit(1)
