// Parsers dedicados para os formatos que a aba "Coparticipação" sempre
// recebe. Duas variantes conhecidas, com granularidades diferentes:
//
// 1) "DIRF COPAY COMPLETA": uma linha por pessoa (TPSE = cobrança do
//    próprio titular, DTPS = cobrança de um dependente). Cabeçalho não
//    fica na primeira linha da planilha — vem depois de um bloco com os
//    dados da operadora.
// 2) "PART. DOS SEGURADOS": layout de registros (tipo 1=cabeçalho do
//    arquivo, 2=dados, 3=trailer), com um valor já agregado por titular
//    (soma do titular + dependentes em uma única linha).
//
// As duas são aceitas: cada arquivo enviado é detectado e convertido para
// as colunas da aba "Coparticipação"; dá para enviar mais de um arquivo
// (de formatos iguais ou diferentes) e os resultados são somados na
// planilha final.

import { TEMPLATE_SHEETS } from "./template";
import { normalizeHeader } from "./normalize";

function s(v: unknown): string {
  return String(v ?? "").trim();
}

/** Aceita tanto number quanto string em formato BR (" 140,00"). */
function toNumber(v: unknown): number | "" {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "number") return v;
  const str = s(v);
  if (!str) return "";
  const cleaned = str.replace(/\./g, "").replace(",", ".");
  const n = parseFloat(cleaned);
  return Number.isNaN(n) ? "" : n;
}

function numOrBlank(v: unknown): number | string {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "number") return v;
  const str = s(v);
  return /^\d+$/.test(str) ? Number(str) : str;
}

/** CPF costuma vir como número no Excel, o que pode comer um zero à esquerda. */
function formatCPF(v: unknown): string {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "number") return String(Math.round(v)).padStart(11, "0");
  const str = s(v);
  return /^\d+$/.test(str) ? str.padStart(11, "0") : str;
}

function coparticipacaoColumns(): string[] {
  return TEMPLATE_SHEETS.find((t) => t.name === "Coparticipação")!.columns;
}

export type CoparticipacaoResult = {
  headers: string[];
  rows: unknown[][];
};

// ---------------------------------------------------------------------
// Formato 1: DIRF COPAY COMPLETA (linhas TPSE / DTPS)
// ---------------------------------------------------------------------

/** Procura, nas primeiras linhas, o cabeçalho "Código do Registro / CPF Titular". */
export function detectDirfCopayCompleta(aoa: unknown[][]): number | null {
  const limit = Math.min(aoa.length, 20);
  for (let r = 0; r < limit; r++) {
    const row = aoa[r] ?? [];
    if (
      normalizeHeader(row[0]) === "CODIGO DO REGISTRO" &&
      normalizeHeader(row[1]).includes("CPF TITULAR")
    ) {
      return r;
    }
  }
  return null;
}

export function parseDirfCopayCompleta(
  aoa: unknown[][],
  headerRowIndex: number
): CoparticipacaoResult {
  const columns = coparticipacaoColumns();
  const rows: unknown[][] = [];

  for (let r = headerRowIndex + 1; r < aoa.length; r++) {
    const raw = aoa[r] ?? [];
    const tipo = s(raw[0]);
    if (tipo !== "TPSE" && tipo !== "DTPS") continue;

    const subfatura = s(raw[3]);
    const certificado = numOrBlank(raw[2]);
    const nomeTitular = s(raw[4]);

    let nomeSegurado: string;
    let cpf: string;
    let valor: unknown;

    if (tipo === "TPSE") {
      // cobrança do próprio titular
      nomeSegurado = nomeTitular;
      cpf = formatCPF(raw[1]);
      valor = toNumber(raw[10]);
    } else {
      // DTPS: cobrança de um dependente
      nomeSegurado = s(raw[7]);
      cpf = formatCPF(raw[5]);
      valor = toNumber(raw[10]);
    }

    const row = columns.map((col) => {
      switch (col) {
        case "NUMERO DA SUBFATURA":
          return subfatura;
        case "NUMERO DO CERTIFICADO":
          return certificado;
        case "TITULAR":
          return nomeTitular;
        case "NOME DO SEGURADO":
          return nomeSegurado;
        case "CPF":
          return cpf;
        case "VALOR DO FATOR MODERADOR":
          return valor;
        default:
          return "";
      }
    });
    rows.push(row);
  }

  return { headers: columns, rows };
}

// ---------------------------------------------------------------------
// Formato 2: PART. DOS SEGUROS (registros tipo 1/2/3, valor já agregado)
// ---------------------------------------------------------------------

export function detectParticSegurado(aoa: unknown[][]): boolean {
  const row0 = (aoa[0] ?? []).map((v) => s(v).toUpperCase());
  const row1 = (aoa[1] ?? []).map((v) => s(v).toUpperCase());
  return (
    row0[0] === "TIPO DE REGISTRO" &&
    row0[1] === "TIPO DE ARQUIVO" &&
    normalizeHeader(row1[1]).startsWith("PARTIC")
  );
}

/**
 * Esse formato já traz o valor agregado por titular (soma do titular +
 * dependentes), então TITULAR e NOME DO SEGURADO saem iguais e CPF não
 * existe nesse arquivo (fica em branco).
 */
export function parseParticSegurado(aoa: unknown[][]): CoparticipacaoResult {
  const columns = coparticipacaoColumns();
  const rows: unknown[][] = [];

  for (const raw of aoa) {
    if (s(raw[0]) !== "2") continue;

    const subfatura = s(raw[2]);
    const certificado = numOrBlank(raw[3]);
    const nome = s(raw[5]);
    const valor = toNumber(raw[7]);

    const row = columns.map((col) => {
      switch (col) {
        case "NUMERO DA SUBFATURA":
          return subfatura;
        case "NUMERO DO CERTIFICADO":
          return certificado;
        case "TITULAR":
          return nome;
        case "NOME DO SEGURADO":
          return nome;
        case "CPF":
          return "";
        case "VALOR DO FATOR MODERADOR":
          return valor;
        default:
          return "";
      }
    });
    rows.push(row);
  }

  return { headers: columns, rows };
}
