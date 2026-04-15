import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import format_brl, COL_V

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    # --- 1. PROCESSAMENTO DE DADOS (CÁLCULOS MANTIDOS) ---
    rec_total = df_rec[COL_V].sum()
    desp_total = abs(saidas_df[COL_V].sum())
    res_liquido = rec_total - desp_total
    indice_custo = (desp_total / rec_total * 100) if rec_total != 0 else 0

    col_nome = next((c for c in ['Nome', 'Favorecido', 'Descricao'] if c in df_rec.columns), df_rec.columns[0])
    top_5_rec = df_rec.groupby(col_nome)[COL_V].sum().sort_values(ascending=False).head(5)
    perc_3 = (top_5_rec.head(3).sum() / rec_total * 100) if rec_total > 0 else 0

    lista_p = ["RESCISÃO", "BÔNUS", "JUROS", "MULTAS", "EVENTOS CLIENTES", "13º SALÁRIO", "ADIANTAMENTO"]
    df_pontuais = saidas_df[saidas_df['Categoria'].str.upper().str.contains('|'.join(lista_p), na=False)]
    df_recorrentes = saidas_df[~saidas_df.index.isin(df_pontuais.index)]
    v_pont = abs(df_pontuais[COL_V].sum())
    v_reco = abs(df_recorrentes[COL_V].sum())
    prev = (v_reco / (v_reco + v_pont) * 100) if (v_reco + v_pont) > 0 else 0

    # --- 2. CABEÇALHO ---
    st.markdown("### 🧠 STORYTELLING EXECUTIVO")
    st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")
    
    # --- GRÁFICO FLUXO (MANTIDO) ---
    df_m_rec = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index()
    df_m_sai = saidas_df.groupby('Mes_Ano')[COL_V].sum().abs().reset_index()
    df_m = pd.merge(df_m_rec, df_m_sai, on='Mes_Ano', suffixes=('_Ent', '_Sai'))
    df_m['Saldo'] = df_m[f'{COL_V}_Ent'] - df_m[f'{COL_V}_Sai']
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Ent'], name='Entradas', marker_color='#2ecc71'))
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Sai'], name='Saídas', marker_color='#e74c3c'))
    fig_flow.add_trace(go.Scatter(x=df_m['Mes_Ano'], y=df_m['Saldo'], name='Saldo', line=dict(color='#00D1FF', width=3), marker=dict(size=10)))
    fig_flow.update_layout(template="plotly_dark", barmode='group', height=350, margin=dict(t=20, b=20), hovermode="x unified")

    # --- GRÁFICO PARETO (MANTIDO COM CORES SEMÂNTICAS) ---
    df_p_data = saidas_df.groupby('Categoria')[COL_V].sum().abs().sort_values(ascending=False).head(10).reset_index()
    total_p = df_p_data[COL_V].sum()
    df_p_data['% Acumulada'] = (df_p_data[COL_V].cumsum() / total_p) * 100
    
    def define_cor_pareto(cat):
        if any(p in cat.upper() for p in lista_p):
            return "#ff4b4b"
        return "#00D1FF"

    df_p_data['Cor'] = df_p_data['Categoria'].apply(define_cor_pareto)

    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(x=df_p_data['Categoria'], y=df_p_data[COL_V], name='Valor (R$)', marker_color=df_p_data['Cor'], yaxis='y1'))
    fig_p.add_trace(go.Scatter(x=df_p_data['Categoria'], y=df_p_data['% Acumulada'], name='% Acumulada', line=dict(color='#f1c40f', width=3), yaxis='y2'))
    fig_p.update_layout(
        template="plotly_dark", height=400, showlegend=True,
        yaxis=dict(title="Valor (R$)", side="left", showgrid=False),
        yaxis2=dict(title="Porcentagem (%)", side="right", overlaying="y", range=[0, 110], showgrid=False),
        margin=dict(t=50, b=50), hovermode="x unified"
    )

    # --- 3. INDICADOR DE SAÚDE ---
    st.write("---")
    margem_calc = (res_liquido / rec_total) if rec_total > 0 else 0
    pontos_saude = int(max(0, min(100, margem_calc * 100))) if res_liquido > 0 else 0
    
    if pontos_saude > 70:
        cor_saude = "#2ecc71"; status_saude = "Excelente"; desc_saude = "Operação com margem sólida e custos controlados."
    elif pontos_saude > 0:
        cor_saude = "#f1c40f"; status_saude = "Atenção"; desc_saude = "Margem positiva, porém estreita. Requer monitoramento."
    else:
        cor_saude = "#ff4b4b"; status_saude = "Crítico"; desc_saude = "Recuo em margem líquida, variação de custos e déficit operacional detectado."

    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        st.markdown(f"""<div style="text-align: center; border: 2px solid {cor_saude}; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; margin: auto;">
            <span style="font-size: 24px; font-weight: bold; color: {cor_saude};">{pontos_saude}</span></div>
            <p style="text-align: center; margin-top: 5px; font-size: 10px; color: #aaa;">PONTOS</p>""", unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"<h4 style='color: {cor_saude}; margin-bottom: 0;'>{status_saude}</h4>", unsafe_allow_html=True)
        st.write(desc_saude)

    # --- 4. KPI CARDS (MANTIDO) ---
    c1, c2, c3, c4 = st.columns(4)
    labels = ["RECEITA TOTAL", "DESPESA TOTAL", "RESULTADO LÍQUIDO", "CUSTO / RECEITA"]
    valores = [rec_total, desp_total, res_liquido, indice_custo]
    cores = ["#2ecc71", "#e74c3c", "#95a5a6", "#f1c40f"]

    for col, lab, val, cor in zip([c1, c2, c3, c4], labels, valores, cores):
        if lab == "RESULTADO LÍQUIDO":
            v_color = "#ff4b4b" if val < 0 else "#2ecc71"
            v_border = "#ff4b4b" if val < 0 else "#95a5a6"
            margem = (val / rec_total * 100) if rec_total > 0 else 0
            observacao_html = f"""<p style='margin:0; font-size: 11px; color: #aaa; margin-top: 5px;'>
                                <span style='color: #e74c3c;'>➘</span> Margem de {margem:.1f}% sobre a receita</p>""" if val < 0 else ""
            col.markdown(f"""<div style="border: 1px solid {v_border}; padding: 15px; border-radius: 10px;">
                         <p style="margin:0; font-size: 10px; color: {v_color}; font-weight: bold;">● {lab}</p>
                         <h3 style="margin:0; font-size: 18px; color: {v_color};">{format_brl(val)}</h3>
                         {observacao_html}</div>""", unsafe_allow_html=True)
        else:
            v_str = f"{val:.1f}%" if lab == "CUSTO / RECEITA" else format_brl(val)
            col.markdown(f"""<div style="border: 1px solid {cor}; padding: 15px; border-radius: 10px;">
                         <p style="margin:0; font-size: 10px; color: {cor}; font-weight: bold;">● {lab}</p>
                         <h3 style="margin:0; font-size: 18px;">{v_str}</h3></div>""", unsafe_allow_html=True)

    # --- NOVO: 4.1 DECOMPOSIÇÃO DE MARGEM (EBITDA SIMULADO) ---
    st.write("")
    with st.container(border=True):
        st.markdown("##### 📊 Eficiência Operacional (EBITDA Simulado)")
        m_col1, m_col2, m_col3 = st.columns(3)
        
        # Cálculos de Margem de Contribuição
        margem_contribuicao = rec_total - v_pont
        percentual_mc = (margem_contribuicao / rec_total * 100) if rec_total > 0 else 0
        ebitda_margem = (res_liquido / rec_total * 100) if rec_total > 0 else 0

        m_col1.metric("Margem de Contribuição", format_brl(margem_contribuicao), f"{percentual_mc:.1f}%")
        m_col2.metric("Custos Fixos (Recorrentes)", format_brl(v_reco), delta_color="off")
        m_col3.metric("Margem Líquida (EBITDA %)", f"{ebitda_margem:.1f}%", delta=f"{ebitda_margem:.1f}%", help="Resultado final sobre a receita bruta.")
        
        st.caption("A Margem de Contribuição indica quanto sobra da receita após pagar os custos variáveis (pontuais) para cobrir os custos fixos.")

    # --- 5. GRÁFICOS INTERATIVOS NA TELA (MANTIDO) ---
    st.markdown("#### 📉 Evolução do Fluxo de Caixa")
    st.plotly_chart(fig_flow, use_container_width=True)

    st.markdown("#### 🎯 Análise de Pareto — Top 10 Despesas")
    st.plotly_chart(fig_p, use_container_width=True)

    # --- 6. CONCENTRAÇÃO DE RECEITA (MANTIDO) ---
    st.markdown("#### 👁️ Concentração de Receita")
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
        st.markdown(f"**Índice de Concentração**")
        st.title(f"{perc_3:.1f}%")
        st.caption("Percentual da receita concentrado nos 3 maiores pagadores.")
        st.success("✅ Baixo Risco: Base de receita diversificada.")

    # --- 7. ESTRUTURA DE CUSTOS (MANTIDO) ---
    st.markdown("#### ⚡ Estrutura de Custos")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        with st.container(border=True):
            st.caption("RECORRENTES"); st.subheader(format_brl(v_reco))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_recorrentes['Categoria'].nunique()} categorias</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"): st.write(", ".join(sorted(df_recorrentes['Categoria'].unique())))
    with col_e2:
        with st.container(border=True):
            st.caption("PONTUAIS"); st.subheader(format_brl(v_pont))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_pontuais['Categoria'].nunique()} categorias</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"): st.write(", ".join(sorted(df_pontuais['Categoria'].unique())))
    with col_e3:
        with st.container(border=True):
            st.caption("PREVISIBILIDADE"); st.subheader(f"{prev:.0f}%"); st.progress(prev/100)

    # --- 8. RESUMO FINAL E GRÁFICO WATERFALL (MANTIDO) ---
    st.markdown(f"""<div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top:20px;">
                <span style="color: #ff4b4b; font-weight: bold;">📢 RESUMO PARA A DIRETORIA</span><br>
                No período selecionado, a operação gerou <span style="color:#2ecc71;">{format_brl(rec_total)}</span> em receitas 
                e consumiu <span style="color:#e74c3c;">{format_brl(desp_total)}</span> em despesas, resultando em um 
                déficit de <span style="color:#e74c3c;">{format_brl(abs(res_liquido))}</span>.</div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 📉 Gráfico de Cascata — Consumo da Receita")
    
    df_waterfall = saidas_df.groupby('Categoria')[COL_V].sum().abs().sort_values(ascending=False)
    top_5_despesas_indices = df_waterfall.head(5).index
    df_top_5 = df_waterfall.loc[top_5_despesas_indices]
    valor_outros = df_waterfall.drop(top_5_despesas_indices).sum()
    
    wf_x = ["Receita Total"] + list(df_top_5.index) + ["Outros"] + ["Resultado Líquido"]
    wf_y = [rec_total] + list(-df_top_5) + [-valor_outros] + [res_liquido]
    wf_measure = ["relative"] + ["relative"] * (len(df_top_5) + 1) + ["total"]
    wf_text = [format_brl(val) for val in wf_y]

    fig_wf = go.Figure(go.Waterfall(
        name="Fluxo de Caixa", orientation="v", measure=wf_measure, x=wf_x, y=wf_y, text=wf_text,
        textposition="outside", connector={"line": {"color": "rgba(255, 255, 255, 0.2)"}},
        increasing={"marker": {"color": "#2ecc71"}}, decreasing={"marker": {"color": "#e74c3c"}},
        totals={"marker": {"color": "#00D1FF"}}
    ))
    
    fig_wf.update_layout(template="plotly_dark", height=400, margin=dict(t=50, b=50), showlegend=False, hovermode="x unified")
    st.plotly_chart(fig_wf, use_container_width=True)

    with st.container(border=True):
        st.markdown("""
        <div style="padding: 10px;">
            <h5 style="color: #00D1FF; margin-bottom: 15px;">🔍 Entendendo a Análise de Cascata</h5>
            <p style="font-size: 14px; line-height: 1.6;">
                Este gráfico ilustra a <b>jornada do seu capital</b> desde a entrada bruta até o saldo final. Diferente de um gráfico comum, ele isola o impacto individual de cada grande grupo de custo:
            </p>
            <ul style="font-size: 13px; color: #ccc;">
                <li><b style="color: #2ecc71;">Coluna Verde (Início):</b> Representa 100% da sua Receita Gerada no período.</li>
                <li><b style="color: #e74c3c;">Degraus Vermelhos:</b> Mostram exatamente quanto cada categoria "subtraiu" da sua receita, em ordem de relevância.</li>
                <li><b style="color: #00D1FF;">Coluna Azul (Final):</b> É o que restou (Resultado Líquido).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
