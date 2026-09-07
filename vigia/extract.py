"""HTML -> texto visivel, e o recorte do modo pricing.

O recorte e o produto. O crawler qualquer um copia.
"""

import re

from bs4 import BeautifulSoup

DROP_TAGS = (
    "script", "style", "noscript", "svg", "iframe", "canvas",
    "template", "nav", "footer", "form", "head",
)

# Blocos que quase sempre sao ruido em pagina de preco.
JUNK_LINE = re.compile(
    r"cookie|consentimento|consent|privacidade|privacy polic|aceitar todos|"
    r"newsletter|inscreva-se|subscribe to our|chat|whatsapp|siga-nos|follow us|"
    r"copyright|todos os direitos|all rights reserved",
    re.I,
)

# [ \t] em vez de \s: \s casaria \n e o preco atravessaria linhas, quebrando
# toda a deteccao por linha.
PRICE = re.compile(
    # simbolo antes: R$ 99, $9, US$ 14
    r"(?:R\$|US\$|\$|USD|BRL|EUR|GBP|€|£)[ \t]?\d[\d.,]*"
    # simbolo depois: "4 €", "9.99 EUR" - padrao europeu, comum em SaaS da UE
    r"|\d[\d.,]*[ \t]?(?:€|£|EUR|BRL|USD)\b"
    r"|\d[\d.,]*[ \t]?(?:reais|/mês|/mo\b|/month|por mês|per month|/ano|/year|/yr)"
    r"|\b\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?\b",
    re.I,
)

# Tabela de preco costuma quebrar o valor e o periodo em elementos separados:
# "24" numa linha, "per month" na seguinte. Sem colar as duas, a linha "24" nao
# tem cifrao nenhum, o recorte a descarta e a mudanca de preco passa invisivel.
NUM_ONLY = re.compile(r"^(?:R\$|US\$|\$|€|£)?[ \t]?\d[\d.,]*[ \t]*$")
PERIOD_HINT = re.compile(
    r"^/?[ \t]*(?:per|por|a|ao|by)?[ \t]*"
    r"(?:m[eê]s|month(?:ly)?|mo|ano|year(?:ly)?|yr|usu[aá]rio|user|seat|"
    r"USD|EUR|BRL|reais|€|£)\b",
    re.I,
)

# "Ate 10 projetos" -> "Ate 3 projetos" e mudanca de plano, nao de copy.
# Sem isso o corte do limite do free passa batido, que e justamente uma das
# mudancas que o cliente mais precisa saber.
LIMIT = re.compile(
    r"\b(?:at[eé]|up to|no m[aá]ximo|max(?:imum)?|limite de|limited to)\s+\d+"
    r"|\b\d+\s*(?:projetos?|usu[aá]rios?|users?|seats?|assentos?|sites?|"
    r"dom[ií]nios?|monitors?|requisi[cç][oõ]es?|requests?|mensagens?|messages?|"
    r"cr[eé]ditos?|credits?|membros?|members?|contas?|accounts?|GB|TB|MB)\b",
    re.I,
)

PLAN_WORD = re.compile(
    r"\b(?:plano|plan|pricing|preço|preco|price|assinatura|subscription|"
    r"grátis|gratis|free|trial|teste|starter|basic|básico|basico|pro\b|plus\b|"
    r"premium|business|enterprise|team|ilimitado|unlimited|por usuário|per user|"
    r"per seat|desconto|discount|off\b|cupom|coupon|anual|annual|mensal|monthly|"
    r"limite|limit|créditos|creditos|credits|seats|frete|parcela|à vista|a vista|"
    r"estoque|disponível|disponivel|esgotado|sold out|out of stock)\b",
    re.I,
)


# Marca de secao. Sem ela o alerta diz "45% OFF saiu" numa pagina que tem 45%
# OFF em tres lugares diferentes - e o cliente nao sabe qual.
SECTION_MARK = "§ "
HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


# Titulo com mais que isso e paragrafo de marketing, nao rotulo de secao.
# A Bling usa um <h2> de 200 chars ("Integre mais de 400 canais, venda com...")
# que nao localiza nada.
MAX_SECTION_LEN = 60


def secao_de(lines: list[str], idx: int) -> str | None:
    """O titulo curto mais proximo acima da linha idx."""
    reserva = None
    for j in range(min(idx, len(lines) - 1), -1, -1):
        if not lines[j].startswith(SECTION_MARK):
            continue
        titulo = lines[j][len(SECTION_MARK):].strip()
        if not titulo:
            continue
        if len(titulo) <= MAX_SECTION_LEN:
            return titulo
        if reserva is None:
            reserva = titulo[:MAX_SECTION_LEN].rstrip() + "..."
    return reserva


def visible_text(html: str, css: str | None = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(list(DROP_TAGS)):
        tag.decompose()

    # Prefixa titulos para saber, depois, em que secao cada linha vive.
    for tag in soup.find_all(HEADING_TAGS):
        texto = tag.get_text(" ", strip=True)
        if texto:
            tag.string = f"{SECTION_MARK}{texto}"

    root = soup
    if css:
        picked = soup.select(css)
        if picked:
            root = BeautifulSoup("".join(str(p) for p in picked), "html.parser")

    raw = root.get_text("\n", strip=True)
    lines = []
    for line in raw.splitlines():
        line = re.sub(r"[ \t ]+", " ", line).strip()
        if not line or len(line) < 2:
            continue
        if JUNK_LINE.search(line):
            continue
        lines.append(line)

    # Cola "24" + "per month" numa linha so, antes de qualquer outra coisa.
    glued = []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if NUM_ONLY.match(line) and PERIOD_HINT.match(nxt):
            glued.append(f"{line.strip()} {nxt.strip()}")
            i += 2
            continue
        glued.append(line)
        i += 1

    # Remove repeticao imediata (menus duplicados por breakpoint responsivo).
    out = []
    for line in glued:
        if not out or out[-1] != line:
            out.append(line)
    return "\n".join(out)


def pricing_slice(text: str, window: int = 1, context_max_len: int = 80) -> str:
    """So as linhas com preco/plano/limite, mais um pouco de contexto ao redor.

    O contexto entra so se for curto: celula de tabela de preco tem rotulo, nao
    paragrafo. Sem esse corte, um post do blog ao lado do titulo "Planos"
    entraria no diff e viraria alerta falso a cada revisao de texto.
    """
    lines = text.splitlines()
    hits = {
        i for i, line in enumerate(lines)
        if PRICE.search(line) or PLAN_WORD.search(line) or LIMIT.search(line)
    }
    # Titulos ficam sempre: sao o mapa que localiza a mudanca depois.
    keep = set(hits) | {i for i, line in enumerate(lines) if line.startswith(SECTION_MARK)}
    for i in hits:
        for j in range(max(0, i - window), min(len(lines), i + window + 1)):
            if len(lines[j]) <= context_max_len:
                keep.add(j)
    sliced = [lines[i] for i in sorted(keep)]
    # Se o recorte falhou (pagina sem sinal de preco), devolve tudo: melhor
    # alertar demais uma vez do que cegar o monitoramento. O teste e sobre os
    # hits de preco, nao sobre o total - titulos entram sempre e mascarariam
    # uma pagina que nao tem preco nenhum.
    return "\n".join(sliced) if len(hits) >= 3 else text


def prepare(html: str, mode: str = "pricing", css: str | None = None) -> str:
    text = visible_text(html, css)
    if mode == "pricing":
        return pricing_slice(text)
    if mode == "product":
        return pricing_slice(text, window=2)
    return text
