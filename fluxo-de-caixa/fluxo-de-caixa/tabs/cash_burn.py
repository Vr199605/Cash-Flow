import streamlit as st

from config import COL_V


def render(saidas_df):
    st.markdown("### Queima de Caixa Diária (Acumulada)")
    if saidas_df.empty:
        st.info("Nenhuma saída encontrada para o período selecionado.")
        return

    burn = (
        saidas_df.groupby('Data de pagamento')[COL_V]
        .sum().abs().cumsum().reset_index()
    )
    st.line_chart(burn.set_index('Data de pagamento'), color="#FF4B4B")

    st.markdown("#### Detalhamento de Saída Diária")
    diario = (
        saidas_df.groupby('Data de pagamento')[COL_V]
        .sum().abs().reset_index()
        .rename(columns={COL_V: "Valor do Dia"})
    )
    st.dataframe(diario, use_container_width=True, hide_index=True)
