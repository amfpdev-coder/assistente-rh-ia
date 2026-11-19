import pandas as pd
import pytest

from app.graficos import escolher_grafico


@pytest.mark.parametrize("resultado, esperado", [
    (pd.DataFrame({"headcount": [61]}), "metrica"),
    (pd.DataFrame({"salario_medio": [13835.81]}), "metrica"),
    (pd.DataFrame({"area": ["Comercial", "Atendimento"], "desligamentos": [11, 9]}), "barras"),
    (pd.DataFrame({"mes": pd.to_datetime(["2026-08-01", "2026-09-01"]), "desligamentos": [12, 15]}), "linha"),
    (pd.DataFrame({"area": ["Comercial"], "desligamentos": [11]}), "tabela"),
    (pd.DataFrame({"nivel": ["Pleno"], "genero": ["Feminino"], "pessoas": [40]}), "tabela"),
    (pd.DataFrame({"area": pd.Series([], dtype="object"), "n": pd.Series([], dtype="int64")}), "tabela"),
])
def test_escolher_grafico(resultado, esperado):
    assert escolher_grafico(resultado) == esperado