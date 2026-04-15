import pandas as pd
import streamlit as st

st.set_page_config(page_title="CASH FLOW | AP", layout="wide", initial_sidebar_state="expanded")

from auth import check_password

if not check_password():
    st.stop()

# Importações após autenticação
import io  # noqa: E402
from config import COL_V, CSS, format_brl
from data import load_and_process
from pdf_report import gerar_pdf_perfeito
from tabs import (
    analise_mensal,
    apresentacao,
    cash_burn,
    contas_pagar,
    dados,
    departamentos,
    lucratividade,
    pareto,
    pareto_nomes,
    recebidos,
    storytelling,
)

st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color: #00D1FF;'>💎 DASHBOARD</h2>", unsafe_allow_html=True)

    empresas_selecionadas = st.multiselect(
        "🏢 Empresa(s):", options=["Globus", "MGL"], default=["Globus", "MGL"]
    )
    if not empresas_selecionadas:
        st.stop()

    somar_contas_pagar = st.checkbox("Somar Contas a Pagar ao Cash Out?", value=False)

    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.write("---")

    df_raw, df_rec_raw, df_cp_raw, df_depara_raw = load_and_process(tuple(empresas_selecionadas))

    if somar_contas_pagar:
        df_cp_temp = df_cp_raw.copy()
        df_cp_temp[COL_V] = df_cp_temp[COL_V].apply(lambda x: -abs(x))
        df_raw = pd.concat([df_raw, df_cp_temp], ignore_index=True)

    lista_meses = sorted(
        set(df_raw['Mes_Ano'].unique()) | set(df_rec_raw['Mes_Ano'].unique()),
        key=lambda x: pd.to_datetime(x, format='%m/%Y'),
    )
    default_mes = [lista_meses[-1]] if lista_meses else []
    meses_sel = st.multiselect("📅 Períodos:", options=lista_meses, default=default_mes)

    grupos_disponiveis = sorted(df_raw['Grupo_Filtro'].unique())
    grupos_sel = st.multiselect(
        "📂 Grupos:",
        options=grupos_disponiveis,
        default=[g for g in grupos_disponiveis if g != "Outros"],
    )

    cats_disponiveis = sorted(df_raw[df_raw['Grupo_Filtro'].isin(grupos_sel)]['Categoria'].unique())
    cats_sel = st.multiselect("🏷️ Categorias:", options=cats_disponiveis, default=cats_disponiveis)

    st.write("---")
    st.markdown("### 📄 Exportação")
    if meses_sel:
        df_pdf_sai = df_raw[(df_raw['Mes_Ano'].isin(meses_sel)) & (df_raw[COL_V] < 0)]
        df_pdf_rec = df_rec_raw[df_rec_raw['Mes_Ano'].isin(meses_sel)]
        pdf_data = gerar_pdf_perfeito(df_pdf_sai, df_pdf_rec, meses_sel, empresas_selecionadas)
        st.download_button(
            label="📥 Baixar Relatório Full Storytelling (PDF)",
            data=pdf_data,
            file_name="Relatorio_Financeiro_Completo.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# FILTROS APLICADOS (LÓGICA GLOBAL)
# ---------------------------------------------------------------------------
df = df_raw.copy()
if meses_sel:
    df = df[df['Mes_Ano'].isin(meses_sel)]
if grupos_sel:
    df = df[df['Grupo_Filtro'].isin(grupos_sel)]
if cats_sel:
    df = df[df['Categoria'].isin(cats_sel)]

df_rec = df_rec_raw.copy()
if meses_sel:
    df_rec = df_rec[df_rec['Mes_Ano'].isin(meses_sel)]

saidas_df = df[df[COL_V] < 0]

# Filtro específico para Contas a Pagar (respeitando meses e empresas)
df_cp_f = df_cp_raw[df_cp_raw['Mes_Ano'].isin(meses_sel)] if meses_sel else df_cp_raw

# ---------------------------------------------------------------------------
# HEADER PRINCIPAL
# ---------------------------------------------------------------------------
try:
    st.image("avaliacoes_salvas/logo_maldivas.png", width=300)
except Exception:
    pass

st.title("💸 Cash Flow | Expenses and Receipts")

total_cash_in = df_rec[COL_V].sum()
st.markdown(
    f"<div style='background: rgba(0,209,255,0.1); padding: 20px; border-radius: 15px; "
    f"border: 1px solid #00D1FF;'>"
    f"<p style='color: #00D1FF; margin: 0; font-weight: bold;'>💰 TOTAL CASH IN (ENTRADAS)</p>"
    f"<h2 style='color: #00D1FF; margin: 0;'>{format_brl(total_cash_in)}</h2></div>",
    unsafe_allow_html=True,
)
st.write("")

# Métricas de saída por grupo
total_saidas = saidas_df[COL_V].sum()
cols_m = st.columns(len(grupos_sel) + 1)
cols_m[0].metric("CASH OUT TOTAL", format_brl(abs(total_saidas)))
for i, grupo in enumerate(grupos_sel):
    val = df[(df['Grupo_Filtro'] == grupo) & (df[COL_V] < 0)][COL_V].sum()
    cols_m[i + 1].metric(grupo.upper(), format_brl(abs(val)))

st.write("")

# Métricas de contas a pagar baseadas no dataframe filtrado df_cp_f
val_cp_total = df_cp_f[COL_V].sum()
agrupado_cp = df_cp_f.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index()

cols_cp = st.columns(len(agrupado_cp) + 1)
cols_cp[0].metric("CONTAS A PAGAR (TOTAL)", format_brl(abs(val_cp_total)))
for idx, row in agrupado_cp.iterrows():
    cols_cp[idx + 1].metric(f"CP: {row['Grupo_Filtro'].upper()}", format_brl(row[COL_V]))

st.write("---")

# ---------------------------------------------------------------------------
# ABAS - COMUNICANDO OS FILTROS
# ---------------------------------------------------------------------------
(
    tab1, tab2, tab3, tab4, tab5,
    tab6, tab7, tab8, tab9, tab10, tab11,
) = st.tabs([
    "📊 APRESENTAÇÃO", "🔥 CASH BURN", "🎯 PARETO", "📋 DADOS", "💰 RECEBIDOS",
    "📈 ANÁLISE MENSAL", "💎 LUCRATIVIDADE", "🔍 PARETO NOMES",
    "📑 CONTAS A PAGAR", "🏢 DEPARTAMENTOS GLOBUS", "🧠 STORYTELLING",
])

with tab1:
    # Passamos o df filtrado se a função 'apresentacao' suportar, 
    # caso contrário, ela usará a lógica interna baseada nas empresas.
    apresentacao.render(empresas_selecionadas, somar_contas_pagar)
with tab2:
    cash_burn.render(saidas_df)
with tab3:
    pareto.render(saidas_df)
with tab4:
    dados.render(df)
with tab5:
    recebidos.render(df_rec)
with tab6:
    analise_mensal.render(df, df_rec, meses_sel)
with tab7:
    lucratividade.render(df, df_rec, saidas_df)
with tab8:
    pareto_nomes.render(df_rec)
with tab9:
    # Usando o df_cp_f (filtrado por período)
    contas_pagar.render(df_cp_f, meses_sel, empresas_selecionadas)
with tab10:
    # Usando o df (já filtrado por Grupo/Categoria/Mês) para Departamentos
    departamentos.render(df, df_depara_raw, meses_sel, empresas_selecionadas)
with tab11:
    # Garantindo que o storytelling veja os dados filtrados
    storytelling.render(df, df_rec, df, saidas_df, meses_sel)
