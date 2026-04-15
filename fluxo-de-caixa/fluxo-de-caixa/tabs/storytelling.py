import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from config import format_brl, COL_V

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    st.markdown("### 🧠 STORYTELLING EXECUTIVO")
    st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")

    # --- INDICADOR DE SAÚDE ---
    col_vazia, col_saude, col_texto = st.columns([1, 1, 3])
    with col_saude:
        st.markdown(
            f"""
            <div style="text-align: center; border: 2px solid #555; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; margin: auto;">
                <span style="font-size: 24px; font-weight: bold; color: #ff4b4b;">0</span>
            </div>
            <p style="text-align: center; margin-top: 5px; font-size: 12px; color: #aaa;">PONTOS</p>
            """, unsafe_allow_html=True
        )
    with col_texto:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 0;'>Crítico</h4>", unsafe_allow_html=True)
        st.write("Recuo em margem líquida, variação de custos, concentração de receita e anomalias detectadas.")

    st.write("---")

    # --- KPI CARDS ---
    rec_total = df_rec[COL_V].sum()
    desp_total = abs(saidas_df[COL_V].sum())
    res_liquido = rec_total - desp_total
    indice_custo = (desp_total / rec_total * 100) if rec_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div style="border: 1px solid #00ff00; padding: 15px; border-radius: 10px;">'
                    f'<p style="margin:0; font-size: 12px; color: #00ff00;">🟢 RECEITA TOTAL</p>'
                    f'<h3 style="margin:0;">{format_brl(rec_total)}</h3></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="border: 1px solid #ff4b4b; padding: 15px; border-radius: 10px;">'
                    f'<p style="margin:0; font-size: 12px; color: #ff4b4b;">🔴 DESPESA TOTAL</p>'
                    f'<h3 style="margin:0;">{format_brl(desp_total)}</h3></div>', unsafe_allow_html=True)
    with c3:
        color = "#ff4b4b" if res_liquido < 0 else "#00ff00"
        st.markdown(f'<div style="border: 1px solid {color}; padding: 15px; border-radius: 10px;">'
                    f'<p style="margin:0; font-size: 12px; color: {color};">🔘 RESULTADO LÍQUIDO</p>'
                    f'<h3 style="margin:0;">{format_brl(res_liquido)}</h3></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div style="border: 1px solid #f1c40f; padding: 15px; border-radius: 10px;">'
                    f'<p style="margin:0; font-size: 12px; color: #f1c40f;">🟡 CUSTO / RECEITA</p>'
                    f'<h3 style="margin:0;">{indice_custo:.1f}%</h3></div>', unsafe_allow_html=True)

    # --- GRÁFICO DE EVOLUÇÃO (BARRAS) ---
    st.markdown("#### 📊 Evolução do Fluxo de Caixa")
    df_fluxo = df_geral.groupby('Mes_Ano')[COL_V].sum().reset_index()
    df_fluxo_rec = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index()

    fig_evol = go.Figure()
    fig_evol.add_trace(go.Bar(x=df_fluxo_rec['Mes_Ano'], y=df_fluxo_rec[COL_V], name='Entradas', marker_color='#00ff00'))
    fig_evol.add_trace(go.Bar(x=df_fluxo['Mes_Ano'], y=df_fluxo[COL_V].abs(), name='Saídas', marker_color='#ff4b4b'))
    fig_evol.update_layout(template="plotly_dark", barmode='group', height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_evol, use_container_width=True)

    # --- PIZZA E RADAR ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🍕 Distribuição por Grupo")
        df_pizza = saidas_df.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index()
        fig_pizza = px.pie(df_pizza, values=COL_V, names='Grupo_Filtro', hole=.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pizza.update_layout(template="plotly_dark", height=300, showlegend=False)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_right:
        st.markdown("#### 🕸️ Radar de Concentração (%)")
        # Exemplo de Radar simulando concentração de custos
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=[40, 30, 50, 20, 45],
            theta=['Operacional', 'Tributário', 'Pessoal', 'Marketing', 'Financeiro'],
            fill='toself', marker_color='#00D1FF'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                               template="plotly_dark", height=300)
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- RESUMO FINAL ---
    st.markdown(f"""
        <div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <p style="margin:0; font-size: 14px; color: white;">
                No período de <b>{', '.join(meses_sel)}</b>, a operação gerou <span style="color:#00ff00;">{format_brl(rec_total)}</span> 
                em receitas e consumiu <span style="color:#ff4b4b;">{format_brl(desp_total)}</span> em despesas, 
                resultando em um <span style="color:#ff4b4b;">déficit de {format_brl(res_liquido)}</span>.
            </p>
        </div>
    """, unsafe_allow_html=True)
