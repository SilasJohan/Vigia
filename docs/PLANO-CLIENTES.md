# Plano de aquisição — os 12 alvos

Regra da casa: **45 minutos por dia, todo dia.** Não é maratona de fim de semana.
Aquisição é frequência, não intensidade. Rastreie tudo em `alvos/contatos.csv`.

Números honestos antes de começar, para você não se assustar no meio:
12 alvos → ~4 respostas → ~2 testes → **0 ou 1 pagante.** É pouco por design: são
12 mensagens escritas à mão, não 500 automáticas. Se der 1 pagante, você tem negócio.
Se der 0 mas 4 responderem, o problema é a oferta e dá para consertar. Se 0 responderem,
o problema é o canal.

---

## O que você vende (decore isto)

Não é "monitoramento de site". É:

> A sua página de comparação cita o preço do concorrente. Quando ele muda, a sua página
> passa a mentir e ninguém te avisa. Eu te aviso no mesmo dia.

Você tem uma prova geral e uma prova por alvo:
- **Geral:** a Tally cobra hoje $24/$74. Artigos de 2026 que ranqueiam para "Tally
  alternatives" dizem $29/$89. O erro está no ar agora.
- **Por alvo:** a auditoria da Fase 2, abaixo.

---

## FASE 0 — hoje, 30 minutos (obrigatória, tudo depende dela)

```
python -m vigia whoami            # mande /start enquanto ele espera
# cole o chat_id no .env como ADMIN_CHAT_ID
python -m vigia carregar alvos/monitorar.csv
python -m vigia check --force     # 1a passada: grava o preço de hoje de 29 páginas
python -m vigia check --loop 60   # deixe rodando
```

Sem isso você não tem o que dizer na mensagem. Com isso, você tem **o preço real de hoje
de 29 páginas**, que é justamente o que ninguém tem à mão.

## FASE 1 — dias 1 e 2, 45 min/dia: achar a pessoa, não a empresa

`hello@empresa.com` é caixa de spam. Você quer a pessoa que **escreveu a página de
comparação** — é ela que sente a dor de a página estar errada.

Na Hyperping, por exemplo, o CEO é Léo Bäker, mas quem cuida de conteúdo é Nicolas
Mérouze. A dor da página desatualizada é do Nicolas. Mande para ele, ou para
`hello@` mencionando o post.

Rota para cada alvo (já anotada em `alvos/contatos.csv`):

1. Rodapé do site → e-mail público.
2. O post de comparação → **quem assinou**. Esse nome é seu alvo.
3. `x.com` → busque o nome + a empresa → handle.
4. OSS (Formbricks, openstatus) → GitHub + Discord. Nesses dois, **entre no Discord e
   seja útil por dois dias antes de qualquer oferta.** Vender de primeira em Discord
   de projeto queima você.
5. BR (Magis5, Ideris) → e-mail comercial do site, LinkedIn dos sócios.

Meta da fase: **10 dos 12 com contato preenchido.** Se um alvo não tem contato achável
em 5 minutos, marque `morto` e siga. Não existe alvo insubstituível.

## FASE 2 — dia 3, 45 min: a auditoria (é isso que faz a mensagem funcionar)

Para cada alvo, monte 3 linhas. É trabalho manual e é exatamente onde está o valor.

1. Abra a página de comparação dele (`/vs/x`, `/alternatives`, o post do blog).
2. Anote **cada preço de concorrente que a página cita**.
3. Compare com o preço real de hoje — você já tem, em `alvos/monitorar.csv` e no
   `python -m vigia stats`.

Resultado, um dos dois, e **os dois servem**:

- **Está errado** → você tem uma bomba. "Sua página diz $29, o real é $24."
- **Está certo** → você tem outra coisa, quase tão boa: "Está certo hoje — o que significa
  que alguém do seu time confere isso na mão. Eu faço isso de graça pelo resto da semana."

Não espere uma mudança acontecer para mandar a mensagem. A auditoria já é o valor.

## FASE 3 — dias 3 a 10: a sequência de 3 toques

Uma pessoa por vez, escrita à mão. Sem ferramenta de disparo, sem cópia carbono.
Além de queimar o domínio, disparo em massa para lista sem consentimento é problema
legal (GDPR/LGPD) — e o seu diferencial é justamente não ser mais um robô.

### Toque 1 — a auditoria

Assunto: `your [CONCORRENTE] comparison page has a shelf life`

> Hi [NOME],
>
> Your [PÁGINA] quotes [CONCORRENTE] at [PREÇO CITADO]. I checked their live page today:
> it's [PREÇO REAL]. / It's still accurate — which means someone on your side is
> checking it by hand.
>
> I diff [N] competitor pricing pages every 6h — text only, cookie banners and visitor
> counters filtered out — and send a Telegram message when a price, plan or free-tier
> limit actually moves.
>
> Want it pointed at [CONCORRENTE 1], [2] and [3] for the rest of the week, free?
> $9/mo after that if it's useful, cancel in one message. If nothing moves I'll tell you
> that too — "nobody is repricing right now" is worth knowing before you reprice.
>
> — Silas

Por que funciona: abre com **o dado dele**, não com você. Nomeia o custo. Grátis e com
prazo. Preço na mensagem (sem "vamos marcar uma call"). E o parágrafo final tira a
suspeita de que você vai inventar alerta para justificar cobrança.

### Toque 2 — +3 dias, só se ele não respondeu

Não repita o pedido. **Entregue de novo.**

> Quick follow-up with actual data: in the last 3 days [CONCORRENTE 1] and [2] didn't
> move, [3] changed [O QUE]. Full week free if you want it on yours — just say go.

Isso prova que o serviço existe e está rodando. É o toque que mais converte, porque a
maioria some depois do primeiro.

### Toque 3 — +4 dias, e é o último

> Last one from me — I'll stop here. If competitor pricing ever becomes a thing you
> want watched, I'm at [contato]. Either way, your [PÁGINA] is accurate as of today.

Sai deixando valor. Alguns voltam meses depois; quem insiste um 4º toque não volta nunca.

### Ajustes por canal

- **X/DM:** corte para 3 linhas. O fato, a oferta, o preço. Nada de assunto.
- **Discord (Formbricks, openstatus):** não mande oferta. Poste a auditoria como
  contribuição no canal certo e deixe a pergunta vir.
- **BR (Magis5, Ideris):** português, R$49, Pix, e ofereça WhatsApp junto do Telegram —
  hub brasileiro vive no WhatsApp.

## FASE 4 — as respostas que você vai receber

Tenha estas prontas. Improvisar aqui é onde se perde a venda.

**"Já usamos Visualping / Distill."**
> Makes sense. The difference is what doesn't arrive: mine ignores cookie banners,
> visitor counters and date changes, and only pings on price/plan/limit. If you're
> happy with the noise level there, honestly keep it.

**"Quanto custa?" / "Está caro."**
> $9/mo for 10 URLs. If that's the blocker I'd rather you not pay — the free week is
> real and there's no card.

**"Quem é você?" / "Que empresa é essa?"**
> I build it myself. The account and invoicing are in my legal guardian's name — I'm 14.
> Happy to keep it text-only. The audit above is the actual work; judge that.

Não abra a idade sozinho. Se perguntarem, responda numa linha, com a verdade, e volte
para o trabalho. Quem valoriza o dado não liga; quem liga não ia comprar mesmo.

**"Vamos marcar uma call?"**
> I'd rather keep it in writing — faster for both of us. Anything you'd ask on a call
> I can answer here today.

Recuse call sozinho, sempre. Se for indispensável, seu responsável entra.

**"Manda nota fiscal / contrato."**
> Sure — it goes out under my guardian's registration. Give me a day.

Aí é conversa com o responsável, não improviso seu.

**"Como sei que funciona?"**
> You already saw it: the audit in my first message came out of it. Point it at three
> URLs and you'll have alerts within 24h.

## FASE 5 — a rotina diária de 45 min

| Bloco | O quê |
|---|---|
| 10 min | Ler os alertas da noite. Marcar lixo com `/lixo_<n>`. Se passar de 30% de lixo, isso é a prioridade do dia, não vender. |
| 15 min | 1 auditoria nova ou 1 contato novo achado. |
| 15 min | Mandar 1 ou 2 toques. Atualizar `contatos.csv`. |
| 5 min | Anotar em `notas` a **frase exata** de quem respondeu. |

Aquela última coluna vale mais que o código. Cinco frases de estranhos dizendo por que
não compraram valem mais que qualquer palpite meu ou seu.

## FASE 6 — quando os 12 acabarem: o motor de alvos

Não me peça outra lista. O padrão se repete e você aplica sozinho:

1. Busque `"<líder> alternatives" 2026` ou `"vs <líder>"`.
2. **Quem escreveu o post é o alvo.** Ele acabou de provar que monitora concorrente na mão.
3. Confirme: time pequeno? preço público baixo? é o menor do cluster? → entra na lista.
4. Rode a URL dele pelo Vigia. Monitorável? → `monitorar.csv`.

Clusters que ainda não toquei e têm a mesma cara: encurtador de link (Dub, Short.io),
agendamento (Cal.com, SavvyCal, Zcal), e-mail transacional (Resend, Loops, Postmark),
newsletter (Buttondown, beehiiv), session replay, CRM para solo.

Cada cluster novo = 3 a 5 alvos. Você não vai ficar sem alvo; vai ficar sem tempo.

## Metas e linha de corte

| Dia | Meta |
|---|---|
| 2 | 10 dos 12 com contato |
| 3 | 5 auditorias prontas |
| 5 | 8 toques 1 enviados |
| 8 | 12 toques 1, 6 toques 2, ≥3 respostas |
| 10 | ≥2 pessoas usando o bot sozinhas |
| 14 | 1 pagante — ou 20 conversas reais explicando por que não |

**Mate o alvo** (não o projeto) depois do toque 3 sem resposta.

**Mate a ideia** se, no dia 21, você tiver 20+ conversas reais e zero real recebido.
Esse é o critério do seu próprio plano e ele continua valendo. "Falta marketing" não é
diagnóstico.

**Não mate** por: ninguém responder nos 3 primeiros dias (normal), landing feia (você
não tem landing e não precisa), ou uma semana sem mudança nas páginas (é sinal, e você
vende isso).
