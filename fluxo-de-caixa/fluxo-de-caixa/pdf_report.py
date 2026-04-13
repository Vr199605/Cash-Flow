import io
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import COL_V, format_brl


def gerar_pdf_perfeito(df_sai, df_rec, meses: list, empresas_selecionadas: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
    )
    getSampleStyleSheet()

    st_tit = ParagraphStyle('Tit', fontSize=24, textColor=colors.HexColor("#00D1FF"), fontName='Helvetica-Bold', spaceAfter=14)
    st_sub = ParagraphStyle('Sub', fontSize=9, textColor=colors.HexColor("#64748B"), spaceAfter=20)
    st_h1 = ParagraphStyle('H1', fontSize=14, textColor=colors.HexColor("#1E293B"), fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=10)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=colors.HexColor("#334155"), leading=14, alignment=4)
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.5 * inch, height=1.0 * inch)
        img.hAlign = 'LEFT'
        elementos.append(img)
        elementos.append(Spacer(1, 12))

    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    nome_exibicao = "+".join(sorted(empresas_selecionadas))

    elementos.append(Paragraph(f"RELATÓRIO FINANCEIRO - {nome_exibicao.upper()}", st_tit))
    elementos.append(Paragraph(
        f"Consolidado: {', '.join(meses)}  |  Emissão: {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        st_sub,
    ))
    elementos.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#00D1FF"), spaceAfter=20))

    elementos.append(Paragraph("Objetivo e Metodologia", st_h1))
    elementos.append(Paragraph(
        "Este relatório apresenta a saúde financeira detalhada da operação. Os dados foram processados "
        "através de conexões dinâmicas, garantindo que cada entrada e saída seja categorizada para "
        "análise de Pareto e eficiência operacional.",
        st_body,
    ))

    # I. KPIs
    elementos.append(Paragraph("I. PERFORMANCE DE LIQUIDEZ", st_h1))
    data_kpi = [
        ["MÉTRICA", "VALOR"],
        ["(+) TOTAL RECEBIMENTOS", format_brl(v_in)],
        ["(-) TOTAL DESPESAS", format_brl(v_out)],
        ["(=) RESULTADO LÍQUIDO", format_brl(saldo)],
        ["MARGEM SOBRE RECEITA", f"{(saldo / v_in * 100 if v_in > 0 else 0):.2f}%"],
    ]
    t_kpi = Table(data_kpi, colWidths=[300, 150])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0, 3), (1, 3), colors.HexColor("#F1F5F9")),
        ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
    ]))
    elementos.append(t_kpi)

    # II. Fluxo mensal
    elementos.append(Paragraph("II. FLUXO MENSAL DETALHADO", st_h1))
    elementos.append(Paragraph(
        "Acompanhamento do resultado líquido mensal (In vs Out) para identificação de gaps de caixa.",
        st_body,
    ))

    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['Net'] = df_burn['In'] - df_burn['Out']
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort')

    data_b = [["MÊS/ANO", "ENTRADAS (+)", "SAÍDAS (-)", "SALDO LÍQUIDO"]]
    for row in df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values:
        data_b.append([row[0], format_brl(row[1]), format_brl(row[2]), format_brl(row[3])])

    t_b = Table(data_b, colWidths=[110, 110, 110, 120])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    for i, row in enumerate(df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values):
        cor = colors.red if row[3] < 0 else colors.HexColor("#008000")
        t_b.setStyle(TableStyle([('TEXTCOLOR', (3, i + 1), (3, i + 1), cor)]))
    elementos.append(t_b)

    # III. Grupos
    elementos.append(PageBreak())
    elementos.append(Paragraph("III. ANÁLISE DE IMPACTO POR GRUPO", st_h1))
    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index()
    data_g = [["GRUPO", "VALOR TOTAL", "IMPACTO NA RECEITA"]]
    for row in df_g.values:
        impacto = (row[1] / v_in * 100) if v_in > 0 else 0
        data_g.append([str(row[0]), format_brl(row[1]), f"{impacto:.1f}%"])
    t_g = Table(data_g, colWidths=[200, 125, 125])
    t_g.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elementos.append(t_g)

    # IV. Top 10 recebimentos
    if 'Nome' in df_rec.columns:
        elementos.append(Paragraph("IV. CONCENTRAÇÃO DE RECEBIMENTOS (TOP 10)", st_h1))
        df_n = df_rec.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10).reset_index()
        data_n = [["ORIGEM / NOME", "VALOR"]] + [[str(r[0]), format_brl(r[1])] for r in df_n.values]
        t_n = Table(data_n, colWidths=[320, 130])
        t_n.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00D1FF")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elementos.append(t_n)

    elementos.append(Spacer(1, 50))
    elementos.append(Paragraph(
        "--- Documento Gerado para Fins de Auditoria e Decisão Estratégica ---",
        st_footer,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
