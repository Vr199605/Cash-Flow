import pandas as pd
import streamlit as st
import re

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
        # Saídas
        df_s = pd.read_csv(URLS[emp]["s"])
        df_s.columns = df_s.columns.str.strip()
        df_s[COL_V] = df_s[COL_V].apply(_clean_val)
        df_s['Data de pagamento'] = pd.to_datetime(df_s['Data de pagamento'], dayfirst=True, errors='coerce')
        df_s['Empresa'] = emp
        list_s.append(df_s)

        # Recebidos
        df_r = pd.read_csv(URLS[emp]["r"])
        df_r.columns = df_r.columns.str.strip()
        df_r[COL_V] = df_r[COL_V].apply(_clean_val)
        df_r['Data de pagamento'] = pd.to_datetime(df_r['Data de pagamento'], dayfirst=True, errors='coerce')
        df_r['Empresa'] = emp
        list_r.append(df_r)

        # Contas a Pagar
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

        if emp == "Globus":
            df_depara_globus = pd.read_csv(URLS[emp]["depara"])
            df_depara_globus.columns = df_depara_globus.columns.str.strip()

    # Concatenar saídas
    df_saidas = pd.concat(list_s, ignore_index=True).dropna(subset=['Data de pagamento'])
    df_saidas['Mes_Ano'] = df_saidas['Data de pagamento'].dt.strftime('%m/%Y')
    df_saidas['Grupo_Filtro'] = df_saidas['Categoria'].apply(_atribuir_grupo)

    # --- LÓGICA DE IMPACTO TOTAL (GARANTIR QUE TODOS OS VALORES APAREÇAM) ---
    if not df_depara_globus.empty and 'Centro de Custo' in df_saidas.columns:
        # 1. Limpeza do Centro de Custo para bater com o depara (pega só os números)
        df_saidas['CC_Merge'] = df_saidas['Centro de Custo'].astype(str).str.extract(r'(\d+)').astype(float)
        
        # 2. Identifica qual coluna de destino usar do seu depara (SETOR ou DEPARTAMENTO)
        col_destino = 'SETOR' if 'SETOR' in df_depara_globus.columns else 'DEPARTAMENTO'
        
        if 'Centro de Custo' in df_depara_globus.columns:
            depara_aux = df_depara_globus[['Centro de Custo', col_destino]].copy()
            depara_aux.columns = ['CC_Merge', 'Dept_Tmp']
            depara_aux['CC_Merge'] = depara_aux['CC_Merge'].astype(float)
            depara_aux = depara_aux.drop_duplicates(subset=['CC_Merge'])

            # 3. Merge LEFT: mantém todas as linhas das saídas, sem exceção
            df_saidas = pd.merge(df_saidas, depara_aux, on='CC_Merge', how='left')
            
            # 4. O PULO DO GATO: Se ficou vazio (NaN), vira 'BACKOFFICE'
            df_saidas['Departamento'] = df_saidas['Dept_Tmp'].fillna('BACKOFFICE')
        else:
            df_saidas['Departamento'] = 'BACKOFFICE'
    else:
        # Se não tiver depara, joga tudo em BACKOFFICE para não perder os dados
        df_saidas['Departamento'] = 'BACKOFFICE'
    # -----------------------------------------------------------------------

    df_rec = pd.concat(list_r, ignore_index=True).dropna(subset=['Data de pagamento'])
    df_rec['Mes_Ano'] = df_rec['Data de pagamento'].dt.strftime('%m/%Y')

    df_cp_all = pd.concat(list_cp, ignore_index=True)
    df_cp_all['Mes_Ano'] = df_cp_all['Data de pagamento'].dt.strftime('%m/%Y')
    df_cp_all['Grupo_Filtro'] = df_cp_all['Categoria'].apply(_atribuir_grupo)

    return df_saidas, df_rec, df_cp_all, df_depara_globus
