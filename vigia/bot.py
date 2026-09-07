"""Bot do Telegram por long polling. Onboarding sem landing page:
/start -> cola URL -> comeca.
"""

import re
import time
import traceback
from datetime import datetime, timedelta, timezone

from . import config, db, runner, tg

URL_RE = re.compile(r"https?://[^\s<>\"]+", re.I)
MODES = ("pricing", "product", "page")

WELCOME = (
    "👁 <b>Vigia</b>\n"
    "Eu olho a pagina do seu concorrente e te aviso <b>so quando muda o que importa</b>: "
    "preco, plano, limite do free, feature.\n\n"
    "<b>Comece agora:</b> cole aqui a URL da pagina de preco de um concorrente.\n"
    "Exemplo: <code>https://www.notion.com/pricing</code>\n\n"
    f"Teste gratis de {config.TRIAL_DAYS} dias, ate 10 URLs. Depois R$49/mes ou US$9/mes.\n"
    "Cancelar e uma mensagem: /stop\n\n"
    "/ajuda para todos os comandos."
)

HELP = (
    "<b>Comandos</b>\n"
    "Cole uma URL — comeco a monitorar\n"
    "/list — suas paginas monitoradas\n"
    "/stop &lt;id&gt; — para uma pagina\n"
    "/mode pricing|product|page [id] — o que eu considero relevante\n"
    "/agora — checa suas paginas na hora\n"
    "/preco — planos e pagamento\n"
    "/lixo_&lt;n&gt; — marca um alerta como inutil (isso treina o filtro)\n\n"
    "<b>Modos</b>\n"
    "<code>pricing</code> — so preco, plano, desconto, limite (padrao)\n"
    "<code>product</code> — preco, titulo, estoque de um produto\n"
    "<code>page</code> — qualquer texto, a IA filtra o lixo\n\n"
    "<b>O que eu nao faco</b>: area logada, captcha, login, burlar bloqueio. "
    "Pagina publica ou nada."
)

PRICING = (
    "<b>Planos</b>\n"
    "Starter — R$49/mes ou US$9: 10 URLs, checagem a cada 6h\n"
    "Pro — R$99/mes ou US$19: 40 URLs, checagem a cada 1h, historico 90 dias\n"
    "Loja — R$149/mes: 100 produtos, modo preco, digest diario\n\n"
    "Pix ou cartao. Me responda <b>quero</b> e eu mando a chave/link.\n"
    "Cancelamento: uma mensagem, sem burocracia."
)


def plan_limits(sub):
    return config.PLANS.get(sub["plan"], config.PLANS["trial"])


def trial_days_left(sub) -> int | None:
    if sub["plan"] != "trial" or not sub["trial_start"]:
        return None
    try:
        start = datetime.fromisoformat(sub["trial_start"])
    except ValueError:
        return None
    end = start + timedelta(days=config.TRIAL_DAYS)
    return max(0, (end - datetime.now(timezone.utc)).days)


def cmd_add(conn, chat_id, text):
    match = URL_RE.search(text)
    if not match:
        return "Nao achei URL nenhuma. Cole o link completo, com https://"
    url = match.group(0).rstrip(".,);")

    sub = db.ensure_subscriber(conn, chat_id)
    max_urls, min_interval = plan_limits(sub)
    current = db.list_watches(conn, chat_id)
    if len(current) >= max_urls and url not in [w["url"] for w in current]:
        return (
            f"Voce esta no limite de {max_urls} URLs do plano <b>{sub['plan']}</b>.\n"
            "Use /stop &lt;id&gt; para liberar uma, ou /preco para subir de plano."
        )

    mode = next((m for m in MODES if m in text.lower().split()), "pricing")
    watch = db.add_watch(conn, chat_id, url, mode=mode, interval_min=min_interval)
    left = trial_days_left(sub)
    tail = f"\nTeste gratis: {left} dia(s) restantes." if left is not None else ""
    return (
        f"✅ Monitorando <b>#{watch['id']}</b> {tg.esc(runner.domain(url))} "
        f"no modo <code>{mode}</code>, a cada {watch['interval_min'] // 60}h.\n"
        f"A primeira leitura e a base de comparacao — o primeiro alerta vem na proxima mudanca."
        f"{tail}"
    )


def cmd_list(conn, chat_id):
    rows = db.list_watches(conn, chat_id)
    if not rows:
        return "Nada monitorado ainda. Cole uma URL para comecar."
    lines = ["<b>Suas paginas</b>"]
    for row in rows:
        status = ""
        if row["last_error"]:
            status = f" ⚠️ {tg.esc(row['last_error'][:60])}"
        elif not row["last_hash"]:
            status = " (aguardando 1a leitura)"
        lines.append(
            f"#{row['id']} <code>{row['mode']}</code> {tg.esc(runner.domain(row['url']))}"
            f" · {row['interval_min'] // 60}h{status}"
        )
    lines.append("\n/stop &lt;id&gt; para parar uma delas.")
    return "\n".join(lines)


def cmd_stop(conn, chat_id, args):
    if not args:
        return "Use /stop &lt;id&gt;. Veja os ids em /list."
    try:
        watch_id = int(args[0].lstrip("#"))
    except ValueError:
        return "Id invalido. Use /stop 3, por exemplo."
    if db.stop_watch(conn, chat_id, watch_id):
        return f"Parei o #{watch_id}. Sem drama, sem formulario."
    return f"Nao achei o #{watch_id} na sua lista."


def cmd_mode(conn, chat_id, args):
    mode = next((a.lower() for a in args if a.lower() in MODES), None)
    if not mode:
        return f"Use /mode {'|'.join(MODES)} [id]"
    watch_id = next((int(a.lstrip("#")) for a in args if a.lstrip("#").isdigit()), None)
    count = db.set_mode(conn, chat_id, mode, watch_id)
    if not count:
        return "Nao achei esse watch."
    alvo = f"#{watch_id}" if watch_id else f"{count} pagina(s)"
    return f"Modo de {alvo} agora e <code>{mode}</code>."


def cmd_now(conn, chat_id):
    tg.send(chat_id, "Checando agora. Aviso se algo mudou.")
    tally = runner.run_once(force=True, chat_id=chat_id, verbose=False)
    if tally.get("change"):
        return None  # o alerta em si ja foi enviado
    if tally.get("error"):
        return "Algumas paginas falharam. Veja /list."
    return "Nada mudou. Isso tambem e informacao."


def cmd_junk(conn, chat_id, change_id):
    row = conn.execute(
        "SELECT c.id FROM changes c JOIN watches w ON w.id = c.watch_id"
        " WHERE c.id = ? AND w.chat_id = ?",
        (change_id, str(chat_id)),
    ).fetchone()
    if not row:
        return "Nao achei esse alerta."
    db.set_feedback(conn, change_id, "lixo")
    tg.send_admin(f"👎 chat {chat_id} marcou o alerta {change_id} como lixo.")
    return "Anotado. Alertas desse tipo passam a valer menos."


def cmd_texto(conn, chat_id, change_id):
    """O trecho bruto que gerou o alerta. Para quando o resumo nao convence."""
    row = conn.execute(
        "SELECT c.diff, c.ts, c.summary, w.url, w.label FROM changes c"
        " JOIN watches w ON w.id = c.watch_id WHERE c.id = ? AND w.chat_id = ?",
        (change_id, str(chat_id)),
    ).fetchone()
    if not row:
        return "Nao achei esse alerta."
    linhas = [
        l for l in (row["diff"] or "").splitlines()
        if l[:1] in "+- " and not l.startswith(("+++", "---"))
    ]
    corpo = "\n".join(linhas)[:2500] or "(vazio)"
    return (
        f"<b>{tg.esc(row['label'] or row['url'])}</b> · {row['ts'][:16]}\n"
        f"{tg.esc(row['summary'] or '')}\n\n"
        f"<pre>{tg.esc(corpo)}</pre>\n"
        f"- = como era · + = como esta"
    )


def cmd_stats(conn):
    total, junk, rate = db.noise_rate(conn)
    subs = db.subscribers(conn)
    paying = [s for s in subs if s["plan"] != "trial"]
    watches = db.list_watches(conn)
    return (
        f"<b>Vigia</b>\n"
        f"assinantes: {len(subs)} ({len(paying)} pagando)\n"
        f"urls ativas: {len(watches)}\n"
        f"alertas enviados: {total}\n"
        f"marcados como lixo: {junk} ({rate:.0%}) — meta &lt; 30%"
    )


def handle(conn, chat_id, handle_name, text) -> str | None:
    text = (text or "").strip()
    parts = text.split()
    cmd = parts[0].lower().split("@")[0] if parts else ""
    args = parts[1:]
    is_admin = config.ADMIN_CHAT_ID and str(chat_id) == config.ADMIN_CHAT_ID

    db.ensure_subscriber(conn, chat_id, handle_name)

    if cmd in ("/start", "/ajuda", "/help"):
        return WELCOME if cmd == "/start" else HELP
    if cmd in ("/preco", "/precos", "/pricing", "/planos"):
        return PRICING
    if cmd in ("/watch", "/add", "/monitorar"):
        return cmd_add(conn, chat_id, " ".join(args))
    if cmd in ("/list", "/lista"):
        return cmd_list(conn, chat_id)
    if cmd in ("/stop", "/parar"):
        return cmd_stop(conn, chat_id, args)
    if cmd in ("/mode", "/modo"):
        return cmd_mode(conn, chat_id, args)
    if cmd in ("/agora", "/now", "/check"):
        return cmd_now(conn, chat_id)
    if cmd.startswith("/texto"):
        digits = re.sub(r"\D", "", cmd) or (args[0] if args else "")
        if str(digits).isdigit():
            return cmd_texto(conn, chat_id, int(digits))
        return "Use /texto_&lt;numero do alerta&gt;."
    if cmd.startswith("/lixo"):
        digits = re.sub(r"\D", "", cmd) or (args[0] if args else "")
        if str(digits).isdigit():
            return cmd_junk(conn, chat_id, int(digits))
        return "Use /lixo_&lt;numero do alerta&gt;."
    if cmd == "/stats" and is_admin:
        return cmd_stats(conn)
    if cmd == "/pagou" and is_admin:
        if len(args) < 2 or args[1] not in config.PLANS:
            return f"/pagou <chat_id> <{'|'.join(config.PLANS)}>"
        db.set_plan(conn, args[0], args[1])
        tg.send(args[0], "Pagamento confirmado. Plano ativo, monitoramento segue. Obrigado.")
        return f"chat {args[0]} -> {args[1]}"

    if URL_RE.search(text):
        return cmd_add(conn, chat_id, text)
    if text.lower() in ("quero", "quero sim", "i want", "yes"):
        tg.send_admin(f"💰 chat {chat_id} (@{handle_name}) disse QUERO. Manda o Pix.")
        return "Perfeito. Ja avisei — voce recebe a chave Pix ou o link de cartao em minutos."
    return "Nao entendi. Cole uma URL ou use /ajuda."


def poll():
    conn = db.connect()
    offset = int(db.meta_get(conn, "tg_offset", 0) or 0)
    me = tg.call("getMe")
    print(f"bot @{me['username']} ouvindo (offset {offset}). Ctrl+C para sair.")

    while True:
        try:
            updates = tg.get_updates(offset=offset or None)
        except Exception as exc:  # noqa: BLE001 - rede cai, o bot nao
            print(f"[poll] {type(exc).__name__}: {exc}")
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            db.meta_set(conn, "tg_offset", offset)
            message = update.get("message") or {}
            chat = message.get("chat") or {}
            if not chat.get("id"):
                continue
            sender = message.get("from") or {}
            handle_name = sender.get("username") or sender.get("first_name")
            try:
                reply = handle(conn, chat["id"], handle_name, message.get("text", ""))
                if reply:
                    tg.send(chat["id"], reply)
            except Exception:  # noqa: BLE001 - um comando ruim nao mata o bot
                traceback.print_exc()
                tg.send(chat["id"], "Deu erro do meu lado. Ja fui avisado.")
                tg.send_admin(f"❌ erro no chat {chat['id']}:\n<pre>{tg.esc(traceback.format_exc()[-800:])}</pre>")
