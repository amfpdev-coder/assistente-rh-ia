# Assistente de RH com IA

Faça perguntas em português sobre dados de RH e receba a resposta, a consulta SQL usada e um gráfico, sem que a IA veja dados pessoais.

> 🚧 Em construção. Etapa atual: base de dados fictícia e pseudonimização (LGPD).

## O problema

Times de RH dependem de alguém técnico para tirar números simples dos dados, como "qual área teve mais desligamentos no último trimestre?".

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

## Stack

Python, pandas, Faker, DuckDB, pytest, Streamlit e uma API de LLM.

## Como rodar localmente

```bash
git clone https://github.com/amfpdev-coder/assistente-rh-ia.git
cd assistente-rh-ia
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Os dados são 100% fictícios, gerados com Faker. Nenhum dado pessoal real é usado, e os arquivos gerados não vão para o repositório.

Crie o arquivo `.env` a partir do `.env.example` e gere a chave:

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
