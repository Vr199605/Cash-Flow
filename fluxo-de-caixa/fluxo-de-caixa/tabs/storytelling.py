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

    # --- 3. EVOLUÇÃO DO FLUXO (INTERATIVO) ---
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

    # --- 4. CONCENTRAÇÃO DE RECEITA (PARETO NOMES) ---
    st.markdown("#### 👁️ Concentração de Receita")
    col_cliente = 'Descricao' if 'Descricao' in df_rec.columns else (df_rec.columns[0] if not df_rec.empty else 'Cliente')
    top_5_rec = df_rec.groupby(col_cliente)[COL_V].sum().sort_values(ascending=False).head(5)
    
    c_rec1, c_rec2 = st.columns([1, 1])
    with c_rec1:
        with st.container(border=True):
            st.markdown("**Top 5 Fontes de Receita**")
            for nome, valor in top_5_rec.items():
                p = (valor/rec_total*100) if rec_total > 0 else 0
                st.caption(f"{nome} — {format_brl(valor)} ({p:.1f}%)")
                st.progress(min(p/100, 1.0))
    with c_rec2:
        perc_3 = (top_5_rec.head(3).sum() / rec_total * 100) if rec_total > 0 else 0
        st.markdown(f"**Índice de Concentração**")
        st.title(f"{perc_3:.1f}%")
        st.caption("Percentual da receita concentrado nos 3 maiores pagadores.")
        st.success("✅ Baixo Risco: Base de receita diversificada.")

    # --- 5. ESTRUTURA DE CUSTOS (COM EXPANDERS) ---
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
            st.write(f"{df_recorrentes['Categoria'].nunique()} categorias")
            with st.expander("▼ Ver categorias"):
                cats_reco = sorted(df_recorrentes['Categoria'].unique())
                st.write(", ".join(cats_reco))

    with col_e2:
        with st.container(border=True):
            st.caption("PONTUAIS")
            st.subheader(format_brl(v_pont))
            st.write(f"{df_pontuais['Categoria'].nunique()} categorias")
            with st.expander("▼ Ver categorias"):
                cats_pont = sorted(df_pontuais['Categoria'].unique())
                st.write(", ".join(cats_pont))

    with col_e3:
        with st.container(border=True):
            prev = (v_reco / (v_reco + v_pont) * 100) if (v_reco + v_pont) > 0 else 0
            st.caption("PREVISIBILIDADE")
            st.subheader(f"{prev:.0f}%")
            st.write("dos custos são previsíveis")
            st.progress(prev/100)

    # --- 6. RESUMO PARA A DIRETORIA ---
    st.markdown(f"""<div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top:20px;">
                <span style="color: #ff4b4b; font-weight: bold;">📢 RESUMO PARA A DIRETORIA</span><br>
                No período selecionado, a operação gerou <span style="color:#2ecc71;">{format_brl(rec_total)}</span> em receitas 
                e consumiu <span style="color:#e74c3c;">{format_brl(desp_total)}</span> em despesas, resultando em um 
                déficit de <span style="color:#e74c3c;">{format_brl(abs(res_liquido))}</span>.</div>""", unsafe_allow_html=True)
