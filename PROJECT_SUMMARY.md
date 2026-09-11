# ПОЛНОЕ ОПИСАНИЕ ПРОЕКТА StroiApp — ai.stroiapp.ru + stroiapp.ru

## 1. ЧТО ЭТО ЗА ПРОЕКТ

**StroiApp** — это полноценная экосистема для управления интернет-магазином строительных материалов в Москве и Московской области.

### Два основных компонента:

| Компонент | URL | Роль |
|-----------|-----|------|
| **stroiapp.ru** | https://stroiapp.ru | Публичный интернет-магазин на OpenCart 3. Клиенты покупают здесь. |
| **ai.stroiapp.ru** | http://localhost:5173 (dev) / https://ai.stroiapp.ru (prod) | Приватный AI-менеджер для администратора. Управление товарами, SEO, ценами, аналитика. |

### Архитектура:

```
┌─────────────────────────────────────────────────────────────┐
│                     ПОЛЬЗОВАТЕЛЬ                            │
│                 (Администратор магазина)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              ai.stroiapp.ru (React Frontend)                │
│              Порт: 5173 (dev) / 80 (prod)                   │
│   Вкладки: Товары | AI SEO | Аналитика | Клиенты | Заказы  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST API
┌────────────────────────▼────────────────────────────────────┐
│              ai.stroiapp.ru (FastAPI Backend)               │
│              Порт: 8010                                     │
│   Python + FastAPI + Uvicorn                                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP API calls
┌────────────────────────▼────────────────────────────────────┐
│              stroiapp.ru (OpenCart PHP Backend)             │
│              PHP 7.4 + OpenCart 3 + MySQL                   │
│   catalog/controller/api/ai_manager.php — API контроллер    │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
┌────────────────────────▼────────────────────────────────────┐
│              MySQL Database (ct45965_open)                  │
│   Таблицы: oc_openproduct, oc_openproduct_description,     │
│            oc_openproduct_attribute, oc_opencategory, etc. │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. ЧТО БЫЛО СДЕЛАНО ДО ЭТОГО (Исторические этапы)

### Этап 1: Создание AI-менеджера
- Создан React-фронтенд (`frontend/`) с дашбордом, навигацией, тостами
- Создан FastAPI-бэкенд (`backend/`) с маршрутами для OpenCart
- Создан PHP API-контроллер (`ai_manager.php`) для безопасного проксирования запросов
- Настроена аутентификация через токен `change_this_ai_manager_token`

### Этап 2: Управление категориями
- Дерево категорий слева (рекурсивное построение)
- Отображение товаров по категории
- Inline-редактирование цен прямо в карточке товара
- Inline-редактирование остатка (quantity)

### Этап 3: Добавление и редактирование товаров
- Модалка «Добавить товар» с полями: название, SKU, модель, цена, остаток
- Модалка «Детали товара» с режимами просмотра и редактирования
- Загрузка изображений через `POST /opencart/images/upload`
- Сохранение описания, SEO-метаданных (meta_title, meta_description, meta_keyword)
- Запись файлов на сервер через `file/writeSafe`

### Этап 4: AI SEO Генератор
- Вкладка «AI SEO» с таблицей всех товаров
- DeepSeek AI интеграция (`deepseek-chat`) для генерации:
  - Описания товара (400-600 символов)
  - Meta Title (50-60 символов)
  - Meta Description (150-160 символов)
  - Keywords (5-7 слов)
- Batch-генерация: 1, 10, 100, 500 товаров за раз
- Геотаргетинг: Москва и Московская область
- Прогресс-бар, логи, превью сгенерированного контента

### Этап 5: 4-ценовая модель
- Добавлена колонка `price_non_cash` в таблицу `oc_openproduct`
- **Приход наличные** (`cash_price`) — ручной ввод
- **Приход безнал** (`non_cash_price`) — ручной ввод
- **Продажа наличные** (`price`) — ручной ввод
- **Продажа безнал** (`price_non_cash`) — авто: `price * 1.285` (+28.5%)
- Все 4 цены в CSV экспорт/импорт
- Авто-пересчет при изменении продажной наличной цены

### Этап 6: Характеристики (Attributes)
- 1645 атрибутов загружаются из OpenCart
- `product/attributes` — получение характеристик товара
- `product/updateAttributes` — сохранение характеристик
- UI: выпадающий список + поле значения + добавить/удалить
- Отображение характеристик в режиме просмотра

### Этап 7: Автодополнение (Smart Fill)
- Кнопка «Автодополнение» в модалке редактирования товара
- Генерирует: Описание + Meta Title + Meta Description + Keywords + Характеристики
- Характеристики определяются по ключевым словам в названии товара:
  - Штукатурка → Тип, Назначение, Вес, Основной компонент, Цвет, Свойства
  - Краска → Тип, Назначение, Цвет, Свойства
  - Грунтовка → Тип, Назначение, Свойства
  - Плитка → Тип, Назначение, Цвет
  - Цемент → Тип, Назначение, Вес
  - Гипс → Тип, Назначение, Вес

### Этап 8: 8 новых разделов AI Manager
- **Раздел 1: Конкуренты и ставки** (`competitors_bids.py`) — CRUD конкурентов, сканирование цен, сравнение с нашими товарами
- **Раздел 2: Бюджет и окупаемость** (`budget_roi.py`) — расчёт прибыли по бюджету, прогноз ROI, выбор товаров
- **Раздел 3: Акции и локомотивы** (`promotions.py`) — поиск связок товаров, создание акций со скидками
- **Раздел 4: Тендеры** (`tenders.py`) — поиск тендеров по региону, проверка покрытия товарами, генерация КП
- **Раздел 5: Отзывы и репутация** (`reviews.py`) — парсинг негативных отзывов о конкурентах, генерация коммерческих предложений
- **Раздел 6: Автосмета** (`autosmeta.py`) — распознавание сметы, сверка со складом, генерация счёта (нал / безнал)
- **Раздел 7: Контент-фабрика** (`content_factory.py`) — массовая генерация SEO-статей, очередь публикации в блог OpenCart
- **Раздел 8: Клиенты и объекты** (`clients_objects.py`) — клиенты из OpenCart, объекты строительства, прогноз потребности материалов по этапам
- **Раздел 9: Конструктор страниц** (`site_builder.py` + `SiteBuilder.jsx`) — drag-and-drop конструктор блоков для stroiapp.ru: hero, текст, товары, категории, картинки, видео, карусель, CTA, HTML
- Все разделы имеют полноценный backend (FastAPI) и frontend UI (React + Tailwind)
- Backend build проходит без ошибок, frontend Vite build успешен

---

## 3. ТЕКУЩЕЕ СОСТОЯНИЕ (Что работает сейчас)

### 3.1. Файлы проекта

| Файл | Путь | Назначение |
|------|------|------------|
| `ai_manager.php` | `stroiapp.ru/public_html/catalog/controller/api/ai_manager.php` | PHP API контроллер OpenCart |
| `opencart.py` | `ai.stroiapp.ru/backend/app/api/routes/opencart.py` | FastAPI маршруты для OpenCart |
| `ai_seo.py` | `ai.stroiapp.ru/backend/app/api/routes/ai_seo.py` | FastAPI маршруты для AI SEO |
| `competitors_bids.py` | `ai.stroiapp.ru/backend/app/api/routes/competitors_bids.py` | Конкуренты и ставки |
| `budget_roi.py` | `ai.stroiapp.ru/backend/app/api/routes/budget_roi.py` | Бюджет и окупаемость |
| `promotions.py` | `ai.stroiapp.ru/backend/app/api/routes/promotions.py` | Акции и локомотивы |
| `tenders.py` | `ai.stroiapp.ru/backend/app/api/routes/tenders.py` | Тендеры |
| `reviews.py` | `ai.stroiapp.ru/backend/app/api/routes/reviews.py` | Отзывы и репутация |
| `autosmeta.py` | `ai.stroiapp.ru/backend/app/api/routes/autosmeta.py` | Автосмета |
| `content_factory.py` | `ai.stroiapp.ru/backend/app/api/routes/content_factory.py` | Контент-фабрика |
| `clients_objects.py` | `ai.stroiapp.ru/backend/app/api/routes/clients_objects.py` | Клиенты и объекты |
| `ai_deepseek.py` | `ai.stroiapp.ru/backend/app/api/routes/ai_deepseek.py` | Универсальный DeepSeek API |
| `deepseek_client.py` | `ai.stroiapp.ru/backend/app/services/deepseek_client.py` | DeepSeek клиент (httpx) |
| `site_builder.py` | `ai.stroiapp.ru/backend/app/api/routes/site_builder.py` | Конструктор страниц (блоки) |
| `block_store.py` | `ai.stroiapp.ru/backend/app/db/block_store.py` | SQLite CRUD для блоков |
| `SiteBuilder.jsx` | `ai.stroiapp.ru/frontend/src/components/SiteBuilder.jsx` | Drag-and-drop конструктор |
| `main.jsx` | `ai.stroiapp.ru/frontend/src/main.jsx` | React frontend (все вкладки) |
| `api.js` | `ai.stroiapp.ru/frontend/src/lib/api.js` | Утилиты HTTP API |
| `.env` | `ai.stroiapp.ru/backend/.env` | Конфигурация (токены, URL) |

### 3.2. API Endpoints (FastAPI → OpenCart)

```
GET  /api/opencart/categories/list
GET  /api/opencart/products/byCategory?category_id={id}
GET  /api/opencart/products/{product_id}
POST /api/opencart/products/update
POST /api/opencart/products/add
POST /api/opencart/products/generateSeo       ← генерация описания+SEO+атрибуты
GET  /api/opencart/products/attributes?product_id={id}
POST /api/opencart/products/updateAttributes
GET  /api/opencart/attributes/list              ← 1645 атрибутов
POST /api/opencart/images/upload
POST /api/opencart/files/write
GET  /api/ai-seo/products                     ← для вкладки AI SEO
POST /api/ai-seo/generate                     ← DeepSeek AI генерация

# 8 новых разделов AI Manager
GET  /api/competitors-bids/status
POST /api/competitors-bids/add
POST /api/competitors-bids/scan
GET  /api/competitors-bids/list
POST /api/competitors-bids/import-prices
POST /api/competitors-bids/compare

POST /api/budget-roi/calculate
GET  /api/budget-roi/forecast

POST /api/promotions/find-bundles
POST /api/promotions/create
GET  /api/promotions/list

POST /api/tenders/search
POST /api/tenders/check-coverage
POST /api/tenders/submit

POST /api/reviews/parse-competitors
POST /api/reviews/generate-kp

POST /api/autosmeta/upload
POST /api/autosmeta/recognize
POST /api/autosmeta/generate-invoice

POST /api/content-factory/generate-articles
POST /api/content-factory/publish
GET  /api/content-factory/queue

POST /api/ai/deepseek/chat                 ← универсальный запрос к DeepSeek
POST /api/ai/deepseek/generate-article      ← генерация SEO-статьи
POST /api/ai/deepseek/generate-kp           ← генерация коммерческого предложения
GET  /api/ai/deepseek/status                ← статус подключения DeepSeek

GET  /api/clients-objects/clients
POST /api/clients-objects/add-object
GET  /api/clients-objects/objects
GET  /api/clients-objects/object/{id}/stages
POST /api/clients-objects/forecast-demand
POST /api/clients-objects/notify

POST /api/site-builder/blocks              ← создать блок
GET  /api/site-builder/blocks              ← список блоков страницы
GET  /api/site-builder/blocks/{id}          ← получить блок
PUT  /api/site-builder/blocks/{id}         ← обновить блок
DELETE /api/site-builder/blocks/{id}       ← удалить блок
POST /api/site-builder/reorder             ← изменить порядок блоков
GET  /api/site-builder/public/blocks       ← публичный API для stroiapp.ru
GET  /api/site-builder/block-types         ← список типов блоков
```

### 3.3. PHP Actions (OpenCart)

```
product/list
product/listByCategory
product/get
product/update
product/add
product/edit
product/attributes
product/updateAttributes
attribute/list
seo/generate
image/upload
file/writeSafe
file/readSafe
file/listSafe
category/list
category/tree
db/executeSql
customer/list
order/list
```

### 3.4. UI Вкладки (Frontend)

| Вкладка | Описание |
|---------|----------|
| **Главная** | Дашборд с KPI: товары, клиенты, заказы, конкуренты |
| **Товары** | Дерево категорий + карточки товаров + inline-edit + модалки |
| **AI SEO** | Таблица товаров + batch-генерация SEO через DeepSeek |
| **Аналитика** | Сравнение с конкурентами, графики |
| **Клиенты** | Список клиентов, фильтры |
| **Заказы** | Список заказов, обновление статусов |

### 3.5. База данных (OpenCart)

**Новые/измененные колонки:**
```sql
oc_openproduct:
  price_non_cash DECIMAL(15,4) NOT NULL DEFAULT '0.0000'  -- добавлена
  cash_price DECIMAL(15,4) NOT NULL DEFAULT '0.0000'     -- существовала
  non_cash_price DECIMAL(15,4) NOT NULL DEFAULT '0.0000'  -- существовала

oc_openproduct_attribute:
  product_id + attribute_id + language_id + text         -- стандартная OC
```

---

## 4. ТЕХНИЧЕСКИЙ СТЕК

### Frontend (ai.stroiapp.ru)
- **React 18** + Vite
- **Tailwind CSS** + кастомные utility-классы (`glass`, `glass-hover`)
- **Lucide React** — иконки (Sparkles, Plus, X, Image, Upload, etc.)
- **No Redux** — управление состоянием через `useState`/`useEffect`
- Toast-уведомления — кастомная система

### Backend (ai.stroiapp.ru)
- **Python 3.11**
- **FastAPI** + **Uvicorn**
- **httpx** — асинхронные HTTP-запросы к OpenCart
- **Pydantic** — валидация данных
- **python-dotenv** — конфигурация через `.env`

### OpenCart (stroiapp.ru)
- **OpenCart 3.x**
- **PHP 7.4**
- **MySQL** (база `ct45965_open`, префикс `oc_open`)

### Интеграции
- **DeepSeek AI** — генерация SEO-контента (API key в `.env`)
- **Яндекс.Директ** — рекламная аналитика (токен в `.env`)
- **DaData** — подсказки адресов (токен в `.env`)
- **Telegram Bot** — уведомления (токен + chat_id в `.env`)

---

## 5. КОНФИГУРАЦИЯ (.env)

```bash
APP_NAME="AI StroiApp Manager"
OPENCART_API_URL="https://stroiapp.ru"
OPENCART_API_TOKEN="change_this_ai_manager_token"
DEEPSEEK_API_KEY=""
YANDEX_DIRECT_TOKEN=""
DADATA_TOKEN=""
TELEGRAM_BOT_TOKEN=""
MANAGER_TELEGRAM_CHAT_ID=""
```

---

## 6. КАК ЗАПУСТИТЬ

### Backend (FastAPI):
```bash
cd ai.stroiapp.ru/backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### Frontend (React):
```bash
cd ai.stroiapp.ru/frontend
npm run dev   # порт 5173
```

### Открыть в браузере:
```
http://localhost:5173
```

---

## 6.5. LIVE SYNC — мгновенная синхронизация файлов с хостингом

Создана система автоматической загрузки изменённых файлов на production-хостинг `stroiapp.ru`.

### Как работает:
1. **Python-скрипт** (`scripts/live_sync.py`) отслеживает файловую систему через `watchdog`
2. При изменении любого `.php`, `.twig`, `.css`, `.js`, `.xml`, `.json` → файл мгновенно отправляется на хостинг через API `ai_manager.php`
3. После загрузки автоматически вызывается `site/clearCache` — кэш OpenCart сбрасывается
4. **Debounce**: изменения за 2 секунды группируются в один batch

### Файлы:
- `scripts/live_sync.py` — основной скрипт
- `scripts/sync.bat` — запуск watch-режима (двойной клик)
- `scripts/full_sync.bat` — полная заливка всех файлов
- `scripts/requirements.txt` — зависимости (`watchdog`, `requests`, `python-dotenv`)

### Запуск:
```bash
# Watch-режим (автоматическая синхронизация при сохранении)
cd ai.stroiapp.ru/scripts
pip install -r requirements.txt
python live_sync.py --watch

# Или двойным кликом: sync.bat

# Разовая полная синхронизация
python live_sync.py --full
# Или: full_sync.bat
```

### Настройка:
В `backend/.env` добавлены переменные:
```
OPENCART_SYNC_URL="https://stroiapp.ru"
OPENCART_SYNC_TOKEN="change_this_ai_manager_token"
```

---

## 7. БЕЗОПАСНОСТЬ

- **Токенная аутентификация** — все PHP endpoints проверяют `HTTP_AI_MANAGER_TOKEN`
- **Бэкапы файлов** — при записи через `file/writeSafe` создается `.bak` в `ai_backups/`
- **SQL-инъекции** — все запросы используют `$this->db->escape()` и `(int)` приведение
- **CORS** — настроен для `localhost:5173`

---

## 8. ПЛАНЫ НА БУДУЩЕЕ

- [ ] Интеграция с 1С для синхронизации остатков
- [ ] Автоматическое ценообразование на основе конкурентов
- [ ] Telegram-бот для уведомлений о заказах
- [ ] Мобильное приложение (React Native)
- [ ] ML-рекомендации товаров для клиентов
- [ ] Автоматическая генерация изображений через AI
- [ ] Интеграция с Яндекс.Маркет и Ozon

---

## 9. КЛЮЧЕВЫЕ КОНСТАНТЫ

```javascript
const MARKUP = 1.285;  // 28.5% наценка на безналичную продажу
const API_URL = "http://127.0.0.1:8010/api";  // Бэкенд FastAPI
```

---

## 10. КОНТАКТЫ / ДОСТУП

- **Публичный магазин**: https://stroiapp.ru
- **AI Менеджер**: http://localhost:5173 (локально)
- **OpenCart Admin**: https://stroiapp.ru/admin
- **API Token**: `change_this_ai_manager_token`

---

*Документ актуален на: 30 мая 2026*
*Последнее обновление: идеальная главная страница, блог, акции, Live Sync*
