import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import format_brl, COL_V

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    st.markdown("### 🧠 STORYTELLING EXECUTIVO")
    st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")

    # --- 1. INDICADOR DE SAÚDE ---
    col_saude_1, col_saude_2 = st.columns([1, 3])
    with col_saude_1:
        st.markdown(
            f"""<div style="text-align: center; border: 2px solid #555; border-radius: 50%; width: 80px; height: 80px; 
            display: flex; align-items: center; justify-content: center; margin: auto;">
            <span style="font-size: 24px; font-weight: bold; color: #ff4b4b;">0</span></div>
            <p style="text-align: center; margin-top: 5px; font-size: 10px; color: #aaa;">PONTOS</p>""", 
            unsafe_allow_html=True
        )
    with col_saude_2:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 0;'>Crítico</h4>", unsafe_allow_html=True)
        st.write("Recuo em margem líquida, variação de custos, concentração de receita e anomalias detectadas.")

    # --- 2. KPI CARDS ---
    rec_total = df_rec[COL_V].sum()
    desp_total = abs(saidas_df[COL_V].sum())
    res_liquido = rec_total - desp_total
    indice_custo = (desp_total / rec_total * 100) if rec_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    labels = ["RECEITA TOTAL", "DESPESA TOTAL", "RESULTADO LÍQUIDO", "CUSTO / RECEITA"]
    valores = [rec_total, desp_total, res_liquido, indice_custo]
    cores = ["#00ff00", "#ff4b4b", "#555", "#f1c40f"]

    for col, lab, val, cor in zip([c1, c2, c3, c4], labels, valores, cores):
        v_str = f"{val:.1f}%" if lab == "CUSTO / RECEITA" else format_brl(val)
        col.markdown(f"""<div style="border: 1px solid {cor}; padding: 15px; border-radius: 10px;">
                     <p style="margin:0; font-size: 10px; color: {cor};">● {lab}</p>
                     <h3 style="margin:0; font-size: 18px;">{v_str}</h3></div>""", unsafe_allow_html=True)

    # --- 3. EVOLUÇÃO DO FLUXO (BARRA + LINHA) ---
    st.markdown("#### 📉 Evolução do Fluxo de Caixa")
    df_m_rec = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index()
    df_m_sai = saidas_df.groupby('Mes_Ano')[COL_V].sum().abs().reset_index()
    df_m = pd.merge(df_m_rec, df_m_sai, on='Mes_Ano', suffixes=('_Ent', '_Sai'))
    df_m['Saldo'] = df_m[f'{COL_V}_Ent'] - df_m[f'{COL_V}_Sai']
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Ent'], name='Entradas', marker_color='#27ae60'))
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Sai'], name='Saídas', marker_color='#c0392b'))
    fig_flow.add_trace(go.Scatter(x=df_m['Mes_Ano'], y=df_m['Saldo'], name='Saldo', line=dict(color='#00D1FF', width=3), marker=dict(size=10)))
    
    fig_flow.update_layout(template="plotly_dark", barmode='group', height=350, margin=dict(t=20, b=20),
                          hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_flow, use_container_width=True)

    # --- 4. PARETO TOP 10 ---
    st.markdown("#### 🎯 Análise de Pareto — Top 10 Despesas")
    df_pareto = saidas_df.groupby('Categoria')[COL_V].sum().abs().sort_values(ascending=False).head(10).reset_index()
    df_pareto['% Acumulada'] = (df_pareto[COL_V].cumsum() / df_pareto[COL_V].sum()) * 100
    
    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(x=df_pareto['Categoria'], y=df_pareto[COL_V], name='Valor', marker_color='#00D1FF', yaxis='y1'))
    fig_p.add_trace(go.Scatter(x=df_pareto['Categoria'], y=df_pareto['% Acumulada'], name='% Acumulada', line=dict(color='#f1c40f'), yaxis='y2'))
    fig_p.update_layout(template="plotly_dark", height=350, yaxis=dict(title="Valor (R$)"), 
                        yaxis2=dict(title="%", overlaying='y', side='right', range=[0, 105]),
                        margin=dict(t=20), hovermode="x unified")
    st.plotly_chart(fig_p, use_container_width=True)

    # --- 5. CONCENTRAÇÃO E ESTRUTURA (CORREÇÃO KEYERROR) ---
    col_rec, col_est = st.columns(2)
    
    with col_rec:
        st.markdown("#### 👁️ Concentração de Receita")
        # Tentativa de encontrar a coluna de nome do cliente (ajuste se for diferente)
        col_cliente = 'Descricao' if 'Descricao' in df_rec.columns else df_rec.columns[0]
        
        top_5_rec = df_rec.groupby(col_cliente)[COL_V].sum().sort_values(ascending=False).head(5)
        perc_conc = (top_5_rec.head(3).sum() / rec_total * 100) if rec_total > 0 else 0
        
        with st.container(border=True):
            for nome, valor in top_5_rec.items():
                p = (valor/rec_total*100) if rec_total > 0 else 0
                st.caption(f"{nome} | {format_brl(valor)} ({p:.1f}%)")
                st.progress(min(p/100, 1.0))
            st.markdown(f"**Índice de Concentração: {perc_conc:.1f}%**")

    with col_est:
        st.markdown("#### ⚡ Estrutura de Custos")
        lista_pontuais = ["Rescisão", "Bônus", "juros", "multas", "eventos clientes"]
        # Filtragem segura usando regex
        df_pontuais = saidas_df[saidas_df['Categoria'].str.contains('|'.join(lista_pontuais), case=False, na=False)]
        df_recorrentes = saidas_df[~saidas_df.index.isin(df_pontuais.index)]
        
        v_pontual = abs(df_pontuais[COL_V].sum())
        v_recorrente = abs(df_recorrentes[COL_V].sum())
        previsibilidade = (v_recorrente / (v_recorrente + v_pontual) * 100) if (v_recorrente + v_pontual) > 0 else 0

        c_est1, c_est2 = st.columns(2)
        c_est1.markdown(f'<div style="border: 1px solid #00D1FF; padding:10px; border-radius:10px;"><p style="font-size:10px; margin:0;">RECORRENTES</p><b>{format_brl(v_recorrente)}</b></div>', unsafe_allow_html=True)
        c_est2.markdown(f'<div style="border: 1px solid #f1c40f; padding:10px; border-radius:10px;"><p style="font-size:10px; margin:0;">PONTUAIS</p><b>{format_brl(v_pontual)}</b></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**Previsibilidade: {previsibilidade:.0f}%**")
        st.progress(previsibilidade/100)

    # --- 6. RESUMO FINAL ---
    st.markdown(f"""<div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top:20px;">
                No período selecionado, a operação gerou <span style="color:#00ff00;">{format_brl(rec_total)}</span> em receitas 
                e consumiu <span style="color:#ff4b4b;">{format_brl(desp_total)}</span> em despesas, 
                resultando em um saldo de <span style="color:{'#00ff00' if res_liquido > 0 else '#ff4b4b'};">{format_brl(res_liquido)}</span>.</div>""", unsafe_allow_html=True)
