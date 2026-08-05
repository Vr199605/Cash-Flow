// Parser dedicado para o layout "Fatura Técnica" (arquivo de registros por
// tipo: 1=cabeçalho do arquivo, 2=cabeçalho de subfatura, 3=beneficiário/
// lançamento, 4=totais, 5=trailer). É o formato que a Irko sempre envia
// para preencher a aba "Analítico Completo".
//
// Diferente de uma planilha "normal" (1 linha de cabeçalho + linhas de
// dados), esse arquivo tem blocos de cabeçalho e dados intercalados,
// repetidos a cada subfatura. Por isso não dá para usar o casamento de
// colunas genérico — este módulo interpreta a estrutura de registros e
// converte o resultado para o formato exato da aba "Analítico Completo".

import { TEMPLATE_SHEETS } from "./template";

function s(v: unknown): string {
  return String(v ?? "").trim();
}

/** Converte número em formato BR (" 1.383,37") para number. */
function parseBRL(v: unknown): number | "" {
  const str = s(v);
  if (!str) return "";
  const cleaned = str.replace(/\./g, "").replace(",", ".");
  const n = parseFloat(cleaned);
  return Number.isNaN(n) ? "" : n;
}

function toNumberOrText(v: string): number | string {
  if (/^\d+$/.test(v)) return Number(v);
  return v;
}

function isEmptyDate(str: string): boolean {
  return !str || str === "00/00/0000";
}

function parseBRDate(str: string): Date | null {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(str);
  if (!m) return null;
  const [, d, mo, y] = m;
  return new Date(Number(y), Number(mo) - 1, Number(d));
}

/** Último dia do mês de competência ("07/2026" -> 31/07/2026). */
function lastDayOfCompetencia(comp: string): Date | null {
  const m = /^(\d{2})\/(\d{4})$/.exec(comp);
  if (!m) return null;
  const [, mo, y] = m;
  return new Date(Number(y), Number(mo), 0);
}

function ageAt(birth: Date, ref: Date): number {
  let age = ref.getFullYear() - birth.getFullYear();
  const beforeBirthday =
    ref.getMonth() < birth.getMonth() ||
    (ref.getMonth() === birth.getMonth() && ref.getDate() < birth.getDate());
  if (beforeBirthday) age--;
  return age;
}

// Tabelas de código -> texto observadas/usuais em layouts de fatura técnica
// de operadoras de saúde (padrão ANS). Documentado aqui porque o arquivo de
// origem não inclui um dicionário de códigos.
const SEX_MAP: Record<string, string> = { "1": "MASCULINO", "2": "FEMININO" };
const MARITAL_MAP: Record<string, string> = {
  "1": "SOLTEIRO",
  "2": "CASADO",
  "3": "VIÚVO",
  "4": "DIVORCIADO",
  "5": "DESQUITADO",
  "6": "SEPARADO JUDICIALMENTE",
  "7": "UNIÃO ESTÁVEL",
  "9": "NÃO DECLARADO",
};
const KINSHIP_MAP: Record<string, string> = {
  "0": "TITULAR",
  "1": "CÔNJUGE",
  "2": "FILHO(A)",
  "3": "ENTEADO(A)",
  "4": "PAI/MÃE",
  "5": "SOGRO(A)",
  "6": "NETO(A)",
  "7": "IRMÃO/IRMÃ",
  "8": "AGREGADO",
  "9": "OUTROS",
};

/** Detecta se a primeira linha da planilha é o cabeçalho de uma Fatura Técnica. */
export function detectFaturaTecnica(aoa: unknown[][]): boolean {
  const row0 = (aoa[0] ?? []).map((v) => s(v).toUpperCase());
  return row0[0] === "TIPO DE REGISTRO" && row0[1] === "TIPO DE ARQUIVO";
}

export type FaturaTecnicaResult = {
  headers: string[];
  rows: unknown[][];
};

/**
 * Varre todas as linhas do arquivo (registros tipo 1/2/3/4/5) e extrai os
 * registros tipo 3 (beneficiário/lançamento), já no formato de colunas da
 * aba "Analítico Completo".
 *
 * Observações/premissas assumidas (o arquivo de origem não fornece isso
 * diretamente):
 * - CPF TITULAR e CPF SEGURADO/DEPENDENTE: não existem nesse arquivo, saem em branco.
 * - IOF: não existe nesse arquivo, sai em branco; TOTAL é preenchido igual a
 *   VALOR DO LANCAMENTO (sem acréscimo de IOF).
 * - IDADE: calculada a partir da DATA DE NASCIMENTO em relação ao último dia
 *   do mês de competência da fatura.
 * - CODIGO DO SEXO, ESTADO CIVIL e COD. GRAU PARENT.DEP.: o arquivo traz
 *   apenas códigos numéricos; convertidos para texto usando as tabelas
 *   padrão de operadoras de saúde. Confira se sua operadora usa a mesma
 *   tabela antes de usar esses três campos para decisões críticas.
 * - Linhas sem beneficiário real (ex.: "F.MODERADORES PAGOS EM MM/AAAA",
 *   cobranças de coparticipação) ficam com os campos de identificação do
 *   beneficiário em branco, igual ao padrão do arquivo-modelo.
 */
export function parseFaturaTecnicaAnalitico(
  aoa: unknown[][]
): FaturaTecnicaResult {
  const columns = TEMPLATE_SHEETS.find(
    (t) => t.name === "Analítico Completo"
  )!.columns;

  let competencia = "";
  let subfaturaLabel = "";
  const titularByCert: Record<string, string> = {};
  const rows: unknown[][] = [];

  for (const raw of aoa) {
    const tipo = s(raw[0]);

    if (tipo === "1") {
      competencia = s(raw[8]);
      continue;
    }

    if (tipo === "2") {
      const numero = s(raw[2]);
      const nome = s(raw[3]);
      subfaturaLabel = numero ? (nome ? `${numero} - ${nome}` : numero) : "";
      continue;
    }

    if (tipo !== "3") continue; // ignora cabeçalhos de bloco, totais (4), trailer (5) e linhas em branco

    const numeroCertificado = s(raw[2]);
    const nomeSegurado = s(raw[4]);
    const dataNascStr = s(raw[6]);
    const sexoCod = s(raw[7]);
    const civilCod = s(raw[8]);
    const grauCod = s(raw[9]);
    const codigoPlano = s(raw[10]);
    const dataVigStr = s(raw[11]);
    const tipoLancamento = s(raw[12]);
    const dataLancamento = s(raw[13]);
    const valorLancamento = parseBRL(raw[14]);
    const parteSegurado = parseBRL(raw[15]);
    const codigoLancamento = s(raw[16]);
    const cargo = s(raw[17]);
    const matricula = s(raw[18]);

    const isPessoa = !isEmptyDate(dataNascStr);
    const isTitular = isPessoa && grauCod === "0";
    const certKey = `${subfaturaLabel}::${numeroCertificado}`;

    if (isTitular) titularByCert[certKey] = nomeSegurado;
    const nomeTitular = isPessoa ? titularByCert[certKey] ?? nomeSegurado : "";

    const birth = isPessoa ? parseBRDate(dataNascStr) : null;
    const ref = lastDayOfCompetencia(competencia);
    const idade = birth && ref ? ageAt(birth, ref) : "";

    const row = columns.map((col) => {
      switch (col) {
        case "COMPETÊNCIA":
          return competencia;
        case "NUMERO DA SUBFATURA":
          return subfaturaLabel;
        case "NUMERO DO CERTIFICADO":
          return numeroCertificado ? toNumberOrText(numeroCertificado) : "";
        case "TIPO DE BENEFICIÁRIO":
          return isPessoa ? (isTitular ? "TITULAR" : "DEPENDENTE") : "";
        case "NOME TITULAR":
          return nomeTitular;
        case "CPF TITULAR":
          return "";
        case "NOME SEGURADO/DEPENDENTE":
          return nomeSegurado;
        case "CPF SEGURADO/DEPENDENTE":
          return "";
        case "DATA DE NASCIMENTO":
          return isPessoa ? dataNascStr : "";
        case "IDADE":
          return idade;
        case "CODIGO DO SEXO":
          return isPessoa ? SEX_MAP[sexoCod] ?? "" : "";
        case "ESTADO CIVIL":
          return isPessoa ? MARITAL_MAP[civilCod] ?? "" : "";
        case "COD. GRAU PARENT.DEP.":
          return isPessoa ? KINSHIP_MAP[grauCod] ?? "" : "";
        case "CODIGO DO PLANO":
          return isPessoa ? codigoPlano : "";
        case "DATA INICIO VIGENCIA":
          return isEmptyDate(dataVigStr) ? "" : dataVigStr;
        case "TIPO DE LANÇAMENTO":
          return tipoLancamento;
        case "NOME DO LANÇAMENTO":
          return "";
        case "DATA DE LANCAMENTO":
          return dataLancamento;
        case "VALOR DO LANCAMENTO":
          return valorLancamento;
        case "IOF":
          return "";
        case "TOTAL":
          return valorLancamento;
        case "PARTE DO SEGURADO":
          return parteSegurado;
        case "CODIGO DO LANCAMENTO":
          return codigoLancamento;
        case "CARGO / OCUPACAO":
          return cargo;
        case "MATRICULA ESPECIAL":
          return matricula;
        default:
          return "";
      }
    });

    rows.push(row);
  }

  return { headers: columns, rows };
}
