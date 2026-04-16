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
    # Ajuste de margens para um visual mais "limpo" e editorial
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50,
    )
    
    styles = getSampleStyleSheet()

    # --- ESTILOS PERSONALIZADOS (A PERFEIÇÃO VISUAL) ---
    st_tit = ParagraphStyle('Tit', fontSize=26, textColor=colors.HexColor("#0F172A"), fontName='Helvetica-Bold', spaceAfter=6)
    st_emp = ParagraphStyle('Emp', fontSize=12, textColor=colors.HexColor("#00D1FF"), fontName='Helvetica-Bold', spaceAfter=14)
    st_sub = ParagraphStyle('Sub', fontSize=9, textColor=colors.HexColor("#64748B"), spaceAfter=20)
    st_h1 = ParagraphStyle('H1', fontSize=16, textColor=colors.HexColor("#0F172A"), fontName='Helvetica-Bold', spaceBefore=25, spaceAfter=12)
    st_body = ParagraphStyle('Body', fontSize=10, textColor=colors.HexColor("#334155"), leading=15, alignment=4)
    st_story = ParagraphStyle('Story', fontSize=10, textColor=colors.HexColor("#1E293B"), leading=16, italic=True, leftIndent=20, rightIndent=20, spaceBefore=10, spaceAfter=10)
    st_footer = ParagraphStyle('Foot', fontSize=8, textColor=colors.grey, alignment=1)

    elementos = []

    # 1. LOGO E CABEÇALHO
    logo_path = "avaliacoes_salvas/logo_maldivas.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.2 * inch, height=0.8 * inch)
        img.hAlign = 'LEFT'
        elementos.append(img)
    
    elementos.append(Spacer(1, 15))
    nome_exibicao = " | ".join(sorted(empresas_selecionadas))
    elementos.append(Paragraph("RELATÓRIO EXECUTIVO FINANCEIRO", st_tit))
    elementos.append(Paragraph(nome_exibicao.upper(), st_emp))
    elementos.append(Paragraph(
        f"Período Consolidado: {', '.join(meses)}  |  Data de Emissão: {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        st_sub,
    ))
    elementos.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#00D1FF"), spaceAfter=25))

    # 2. STORYTELLING: O CONTEXTO (INTEGRAÇÃO DA INTELIGÊNCIA)
    v_in = df_rec[COL_V].sum()
    v_out = abs(df_sai[COL_V].sum())
    saldo = v_in - v_out
    margem = (saldo / v_in * 100 if v_in > 0 else 0)

    elementos.append(Paragraph("A Narrativa dos Dados (Storytelling)", st_h1))
    
    # Lógica de narrativa baseada nos números reais
    status_caixa = "superavitária" if saldo > 0 else "deficitária"
    tom_analise = "saudável e permite reinvestimento" if margem > 15 else "que exige monitoramento rigoroso de custos fixos"
    
    story_text = (
        f"A operação atual apresenta uma estrutura {status_caixa}, com uma margem líquida de {margem:.2f}%. "
        f"O fluxo de caixa foi sustentado por um volume total de {format_brl(v_in)} em entradas, "
        f"confrontados por {format_brl(v_out)} em saídas operacionais e administrativas. "
        f"Esta performance reflete uma dinâmica {tom_analise} para o período analisado."
    )
    elementos.append(Paragraph(story_text, st_story))

    # 3. KPIs DE PERFORMANCE
    elementos.append(Paragraph("I. INDICADORES CHAVE (KPIs)", st_h1))
    data_kpi = [
        [Paragraph("<b>INDICADOR ESTRATÉGICO</b>", st_body), Paragraph("<b>VALOR CONSOLIDADO</b>", st_body)],
        ["RECEITA BRUTA (CASH IN)", format_brl(v_in)],
        ["DESPESAS TOTAIS (CASH OUT)", format_brl(v_out)],
        ["RESULTADO LÍQUIDO", format_brl(saldo)],
        ["EFICIÊNCIA OPERACIONAL (MARGEM %)", f"{margem:.2f}%"],
    ]
    
    t_kpi = Table(data_kpi, colWidths=[320, 130])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0, 3), (1, 3), colors.HexColor("#F8FAFC")),
    ]))
    elementos.append(t_kpi)

    # 4. FLUXO MENSAL (CASH BURN ANALYTICS)
    elementos.append(Paragraph("II. DINÂMICA DE CAIXA MENSAL", st_h1))
    
    burn_in = df_rec.groupby('Mes_Ano')[COL_V].sum().reset_index().rename(columns={COL_V: 'In'})
    burn_out = df_sai.groupby('Mes_Ano')[COL_V].sum().abs().reset_index().rename(columns={COL_V: 'Out'})
    df_burn = pd.merge(burn_in, burn_out, on='Mes_Ano', how='outer').fillna(0)
    df_burn['Net'] = df_burn['In'] - df_burn['Out']
    df_burn['_sort'] = pd.to_datetime(df_burn['Mes_Ano'], format='%m/%Y')
    df_burn = df_burn.sort_values('_sort')

    data_b = [["MÊS REFERÊNCIA", "ENTRADAS (+)", "SAÍDAS (-)", "RESULTADO"]]
    for row in df_burn[['Mes_Ano', 'In', 'Out', 'Net']].values:
        data_b.append([row[0], format_brl(row[1]), format_brl(row[2]), format_brl(row[3])])

    t_b = Table(data_b, colWidths=[115, 115, 115, 105])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBFCFD")]),
    ]))
    
    # Aplicação de cores dinâmicas no saldo
    for i, row in enumerate(df_burn['Net'].values):
        cor = colors.HexColor("#B91C1C") if row < 0 else colors.HexColor("#15803D")
        t_b.setStyle(TableStyle([('TEXTCOLOR', (3, i + 1), (3, i + 1), cor), ('FONTNAME', (3, i + 1), (3, i + 1), 'Helvetica-Bold')]))
    
    elementos.append(t_b)

    # 5. ANÁLISE DE GRUPOS E IMPACTO
    elementos.append(PageBreak())
    elementos.append(Paragraph("III. DISTRIBUIÇÃO E IMPACTO POR GRUPO", st_h1))
    elementos.append(Paragraph("Análise de Pareto aplicada aos grupos de despesa para identificar os maiores ofensores do caixa.", st_body))
    elementos.append(Spacer(1, 10))

    df_g = df_sai.groupby('Grupo_Filtro')[COL_V].sum().abs().reset_index().sort_values(by=COL_V, ascending=False)
    data_g = [["GRUPO ESTRATÉGICO", "INVESTIMENTO TOTAL", "% SOBRE RECEITA"]]
    for row in df_g.values:
        impacto = (row[1] / v_in * 100) if v_in > 0 else 0
        data_g.append([str(row[0]).upper(), format_brl(row[1]), f"{impacto:.1f}%"])
    
    t_g = Table(data_g, colWidths=[220, 130, 100])
    t_g.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.1, colors.grey),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(t_g)

    # 6. TOP 10 RECEBIMENTOS (CONCENTRAÇÃO)
    if 'Nome' in df_rec.columns:
        elementos.append(Paragraph("IV. PRINCIPAIS FONTES DE RECEITA (TOP 10)", st_h1))
        df_n = df_rec.groupby('Nome')[COL_V].sum().sort_values(ascending=False).head(10).reset_index()
        data_n = [["PARCEIRO / ORIGEM", "VALOR NOMINAL"]] + [[str(r[0]), format_brl(r[1])] for r in df_n.values]
        
        t_n = Table(data_n, colWidths=[330, 120])
        t_n.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00D1FF")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.1, colors.HexColor("#E2E8F0")),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ]))
        elementos.append(t_n)

    # RODAPÉ FINAL
    elementos.append(Spacer(1, 60))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Paragraph(
        "Este documento é estritamente confidencial e gerado automaticamente pelo sistema de BI. <br/>"
        "As análises aqui contidas visam subsidiar a tomada de decisão estratégica do corpo executivo.",
        st_footer,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
