# Telegram Meme Bot

Бот принимает голосовые и видео сообщения, распознаёт речь, саммаризирует, превращает в мем и отправляет картинку с мемом в ответ.

## Быстрый старт

1. Клонируй репозиторий:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
2. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Переименуй `.env.example` в `.env` и заполни токены:
   ```env
   TELEGRAM_TOKEN=your_telegram_token
   MISTRAL_API_KEY=your_mistral_api_key
   ```
4. Положи все шаблоны мемов (png/jpg) и шрифт DejaVuSans.ttf в папку с ботом.
5. Запусти бота:
   ```bash
   python3 bot.py
   ```

## Деплой в Railway

1. Залей проект на GitHub.
2. На [railway.app](https://railway.app/) создай новый проект, выбери "Deploy from GitHub repo".
3. В настройках Railway добавь переменные окружения:
   - `TELEGRAM_TOKEN`
   - `MISTRAL_API_KEY`
4. Убедись, что в репозитории есть requirements.txt и .gitignore.
5. Railway сам определит команду запуска (`python3 bot.py`).
6. После деплоя бот будет работать 24/7!

## Примечания
- Не заливай реальные токены в публичный репозиторий!
- Для работы с кириллицей нужен файл шрифта DejaVuSans.ttf (скачать можно с [github.com/dejavu-fonts/dejavu-fonts](https://github.com/dejavu-fonts/dejavu-fonts/blob/master/ttf/DejaVuSans.ttf?raw=true)).
- Все шаблоны мемов должны быть в корне проекта.

## Контакты
Вопросы и предложения — в Issues или Telegram! 