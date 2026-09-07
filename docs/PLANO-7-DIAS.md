# Semana 1 — o que já está pronto e o que é você

Objetivo da semana: **saber se um estranho paga.** Não é "ter um GitHub bonito".

## Estado do repositório

| Item do plano | Situação |
|---|---|
| Script de fetch + diff + filtro de ruído | pronto (`vigia/fetch.py`, `extract.py`, `differ.py`) |
| IA que decide se importa (Groq/Gemini/Ollama + fallback regex) | pronto (`vigia/ai.py`) |
| Bot Telegram (/start, URL, /list, /stop, /mode, /agora, /lixo) | pronto (`vigia/bot.py`) |
| Banco com histórico (SQLite, restart-safe) | pronto (`vigia/db.py`) |
| Gerador de briefing para DM | pronto (`python -m vigia brief`) |
| Controle de trial e cobrança no dia 8 | pronto (`python -m vigia trials`) |
| Métricas do dia 30 | pronto (`python -m vigia stats`) |
| Textos das DMs, oferta, FAQ | pronto (`docs/OFERTA.md`) |
| **Token do BotFather** | **você** |
| **Conversa com o responsável legal (titular)** | **você — bloqueia tudo** |
| **40 alvos em `alvos/alvos.csv`** | **você** |
| **10 conversas com estranhos** | **você — é aqui que a ideia vive ou morre** |

O código era a parte fácil. Está feita. O resto não terceiriza.

---

## Dia 1 — destravar o legal e montar a lista

1. **Conversa de 20 min com o responsável.** Titular legal: sim ou não. Se for não, pare — não existe versão legal disso aos 14. O que ele precisa entender: conta Mercado Pago (Pix) no nome dele, e Stripe depois, se houver receita. Você opera, ele assina.
2. `@BotFather` → `/newbot` → copie o token.
3. ```
   copy .env.example .env
   ```
   Preencha `TELEGRAM_TOKEN`. Depois mande `/start` para o seu bot e rode `python -m vigia whoami` para pegar seu `ADMIN_CHAT_ID`.
4. Chave de IA grátis (2 min, sem cartão): [console.groq.com/keys](https://console.groq.com/keys) → `GROQ_API_KEY` no `.env`.
5. `python -m vigia doctor` — tem que passar tudo.
6. Preencha `alvos/alvos.csv` até 40 linhas. **Só página pública com preço visível.**

## Dia 2 — o critério de pronto

```
python -m vigia demo
```
Isso muda um HTML local de propósito (R$99 → R$79, free de 3 → 1 projeto), filtra o banner de cookie e o rodapé, e manda o alerta no seu Telegram. Se chegou, o motor está de pé.

Depois teste em páginas reais:
```
python -m vigia add https://sentry.io/pricing/ --label Sentry
python -m vigia check --force
```

## Dia 3 — 10 monitoramentos reais, sem pedir dinheiro

```
python -m vigia add <url> --label <nome>     # 10 vezes
python -m vigia check --loop 60              # deixe rodando
```
O resto do dia é comunidade: responda 15 posts em r/SaaS, r/indiehackers e grupos BR sobre concorrência/preço. **Zero link.** Anote 20 contatos.

## Dia 4 — o teste de valor

```
python -m vigia brief sentry.io --days 3
```
Copie, ajuste, mande 5 DMs. Se nada mudou nas páginas, a DM 2 do `docs/OFERTA.md` serve — "nada mudou" também é sinal.

Suba o bot para as pessoas se servirem sozinhas:
```
python -m vigia bot
```
Meta: 3 pessoas colando URL sem você implorar.

## Dia 5 — Brasil em paralelo

5 conversas em grupos de e-commerce. Oferta em reais, Pix, Telegram.
Não venda "IA". Venda "você fica sabendo se o concorrente baixar o preço".
Se a IA estiver alertando lixo, veja quais e ajuste o `SYSTEM` em `vigia/ai.py`:
```
python -m vigia stats
```

## Dia 6 — cobrança na mesa

```
python -m vigia trials
```
Quem está com 0 dias restantes recebe a mensagem do dia 8 (`docs/OFERTA.md`).
Quando pagarem: `/pagou <chat_id> starter` no seu próprio bot.

## Dia 7 — go / no-go

**Continue** se pelo menos um for verdade:
- 1 pagamento real acima de R$20;
- 3 usuários colaram URL sozinhos e 1 perguntou "quanto custa?";
- 5 respostas "isso é exatamente o que eu preciso", com URL real, de gente que você não conhece.

**Abandone** se: só amigo comentou "legal"; a IA alerta banner de cookie e você não consegue baixar isso; você não conseguiu 10 conversas com estranhos; o responsável recusou ser titular.

---

## Deixar rodando no seu PC (Windows)

Duas janelas de terminal:
```
python -m vigia bot                # responde comandos
python -m vigia check --loop 60    # checa quem está vencido
```

Para sobreviver a reboot, agende o ciclo no Task Scheduler:
```powershell
$py = (Get-Command python).Source
schtasks /create /tn "Vigia check" /tr "$py -m vigia check" /sc minute /mo 60 /st 08:00 /f
```
Seja honesto com o cliente na semana 1: roda no seu PC. VPS só depois de MRR > R$500.
