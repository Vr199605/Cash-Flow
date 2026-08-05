// Modelo extraído de "001_Irko_Organização_Resumo da Fatura_08.2026.xls"
// 4 abas, cada uma com um conjunto fixo de colunas. Este é o "molde" que
// toda planilha gerada pelo sistema vai seguir.

export type TemplateSheet = {
  /** Nome exato da aba, igual ao arquivo-modelo */
  name: string;
  /** Cabeçalhos, na ordem exata do arquivo-modelo */
  columns: string[];
  /** Descrição curta exibida na interface */
  description: string;
};

export const TEMPLATE_SHEETS: TemplateSheet[] = [
  {
    name: "Analítico Completo",
    description: "Um registro por beneficiário/lançamento da fatura.",
    columns: [
      "COMPETÊNCIA",
      "NUMERO DA SUBFATURA",
      "NUMERO DO CERTIFICADO",
      "TIPO DE BENEFICIÁRIO",
      "NOME TITULAR",
      "CPF TITULAR",
      "NOME SEGURADO/DEPENDENTE",
      "CPF SEGURADO/DEPENDENTE",
      "DATA DE NASCIMENTO",
      "IDADE",
      "CODIGO DO SEXO",
      "ESTADO CIVIL",
      "COD. GRAU PARENT.DEP.",
      "CODIGO DO PLANO",
      "DATA INICIO VIGENCIA",
      "TIPO DE LANÇAMENTO",
      "NOME DO LANÇAMENTO",
      "DATA DE LANCAMENTO",
      "VALOR DO LANCAMENTO",
      "IOF",
      "TOTAL",
      "PARTE DO SEGURADO",
      "CODIGO DO LANCAMENTO",
      "CARGO / OCUPACAO",
      "MATRICULA ESPECIAL",
    ],
  },
  {
    name: "Coparticipação",
    description: "Fator moderador por segurado.",
    columns: [
      "NUMERO DA SUBFATURA",
      "NUMERO DO CERTIFICADO",
      "TITULAR",
      "NOME DO SEGURADO",
      "CPF",
      "VALOR DO FATOR MODERADOR",
    ],
  },
  {
    name: "Movimentações Faturadas",
    description: "Inclusões, exclusões e demais movimentações do período.",
    columns: [
      "NUMERO DA SUBFATURA",
      "TIPO DE BENEFICIÁRIO",
      "NOME TITULAR",
      "CPF TITULAR",
      "NOME SEGURADO/DEPENDENTE",
      "CPF SEGURADO/DEPENDENTE",
      "NOME DO LANÇAMENTO",
    ],
  },
  {
    name: "Rateio",
    description: "Totais por subfatura e tipo de lançamento.",
    columns: [
      "NUMERO DA SUBFATURA",
      "NOME DO LANÇAMENTO",
      "TOTAL LANCAMENTOS (VALOR)",
      "IOF",
      "VALOR TOTAL",
    ],
  },
];
