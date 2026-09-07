"""Testes de resiliencia: queda de luz, de internet, e desligar a maquina.

O caso que importa: se a internet cai por 3 ciclos, o Vigia NAO pode mandar 29
avisos dizendo que 29 sites bloquearam o acesso. Isso queimaria a confianca do
cliente por causa de um Wi-Fi ruim.

Rode: python tests/test_rede.py
"""

import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tempfile  # noqa: E402
import os  # noqa: E402

# Banco proprio, para nao tocar no vigia.db real
os.environ["VIGIA_DB"] = str(Path(tempfile.gettempdir()) / "vigia_test_rede.db")

from vigia import db, fetch, runner  # noqa: E402

# Precisa ser realista: pagina curta faz o looks_empty() achar que e um SPA
# vazio e tentar subir o Playwright.
PAGINA = """<html><body>
<h1>Planos que crescem com voce</h1>
<h2>Free</h2><p>R$ 0</p><p>Ate 3 projetos</p><p>1 usuario</p>
<p>Suporte pela comunidade</p><p>Relatorios basicos</p>
<h2>Pro</h2><p>R$ 99/mes</p><p>Ate 10 projetos</p><p>5 usuarios</p>
<p>Suporte por e-mail em 24h</p><p>Relatorios avancados e exportacao</p>
<p>Integracoes com 400 canais</p><p>Historico de 90 dias</p>
<h2>Business</h2><p>R$ 399/mes</p><p>Projetos ilimitados</p>
<p>25 usuarios</p><p>SSO e auditoria</p><p>Gerente de conta dedicado</p>
<p>SLA de 99,9% e suporte por telefone</p><p>Historico ilimitado</p>
<h2>Perguntas frequentes</h2>
<p>Posso trocar de plano quando quiser? Sim, a qualquer momento.</p>
<p>Tem desconto anual? Sim, dois meses gratis no pagamento anual.</p>
</body></html>"""


def _watch(conn, url="https://exemplo.com/pricing"):
    conn.execute("DELETE FROM changes")
    conn.execute("DELETE FROM watches")
    conn.commit()
    return db.add_watch(conn, "123", url, label="Exemplo")


def _sem_rede(url):
    raise fetch.NetworkError("rede: ConnectError: getaddrinfo failed")


def test_internet_caida_nao_penaliza_o_site():
    conn = db.connect()
    w = _watch(conn)
    with mock.patch.object(fetch, "fetch_http", _sem_rede), \
         mock.patch.object(fetch, "online", lambda timeout=5.0: False):
        r = runner.check_watch(conn, w, notify=False, verbose=False, ciclo={"offline": None})
    assert r["status"] == "offline", r
    fc = conn.execute("SELECT fail_count FROM watches WHERE id=?", (w["id"],)).fetchone()[0]
    assert fc == 0, f"internet caida incrementou fail_count para {fc}"
    conn.close()


def test_internet_caida_nao_manda_alerta():
    """Com 3 falhas, o codigo avisaria o cliente. Offline nao pode chegar la."""
    conn = db.connect()
    w = _watch(conn)
    conn.execute("UPDATE watches SET fail_count = 2 WHERE id = ?", (w["id"],))
    conn.commit()
    w = db.list_watches(conn)[0]

    enviados = []
    with mock.patch.object(fetch, "fetch_http", _sem_rede), \
         mock.patch.object(fetch, "online", lambda timeout=5.0: False), \
         mock.patch.object(runner.tg, "send", lambda *a, **k: enviados.append(a)):
        runner.check_watch(conn, w, notify=True, verbose=False, ciclo={"offline": None})
    assert not enviados, f"mandou alerta com a internet caida: {enviados}"
    conn.close()


def test_site_fora_com_internet_ok_conta_como_falha():
    conn = db.connect()
    w = _watch(conn)
    with mock.patch.object(fetch, "fetch_http", _sem_rede), \
         mock.patch.object(fetch, "online", lambda timeout=5.0: True):
        r = runner.check_watch(conn, w, notify=False, verbose=False, ciclo={"offline": None})
    assert r["status"] == "error", r
    fc = conn.execute("SELECT fail_count FROM watches WHERE id=?", (w["id"],)).fetchone()[0]
    assert fc == 1, f"falha do site nao foi contada (fail_count={fc})"
    conn.close()


def test_conexao_e_checada_uma_vez_por_ciclo():
    """Nao pode sondar a rede 29 vezes por rodada."""
    conn = db.connect()
    _watch(conn)
    sondas = []

    def contar(timeout=5.0):
        sondas.append(1)
        return False

    with mock.patch.object(fetch, "fetch_http", _sem_rede), \
         mock.patch.object(fetch, "online", contar):
        ciclo = {"offline": None}
        w = db.list_watches(conn)[0]
        for _ in range(5):
            runner.check_watch(conn, w, notify=False, verbose=False, ciclo=ciclo)
    assert len(sondas) == 1, f"sondou a rede {len(sondas)} vezes num ciclo"
    conn.close()


def test_base_sobrevive_a_desligar_no_meio():
    """Estado e commitado por pagina: desligar depois da 1a nao perde a 1a."""
    conn = db.connect()
    w = _watch(conn)
    with mock.patch.object(fetch, "fetch_http", lambda url: PAGINA):
        runner.check_watch(conn, w, notify=False, verbose=False, ciclo={"offline": None})
    conn.close()

    # "reabre o programa depois do desligamento"
    conn = db.connect()
    w2 = db.list_watches(conn)[0]
    assert w2["last_hash"], "base nao sobreviveu ao restart"
    assert w2["check_count"] >= 1
    conn.close()


def main():
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print(f"  ok    {teste.__name__}")
        except AssertionError as exc:
            falhas += 1
            print(f"  FALHA {teste.__name__}: {exc}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
