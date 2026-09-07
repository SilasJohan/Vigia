# A quem vender, e por quê esses

Pesquisa feita em 2026-09-07. Tudo aqui foi verificado com o próprio Vigia ou lido
na página ao vivo. Onde eu não confirmei, está escrito que não confirmei.

---

## 1. O ângulo de venda que eu achei (e que muda o pitch do plano)

O plano original vendia: *"saiba quando o concorrente mudar de preço."* É verdadeiro,
mas é vago — o cliente ouve isso e pensa "legal", não "preciso disso hoje".

O que a pesquisa mostrou é mais afiado. Micro-SaaS em categoria disputada vive de
páginas de comparação para SEO: `youform.com/fillout-alternative/`,
`hyperping.com/blog/best-uptimerobot-alternatives`, `sleekplan.com/blog/top-10-productboard-alternatives`.
Essas páginas têm **o preço do concorrente escrito na mão dentro do texto**.

Quando o concorrente muda o preço, a página não muda. Ela simplesmente passa a mentir
— e continua ranqueando, atraindo visitante e convertendo pior, calada.

**Prova que eu verifiquei hoje, não suposição:**

- A página da Tally diz, agora: **Pro $24/mês, Business $74/mês** (mensal é o padrão).
- Artigos de 2026 que ranqueiam para "best Tally alternatives" citam **$29 e $89**.
- Ou seja: quem tem uma página `/vs/tally` está com 17–20% de erro no argumento
  principal dela, e não sabe.

- A Hyperping mantém, à mão, os preços de **cinco** concorrentes espalhados em 8+ posts:
  UptimeRobot `$12/$39`, Better Stack `$21/$29/$12/$17`, Cronitor `$2/monitor`,
  Pingdom `$18/$78/$149/$1.295`, Uptime.com `$7/$30/$60/$600`.
- A Youform cita Fillout como `$15/$40/$75`. Conferi na Fillout: está **correto hoje**.
  Isso é a pior notícia possível para eles e a melhor para você — significa que alguém
  ali gasta tempo toda semana conferindo isso na mão.

**O pitch, então, não é "monitore seu concorrente". É:**

> Suas páginas de comparação citam o preço do concorrente. No dia em que ele mudar,
> sua melhor página de SEO passa a mentir e você não é avisado. Eu te aviso no mesmo dia.

Isso tem dono (quem escreveu a página), tem urgência (já pode estar errado agora) e
tem número (quantas páginas × quantos preços). É o que se responde numa DM.

## 2. Quem compra: o entrante, nunca o líder

A Plausible não liga para o preço da Pirsch. A Pirsch vive dele.

Regra para escolher alvo: **quem precisa se posicionar contra alguém maior.** Por isso
`prospects.csv` está ordenado por "papel no cluster", e os líderes (Canny, Tally,
Better Stack, Bling) aparecem só em `monitorar.csv` — eles são o que você vigia
*para* o cliente, não o cliente.

Sinais, em ordem de força:

1. Publica post "alternativas ao X" com preço do concorrente escrito no texto. ← mais forte
2. É o menor/mais novo de um cluster com 4+ players brigando por preço.
3. Time de 1 a 5 pessoas, sem VC (decide sozinho, assina sozinho, não tem processo de compras).
4. Preço público baixo ($4–29) — categoria onde preço é o argumento.
5. Concorrentes dele são monitoráveis sem browser (verifiquei; está em `monitorar.csv`).

## 3. Os 12 alvos

Em `alvos/prospects.csv`. Resumo:

| # | Alvo | Cluster | Por quê | Vigiar para ele |
|---|---|---|---|---|
| 1 | **Hyperping** | uptime | 8+ posts com preço de 5 concorrentes na mão. 4 pessoas, 7 anos sem VC. Contato público confirmado: `hello@hyperping.io` | UptimeRobot, Better Stack, Cronitor, Pulsetic |
| 2 | **Youform** | forms | Mantém 2 páginas `/vs/` com preço do concorrente, e mantém certo — na mão | Tally, Fillout, Formbricks |
| 3 | **Sleekplan** | feedback | Publica "Top 10 Productboard Alternatives" | Canny, Featurebase, Frill, UserJot |
| 4 | **Featurebase** | feedback | Publica alternatives sobre ProductPlan e Sleekplan | Canny, Sleekplan, UserJot |
| 5 | **Muro Analytics** | analytics | Entrante novo onde todos brigam por $4–9 | Plausible, Fathom, Simple Analytics |
| 6 | **UserJot** | feedback | $0/$29/$59 em cluster de 8 players | Canny, Featurebase, Sleekplan |
| 7 | **Pulsetic** | uptime | Se posiciona como "o substituto do UptimeRobot" | UptimeRobot, Hyperping, Better Stack |
| 8 | **Formbricks** | forms | OSS entrando onde Tally e Fillout mexeram no preço | Tally, Fillout, Youform |
| 9 | **CaptureKit** | screenshot | Entrante barato vs ScreenshotOne $79 e Urlbox $99 | ScreenshotOne, Urlbox, ApiFlash |
| 10 | **openstatus** | uptime | OSS com plano pago, time mínimo | Better Stack, Hyperping |
| 11 | **Magis5** | e-commerce BR | Hub disputando com Bling (R$49) e Tiny. **Paga em Pix, fala português** | Bling, Olist Tiny, Ideris, Nuvemshop |
| 12 | **Ideris** | e-commerce BR | Mesmo cluster. **Pix, português** | Bling, Olist Tiny, Magis5 |

Só o contato da Hyperping está confirmado. Nos outros o campo está **vazio de
propósito** — inventar e-mail queima o domínio e é a única coisa aqui que não dá para
desfazer. Pegue no rodapé do site ou no byline do blog deles.

## 4. A DM da Hyperping (alvo #1, pronta)

Assunto: `your UptimeRobot comparison page has a shelf life`

> Hi Léo,
>
> Your "best UptimeRobot alternatives" post quotes UptimeRobot at $12 Solo / $39 Team,
> Better Stack at $21 per 50 monitors, and Cronitor at $2/monitor. I count five
> competitors' prices hardcoded across your alternatives posts.
>
> The day any of them changes, those pages start costing you conversions and nothing
> tells you. I've been diffing all four pricing pages every 6h — text only, cookie
> banners and visitor counters filtered out — and I send a Telegram message when a
> price, plan or free-tier limit actually moves.
>
> Want it pointed at your four for the rest of the week, free? If it's useful it's
> $9/mo after that, cancel in one message. If nothing moves, I'll tell you that too —
> "no one is repricing right now" is worth knowing before you reprice.
>
> — Silas

Por que funciona: começa com **o dado deles**, não com você. Diz o custo do problema.
Oferece grátis e limitado. Preço na mensagem, sem call. E o P.S. honesto ("se nada mudar
eu digo") remove a suspeita de que você vai inventar alerta para justificar a cobrança.

**Antes de mandar, tenha o fato na mão:**
```
python -m vigia carregar alvos/monitorar.csv --cluster uptime
python -m vigia check --force          # 1a passada = base
# espere 2-3 dias
python -m vigia brief uptimerobot.com --days 3
```

## 5. O molde para os outros 11

Troque três coisas: a página `/vs/` deles, o preço que ela cita, e os concorrentes.

> Your [PÁGINA /VS/] quotes [CONCORRENTE] at [PREÇO QUE A PÁGINA DIZ].
> [Se mudou: "That changed to X on [data]." / Se não: "Still accurate today — which
> means someone on your side is checking it by hand."]
>
> I diff [N] competitor pricing pages every 6h and ping you on Telegram only when a
> price, plan or limit actually moves. Want yours on it for the rest of the week, free?
> $9/mo after, cancel in one message.

Para os alvos 11 e 12 (BR), em português, R$49, Pix, e troque "Telegram" por
"Telegram ou WhatsApp" — o hub brasileiro vive no WhatsApp.

## 6. Ordem de execução

1. **Hoje** — `.env` com o token do bot (e a chave grátis da Groq).
2. **Hoje** — `python -m vigia carregar alvos/monitorar.csv` → 29 URLs no ar. As páginas
   dos 12 alvos e dos concorrentes deles começam a acumular histórico agora. Sem
   histórico você não tem DM.
3. **Hoje** — `python -m vigia check --force`, depois deixe `check --loop 60` rodando.
4. **Dias 2–3** — pegue os 11 contatos que faltam. 20 minutos de rodapé de site.
5. **Dia 3** — `python -m vigia brief <concorrente> --days 3` para cada cluster.
6. **Dia 4** — 5 DMs, começando pela Hyperping (é a única com contato confirmado e o
   melhor sinal). Uma por vez, personalizada. 5 boas valem mais que 50 iguais.
7. **Dia 8** — cobre quem estiver usando.

Se em 20 DMs com fato real ninguém pagar, o problema não é marketing: é a ideia. Esse
era o critério do seu próprio plano e ele continua valendo.

## 7. Três avisos honestos

**Isto é uma lista de alvos, não de clientes.** Todo sinal aqui é observável de fora:
tamanho do time, preço público, página de comparação. Nenhum deles disse que quer
comprar. A conversão real do plano (1 em 10) continua sendo a aposta.

**Página com botão mensal/anual pode gerar alerta falso.** A Tally mostra $24 no padrão
mensal; se ela trocar o padrão para anual, o Vigia vê o número mudar e vai achar que o
preço caiu. Quando isso incomodar, prenda a tabela com `--css`. Não é bug de coleta, é
limite de olhar só o texto renderizado.

**A lista BR (11–12) é de empresas, não do lojista do plano original.** O lojista de
Shopify/Nuvemshop não é indexável — ele está em grupo de Facebook e WhatsApp. Aquele
canal não sai de pesquisa, sai de você entrar nos grupos. Os alvos 11 e 12 são o jeito
de atacar o Brasil com a mesma DM dos outros dez.
