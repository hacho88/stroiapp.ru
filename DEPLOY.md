# Деплой AI StroiApp Manager на ai.stroiapp.ru (Timeweb)

## Архитектура

- **Backend**: FastAPI (`backend/`), запускается через Passenger (`passenger_wsgi.py`)
- **Frontend**: React + Vite, статика (`frontend/dist/`), отдаётся nginx'ом
- **БД**: SQLite (`backend/data/app.db`) — создаётся автоматически
- **OpenCart API**: бэкенд обращается к `https://stroiapp.ru/index.php?route=api/ai_manager`

## Шаг 1. Панель Timeweb — подготовка сайта

1. Зайти в панель Timeweb → «Сайты» → `ai.stroiapp.ru`
2. **Удалить WordPress** (он был установлен по умолчанию, не нужен):
   - Сайты → ai.stroiapp.ru → «Удалить CMS» или удалить содержимое `public_html`
3. Проверить, что PHP-версия сайта не важна (будет Python)

## Шаг 2. Подключение GitHub

В панели Timeweb: «Сайты» → `ai.stroiapp.ru` → «Git» → подключить репозиторий:

- **Репозиторий**: `https://github.com/hacho88/stroiapp.ru`
- **Ветка**: `master`
- **Путь к сайту**: корень репозитория (код лежит в `backend/` и `frontend/`)

Либо клонировать вручную по SSH (включается в панели):

```bash
cd ~/ai.stroiapp.ru
git clone https://github.com/hacho88/stroiapp.ru.git repo
```

## Шаг 2а. Если панель поддерживает Python-сайты

Timeweb: «Сайты» → создать сайт с типом **Python**:

- **Путь приложения**: `backend/passenger_wsgi.py` → переменная `application`
- **Python**: 3.10
- **Команда установки зависимостей**: `pip3 install -r requirements.txt --user`
- **Файл запуска**: `passenger_wsgi.py`, объект `application`

## Шаг 3. Сборка фронтенда (локально, один раз)

```powershell
cd frontend
npm install
npm run build
```

Получится `frontend/dist/` — загрузить содержимое в `public_html/` сайта
(или настроить в панели «корень сайта» → `frontend/dist`).

## Шаг 4. Переменные окружения

Скопировать `backend/.env.example` → `backend/.env` и заполнить:

```
OPENCART_API_URL=https://stroiapp.ru
OPENCART_API_TOKEN=<токен из catalog/controller/api/ai_manager.php>
DEEPSEEK_API_KEY=<ключ DeepSeek>
YANDEX_DIRECT_TOKEN=<токен Директ>
```

⚠️ `.env` не коммитится в git (в .gitignore). На сервере создаётся вручную.

## Шаг 5. SSL-сертификат

В панели Timeweb: «Домены» → `ai.stroiapp.ru` → выпустить бесплатный
Let's Encrypt сертификат. Без него сайт работает только по HTTP.

## Структура на сервере

```
~/ai.stroiapp.ru/
├── repo/                  # git clone репозитория
│   ├── backend/
│   │   ├── passenger_wsgi.py
│   │   ├── requirements.txt
│   │   ├── app/
│   │   └── data/app.db    # SQLite, создаётся автоматически
│   └── frontend/
│       └── dist/          # собранный фронтенд → public_html
```

## Обновление

```bash
cd ~/ai.stroiapp.ru/repo
git pull
# перезапуск Passenger:
touch tmp/restart.txt
```

## Если панель НЕ поддерживает Python-приложения

Варианты:
1. **VPS Timeweb** — полный контроль, uvicorn + nginx (рекомендуется)
2. Оставить бэкенд локальным (`uvicorn app.main:app --port 8000`),
   а на сервер выложить только статику фронтенда с
   `VITE_API_URL=http://<IP-пользователя>:8000/api` (работает только из своей сети)
