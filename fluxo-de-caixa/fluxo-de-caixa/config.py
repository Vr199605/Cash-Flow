COL_V = 'Valor categoria/centro de custo'


def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MAPA_GRUPOS = {
    "Administrativo": [
        "ALUGUEL", "COMPRA DE ATIVO FIXO", "CONDOMÍNIO", "COWORKING", "CUSTO OPERACIONAL",
        "DESPESAS FINANCEIRAS", "ENERGIA ELÉTRICA", "ESTORNO", "EVENTOS FUNCIONÁRIOS",
        "DESPESAS VIAGEM", "MANUTENÇÃO ESCRITÓRIO", "MATERIAIS DE TI", "MATERIAL DE COPA",
        "MATERIAL DE ESCRITÓRIO", "MATERIAL DE LIMPEZA", "Multas Pagas", "LOCOMOÇÃO",
        "OUTRAS DESPESAS", "PAGAMENTO DE EMPRÉSTIMO", "REPRESENTAÇÃO", "SEGUROS",
        "SERVIÇOS CONTÁBEIS", "SERVIÇOS CONTRATADOS", "SERVIÇOS DE E-MAIL",
        "SERVIÇOS DE ENTREGA", "SERVIÇOS DE PUBLICIDADE", "SERVIÇOS JURÍDICOS",
        "SERVIÇOS TI", "SISTEMAS", "TAXAS E CONTRIBUIÇÕES", "TELEFONIA/INTERNET",
        "TREINAMENTOS", "VAGAS GARAGEM - SÓCIOS",
    ],
    "Despesa de pessoal": [
        "13º SALÁRIO", "ADIANTAMENTO AO FUNCIONÁRIO", "ANTECIPAÇÃO DE RESULTADOS",
        "ASSISTÊNCIA MÉDICA", "ASSISTÊNCIA ODONTO", "BÔNUS CLT", "BÔNUS PERFORMANCE - G",
        "CONSULTORIA ESPECIALIZADA - G", "CONSULTORIA ESPECIALIZADA - TI",
        "DESPESA EVENTUAL DE PESSOAL", "ESTAGIÁRIO FOLHA", "EXAMES OCUPACIONAIS",
        "FÉRIAS", "FGTS", "GRATIFICAÇÕES CLT", "GRATIFICAÇÕES PJ - G", "INSS", "IRRF",
        "PRO LABORE", "RESCISÃO", "SALÁRIOS CLT", "SEGURO DE VIDA",
        "SERVIÇOS CONTRATADOS", "VA/VR", "VT",
    ],
    "Operacional": [
        "BÔNUS - TERCEIROS", "COMISSÕES SEGUROS", "CUSTO OPERACIONAL",
        "Descontos Recebidos", "EVENTOS CLIENTES", "Multas Pagas",
        "REBATE COMISSÕES", "REPRESENTAÇÃO", "ÁGUA", "COLETA DE LIXO", "Outras Retenções sobre Pagamentos"
    ],
    "Tributário": [
        "COFINS", "COFINS Retido sobre Pagamentos", "CSLL",
        "CSLL Retido sobre Pagamentos", "DESPESAS FINANCEIRAS", "ESTORNO",
        "INSS Retido sobre Pagamentos", "Juros Pagos", "IPTU", "IRPJ",
        "IRPJ Retido sobre Pagamentos", "ISS", "ISS Retido sobre Pagamentos",
        "Juros Pagos", "Multas Pagas", "Pagamento de ISS Retido",
        "PARCELAMENTO RECEITA FEDERAL", "PERT CSLL", "PERT IRPJ", "PERT IRRF",
        "PERT SN", "PIS", "PIS Retido sobre Pagamentos",
    ],
}

URLS = {
    "Globus": {
        "s": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=1959056339&single=true&output=csv",
        "r": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=58078527&single=true&output=csv",
        "cp": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=2118565092&single=true&output=csv",
        "depara": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=1181327025&single=true&output=csv",
    },
    "MGL": {
        "s": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=1774273194&single=true&output=csv",
        "r": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=748812022&single=true&output=csv",
        "cp": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=379762787&single=true&output=csv",
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
.main { background-color: #0B0E14; }
div[data-testid="stMetricValue"] { color: #00D1FF; font-weight: 700; font-size: 1.8rem !important; }
div[data-testid="stMetricLabel"] { color: #94A3B8; font-weight: 400; }
div[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
.stTabs [data-baseweb="tab"] {
    height: 45px;
    background-color: #1E293B;
    border-radius: 8px 8px 0 0;
    color: #94A3B8;
    padding: 10px 20px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #00D1FF !important;
    color: #0B0E14 !important;
}
.css-1d391kg { background-color: #111827; }
</style>
"""
