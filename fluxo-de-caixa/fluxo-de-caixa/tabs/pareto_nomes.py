import streamlit as st

from config import COL_V


def render(df_rec):
    st.markdown("### Pareto por Nomes (Recebimentos)")

    if 'Nome' not in df_rec.columns:
        st.info("Coluna 'Nome' não encontrada nos dados de recebimentos.")
        return

    nomes = sorted(df_rec['Nome'].dropna().unique())
    selecionados = st.multiselect("🔍 Filtrar Nomes Específicos:", options=nomes, default=nomes)
    df_filtrado = df_rec[df_rec['Nome'].isin(selecionados)]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Maiores Recebimentos por Nome")
        top10 = (
            df_filtrado.groupby('Nome')[COL_V]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        st.dataframe(top10.style.format({COL_V: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Distribuição do Recebimento (Top 10)")
        st.bar_chart(
            df_filtrado.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10),
            color="#00D1FF",
        )
