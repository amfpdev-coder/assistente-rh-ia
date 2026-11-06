"""Carrega os CSVs de data/brutos no banco DuckDB data/rh.duckdb."""

from pathlib import Path

import duckdb

PASTA_DATA = Path(__file__).parent
PASTA_BRUTOS = PASTA_DATA / "brutos"
CAMINHO_BANCO = PASTA_DATA / "rh.duckdb"

ESQUEMA = """
CREATE TABLE areas (
    id_area   INTEGER PRIMARY KEY,
    nome_area VARCHAR NOT NULL,
    diretoria VARCHAR NOT NULL
);

CREATE TABLE colaboradores (
    id_colaborador  INTEGER PRIMARY KEY,
    nome            VARCHAR NOT NULL,
    cpf             VARCHAR NOT NULL UNIQUE,
    email           VARCHAR NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    genero          VARCHAR NOT NULL,
    id_area         INTEGER NOT NULL REFERENCES areas (id_area),
    cargo           VARCHAR NOT NULL,
    nivel           VARCHAR NOT NULL,
    salario         DECIMAL(10, 2) NOT NULL,
    tipo_contrato   VARCHAR NOT NULL,
    data_admissao   DATE NOT NULL,
    cidade          VARCHAR NOT NULL,
    uf              VARCHAR(2) NOT NULL,
    status          VARCHAR NOT NULL
);

CREATE TABLE desligamentos (
    id_desligamento   INTEGER PRIMARY KEY,
    id_colaborador    INTEGER NOT NULL UNIQUE REFERENCES colaboradores (id_colaborador),
    data_desligamento DATE NOT NULL,
    tipo              VARCHAR NOT NULL,
    motivo            VARCHAR NOT NULL
);
"""


def conectar(somente_leitura: bool = True) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(CAMINHO_BANCO), read_only=somente_leitura)


def carregar() -> None:
    CAMINHO_BANCO.unlink(missing_ok=True)

    with conectar(somente_leitura=False) as con:
        con.execute(ESQUEMA)
        for tabela in ["areas", "colaboradores", "desligamentos"]:
            arquivo = (PASTA_BRUTOS / f"{tabela}.csv").as_posix()
            con.execute(f"INSERT INTO {tabela} BY NAME SELECT * FROM read_csv('{arquivo}', header = true)")

        con.sql("""
            SELECT 'areas' AS tabela, count(*) AS linhas FROM areas
            UNION ALL SELECT 'colaboradores', count(*) FROM colaboradores
            UNION ALL SELECT 'desligamentos', count(*) FROM desligamentos
        """).show()


if __name__ == "__main__":
    carregar()
