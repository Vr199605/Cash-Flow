import pandas as pd
import streamlit as st

from config import COL_V


def _clean_cc(val) -> str:
    if pd.isna(val):
        return ""
    s = str(val).strip().split('.')[0].split(',')[0]
    return "".join(filter(str.isdigit, s))


def render(df_raw, df_depara_raw, df_depara_globus, meses_sel: list, empresas_selecionadas: list):
    st.markdown("### 🏢 ANÁLISE DE CUSTOS POR SETOR / DEPARTAMENTO (GLOBUS)")

    if "Globus" not in empresas_selecionadas or df_depara_raw.empty:
        st.info("Selecione a empresa 'Globus' para visualizar a análise por Setor e Departamento.")
        return

    df_globus = df_raw[(df_raw['Empresa'] == "Globus") & (df_raw[COL_V] < 0)].copy()
    if meses_sel:
        df_globus = df_globus[df_globus['Mes_Ano'].isin(meses_sel)].copy()

    # --- PROCESSAMENTO DEPARA 1 (POR CENTRO DE CUSTO) ---
    depara_cc = df_depara_raw[['Centro de Custo', 'SETOR', 'DEPARTAMENTO']].copy()
    depara_cc['CC_CLEAN'] = depara_cc['Centro de Custo'].apply(_clean_cc)
    depara_cc = depara_cc.drop_duplicates(subset=['CC_CLEAN'])
    
    # --- PROCESSAMENTO DEPARA 2 (POR NOME/FORNECEDOR) ---
    # Usamos o novo depara enviado para buscar por correspondência de nome
    depara_nome = df_depara_globus[['Nome', 'SETOR', 'DEPARTAMENTO']].copy()
    depara_nome['Nome'] = depara_nome['Nome'].astype(str).str.strip().str.upper()
    depara_nome = depara_nome.drop_duplicates(subset=['Nome'])

    # Preparação do DF principal
    df_globus['CC_CLEAN'] = df_globus['Centro de Custo'].apply(_clean_cc)
    df_globus['Nome_Upper'] = df_globus['Nome'].astype(str).str.strip().str.upper()

    # 1. Merge por Centro de Custo
    df_merged = pd.merge(df_globus, depara_cc[['CC_CLEAN', 'SETOR', 'DEPARTAMENTO']], on='CC_CLEAN', how='left')

    # 2. Preenchimento de lacunas usando o Merge por Nome
    # Criamos um merge auxiliar
    df_merged = pd.merge(df_merged, depara_nome, left_on='Nome_Upper', right_on='Nome', how='left', suffixes=('', '_NOME'))

    # Se o SETOR estiver vazio pelo CC, usamos o do NOME
    df_merged['SETOR'] = df_merged['SETOR'].fillna(df_merged['SETOR_NOME'])
    df_merged['DEPARTAMENTO'] = df_merged['DEPARTAMENTO'].fillna(df_merged['DEPARTAMENTO_NOME'])

    # Limpeza de colunas auxiliares
    df_merged = df_merged.drop(columns=['SETOR_NOME', 'DEPARTAMENTO_NOME', 'Nome_NOME', 'Nome_Upper'])

    # --- INTERFACE DE FILTROS ---
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
    st.subheader("📜 Detalhamento dos Custos (Setorizado)")
    # O nome não é incluído na visualização final conforme solicitado
    st.dataframe(
        df_analise[['Data de pagamento', 'Mes_Ano', 'Categoria', 'SETOR', 'DEPARTAMENTO', COL_V]],
        use_container_width=True,
        hide_index=True,
    )
