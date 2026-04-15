import streamlit as st
import pandas as pd
import plotly.express as px
from config import COL_V, format_brl

def render(df, df_depara_raw, meses_sel, empresas_selecionadas):
    st.markdown("### 🏢 ANÁLISE DE CUSTOS POR SETOR / DEPARTAMENTO (GLOBUS)")

    # 1. VALIDAÇÃO INICIAL
    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados na barra lateral.")
        return

    # 2. GARANTIA DE COLUNA
    # O data.py já envia a coluna 'Departamento'. Se por algum motivo ela não existir, 
    # criamos como BACKOFFICE para garantir que o valor da RESCISÃO apareça.
    if 'Departamento' not in df.columns:
        df['Departamento'] = 'BACKOFFICE'
    
    # Preenchimento preventivo de nulos caso algum filtro tenha limpado a coluna
    df['Departamento'] = df['Departamento'].fillna('BACKOFFICE')

    # 3. FILTROS INTERNOS DA ABA
    col1, col2 = st.columns(2)
    
    with col1:
        setores_disponiveis = sorted(df['Departamento'].unique())
        setores_sel = st.multiselect(
            "🔍 Filtrar por Setor/Departamento:",
            options=setores_disponiveis,
            default=setores_disponiveis
        )

    # 4. APLICAÇÃO DOS FILTROS DA ABA
    df_f = df[df['Departamento'].isin(setores_sel)]

    if df_f.empty:
        st.info("💡 Selecione um setor acima para visualizar os dados.")
        return

    # 5. MÉTRICAS DE TOPO
    total_setor = abs(df_f[COL_V].sum())
    st.metric("Custo Total dos Setores Selecionados", format_brl(total_setor))

    # 6. AGRUPAMENTO E GRÁFICO
    # Aqui somamos tudo (incluindo a Rescisão que caiu no Backoffice)
    df_pizza = df_f.groupby('Departamento')[COL_V].sum().abs().reset_index()
    df_pizza = df_pizza.sort_values(by=COL_V, ascending=False)

    fig = px.pie(
        df_pizza, 
        values=COL_V, 
        names='Departamento',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

    # 7. TABELA DETALHADA
    st.markdown("#### 📝 Detalhamento por Categoria")
    # Isso permite ver que a 'RESCISÃO' está dentro do 'BACKOFFICE'
    df_detalhe = df_f.groupby(['Departamento', 'Categoria'])[COL_V].sum().abs().reset_index()
    df_detalhe.columns = ['Setor', 'Categoria', 'Valor Total']
    
    st.dataframe(
        df_detalhe.sort_values(by=['Setor', 'Valor Total'], ascending=[True, False]),
        use_container_width=True,
        hide_index=True
    )

    # 8. CONFERÊNCIA DE SEGURANÇA
    total_original = abs(df[COL_V].sum())
    if abs(total_setor - total_original) > 1:
        st.caption(f"Nota: Total original filtrado: {format_brl(total_original)}")
