import io
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, 
    Spacer, Table, TableStyle
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from config import COL_V, format_brl

def gerar_pdf_perfeito(df_sai, df_rec, meses: list, empresas_selecionadas: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
    )
    
    # --- PALETA E ESTILOS PREMIUM ---
    C_PRIMARIO = colors.HexColor("#00D1FF")
    C_SECUNDARIO = colors.HexColor("#0F172A")
    C_TEXTO = colors.HexColor("#334155")
    C_BG = colors.HexColor("#F8FAFC")

    st = getSampleStyleSheet()
    st_capa = ParagraphStyle('Capa', fontSize=34, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', alignment=1, spaceAfter=20)
    st_tit = ParagraphStyle('Tit', fontSize=22, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=12)
    st_h1 = ParagraphStyle('H1', fontSize=16, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10)
    st_sub_center = ParagraphStyle('SubC', fontSize=10, textColor=colors.HexColor("#64748B"), alignment=1, leading=14)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=C_TEXTO, leading=14, alignment=4)
    st_story = ParagraphStyle('Story', fontSize=11, textColor=C_SECUNDARIO, leading=16, leftIndent=20, rightIndent=20, borderPadding=15, backColor=C_BG, borderRadius=10)
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    # --- PÁGINA 1: CAPA IMPACTANTE ---
    elementos.append(Spacer(1, 100))
    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3.0 * inch, height=1.1 * inch)
        img.hAlign = 'CENTER'
        elementos.append(img)
    
    elementos.append(Spacer(1, 50))
    elementos.append(Paragraph("RELATÓRIO EXECUTIVO DE", st_sub_center))
    elementos.append(Paragraph("PERFORMANCE FINANCEIRA", st_capa))
    
    emp_str = " | ".join(sorted(empresas_selecionadas))
    elementos.append(Paragraph(f"<b>UNIDADES:</b> {emp_str.upper()}", st_sub_center))
    elementos.append(Paragraph(f"<b>PERÍODO:</b> {', '.join(meses)}", st_sub_center))
    
    elementos.append(Spacer(1, 150))
    elementos.append(HRFlowable(width="50%", thickness=1.5, color=C_PRIMARIO, hAlign='CENTER'))
    elementos.append(Paragraph(f"Emitido em: {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}", st_sub_center))
    elementos.append(PageBreak())

    # --- PÁGINA 2: STORYTELLING E DASHBOARD ---
    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    margem = (saldo / v_in * 100 if v_in > 0 else 0)

    elementos.append(Paragraph("01. VISÃO ESTRATÉGICA (STORYTELLING)", st_h1))
    
    tendencia = "positiva" if saldo > 0 else "de atenção"
    analise_texto = (
        f"A análise consolidada revela uma operação {tendencia}. Com receita total de {format_brl(v_in)} "
        f"e custo operacional de {format_brl(v_out)}, o resultado líquido é de {format_brl(saldo)}. "
        f"A margem de {margem:.2f}% reflete a eficiência atual da operação frente aos custos fixos e variáveis."
    )
    elementos.append(Paragraph(analise_texto, st_story))
    elementos.append(Spacer(1, 25))

    # Tabela de KPIs (Estilo Card)
    data_kpi = [
        [Paragraph("<b>RECEITA TOTAL</b>", st_body), Paragraph("<b>DESPESA TOTAL</b>", st_body)],
        [format_brl(v_in), format_brl(v_out)],
        [Paragraph("<b>RESULTADO LÍQUIDO</b>", st_body), Paragraph("<b>MARGEM OPERACIONAL</b>", st_body)],
        [format_brl(saldo), f"{margem:.2f}%"]
    ]
    t_kpi = Table(data_kpi, colWidths=[235, 235])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 16),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor("#15803D") if saldo > 0 else colors.red),
        ('GRID', (0, 0), (-1, -1), 2, colors.white),
    ]))
    elementos.append(t_kpi)

    # --- GRÁFICO DE PIZZA (DISTRIBUIÇÃO DE DESPESAS) ---
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("02. COMPOSIÇÃO DE INVESTIMENTOS POR GRUPO", st_h1))
    
    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index().sort_values(by=COL_V, ascending=False).head(5)
    
    d = Drawing(400, 200)
    pc = Pie()
    pc.x = 150
    pc.y = 50
    pc.width = 120
    pc.height = 120
    pc.data = df_g[COL_V].tolist()
    pc.labels = [f"{n[:15]}..." for n in df_g['Grupo_Filtro'].tolist()]
    pc.sideLabels = 1
    pc.slices.strokeWidth = 0.5
    pc.slices[0].fillColor = C_PRIMARIO
    pc.slices[1].fillColor = C_SECUNDARIO
    d.add(pc)
    elementos.append(d)

    # --- PÁGINA 3: TABELAS DETALHADAS ---
    elementos.append(PageBreak())
    elementos.append(Paragraph("03. FLUXO DE CAIXA MENSAL", st_h1))
    
    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['Net'] = df_burn['In'] - df_burn['Out']
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort')

    data_b = [["MÊS/ANO", "ENTRADAS", "SAÍDAS", "SALDO"]]
    for r in df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values:
        data_b.append([r[0], format_brl(r[1]), format_brl(r[2]), format_brl(r[3])])

    t_b = Table(data_b, colWidths=[115, 115, 115, 115])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_SECUNDARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG]),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.HexColor("#CBD5E1")),
    ]))
    elementos.append(t_b)

    if 'Nome' in df_rec.columns:
        elementos.append(Spacer(1, 30))
        elementos.append(Paragraph("04. CONCENTRAÇÃO DE RECEITA (TOP 10)", st_h1))
        df_n = df_rec.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10).reset_index()
        data_n = [["ORIGEM", "VALOR"]] + [[str(r[0])[:40], format_brl(r[1])] for r in df_n.values]
        t_n = Table(data_n, colWidths=[350, 120])
        t_n.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, C_PRIMARIO),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elementos.append(t_n)

    # RODAPÉ CONFIDENCIAL
    elementos.append(Spacer(1, 50))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Paragraph("RELATÓRIO GERADO AUTOMATICAMENTE - CONFIDENCIAL", st_footer))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
