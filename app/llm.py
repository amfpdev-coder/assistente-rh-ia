"""Pergunta em português -> SQL -> resposta, usando uma API de LLM compatível com OpenAI."""

import os
import re

import duckdb
from dotenv import load_dotenv
from openai import OpenAI

from app.anonimizar import CAMINHO_ANON

load_dotenv()

DATA_REFERENCIA = "2026-10-31" # último dia dos dados fictícios
MAX_VALORES_LISTADOS = 12

PROMPT_SQL = """Você escreve consultas SQL para um banco DuckDB de RH.

Esquema (tabela.coluna tipo):
{esquema}

Relacionamentos:
- colaboradores.id_area = areas.id_area
- desligamentos.id_colaborador = colaboradores.id_colaborador

Regras:
- Responda apenas com UMA consulta SELECT, sem explicações e sem blocos de código.
- Use somente as tabelas, colunas e valores do esquema.
- Os dados vão até {data_referencia}. Use DATE '{data_referencia}' como "hoje", nunca current_date.
- Períodos relativos contam para trás a partir de hoje, em meses completos: "último mês" = outubro/2026, "último trimestre" = agosto a outubro/2026, "último ano" = novembro/2025 a outubro/2026.
- Dê nomes claros às colunas calculadas (por exemplo, AS desligamentos)."""


def criar_cliente() -> OpenAI:
    return OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        max_retries=5,
    )


def conectar_anon() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(CAMINHO_ANON), read_only=True)


def limpar_sql(texto: str) -> str:
    texto = re.sub(r"^```(?:sql)?|```$", "", texto.strip(), flags=re.IGNORECASE | re.MULTILINE)
    return texto.strip().rstrip(";")


def gerar_sql(pergunta: str, cliente: OpenAI, esquema: str) -> str:
    resposta = cliente.chat.completions.create(
        model=os.environ["LLM_MODELO"],
        messages=[
            {"role": "system", "content": PROMPT_SQL.format(esquema=esquema, data_referencia=DATA_REFERENCIA)},
            {"role": "user", "content": pergunta},
        ],
        reasoning_effort="low",
        temperature=0,
    )
    return limpar_sql(resposta.choices[0].message.content or "")


def descrever_esquema(con: duckdb.DuckDBPyConnection) -> str:
    colunas = con.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        ORDER BY table_name, ordinal_position
    """).fetchall()

    linhas = []
    for tabela, coluna, tipo in colunas:
        linha = f"{tabela}.{coluna} {tipo}"
        if tipo == "VARCHAR":
            valores = [
                valor
                for (valor,) in con.execute(
                    f'SELECT DISTINCT "{coluna}" FROM {tabela} ORDER BY 1 LIMIT {MAX_VALORES_LISTADOS + 1}'
                ).fetchall()
            ]
            if len(valores) <= MAX_VALORES_LISTADOS:
                linha += " -- valores: " + ", ".join(valores)
        linhas.append(linha)
    return "\n".join(linhas)