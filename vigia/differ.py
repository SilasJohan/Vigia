"""Diff textual com filtro de ruido. Nada de pixel.

Se mais de 40% dos alertas forem lixo, o produto morre. O filtro daqui e a
primeira linha de defesa; a IA e a segunda.
"""

import difflib
import hashlib
import re

from . import config
from . import extract
from .extract import LIMIT, PRICE, SECTION_MARK

# Mudanca curta mas que muda a decisao de compra: promocao, corte, plano novo.
PROMO = re.compile(
    r"\b(?:off\b|desconto|discount|promo(?:tion|cao|ção)?|black\s?friday|cyber|"
    r"cupom|coupon|gr[aá]tis|free\b|sale\b|save\b|oferta|%)",
    re.I,
)

# Coisas que mudam a cada request e nao significam nada.
VOLATILE = [
    (re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b"), "<hora>"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "<data>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<data>"),
    (re.compile(r"\bh[áa] (?:cerca de )?\d+ (?:segundos?|minutos?|horas?|dias?)\b", re.I), "<relativo>"),
    (re.compile(r"\b\d+ (?:seconds?|minutes?|hours?|days?) ago\b", re.I), "<relativo>"),
    (re.compile(r"\b(?:19|20)\d{2}\b"), "<ano>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<uuid>"),
    (re.compile(r"\b[0-9a-f]{24,}\b", re.I), "<hash>"),
    (re.compile(r"\b\d+ (?:visitas?|views?|pessoas? (?:est[aã]o|viram)|vendidos?|sold)\b", re.I), "<contador>"),
    (re.compile(r"\b(?:restam|apenas|only|last)\s+\d+\s+(?:vagas?|unidades?|spots?|left)\b", re.I), "<escassez>"),
]


def denoise(text: str) -> str:
    for pattern, token in VOLATILE:
        text = pattern.sub(token, text)
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha256(denoise(text).encode("utf-8")).hexdigest()


# Linha que carrega um token volatil nao justifica alerta sozinha. "Atualizado
# em <data> as <hora>" tem palavras de verdade, entao exigir que a linha fosse
# SO tokens nao pegava o caso - e uma pagina que passa a exibir o horario da
# ultima atualizacao acordava o cliente por nada.
#
# <ano> fica FORA da lista de proposito: "Black Friday 2026 - 50% off" contem um
# ano e e exatamente o tipo de mudanca que o cliente quer receber.
NOISE_TOKEN = re.compile(r"<(?:hora|data|relativo|uuid|hash|contador|escassez)>")

# Linha sem nenhum texto proprio (so numero, pontuacao ou token).
TOKEN_ONLY = re.compile(r"^(?:<[a-z]+>|[\s\W_\d])*$")


def is_noise_line(content: str) -> bool:
    return bool(NOISE_TOKEN.search(content) or TOKEN_ONLY.match(content))


def drop_noise_lines(diff: str) -> str:
    """Tira do diff as linhas alteradas que sao so ruido.

    Mexe apenas no que e mostrado/contado - o diff aqui nunca e aplicado como
    patch, entao a contagem do cabecalho @@ nao precisa fechar.
    """
    blocos, atual, mudou = [], [], False
    for line in diff.splitlines():
        if line.startswith("@@"):
            if mudou:
                blocos.extend(atual)
            atual, mudou = [line], False
            continue
        if line[:1] in "+-" and not line.startswith(("+++", "---")):
            if is_noise_line(line[1:].strip()):
                continue  # ruido: nao entra nem na conta nem na mensagem
            mudou = True
        atual.append(line)
    if mudou:
        blocos.extend(atual)
    return "\n".join(blocos)


def build_diff(old: str, new: str, context: int = 1, max_lines: int = 120) -> str:
    old_lines = denoise(old).splitlines()
    new_lines = denoise(new).splitlines()
    lines = list(
        difflib.unified_diff(old_lines, new_lines, lineterm="", n=context)
    )[2:]  # descarta os cabecalhos ---/+++
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (+{len(lines) - max_lines} linhas)"]
    return drop_noise_lines("\n".join(lines))


# O que torna uma linha "citavel": um valor. E o que vale procurar no resto da
# pagina antes de afirmar que saiu.
TOKEN_CITAVEL = re.compile(r"\d[\d.,]*\s?%|(?:R\$|US\$|\$|€|£)\s?\d[\d.,]*|\d[\d.,]{2,}")


def ainda_na_pagina(linha: str, lines: list[str], minimo: float = 0.72):
    """O trecho saiu daqui, mas o mesmo valor continua em outro lugar?

    A pagina da Bling tem '45% OFF' em tres trechos. Quando um sai, dizer so
    "45% OFF saiu" faz o cliente abrir a pagina, achar 45% OFF em outro canto e
    concluir que voce errou. Este aviso evita afirmar besteira numa DM.

    Procura primeiro pelo VALOR (comparar linha inteira por similaridade nao
    pega '45% OFF' dentro de 'Oferta Black: 45% OFF*'), depois por semelhanca.
    """
    alvo = linha.strip()
    if not alvo:
        return None

    for token in TOKEN_CITAVEL.findall(alvo):
        for i, outra in enumerate(lines):
            if outra.startswith(SECTION_MARK):
                continue
            if token in outra and outra.strip() != alvo:
                return {"linha": outra.strip(), "pos": i, "token": token, "como": "valor"}

    if len(alvo) < 12:
        return None
    baixo = alvo.lower()
    melhor, melhor_i = 0.0, None
    for i, outra in enumerate(lines):
        o = outra.strip().lower()
        if not o or o == baixo or outra.startswith(SECTION_MARK):
            continue
        r = difflib.SequenceMatcher(None, baixo, o).ratio()
        if r > melhor:
            melhor, melhor_i = r, i
    if melhor >= minimo:
        return {"linha": lines[melhor_i].strip(), "pos": melhor_i,
                "token": None, "como": "texto parecido"}
    return None


def pair_changes(old: str, new: str, max_pairs: int = 8):
    """Emparelha o que era com o que passou a ser, e localiza cada mudanca.

    Devolve dicts com antes/agora (None = saiu/entrou), a secao em que a linha
    vive, a posicao no texto e o aviso de texto semelhante remanescente.
    """
    a = denoise(old).splitlines()
    b = denoise(new).splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)

    pares = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        antes = [(i, a[i].strip()) for i in range(i1, i2)
                 if a[i].strip() and not is_noise_line(a[i].strip())]
        agora = [(j, b[j].strip()) for j in range(j1, j2)
                 if b[j].strip() and not is_noise_line(b[j].strip())]
        if not antes and not agora:
            continue

        # Ancora no texto NOVO: as linhas intactas em volta da alteracao.
        # E o que realmente localiza a mudanca numa pagina de 300 trechos -
        # muito mais util que um <h2> qualquer.
        def _viz(idx, passo):
            k = idx
            while 0 <= k < len(b):
                if b[k].strip() and not b[k].startswith(SECTION_MARK):
                    return b[k].strip()
                k += passo
            return None

        vizinhos = (_viz(j1 - 1, -1), _viz(j2, 1))

        for k in range(max(len(antes), len(agora))):
            i_ant, txt_ant = antes[k] if k < len(antes) else (None, None)
            j_ago, txt_ago = agora[k] if k < len(agora) else (None, None)

            # Localiza pelo lado que existe; se saiu, usa o texto antigo.
            if j_ago is not None:
                secao, pos, total = extract.secao_de(b, j_ago), j_ago, len(b)
            else:
                secao, pos, total = extract.secao_de(a, i_ant), i_ant, len(a)

            pares.append({
                "antes": txt_ant,
                "agora": txt_ago,
                "secao": secao,
                "pos": pos,
                "total": total,
                "vizinhos": vizinhos,
                "grupo": (tag, i1, j1),  # para juntar o que e um bloco so
                # so faz sentido avisar quando a linha desapareceu
                "resto": ainda_na_pagina(txt_ant, b) if (txt_ant and not txt_ago) else None,
            })
    return pares[:max_pairs]


def changed_chars(diff: str) -> int:
    total = 0
    for line in diff.splitlines():
        if line[:1] in "+-" and not line.startswith(("+++", "---")):
            total += len(line.strip("+- ").strip())
    return total


def changed_text(diff: str) -> str:
    return "\n".join(
        line[1:].strip()
        for line in diff.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )


def is_significant(diff: str, min_chars: int | None = None) -> bool:
    """Tamanho OU sinal.

    So por tamanho, "Black Friday 2026: 50% off" (27 chars) e "Ate 3 projetos"
    (corte do plano gratis) ficariam abaixo do limiar de 40 e passariam batidos -
    justamente os alertas que o cliente quer. Linha curta com preco, desconto ou
    limite passa direto; o resto ainda precisa de volume.
    """
    if not diff.strip():
        return False
    mudado = changed_text(diff)
    if PRICE.search(mudado) or PROMO.search(mudado) or LIMIT.search(mudado):
        return True
    return changed_chars(diff) >= (
        config.MIN_DIFF_CHARS if min_chars is None else min_chars
    )
