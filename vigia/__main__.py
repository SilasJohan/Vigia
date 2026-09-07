"""CLI do Vigia.

  python -m vigia doctor              # o ambiente esta de pe?
  python -m vigia demo                # pipeline completo com HTML local (teste do dia 2)
  python -m vigia add URL [--chat ID] [--mode pricing] [--label Nome] [--css ".pricing"]
  python -m vigia list
  python -m vigia check [--force] [--quiet-telegram]
  python -m vigia bot                 # long polling dos comandos
  python -m vigia brief DOMINIO       # texto pronto para a DM de aquisicao
  python -m vigia trials              # quem vence o teste gratis
  python -m vigia stats
  python -m vigia whoami              # descobre seu chat_id
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import ai, bot, config, db, differ, extract, runner, tg

FIXTURES = Path(__file__).resolve().parent.parent / "alvos" / "fixtures"


def cmd_doctor(_):
    print(f"db            {config.DB_PATH}")
    print(f"user-agent    {config.USER_AGENT}")
    print(f"intervalo min {config.MIN_INTERVAL_MIN} min · delay {config.REQUEST_DELAY_S}s")

    ok = True
    if config.TELEGRAM_TOKEN:
        try:
            me = tg.call("getMe")
            print(f"telegram      OK  @{me['username']}")
        except Exception as exc:  # noqa: BLE001
            print(f"telegram      FALHOU  {exc}")
            ok = False
    else:
        print("telegram      SEM TOKEN  -> crie o bot no @BotFather e preencha .env")
        ok = False
    print(f"admin_chat_id {config.ADMIN_CHAT_ID or 'vazio (rode: python -m vigia whoami)'}")

    engines = [name for name, _ in ai.providers()]
    print(f"ia            ordem: {engines or ['(nenhuma)']} -> fallback regex")
    probe = ai.classify(
        "https://exemplo.com/pricing",
        "pricing",
        "-Pro US$49/mo\n+Pro US$39/mo",
    )
    print(f"              teste: engine={probe['engine']} important={probe['important']}"
          f" categoria={probe['category']}")
    print(f"              resumo: {probe['summary']}")

    try:
        import playwright  # noqa: F401
        print("playwright    instalado")
    except ImportError:
        print("playwright    ausente (ok: so faz falta em pagina que exige JS)")

    conn = db.connect()
    print(f"watches       {len(db.list_watches(conn))} ativos")
    conn.close()
    return 0 if ok else 1


def _write_fixtures():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    base = """<!doctype html><html><head><title>Concorrente - Precos</title></head><body>
<div class="cookie">Usamos cookies. Aceitar todos.</div>
<h1>Planos simples e transparentes</h1>
<div class="plan"><h2>Free</h2><p>R$ 0</p><p>Ate 3 projetos</p></div>
<div class="plan"><h2>Pro</h2><p>R$ 99/mes</p><p>Projetos ilimitados</p><p>Suporte por e-mail</p></div>
<div class="plan"><h2>Business</h2><p>R$ 399/mes</p><p>SSO e auditoria</p></div>
<footer>Atualizado em 01/09/2026 as 10:14 - 1834 visitas</footer></body></html>"""
    depois = """<!doctype html><html><head><title>Concorrente - Precos</title></head><body>
<div class="cookie">Usamos cookies. Aceitar todos os cookies e similares.</div>
<h1>Planos simples e transparentes</h1>
<div class="plan"><h2>Free</h2><p>R$ 0</p><p>Ate 1 projeto</p></div>
<div class="plan"><h2>Pro</h2><p>R$ 79/mes</p><p>Projetos ilimitados</p><p>Suporte por e-mail</p></div>
<div class="plan"><h2>Business</h2><p>R$ 399/mes</p><p>SSO e auditoria</p></div>
<footer>Atualizado em 07/09/2026 as 18:02 - 2291 visitas</footer></body></html>"""
    (FIXTURES / "antes.html").write_text(base, encoding="utf-8")
    (FIXTURES / "depois.html").write_text(depois, encoding="utf-8")
    return FIXTURES / "antes.html", FIXTURES / "depois.html"


def cmd_demo(args):
    """Criterio de pronto do dia 2: mudanca provocada por voce chega no Telegram."""
    antes_path, depois_path = _write_fixtures()
    antes = extract.prepare(antes_path.read_text(encoding="utf-8"), "pricing")
    depois = extract.prepare(depois_path.read_text(encoding="utf-8"), "pricing")

    diff = differ.build_diff(antes, depois)
    print("--- diff (ja sem data/hora/contador) ---")
    print(diff or "(vazio)")
    print(f"--- {differ.changed_chars(diff)} chars mudados · "
          f"significativo={differ.is_significant(diff)} ---")

    result = ai.classify("file://demo/pricing", "pricing", diff)
    print(f"engine={result['engine']} important={result['important']} "
          f"categoria={result['category']}")
    print(f"resumo: {result['summary']}")

    chat = args.chat or config.ADMIN_CHAT_ID
    if not chat:
        print("\n(sem ADMIN_CHAT_ID: nada enviado. rode 'python -m vigia whoami')")
        return 0

    fake = {
        "id": 0, "url": "https://concorrente.exemplo/pricing", "chat_id": chat,
        "label": "Concorrente (demo)", "mode": "pricing",
    }
    tg.send(chat, runner.alert_text(fake, result, diff).replace("{cid}", "0"))
    print(f"\nalerta enviado para o chat {chat}. Confira no Telegram.")
    return 0


def cmd_add(args):
    conn = db.connect()
    chat = args.chat or config.ADMIN_CHAT_ID
    if not chat:
        print("Informe --chat ID (ou preencha ADMIN_CHAT_ID no .env)")
        return 1
    watch = db.add_watch(
        conn, chat, args.url, mode=args.mode, css=args.css,
        label=args.label, interval_min=args.interval,
    )
    print(f"#{watch['id']} {watch['url']} modo={watch['mode']} "
          f"intervalo={watch['interval_min']}min")
    conn.close()
    return 0


def cmd_carregar(args):
    """Carrega em lote as URLs de alvos/monitorar.csv."""
    import csv

    chat = args.chat or config.ADMIN_CHAT_ID
    if not chat:
        print("Informe --chat ID (ou preencha ADMIN_CHAT_ID no .env)")
        return 1

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"nao achei {caminho}")
        return 1

    # Linhas comecando com # sao comentario, nao dados.
    limpas = [
        linha for linha in caminho.read_text(encoding="utf-8").splitlines()
        if linha.strip() and not linha.lstrip().startswith("#")
    ]

    conn = db.connect()
    adicionados = 0
    for row in csv.DictReader(limpas):
        url = (row.get("url") or "").strip()
        if not url.startswith("http"):
            continue
        if args.cluster and row.get("cluster") != args.cluster:
            continue
        if (row.get("status_tecnico") or "ok").strip() != "ok":
            print(f"  pulei (nao monitoravel): {url}")
            continue
        watch = db.add_watch(
            conn, chat, url,
            mode=(row.get("modo") or "pricing").strip(),
            label=(row.get("empresa") or "").strip() or None,
        )
        adicionados += 1
        print(f"  #{watch['id']:>3} {watch['label'] or url}")

    total = len(db.list_watches(conn, chat))
    conn.close()
    print(f"\n{adicionados} carregada(s). {total} ativa(s) no chat {chat}.")
    print("Agora rode: python -m vigia check --force   (a 1a passada so grava a base)")
    return 0


def cmd_rebase(args):
    """Descarta a base guardada e forca uma releitura limpa.

    Use quando o extrator mudar de formato, quando trocar de modo ou de --css.
    Sem isso, a proxima checagem compara textos de formatos diferentes e reporta
    a pagina inteira como alterada.
    """
    conn = db.connect()
    alvos = db.list_watches(conn, only_active=False)
    if args.label:
        alvos = [w for w in alvos if (w["label"] or "").lower() == args.label.lower()]
    if not alvos:
        print("nenhum watch corresponde")
        return 1
    for w in alvos:
        conn.execute(
            "UPDATE watches SET last_hash = NULL, last_text = NULL WHERE id = ?", (w["id"],)
        )
    conn.commit()
    conn.close()
    print(f"{len(alvos)} base(s) descartada(s). Rode: python -m vigia check --force")
    print("(a proxima passada grava a base nova e nao alerta nada)")
    return 0


def cmd_list(_):
    conn = db.connect()
    rows = db.list_watches(conn, only_active=False)
    if not rows:
        print("(vazio)")
    for row in rows:
        state = "off" if not row["active"] else ("erro" if row["last_error"] else "ok")
        print(f"#{row['id']:>3} [{state:^4}] {row['mode']:<8} chat={row['chat_id']:<12} "
              f"{row['url']}")
        if row["last_error"]:
            print(f"          {row['last_error'][:100]}")
    conn.close()
    return 0


def cmd_check(args):
    if not args.loop:
        runner.run_once(force=args.force, notify=not args.quiet_telegram)
        return 0

    import time
    print(f"loop a cada {args.loop} min (Ctrl+C para sair). "
          f"Cada URL respeita o proprio intervalo.")
    while True:
        try:
            runner.run_once(force=False, notify=not args.quiet_telegram)
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # noqa: BLE001 - o loop nao pode morrer
            print(f"[loop] {type(exc).__name__}: {exc}")
            tg.send_admin(f"⚠️ ciclo falhou: {tg.esc(str(exc))[:300]}")
        time.sleep(args.loop * 60)


def cmd_bot(_):
    bot.poll()
    return 0


def cmd_brief(args):
    """Monta o texto da DM com um fato observado. Isso e a aquisicao."""
    conn = db.connect()
    rows = [
        row for row in db.recent_changes(conn, limit=200)
        if args.domain.lower() in row["url"].lower()
    ]
    watches = [w for w in db.list_watches(conn, only_active=False)
               if args.domain.lower() in w["url"].lower()]
    conn.close()

    if not watches:
        print(f"Nao ha watch para '{args.domain}'. Adicione com: python -m vigia add URL")
        return 1

    days = args.days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for row in rows:
        try:
            if datetime.fromisoformat(row["ts"]) >= cutoff:
                recent.append(row)
        except ValueError:
            continue

    important = [r for r in recent if r["important"]]
    print("=" * 60)
    if important:
        facts = "\n".join(f"- {r['summary']}" for r in important[:4])
        print(f"""PT
---
Oi, tudo bem? Nos ultimos {days} dias eu acompanhei a pagina de precos de {args.domain}.
{facts}

Eu monitoro paginas publicas de concorrentes e mando so o que importa (preco, plano, limite) no Telegram. Quer receber isso de graca pelo resto da semana? Depois sao R$49/mes, cancela com uma mensagem.

EN
---
Hey - I've been watching {args.domain}'s pricing page for the last {days} days.
{facts}

I watch competitor pricing pages and send a Telegram digest of only the changes that matter (price, plan, limits). 10 URLs. Want the rest of the week free? Then $9/mo, cancel in one message.""")
    else:
        print(f"""PT
---
Oi! Acompanhei a pagina de precos de {args.domain} nos ultimos {days} dias: nada mudou.
Isso tambem e sinal - eles nao estao mexendo em preco agora.

Eu monitoro paginas publicas de concorrentes e aviso no Telegram no dia em que mudar (preco, plano, limite do free). Quer que eu inclua os seus concorrentes de graca pelo resto da semana?

EN
---
Watched {args.domain} for {days} days - no pricing change. That's a signal too.
I watch competitor pricing pages and ping you on Telegram the day something moves. Want the rest of the week free?""")
    print("=" * 60)
    print(f"(base: {len(recent)} mudanca(s) registrada(s), {len(important)} relevante(s))")
    return 0


def cmd_trials(_):
    conn = db.connect()
    print(f"{'chat_id':<14}{'handle':<20}{'plano':<10}{'dias restantes':<16}urls")
    for sub in db.subscribers(conn):
        left = bot.trial_days_left(sub)
        urls = len(db.list_watches(conn, sub["chat_id"]))
        marker = ""
        if left == 0:
            marker = "  <- COBRE HOJE"
        print(f"{sub['chat_id']:<14}{str(sub['handle'] or '-'):<20}{sub['plan']:<10}"
              f"{str(left if left is not None else '-'):<16}{urls}{marker}")
    conn.close()
    return 0


def cmd_dossie(args):
    """Tudo o que sabemos de UMA pagina, pronto para citar.

    Isto substitui o caderninho: o banco ja guarda data, secao, antes/agora e
    quantas leituras foram feitas. Anotar a mao seria refazer o que ja existe.
    """
    conn = db.connect()
    termo = args.empresa.lower()
    alvos = [
        w for w in db.list_watches(conn, only_active=False)
        if termo in (w["label"] or "").lower() or termo in w["url"].lower()
    ]
    if not alvos:
        print(f"nada com '{args.empresa}'. Veja os nomes em: python -m vigia list")
        return 1

    for w in alvos:
        desde = w["observando_desde"] or w["created_at"]
        dias = 0.0
        try:
            dias = (datetime.now(timezone.utc)
                    - datetime.fromisoformat(desde)).total_seconds() / 86400
        except (ValueError, TypeError):
            pass
        mudancas = [c for c in db.recent_changes(conn, limit=200)
                    if c["watch_id"] == w["id"]]
        relevantes = [c for c in mudancas if c["important"]]

        print("=" * 70)
        print(f"{w['label'] or runner.domain(w['url'])}  ·  {w['url']}")
        print("=" * 70)
        print(f"observando desde .... {(desde or '?')[:10]}  ({dias:.1f} dias)")
        print(f"leituras feitas ..... {w['check_count'] or 0}")
        print(f"modo ................ {w['mode']}"
              + (f"  css={w['css']}" if w["css"] else ""))
        print(f"mudancas relevantes . {len(relevantes)}")
        if w["last_error"]:
            print(f"ULTIMO ERRO ......... {w['last_error'][:80]}")

        if not relevantes:
            print("\nNenhuma mudanca relevante ainda.")
            print("Isso tambem e um fato citavel - veja a frase no final.")
        for c in relevantes:
            print(f"\n  [{c['ts'][:16]}] {c['category']}")
            print(f"  {c['summary']}")
            for l in (c["diff"] or "").splitlines():
                if l[:1] in "+-" and not l.startswith(("+++", "---")):
                    marca = "era :" if l.startswith("-") else "virou:"
                    print(f"      {marca} {l[1:].strip()[:64]}")
            if c["feedback"] == "lixo":
                print("      (voce marcou como lixo)")

        print("\n" + "-" * 70)
        print("FRASE PRONTA PARA A MENSAGEM (confira antes de mandar)")
        print("-" * 70)
        nome = w["label"] or runner.domain(w["url"])
        if relevantes:
            ultima = relevantes[0]
            print(f"PT: Acompanho a pagina de precos da {nome} desde "
                  f"{(desde or '')[:10]} ({w['check_count'] or 0} leituras). "
                  f"Em {ultima['ts'][:10]}: {ultima['summary']}")
            print(f"EN: I've been checking {nome}'s pricing page since "
                  f"{(desde or '')[:10]} ({w['check_count'] or 0} checks). "
                  f"On {ultima['ts'][:10]}: {ultima['summary']}")
        else:
            print(f"PT: Acompanho a pagina de precos da {nome} ha {dias:.0f} dias "
                  f"({w['check_count'] or 0} leituras): nenhuma mudanca. "
                  f"Isso tambem e sinal - nao estao mexendo em preco agora.")
            print(f"EN: I've checked {nome}'s pricing page {w['check_count'] or 0} "
                  f"times over {dias:.0f} days: no changes. That's a signal too.")
        print()
    conn.close()
    return 0


def cmd_mercado(args):
    """O mercado se move? Mede a premissa do negocio antes de vender.

    Se 29 paginas de preco nao mudam em 3 semanas, o produto e ilusao e nenhuma
    habilidade de venda conserta. Se mudam, existe algo para vender. Este comando
    e o unico juiz.
    """
    import csv

    conn = db.connect()
    rows = db.changes_por_dia(conn, dias=args.dias)

    # cluster vem do CSV de alvos, nao do banco
    cluster_de = {}
    alvos = Path("alvos/monitorar.csv")
    if alvos.exists():
        limpas = [
            l for l in alvos.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")
        ]
        for r in csv.DictReader(limpas):
            cluster_de[(r.get("url") or "").strip()] = (r.get("cluster") or "?").strip()

    # janela real de observacao: desde o watch mais antigo
    inicio = min((r["created_at"] for r in rows if r["created_at"]), default=None)
    dias_obs = 0.0
    if inicio:
        try:
            dias_obs = (
                datetime.now(timezone.utc) - datetime.fromisoformat(inicio)
            ).total_seconds() / 86400
        except ValueError:
            pass

    total_mud = sum(r["mudancas"] for r in rows)
    total_preco = sum(r["preco"] or 0 for r in rows)
    com_mudanca = [r for r in rows if r["mudancas"]]

    print("=" * 68)
    print(f"O MERCADO SE MOVE?  ({len(rows)} paginas, "
          f"{dias_obs:.1f} dias de observacao real)")
    print("=" * 68)

    if dias_obs < 1:
        print("\nMenos de 1 dia de dados. Volte aqui em 3 dias - antes disso")
        print("qualquer conclusao e chute.\n")

    print(f"\nmudancas relevantes .... {total_mud}")
    print(f"  delas, de preco ...... {total_preco}")
    print(f"paginas que mudaram .... {len(com_mudanca)} de {len(rows)}")
    if dias_obs >= 1 and rows:
        por_pagina_mes = (total_mud / len(rows)) / max(dias_obs, 1) * 30
        print(f"ritmo .................. {por_pagina_mes:.2f} mudancas por pagina por mes")
        if por_pagina_mes > 0:
            print(f"                         (~1 a cada {30 / por_pagina_mes:.0f} dias por pagina)")

    if com_mudanca:
        print("\npaginas que se mexeram:")
        for r in com_mudanca:
            cl = cluster_de.get(r["url"], "?")
            print(f"  {r['mudancas']:>2}x  [{cl:<13}] {r['label'] or r['url']:<20}"
                  f" preco={r['preco'] or 0} plano={r['plano'] or 0}"
                  f" lixo={r['lixo'] or 0}  ultima: {(r['ultima'] or '')[:10]}")

    paradas = [r for r in rows if not r["mudancas"]]
    if paradas:
        print(f"\nparadas no periodo ({len(paradas)}): "
              f"{', '.join((r['label'] or '?') for r in paradas[:12])}"
              f"{' ...' if len(paradas) > 12 else ''}")

    print("\n" + "-" * 68)
    print("COMO LER ISTO")
    print("-" * 68)
    if dias_obs < 7:
        print("Dados insuficientes para julgar. Meta: 21 dias.")
    elif total_mud == 0:
        print("Zero mudancas. A premissa do negocio nao se sustenta nestes clusters:")
        print("ninguem paga para ser avisado de algo que nao acontece. Troque de")
        print("cluster (e-commerce e varejo mexem mais que SaaS) ou mate a ideia.")
    elif len(com_mudanca) <= 2:
        print("Poucas paginas se movem. Ou os clusters estao errados, ou o valor")
        print("esta em 2-3 paginas especificas - venda para quem vigia ESSAS.")
    else:
        print(f"{len(com_mudanca)} paginas se moveram: existe o que vender. O argumento")
        print("da DM nao e mais hipotese, e este numero. Use-o literalmente:")
        print(f'  "acompanhei {len(rows)} paginas de preco por {dias_obs:.0f} dias;')
        print(f'   {total_mud} mudaram, {total_preco} eram preco."')
    print("\nMeta de qualidade: lixo < 30% (veja 'python -m vigia stats').")
    conn.close()
    return 0


def cmd_stats(_):
    conn = db.connect()
    total, junk, rate = db.noise_rate(conn)
    subs = db.subscribers(conn)
    print(f"assinantes ........ {len(subs)}")
    print(f"pagando ........... {len([s for s in subs if s['plan'] != 'trial'])}")
    print(f"urls ativas ....... {len(db.list_watches(conn))}")
    print(f"alertas enviados .. {total}")
    print(f"marcados como lixo. {junk} ({rate:.0%})   meta < 30%")
    print("\nultimas mudancas:")
    for row in db.recent_changes(conn, limit=10):
        flag = "!" if row["important"] else " "
        print(f" {flag} {row['ts'][:16]} {row['category'] or '-':<8} "
              f"{runner.domain(row['url']):<28} {(row['summary'] or '')[:70]}")
    conn.close()
    return 0


def cmd_whoami(args):
    if not config.TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN esta vazio.\n")
        if (config.ROOT / ".env").exists():
            print(f"O arquivo {config.ROOT / '.env'} existe, mas nao tem a linha")
            print("  TELEGRAM_TOKEN=123456:ABC...")
        else:
            print(f"Nao existe {config.ROOT / '.env'}.")
            print("Atencao: preencher o .env.example NAO funciona - ele e so o molde.")
            print("  Windows:  copy .env.example .env")
        return 1

    try:
        me = tg.call("getMe")
    except tg.TelegramError as exc:
        print(f"O Telegram recusou o token: {exc}")
        print("Confira se copiou o token inteiro (formato 123456789:AA...), sem espaco.")
        return 1
    print(f"bot @{me['username']} respondendo.\n")

    # Nao exige que a mensagem seja anterior ao comando: fica esperando.
    # Update ja confirmado por um 'vigia bot' anterior o Telegram nao reentrega,
    # entao pedir "mande antes" era uma armadilha.
    import time

    limite = time.monotonic() + args.wait
    print(f"Mande /start para @{me['username']} agora. Esperando ate {args.wait}s...\n")

    seen = {}
    while not seen and time.monotonic() < limite:
        try:
            updates = tg.get_updates(poll=20)
        except tg.TelegramError as exc:
            print(f"getUpdates falhou: {exc}")
            return 1
        for update in updates:
            chat = (update.get("message") or {}).get("chat") or {}
            if chat.get("id"):
                seen[chat["id"]] = chat.get("username") or chat.get("first_name") or "-"

    if not seen:
        print("Nada chegou. Confira se abriu a conversa certa:")
        print(f"  https://t.me/{me['username']}")
        print("Se 'python -m vigia bot' estiver rodando em outra janela, pare ele:")
        print("as duas coisas competem pela mesma fila de mensagens.")
        return 1

    for chat_id, name in seen.items():
        print(f"chat_id={chat_id}  ({name})")
    print(f"\nCopie para o {config.ROOT / '.env'}:  ADMIN_CHAT_ID=<o seu>")
    return 0


def main(argv=None):
    # O console do Windows abre em cp1252 e engasga com acento/emoji.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(prog="vigia", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="checa ambiente, telegram e IA").set_defaults(fn=cmd_doctor)

    demo = sub.add_parser("demo", help="pipeline completo com HTML local")
    demo.add_argument("--chat", help="chat_id de destino (default: ADMIN_CHAT_ID)")
    demo.set_defaults(fn=cmd_demo)

    add = sub.add_parser("add", help="adiciona uma URL")
    add.add_argument("url")
    add.add_argument("--chat")
    add.add_argument("--mode", default="pricing", choices=bot.MODES)
    add.add_argument("--css", help="seletor CSS para recortar (ex: '.pricing-table')")
    add.add_argument("--label")
    add.add_argument("--interval", type=int, help="minutos entre checagens")
    add.set_defaults(fn=cmd_add)

    carregar = sub.add_parser("carregar", help="carrega URLs de um CSV em lote")
    carregar.add_argument("arquivo", nargs="?", default="alvos/monitorar.csv")
    carregar.add_argument("--chat")
    carregar.add_argument("--cluster", help="carrega so um cluster (ex: uptime)")
    carregar.set_defaults(fn=cmd_carregar)

    rebase = sub.add_parser("rebase", help="descarta a base e forca releitura limpa")
    rebase.add_argument("--label", help="so um watch (ex: Bling)")
    rebase.set_defaults(fn=cmd_rebase)

    sub.add_parser("list", help="lista os watches").set_defaults(fn=cmd_list)

    check = sub.add_parser("check", help="roda um ciclo de checagem")
    check.add_argument("--force", action="store_true", help="ignora o intervalo")
    check.add_argument("--quiet-telegram", action="store_true", help="nao envia alerta")
    check.add_argument("--loop", type=int, metavar="MIN",
                       help="repete para sempre a cada MIN minutos (use no PC ligado)")
    check.set_defaults(fn=cmd_check)

    sub.add_parser("bot", help="long polling dos comandos").set_defaults(fn=cmd_bot)

    brief = sub.add_parser("brief", help="texto da DM de aquisicao")
    brief.add_argument("domain")
    brief.add_argument("--days", type=int, default=3)
    brief.set_defaults(fn=cmd_brief)

    sub.add_parser("trials", help="quem vence o teste gratis").set_defaults(fn=cmd_trials)
    dossie = sub.add_parser("dossie", help="tudo sobre uma pagina, pronto para citar")
    dossie.add_argument("empresa", help="nome ou dominio (ex: Bling, tally)")
    dossie.set_defaults(fn=cmd_dossie)

    mercado = sub.add_parser("mercado", help="o mercado se move? mede a premissa")
    mercado.add_argument("--dias", type=int, default=30)
    mercado.set_defaults(fn=cmd_mercado)

    sub.add_parser("stats", help="metricas do dia 30").set_defaults(fn=cmd_stats)
    whoami = sub.add_parser("whoami", help="descobre seu chat_id")
    whoami.add_argument("--wait", type=int, default=60,
                        help="segundos esperando voce mandar /start (default 60)")
    whoami.set_defaults(fn=cmd_whoami)

    args = parser.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
