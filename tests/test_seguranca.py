import pytest

from app.llm import conectar_anon
from app.seguranca import SQLBloqueado, validar_sql


@pytest.mark.parametrize("sql", [
    "SELECT count(*) FROM colaboradores",
    "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
])
def test_aceita_select(sql):
    assert validar_sql(sql) == sql


@pytest.mark.parametrize("sql", [
    "DROP TABLE areas",
    "DELETE FROM colaboradores",
    "SELECT 1; DROP TABLE areas",
    "ATTACH 'data/rh.duckdb' AS original",
    "COPY colaboradores TO 'vazamento.csv'",
    "PRAGMA database_list",
    "",
    "SELEC isso nem é SQL",
])
def test_bloqueia_o_que_nao_e_select(sql):
    with pytest.raises(SQLBloqueado):
        validar_sql(sql)

@pytest.mark.parametrize("sql", [
    "SELECT * FROM read_text('.env')",
    "SELECT * FROM read_csv('data/brutos/colaboradores.csv')",
])
def test_select_nao_le_arquivos_de_fora(sql):
    validar_sql(sql)  # passa na camada 1: é um SELECT...
    with conectar_anon() as con, pytest.raises(Exception, match="Permission"):
        con.execute(sql)  # ...mas a camada 3 bloqueia