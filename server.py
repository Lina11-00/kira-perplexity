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


@mcp.tool()
def instagram_trends(topic: str = "", recency: str = "week") -> str:
    """
    Тренды Instagram под Киру: форматы Reels, тренды-аудио, хэштеги, хуки,
    что постят похожие AI-персонажи. Готово к контент-плану.

    Args:
        topic: Узкая тема/ниша. Пусто = общая ниша Киры.
        recency: "day", "week", "month".
    """
    niche = topic.strip() or (
        "AI-инструменты, нейросети, digital-эстетика, beauty-tech, "
        "онлайн-профессии для девушек 18–30"
    )
    system = (
        "Ты — Instagram-аналитик digital-персонажа Киры. Отслеживаешь, что "
        "реально залетает в Reels именно сейчас. Тон живой и небанальный, без "
        "клише. Каждый тренд должен быть пригоден для производства короткого видео."
    )
    user = (
        f"Найди актуальные тренды Instagram Reels по нише: {niche}.\n"
        "Дай 5–7 пунктов, для каждого строго:\n"
        "1) Формат/тренд (коротко)\n"
        "2) Почему залетает сейчас (1–2 предложения, со ссылкой)\n"
        "3) Тренд-аудио или приём, если есть\n"
        "4) 1–2 хэштега\n"
        "5) Хук для Киры под этот формат (1 предложение)\n"
        "Пиши на русском. В конце — источники."
    )
    return _call_perplexity("sonar-pro", system, user, recency=recency)


@mcp.tool()
def kira_script_research(topic: str, recency: str = "month") -> str:
    """
    Ресёрч под сценарий видео Киры: факты, статистика, готовые хуки, углы захода
    и скелет сценария. Финальный текст в голосе Киры пишется отдельно.

    Args:
        topic: Тема видео.
        recency: Свежесть фактов — "week", "month", "year".
    """
    system = (
        "Ты — ресёрч-редактор для сценариев Киры. Кира — умный современный "
        "AI-персонаж для девушек про нейросети и digital. Дай фактуру и структуру "
        "для сценария, без воды и без мотивационных клише. Всё с опорой на источники."
    )
    user = (
        f"Собери ресёрч для короткого видео (Reels/Shorts) на тему: {topic}.\n"
        "Дай строго:\n"
        "1) 5 проверенных фактов/цифр по теме (с источниками)\n"
        "2) 5 вариантов хука (первая фраза видео)\n"
        "3) 3 угла захода (под какой смысл раскрывать тему)\n"
        "4) Скелет сценария: Хук → 3 смысловых блока → CTA\n"
        "5) Частые ошибки/мифы по теме, которые можно опровергнуть\n"
        "Пиши на русском. В конце — источники."
    )
    return _call_perplexity("sonar-pro", system, user, recency=recency)


@mcp.tool()
def kira_look_research(theme: str, recency: str = "month") -> str:
    """
    Ресёрч образа/визуала Киры: эстетика, fashion-референсы, палитра, свет,
    локации, стайлинг. Формат удобен для перевода в ТЗ для Higgsfield.

    Args:
        theme: Тема/направление образа (напр. "digital it-girl", "old money + AI").
        recency: "month", "year".
    """
    system = (
        "Ты — визуальный ресёрчер для AI-персонажа Киры. Описывай эстетики "
        "конкретно и предметно, как для художника-постановщика. Любой референс "
        "должен переводиться в понятное визуальное ТЗ."
    )
    user = (
        f"Сделай визуальный ресёрч по образу/эстетике: {theme}.\n"
        "Дай строго:\n"
        "1) Суть эстетики в 2 предложениях\n"
        "2) Цветовая палитра (4–6 цветов словами)\n"
        "3) Свет и атмосфера\n"
        "4) Одежда/стайлинг/детали\n"
        "5) Локации/фон\n"
        "6) Какие визуальные направления сейчас в тренде в этой эстетике (со ссылками)\n"
        "Пиши на русском. В конце — источники."
    )
    return _call_perplexity("sonar-pro", system, user, recency=recency)


@mcp.tool()
def bot_script_research(goal: str, recency: str = "month") -> str:
    """
    Ресёрч под сценарии бота/DM-воронки Киры: заходы, отработка возражений,
    призывы, лид-магниты, что реально работает. Тексты бота собираются отдельно.

    Args:
        goal: Цель воронки (напр. "прогрев на покупку курса", "сбор заявок").
        recency: "month", "year".
    """
    system = (
        "Ты — ресёрчер по DM-воронкам и чат-ботам. Дай практику, что работает "
        "сейчас в прогревах и автоворонках в соцсетях. Конкретно, без воды, "
        "с опорой на источники и реальные приёмы."
    )
    user = (
        f"Собери ресёрч для сценария бота/DM-воронки с целью: {goal}.\n"
        "Дай строго:\n"
        "1) 3 варианта приветственного сообщения (заход)\n"
        "2) Логика воронки по шагам (что за чем)\n"
        "3) Частые возражения и как их отрабатывать\n"
        "4) Призывы к действию (CTA), что конвертит\n"
        "5) Идеи лид-магнита под эту цель\n"
        "Пиши на русском. В конце — источники."
    )
    return _call_perplexity("sonar-pro", system, user, recency=recency)


if __name__ == "__main__":
    # streamable-http — то, что нужно для подключения как remote MCP / Claude connector
    mcp.run(transport="streamable-http")
