import streamlit as st

from config import COL_V, format_brl


def render(df, df_rec, saidas_df):
    st.subheader("INDICADORES DE LUCRATIVIDADE")

    lucro = df_rec[COL_V].sum() - abs(df[df[COL_V] < 0][COL_V].sum())
    cor = "#FF4B4B" if lucro < 0 else "#00D1FF"

    st.markdown("##### LUCRO LÍQUIDO (CAIXA)")
    st.markdown(f"<h2 style='color: {cor};'>{format_brl(lucro)}</h2>", unsafe_allow_html=True)

    st.markdown("#### Eficiência por Grupo (Gasto vs Receita)")
    st.bar_chart(saidas_df.groupby('Grupo_Filtro')[COL_V].sum().abs(), color="#00D1FF")

    total_ent = df_rec[COL_V].sum()
    if total_ent > 0:
        st.markdown("📊 **Detalhamento de Impacto no Faturamento:**")
        grupos = saidas_df.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index()
        grupos['Porcentagem'] = (grupos[COL_V] / total_ent * 100).apply(lambda x: f"{x:.1f}%")
        grupos[COL_V] = grupos[COL_V].apply(format_brl)
        st.dataframe(grupos, use_container_width=True, hide_index=True)
