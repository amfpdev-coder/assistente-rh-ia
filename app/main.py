"""Tela do assistente de RH: pergunta em português -> resposta, gráfico e SQL."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st
from openai import RateLimitError

from app.graficos import escolher_grafico
from app.llm import Resposta, perguntar
from app.seguranca import SQLBloqueado

EXEMPLOS = [
    "Qual área teve mais desligamentos no último trimestre?",
    "Quantas pessoas ativas há em Tecnologia?",
    "Quantos desligamentos houve por mês no último ano?",
    "Qual o salário médio por nível?",
]

@st.cache_data(ttl=3600, show_spinner=False)
def responder(pergunta: str) -> Resposta:
    return perguntar(pergunta)


def usar_exemplo(texto: str) -> None:
    st.session_state.pergunta = texto


def formatar_numero(valor: float) -> str:
    texto = f"{valor:,.0f}" if float(valor).is_integer() else f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def mostrar_grafico(resultado: pd.DataFrame) -> None:
    tipo = escolher_grafico(resultado)
    if tipo == "metrica":
        st.metric(resultado.columns[0], formatar_numero(float(resultado.to_numpy()[0, 0])))
    elif tipo in ("barras", "linha"):
        x = resultado.select_dtypes(exclude="number").columns[0]
        y = resultado.select_dtypes("number").columns[0]
        if tipo == "barras":
            grafico = alt.Chart(resultado).mark_bar().encode(
                x=alt.X(y, title=y, scale=alt.Scale(domainMin=0)),
                y=alt.Y(x, title=None, sort="-x"),
                tooltip=[x, y],
            )
            st.altair_chart(grafico, width="stretch")
        else:
            st.line_chart(resultado, x=x, y=y)


def mostrar_resposta(resposta: Resposta, guardada: bool) -> None:
    st.success(resposta.texto)
    mostrar_grafico(resposta.resultado)
    with st.expander("Ver dados e SQL"):
        st.dataframe(resposta.resultado.round(2), hide_index=True)
        st.code(resposta.sql, language="sql")
    if guardada:
        st.caption(f"Resposta guardada de uma pergunta igual (na primeira vez levou {resposta.segundos:.1f} s).")
    else:
        st.caption(f"Respondido em {resposta.segundos:.1f} s")


st.set_page_config(page_title="Assistente de RH com IA", page_icon="📊")
st.title("📊 Assistente de RH com IA")
st.write(
    "Pergunte em português sobre os dados de RH. A IA gera a consulta SQL, "
    "que roda numa base sem dados pessoais, e responde em uma frase."
)
st.caption("Dados 100% fictícios: 500 colaboradores, de nov/2024 a out/2026.")

st.write("**Exemplos:**")
colunas = st.columns(2)
for i, exemplo in enumerate(EXEMPLOS):
    colunas[i % 2].button(exemplo, on_click=usar_exemplo, args=(exemplo,), width="stretch")

pergunta = st.text_input(
    "Sua pergunta", key="pergunta", placeholder="Ex.: Quantas pessoas saíram do Comercial no último ano?"
)

if st.button("Perguntar", type="primary", disabled=not pergunta.strip()):
    try:
        inicio = time.perf_counter()
        with st.spinner("Consultando os dados..."):
            resposta = responder(pergunta.strip())
        guardada = time.perf_counter() - inicio < 0.5

    except SQLBloqueado:
        st.warning("Essa pergunta gerou um comando que não é de leitura, e ele foi bloqueado. O assistente só consulta dados.")
    except RateLimitError:
        st.error("O limite gratuito da IA foi atingido. Tente de novo em alguns minutos.")
    except Exception:
        st.error("Não consegui responder essa pergunta. Tente reformular.")
    else:
        mostrar_resposta(resposta, guardada)
