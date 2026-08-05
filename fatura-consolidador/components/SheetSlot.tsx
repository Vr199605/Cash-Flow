"use client";

import { useRef, useState } from "react";
import type { TemplateSheet } from "@/lib/template";
import { parseSourceFile, type ParsedSource } from "@/lib/workbook";
import { autoMapColumns } from "@/lib/normalize";

export type FileEntryState = {
  id: string;
  parsed: ParsedSource;
  sheetIndex: number;
  mapping: Record<string, number | null>;
};

export type SlotState = {
  files: FileEntryState[];
};

export const EMPTY_SLOT: SlotState = { files: [] };

function formatCell(v: unknown): string {
  if (v instanceof Date) return v.toLocaleDateString("pt-BR");
  if (v === null || v === undefined) return "";
  return String(v);
}

function newId() {
  return Math.random().toString(36).slice(2);
}

function FileEntryCard({
  templateSheet,
  entry,
  onChange,
  onRemove,
}: {
  templateSheet: TemplateSheet;
  entry: FileEntryState;
  onChange: (next: FileEntryState) => void;
  onRemove: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const currentSheet = entry.parsed.sheets[entry.sheetIndex];

  function handleSheetChange(idx: number) {
    const mapping = autoMapColumns(
      templateSheet.columns,
      entry.parsed.sheets[idx].headers
    );
    onChange({ ...entry, sheetIndex: idx, mapping });
  }

  function handleMappingChange(col: string, idx: number | null) {
    onChange({ ...entry, mapping: { ...entry.mapping, [col]: idx } });
  }

  const mappedCount = Object.values(entry.mapping).filter(
    (v) => v !== null
  ).length;

  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700">
      {currentSheet.autoConverted && (
        <p className="m-3 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300">
          ℹ️ Formato conhecido detectado e convertido automaticamente.
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
        <div className="text-slate-600 dark:text-slate-300">
          <span className="font-medium">{entry.parsed.fileName}</span> ·{" "}
          {currentSheet.rows.length} linha(s) detectada(s) · {mappedCount}/
          {templateSheet.columns.length} coluna(s) mapeada(s)
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-brand-600 hover:underline dark:text-brand-400"
          >
            {expanded ? "Ocultar mapeamento" : "Ver / ajustar mapeamento"}
          </button>
          <button
            onClick={onRemove}
            className="text-red-600 hover:underline dark:text-red-400"
          >
            Remover
          </button>
        </div>
      </div>

      {expanded && (
        <div className="space-y-3 border-t border-slate-100 p-3 dark:border-slate-800">
          {entry.parsed.sheets.length > 1 && (
            <div>
              <label className="block text-xs font-medium text-slate-500 dark:text-slate-400">
                Aba do arquivo enviado a usar como origem
              </label>
              <select
                value={entry.sheetIndex}
                onChange={(e) => handleSheetChange(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800"
              >
                {entry.parsed.sheets.map((s, i) => (
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
                        value={entry.mapping[col] ?? ""}
                        onChange={(e) =>
                          handleMappingChange(
                            col,
                            e.target.value === "" ? null : Number(e.target.value)
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
  );
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

  async function handleFiles(fileList: FileList) {
    setLoading(true);
    setError(null);
    const newEntries: FileEntryState[] = [];
    try {
      for (const file of Array.from(fileList)) {
        const parsed = await parseSourceFile(file);
        if (parsed.sheets.length === 0 || parsed.sheets[0].headers.length === 0) {
          throw new Error(
            `Não encontrei cabeçalhos na primeira linha de "${file.name}".`
          );
        }
        const mapping = autoMapColumns(
          templateSheet.columns,
          parsed.sheets[0].headers
        );
        newEntries.push({ id: newId(), parsed, sheetIndex: 0, mapping });
      }
      onChange({ files: [...state.files, ...newEntries] });
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Não foi possível ler um dos arquivos."
      );
    } finally {
      setLoading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function updateEntry(id: string, next: FileEntryState) {
    onChange({
      files: state.files.map((f) => (f.id === id ? next : f)),
    });
  }

  function removeEntry(id: string) {
    onChange({ files: state.files.filter((f) => f.id !== id) });
  }

  const totalRows = state.files.reduce(
    (sum, f) => sum + f.parsed.sheets[f.sheetIndex].rows.length,
    0
  );

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3 p-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            {templateSheet.name}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {templateSheet.description}
            {state.files.length > 0 &&
              ` · ${state.files.length} arquivo(s) · ${totalRows} linha(s) no total`}
          </p>
        </div>

        <label className="cursor-pointer rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">
          + Adicionar planilha
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".xlsx,.xls,.csv,.ods"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFiles(e.target.files);
              }
            }}
          />
        </label>
      </div>

      {loading && (
        <p className="px-4 pb-4 text-sm text-slate-500">Lendo arquivo(s)…</p>
      )}
      {error && (
        <p className="px-4 pb-4 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      {state.files.length === 0 ? (
        <p className="px-4 pb-4 text-sm text-slate-400 dark:text-slate-500">
          Nenhuma planilha enviada ainda.
        </p>
      ) : (
        <div className="space-y-3 border-t border-slate-100 p-4 dark:border-slate-800">
          {state.files.map((entry) => (
            <FileEntryCard
              key={entry.id}
              templateSheet={templateSheet}
              entry={entry}
              onChange={(next) => updateEntry(entry.id, next)}
              onRemove={() => removeEntry(entry.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
