# Vigia

Monitora páginas **públicas** de concorrentes (preço, plano, feature), resume a
mudança com IA e alerta no Telegram — jogando fora o que não importa.

O diferencial não é o crawler. É o recorte: banner de cookie, contador de
visitas, data no rodapé e "restam 3 vagas" não geram alerta.

## Começo rápido

```bash
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

Preencha no `.env`:

- `TELEGRAM_TOKEN` — crie o bot no [@BotFather](https://t.me/BotFather) (`/newbot`)
- `GROQ_API_KEY` — grátis, sem cartão, em [console.groq.com/keys](https://console.groq.com/keys)
  (opcional: sem chave de IA nenhuma, o Vigia cai numa heurística por regex e continua funcionando)

Depois:

```bash
python -m vigia whoami        # mande /start ao bot e pegue seu ADMIN_CHAT_ID
python -m vigia doctor        # ambiente, Telegram e IA de pé?
python -m vigia demo          # muda um HTML local e manda o alerta no seu Telegram
```

## Uso

```bash
python -m vigia add https://sentry.io/pricing/ --label Sentry
python -m vigia add https://loja.com/produto/x --mode product
python -m vigia list
python -m vigia check --force            # um ciclo agora, ignorando intervalo
python -m vigia check --loop 60          # deixa rodando no PC
python -m vigia bot                      # o cliente se serve sozinho pelo Telegram
python -m vigia brief sentry.io --days 3  # texto pronto da DM de aquisição
python -m vigia carregar alvos/monitorar.csv   # 29 alvos verificados de uma vez
python -m vigia trials                   # quem vence o teste grátis (cobrar!)
python -m vigia dossie Bling             # evidência de uma página + frase pronta para citar
python -m vigia rebase                   # descarta a base (ao mudar --mode / --css / extrator)
python -m vigia mercado                  # o mercado se move? mede a premissa do negócio
python -m vigia stats                    # métricas, incluindo taxa de lixo
```

### Comandos do bot

Cole uma URL · `/list` · `/stop <id>` · `/mode pricing|product|page` ·
`/agora` · `/preco` · `/texto_<n>` · `/lixo_<n>` · `/ajuda`
Admin: `/stats`, `/pagou <chat_id> <plano>`

## Modos

| Modo | O que entra no diff |
|---|---|
| `pricing` | só linhas com preço, plano, desconto, limite (padrão) |
| `product` | preço, título, estoque, com mais contexto ao redor |
| `page` | todo o texto visível; a IA classifica importante vs lixo |

`--css ".pricing-table"` recorta antes de tudo, quando você sabe onde olhar.

## Como funciona

```
fetch httpx ──(app shell vazio?)──> Playwright
     │
     v
texto visível (sem script/nav/footer/cookie)
     │
     v
recorte do modo ──> denoise (data, hora, uuid, contador, escassez)
     │
     v
hash igual? ──sim──> nada
     │ não
     v
diff unificado ──> menor que MIN_DIFF_CHARS? ──sim──> ruído, só atualiza a base
     │ não
     v
IA: {important, category, summary}   (Groq → Gemini → Ollama → regex)
     │
     v
important? ──sim──> Telegram + grava em changes
```

## Regras que o código respeita

- Página pública ou não monitora. **Sem login, sem captcha, sem contornar bloqueio.**
- Intervalo mínimo de 6h por URL; 2s entre requisições. Você é um visitante, não um DDoS.
- User-Agent identificável: `VigiaBot/0.1 (+URL)`.
- Se o site bloquear (403/429), o cliente é avisado na 3ª falha. Não insistimos.
- Guarda só a URL pedida, o texto público dela e o histórico. Nada de PII de terceiros.

## Limitações conhecidas

- Página com botão **mensal/anual** mostra só o estado padrão. Se o site trocar o
  padrão, o Vigia lê um número diferente e reporta "mudança de preço" que não houve.
  Prenda a tabela com `--css` quando isso incomodar.
- Preço renderizado por JS exige Playwright (verificado: Pirsch, Umami, Counter).
- Site que responde 403 (ex.: Nolt) não é monitorado. É decisão, não limitação.

## Estrutura

```
vigia/
  config.py    .env, limites de plano, User-Agent
  db.py        SQLite: subscribers, watches, changes
  fetch.py     httpx + Playwright opcional
  extract.py   HTML -> texto visível; recorte pricing/product
  differ.py    denoise + diff + limiar de significância
  ai.py        Groq / Gemini / Ollama / heurística regex
  tg.py        Telegram Bot API direto (sem SDK)
  runner.py    o ciclo de checagem
  bot.py       long polling dos comandos
  __main__.py  CLI
docs/
  COMANDOS.md       todos os comandos + como observar nas 3 semanas
  PLANO-CLIENTES.md os 12 alvos, sequência de contato, respostas prontas
  PLANO-7-DIAS.md   o que está pronto e o que é você
  OFERTA.md         DMs, oferta, FAQ, cobrança do dia 8
alvos/
  prospects.csv     12 alvos rankeados por sinal de compra
  monitorar.csv     29 URLs verificadas + preço-base de 2026-09-07
  verificacao.csv   saída bruta do teste técnico de cada URL
  COMO-VENDER.md    o ângulo de venda, a DM pronta, a ordem de execução
```

## Custo

R$0 até ter receita: Telegram grátis, Groq/Gemini free tier sem cartão, SQLite,
seu próprio PC. VPS só depois de cliente pagante — não o contrário.
