"""Pergunta em português -> SQL -> resposta, usando uma API de LLM compatível com OpenAI."""

import os
import re
import sys
import time
from dataclasses import dataclass

import duckdb
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from app.anonimizar import CAMINHO_ANON
from app.seguranca import validar_sql

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
- Perguntas sobre quem está na empresa (headcount, salários, perfil do quadro) consideram só colaboradores.status = 'Ativo', a menos que a pergunta fale de desligados ou de histórico.
- Dê nomes claros às colunas calculadas (por exemplo, AS desligamentos)."""

PROMPT_RESPOSTA = """Você é um assistente de RH. Recebe uma pergunta e o resultado de uma consulta (CSV) e responde em português.

Regras:
- Escreva UMA frase completa, que retome a pergunta e traga a resposta. Nunca responda só com um número.
- Use apenas os números do resultado. Não invente nem calcule valores novos.
- Arredonde: dinheiro como R$ 1.234,56; porcentagens com 1 casa decimal.
- Se o resultado estiver vazio, diga que não há dados para essa pergunta.
- Não mencione SQL, consultas, tabelas ou colunas.

Exemplo:
Pergunta: Quantas pessoas ativas há em RH?
Resultado: headcount
19
Resposta: A área de RH tem 19 pessoas ativas."""

MAX_LINHAS_NA_RESPOSTA = 20


def criar_cliente() -> OpenAI:
    return OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        max_retries=5,
    )


def conectar_anon() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(
        str(CAMINHO_ANON),
        read_only=True,
        config={"enable_external_access": False},
    )


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


def executar_sql(sql: str, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(validar_sql(sql)).df()


def escrever_resposta(pergunta: str, resultado: pd.DataFrame, cliente: OpenAI) -> str:
    tabela = resultado.head(MAX_LINHAS_NA_RESPOSTA).to_csv(index=False)
    resposta = cliente.chat.completions.create(
        model=os.environ["LLM_MODELO"],
        messages=[
            {"role": "system", "content": PROMPT_RESPOSTA},
            {"role": "user", "content": f"Pergunta: {pergunta}\n\nResultado (CSV):\n{tabela}"},
        ],
        reasoning_effort="low",
        temperature=0,
    )
    texto = resposta.choices[0].message.content or ""
    return texto.replace("\u202f", " ").strip()



@dataclass
class Resposta:
    pergunta: str
    sql: str
    resultado: pd.DataFrame
    texto: str
    segundos: float


def perguntar(pergunta: str) -> Resposta:
    inicio = time.perf_counter()
    cliente = criar_cliente()
    with conectar_anon() as con:
        sql = gerar_sql(pergunta, cliente, descrever_esquema(con))
        resultado = executar_sql(sql, con)
    texto = escrever_resposta(pergunta, resultado, cliente)
    return Resposta(pergunta, sql, resultado, texto, round(time.perf_counter() - inicio, 2))


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "Qual área teve mais desligamentos no último trimestre?"
    r = perguntar(pergunta)
    print(f"SQL:\n{r.sql}\n")
    print(r.resultado.head(10).to_string(index=False), "\n")
    print(f"Resposta: {r.texto}")
    print(f"Tempo: {r.segundos}s")
