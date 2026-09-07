"""Busca o HTML. httpx primeiro; Playwright so quando a pagina exige JS.

Regra do MVP: pagina publica ou nao monitora. Nada de login, captcha ou
burlar bloqueio. Se o site barrar, o cliente e avisado.
"""

import httpx

from . import config

HEADERS = {
    "User-Agent": config.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# Marcadores de pagina que so renderiza no browser (app shell vazio).
SPA_MARKERS = (
    'id="root"',
    'id="app"',
    'id="__next"',
    "data-reactroot",
    "ng-app",
    "__NUXT__",
)

BLOCK_STATUS = {401, 402, 403, 407, 429, 451}


class FetchError(Exception):
    """Falha esperada de coleta. A mensagem vai para o cliente."""


class BlockedError(FetchError):
    """O site recusou o acesso. Nao insista, avise o cliente."""


class NetworkError(FetchError):
    """Nao chegou resposta. Pode ser o site ou pode ser a SUA rede."""


def online(timeout: float = 5.0) -> bool:
    """Tem internet?

    Sem isso, uma queda de luz ou de Wi-Fi faz o Vigia culpar 29 sites de
    bloqueio e mandar 29 avisos errados para o cliente.
    """
    for url in ("https://api.telegram.org", "https://one.one.one.one"):
        try:
            httpx.head(url, timeout=timeout, follow_redirects=True)
            return True
        except httpx.HTTPError:
            continue
    return False


def fetch_http(url: str) -> str:
    try:
        with httpx.Client(
            headers=HEADERS,
            timeout=config.TIMEOUT_S,
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
    except httpx.HTTPError as exc:
        raise NetworkError(f"rede: {type(exc).__name__}: {exc}") from exc

    if resp.status_code in BLOCK_STATUS:
        raise BlockedError(f"site recusou o acesso (HTTP {resp.status_code})")
    if resp.status_code >= 400:
        raise FetchError(f"HTTP {resp.status_code}")

    ctype = resp.headers.get("content-type", "")
    if "html" not in ctype and "text" not in ctype and "json" not in ctype:
        raise FetchError(f"content-type nao textual: {ctype or 'desconhecido'}")
    return resp.text


def looks_empty(html: str, visible_text: str) -> bool:
    """Heuristica: HTML chegou, mas o conteudo vem por JS."""
    if len(visible_text) >= 400:
        return False
    return any(marker in html for marker in SPA_MARKERS) or len(visible_text) < 120


def fetch_browser(url: str) -> str:
    """Renderiza com Playwright. Import tardio: dependencia opcional."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - ambiente sem playwright
        raise FetchError(
            "pagina exige JS e o Playwright nao esta instalado "
            "(pip install playwright && python -m playwright install chromium)"
        ) from exc

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(user_agent=config.USER_AGENT, locale="pt-BR")
            page.goto(url, wait_until="networkidle", timeout=int(config.TIMEOUT_S * 1000))
            return page.content()
        except Exception as exc:  # noqa: BLE001 - falha de render vira FetchError
            raise FetchError(f"playwright: {exc}") from exc
        finally:
            browser.close()
