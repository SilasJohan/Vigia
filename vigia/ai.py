"""Classificacao do diff: isso importa ou e lixo?

Ordem de tentativa (todos com free tier sem cartao): Groq -> Gemini -> Ollama
local -> heuristica por regex. A heuristica existe para o bot nunca ficar
mudo quando a API cair.
"""

import json
import re

import httpx

from . import config
from .extract import LIMIT, PLAN_WORD, PRICE

SYSTEM = (
    "Voce e um analista de inteligencia competitiva. Recebe o diff do texto "
    "visivel de uma pagina publica de um concorrente e decide se a mudanca "
    "interessa a quem vende no mesmo mercado.\n"
    "IMPORTA: preco, valor de plano, moeda, desconto/promocao, novo plano ou "
    "plano removido, limite do plano gratis, limite de uso/assentos, feature "
    "adicionada ou retirada, mudanca de posicionamento na headline, frete, "
    "parcelamento, estoque/disponibilidade.\n"
    "NAO IMPORTA: banner de cookie, aviso de LGPD, newsletter, data/hora, "
    "contador de visitas, escassez falsa, texto de rodape, links de rede "
    "social, mudanca de ordem sem mudanca de conteudo, erro de renderizacao.\n"
    "Responda SOMENTE com JSON: "
    '{"important": true|false, "category": "price|plan|feature|copy|stock|noise", '
    '"summary": "uma frase curta, em portugues, dizendo o que mudou (valor antigo -> novo quando houver)"}'
)

CATEGORIES = {"price", "plan", "feature", "copy", "stock", "noise"}


def _prompt(url: str, mode: str, diff: str) -> str:
    return (
        f"URL: {url}\nModo: {mode}\n"
        "Diff (linhas com - sao o texto antigo, + o novo):\n"
        f"```\n{diff[:6000]}\n```"
    )


def _parse(raw: str) -> dict | None:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    category = str(data.get("category", "")).lower()
    return {
        "important": bool(data.get("important")),
        "category": category if category in CATEGORIES else "copy",
        "summary": str(data.get("summary", "")).strip()[:500] or "Mudanca detectada.",
        "engine": "ia",
    }


def _groq(url, mode, diff):
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={
            "model": config.GROQ_MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": _prompt(url, mode, diff)},
            ],
        },
        timeout=45,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _gemini(url, mode, diff):
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent"
    )
    resp = httpx.post(
        endpoint,
        headers={"x-goog-api-key": config.GEMINI_API_KEY},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"parts": [{"text": _prompt(url, mode, diff)}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
        timeout=45,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


_ollama_cache: dict = {}


def ollama_models() -> list[str]:
    """O que esta realmente instalado. Cacheado por processo."""
    if "lista" not in _ollama_cache:
        try:
            resp = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
            resp.raise_for_status()
            _ollama_cache["lista"] = [
                m["name"] for m in resp.json().get("models", []) if m.get("name")
            ]
        except Exception:  # noqa: BLE001 - ollama desligado nao e erro fatal
            _ollama_cache["lista"] = []
    return _ollama_cache["lista"]


def ollama_model() -> str | None:
    """Resolve o modelo a usar.

    Apontar para um modelo que nao esta instalado e o erro mais chato do Ollama:
    ele responde 404 e parece que o servidor esta fora. Aqui, se o modelo do .env
    nao existir, usamos o que existe - preferindo um modelo local, porque modelo
    '-cloud' depende de login e tem cota.
    """
    disponiveis = ollama_models()
    if not disponiveis:
        return None
    pedido = config.OLLAMA_MODEL
    if pedido and any(m == pedido or m.startswith(f"{pedido}:") for m in disponiveis):
        return pedido
    locais = [m for m in disponiveis if not m.endswith("-cloud")]
    escolhido = (locais or disponiveis)[0]
    if pedido:
        print(f"  [ia] modelo '{pedido}' nao esta instalado; usando '{escolhido}'")
    return escolhido


def _ollama(url, mode, diff):
    modelo = ollama_model()
    if not modelo:
        raise RuntimeError("ollama sem modelo instalado (rode: ollama pull qwen2.5:7b)")
    resp = httpx.post(
        f"{config.OLLAMA_URL}/api/generate",
        json={
            "model": modelo,
            "system": SYSTEM,
            "prompt": _prompt(url, mode, diff),
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def heuristic(diff: str) -> dict:
    """Sem IA: regex decide. Conservador, mas nunca fica mudo."""
    removed, added = [], []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())

    blob = "\n".join(removed + added)
    if PRICE.search(blob):
        category, important = "price", True
    elif PLAN_WORD.search(blob) or LIMIT.search(blob):
        category, important = "plan", True
    else:
        category, important = "copy", False

    # O resumo mostra a linha com preco antes de qualquer outra.
    def pick(lines):
        return next((line for line in lines if PRICE.search(line)), None) or next(
            (line for line in lines if line), None
        )

    before, after = pick(removed), pick(added)
    if before and after:
        detail = f"{before[:90]} -> {after[:90]}"
    else:
        detail = (before or after or "")[:180]
    return {
        "important": important,
        "category": category,
        "summary": f"[sem IA] {detail}" if detail else "[sem IA] Mudanca detectada.",
        "engine": "regex",
    }


def providers():
    """Ollama primeiro, de proposito.

    Modelo local nao tem chave, nao tem cota e nao tem fatura - e o unico trilho
    que nao te deixa na mao no meio do mes. Groq e Gemini ficam como rede de
    seguranca para quando o Ollama estiver desligado.
    """
    order = []
    if config.AI_PROVIDER in ("auto", "ollama"):
        order.append(("ollama", _ollama))
    if config.AI_PROVIDER in ("auto", "groq") and config.GROQ_API_KEY:
        order.append(("groq", _groq))
    if config.AI_PROVIDER in ("auto", "gemini") and config.GEMINI_API_KEY:
        order.append(("gemini", _gemini))
    return order


def classify(url: str, mode: str, diff: str) -> dict:
    for name, call in providers():
        try:
            parsed = _parse(call(url, mode, diff))
        except Exception as exc:  # noqa: BLE001 - provider ruim nao derruba o ciclo
            print(f"  [ia] {name} falhou: {type(exc).__name__}: {exc}")
            continue
        if parsed:
            parsed["engine"] = name
            return parsed
    return heuristic(diff)
