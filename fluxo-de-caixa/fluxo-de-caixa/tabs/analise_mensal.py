import pandas as pd
import streamlit as st

from config import COL_V, format_brl


def render(df, df_rec, meses_sel: list):
    label = ", ".join(meses_sel) if meses_sel else "Geral"
    st.markdown(f"### Análise Financeira: {label}")

    v_ent = df_rec[COL_V].sum()
    v_sai = abs(df[df[COL_V] < 0][COL_V].sum())
    resultado = v_ent - v_sai
    cor = "#FF4B4B" if resultado < 0 else "#00D1FF"

    col1, col2 = st.columns(2)
    col1.metric("Entrou no Período", format_brl(v_ent))
    col2.metric("Saiu no Período", format_brl(v_sai))

    st.markdown("#### Saldo Líquido")
    st.markdown(f"<h2 style='color: {cor};'>{format_brl(resultado)}</h2>", unsafe_allow_html=True)

    chart_df = pd.DataFrame({'Valores': [v_ent, v_sai], 'Tipo': ['Entradas', 'Saídas']}).set_index('Tipo')
    st.bar_chart(chart_df, color="#00D1FF")
