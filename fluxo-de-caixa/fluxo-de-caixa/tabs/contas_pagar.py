import streamlit as st

from config import COL_V, format_brl


def render(df_cp_raw, meses_sel: list, empresas_selecionadas: list):
    st.markdown("### 📑 CONTAS A PAGAR (CONSOLIDADO)")

    if df_cp_raw.empty:
        st.warning("Nenhum dado encontrado na aba Contas a Pagar.")
        return

    st.markdown(f"**Empresas sendo exibidas:** {', '.join(empresas_selecionadas)}")

    cats = sorted(df_cp_raw['Categoria'].dropna().unique())
    cats_sel = st.multiselect("🔍 Filtrar por Categorias (Contas a Pagar):", options=cats, default=cats)

    df_filtrado = df_cp_raw[df_cp_raw['Categoria'].isin(cats_sel)]
    if meses_sel:
        df_filtrado = df_filtrado[df_filtrado['Mes_Ano'].isin(meses_sel)]

    total = df_filtrado[COL_V].sum()
    st.info(f"**Resumo:** O valor total provisionado é de **{format_brl(abs(total))}**")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
