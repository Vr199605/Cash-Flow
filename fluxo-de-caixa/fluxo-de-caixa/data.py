import pandas as pd
import streamlit as st

from config import COL_V, MAPA_GRUPOS, URLS


def _clean_val(v):
    if isinstance(v, str):
        v = v.replace('R$', '').replace('.', '').replace(' ', '').replace(',', '.')
        try:
            return float(v)
        except ValueError:
            return 0.0
    return v


def _atribuir_grupo(cat) -> str:
    if pd.isna(cat):
        return "Outros"
    cat_upper = str(cat).strip().upper()
    for grupo, categorias in MAPA_GRUPOS.items():
        for c in categorias:
            if c.strip().upper() in cat_upper or cat_upper in c.strip().upper():
                return grupo
    return "Outros"


@st.cache_data(ttl=600)
def load_and_process(empresas_selecionadas: tuple):
    list_s, list_r, list_cp = [], [], []
    df_depara_globus = pd.DataFrame()

    for emp in empresas_selecionadas:
        # Carregamento de Saídas
        df_s = pd.read_csv(URLS[emp]["s"])
        df_s.columns = df_s.columns.str.strip()
        df_s[COL_V] = df_s[COL_V].apply(_clean_val)
        df_s['Data de pagamento'] = pd.to_datetime(df_s['Data de pagamento'], dayfirst=True, errors='coerce')
        df_s['Empresa'] = emp
        list_s.append(df_s)

        # Carregamento de Recebidos
        df_r = pd.read_csv(URLS[emp]["r"])
        df_r.columns = df_r.columns.str.strip()
        df_r[COL_V] = df_r[COL_V].apply(_clean_val)
        df_r['Data de pagamento'] = pd.to_datetime(df_r['Data de pagamento'], dayfirst=True, errors='coerce')
        df_r['Empresa'] = emp
        list_r.append(df_r)

        # Carregamento de Contas a Pagar
        df_cp = pd.read_csv(URLS[emp]["cp"])
        df_cp.columns = df_cp.columns.str.strip()
        if COL_V in df_cp.columns:
            df_cp[COL_V] = df_cp[COL_V].apply(_clean_val)
        if 'Data de vencimento' in df_cp.columns:
            df_cp['Data de pagamento'] = pd.to_datetime(df_cp['Data de vencimento'], dayfirst=True, errors='coerce')
        else:
            df_cp['Data de pagamento'] = pd.Timestamp.now()
        df_cp['Empresa'] = emp
        list_cp.append(df_cp)

        # Carregamento do Depara (Apenas Globus)
        if emp == "Globus":
            try:
                df_depara_globus = pd.read_csv(URLS[emp]["depara"])
                df_depara_globus.columns = df_depara_globus.columns.str.strip()
            except Exception:
                df_depara_globus = pd.DataFrame()

    # Processamento Final de Saídas
    df_saidas = (
        pd.concat(list_s, ignore_index=True)
        .dropna(subset=['Data de pagamento'])
        .sort_values('Data de pagamento')
    )
    df_saidas['Mes_Ano'] = df_saidas['Data de pagamento'].dt.strftime('%m/%Y')
    df_saidas['Grupo_Filtro'] = df_saidas['Categoria'].apply(_atribuir_grupo)

    # --- LÓGICA DE DEPARA PARA DEPARTAMENTOS (BACKOFFICE AUTOMÁTICO) ---
    # 1. Verifica se o depara foi carregado
    if not df_depara_globus.empty:
        # 2. Identifica se as colunas existem (ignorando maiúsculas/minúsculas para segurança)
        cols_originais = {c.upper(): c for c in df_depara_globus.columns}
        
        if 'CENTRO DE CUSTO' in cols_originais and 'DEPARTAMENTO' in cols_originais:
            # Normaliza os nomes para o merge
            col_cc = cols_originais['CENTRO DE CUSTO']
            col_dept = cols_originais['DEPARTAMENTO']
            
            # Prepara o depara para o merge
            depara_clean = df_depara_globus[[col_cc, col_dept]].copy()
            depara_clean.columns = ['Centro de Custo', 'Departamento']
            
            # Faz o merge (how='left' garante que NADA seja deletado das saídas)
            df_saidas = pd.merge(df_saidas, depara_clean, on='Centro de Custo', how='left')
            
            # O que não encontrou (NaN) ou está vazio, vira 'Backoffice'
            df_saidas['Departamento'] = df_saidas['Departamento'].fillna('Backoffice')
        else:
            # Se as colunas não existirem na planilha, cria a coluna como Backoffice
            df_saidas['Departamento'] = 'Backoffice'
    else:
        # Se não houver planilha de depara, tudo vira Backoffice
        df_saidas['Departamento'] = 'Backoffice'
    # -------------------------------------------------------------------

    df_rec = pd.concat(list_r, ignore_index=True).dropna(subset=['Data de pagamento'])
    df_rec['Mes_Ano'] = df_rec['Data de pagamento'].dt.strftime('%m/%Y')

    df_cp_all = pd.concat(list_cp, ignore_index=True)
    df_cp_all['Mes_Ano'] = df_cp_all['Data de pagamento'].dt.strftime('%m/%Y')
    df_cp_all['Grupo_Filtro'] = df_cp_all['Categoria'].apply(_atribuir_grupo)

    return df_saidas, df_rec, df_cp_all, df_depara_globus
