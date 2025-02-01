# Telegram Quiz Bot

## Description (English)
**Telegram Quiz Bot** is a Telegram bot designed for student testing based on covered material. The bot provides interfaces for both teachers and students, supports automatic score calculation, and sends video feedback based on test results.

## Features
### For Teachers:
- Add test questions with multiple-choice answers.
- Upload video feedback for students based on test performance.
- Start testing sessions for students on selected topics.
- View accumulated student scores.

### For Students:
- Register in the bot with full name and contact details.
- Take tests with automatic scoring.
- Receive a video feedback message after completing the test.

## Installation
### Requirements:
- Docker
- Docker Compose

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/biguxuzz/telegram-quiz-bot.git
   cd telegram-quiz-bot
   ```
2. Create a `.env` file and set the required environment variables (e.g., bot API key, database credentials, etc.).
3. Start the containers:
   ```bash
   docker-compose up -d
   ```

## Technologies Used
- Python + Telebot
- PostgreSQL (database)
- Docker (containerization)
- Pytest (automated testing)

## License
This project is licensed under the **AGPL-3.0**. See [`LICENSE`](LICENSE) for details.

## Contacts
- **GitHub**: [biguxuzz](https://github.com/biguxuzz)
- **Telegram**: [@biguxuzz](https://t.me/biguxuzz)
- **Email**: [gorp@1cgst.ru](mailto:gorp@1cgst.ru)

---

## Описание (Русский)
**Telegram Quiz Bot** – это телеграм-бот для тестирования студентов по пройденному материалу. Бот предоставляет интерфейсы для преподавателей и студентов, поддерживает автоматический подсчет баллов и отправку видео-комментариев по результатам тестирования.

## Возможности
### Для преподавателей:
- Добавление тестовых вопросов с вариантами ответов.
- Загрузка видео с комментариями для студентов по результатам тестирования.
- Запуск тестирования для студентов по выбранным разделам.
- Просмотр накопленных баллов студентов.

### Для студентов:
- Регистрация в боте с вводом ФИО и передачи контакта.
- Прохождение тестирования с автоматическим подсчетом баллов.
- Получение видео-комментария после завершения теста.

## Установка
### Требования:
- Docker
- Docker Compose

### Запуск
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/biguxuzz/telegram-quiz-bot.git
   cd telegram-quiz-bot
   ```
2. Создайте `.env` файл и укажите необходимые переменные окружения (например, API-ключ бота, данные для БД и т. д.).
3. Запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

## Используемые технологии
- Python + Telebot
- PostgreSQL (база данных)
- Docker (контейнеризация)
- Pytest (автоматическое тестирование)

## Лицензия
Этот проект распространяется под лицензией **AGPL-3.0**. Подробнее см. в файле [`LICENSE`](LICENSE).

## Контакты
- **GitHub**: [biguxuzz](https://github.com/biguxuzz)
- **Telegram**: [@biguxuzz](https://t.me/biguxuzz)
- **Email**: [gorp@1cgst.ru](mailto:gorp@1cgst.ru)

