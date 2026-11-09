"""Garante que só consultas de leitura (um único SELECT) cheguem ao banco."""

import duckdb

class SQLBloqueado(Exception):
    """A consulta não é um SELECT único e foi bloqueada."""


def validar_sql(sql: str) -> str:
    try:
        comandos = duckdb.extract_statements(sql)
    except duckdb.Error as erro:
        raise SQLBloqueado(f"SQL inválido: {erro}") from erro

    if len(comandos) != 1:
        raise SQLBloqueado(f"Esperava 1 comando, recebi {len(comandos)}.")
    if comandos[0].type != duckdb.StatementType.SELECT:
        raise SQLBloqueado(f"Só SELECT é permitido, recebi {comandos[0].type.name}.")
    return sql