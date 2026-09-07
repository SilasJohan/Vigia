import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(ROOT / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "").strip()

AI_PROVIDER = os.environ.get("AI_PROVIDER", "auto").strip().lower()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b").strip()

MIN_INTERVAL_MIN = _int("MIN_INTERVAL_MIN", 360)
REQUEST_DELAY_S = _float("REQUEST_DELAY_S", 2.0)
MIN_DIFF_CHARS = _int("MIN_DIFF_CHARS", 40)

BOT_INFO_URL = os.environ.get("BOT_INFO_URL", "https://github.com/SilasJohan/vigia").strip()
USER_AGENT = f"VigiaBot/0.1 (+{BOT_INFO_URL})"

DB_PATH = Path(os.environ.get("VIGIA_DB") or (ROOT / "vigia.db"))
TIMEOUT_S = 25.0

# Limites por plano: (max_urls, intervalo_minimo_min)
PLANS = {
    "trial": (10, 360),
    "starter": (10, 360),
    "pro": (40, 60),
    "loja": (100, 360),
}
TRIAL_DAYS = 7
