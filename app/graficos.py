"""Escolhe como mostrar o resultado de uma consulta na tela."""

import pandas as pd

def escolher_grafico(resultado: pd.DataFrame) -> str:
    numericas = resultado.select_dtypes("number").columns
    datas = resultado.select_dtypes("datetime").columns
    textos = resultado.select_dtypes(["object", "string"]).columns

    if resultado.shape == (1, 1) and len(numericas) == 1:
        return "metrica"
    if resultado.shape[1] == 2 and len(numericas) == 1:
        if len(datas) == 1:
            return "linha"
        if len(textos) == 1 and len(resultado) >= 2:
            return "barras"
    return "tabela"
