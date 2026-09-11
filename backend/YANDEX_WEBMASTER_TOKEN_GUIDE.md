# Инструкция: получение токена Yandex Webmaster API

## Шаг 1: Создать OAuth-приложение

1. Откройте: https://oauth.yandex.ru/client/new
2. Заполните:
   - **Название приложения**: `StroiApp Webmaster`
   - **Платформы**: поставьте галочку **Веб-сервисы**
   - **Redirect URI**: `https://oauth.yandex.ru/verification_code`
   - **Доступы** (в поиске наберите "webmaster"):
     - `webmaster:read` — чтение данных
     - `webmaster:write` — запись (добавление sitemap, запрос переобхода)
     - `webmaster:verify` — подтверждение владения сайтом
   - Также добавьте (опционально):
     - `searchapi:read` — поиск (если нужен Search API)
3. Нажмите **Создать приложение**
4. Скопируйте **ClientID** (например `abc123def456...`)

## Шаг 2: Получить код авторизации

Откройте в браузере (замените CLIENT_ID на ваш):

```
https://oauth.yandex.ru/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=https://oauth.yandex.ru/verification_code
```

Войдите под аккаунтом `stroiapp`, разрешите доступ. Появится код — скопируйте его.

## Шаг 3: Обменять код на токен

Выполните (замените CLIENT_ID, CLIENT_SECRET, CODE):

```bash
curl -X POST https://oauth.yandex.ru/token ^
  -d "grant_type=authorization_code" ^
  -d "code=CODE" ^
  -d "client_id=CLIENT_ID" ^
  -d "client_secret=CLIENT_SECRET"
```

В ответе будет `access_token` — это и есть токен Webmaster API.

## Шаг 4: Сохранить токен

Добавьте в `backend/.env`:
```
YANDEX_WEBMASTER_TOKEN="y0_AgAAA..."
```

## Что даст токен:

- Автоматическое добавление sitemap
- Запрос переобхода страниц (ускорит индексацию гео-страниц)
- Мониторинг статуса индексации
- Проверка видимости в поиске
