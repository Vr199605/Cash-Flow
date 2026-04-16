import io
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, 
    Spacer, Table, TableStyle, KeepTogether
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.legends import Legend

from config import COL_V, format_brl

def gerar_pdf_perfeito(df_sai, df_rec, meses: list, empresas_selecionadas: list) -> io.BytesIO:
    buffer = io.BytesIO()
    # Margens amplas para evitar cortes e sobreposições
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50,
    )
    
    # --- DEFINIÇÃO DE CORES ---
    C_PRIMARIO = colors.HexColor("#00D1FF")
    C_SECUNDARIO = colors.HexColor("#0F172A")
    C_TEXTO = colors.HexColor("#334155")
    C_BG = colors.HexColor("#F1F5F9")

    # --- ESTILOS DE TEXTO ---
    st = getSampleStyleSheet()
    st_capa = ParagraphStyle('Capa', fontSize=36, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', alignment=1, spaceAfter=30)
    st_h1 = ParagraphStyle('H1', fontSize=18, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=15)
    st_sub_center = ParagraphStyle('SubC', fontSize=11, textColor=colors.HexColor("#64748B"), alignment=1, leading=16)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=C_TEXTO, leading=14, alignment=4)
    st_story = ParagraphStyle('Story', fontSize=11, textColor=C_SECUNDARIO, leading=18, leftIndent=25, rightIndent=25, borderPadding=20, backColor=colors.white, borderSize=1, borderColor=C_BG)
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    # --- PÁGINA 1: CAPA ---
    elementos.append(Spacer(1, 120))
    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3.2 * inch, height=1.2 * inch)
        img.hAlign = 'CENTER'
        elementos.append(img)
    
    elementos.append(Spacer(1, 60))
    elementos.append(Paragraph("RELATÓRIO DE INTELIGÊNCIA", st_sub_center))
    elementos.append(Paragraph("GESTÃO FINANCEIRA", st_capa))
    
    emp_str = " + ".join(sorted(empresas_selecionadas))
    elementos.append(Paragraph(f"<b>CONSOLIDADO:</b> {emp_str.upper()}", st_sub_center))
    elementos.append(Paragraph(f"<b>REFERÊNCIA:</b> {', '.join(meses)}", st_sub_center))
    
    elementos.append(Spacer(1, 180))
    elementos.append(HRFlowable(width="40%", thickness=2, color=C_PRIMARIO, hAlign='CENTER'))
    elementos.append(Paragraph(f"Emissão: {pd.Timestamp.now().strftime('%d/%m/%Y')}", st_sub_center))
    elementos.append(PageBreak())

    # --- PÁGINA 2: STORYTELLING E DASHBOARD ---
    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    margem = (saldo / v_in * 100 if v_in > 0 else 0)

    elementos.append(Paragraph("01. NARRATIVA ESTRATÉGICA", st_h1))
    
    status = "SAUDÁVEL" if saldo > 0 else "CRÍTICA"
    cor_status = "#15803D" if saldo > 0 else "#B91C1C"
    
    texto_narrativa = (
        f"A operação apresenta uma saúde financeira <b><font color='{cor_status}'>{status}</font></b> no período. "
        f"Com um faturamento bruto de {format_brl(v_in)}, a empresa destinou {format_brl(v_out)} para cobrir suas "
        f"obrigações operacionais, resultando em um superávit/déficit líquido de {format_brl(saldo)}. "
        f"A margem operacional de {margem:.2f}% serve como o principal termômetro de eficiência."
    )
    elementos.append(Paragraph(texto_narrativa, st_story))
    elementos.append(Spacer(1, 30))

    # Tabela de KPIs (Cards)
    data_kpi = [
        [Paragraph("<b>TOTAL RECEBIDO</b>", st_body), Paragraph("<b>TOTAL DESEMBOLSADO</b>", st_body)],
        [format_brl(v_in), format_brl(v_out)],
        [Paragraph("<b>RESULTADO LÍQUIDO</b>", st_body), Paragraph("<b>EFICIÊNCIA (%)</b>", st_body)],
        [format_brl(saldo), f"{margem:.2f}%"]
    ]
    t_kpi = Table(data_kpi, colWidths=[240, 240])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, 1), 18),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 18),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor(cor_status)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 2, colors.white),
    ]))
    elementos.append(t_kpi)

    # --- GRÁFICO 1: PIZZA DE DESPESAS ---
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("02. DISTRIBUIÇÃO POR GRUPO DE DESPESA", st_h1))
    
    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index().sort_values(by=COL_V, ascending=False).head(6)
    
    d_pizza = Drawing(480, 220)
    pc = Pie()
    pc.x = 10
    pc.y = 50
    pc.width = 130
    pc.height = 130
    pc.data = df_g[COL_V].tolist()
    pc.labels = [f"{p:.1f}%" for p in (df_g[COL_V] / v_out * 100)]
    pc.slices.strokeWidth = 0.5
    
    legenda = Legend()
    legenda.x = 200
    legenda.y = 140
    legenda.fontSize = 10
    legenda.fontName = 'Helvetica'
    legenda.columnMaximum = 10
    legenda.colorNamePairs = [(pc.slices[i].fillColor, df_g['Grupo_Filtro'].iloc[i]) for i in range(len(df_g))]
    
    d_pizza.add(pc)
    d_pizza.add(legenda)
    elementos.append(d_pizza)

    # --- PÁGINA 3: FLUXO MENSAL E BARRAS ---
    elementos.append(PageBreak())
    elementos.append(Paragraph("03. EVOLUÇÃO MENSAL E CASH BURN", st_h1))
    
    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort').tail(6)

    # Gráfico de Barras
    d_bar = Drawing(480, 200)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 400
    bc.data = [df_burn['In'].tolist(), df_burn['Out'].tolist()]
    bc.categoryAxis.categoryNames = df_burn['Mes_Ano'].tolist()
    bc.bars[0].fillColor = C_PRIMARIO
    bc.bars[1].fillColor = C_SECUNDARIO
    bc.valueAxis.valueMin = 0
    d_bar.add(bc)
    elementos.append(d_bar)
    elementos.append(Spacer(1, 20))

    # Tabela de Dados Mensais
    data_b = [["MÊS/ANO", "CASH IN", "CASH OUT", "SALDO LÍQUIDO"]]
    for r in df_burn[['Mes_Ano', 'In', 'Out']].values:
        data_b.append([r[0], format_brl(r[1]), format_brl(r[2]), format_brl(r[1]-r[2])])

    t_b = Table(data_b, colWidths=[120, 120, 120, 120])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_SECUNDARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG]),
    ]))
    elementos.append(t_b)

    # --- PÁGINA 4: PARETO E RECEBIMENTOS ---
    elementos.append(PageBreak())
    elementos.append(Paragraph("04. ANÁLISE DE CONCENTRAÇÃO (TOP 10)", st_h1))
    
    if 'Nome' in df_rec.columns:
        df_n = df_rec.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10).reset_index()
        data_n = [["ORIGEM / CLIENTE", "VALOR TOTAL"]] + [[str(r[0])[:45], format_brl(r[1])] for r in df_n.values]
        t_n = Table(data_n, colWidths=[360, 120])
        t_n.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARIO),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, C_BG),
        ]))
        elementos.append(t_n)

    elementos.append(Spacer(1, 60))
    elementos.append(Paragraph("--- DOCUMENTO PARA FINS DE ANÁLISE EXECUTIVA ---", st_footer))
    elementos.append(Paragraph("Gerado por Maldivas Seguros - Inteligência de Mercado", st_footer))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
