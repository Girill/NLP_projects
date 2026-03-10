# Telegram-интерфейс: описание и инструкции

## Ключевые фрагменты кода

### Загрузка токена и режима из конфигурации

```python
# config.py
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

RUN_MODE = os.getenv("RUN_MODE", "cli").strip().lower()
if RUN_MODE not in ("cli", "telegram"):
    RUN_MODE = "cli"
TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
```

### Инициализация Aiogram и обработчик сообщений

```python
# telegram_bot.py
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from rag import answer

router = Router()

@router.message()
async def handle_message(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Отправьте, пожалуйста, текстовый вопрос.")
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    reply = await _answer_question_sync(text)  # run_in_executor(rag.answer)
    await message.answer(reply)
```

### Переключение режимов CLI / Telegram в main.py

```python
# main.py
if len(sys.argv) < 2:
    if config.RUN_MODE == "telegram":
        run_telegram_bot()
        return
    print(__doc__)
    return
cmd = sys.argv[1].lower()
# ...
elif cmd == "telegram":
    run_telegram_bot()
elif cmd == "run":
    if config.RUN_MODE == "telegram":
        run_telegram_bot()
    else:
        print("Режим CLI. Для запуска бота задайте RUN_MODE=telegram в .env ...")
```

### Запуск бота и проверка токена

```python
# telegram_bot.py
def run_bot() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        print("Ошибка: не задан TELEGRAM_BOT_TOKEN. Создайте .env, см. .env.example")
        sys.exit(1)
    # ...
    async def main() -> None:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        await dp.start_polling(bot)
    asyncio.run(main())
```

---

## Запуск и тестирование

### Режим CLI (ответы в терминал)

1. Убедитесь, что в `.env` нет `RUN_MODE=telegram` или задано `RUN_MODE=cli`.
2. Индексация и вопрос:
   ```bash
   pip install -r requirements.txt
   python main.py ingest
   python main.py ask "Ваш вопрос"
   ```

### Режим Telegram

1. Получите токен у [@BotFather](https://t.me/BotFather) (`/newbot`).
2. Создайте `.env` из шаблона:
   ```bash
   cp .env.example .env
   ```
   В `.env` укажите:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   RUN_MODE=telegram
   ```
3. Запуск бота:
   ```bash
   python main.py telegram
   ```
   или при уже заданном `RUN_MODE=telegram`:
   ```bash
   python main.py run
   ```
4. В Telegram найдите бота по имени и отправьте текстовый вопрос — ответ придёт из того же RAG-пайплайна, что и в CLI.

### Ошибки

- **«Не задан TELEGRAM_BOT_TOKEN»** — создайте `.env` и добавьте `TELEGRAM_BOT_TOKEN=...`.
- **Ошибка подключения к Telegram** — проверьте токен и доступ в интернет.
- **Долгий ответ** — бот перед ответом показывает «печатает…»; при таймаутах проверьте работу Ollama и ChromaDB.
