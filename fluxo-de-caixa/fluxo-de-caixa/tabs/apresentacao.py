import streamlit as st


def render(empresas_selecionadas: list, somar_contas_pagar: bool):
    st.markdown("<h3>🏛️ Visão Executiva e Estrutura de Dados</h3>", unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 🎯 Objetivo da Ferramenta\nAnálise consolidada: **{', '.join(empresas_selecionadas)}**")
        st.markdown(
            "1. **Ingestão:** Conexão direta.\n"
            "2. **Processamento:** Limpeza e padronização.\n"
            "3. **Categorização:** Mapeamento inteligente."
        )
        if somar_contas_pagar:
            st.info("💡 **Aviso:** Os dados de 'Contas a Pagar' estão integrados aos gráficos e cálculos atuais.")
    with col2:
        st.markdown("#### 🛠️ Pilares de Análise")
        st.success("**Fluxo de Caixa:** Diferença exata entre entradas e saídas.")
        st.warning("**Eficiência:** Identificação de gargalos (Pareto).")
        st.info("**Saúde Líquida:** Visibilidade imediata de lucro/prejuízo.")
