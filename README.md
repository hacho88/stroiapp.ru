# AI StroiApp Manager

Веб-приложение для управления продвижением интернет-магазина stroiapp.ru на OpenCart 3.

## Структура

- `backend` — FastAPI API-сервис.
- `frontend` — React + TailwindCSS интерфейс.
- OpenCart API-контроллер создан отдельно в `../stroiapp.ru/public_html/catalog/controller/api/ai_manager.php`.

## Backend

1. Установить Python 3.11+.
2. Перейти в папку `backend`.
3. Создать окружение и установить зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Скопировать `.env.example` в `.env` и заполнить ключи API.
5. Запустить сервис:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Документация API будет доступна по адресу `http://localhost:8000/docs`.

## Frontend

1. Перейти в папку `frontend`.
2. Установить зависимости:

```powershell
npm install
```

3. Запустить интерфейс:

```powershell
npm run dev
```

## Реализованные API MVP

- `GET /api/product/list`
- `GET /api/product/get/{sku}`
- `POST /api/product/update`
- `POST /api/dashboard/calculate`
- `GET /api/dashboard/compare`
- `POST /api/dashboard/launchAll`
- `POST /api/seo/generateDescription`
- `POST /api/seo/generateAllDescriptions`
- `POST /api/seo/autoFillMeta`
- `POST /api/seo/generateFAQ`
- `POST /api/seo/updateContent`
- `POST /api/lead/invoice`
- `POST /api/sitedoctor/updateStyles`
- `POST /api/sitedoctor/updateLayout`
- `POST /api/sitedoctor/updateBanner`
- `POST /api/telegram/notify`
- `POST /api/competitors/scan`

## Алгоритм бюджета

- товары сортируются по ROI от большего к меньшему;
- товары с ROI ниже 120% не добавляются;
- если товар не помещается в остаток бюджета, он пропускается;
- неизрасходованный бюджет сохраняется;
- оптимальная позиция хранится на уровне товара и не обязательно равна первому месту.

## Следующие этапы

- подключить реальную БД сайта из SQL-дампа;
- добавить постоянную БД для ai.stroiapp.ru;
- подключить OpenCart API-синхронизацию;
- подключить DeepSeek, Yandex Direct API v5, DaData/ФНС, Telegram Bot API;
- заменить MVP-заглушки на реальные интеграции.
