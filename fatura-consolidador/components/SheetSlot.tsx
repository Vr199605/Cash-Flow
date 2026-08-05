"use client";

import { useRef, useState } from "react";
import type { TemplateSheet } from "@/lib/template";
import { parseSourceFile, type ParsedSource } from "@/lib/workbook";
import { autoMapColumns } from "@/lib/normalize";

export type SlotState = {
  parsed: ParsedSource | null;
  sheetIndex: number;
  mapping: Record<string, number | null>;
};

export const EMPTY_SLOT: SlotState = {
  parsed: null,
  sheetIndex: 0,
  mapping: {},
};

function formatCell(v: unknown): string {
  if (v instanceof Date) return v.toLocaleDateString("pt-BR");
  if (v === null || v === undefined) return "";
  return String(v);
}

export default function SheetSlot({
  templateSheet,
  state,
  onChange,
}: {
  templateSheet: TemplateSheet;
  state: SlotState;
  onChange: (next: SlotState) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const currentSheet = state.parsed?.sheets[state.sheetIndex] ?? null;

  async function handleFile(file: File) {
    setLoading(true);
    setError(null);
    try {
      const parsed = await parseSourceFile(file);
      if (parsed.sheets.length === 0 || parsed.sheets[0].headers.length === 0) {
        throw new Error(
          "Não encontrei cabeçalhos na primeira linha desse arquivo."
        );
      }
      const mapping = autoMapColumns(
        templateSheet.columns,
        parsed.sheets[0].headers
      );
      onChange({ parsed, sheetIndex: 0, mapping });
      setExpanded(true);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Não foi possível ler esse arquivo."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSheetChange(idx: number) {
    if (!state.parsed) return;
    const mapping = autoMapColumns(
      templateSheet.columns,
      state.parsed.sheets[idx].headers
    );
    onChange({ ...state, sheetIndex: idx, mapping });
  }

  function handleMappingChange(col: string, idx: number | null) {
    onChange({ ...state, mapping: { ...state.mapping, [col]: idx } });
  }

  function clear() {
    onChange(EMPTY_SLOT);
    if (inputRef.current) inputRef.current.value = "";
  }

  const mappedCount = Object.values(state.mapping).filter(
    (v) => v !== null
  ).length;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3 p-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            {templateSheet.name}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {templateSheet.description}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {state.parsed && (
            <button
              onClick={clear}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Remover
            </button>
          )}
          <label className="cursor-pointer rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">
            {state.parsed ? "Trocar arquivo" : "Enviar planilha"}
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls,.csv,.ods"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
          </label>
        </div>
      </div>

      {loading && (
        <p className="px-4 pb-4 text-sm text-slate-500">Lendo arquivo…</p>
      )}
      {error && (
        <p className="px-4 pb-4 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      {state.parsed && currentSheet && (
        <div className="border-t border-slate-100 px-4 py-3 dark:border-slate-800">
          {currentSheet.autoConverted && (
            <p className="mb-3 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300">
              ℹ️ Formato <strong>Fatura Técnica</strong> detectado e
              convertido automaticamente. Sexo, estado civil e grau de
              parentesco foram convertidos de código para texto; idade
              calculada em relação à competência da fatura. CPF e IOF não
              existem nesse arquivo e ficam em branco — TOTAL sai igual ao
              VALOR DO LANÇAMENTO (sem IOF).
            </p>
          )}
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <div className="text-slate-600 dark:text-slate-300">
              <span className="font-medium">{state.parsed.fileName}</span>{" "}
              · {currentSheet.rows.length} linha(s) detectada(s) ·{" "}
              {mappedCount}/{templateSheet.columns.length} coluna(s)
              mapeada(s)
            </div>
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-brand-600 hover:underline dark:text-brand-400"
            >
              {expanded ? "Ocultar mapeamento" : "Ver / ajustar mapeamento"}
            </button>
          </div>

          {expanded && (
            <div className="mt-3 space-y-3">
              {state.parsed.sheets.length > 1 && (
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400">
                    Aba do arquivo enviado a usar como origem
                  </label>
                  <select
                    value={state.sheetIndex}
                    onChange={(e) =>
                      handleSheetChange(Number(e.target.value))
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800"
                  >
                    {state.parsed.sheets.map((s, i) => (
                      <option key={s.name} value={i}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700">
                <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
                  <thead className="bg-slate-50 dark:bg-slate-800">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                        Coluna do modelo
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                        Coluna na planilha enviada
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {templateSheet.columns.map((col) => (
                      <tr key={col}>
                        <td className="px-3 py-1.5 text-slate-700 dark:text-slate-200">
                          {col}
                        </td>
                        <td className="px-3 py-1.5">
                          <select
                            value={state.mapping[col] ?? ""}
                            onChange={(e) =>
                              handleMappingChange(
                                col,
                                e.target.value === ""
                                  ? null
                                  : Number(e.target.value)
                              )
                            }
                            className="w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
                          >
                            <option value="">— não preencher —</option>
                            {currentSheet.headers.map((h, i) => (
                              <option key={i} value={i}>
                                {h || `Coluna ${i + 1}`}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {currentSheet.rows.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">
                    Prévia (3 primeiras linhas da origem)
                  </p>
                  <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700">
                    <table className="min-w-full text-xs">
                      <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                          {currentSheet.headers.map((h, i) => (
                            <th
                              key={i}
                              className="whitespace-nowrap px-2 py-1 text-left font-medium text-slate-500 dark:text-slate-400"
                            >
                              {h || `Coluna ${i + 1}`}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {currentSheet.rows.slice(0, 3).map((row, ri) => (
                          <tr
                            key={ri}
                            className="border-t border-slate-100 dark:border-slate-800"
                          >
                            {currentSheet.headers.map((_, ci) => (
                              <td
                                key={ci}
                                className="whitespace-nowrap px-2 py-1 text-slate-600 dark:text-slate-300"
                              >
                                {formatCell(row[ci])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
