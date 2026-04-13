import pandas as pd
import streamlit as st

from config import COL_V


def _clean_cc(val) -> str:
    if pd.isna(val):
        return ""
    s = str(val).strip().split('.')[0].split(',')[0]
    return "".join(filter(str.isdigit, s))


def render(df_raw, df_depara_raw, meses_sel: list, empresas_selecionadas: list):
    st.markdown("### 🏢 ANÁLISE DE CUSTOS POR SETOR / DEPARTAMENTO (GLOBUS)")

    if "Globus" not in empresas_selecionadas or df_depara_raw.empty:
        st.info("Selecione a empresa 'Globus' para visualizar a análise por Setor e Departamento.")
        return

    df_globus = df_raw[(df_raw['Empresa'] == "Globus") & (df_raw[COL_V] < 0)].copy()
    if meses_sel:
        df_globus = df_globus[df_globus['Mes_Ano'].isin(meses_sel)].copy()

    depara = df_depara_raw[['Centro de Custo', 'SETOR', 'DEPARTAMENTO']].copy()
    df_globus['CC_CLEAN'] = df_globus['Centro de Custo'].apply(_clean_cc)
    depara['CC_CLEAN'] = depara['Centro de Custo'].apply(_clean_cc)

    df_merged = pd.merge(df_globus, depara, on='CC_CLEAN', how='left')

    setores = sorted(df_merged['SETOR'].dropna().unique())
    setor_sel = st.multiselect("🔍 Filtrar por Setor:", options=setores, default=setores)

    deptos = sorted(df_merged[df_merged['SETOR'].isin(setor_sel)]['DEPARTAMENTO'].dropna().unique())
    depto_sel = st.multiselect("🔍 Filtrar por Departamento:", options=deptos, default=deptos)

    df_analise = df_merged[
        df_merged['SETOR'].isin(setor_sel) & df_merged['DEPARTAMENTO'].isin(depto_sel)
    ]

    if df_analise.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados nesta aba.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Custos por Setor")
        custo_setor = df_analise.groupby('SETOR')[COL_V].sum().abs().sort_values(ascending=False).reset_index()
        st.dataframe(custo_setor.style.format({COL_V: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
        st.bar_chart(custo_setor.set_index('SETOR'), color="#00D1FF")
    with col2:
        st.subheader("Custos por Departamento")
        custo_depto = df_analise.groupby('DEPARTAMENTO')[COL_V].sum().abs().sort_values(ascending=False).reset_index()
        st.dataframe(custo_depto.style.format({COL_V: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
        st.bar_chart(custo_depto.set_index('DEPARTAMENTO'), color="#00D1FF")

    st.write("---")
    st.subheader("📜 Detalhamento dos Custos")
    st.dataframe(
        df_analise[['Data de pagamento', 'Mes_Ano', 'Categoria', 'SETOR', 'DEPARTAMENTO', COL_V]],
        use_container_width=True,
        hide_index=True,
    )
