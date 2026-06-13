# Kira Perplexity Scout — MCP-сервер

Подключает Perplexity как помощника прямо в инструменты Claude/Cowork.
Даёт 3 инструмента: `perplexity_search`, `kira_trend_scout`, `perplexity_deep`.

---

## Что внутри
- `server.py` — сам MCP-сервер (Perplexity Sonar API → MCP-инструменты)
- `requirements.txt` — зависимости
- `.env.example` — шаблон для API-ключа
- `Procfile` — команда запуска для хостинга

---

## Шаг 1. Получить API-ключ Perplexity
1. Зайди на **perplexity.ai → Settings → API** (нужен аккаунт; для API нужен платный тариф/кредиты).
2. Создай ключ. Он выглядит как `pplx-xxxxxxxx...`
3. Сохрани — он понадобится на деплое.

---

## Шаг 2. Задеплоить сервер (вариант через Render — бесплатно и без терминала)

Claude connectors требуют **публичный HTTPS-URL**, поэтому сервер надо разместить онлайн.
Самый простой путь — Render:

1. Залей папку `perplexity-mcp` в новый репозиторий на GitHub
   (или используй любой git-хостинг).
2. Зайди на **render.com → New → Web Service** и подключи репозиторий.
3. Настройки:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python server.py`
4. В разделе **Environment** добавь переменную:
   - `PERPLEXITY_API_KEY` = твой ключ `pplx-...`
5. Нажми **Deploy**. Render выдаст URL вида
   `https://kira-perplexity-scout.onrender.com`
6. Твой MCP-endpoint будет:
   `https://kira-perplexity-scout.onrender.com/mcp`

> Альтернатива без GitHub: Railway, Fly.io — логика та же (env-переменная + start command).
> Локальный запуск (`python server.py`) тоже работает, но тогда нужен туннель (ngrok),
> чтобы дать Claude публичный HTTPS-адрес.

---

## Шаг 3. Подключить к Cowork / Claude
1. В Claude открой **Settings → Connectors → Add custom connector**.
2. Вставь URL endpoint: `https://...onrender.com/mcp`
3. Тип транспорта: **Streamable HTTP** (сервер уже на нём).
4. Сохрани и включи коннектор в чате.

После этого в моём списке инструментов появятся:
- `perplexity_search(query, recency)` — быстрый поиск с источниками
- `kira_trend_scout(topic, recency)` — тренд-бриф под Киру
- `perplexity_deep(query)` — глубокий ресёрч

---

## Шаг 4. Проверка
Напиши мне: «Запусти kira_trend_scout по теме AI-инструменты, свежесть week».
Если коннектор подключён — я вызову Perplexity и верну бриф с источниками.

---

## Безопасность
- Ключ `PERPLEXITY_API_KEY` хранится только в env хостинга, в коде его нет.
- Не коммить `.env` в git (добавь его в `.gitignore`).
- Если ключ утёк — отзови его в Settings Perplexity и создай новый.
