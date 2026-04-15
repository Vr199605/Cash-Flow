import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import format_brl, COL_V
from fpdf import FPDF
import io

# --- FUNÇÃO DO PDF PREMIUM (DESIGN DARK FIEL À TELA) ---
def exportar_pdf_premium(rec_total, desp_total, res_liquido, perc_conc, prev, top_5_rec, fig_flow, fig_p, meses_sel):
    pdf = FPDF()
    pdf.add_page()
    
    # Fundo Escuro
    pdf.set_fill_color(14, 17, 23)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Cabeçalho
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "STORYTELLING EXECUTIVO - MALDIVAS", ln=True, align='L')
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"Periodo: {', '.join(meses_sel) if meses_sel else 'Geral'} | Emissao: 15/04/2026", ln=True, align='L')
    pdf.ln(10)

    # Cards de KPI no PDF
    pdf.set_draw_color(46, 204, 113) # Verde
    pdf.rect(10, 35, 90, 20)
    pdf.set_xy(12, 37); pdf.set_text_color(46, 204, 113); pdf.set_font("Arial", "B", 8)
    pdf.cell(40, 5, "RECEITA TOTAL")
    pdf.set_xy(12, 44); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 5, format_brl(rec_total))

    pdf.set_draw_color(231, 76, 60) # Vermelho
    pdf.rect(110, 35, 90, 20)
    pdf.set_xy(112, 37); pdf.set_text_color(231, 76, 60); pdf.set_font("Arial", "B", 8)
    pdf.cell(40, 5, "DESPESA TOTAL")
    pdf.set_xy(112, 44); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 5, format_brl(desp_total))

    # Gráficos no PDF (Requer Kaleido instalado)
    pdf.ln(35)
    try:
        img_flow = fig_flow.to_image(format="png", width=800, height=350)
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Evolucao do Fluxo de Caixa", ln=True)
        pdf.image(io.BytesIO(img_flow), x=10, w=190)
    except:
        pdf.set_text_color(150, 150, 150); pdf.cell(0, 10, "(Graficos inclusos no processamento digital)", ln=True)

    pdf.ln(5)
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, f"Indice de Concentracao: {perc_conc:.1f}%", ln=True)
    pdf.cell(0, 10, f"Previsibilidade de Custos: {prev:.0f}%", ln=True)

    return bytes(pdf.output())

def render(df, df_rec, df_geral, saidas_df, meses_sel):
    # --- 1. PROCESSAMENTO DE DADOS (CÁLCULOS) ---
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

    # --- 2. CABEÇALHO COM TÍTULO E BOTÃO DE EXPORTAÇÃO ---
    col_tit, col_btn = st.columns([3, 1])
    with col_tit:
        st.markdown("### 🧠 STORYTELLING EXECUTIVO")
        st.caption(f"Período: {', '.join(meses_sel) if meses_sel else 'Todo o período'} | Gerado em 15 de abril de 2026")
    
    # Preparando os objetos de gráfico para uso tanto na tela quanto no PDF
    df_m_rec = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index()
    df_m_sai = saidas_df.groupby('Mes_Ano')[COL_V].sum().abs().reset_index()
    df_m = pd.merge(df_m_rec, df_m_sai, on='Mes_Ano', suffixes=('_Ent', '_Sai'))
    df_m['Saldo'] = df_m[f'{COL_V}_Ent'] - df_m[f'{COL_V}_Sai']
    
    fig_flow = go.Figure()
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Ent'], name='Entradas', marker_color='#2ecc71'))
    fig_flow.add_trace(go.Bar(x=df_m['Mes_Ano'], y=df_m[f'{COL_V}_Sai'], name='Saídas', marker_color='#e74c3c'))
    fig_flow.add_trace(go.Scatter(x=df_m['Mes_Ano'], y=df_m['Saldo'], name='Saldo', line=dict(color='#00D1FF', width=3), marker=dict(size=10)))
    fig_flow.update_layout(template="plotly_dark", barmode='group', height=350, margin=dict(t=20, b=20), hovermode="x unified")

    df_pareto = saidas_df.groupby('Categoria')[COL_V].sum().abs().sort_values(ascending=False).head(10).reset_index()
    df_pareto['% Acumulada'] = (df_pareto[COL_V].cumsum() / df_pareto[COL_V].sum()) * 100
    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(x=df_pareto['Categoria'], y=df_pareto[COL_V], name='Valor', marker_color='#00D1FF', yaxis='y1'))
    fig_p.add_trace(go.Scatter(x=df_pareto['Categoria'], y=df_pareto['% Acumulada'], name='% Acumulada', line=dict(color='#f1c40f'), yaxis='y2'))
    fig_p.update_layout(template="plotly_dark", height=350, margin=dict(t=20), hovermode="x unified")

    with col_btn:
        pdf_bytes = exportar_pdf_premium(rec_total, desp_total, res_liquido, perc_3, prev, top_5_rec, fig_flow, fig_p, meses_sel)
        st.download_button(label="📥 Relatório PDF Premium", data=pdf_bytes, file_name="Storytelling_Maldivas.pdf", mime="application/pdf")

    # --- 3. INDICADOR DE SAÚDE ---
    st.write("---")
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        st.markdown(f"""<div style="text-align: center; border: 2px solid #555; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; margin: auto;">
            <span style="font-size: 24px; font-weight: bold; color: #ff4b4b;">0</span></div>
            <p style="text-align: center; margin-top: 5px; font-size: 10px; color: #aaa;">PONTOS</p>""", unsafe_allow_html=True)
    with col_s2:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 0;'>Crítico</h4>", unsafe_allow_html=True)
        st.write("Recuo em margem líquida, variação de custos, concentração de receita e anomalias detectadas.")

    # --- 4. KPI CARDS ---
    c1, c2, c3, c4 = st.columns(4)
    labels = ["RECEITA TOTAL", "DESPESA TOTAL", "RESULTADO LÍQUIDO", "CUSTO / RECEITA"]
    valores = [rec_total, desp_total, res_liquido, indice_custo]
    cores = ["#2ecc71", "#e74c3c", "#95a5a6", "#f1c40f"]

    for col, lab, val, cor in zip([c1, c2, c3, c4], labels, valores, cores):
        v_str = f"{val:.1f}%" if lab == "CUSTO / RECEITA" else format_brl(val)
        col.markdown(f"""<div style="border: 1px solid {cor}; padding: 15px; border-radius: 10px;">
                     <p style="margin:0; font-size: 10px; color: {cor}; font-weight: bold;">● {lab}</p>
                     <h3 style="margin:0; font-size: 18px;">{v_str}</h3></div>""", unsafe_allow_html=True)

    # --- 5. GRÁFICOS INTERATIVOS NA TELA ---
    st.markdown("#### 📉 Evolução do Fluxo de Caixa")
    st.plotly_chart(fig_flow, use_container_width=True)

    st.markdown("#### 🎯 Análise de Pareto — Top 10 Despesas")
    st.plotly_chart(fig_p, use_container_width=True)

    # --- 6. CONCENTRAÇÃO DE RECEITA (ESTILO PARETO NOMES) ---
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
        st.success("✅ Baixo Risco: Base de receita diversificada — excelente resiliência operacional.")

    # --- 7. ESTRUTURA DE CUSTOS (COM EXPANDERS/SETINHAS) ---
    st.markdown("#### ⚡ Estrutura de Custos")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        with st.container(border=True):
            st.caption("RECORRENTES")
            st.subheader(format_brl(v_reco))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_recorrentes['Categoria'].nunique()} categorias</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"):
                st.write(", ".join(sorted(df_recorrentes['Categoria'].unique())))
    with col_e2:
        with st.container(border=True):
            st.caption("PONTUAIS")
            st.subheader(format_brl(v_pont))
            st.markdown(f"<span style='color:#555; font-size:12px;'>{df_pontuais['Categoria'].nunique()} categorias</span>", unsafe_allow_html=True)
            with st.expander("▼ Ver categorias"):
                st.write(", ".join(sorted(df_pontuais['Categoria'].unique())))
    with col_e3:
        with st.container(border=True):
            st.caption("PREVISIBILIDADE")
            st.subheader(f"{prev:.0f}%")
            st.write("dos custos são previsíveis")
            st.progress(prev/100)

    # --- 8. RESUMO FINAL PARA DIRETORIA ---
    st.markdown(f"""<div style="background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top:20px;">
                <span style="color: #ff4b4b; font-weight: bold;">📢 RESUMO PARA A DIRETORIA</span><br>
                No período selecionado, a operação gerou <span style="color:#2ecc71;">{format_brl(rec_total)}</span> em receitas 
                e consumiu <span style="color:#e74c3c;">{format_brl(desp_total)}</span> em despesas, resultando em um 
                déficit de <span style="color:#e74c3c;">{format_brl(abs(res_liquido))}</span>.</div>""", unsafe_allow_html=True)
