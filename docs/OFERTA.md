# Oferta, DMs e FAQ

Regra que vale para tudo aqui: **nunca peça atenção sem entregar um fato primeiro.**
A mensagem que converte não é "criei um SaaS", é "seu concorrente baixou o preço ontem".

`python -m vigia brief <dominio> --days 3` monta a versão com os fatos reais já preenchidos.
Os textos abaixo são o molde.

---

## A oferta em uma frase

**PT**
> Eu monitoro as páginas públicas de preço dos seus concorrentes e te aviso no Telegram só quando muda o que importa: preço, plano, limite do grátis, feature. 10 URLs. 7 dias grátis. Depois R$49/mês. Cancela com uma mensagem.

**EN**
> I watch competitor pricing pages and send a Telegram digest of only the changes that matter (price, plan, limits). 10 URLs. 7 days free. Then $9/mo. Cancel in one message.

---

## DM 1 — houve mudança (a melhor)

**EN**
> Hey — I've been watching [CONCORRENTE]'s pricing page for the last 3 days.
> They dropped Pro from $49 to $39 and cut the free tier from 3 projects to 1.
>
> I watch competitor pricing pages and send a Telegram digest of only the changes that matter — price, plans, limits. No cookie-banner noise.
>
> Want the rest of the week free? If it's useful it's $9/mo after that, cancel in one message.

**PT**
> Oi! Nos últimos 3 dias eu acompanhei a página de preços da [CONCORRENTE].
> Eles baixaram o Pro de R$99 para R$79 e cortaram o plano grátis de 3 para 1 projeto.
>
> Eu monitoro páginas públicas de concorrentes e mando no Telegram só o que importa: preço, plano, limite. Sem alerta de banner de cookie.
>
> Quer receber isso de graça pelo resto da semana? Se for útil, R$49/mês. Cancela com uma mensagem.

## DM 2 — nada mudou (funciona, é sinal)

**EN**
> Watched [CONCORRENTE] and [CONCORRENTE 2] for 3 days: zero pricing changes. That's a signal too — nobody's moving right now.
> I'll ping you on Telegram the day one of them does. Want your competitors on the list for the rest of the week, free?

**PT**
> Acompanhei [CONCORRENTE] por 3 dias: nenhuma mudança de preço. Isso também é informação — ninguém está mexendo agora.
> Te aviso no Telegram no dia em que mudar. Quero incluir os seus concorrentes de graça pelo resto da semana. Topa?

## DM 3 — comentário em comunidade (r/SaaS, "how do you track competitors?")

> Manually, until it got embarrassing. Now I diff the visible text of their pricing pages every 6h and have a model throw away anything that isn't price/plan/limit — cookie banners and "3 people are viewing" counters are 90% of the noise in tools like Visualping.
> Happy to point mine at your competitors for a week if you want to see the output, no strings.

Sem link no primeiro comentário. Só depois de o terceiro comentário ter sido útil.

## Mensagem do dia 8 — a cobrança

**PT**
> A semana grátis fecha hoje. Nesses 7 dias você recebeu [N] alertas, [M] deles de mudança de preço.
> Para continuar: R$49/mês no Pix (chave abaixo) ou cartão. Se não fizer sentido, sem problema — eu paro hoje e não te cobro nada.
> Chave Pix: [CHAVE DO RESPONSÁVEL]

**EN**
> Free week ends today. You got [N] alerts, [M] of them actual price changes.
> To keep it running: $9/mo, card link below. If it's not worth it, no problem — I'll stop today, no charge.

Não peça call. Se pedirem call, o responsável entra. Texto converte e é mais seguro.

---

## FAQ (8 linhas, cole quando perguntarem)

1. **O que você monitora?** Qualquer página pública que você me passar: preço, planos, changelog, produto, termos.
2. **Com que frequência?** A cada 6h no Starter, 1h no Pro. Nunca mais rápido que isso — eu não sobrecarrego o site de ninguém.
3. **Como chega o alerta?** Telegram. E-mail se você preferir.
4. **Vou receber alerta de banner de cookie?** Não. É exatamente o problema que eu resolvo: filtro de texto + IA que joga fora o que não é preço/plano/feature. Se passar lixo, responde /lixo e eu ajusto.
5. **Página com login?** Não monitoro. Só o que é público sem login. Sem captcha, sem contornar bloqueio.
6. **Guarda meus dados?** Só a URL que você pediu, o texto público dela e o histórico das mudanças. Nada de dado pessoal de terceiros.
7. **Como cancelo?** Uma mensagem no Telegram. Sem formulário, sem ligar.
8. **Quem emite a nota?** A conta é titularizada pelo meu responsável legal. Pix ou cartão no nome dele.

---

## O que é proibido no dia 1

- Product Hunt, anúncio pago, "build in public" como estratégia principal.
- Pedir para amigo ou parente fingir que é cliente. Isso destrói o único dado que importa.
- Prometer feature que não existe (dashboard, Slack, WhatsApp) para fechar venda.
- Se apresentar como "CEO de 14 anos". Venda o digest. Idade só se perguntarem — e aí, verdade.
