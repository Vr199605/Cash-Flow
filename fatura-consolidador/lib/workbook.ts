import * as XLSX from "xlsx";
import { TEMPLATE_SHEETS } from "./template";
import { detectFaturaTecnica, parseFaturaTecnicaAnalitico } from "./faturaTecnica";
import {
  detectDirfCopayCompleta,
  parseDirfCopayCompleta,
  detectParticSegurado,
  parseParticSegurado,
} from "./coparticipacao";

export type ParsedSheet = {
  name: string;
  headers: string[];
  rows: unknown[][];
  /** true quando esta aba foi gerada por um parser especializado (ex.: Fatura Técnica, DIRF Copay) */
  autoConverted?: boolean;
};

export type ParsedSource = {
  fileName: string;
  sheets: ParsedSheet[];
};

/** Lê um arquivo (.xlsx, .xls, .csv, .ods) enviado pelo usuário, inteiramente no navegador. */
export async function parseSourceFile(file: File): Promise<ParsedSource> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array", cellDates: true });

  const sheets: ParsedSheet[] = [];

  for (const name of wb.SheetNames) {
    const ws = wb.Sheets[name];
    const aoa = XLSX.utils.sheet_to_json<unknown[]>(ws, {
      header: 1,
      raw: true,
      defval: "",
      blankrows: false,
    });

    // Formatos com layout conhecido geram uma aba já convertida para o
    // formato do modelo, listada primeiro para ser selecionada por padrão.
    if (detectFaturaTecnica(aoa)) {
      const { headers, rows } = parseFaturaTecnicaAnalitico(aoa);
      sheets.push({
        name: `${name} → Analítico Completo (convertida automaticamente)`,
        headers,
        rows,
        autoConverted: true,
      });
    }

    const dirfHeaderRow = detectDirfCopayCompleta(aoa);
    if (dirfHeaderRow !== null) {
      const { headers, rows } = parseDirfCopayCompleta(aoa, dirfHeaderRow);
      sheets.push({
        name: `${name} → Coparticipação (convertida automaticamente)`,
        headers,
        rows,
        autoConverted: true,
      });
    }

    if (detectParticSegurado(aoa)) {
      const { headers, rows } = parseParticSegurado(aoa);
      sheets.push({
        name: `${name} → Coparticipação (convertida automaticamente)`,
        headers,
        rows,
        autoConverted: true,
      });
    }

    const [headerRow, ...rest] = aoa.length > 0 ? aoa : [[]];
    const headers = (headerRow ?? []).map((h) => String(h ?? "").trim());
    sheets.push({ name, headers, rows: rest });
  }

  return { fileName: file.name, sheets };
}

export type FileSource = {
  fileName: string;
  sheetName: string;
  rows: unknown[][];
  /** coluna do modelo -> índice da coluna na planilha de origem (ou null) */
  mapping: Record<string, number | null>;
};

export type TabAssignment = {
  /** Nome da aba do modelo, ex.: "Coparticipação" */
  templateSheetName: string;
  /** Uma ou mais planilhas enviadas para essa aba (podem ser somadas) */
  sources: FileSource[];
};

const ANALITICO = "Analítico Completo";
const MOVIMENTACOES = "Movimentações Faturadas";
const MOVIMENTACOES_COLUNAS_ORIGEM = [
  "NUMERO DA SUBFATURA",
  "TIPO DE BENEFICIÁRIO",
  "NOME TITULAR",
  "CPF TITULAR",
  "NOME SEGURADO/DEPENDENTE",
  "CPF SEGURADO/DEPENDENTE",
  "NOME DO LANÇAMENTO",
] as const;

function sourcesToObjectRows(
  templateColumns: string[],
  sources: FileSource[]
): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = [];
  for (const src of sources) {
    for (const row of src.rows) {
      const obj: Record<string, unknown> = {};
      for (const col of templateColumns) {
        const idx = src.mapping[col];
        const val = idx === null || idx === undefined ? "" : row[idx];
        obj[col] = val === undefined ? "" : val;
      }
      out.push(obj);
    }
  }
  return out;
}

function objectRowsToAoa(
  templateColumns: string[],
  rows: Record<string, unknown>[]
): unknown[][] {
  return [
    templateColumns,
    ...rows.map((r) => templateColumns.map((c) => r[c] ?? "")),
  ];
}

/**
 * A aba "Movimentações Faturadas" não recebe upload: é montada a partir
 * dos registros do "Analítico Completo" que têm TIPO DE LANÇAMENTO
 * preenchido (não vazio).
 */
export function deriveMovimentacoesFaturadas(
  analiticoRows: Record<string, unknown>[]
): Record<string, unknown>[] {
  return analiticoRows
    .filter((r) => String(r["TIPO DE LANÇAMENTO"] ?? "").trim() !== "")
    .map((r) =>
      Object.fromEntries(
        MOVIMENTACOES_COLUNAS_ORIGEM.map((c) => [c, r[c] ?? ""])
      )
    );
}

/**
 * Monta o workbook final seguindo exatamente as 4 abas e cabeçalhos do
 * modelo. "Analítico Completo" e "Coparticipação" usam os arquivos que o
 * usuário enviou; "Movimentações Faturadas" é derivada automaticamente do
 * Analítico Completo; "Rateio" sai apenas com o cabeçalho (nenhuma regra
 * de preenchimento automático foi definida para ela).
 */
export function buildConsolidatedWorkbook(assignments: TabAssignment[]) {
  const wb = XLSX.utils.book_new();

  const analiticoTemplate = TEMPLATE_SHEETS.find((t) => t.name === ANALITICO)!;
  const analiticoAssignment = assignments.find(
    (a) => a.templateSheetName === ANALITICO
  );
  const analiticoRows = sourcesToObjectRows(
    analiticoTemplate.columns,
    analiticoAssignment?.sources ?? []
  );

  for (const templateSheet of TEMPLATE_SHEETS) {
    let rows: Record<string, unknown>[];

    if (templateSheet.name === ANALITICO) {
      rows = analiticoRows;
    } else if (templateSheet.name === MOVIMENTACOES) {
      rows = deriveMovimentacoesFaturadas(analiticoRows);
    } else {
      const assignment = assignments.find(
        (a) => a.templateSheetName === templateSheet.name
      );
      rows = sourcesToObjectRows(
        templateSheet.columns,
        assignment?.sources ?? []
      );
    }

    const aoa = objectRowsToAoa(templateSheet.columns, rows);
    const ws = XLSX.utils.aoa_to_sheet(aoa);
    XLSX.utils.book_append_sheet(wb, ws, templateSheet.name.slice(0, 31));
  }

  return wb;
}

export function downloadWorkbook(wb: XLSX.WorkBook, fileName: string) {
  XLSX.writeFile(wb, fileName, { compression: true });
}
