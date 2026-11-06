"""Gera dados fictícios de RH: áreas, colaboradores e desligamentos."""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEMENTE = 42
INICIO = date(2024, 11, 1)
FIM = date(2026, 10, 31)
PASTA_SAIDA = Path(__file__).parent / "brutos"

fake = Faker("pt_BR")
Faker.seed(SEMENTE)
random.seed(SEMENTE)


# peso: fatia do quadro de funcionários (a soma dá 1)
# rotatividade: chance de uma pessoa sair em um ano
# fator_salario: multiplica o salário base do nível
AREAS = [
    {"nome": "Tecnologia", "diretoria": "Produto e Tecnologia", "peso": 0.18, "rotatividade": 0.15, "fator_salario": 1.40},
    {"nome": "Comercial", "diretoria": "Receita", "peso": 0.15, "rotatividade": 0.35, "fator_salario": 1.00},
    {"nome": "Atendimento", "diretoria": "Operações", "peso": 0.22, "rotatividade": 0.45, "fator_salario": 0.75},
    {"nome": "Operações", "diretoria": "Operações", "peso": 0.14, "rotatividade": 0.25, "fator_salario": 0.90},
    {"nome": "Financeiro", "diretoria": "Corporativo", "peso": 0.08, "rotatividade": 0.10, "fator_salario": 1.15},
    {"nome": "Marketing", "diretoria": "Receita", "peso": 0.09, "rotatividade": 0.22, "fator_salario": 1.05},
    {"nome": "RH", "diretoria": "Corporativo", "peso": 0.07, "rotatividade": 0.15, "fator_salario": 0.95},
    {"nome": "Jurídico", "diretoria": "Corporativo", "peso": 0.07, "rotatividade": 0.08, "fator_salario": 1.25},
]

TOTAL_COLABORADORES = 500
FATIA_JA_CONTRATADOS = 0.6  # parte do quadro que já estava na empresa em INICIO

NIVEIS = {  # nível: (peso, salário base)
    "Estágio": (0.08, 1_800),
    "Júnior": (0.30, 3_800),
    "Pleno": (0.32, 6_500),
    "Sênior": (0.20, 10_000),
    "Gestão": (0.10, 16_000),
}

FUNCOES = {
    "Tecnologia": ["Desenvolvedor(a)", "Analista de Dados"],
    "Comercial": ["Executivo(a) de Vendas", "Analista Comercial"],
    "Atendimento": ["Analista de Atendimento", "Especialista de Suporte"],
    "Operações": ["Analista de Operações", "Analista de Processos"],
    "Financeiro": ["Analista Financeiro", "Analista Contábil"],
    "Marketing": ["Analista de Marketing", "Designer"],
    "RH": ["Analista de RH", "Business Partner de RH"],
    "Jurídico": ["Advogado(a)", "Analista Jurídico"],
}

CIDADES = [  # (cidade, UF, peso)
    ("São Paulo", "SP", 0.45),
    ("Campinas", "SP", 0.08),
    ("Rio de Janeiro", "RJ", 0.12),
    ("Belo Horizonte", "MG", 0.10),
    ("Curitiba", "PR", 0.08),
    ("Porto Alegre", "RS", 0.06),
    ("Recife", "PE", 0.06),
    ("João Pessoa", "PB", 0.05),
    ("Florianópolis", "SC", 0.05),
]

MOTIVOS = {
    "Voluntário": ["Nova oportunidade", "Salário", "Mudança de cidade", "Insatisfação com a liderança", "Motivos pessoais"],
    "Involuntário": ["Baixo desempenho", "Reestruturação", "Corte de custos", "Conduta"],
}
CHANCE_VOLUNTARIO = 0.6


def data_aleatoria(inicio: date, fim: date) -> date:
    dias = (fim - inicio).days
    return inicio + timedelta(days=random.randint(0, dias))


def sortear_admissao() -> date:
    if random.random() < FATIA_JA_CONTRATADOS:
        # quanto mais antiga a data, menos gente contratada nela continua na empresa
        dias = (INICIO - date(2016, 1, 1)).days
        return INICIO - timedelta(days=int(random.triangular(1, dias, 1)))
    return data_aleatoria(INICIO, FIM)


def montar_cargo(area: str, nivel: str) -> str:
    if nivel == "Estágio":
        return f"Estagiário(a) de {area}"
    if nivel == "Gestão":
        return f"Coordenador(a) de {area}"
    return f"{random.choice(FUNCOES[area])} {nivel}"


def sortear_contrato(area: str, nivel: str) -> str:
    if nivel == "Estágio":
        return "Estágio"
    chance_pj = 0.30 if area == "Tecnologia" else 0.05
    return "PJ" if random.random() < chance_pj else "CLT"


def sortear_desligamento(admissao: date, rotatividade: float) -> date | None:
    chance_mensal = 1 - (1 - rotatividade) ** (1 / 12)
    dia = max(admissao, INICIO)
    while dia <= FIM:
        meses_de_casa = (dia - admissao).days / 30
        chance = chance_mensal * 2 if meses_de_casa < 12 else chance_mensal
        if random.random() < chance:
            return min(dia + timedelta(days=random.randint(1, 30)), FIM)
        dia += timedelta(days=30)
    return None


def gerar_areas() -> pd.DataFrame:
    linhas = [
        {"id_area": i, "nome_area": area["nome"], "diretoria": area["diretoria"]}
        for i, area in enumerate(AREAS, start=1)
    ]
    return pd.DataFrame(linhas)


def gerar_colaboradores() -> pd.DataFrame:
    linhas = []
    for _ in range(TOTAL_COLABORADORES):
        area = random.choices(AREAS, weights=[a["peso"] for a in AREAS])[0]
        nivel = random.choices(list(NIVEIS), weights=[peso for peso, _ in NIVEIS.values()])[0]
        salario = NIVEIS[nivel][1] * area["fator_salario"] * random.uniform(0.85, 1.15)

        genero = random.choice(["Feminino", "Masculino"])
        primeiro_nome = fake.first_name_female() if genero == "Feminino" else fake.first_name_male()

        admissao = sortear_admissao()
        idade_na_admissao = random.randint(18, 23) if nivel == "Estágio" else random.randint(22, 55)
        nascimento = admissao - timedelta(days=idade_na_admissao * 365 + random.randint(0, 364))

        cidade, uf, _ = random.choices(CIDADES, weights=[c[2] for c in CIDADES])[0]

        linhas.append({
            "nome": f"{primeiro_nome} {fake.last_name()} {fake.last_name()}",
            "cpf": fake.unique.cpf(),
            "email": fake.unique.email(),
            "data_nascimento": nascimento,
            "genero": genero,
            "id_area": AREAS.index(area) + 1,
            "cargo": montar_cargo(area["nome"], nivel),
            "nivel": nivel,
            "salario": round(salario, 2),
            "tipo_contrato": sortear_contrato(area["nome"], nivel),
            "data_admissao": admissao,
            "cidade": cidade,
            "uf": uf,
        })

    colaboradores = pd.DataFrame(linhas).sort_values("data_admissao", ignore_index=True)
    colaboradores.insert(0, "id_colaborador", range(1, len(colaboradores) + 1))
    return colaboradores


def gerar_desligamentos(colaboradores: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for id_colaborador, id_area, admissao in zip(
        colaboradores["id_colaborador"], colaboradores["id_area"], colaboradores["data_admissao"]
    ):
        area = AREAS[id_area - 1]
        data = sortear_desligamento(admissao, area["rotatividade"])
        if data is None:
            continue
        tipo = "Voluntário" if random.random() < CHANCE_VOLUNTARIO else "Involuntário"
        linhas.append({
            "id_colaborador": id_colaborador,
            "data_desligamento": data,
            "tipo": tipo,
            "motivo": random.choice(MOTIVOS[tipo]),
        })

    desligamentos = pd.DataFrame(linhas).sort_values("data_desligamento", ignore_index=True)
    desligamentos.insert(0, "id_desligamento", range(1, len(desligamentos) + 1))
    return desligamentos


if __name__ == "__main__":
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    areas = gerar_areas()
    colaboradores = gerar_colaboradores()
    desligamentos = gerar_desligamentos(colaboradores)

    saiu = colaboradores["id_colaborador"].isin(desligamentos["id_colaborador"])
    colaboradores["status"] = saiu.map({True: "Desligado", False: "Ativo"})

    areas.to_csv(PASTA_SAIDA / "areas.csv", index=False)
    colaboradores.to_csv(PASTA_SAIDA / "colaboradores.csv", index=False)
    desligamentos.to_csv(PASTA_SAIDA / "desligamentos.csv", index=False)

    print(f"{len(colaboradores)} colaboradores, {len(desligamentos)} desligamentos")
    print(colaboradores["status"].value_counts())
