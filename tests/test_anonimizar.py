import re

import duckdb
import pytest

from app.anonimizar import CAMINHO_ANON, pseudonimizar

PADRAO_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
PADRAO_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


@pytest.fixture(scope="module")
def con():
    if not CAMINHO_ANON.exists():
        pytest.skip("Rode antes: python -m app.anonimizar")
    with duckdb.connect(str(CAMINHO_ANON), read_only=True) as conexao:
        yield conexao


def textos_da_base(con):
    """Devolve todos os valores de texto de todas as tabelas da base."""
    colunas = con.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE data_type = 'VARCHAR'
    """).fetchall()
    for tabela, coluna in colunas:
        for (valor,) in con.execute(f'SELECT DISTINCT "{coluna}" FROM {tabela}').fetchall():
            if valor is not None:
                yield tabela, coluna, valor


def test_nenhuma_coluna_pessoal(con):
    colunas = {nome for (nome,) in con.execute("SELECT column_name FROM information_schema.columns").fetchall()}
    assert colunas.isdisjoint({"nome", "cpf", "email"})


def test_nenhum_cpf_ou__email_nos_dados(con):
    vazamentos = [
        (tabela, coluna, valor)
        for tabela, coluna, valor in textos_da_base(con)
        if PADRAO_CPF.search(valor) or PADRAO_EMAIL.search(valor)
    ]
    assert vazamentos == [], f"Dados pessoais encontrados: {vazamentos[:5]}"


def test_codigos_unicos(con):
    total, distintos = con.execute(
        "SELECT count(*), count(DISTINCT codigo_colaborador) FROM colaboradores"
    ).fetchone()
    assert total == distintos


def test_pseudonimizacao_depende_da_chave():
    cpf = "123.456.789-09"
    assert pseudonimizar(cpf, b"chave-a") == pseudonimizar(cpf, b"chave-a")
    assert pseudonimizar(cpf, b"chave-a") != pseudonimizar(cpf, b"chave-b")