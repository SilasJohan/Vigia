import sqlite3
from datetime import datetime, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
    chat_id     TEXT PRIMARY KEY,
    handle      TEXT,
    plan        TEXT NOT NULL DEFAULT 'trial',
    trial_start TEXT,
    paid_until  TEXT,
    lang        TEXT NOT NULL DEFAULT 'pt',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      TEXT NOT NULL,
    url          TEXT NOT NULL,
    label        TEXT,
    mode         TEXT NOT NULL DEFAULT 'pricing',
    css          TEXT,
    interval_min INTEGER NOT NULL,
    last_hash    TEXT,
    last_text    TEXT,
    last_check   TEXT,
    last_error   TEXT,
    fail_count   INTEGER NOT NULL DEFAULT 0,
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL,
    UNIQUE(chat_id, url)
);

CREATE TABLE IF NOT EXISTS changes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id  INTEGER NOT NULL REFERENCES watches(id),
    ts        TEXT NOT NULL,
    category  TEXT,
    important INTEGER NOT NULL DEFAULT 0,
    summary   TEXT,
    diff      TEXT,
    notified  INTEGER NOT NULL DEFAULT 0,
    feedback  TEXT
);

CREATE INDEX IF NOT EXISTS idx_changes_watch ON changes(watch_id, ts);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Colunas adicionadas depois. ALTER falha se ja existe, e isso e esperado.
MIGRATIONS = [
    "ALTER TABLE watches ADD COLUMN check_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE watches ADD COLUMN observando_desde TEXT",
]


def connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # coluna ja existe
    conn.commit()
    return conn


# --- meta (offset do long polling, etc.) ---

def meta_get(conn, key, default=None):
    row = conn.execute("SELECT v FROM meta WHERE k = ?", (key,)).fetchone()
    return row["v"] if row else default


def meta_set(conn, key, value):
    conn.execute(
        "INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v",
        (key, str(value)),
    )
    conn.commit()


# --- assinantes ---

def ensure_subscriber(conn, chat_id, handle=None, lang="pt"):
    chat_id = str(chat_id)
    row = conn.execute("SELECT * FROM subscribers WHERE chat_id = ?", (chat_id,)).fetchone()
    if row:
        if handle and handle != row["handle"]:
            conn.execute("UPDATE subscribers SET handle = ? WHERE chat_id = ?", (handle, chat_id))
            conn.commit()
        return row
    conn.execute(
        "INSERT INTO subscribers(chat_id, handle, plan, trial_start, lang, created_at)"
        " VALUES(?, ?, 'trial', ?, ?, ?)",
        (chat_id, handle, now(), lang, now()),
    )
    conn.commit()
    return conn.execute("SELECT * FROM subscribers WHERE chat_id = ?", (chat_id,)).fetchone()


def set_plan(conn, chat_id, plan, paid_until=None):
    conn.execute(
        "UPDATE subscribers SET plan = ?, paid_until = ? WHERE chat_id = ?",
        (plan, paid_until, str(chat_id)),
    )
    conn.commit()


def subscribers(conn):
    return conn.execute("SELECT * FROM subscribers ORDER BY created_at").fetchall()


# --- watches ---

def add_watch(conn, chat_id, url, mode="pricing", css=None, label=None, interval_min=None):
    interval_min = max(int(interval_min or config.MIN_INTERVAL_MIN), config.MIN_INTERVAL_MIN)
    conn.execute(
        "INSERT INTO watches(chat_id, url, label, mode, css, interval_min, created_at)"
        " VALUES(?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(chat_id, url) DO UPDATE SET"
        "   active = 1, mode = excluded.mode, css = excluded.css,"
        "   label = COALESCE(excluded.label, watches.label)",
        (str(chat_id), url, label, mode, css, interval_min, now()),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM watches WHERE chat_id = ? AND url = ?", (str(chat_id), url)
    ).fetchone()


def list_watches(conn, chat_id=None, only_active=True):
    sql = "SELECT * FROM watches WHERE 1=1"
    args = []
    if chat_id is not None:
        sql += " AND chat_id = ?"
        args.append(str(chat_id))
    if only_active:
        sql += " AND active = 1"
    return conn.execute(sql + " ORDER BY id", args).fetchall()


def due_watches(conn, force=False):
    rows = list_watches(conn)
    if force:
        return rows
    due = []
    for row in rows:
        if not row["last_check"]:
            due.append(row)
            continue
        try:
            last = datetime.fromisoformat(row["last_check"])
        except ValueError:
            due.append(row)
            continue
        age_min = (datetime.now(timezone.utc) - last).total_seconds() / 60
        if age_min >= row["interval_min"]:
            due.append(row)
    return due


def save_state(conn, watch_id, text_hash, text):
    """Grava o estado e conta a leitura.

    check_count e observando_desde existem para a DM: "verifiquei esta pagina
    84 vezes em 21 dias" e evidencia; "eu acompanhei" e conversa.
    """
    conn.execute(
        "UPDATE watches SET last_hash = ?, last_text = ?, last_check = ?,"
        " last_error = NULL, fail_count = 0,"
        " check_count = COALESCE(check_count, 0) + 1,"
        " observando_desde = COALESCE(observando_desde, ?) WHERE id = ?",
        (text_hash, text, now(), now(), watch_id),
    )
    conn.commit()


def save_error(conn, watch_id, error):
    conn.execute(
        "UPDATE watches SET last_check = ?, last_error = ?, fail_count = fail_count + 1"
        " WHERE id = ?",
        (now(), str(error)[:500], watch_id),
    )
    conn.commit()


def stop_watch(conn, chat_id, watch_id):
    cur = conn.execute(
        "UPDATE watches SET active = 0 WHERE id = ? AND chat_id = ?",
        (watch_id, str(chat_id)),
    )
    conn.commit()
    return cur.rowcount


def set_mode(conn, chat_id, mode, watch_id=None):
    if watch_id:
        cur = conn.execute(
            "UPDATE watches SET mode = ? WHERE id = ? AND chat_id = ?",
            (mode, watch_id, str(chat_id)),
        )
    else:
        cur = conn.execute(
            "UPDATE watches SET mode = ? WHERE chat_id = ? AND active = 1",
            (mode, str(chat_id)),
        )
    conn.commit()
    return cur.rowcount


# --- mudancas ---

def record_change(conn, watch_id, diff, summary, important, category, notified=0):
    cur = conn.execute(
        "INSERT INTO changes(watch_id, ts, category, important, summary, diff, notified)"
        " VALUES(?, ?, ?, ?, ?, ?, ?)",
        (watch_id, now(), category, 1 if important else 0, summary, diff[:8000], notified),
    )
    conn.commit()
    return cur.lastrowid


def mark_notified(conn, change_id):
    conn.execute("UPDATE changes SET notified = 1 WHERE id = ?", (change_id,))
    conn.commit()


def set_feedback(conn, change_id, feedback):
    conn.execute("UPDATE changes SET feedback = ? WHERE id = ?", (feedback, change_id))
    conn.commit()


def recent_changes(conn, chat_id=None, limit=20, important_only=False):
    sql = (
        "SELECT c.*, w.url, w.label, w.chat_id FROM changes c"
        " JOIN watches w ON w.id = c.watch_id WHERE 1=1"
    )
    args = []
    if chat_id is not None:
        sql += " AND w.chat_id = ?"
        args.append(str(chat_id))
    if important_only:
        sql += " AND c.important = 1"
    sql += " ORDER BY c.ts DESC LIMIT ?"
    args.append(limit)
    return conn.execute(sql, args).fetchall()


def watch_history(conn, watch_id):
    """Quantas vezes esta pagina ja mudou, e quando foi a anterior.

    E o que responde 'mudou de verdade?': pagina que muda toda semana e ruido
    estrutural; pagina parada 40 dias que mexe no preco e noticia.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS total, MIN(ts) AS primeira FROM changes"
        " WHERE watch_id = ? AND important = 1",
        (watch_id,),
    ).fetchone()
    anterior = conn.execute(
        "SELECT ts FROM changes WHERE watch_id = ? AND important = 1"
        " ORDER BY ts DESC LIMIT 1 OFFSET 1",
        (watch_id,),
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "primeira": row["primeira"],
        "anterior": anterior["ts"] if anterior else None,
    }


def changes_por_dia(conn, dias=30):
    """Serie de mudancas importantes por pagina, para medir se o mercado se move."""
    return conn.execute(
        "SELECT w.id, w.label, w.url, w.created_at,"
        "       COUNT(c.id) AS mudancas,"
        "       MAX(c.ts) AS ultima,"
        "       SUM(CASE WHEN c.category = 'price' THEN 1 ELSE 0 END) AS preco,"
        "       SUM(CASE WHEN c.category IN ('plan','feature') THEN 1 ELSE 0 END) AS plano,"
        "       SUM(CASE WHEN c.feedback = 'lixo' THEN 1 ELSE 0 END) AS lixo"
        " FROM watches w"
        " LEFT JOIN changes c ON c.watch_id = w.id AND c.important = 1"
        "      AND c.ts >= datetime('now', ?)"
        " GROUP BY w.id ORDER BY mudancas DESC, w.label",
        (f"-{int(dias)} days",),
    ).fetchall()


def noise_rate(conn):
    row = conn.execute(
        "SELECT COUNT(*) AS total,"
        " SUM(CASE WHEN feedback = 'lixo' THEN 1 ELSE 0 END) AS junk"
        " FROM changes WHERE notified = 1"
    ).fetchone()
    total = row["total"] or 0
    junk = row["junk"] or 0
    return total, junk, (junk / total if total else 0.0)
