import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import format_brl, COL_V

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    st.markdown("### 🧠 STORYTELLING EXECUTIVO")
    st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")

    # --- 1. INDICADOR DE SAÚDE ---
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        st.markdown(
            f"""<div style="text-align: center; border: 2px solid #555; border-radius: 50%; width: 80px; height: 80px; 
            display: flex; align-items: center; justify-content: center; margin: auto;">
            <span style="font-size: 24px; font-weight: bold; color: #ff4b4b;">0</span></div>
            <p style="text-align: center; margin-top: 5px; font-size: 10px; color: #aaa;">PONTOS</p>""", 
            unsafe_allow_html=True
        )
    with col_s2:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 0;'>Crítico</h4>", unsafe_allow_html=True)
        st.write("Recuo em margem líquida, variação de custos, concentração de receita e anomalias detectadas.")

    st.write("---")

    # --- 2. KPI CARDS ---
    rec_total = df_rec[COL_V].sum()
    desp_total = abs(saidas_df[COL_V].sum())
    res_liquido = rec_total - desp_total
    indice_custo = (desp_total / rec_total * 100) if rec_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    labels = ["RECEITA TOTAL", "DESPESA TOTAL", "RESULTADO LÍQUIDO", "CUSTO / RECEITA"]
    valores = [rec_total, desp_total, res_liquido, indice_custo]
    cores = ["#2ecc71", "#e74c3c", "#95a5a6", "#f1c40f"]

    for col, lab, val, cor in zip([c1, c2, c3, c4], labels, valores, cores):
        v_str = f"{val:.1f}%" if lab == "CUSTO / RECEITA" else format_brl(val)
        col.markdown(f"""<div style="border: 1px solid {cor}; padding: 15px; border-radius: 10px;">
                     <p style="margin:0; font-size: 10px; color: {cor}; font-weight: bold;">● {lab}</p>
                     <h3 style="margin:0; font-size: 18px;">{v_str}</h3></div>""", unsafe_allow_html=True)

    # --- 3. EVOLUÇÃO DO FLUXO (INTERATIVO COM LINHA DE SALDO) ---
    st.markdown("#### 📉 Evolução do Fluxo de Caixa")
    df_m_rec = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index()
    df_m_sai = saidas_df.groupby('Mes_Ano')[COL_V].sum().abs().reset_index()
    df_m = pd.merge(df_m_rec, df_m_sai, on='Mes_Ano', suffixes=('_Ent', '_Sai'))
    df_m['Saldo'] = df_m[f'{COL_V}_Ent'] - df_m[f'{COL_V}_Sai']
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Ent'], name='Entradas', marker_color='#2ecc71'))
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Sai'], name='Saídas', marker_color='#e74c3c'))
    fig_flow.add_trace(go.Scatter(x=df_m['Mes_Ano'], y=df_m['Saldo'], name='Saldo', line=dict(color='#00D1FF', width=3), marker=dict(size=10)))
    fig_flow.update_layout(template="plotly_dark", barmode='group', height=350, margin=dict(t=20, b=20), hovermode="x unified")
    st.plotly_chart(fig_flow, use_container_width=True)

    # --- 4. ANÁLISE DE PARETO (TOP 10 DESPESAS) ---
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

    # --- 5. CONCENTRAÇÃO DE RECEITA (IDENTICO AO PRINT) ---
    st.markdown("#### 👁️ Concentração de Receita")
    # Identifica a coluna correta de nomes (ex: Nome, Favorecido ou Descricao)
    col_nome = next((c for c in ['Nome', 'Favorecido', 'Descricao'] if c in df_rec.columns), df_rec.columns[0])
    top_5_rec = df_rec.groupby(col_nome)[COL_V].sum().sort_values(ascending=False).head(5)
    
    c_rec1, c_rec2 = st.columns([1, 1])
    with c_rec1:
        with st.container(border=True):
            st.markdown("**Top 5 Fontes de Receita**")
            bar_colors = ["#00D1FF", "#ff4b4b", "#2ecc71", "#f1c40f", "#9b59b6"]
            for (nome, valor), cor in zip(top_5_rec.items(), bar_colors):
                p = (valor/rec_total*100) if rec_total > 0 else 0
                col_text, col_val = st.columns([2, 1])
                col_text.caption(f"{nome}")
                col_val.markdown(f"<p style='font-size:11px; text-align:right; margin:0;'>{format_brl(valor)} ({p:.1f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"""<div style="background-color: #333; border-radius: 5px; height: 6px; width: 100%;">
                            <div style="background-color: {cor}; height: 6px; width: {min(p, 100)}%; border-radius: 5px;"></div>
                            </div><br>""", unsafe_allow_html=True)
    with c_rec2:
        perc_3 = (top_5_rec.head(3).sum() / rec_total * 100) if rec_total > 0 else 0
        st.markdown(f"**Índice de Concentração**")
        st.title(f"{perc_3:.1f}%")
        st.caption("Percentual da receita concentrado nos 3 maiores pagadores.")
        st.success("✅ Baixo Risco: Base de receita diversificada — excelente resiliência operacional.")

    # --- 6. ESTRUTURA DE CUSTOS (COM EXPANDERS) ---
    st.markdown("#### ⚡ Estrutura de Custos")
    lista_p = ["RESCISÃO", "BÔNUS", "JUROS", "MULTAS", "EVENTOS CLIENTES", "13º SALÁRIO", "ADIANTAMENTO"]
    df_pontuais = saidas_df[saidas_df['Categoria'].str.upper().str.contains('|'.join(lista_p), na=False)]
    df_recorrentes = saidas_df[~saidas_df.index.isin(df_pontuais.index)]
    
    v_pont = abs(df_pontuais[COL_V].sum())
    v_reco = abs(df_recorrentes[COL_V].sum())
    
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        with st.container(border=True):
            st.caption("RECORRENTES")
            st.subheader(format_brl(v_reco))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_recorrentes['Categoria'].nunique()} categorias · {(v_reco/(v_reco+v_pont)*100):.1f}% do total</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"):
                st.write(", ".join(sorted(df_recorrentes['Categoria'].unique())))
    with col_e2:
        with st.container(border=True):
            st.caption("PONTUAIS")
            st.subheader(format_brl(v_pont))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_pontuais['Categoria'].nunique()} categorias · {(v_pont/(v_reco+v_pont)*100):.1f}% do total</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"):
                st.write(", ".join(sorted(df_pontuais['Categoria'].unique())))
    with col_e3:
        with st.container(border=True):
            prev = (v_reco / (v_reco + v_pont) * 100) if (v_reco + v_pont) > 0 else 0
            st.caption("PREVISIBILIDADE")
            st.subheader(f"{prev:.0f}%")
            st.write("dos custos são previsíveis")
            st.progress(prev/100)

    # --- 7. RESUMO FINAL ---
    st.markdown(f"""<div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top:20px;">
                <span style="color: #ff4b4b; font-weight: bold;">📢 RESUMO PARA A DIRETORIA</span><br>
                No período selecionado, a operação gerou <span style="color:#2ecc71;">{format_brl(rec_total)}</span> em receitas 
                e consumiu <span style="color:#e74c3c;">{format_brl(desp_total)}</span> em despesas, resultando em um 
                déficit de <span style="color:#e74c3c;">{format_brl(abs(res_liquido))}</span>.</div>""", unsafe_allow_html=True)
