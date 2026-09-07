"""Testes do filtro de ruido. Rode: python tests/test_filtro.py

Estes testes existem por um motivo comercial: o critério de abandono do projeto
é "mais de 40% dos alertas são lixo". Cada caso aqui é um tipo de lixo que já
mataria a confiança do cliente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vigia import ai, differ, extract  # noqa: E402

PAGINA = """<html><body>
<div>Usamos cookies para melhorar sua experiencia. Aceitar todos.</div>
<nav>Home Produto Blog Contato</nav>
<h1>Planos</h1>
<p>Pro</p><p>R$ 99/mes</p><p>Ate 10 projetos</p>
<script>var x = Date.now();</script>
<footer>Atualizado 01/09/2026 as 10:14 - 1834 visitas - 2026 Empresa Ltda</footer>
</body></html>"""


def muda(html, de, para):
    return html.replace(de, para)


def diff_de(html_antes, html_depois, mode="pricing"):
    antes = extract.prepare(html_antes, mode)
    depois = extract.prepare(html_depois, mode)
    return differ.build_diff(antes, depois)


def test_descarta_script_e_nav():
    texto = extract.visible_text(PAGINA)
    assert "Date.now" not in texto, "script vazou para o texto"
    assert "Blog" not in texto, "nav vazou para o texto"


def test_banner_de_cookie_nao_gera_alerta():
    depois = muda(PAGINA, "Aceitar todos.", "Aceitar todos os cookies e similares.")
    assert not differ.is_significant(diff_de(PAGINA, depois)), "cookie gerou alerta"


def test_data_hora_e_contador_nao_geram_alerta():
    depois = muda(
        muda(PAGINA, "01/09/2026 as 10:14", "07/09/2026 as 18:02"),
        "1834 visitas", "2291 visitas",
    )
    assert not differ.is_significant(diff_de(PAGINA, depois)), "rodape gerou alerta"


def test_mudanca_de_preco_gera_alerta_de_preco():
    depois = muda(PAGINA, "R$ 99/mes", "R$ 79/mes")
    diff = diff_de(PAGINA, depois)
    assert differ.is_significant(diff, min_chars=1), "queda de preco foi filtrada"
    veredito = ai.heuristic(diff)
    assert veredito["important"] is True
    assert veredito["category"] == "price"


def test_corte_do_limite_do_free_gera_alerta():
    depois = muda(PAGINA, "Ate 10 projetos", "Ate 3 projetos")
    diff = diff_de(PAGINA, depois)
    veredito = ai.heuristic(diff)
    assert veredito["important"] is True, "corte de limite passou como irrelevante"


def test_pagina_identica_nao_muda_o_hash():
    a = extract.prepare(PAGINA, "pricing")
    b = extract.prepare(PAGINA, "pricing")
    assert differ.fingerprint(a) == differ.fingerprint(b)


def test_hash_ignora_o_volatil():
    """Duas leituras com data/hora diferentes têm o mesmo fingerprint."""
    depois = muda(PAGINA, "01/09/2026 as 10:14", "07/09/2026 as 18:02")
    a = extract.prepare(PAGINA, "pricing")
    b = extract.prepare(depois, "pricing")
    assert differ.fingerprint(a) == differ.fingerprint(b), "hash sensivel a data"


def test_recorte_pricing_descarta_texto_solto():
    html = PAGINA.replace(
        "<h1>Planos</h1>",
        "<h1>Planos</h1><article>Nosso time foi ao evento em Sao Paulo e "
        "conversou com dezenas de clientes sobre cultura de produto.</article>",
    )
    recorte = extract.prepare(html, "pricing")
    assert "R$ 99/mes" in recorte
    assert "cultura de produto" not in recorte, "texto irrelevante entrou no recorte"


def test_linha_de_ruido_nova_nao_conta_como_mudanca():
    """Pagina que passa a exibir 'atualizado em ...' nao pode gerar alerta."""
    antes = extract.prepare(PAGINA, "pricing")
    depois = antes + "\nAtualizado em 07/09/2026 as 22:41\n1834 visitas hoje"
    diff = differ.build_diff(antes, depois)
    assert differ.changed_chars(diff) == 0, f"ruido virou mudanca: {diff!r}"
    assert not differ.is_significant(diff)


def test_ruido_nao_aparece_no_alerta_de_mudanca_real():
    """Alerta legitimo nao deve exibir data/contador junto do preco."""
    antes = extract.prepare(PAGINA, "pricing")
    depois = antes.replace("R$ 99/mes", "R$ 79/mes") + "\nAtualizado em 07/09/2026 as 22:41"
    diff = differ.build_diff(antes, depois)
    assert "99" in diff and "79" in diff, "perdeu a mudanca de preco"
    assert "Atualizado" not in diff, f"ruido vazou para o alerta: {diff!r}"


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
