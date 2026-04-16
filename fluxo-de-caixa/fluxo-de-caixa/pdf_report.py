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
from reportlab.graphics.legends import Legend

from config import COL_V, format_brl

def gerar_pdf_perfeito(df_sai, df_rec, meses: list, empresas_selecionadas: list) -> io.BytesIO:
    buffer = io.BytesIO()
    # Definimos margens amplas para garantir que nada fique "por cima" de nada
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50,
    )
    
    # --- CORES CORPORATIVAS ---
    C_PRIMARIO = colors.HexColor("#00D1FF")
    C_SECUNDARIO = colors.HexColor("#0F172A")
    C_TEXTO = colors.HexColor("#334155")
    C_BG = colors.HexColor("#F8FAFC")

    # --- ESTILOS REFINADOS ---
    st = getSampleStyleSheet()
    st_capa = ParagraphStyle('Capa', fontSize=36, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', alignment=1, spaceAfter=30)
    st_h1 = ParagraphStyle('H1', fontSize=18, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceBefore=25, spaceAfter=15)
    st_sub_center = ParagraphStyle('SubC', fontSize=11, textColor=colors.HexColor("#64748B"), alignment=1, leading=16)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=C_TEXTO, leading=14)
    st_story = ParagraphStyle('Story', fontSize=11, textColor=C_SECUNDARIO, leading=18, leftIndent=25, rightIndent=25, borderPadding=20, backColor=colors.white, borderSize=1, borderColor=colors.HexColor("#E2E8F0"))
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    # --- PÁGINA 1: CAPA IMPACTANTE ---
    elementos.append(Spacer(1, 120))
    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3.2 * inch, height=1.2 * inch)
        img.hAlign = 'CENTER'
        elementos.append(img)
    
    elementos.append(Spacer(1, 60))
    elementos.append(Paragraph("RELATÓRIO DE INTELIGÊNCIA FINANCEIRA", st_sub_center))
    elementos.append(Paragraph("PERFORMANCE EXECUTIVA", st_capa))
    
    emp_str = " + ".join(sorted(empresas_selecionadas))
    elementos.append(Paragraph(f"<b>UNIDADES:</b> {emp_str.upper()}", st_sub_center))
    elementos.append(Paragraph(f"<b>PERÍODO:</b> {', '.join(meses)}", st_sub_center))
    
    elementos.append(Spacer(1, 180))
    elementos.append(HRFlowable(width="40%", thickness=2, color=C_PRIMARIO, hAlign='CENTER'))
    elementos.append(Paragraph(f"Data de Emissão: {pd.Timestamp.now().strftime('%d/%m/%Y')}", st_sub_center))
    elementos.append(PageBreak())

    # --- PÁGINA 2: STORYTELLING E DASHBOARD ---
    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    margem = (saldo / v_in * 100 if v_in > 0 else 0)

    elementos.append(Paragraph("01. ANÁLISE ESTRATÉGICA (STORYTELLING)", st_h1))
    
    # Texto baseado no resultado real
    tendencia = "positiva" if saldo > 0 else "deficitária"
    analise_texto = (
        f"A operação atual apresenta uma estrutura {tendencia}, com uma margem líquida de {margem:.2f}%. "
        f"O fluxo de caixa foi sustentado por um faturamento total de {format_brl(v_in)}, confrontados por "
        f"{format_brl(v_out)} em saídas. Esta performance reflete a dinâmica operacional do período analisado."
    )
    elementos.append(Paragraph(analise_texto, st_story))
    elementos.append(Spacer(1, 30))

    # Tabela de KPIs (Estilo Grid)
    data_kpi = [
        [Paragraph("<b>ENTRADAS (CASH IN)</b>", st_body), Paragraph("<b>SAÍDAS (CASH OUT)</b>", st_body)],
        [format_brl(v_in), format_brl(v_out)],
        [Paragraph("<b>RESULTADO LÍQUIDO</b>", st_body), Paragraph("<b>MARGEM OPERACIONAL</b>", st_body)],
        [format_brl(saldo), f"{margem:.2f}%"]
    ]
    t_kpi = Table(data_kpi, colWidths=[240, 240])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, 1), 18),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 18),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor("#15803D") if saldo > 0 else colors.red),
        ('GRID', (0, 0), (-1, -1), 2, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    elementos.append(t_kpi)

    # --- GRÁFICO DE COMPOSIÇÃO DE DESPESAS ---
    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("02. DISTRIBUIÇÃO DOS INVESTIMENTOS", st_h1))
    
    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index().sort_values(by=COL_V, ascending=False).head(5)
    
    d_pizza = Drawing(480, 200)
    pc = Pie()
    pc.x = 20
    pc.y = 50
    pc.width = 120
    pc.height = 120
    pc.data = df_g[COL_V].tolist()
    pc.labels = [f"{(v/v_out)*100:.1f}%" for v in df_g[COL_V]]
    
    legenda = Legend()
    legenda.x = 180
    legenda.y = 130
    legenda.fontSize = 10
    legenda.fontName = 'Helvetica'
    legenda.colorNamePairs = [(pc.slices[i].fillColor, df_g['Grupo_Filtro'].iloc[i][:30]) for i in range(len(df_g))]
    
    d_pizza.add(pc)
    d_pizza.add(legenda)
    elementos.append(d_pizza)

    # --- PÁGINA 3: DETALHAMENTO MENSAL ---
    elementos.append(PageBreak())
    elementos.append(Paragraph("03. DINÂMICA DE CAIXA MENSAL", st_h1))
    
    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['Net'] = df_burn['In'] - df_burn['Out']
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort')

    data_b = [["MÊS/ANO", "ENTRADAS (+)", "SAÍDAS (-)", "SALDO"]]
    for r in df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values:
        data_b.append([r[0], format_brl(r[1]), format_brl(r[2]), format_brl(r[3])])

    t_b = Table(data_b, colWidths=[120, 120, 120, 120])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_SECUNDARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    elementos.append(t_b)

    # RODAPÉ
    elementos.append(Spacer(1, 60))
    elementos.append(Paragraph("--- RELATÓRIO CONFIDENCIAL - USO INTERNO ---", st_footer))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
