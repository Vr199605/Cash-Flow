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

    # --- PALETA DE CORES E ESTILOS PREMIUM ---
    C_PRIMARIO = colors.HexColor("#00D1FF")
    C_SECUNDARIO = colors.HexColor("#0F172A")
    C_TEXTO = colors.HexColor("#334155")
    C_BG = colors.HexColor("#F8FAFC")

    # Estilos com alinhamento embutido para evitar o TypeError
    st_capa = ParagraphStyle('Capa', fontSize=32, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', alignment=1, spaceAfter=20)
    st_tit = ParagraphStyle('Tit', fontSize=22, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceAfter=10)
    st_sub = ParagraphStyle('Sub', fontSize=10, textColor=colors.HexColor("#64748B"), spaceAfter=20, leading=14)
    # Criamos um estilo específico para subtítulos centralizados na capa
    st_sub_center = ParagraphStyle('SubCenter', parent=st_sub, alignment=1)
    
    st_h1 = ParagraphStyle('H1', fontSize=16, textColor=C_SECUNDARIO, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=C_TEXTO, leading=14, alignment=4)
    st_story = ParagraphStyle('Story', fontSize=11, textColor=C_SECUNDARIO, leading=16, leftIndent=15, borderPadding=10, backColor=C_BG)
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    # --- PÁGINA 1: CAPA PROFISSIONAL ---
    elementos.append(Spacer(1, 120))
    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3.5 * inch, height=1.3 * inch)
        img.hAlign = 'CENTER'
        elementos.append(img)
    
    elementos.append(Spacer(1, 60))
    # Usando o estilo centralizado sem passar o argumento 'alignment' proibido
    elementos.append(Paragraph("RELATÓRIO EXECUTIVO DE", st_sub_center))
    elementos.append(Paragraph("PERFORMANCE FINANCEIRA", st_capa))
    
    emp_str = " | ".join(sorted(empresas_selecionadas))
    elementos.append(Paragraph(f"<b>UNIDADES:</b> {emp_str.upper()}", st_sub_center))
    elementos.append(Paragraph(f"<b>PERÍODO:</b> {', '.join(meses)}", st_sub_center))
    
    elementos.append(Spacer(1, 150))
    elementos.append(HRFlowable(width="60%", thickness=1, color=C_PRIMARIO, hAlign='CENTER'))
    elementos.append(Paragraph(f"Emitido em: {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}", st_sub_center))
    elementos.append(PageBreak())

    # --- PÁGINA 2: SUMÁRIO E STORYTELLING ---
    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    margem = (saldo / v_in * 100 if v_in > 0 else 0)

    elementos.append(Paragraph("01. VISÃO ESTRATÉGICA (STORYTELLING)", st_h1))
    
    tendencia = "positiva" if saldo > 0 else "de atenção"
    analise_texto = (
        f"A análise consolidada revela uma operação {tendencia}. Com uma receita total de {format_brl(v_in)} "
        f"e um custo operacional de {format_brl(v_out)}, a empresa encerra o período com um resultado líquido de "
        f"{format_brl(saldo)}. A margem de {margem:.2f}% indica a eficiência na conversão de receita em caixa."
    )
    elementos.append(Paragraph(analise_texto, st_story))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("02. INDICADORES CHAVE DE PERFORMANCE", st_h1))
    data_kpi = [
        [Paragraph("<b>ENTRADAS TOTAIS</b>", st_body), Paragraph("<b>SAÍDAS TOTAIS</b>", st_body)],
        [format_brl(v_in), format_brl(v_out)],
        [Paragraph("<b>RESULTADO LÍQUIDO</b>", st_body), Paragraph("<b>MARGEM OPERACIONAL</b>", st_body)],
        [format_brl(saldo), f"{margem:.2f}%"]
    ]
    t_kpi = Table(data_kpi, colWidths=[240, 240])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.black),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.red),
        ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor("#15803D") if saldo > 0 else colors.red),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elementos.append(t_kpi)

    # --- PÁGINA 3: FLUXO E PARETO ---
    elementos.append(PageBreak())
    elementos.append(Paragraph("03. EVOLUÇÃO DO FLUXO DE CAIXA MENSAL", st_h1))
    
    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['Net'] = df_burn['In'] - df_burn['Out']
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort')

    data_b = [["MÊS/ANO", "CASH IN (+)", "CASH OUT (-)", "NET CASHFLOW"]]
    for row in df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values:
        data_b.append([row[0], format_brl(row[1]), format_brl(row[2]), format_brl(row[3])])

    t_b = Table(data_b, colWidths=[120, 120, 120, 120])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_SECUNDARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG]),
    ]))
    elementos.append(t_b)

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("04. EXPOSIÇÃO POR GRUPO DE DESPESA", st_h1))
    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index().sort_values(by=COL_V, ascending=False)
    
    data_g = [["GRUPO ESTRATÉGICO", "INVESTIMENTO TOTAL", "PART.% RECEITA"]]
    for row in df_g.values:
        part = (row[1] / v_in * 100) if v_in > 0 else 0
        data_g.append([str(row[0]).upper(), format_brl(row[1]), f"{part:.1f}%"])
    
    t_g = Table(data_g, colWidths=[240, 120, 120])
    t_g.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.grey),
    ]))
    elementos.append(t_g)

    if 'Nome' in df_rec.columns:
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph("05. CONCENTRAÇÃO DE RECEITA (TOP 10)", st_h1))
        df_n = df_rec.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10).reset_index()
        data_n = [["ORIGEM / CLIENTE", "VALOR TOTAL"]] + [[str(r[0]), format_brl(r[1])] for r in df_n.values]
        t_n = Table(data_n, colWidths=[340, 140])
        t_n.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 0), (-1, 0), 2, C_PRIMARIO),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elementos.append(t_n)

    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("--- RELATÓRIO CONFIDENCIAL - USO INTERNO ---", st_footer))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
