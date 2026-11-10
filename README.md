Markdown

# 🛡️ Cyber-Warden Enterprise SOC

> **Autonomous Local AI Threat Intelligence & Incident Response Platform**

Cyber-Warden SOC — это суверенная система мониторинга киберугроз в реальном времени. Проект объединяет непрерывный анализ Telegram-чатов и веб-форумов с помощью локальной языковой модели, а также предоставляет интерактивный центр управления (SOC Dashboard) с аналитикой и графиками.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20SOC-green?style=flat-square&logo=flask)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue?style=flat-square&logo=telegram)

---

## 🚀 Ключевые особенности (Core Features)

- **100% On-Premise & Privacy:** Все данные обрабатываются локально. Ни одно сообщение не уходит в сторонние облачные API (OpenAI, Anthropic и т.д.).
- **Многоуровневый анализ угроз:** Детекция эксплойтов, RCE, SQLi, фишинга, социальной инженерии, вредоносного ПО (ransomware, infostealers) и торговли базами данных.
- **Контекстная память пользователей (`Context-Aware`):** Бот анализирует не отдельные слова, а всю недавнюю историю переписки конкретного пользователя, выявляя скрытую подготовку к атакам.
- **Трилингвальный движок:** Понимание технического сленга и контекста на **русском, узбекском (латиница/кириллица) и английском** языках.
- **Enterprise SOC Dashboard:** Веб-панель управления с живыми графиками (Chart.js), статистикой категорий угроз и лентой инцидентов в реальном времени.
- **Симулятор веб-форума:** Встроенный инструмент для тестирования и инъекции полезной нагрузки (payloads) прямо в веб-интерфейсе.

---

## 🛠️ Системные требования и установка

### Шаг 1. Установка и настройка Ollama (Локальный ИИ)
Проект использует локальную нейросеть через [Ollama](https://ollama.com/).

1. Скачайте и установите **Ollama** для вашей ОС с официального сайта.
2. Откройте терминал (Command Prompt / PowerShell / Terminal) и скачайте оптимизированную модель **Qwen 2.5 (3B)**:
   ```bash
   ollama run qwen2.5:3b

    Убедитесь, что локальный сервер Ollama запущен и доступен по адресу http://localhost:11434.

Шаг 2. Клонирование репозитория и установка зависимостей

    Клонируйте репозиторий или скачайте проект:
    Bash

    git clone [https://github.com/your-username/cyber-warden-soc.git](https://github.com/your-username/cyber-warden-soc.git)
    cd cyber-warden-soc

    Установите необходимые библиотеки Python (Flask, requests, pyTelegramBotAPI):
    Bash

    pip install flask requests pyTelegramBotAPI

Шаг 3. Конфигурация бота

Откройте файл app.py и укажите данные вашего Telegram-бота в секции настроек:
Python

# Токен вашего бота от @BotFather
BOT_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"

# Ваш числовой Telegram ID для получения алертов (узнать можно у @userinfobot)
ADMIN_CHAT_ID = ВАШ_NUMERIC_ID  

Шаг 4. Запуск проекта

Запустите главный файл приложения:
Bash

python app.py

После запуска:

    Telegram-бот начнет автоматический мониторинг групп (убедитесь, что бот добавлен в чат).

    Веб-дэшборд SOC будет доступен в браузере по адресу: http://127.0.0.1:5000

📊 Стек технологий

    Backend: Python, Flask, Multithreading (синхронизация Telegram Polling и Web Server)

    AI Engine: Ollama, Qwen 2.5 (3B parameters)

    Frontend: Tailwind CSS, Chart.js (интерактивные круговые диаграммы)

    Integration: Telegram Bot API (pyTelegramBotAPI)

👨‍💻 Авторы

Разработано для хакатона в рамках систем обеспечения кибербезопасности и предиктивного анализа угроз.
