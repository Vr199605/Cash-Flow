import pandas as pd
import streamlit as st

from config import COL_V


def _clean_cc(val) -> str:
    """Limpa e padroniza o formato do Centro de Custo."""
    if pd.isna(val):
        return ""
    s = str(val).strip().split('.')[0].split(',')[0]
    return "".join(filter(str.isdigit, s))


def render(df_raw, df_depara_raw, df_depara_globus, meses_sel: list, empresas_selecionadas: list):
    st.markdown("### 🏢 ALOCAÇÃO DE CUSTOS POR SETOR E DEPARTAMENTO")

    if "Globus" not in empresas_selecionadas:
        st.info("Selecione a empresa 'Globus' para visualizar a análise detalhada de pessoal.")
        return

    # Filtragem inicial: apenas saídas da Globus
    df_globus = df_raw[(df_raw['Empresa'] == "Globus") & (df_raw[COL_V] < 0)].copy()
    if meses_sel:
        df_globus = df_globus[df_globus['Mes_Ano'].isin(meses_sel)].copy()

    # --- PREPARAÇÃO DO DEPARA 1 (CENTRO DE CUSTO) ---
    # Colunas: Categoria, Nome do Funcionário, Cargo, SETOR, DEPARTAMENTO, Centro de Custo
    depara_cc = df_depara_raw.copy()
    depara_cc['CC_CLEAN'] = depara_cc['Centro de Custo'].apply(_clean_cc)
    depara_cc = depara_cc.drop_duplicates(subset=['CC_CLEAN'])
    
    # --- PREPARAÇÃO DO DEPARA 2 (NOME DO FUNCIONÁRIO) ---
    # Colunas: Nome do Funcionário, Centro de Custo
    # Aqui usamos o df_depara_globus que você vinculou à nova URL
    depara_nome = df_depara_globus.copy()
    depara_nome['NOME_KEY'] = depara_nome['Nome do Funcionário'].astype(str).str.strip().str.upper()
    # Removemos duplicatas para não multiplicar valores no merge
    depara_nome = depara_nome.drop_duplicates(subset=['NOME_KEY'])

    # --- LÓGICA DE ALOCAÇÃO (MERGE) ---
    df_globus['CC_CLEAN'] = df_globus['Centro de Custo'].apply(_clean_cc)
    df_globus['NOME_KEY'] = df_globus['Nome'].astype(str).str.strip().str.upper()

    # Passo 1: Tenta alocar pelo Centro de Custo
    df_merged = pd.merge(
        df_globus, 
        depara_cc[['CC_CLEAN', 'SETOR', 'DEPARTAMENTO']], 
        on='CC_CLEAN', 
        how='left'
    )

    # Passo 2: Onde o SETOR ainda está vazio, tenta pelo Nome do Funcionário
    # Primeiro, trazemos as informações do depara de nomes
    df_merged = pd.merge(
        df_merged, 
        depara_nome[['NOME_KEY', 'SETOR', 'DEPARTAMENTO']], 
        on='NOME_KEY', 
        how='left', 
        suffixes=('', '_NOME')
    )

    # Preenche as lacunas: Se SETOR é nulo, usa SETOR_NOME
    df_merged['SETOR'] = df_merged['SETOR'].fillna(df_merged['SETOR_NOME'])
    df_merged['DEPARTAMENTO'] = df_merged['DEPARTAMENTO'].fillna(df_merged['DEPARTAMENTO_NOME'])

    # Limpeza de colunas temporárias
    df_merged = df_merged.drop(columns=['SETOR_NOME', 'DEPARTAMENTO_NOME', 'NOME_KEY'])
    df_merged['SETOR'] = df_merged['SETOR'].fillna("NÃO ALOCADO")
    df_merged['DEPARTAMENTO'] = df_merged['DEPARTAMENTO'].fillna("NÃO ALOCADO")

    # --- INTERFACE E FILTROS ---
    setores = sorted(df_merged['SETOR'].unique())
    setor_sel = st.multiselect("🔍 Filtrar por Setor:", options=setores, default=[s for s in setores if s != "NÃO ALOCADO"])

    deptos = sorted(df_merged[df_merged['SETOR'].isin(setor_sel)]['DEPARTAMENTO'].unique())
    depto_sel = st.multiselect("🔍 Filtrar por Departamento:", options=deptos, default=deptos)

    df_analise = df_merged[
        df_merged['SETOR'].isin(setor_sel) & df_merged['DEPARTAMENTO'].isin(depto_sel)
    ]

    if df_analise.empty:
        st.warning("Nenhum dado encontrado para os critérios selecionados.")
        return

    # --- EXIBIÇÃO DOS RESULTADOS ---
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
    st.subheader("📜 Detalhamento Gerencial")
    # Exibimos apenas colunas operacionais, ocultando o nome individual conforme solicitado
    st.dataframe(
        df_analise[['Data de pagamento', 'Mes_Ano', 'Categoria', 'SETOR', 'DEPARTAMENTO', COL_V]],
        use_container_width=True,
        hide_index=True,
    )
