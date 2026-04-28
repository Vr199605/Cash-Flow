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
    pareto,
    pareto_nomes,
    recebidos,
    storytelling,
)

st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR - FORMATO CHECKBOX CONFORME SOLICITADO
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color: #00D1FF;'>💎 DASHBOARD</h2>", unsafe_allow_html=True)

    st.markdown("### 🏢 EMPRESA(S)")
    opcoes_empresas = ["Globus", "MGL"]
    empresas_selecionadas = []
    for emp in opcoes_empresas:
        if st.checkbox(emp, value=True, key=f"emp_{emp}"):
            empresas_selecionadas.append(emp)
            
    if not empresas_selecionadas:
        st.warning("Selecione pelo menos uma empresa.")
        st.stop()

    st.write("")
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

    # Lógica de Períodos (Checkboxes)
    st.markdown("### 📅 PERÍODOS")
    lista_meses = sorted(
        set(df_raw['Mes_Ano'].unique()) | set(df_rec_raw['Mes_Ano'].unique()),
        key=lambda x: pd.to_datetime(x, format='%m/%Y'),
    )
    
    meses_sel = []
    with st.container(border=True):
        for mes in lista_meses:
            # Mantém o último mês marcado por padrão como no código original
            default_m = (mes == lista_meses[-1]) if lista_meses else False
            if st.checkbox(mes, value=default_m, key=f"mes_{mes}"):
                meses_sel.append(mes)

    # Lógica de Grupos (Checkboxes)
    st.markdown("### 📂 GRUPOS")
    grupos_disponiveis = sorted(df_raw['Grupo_Filtro'].unique())
    grupos_sel = []
    with st.container(border=True):
        for grp in grupos_disponiveis:
            default_g = (grp != "Outros")
            if st.checkbox(grp, value=default_g, key=f"grp_{grp}"):
                grupos_sel.append(grp)

    # Lógica de Categorias (Checkboxes com scroll)
    st.markdown("### 🏷️ CATEGORIAS")
    cats_disponiveis = sorted(df_raw[df_raw['Grupo_Filtro'].isin(grupos_sel)]['Categoria'].unique())
    cats_sel = []
    # Altura fixa para criar o scroll conforme a imagem
    with st.container(height=300, border=True):
        for cat in cats_disponiveis:
            if st.checkbox(cat, value=True, key=f"cat_{cat}"):
                cats_sel.append(cat)

    st.write("---")
    st.markdown("### 📄 Exportação")
    if meses_sel:
        df_pdf_sai = df_raw[(df_raw['Mes_Ano'].isin(meses_sel)) & (df_raw[COL_V] < 0)]
        df_pdf_rec = df_rec_raw[df_rec_raw['Mes_Ano'].isin(meses_sel)]
        pdf_data = gerar_pdf_perfeito(df_pdf_sai, df_pdf_rec, meses_sel, empresas_selecionadas)
        st.download_button(
            label="📥 Baixar Relatório Full (PDF)",
            data=pdf_data,
            file_name="Relatorio_Financeiro.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# FILTROS APLICADOS (LÓGICA GLOBAL ATUALIZADA)
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

# ATUALIZAÇÃO: Aplicando Grupos e Categorias também ao Contas a Pagar
df_cp_f = df_cp_raw.copy()
if meses_sel:
    df_cp_f = df_cp_f[df_cp_f['Mes_Ano'].isin(meses_sel)]
if grupos_sel:
    df_cp_f = df_cp_f[df_cp_f['Grupo_Filtro'].isin(grupos_sel)]
if cats_sel:
    df_cp_f = df_cp_f[df_cp_f['Categoria'].isin(cats_sel)]

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

total_saidas = saidas_df[COL_V].sum()
cols_m = st.columns(len(grupos_sel) + 1)
cols_m[0].metric("CASH OUT TOTAL", format_brl(abs(total_saidas)))
for i, grupo in enumerate(grupos_sel):
    val = df[(df['Grupo_Filtro'] == grupo) & (df[COL_V] < 0)][COL_V].sum()
    cols_m[i + 1].metric(grupo.upper(), format_brl(abs(val)))

st.write("")

val_cp_total = df_cp_f[COL_V].sum()
agrupado_cp = df_cp_f.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index()

cols_cp = st.columns(len(agrupado_cp) + 1)
cols_cp[0].metric("CONTAS A PAGAR (TOTAL)", format_brl(abs(val_cp_total)))
for idx, row in agrupado_cp.iterrows():
    cols_cp[idx + 1].metric(f"CP: {row['Grupo_Filtro'].upper()}", format_brl(row[COL_V]))

st.write("---")

# ---------------------------------------------------------------------------
# ABAS - ATUALIZADAS (Remoção da aba de departamentos)
# ---------------------------------------------------------------------------
(
    tab1, tab2, tab3, tab4, tab5,
    tab6, tab7, tab8, tab9,
) = st.tabs([
    "📊 APRESENTAÇÃO", "💰 PARETO CASH OUT", "🎯 PARETO CASH IN", "🔥 CASH BURN", 
    "📑 CONTAS A PAGAR", "📈 SALDO CAIXA", "🧠 STORYTELLING", 
    "📋 DADOS", "💰 RECEBIDOS"
])

with tab1:
    apresentacao.render(empresas_selecionadas, somar_contas_pagar)
with tab2:
    pareto.render(saidas_df)
with tab3:
    pareto_nomes.render(df_rec)
with tab4:
    cash_burn.render(saidas_df)
with tab5:
    contas_pagar.render(df_cp_f, meses_sel, empresas_selecionadas)
with tab6:
    analise_mensal.render(df, df_rec, meses_sel)
with tab7:
    storytelling.render(df, df_rec, df, saidas_df, meses_sel)
with tab8:
    dados.render(df)
with tab9:
    recebidos.render(df_rec)
