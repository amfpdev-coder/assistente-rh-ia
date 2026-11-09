"""Cria a base pseudonimizada data/rh_anon.duckdb a partir de data/rh.duckdb."""

import hashlib
import hmac
import os

import duckdb
import pandas as pd
from dotenv import load_dotenv

from data.carregar_duckdb import CAMINHO_BANCO, PASTA_DATA

load_dotenv()

CAMINHO_ANON = PASTA_DATA / "rh_anon.duckdb"


def carregar_chave() -> bytes:
    chave = os.getenv("CHAVE_PSEUDONIMIZACAO")
    if not chave:
        raise RuntimeError("Defina CHAVE_PSEUDONIMIZACAO no arquivo .env (veja o .env.example).")
    return chave.encode()


def pseudonimizar(valor: str, chave: bytes) -> str:
    codigo = hmac.new(chave, valor.encode(), hashlib.sha256).hexdigest()
    return f"COL-{codigo[:8]}"


def gerar_base_anonimizada() -> None:
    chave = carregar_chave()
    CAMINHO_ANON.unlink(missing_ok=True)

    with duckdb.connect(str(CAMINHO_ANON)) as con:
        con.execute(f"ATTACH '{CAMINHO_BANCO.as_posix()}' AS origem (READ_ONLY)")

        cpfs = con.sql("SELECT id_colaborador, cpf FROM origem.colaboradores").df()
        codigos = pd.DataFrame({
            "id_colaborador": cpfs["id_colaborador"],
            "codigo_colaborador": [pseudonimizar(cpf, chave) for cpf in cpfs["cpf"]],
        })
        con.register("codigos", codigos)

        con.execute("CREATE TABLE areas AS SELECT * FROM origem.areas")
        con.execute("""
            CREATE TABLE colaboradores AS
            SELECT c.id_colaborador, k.codigo_colaborador, c.* EXCLUDE (id_colaborador, nome, cpf, email)
            FROM origem.colaboradores c
            JOIN codigos k ON k.id_colaborador = c.id_colaborador
            ORDER BY c.id_colaborador
        """)
        con.execute("CREATE TABLE desligamentos AS SELECT * FROM origem.desligamentos")
        con.execute("DETACH origem")

        con.sql("SELECT * FROM colaboradores LIMIT 3").show()


if __name__ == "__main__":
    gerar_base_anonimizada()
