"""
Kira Trend Scout — Perplexity MCP Server
=========================================
Оборачивает Perplexity Sonar API в MCP-инструменты, которые можно
подключить к Cowork / Claude как кастомный коннектор.

Транспорт: streamable-http (для удалённого хостинга и для Claude connectors).
Авторизация Perplexity: переменная окружения PERPLEXITY_API_KEY.

Инструменты:
  - perplexity_search   : быстрый веб-grounded поиск с источниками
  - kira_trend_scout    : тренд-ресёрч под нишу Киры (готовый бриф)
  - perplexity_deep     : глубокий многошаговый ресёрч (sonar-deep-research)
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

PPLX_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
PPLX_URL = "https://api.perplexity.ai/chat/completions"

# host/port берутся из окружения хостинга (Render/Railway задают PORT сами)
mcp = FastMCP(
    name="Kira Perplexity Scout",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
)


def _call_perplexity(model: str, system: str, user: str, recency: str | None = None) -> str:
    """Низкоуровневый вызов Perplexity Chat Completions с цитированием источников."""
    if not PPLX_API_KEY:
        return "Ошибка: не задан PERPLEXITY_API_KEY в окружении сервера."

    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "return_citations": True,
    }
    if recency:
        # day | week | month | year — ограничивает свежесть источников
        payload["search_recency_filter"] = recency

    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(PPLX_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        return f"Perplexity API вернул ошибку {e.response.status_code}: {e.response.text[:500]}"
    except Exception as e:  # noqa: BLE001
        return f"Не удалось обратиться к Perplexity: {e}"

    answer = data["choices"][0]["message"]["content"]

    # Источники приходят в citations (список URL)
    citations = data.get("citations") or []
    if citations:
        src = "\n".join(f"[{i + 1}] {u}" for i, u in enumerate(citations))
        answer += f"\n\nИсточники:\n{src}"
    return answer


@mcp.tool()
def perplexity_search(query: str, recency: str = "month") -> str:
    """
    Быстрый веб-grounded поиск через Perplexity (sonar-pro) с источниками.

    Args:
        query: Поисковый запрос на любом языке.
        recency: Свежесть источников — "day", "week", "month" или "year".
    """
    system = (
        "Ты ресёрч-ассистент. Отвечай кратко, структурно и фактологично. "
        "Всегда опирайся на свежие источники и не выдумывай данные."
    )
    return _call_perplexity("sonar-pro", system, query, recency=recency)


@mcp.tool()
def kira_trend_scout(topic: str = "", recency: str = "week") -> str:
    """
    Тренд-ресёрч под персонажа Киру: тренды, эстетики, форматы, темы для контента.
    Возвращает готовый бриф, пригодный для контент-плана и сценариев.

    Args:
        topic: Узкая тема/ниша (напр. "AI-инструменты для девушек", "digital-эстетика").
               Пусто = общий скан ниши Киры.
        recency: Свежесть трендов — "day", "week", "month".
    """
    niche = topic.strip() or (
        "нейросети и AI-инструменты, digital-профессии, самореализация, "
        "эстетика современной жизни, контент-мейкинг для девушек 18–30"
    )
    system = (
        "Ты — Kira Trend Scout, тренд-аналитик digital-персонажа Киры. "
        "Кира — современный умный AI-персонаж для девушек, интересующихся "
        "нейросетями, digital-инструментами и эстетикой. Тон: живой, умный, "
        "небанальный, без мотивационных клише и шаблонного AI-стиля. "
        "Каждый тренд должен быть пригоден для реального короткого видео."
    )
    user = (
        f"Найди 5–7 актуальных трендов и тем по нише: {niche}.\n"
        "Для каждого тренда дай строго:\n"
        "1) Название тренда (коротко и цепко)\n"
        "2) Почему сейчас взлетает (1–2 предложения, с опорой на источник)\n"
        "3) Идея видео для Киры (хук + суть, 1 предложение)\n"
        "4) Эстетика/визуальное направление (для Higgsfield/HeyGen)\n"
        "Пиши на русском. В конце добавь источники."
    )
    return _call_perplexity("sonar-pro", system, user, recency=recency)


@mcp.tool()
def perplexity_deep(query: str) -> str:
    """
    Глубокий многошаговый ресёрч (sonar-deep-research). Медленнее, но даёт
    развёрнутый отчёт с множеством источников. Для серьёзных тем/разборов.

    Args:
        query: Тема для глубокого исследования.
    """
    system = (
        "Ты — аналитик. Сделай развёрнутый, структурированный отчёт "
        "с разделами, фактами и источниками. Без воды."
    )
    return _call_perplexity("sonar-deep-research", system, query)


if __name__ == "__main__":
    # streamable-http — то, что нужно для подключения как remote MCP / Claude connector
    mcp.run(transport="streamable-http")
