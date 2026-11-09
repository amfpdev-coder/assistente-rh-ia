# Assistente de RH com IA

Faça perguntas em português sobre dados de RH e receba a resposta, a consulta SQL usada e um gráfico, sem que a IA veja dados pessoais.

> 🚧 Em construção. Prontos: base de dados fictícia, pseudonimização (LGPD) e o assistente no terminal. Próximos: interface web e avaliação de qualidade.

## O problema

Times de RH dependem de alguém técnico para tirar números simples dos dados, como "qual área teve mais desligamentos no último trimestre?".

## Como funciona

1. A pessoa pergunta, por exemplo: "Qual área teve mais desligamentos no último trimestre?"
2. O sistema envia para a IA apenas o esquema das tabelas (nomes, tipos e valores possíveis das colunas), nunca os dados pessoais.
3. A IA devolve uma consulta SQL.
4. Uma checagem bloqueia qualquer comando que não seja um único `SELECT`.
5. O DuckDB roda a consulta na base pseudonimizada.
6. A IA escreve a resposta em uma frase, usando só os números do resultado.

```text
$ python -m app.llm "Qual área teve mais desligamentos no último trimestre?"
Resposta: A área Comercial teve 11 desligamentos.
Tempo: 1.57s
```

### Regras de interpretação

Perguntas de RH costumam ser ambíguas. Duas regras explícitas no prompt resolvem os casos encontrados nos testes:

| Pergunta | Ambiguidade | Regra |
| --- | --- | --- |
| "Último trimestre" | Trimestre do calendário (jul–set) ou últimos 3 meses (ago–out)? A resposta muda: Atendimento ou Comercial | Períodos contam para trás a partir da data de referência dos dados (31/10/2026) |
| "Salário médio de quem é Sênior" | Inclui quem já saiu? Muda de R$ 13.835,81 para R$ 14.050,26 | Perguntas sobre o quadro atual consideram só colaboradores ativos |

## LGPD

O assistente nunca usa dados pessoais. A base que ele consulta (`rh_anon.duckdb`) é gerada a partir da original com três regras:

| Dado | Tratamento | Por quê |
| --- | --- | --- |
| Nome | Trocado por um código (`COL-33c1fa64`) | Permite falar de uma pessoa sem identificá-la |
| CPF | Removido | Nenhuma pergunta de RH precisa dele (princípio da necessidade) |
| E-mail | Removido | Idem |

O código é gerado com **HMAC-SHA256** e uma chave secreta guardada em `.env`, fora do repositório. Um hash simples do CPF não bastaria: existem cerca de 1 bilhão de CPFs possíveis, e todos podem ser testados em minutos. Sem a chave, não há como voltar do código ao CPF.

Por isso, tecnicamente, é uma **pseudonimização**: quem tem a chave consegue refazer o vínculo.

Um teste automático (`tests/test_anonimizar.py`) procura padrões de CPF e e-mail em todas as colunas de texto da base anonimizada e falha se encontrar qualquer um.

## Segurança

O SQL é gerado por uma IA, então o sistema parte do princípio de que ele pode ser malicioso, por exemplo, por *prompt injection* na pergunta. São três camadas, todas cobertas por testes (`tests/test_seguranca.py`):

| Camada | O que bloqueia |
| --- | --- |
| Analisador do próprio DuckDB (`app/seguranca.py`) | Tudo que não for exatamente um `SELECT`: `DROP`, `ATTACH`, `COPY`, `PRAGMA` e vários comandos juntos |
| Conexão somente leitura | Qualquer escrita no banco |
| `enable_external_access = false` | Leitura de arquivos de fora do banco |

A terceira camada existe porque bloquear o que não é `SELECT` não basta: `SELECT * FROM read_text('.env')` é um `SELECT` válido e, sem ela, leria as chaves secretas.

## Stack

Python, pandas, Faker, DuckDB, pytest e uma API de LLM compatível com OpenAI (padrão: Groq, modelo `openai/gpt-oss-120b`). Trocar de provedor é mudar 3 variáveis no `.env`.

## Como rodar localmente

```bash
git clone https://github.com/amfpdev-coder/assistente-rh-ia.git
cd assistente-rh-ia
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Os dados são 100% fictícios, gerados com Faker. Nenhum dado pessoal real é usado, e os arquivos gerados não vão para o repositório.

Crie o arquivo `.env` a partir do `.env.example`, gere a chave de pseudonimização e coloque a chave da API do Groq (grátis em [console.groq.com](https://console.groq.com)):

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # cole o resultado no .env
```

Gere os dados e rode os testes:

```bash
python data/gerar_dados.py          # dados fictícios em data/brutos/
python data/carregar_duckdb.py      # banco original: data/rh.duckdb
python -m app.anonimizar            # banco pseudonimizado: data/rh_anon.duckdb
pytest -v
```

Faça uma pergunta:

```bash
python -m app.llm "Quantas pessoas ativas há em Tecnologia?"
```
