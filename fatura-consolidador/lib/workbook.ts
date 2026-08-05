import * as XLSX from "xlsx";
import { TEMPLATE_SHEETS } from "./template";
import { detectFaturaTecnica, parseFaturaTecnicaAnalitico } from "./faturaTecnica";

export type ParsedSheet = {
  name: string;
  headers: string[];
  rows: unknown[][];
  /** true quando esta aba foi gerada por um parser especializado (ex.: Fatura Técnica) */
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

    // Formatos com layout de registros conhecido (ex.: Fatura Técnica) geram
    // uma aba já convertida para o formato do modelo, listada primeiro para
    // ser selecionada por padrão.
    if (detectFaturaTecnica(aoa)) {
      const { headers, rows } = parseFaturaTecnicaAnalitico(aoa);
      sheets.push({
        name: `${name} → Analítico Completo (convertida automaticamente)`,
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

export type TabAssignment = {
  /** Nome da aba do modelo, ex.: "Rateio" */
  templateSheetName: string;
  /** Origem escolhida pelo usuário para essa aba (ou null se vazia) */
  source: {
    fileName: string;
    sheetName: string;
    rows: unknown[][];
    /** coluna do modelo -> índice da coluna na planilha de origem (ou null) */
    mapping: Record<string, number | null>;
  } | null;
};

/**
 * Monta o workbook final seguindo exatamente as 4 abas e cabeçalhos do
 * modelo, preenchendo cada aba com a origem que o usuário escolheu.
 */
export function buildConsolidatedWorkbook(assignments: TabAssignment[]) {
  const wb = XLSX.utils.book_new();

  for (const templateSheet of TEMPLATE_SHEETS) {
    const assignment = assignments.find(
      (a) => a.templateSheetName === templateSheet.name
    );

    const aoa: unknown[][] = [templateSheet.columns];

    if (assignment?.source) {
      const { rows, mapping } = assignment.source;
      for (const row of rows) {
        const outRow = templateSheet.columns.map((col) => {
          const idx = mapping[col];
          if (idx === null || idx === undefined) return "";
          const val = row[idx];
          return val === undefined ? "" : val;
        });
        aoa.push(outRow);
      }
    }

    const ws = XLSX.utils.aoa_to_sheet(aoa);
    XLSX.utils.book_append_sheet(wb, ws, templateSheet.name.slice(0, 31));
  }

  return wb;
}

export function downloadWorkbook(wb: XLSX.WorkBook, fileName: string) {
  XLSX.writeFile(wb, fileName, { compression: true });
}
