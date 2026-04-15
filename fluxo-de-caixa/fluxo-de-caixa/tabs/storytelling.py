import streamlit as st
import plotly.graph_objects as go
from config import format_brl, COL_V

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    st.markdown("### 🧠 STORYTELLING EXECUTIVO")
    st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")

    # --- INDICADOR DE SAÚDE (O CÍRCULO NO TOPO) ---
    col_vazia, col_saude, col_texto = st.columns([1, 1, 3])
    with col_saude:
        # Exemplo de Gauge ou indicador circular simples
        st.markdown(
            f"""
            <div style="text-align: center; border: 2px solid #555; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 24px; font-weight: bold; color: #ff4b4b;">0</span>
            </div>
            <p style="text-align: center; margin-top: 5px;">PONTOS</p>
            """, unsafe_allow_html=True
        )
    with col_texto:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 0;'>Crítico</h4>", unsafe_allow_html=True)
        st.write("Recuo em margem líquida, variação de custos, concentração de receita e anomalias detectadas.")

    st.write("---")

    # --- KPI CARDS (RECEITA, DESPESA, RESULTADO, ÍNDICE) ---
    # Valores para os cards
    rec_total = df_rec[COL_V].sum()
    desp_total = abs(saidas_df[COL_V].sum())
    res_liquido = rec_total - desp_total
    indice_custo = (desp_total / rec_total * 100) if rec_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
            <div style="border: 1px solid #00ff00; padding: 15px; border-radius: 10px; background-color: rgba(0,255,0,0.05);">
                <p style="margin:0; font-size: 12px; color: #00ff00;">🟢 RECEITA TOTAL</p>
                <h3 style="margin:0;">{format_brl(rec_total)}</h3>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div style="border: 1px solid #ff4b4b; padding: 15px; border-radius: 10px; background-color: rgba(255,75,75,0.05);">
                <p style="margin:0; font-size: 12px; color: #ff4b4b;">🔴 DESPESA TOTAL</p>
                <h3 style="margin:0;">{format_brl(desp_total)}</h3>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        color = "#ff4b4b" if res_liquido < 0 else "#00ff00"
        st.markdown(f"""
            <div style="border: 1px solid {color}; padding: 15px; border-radius: 10px;">
                <p style="margin:0; font-size: 12px; color: {color};">🔘 RESULTADO LÍQUIDO</p>
                <h3 style="margin:0;">{format_brl(res_liquido)}</h3>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
            <div style="border: 1px solid #f1c40f; padding: 15px; border-radius: 10px; background-color: rgba(241,196,15,0.05);">
                <p style="margin:0; font-size: 12px; color: #f1c40f;">🟡 CUSTO / RECEITA</p>
                <h3 style="margin:0;">{indice_custo:.1f}%</h3>
            </div>
        """, unsafe_allow_html=True)

    # --- GRÁFICO DE FLUXO (BARRAS VERDES E VERMELHAS) ---
    st.write("")
    st.subheader("📊 Evolução do Fluxo de Caixa")
    
    # Exemplo de lógica para as barras por mês
    df_evolucao = df_geral.groupby('Mes_Ano')[COL_V].sum().reset_index()
    # (Aqui você deve gerar um gráfico do Plotly com barmode='group' 
    # usando cores específicas: green para entradas e red para saídas)
    
    # --- RODAPÉ: COMPOSIÇÃO E RADAR ---
    st.write("---")
    col_pizza, col_radar = st.columns(2)
    
    with col_pizza:
        st.markdown("#### 🍕 Distribuição por Grupo")
        # Inserir aqui seu st.plotly_chart de Donut Chart
        
    with col_radar:
        st.markdown("#### 🕸️ Radar de Concentração (%)")
        # Inserir aqui seu gráfico de radar (Scatterpolar do Plotly)

    # --- RESUMO FINAL (TEXTO COLORIDO NO FUNDO) ---
    st.markdown(f"""
        <div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <p style="margin:0; font-size: 14px;">
                No período de <b>{', '.join(meses_sel)}</b>, a operação gerou <span style="color:#00ff00;">{format_brl(rec_total)}</span> 
                em receitas e consumiu <span style="color:#ff4b4b;">{format_brl(desp_total)}</span> em despesas, 
                resultando em um <span style="color:#ff4b4b;">déficit de {format_brl(res_liquido)}</span>.
            </p>
        </div>
    """, unsafe_allow_html=True)
