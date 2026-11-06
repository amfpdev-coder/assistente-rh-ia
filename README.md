# Assistente de RH com IA

Faça perguntas em português sobre dados de RH e receba a resposta, a consulta SQL usada e um gráfico, sem que a IA veja dados pessoais.

> 🚧 Em construção. Etapa atual: base de dados fictícia.

## O problema

Times de RH dependem de alguém técnico para tirar números simples dos dados, como "qual área teve mais desligamentos no último trimestre?".

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
