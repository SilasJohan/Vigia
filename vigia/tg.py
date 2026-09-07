"""Telegram Bot API na mao (httpx). Sem SDK: menos dependencia, menos surpresa."""

import html as htmllib

import httpx

from . import config

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramError(Exception):
    pass


def call(method: str, http_timeout: float = 30, **params):
    if not config.TELEGRAM_TOKEN:
        raise TelegramError("TELEGRAM_TOKEN vazio. Copie .env.example para .env.")
    params = {k: v for k, v in params.items() if v is not None}
    resp = httpx.post(
        API.format(token=config.TELEGRAM_TOKEN, method=method),
        json=params,
        timeout=http_timeout,
    )
    data = resp.json()
    if not data.get("ok"):
        raise TelegramError(f"{method}: {data.get('description')}")
    return data["result"]


def send(chat_id, text: str, preview: bool = False, markup: dict | None = None):
    return call(
        "sendMessage",
        chat_id=str(chat_id),
        text=text[:4000],
        parse_mode="HTML",
        link_preview_options={"is_disabled": not preview},
        reply_markup=markup,
    )


def send_admin(text: str):
    if config.ADMIN_CHAT_ID:
        try:
            send(config.ADMIN_CHAT_ID, text)
        except TelegramError as exc:
            print(f"[tg] admin: {exc}")


def get_updates(offset: int | None = None, poll: int = 50):
    """Long polling: a conexao fica aberta ate `poll` segundos."""
    return call(
        "getUpdates",
        http_timeout=poll + 15,
        offset=offset,
        timeout=poll,
        allowed_updates=["message", "callback_query"],
    )


def answer_callback(callback_id: str, text: str = ""):
    return call("answerCallbackQuery", callback_query_id=callback_id, text=text)


def esc(text: str) -> str:
    return htmllib.escape(str(text), quote=False)
