import pytest

from data.gerar_dados import (
    FIM,
    INICIO,
    gerar_areas,
    gerar_colaboradores,
    gerar_desligamentos,
    marcar_status,
)

@pytest.fixture(scope="module")
def dados():
    areas = gerar_areas()
    colaboradores = gerar_colaboradores()
    desligamentos = gerar_desligamentos(colaboradores)
    colaboradores = marcar_status(colaboradores, desligamentos)
    return areas, colaboradores, desligamentos


def test_quantidades(dados):
    areas, colaboradores, desligamentos = dados
    assert len(areas) == 8
    assert len(colaboradores) == 500
    assert 150 <= len (desligamentos) <= 250


def test_chaves_estrangeiras(dados):
    areas, colaboradores, desligamentos = dados
    assert colaboradores["id_area"].isin(areas["id_area"]).all()
    assert desligamentos["id_colaborador"].isin(colaboradores["id_colaborador"]).all()


def test_desligamento_depois_da_admissao_e_dentro_do_periodo(dados):
    _, colaboradores, desligamentos = dados
    juntos = desligamentos.merge(colaboradores, on="id_colaborador")
    assert (juntos["data_desligamento"] > juntos["data_admissao"]).all()
    assert juntos["data_desligamento"].between(INICIO, FIM).all()


def test_status_coerente_com_desligamentos(dados):
    _, colaboradores, desligamentos = dados
    desligado = colaboradores["status"] == "Desligado"
    tem_desligamento = colaboradores["id_colaborador"].isin(desligamentos["id_colaborador"])
    assert (desligado == tem_desligamento).all()


def test_ninguem_desligado_duas_vezes(dados):
    _, _, desligamentos = dados
    assert desligamentos["id_colaborador"].is_unique


def test_cpf_e_email_unicos(dados):
    _, colaboradores, _ = dados
    assert colaboradores["cpf"].is_unique
    assert colaboradores["email"].is_unique

