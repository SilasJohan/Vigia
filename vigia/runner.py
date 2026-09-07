"""Um ciclo de checagem: fetch -> texto -> diff -> IA -> Telegram."""

import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import ai, config, db, differ, extract, fetch, tg

CATEGORY_LABEL = {
    "price": "PRECO",
    "plan": "PLANO",
    "feature": "FEATURE",
    "copy": "COPY",
    "stock": "ESTOQUE",
    "noise": "RUIDO",
}


def domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "") or url


def collect(url: str, mode: str, css: str | None) -> str:
    """Devolve o texto ja recortado pelo modo. Sobe FetchError se falhar."""
    html = fetch.fetch_http(url)
    text = extract.prepare(html, mode, css)
    if fetch.looks_empty(html, text):
        html = fetch.fetch_browser(url)
        text = extract.prepare(html, mode, css)
    if len(text.strip()) < 40:
        raise fetch.FetchError("texto visivel quase vazio (pagina bloqueada ou so imagem)")
    return text


def _idade(ts) -> str:
    """'2 dias atras' a partir de um timestamp ISO."""
    if not ts:
        return "?"
    try:
        quando = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return "?"
    horas = (datetime.now(timezone.utc) - quando).total_seconds() / 3600
    if horas < 1:
        return "agora"
    if horas < 24:
        return f"{int(horas)}h atras"
    return f"{int(horas / 24)} dia(s) atras"


def _antes_agora(pares) -> str:
    """Descreve cada alteracao com localizacao suficiente para voce conferir.

    Junta o que e um bloco unico (5 linhas removidas de uma vez sao 1 fato, nao
    5), diz a secao e as linhas intactas em volta, e avisa quando o mesmo valor
    continua em outro trecho da pagina.
    """
    grupos: dict = {}
    for p in pares:
        grupos.setdefault(p["grupo"], []).append(p)

    blocos, avisos = [], []
    for itens in grupos.values():
        p0 = itens[0]

        cabecalho = []
        if p0["secao"]:
            cabecalho.append(f'secao "{tg.esc(str(p0["secao"]))}"')
        if p0["pos"] is not None:
            cabecalho.append(f"trecho {p0['pos'] + 1} de {p0['total']}")
        blocos.append("📍 " + " · ".join(cabecalho) if cabecalho else "📍 posicao desconhecida")

        antes_txt = [i["antes"] for i in itens if i["antes"]]
        agora_txt = [i["agora"] for i in itens if i["agora"]]

        if antes_txt and agora_txt and len(itens) == 1:
            blocos.append(f"   antes: {tg.esc(antes_txt[0][:70])}")
            blocos.append(f"   agora: <b>{tg.esc(agora_txt[0][:70])}</b>")
        else:
            for t in antes_txt:
                blocos.append(f"   <s>{tg.esc(t[:70])}</s>")
            if antes_txt and not agora_txt:
                blocos.append(f"   ↳ <i>bloco de {len(antes_txt)} linha(s) saiu da pagina</i>"
                              if len(antes_txt) > 1 else "   ↳ <i>saiu da pagina</i>")
            for t in agora_txt:
                blocos.append(f"   <b>{tg.esc(t[:70])}</b>")
            if agora_txt and not antes_txt:
                blocos.append("   ↳ <i>novo na pagina</i>")

        antes_v, depois_v = p0.get("vizinhos") or (None, None)
        if antes_v or depois_v:
            blocos.append(
                f"   <i>entre \"{tg.esc((antes_v or '(inicio)')[:34])}\" e "
                f"\"{tg.esc((depois_v or '(fim)')[:34])}\"</i>"
            )
        blocos.append("")

        for i in itens:
            r = i.get("resto")
            if not r:
                continue
            valor = f"<code>{tg.esc(r['token'])}</code> " if r.get("token") else ""
            avisos.append(
                f"⚠️ {valor}continua na pagina, no trecho {r['pos'] + 1}: "
                f"\"{tg.esc(r['linha'][:60])}\". Saiu <b>so este trecho</b> — "
                f"nao diga que a oferta acabou sem conferir."
            )

    texto = "\n".join(blocos).strip()
    if avisos:
        texto += "\n\n" + "\n".join(dict.fromkeys(avisos))
    return texto


def alert_text(watch, result, diff, pares=None, historico=None) -> str:
    name = watch["label"] or domain(watch["url"])
    tag = CATEGORY_LABEL.get(result["category"], result["category"].upper())

    if pares:
        corpo = _antes_agora(pares)
    else:  # sem os textos completos, cai no diff cru
        corpo = "<pre>" + tg.esc("\n".join(
            line for line in diff.splitlines()
            if line[:1] in "+-" and not line.startswith(("+++", "---"))
        )[:500]) + "</pre>"

    rodape = ""
    if historico:
        total = historico["total"]
        if total <= 1:
            rodape = "\n\n<i>1a mudanca desde que comecei a olhar esta pagina.</i>"
        else:
            rodape = (
                f"\n\n<i>{total}a mudanca nesta pagina · a anterior foi "
                f"{_idade(historico['anterior'])}.</i>"
            )

    return (
        f"<b>[{tag}] {tg.esc(name)}</b>\n"
        f"{tg.esc(result['summary'])}\n\n"
        f"{corpo}"
        f"{rodape}\n\n"
        f"<a href=\"{tg.esc(watch['url'])}\">abrir pagina</a> · "
        f"/texto_{{cid}} para o trecho bruto · /lixo_{{cid}} se foi inutil"
    )


def check_watch(conn, watch, notify=True, verbose=True, ciclo=None):
    """Processa um watch. Devolve dict com o que aconteceu.

    `ciclo` e um dict de estado compartilhado pela rodada, usado para checar a
    conexao uma vez so em vez de a cada pagina.
    """
    if verbose:
        print(f"[{watch['id']}] {watch['url']} ({watch['mode']})")

    try:
        text = collect(watch["url"], watch["mode"], watch["css"])
    except fetch.NetworkError as exc:
        # Nao chegou resposta. Antes de culpar o site, veja se a rede e sua.
        if ciclo is not None and ciclo.get("offline") is None:
            ciclo["offline"] = not fetch.online()
        offline = ciclo.get("offline") if ciclo is not None else (not fetch.online())

        if offline:
            # Sua internet caiu: nao conta como falha do site, nao avisa ninguem,
            # nao mexe no estado. Na volta, o ciclo normal retoma.
            if verbose:
                print("  SEM INTERNET aqui - pulando sem penalizar o site")
            return {"status": "offline"}

        db.save_error(conn, watch["id"], exc)
        if verbose:
            print(f"  falha de rede so neste site: {exc}")
        return {"status": "error", "error": str(exc)}
    except fetch.FetchError as exc:
        db.save_error(conn, watch["id"], exc)
        fails = watch["fail_count"] + 1
        if verbose:
            print(f"  erro ({fails}x): {exc}")
        # Na 3a falha seguida o cliente precisa saber. Nao contornamos bloqueio.
        if notify and fails == 3:
            tg.send(
                watch["chat_id"],
                f"⚠️ Nao consigo mais ler <b>{tg.esc(domain(watch['url']))}</b>: "
                f"{tg.esc(str(exc))}\nO site pode estar bloqueando. Quer trocar a URL? /list",
            )
        return {"status": "error", "error": str(exc)}

    new_hash = differ.fingerprint(text)

    if not watch["last_hash"]:
        db.save_state(conn, watch["id"], new_hash, text)
        if verbose:
            print(f"  baseline salvo ({len(text)} chars)")
        return {"status": "baseline"}

    if new_hash == watch["last_hash"]:
        db.save_state(conn, watch["id"], new_hash, text)
        if verbose:
            print("  sem mudanca")
        return {"status": "unchanged"}

    diff = differ.build_diff(watch["last_text"] or "", text)

    if not differ.is_significant(diff):
        db.save_state(conn, watch["id"], new_hash, text)
        if verbose:
            print(f"  mudanca abaixo do limite ({differ.changed_chars(diff)} chars) - ignorada")
        return {"status": "noise_filtered"}

    result = ai.classify(watch["url"], watch["mode"], diff)
    change_id = db.record_change(
        conn, watch["id"], diff, result["summary"], result["important"], result["category"]
    )
    db.save_state(conn, watch["id"], new_hash, text)

    if verbose:
        flag = "IMPORTA" if result["important"] else "ignorado"
        print(f"  {flag} [{result['category']}/{result['engine']}] {result['summary'][:120]}")

    if result["important"] and notify:
        try:
            pares = differ.pair_changes(watch["last_text"] or "", text)
            historico = db.watch_history(conn, watch["id"])
            tg.send(
                watch["chat_id"],
                alert_text(watch, result, diff, pares, historico)
                .replace("{cid}", str(change_id)),
            )
            db.mark_notified(conn, change_id)
        except tg.TelegramError as exc:
            print(f"  [tg] falha ao enviar: {exc}")

    return {"status": "change", "important": result["important"], "result": result}


def run_once(force=False, notify=True, chat_id=None, verbose=True):
    conn = db.connect()
    watches = db.due_watches(conn, force=force)
    if chat_id:
        watches = [w for w in watches if w["chat_id"] == str(chat_id)]

    tally = {}
    ciclo = {"offline": None}  # checa a conexao no maximo uma vez por rodada
    if verbose:
        print(f"== ciclo: {len(watches)} watch(es) na fila ==")

    for i, watch in enumerate(watches):
        outcome = check_watch(conn, watch, notify=notify, verbose=verbose, ciclo=ciclo)
        tally[outcome["status"]] = tally.get(outcome["status"], 0) + 1

        # Sem internet, insistir nas 28 restantes e so perder tempo.
        if outcome["status"] == "offline":
            restantes = len(watches) - i - 1
            if restantes:
                tally["offline"] = tally.get("offline", 0) + restantes
                if verbose:
                    print(f"== abortando: sem internet ({restantes} nao checadas). "
                          f"Elas continuam vencidas e entram no proximo ciclo. ==")
            break

        if i < len(watches) - 1:
            time.sleep(config.REQUEST_DELAY_S)  # voce e um visitante, nao um DDoS

    if verbose:
        print(f"== fim: {tally or 'nada a fazer'} ==")
    conn.close()
    return tally
