import streamlit as st

from config import COL_V


def render(saidas_df):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Maiores Gastos por Grupo")
        df_grupo = (
            saidas_df.groupby('Grupo_Filtro')[COL_V]
            .sum().abs().sort_values(ascending=False).reset_index()
        )
        st.dataframe(df_grupo.style.format({COL_V: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
        st.bar_chart(df_grupo.set_index('Grupo_Filtro'), color="#00D1FF")

    with col2:
        st.subheader("Top 10 Categorias")
        df_cat = (
            saidas_df.groupby('Categoria')[COL_V]
            .sum().abs().sort_values(ascending=False).head(10).reset_index()
        )
        st.dataframe(df_cat.style.format({COL_V: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
        st.bar_chart(df_cat.set_index('Categoria'), color="#00D1FF")
