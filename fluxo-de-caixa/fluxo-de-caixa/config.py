import unicodedata
import pandas as pd

COL_V = 'Valor categoria/centro de custo'


def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Função para limpar e normalizar qualquer texto:
# Transforma: "Serviços T.I." -> "SERVICOS TI"
# Transforma: "DESPESAS DE CARTÃO DE CRÉDITO" -> "DESPESAS DE CARTAO DE CREDITO"
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto_str = str(texto).strip()
    # Remove caracteres especiais/invisíveis comuns de planilhas
    texto_str = texto_str.replace("\xa0", " ")
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", texto_str)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Remove pontuações simples e padroniza espaços
    sem_pontuacao = (
        sem_acento.replace(".", " ")
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
    )
    return " ".join(sem_pontuacao.upper().split())


MAPA_GRUPOS = {
    "Administrativo": [
        "ALUGUEL",
        "COMPRA DE ATIVO FIXO",
        "CONDOMINIO",
        "COWORKING",
        "CUSTO OPERACIONAL",
        "DESPESAS FINANCEIRAS",
        "DESPESAS DE CARTAO DE CREDITO",
        "CARTAO DE CREDITO",
        "ENERGIA ELETRICA",
        "ESTORNO",
        "EVENTOS FUNCIONARIOS",
        "MANUTENCAO ESCRITORIO",
        "MATERIAIS DE TI",
        "MATERIAL DE COPA",
        "MATERIAL DE ESCRITORIO",
        "MATERIAL DE LIMPEZA",
        "MULTAS PAGAS",
        "LOCOMOCAO",
        "OUTRAS DESPESAS",
        "PAGAMENTO DE EMPRESTIMO",
        "REPRESENTACAO",
        "REEMBOLSO",
        "SEGUROS",
        "SERVICOS CONTABEIS",
        "SERVICOS CONTRATADOS",
        "SERVICOS DE E-MAIL",
        "SERVICOS DE ENTREGA",
        "SERVICOS DE PUBLICIDADE",
        "SERVICOS JURIDICOS",
        "SERVICOS TI",
        "SERVICOS T.I.",
        "SISTEMAS",
        "TAXAS E CONTRIBUICOES",
        "TELEFONIA/INTERNET",
        "TELEFONE E INTERNET",
        "TELEFONIA",
        "INTERNET",
        "TREINAMENTOS",
        "VAGAS GARAGEM - SOCIOS",
    ],
    "Despesa de pessoal": [
        "13 SALARIO",
        "13º SALARIO",
        "ADIANTAMENTO AO FUNCIONARIO",
        "ANTECIPACAO DE RESULTADOS",
        "DIVIDENDOS",
        "ASSISTENCIA MEDICA",
        "ASSISTENCIA ODONTO",
        "BONUS CLT",
        "BONUS PERFORMANCE - G",
        "CONSULTORIA ESPECIALIZADA - G",
        "CONSULTORIA ESPECIALIZADA - TI",
        "DESPESA EVENTUAL DE PESSOAL",
        "DESPESAS VIAGEM",
        "DESPESAS COM VIAGENS",
        "DESPESA COM VIAGEM",
        "VIAGENS",
        "VIAGEM",
        "ESTAGIARIO FOLHA",
        "EXAMES OCUPACIONAIS",
        "FERIAS",
        "FGTS",
        "GRATIFICACOES CLT",
        "GRATIFICACOES PJ - G",
        "INSS",
        "IRRF",
        "PRO LABORE",
        "RESCISAO",
        "SALARIOS CLT",
        "SEGURO DE VIDA",
        "VA/VR",
        "VT",
    ],
    "Operacional": [
        "BONUS - TERCEIROS",
        "COMISSOES SEGUROS",
        "DESCONTOS RECEBIDOS",
        "EVENTOS CLIENTES",
        "REBATE COMISSOES",
        "AGUA",
        "COLETA DE LIXO",
        "OUTRAS RETENCOES SOBRE PAGAMENTOS",
    ],
    "Tributário": [
        "COFINS",
        "COFINS RETIDO SOBRE PAGAMENTOS",
        "CSLL",
        "CSLL RETIDO SOBRE PAGAMENTOS",
        "INSS RETIDO SOBRE PAGAMENTOS",
        "IPTU",
        "IRPJ",
        "IRPJ RETIDO SOBRE PAGAMENTOS",
        "ISS",
        "ISS RETIDO SOBRE PAGAMENTOS",
        "JUROS PAGOS",
        "PAGAMENTO DE ISS RETIDO",
        "PARCELAMENTO RECEITA FEDERAL",
        "PERT CSLL",
        "PERT IRPJ",
        "PERT IRRF",
        "PERT SN",
        "PIS",
        "PIS RETIDO SOBRE PAGAMENTOS",
    ],
}

# Cria um dicionário normalizado com busca exata e busca por contenção
DE_PARA_NORMALIZADO = {
    normalizar_texto(item): grupo
    for grupo, itens in MAPA_GRUPOS.items()
    for item in itens
}


def obter_grupo(categoria):
    cat_norm = normalizar_texto(categoria)
    if not cat_norm:
        return "Outros"

    # 1. Tenta correspondência exata normalizada
    if cat_norm in DE_PARA_NORMALIZADO:
        return DE_PARA_NORMALIZADO[cat_norm]

    # 2. Tenta correspondência parcial (se o texto contiver termos-chave)
    for chave, grupo in DE_PARA_NORMALIZADO.items():
        if len(chave) > 3 and (chave in cat_norm or cat_norm in chave):
            return grupo

    return "Outros"
