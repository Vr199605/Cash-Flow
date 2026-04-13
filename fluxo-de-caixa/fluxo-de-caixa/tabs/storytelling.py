import pandas as pd
import streamlit as st

from config import COL_V, format_brl


def render(df, df_rec, df_raw, saidas_df, meses_sel: list):
    st.markdown("### 🧠 Inteligência Financeira e Storytelling")
    st.write("---")

    if not meses_sel:
        st.info("Selecione pelo menos um período no menu lateral para gerar o Storytelling.")
        return

    v_ent = df_rec[COL_V].sum()
    v_sai = abs(df[df[COL_V] < 0][COL_V].sum())
    lucro = v_ent - v_sai
    sobra_pct = (lucro / v_ent * 100) if v_ent > 0 else 0

    # --- Índice de retenção e variação de saída ---
    st.markdown("#### 📈 Comportamento do Fluxo")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style='background: rgba(30,41,59,0.8); padding: 20px; border-radius: 10px; border-left: 5px solid #00D1FF;'>
            <h4 style='margin:0; color:#00D1FF;'>Índice de Retenção</h4>
            <p style='font-size: 24px; font-weight: bold; margin:0;'>{sobra_pct:.1f}%</p>
            <p style='color: #94A3B8; font-size: 14px;'>
                De cada R$ 100,00 que entram,
                <b>{format_brl(max(0, sobra_pct))}</b> ficam no caixa após as despesas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if len(meses_sel) > 1:
            meses_ord = sorted(meses_sel, key=lambda x: pd.to_datetime(x, format='%m/%Y'))
            m_atual, m_ant = meses_ord[-1], meses_ord[-2]
            gasto_atual = abs(df_raw[df_raw['Mes_Ano'] == m_atual][COL_V].sum())
            gasto_ant = abs(df_raw[df_raw['Mes_Ano'] == m_ant][COL_V].sum())
            diff = gasto_atual - gasto_ant
            pct = (diff / gasto_ant * 100) if gasto_ant > 0 else 0
            cor = "#FF4B4B" if diff > 0 else "#00D1FF"
            st.markdown(f"""
            <div style='background: rgba(30,41,59,0.8); padding: 20px; border-radius: 10px; border-left: 5px solid {cor};'>
                <h4 style='margin:0; color:{cor};'>Variação de Saída</h4>
                <p style='font-size: 24px; font-weight: bold; margin:0;'>{pct:+.1f}%</p>
                <p style='color: #94A3B8; font-size: 14px;'>
                    O custo total variou <b>{format_brl(diff)}</b> em relação ao mês anterior ({m_ant}).
                </p>
            </div>
            """, unsafe_allow_html=True)

    # --- Recorrentes vs Pontuais ---
    st.write("")
    st.markdown("#### 🎯 Classificação de Gastos (Recorrentes vs Pontuais)")

    df_sai_raw = df_raw[df_raw[COL_V] < 0]
    count_meses = max(len(meses_sel), 1)
    recorrencia = (
        df_sai_raw[df_sai_raw['Mes_Ano'].isin(meses_sel)]
        .groupby('Categoria')['Mes_Ano'].nunique() / count_meses
    )
    pontuais = recorrencia[recorrencia <= 0.4].index.tolist()
    recorrentes = recorrencia[recorrencia > 0.4].index.tolist()

    val_pontuais = abs(df[df['Categoria'].isin(pontuais)][COL_V].sum())
    val_recorrentes = abs(df[df['Categoria'].isin(recorrentes)][COL_V].sum())

    cp1, cp2 = st.columns(2)
    with cp1:
        st.info(f"📋 **Gastos Pontuais:** {format_brl(val_pontuais)}")
        with st.expander("Ver categorias pontuais"):
            st.write(", ".join(pontuais) if pontuais else "Nenhuma detectada")
    with cp2:
        st.success(f"🔄 **Gastos Recorrentes:** {format_brl(val_recorrentes)}")
        with st.expander("Ver categorias recorrentes"):
            st.write(", ".join(recorrentes) if recorrentes else "Nenhuma detectada")

    # --- Anomalias ---
    st.write("")
    st.markdown("#### 🚨 Alertas de Anomalias (Desvios Acima de 15%)")

    if len(meses_sel) > 1:
        meses_ord = sorted(meses_sel, key=lambda x: pd.to_datetime(x, format='%m/%Y'))
        cats_atual = df[df[COL_V] < 0].groupby('Categoria')[COL_V].sum().abs()
        historico = (
            df_raw[(df_raw['Mes_Ano'] != meses_ord[-1]) & (df_raw[COL_V] < 0)]
            .groupby(['Mes_Ano', 'Categoria'])[COL_V].sum().abs().reset_index()
        )
        media_hist = historico.groupby('Categoria')[COL_V].mean()

        anomalias = []
        for cat, val in cats_atual.items():
            if cat in media_hist.index:
                media = media_hist[cat]
                if val > media * 1.15:
                    desvio = ((val / media) - 1) * 100
                    anomalias.append(
                        f"A categoria **{cat}** gastou **{format_brl(val)}** (+{desvio:.1f}% acima da média)."
                    )

        if anomalias:
            for a in anomalias:
                st.error(a)
        else:
            st.success("✅ Nenhuma anomalia de custo detectada em relação à média histórica.")

    # --- Explicação das variações ---
    st.write("")
    st.markdown("#### 🔍 Explicação das Variações")
    if not saidas_df.empty:
        maior_grupo = saidas_df.groupby('Grupo_Filtro')[COL_V].sum().abs().idxmax()
        maior_valor = saidas_df.groupby('Grupo_Filtro')[COL_V].sum().abs().max()
        pct_grupo = (maior_valor / v_sai * 100) if v_sai > 0 else 0
        st.warning(
            f"📌 **Concentração de Saída:** O grupo **{maior_grupo}** é o seu maior centro de custo, "
            f"representando **{pct_grupo:.1f}%** de todas as saídas."
        )
        if lucro < 0:
            st.error(
                f"🚨 **Alerta de Caixa:** As saídas superaram as entradas em **{format_brl(abs(lucro))}**. "
                f"Recomenda-se auditar as categorias do grupo {maior_grupo}."
            )
        else:
            st.success(
                f"💎 **Saúde Financeira:** A operação é sustentável, gerando um excedente de "
                f"**{format_brl(lucro)}** para reinvestimento."
            )
