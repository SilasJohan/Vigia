# Comandos

Todos rodam de `D:\Vigia\Vigia`. Nada aqui gasta dinheiro.

## Os 4 que você vai usar sempre

| Comando | O que faz |
|---|---|
| `python -m vigia check` | Uma rodada: lê as páginas vencidas, compara, alerta se mudou. É o coração. |
| `python -m vigia mercado` | **O juiz.** O mercado se move? Quantas mudanças, em quais páginas, em quantos dias. |
| `python -m vigia dossie <nome>` | Tudo sobre uma página: desde quando observa, quantas leituras, cada mudança com antes/depois, e a frase pronta para citar. |
| `python -m vigia stats` | Métricas gerais + taxa de lixo (seu critério de morte: <30%). |

## Configuração (uma vez só)

| Comando | O que faz |
|---|---|
| `python -m vigia whoami` | Descobre seu `chat_id`. Espera 60s você mandar `/start` no bot. |
| `python -m vigia doctor` | Diagnóstico: Telegram responde? Qual IA está ativa? Playwright instalado? Quantos watches? **Rode isso primeiro sempre que algo parecer quebrado.** |
| `python -m vigia carregar alvos/monitorar.csv` | Carrega em lote as 29 URLs verificadas. `--cluster uptime` carrega só um grupo. |

## Gerenciar páginas

| Comando | O que faz |
|---|---|
| `python -m vigia list` | Lista tudo: id, modo, estado (ok/erro/off), URL. |
| `python -m vigia add <url> --label Nome` | Adiciona uma página. `--mode product` para produto de loja, `--css ".tabela-precos"` para recortar só um pedaço. |
| `python -m vigia rebase` | **Descarta a base e força releitura limpa.** Use ao mudar `--mode`, `--css`, ou quando eu mudar o extrator. Sem isso, a próxima checagem compara formatos diferentes e reporta a página inteira como alterada. `--label Bling` para uma só. |

## Rodar continuamente

| Comando | O que faz |
|---|---|
| `python -m vigia check --force` | Ignora o intervalo de 6h e lê tudo agora. Para testar. |
| `python -m vigia check --loop 60` | Fica rodando, checando a cada 60 min quem venceu. Deixe numa janela. |
| `python -m vigia check --quiet-telegram` | Roda sem mandar alerta. Para experimentar sem se auto-spammar. |
| `python -m vigia bot` | Liga o bot para o cliente se servir sozinho (colar URL, `/list`, `/stop`). **Só quando tiver cliente** — enquanto isso ele só consome as mensagens e atrapalha o `whoami`. |

## Vendas

| Comando | O que faz |
|---|---|
| `python -m vigia dossie <nome>` | A evidência de uma página, com frase pronta em PT e EN. |
| `python -m vigia brief <domínio> --days 3` | Rascunho de DM a partir das mudanças dos últimos N dias. |
| `python -m vigia trials` | Quem está no teste grátis e quantos dias faltam. Marca quem vence hoje. |

## Teste

| Comando | O que faz |
|---|---|
| `python -m vigia demo` | Muda um HTML local de propósito e manda o alerta no seu Telegram. Prova que o pipeline inteiro funciona. |
| `python tests/test_filtro.py` | 10 testes do filtro de ruído. Rode depois de qualquer mexida no extrator. |

## No bot (Telegram)

| Comando | O que faz |
|---|---|
| colar uma URL | Começa a monitorar |
| `/list` `/stop <id>` | Ver e parar |
| `/mode pricing\|product\|page` | Muda o que conta como relevante |
| `/agora` | Checa na hora |
| `/texto_<n>` | **O trecho bruto do alerta `<n>`.** Use quando o resumo não convencer. |
| `/lixo_<n>` | Marca o alerta como inútil. Isso alimenta a taxa de lixo. |
| `/stats` `/pagou <chat> <plano>` | Só para você (admin) |

---

# Como observar nas próximas 3 semanas

Sim, é só observar — **mas observar não é esperar.** São 10 minutos por dia.

## O que o sistema já anota (não anote à mão)

O banco já guarda, por página: desde quando observa, quantas leituras, cada mudança com data, seção, antes/depois, categoria, e o seu feedback de lixo. `dossie` cospe tudo isso formatado.

Reescrever isso num caderno é refazer trabalho e introduzir erro. **Não anote mudanças à mão.**

## O que só você pode anotar (`alvos/contatos.csv`)

- Contato achado, e de quem é o cargo certo.
- A **frase exata** de quem responder.
- Sua leitura: "esse alvo tem 3 páginas /vs/, vale mais que os outros".

## Rotina diária — 10 minutos

1. Chegou alerta? Abra e faça **uma** pergunta: *eu conseguiria mandar isso para alguém sem passar vergonha?*
   - Sim → não faça nada. Já está no banco.
   - Não → `/lixo_<n>`. Isso é trabalho de verdade: você está calibrando o filtro.
2. Se o alerta tiver ⚠️ ("o valor continua na página"), **abra a página e confirme**. Esse é o hábito que separa você de um robô de spam.
3. Uma vez por semana: `python -m vigia mercado` e anote o número no seu caderno. Só o número.

## O que faz a mensagem não parecer venda

Você perguntou o essencial: como não ser mais um e-mail tentando vender. Três coisas, em ordem de importância:

**1. A primeira frase tem que ser sobre ele, com um dado que ele pode conferir.**
Não "eu criei uma ferramenta". E sim: *"sua página /vs/tally diz que o Tally cobra $29; hoje a página deles diz $24."* Ele abre, confere, e a partir daí você não é vendedor, é alguém que notou algo.

**2. Precisão vale mais que volume.** Um fato exato ("no dia 12, na seção Planos, o Starter saiu de $15 para $12") prova sistema. Cinco fatos vagos provam que você é um raspador de sites. Por isso o alerta agora diz seção, trecho e vizinhança — e por isso existe o ⚠️.

**3. Diga o que você NÃO sabe.** *"Saiu do banner do topo; as ofertas por plano continuam lá — não sei se é fim da promoção ou só rotação de banner."* Isso é o oposto de vendedor, e é o que faz um fundador responder.

## As duas coisas a fazer além de observar

**Fase 1 do plano: achar os contatos** (`alvos/contatos.csv`). Não depende de dados, faça agora, 20 min por dia.

**A auditoria.** Não precisa esperar mudança: abra a página `/vs/` de cada alvo, anote os preços de concorrente que ela cita, e compare com o preço real de hoje (`dossie` do concorrente). Se estiver errado, você já tem a DM inteira. Isso vale mais que as 3 semanas de espera.

## Quando parar de observar e mandar

Quando `mercado` mostrar **4+ páginas diferentes** que se moveram, ou quando uma auditoria achar um preço errado numa página `/vs/`. O que vier primeiro.
