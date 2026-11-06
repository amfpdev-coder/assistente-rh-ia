-- 1. Headcount ativo por área
SELECT a.nome_area, count(*) AS headcount
FROM colaboradores c
JOIN areas a ON a.id_area = c.id_area
WHERE c.status = 'Ativo'
GROUP BY a.nome_area
ORDER BY headcount DESC;

-- 2. Desligamentos por área no último trimestre (ago–out/2026)
SELECT a.nome_area, count(*) AS desligamentos
FROM desligamentos d
JOIN colaboradores c ON c.id_colaborador = d.id_colaborador
JOIN areas a ON a.id_area = c.id_area
WHERE d.data_desligamento BETWEEN DATE '2026-08-01' AND DATE '2026-10-31'
GROUP BY a.nome_area
ORDER BY desligamentos DESC;

-- 3. Taxa de rotatividade anual por área (nov/2025 a out/2026)
-- rotatividade = desligamentos no período ÷ headcount médio (início + fim) ÷ 2
WITH base AS (
    SELECT c.id_area, c.data_admissao, d.data_desligamento
    FROM colaboradores c
    LEFT JOIN desligamentos d ON d.id_colaborador = c.id_colaborador
),
por_area AS (
    SELECT
        id_area,
        count(*) FILTER (WHERE data_desligamento BETWEEN DATE '2025-11-01' AND DATE '2026-10-31') AS desligamentos,
        count(*) FILTER (WHERE data_admissao <= DATE '2025-11-01'
                        AND (data_desligamento IS NULL OR data_desligamento > DATE '2025-11-01')) AS headcount_inicio,
        count(*) FILTER (WHERE data_admissao <= DATE '2026-10-31'
                        AND (data_desligamento IS NULL OR data_desligamento > DATE '2026-10-31')) AS headcount_fim
    FROM base
    GROUP BY id_area
)
SELECT
    a.nome_area,
    p.desligamentos,
    p.headcount_inicio,
    p.headcount_fim,
    round(100.0 * p.desligamentos / ((p.headcount_inicio + p.headcount_fim) / 2.0), 1) AS rotatividade_pct
FROM por_area p
JOIN areas a ON a.id_area = p.id_area
ORDER BY rotatividade_pct DESC;

-- 4. Salário médio por área e nível (colaboradores ativos)
SELECT a.nome_area, c.nivel, count(*) AS pessoas, round(avg(c.salario), 2) AS salario_medio
FROM colaboradores c
JOIN areas a ON a.id_area = c.id_area
WHERE c.status = 'Ativo'
GROUP BY a.nome_area, c.nivel
ORDER BY a.nome_area, salario_medio;

-- 5. Tempo médio de casa (em meses) dos desligados: voluntários vs. involuntários
SELECT
    d.tipo,
    count(*) AS desligamentos,
    round(avg(date_diff('month', c.data_admissao, d.data_desligamento)), 1) AS meses_de_casa_medio
FROM desligamentos d
JOIN colaboradores c ON c.id_colaborador = d.id_colaborador
GROUP BY d.tipo
ORDER BY meses_de_casa_medio;
