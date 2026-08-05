"use client";

import { useMemo, useState } from "react";
import { TEMPLATE_SHEETS } from "@/lib/template";
import {
  buildConsolidatedWorkbook,
  downloadWorkbook,
  type FileSource,
  type TabAssignment,
} from "@/lib/workbook";
import SheetSlot, { EMPTY_SLOT, type SlotState } from "@/components/SheetSlot";

function todayStamp() {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
}

// Só estas duas abas recebem upload. "Movimentações Faturadas" é derivada
// automaticamente do Analítico Completo e "Rateio" sai só com o cabeçalho.
const UPLOAD_TABS = ["Analítico Completo", "Coparticipação"] as const;
const AUTO_TABS = [
  {
    name: "Movimentações Faturadas",
    note: "Preenchida automaticamente com os registros do Analítico Completo que têm TIPO DE LANÇAMENTO preenchido (não vazio). Não é preciso enviar planilha aqui.",
  },
  {
    name: "Rateio",
    note: "Sai apenas com o cabeçalho do modelo — nenhuma regra de preenchimento automático foi definida para esta aba ainda. Não é preciso enviar planilha aqui.",
  },
];

export default function Home() {
  const [slots, setSlots] = useState<Record<string, SlotState>>(() =>
    Object.fromEntries(UPLOAD_TABS.map((name) => [name, EMPTY_SLOT]))
  );
  const [fileName, setFileName] = useState(
    `Planilha_Consolidada_${todayStamp()}.xlsx`
  );
  const [generated, setGenerated] = useState(false);

  const filledCount = useMemo(
    () => Object.values(slots).filter((s) => s.files.length > 0).length,
    [slots]
  );

  function handleGenerate() {
    const assignments: TabAssignment[] = UPLOAD_TABS.map((name) => {
      const slot = slots[name];
      const sources: FileSource[] = slot.files.map((entry) => {
        const sheet = entry.parsed.sheets[entry.sheetIndex];
        return {
          fileName: entry.parsed.fileName,
          sheetName: sheet.name,
          rows: sheet.rows,
          mapping: entry.mapping,
        };
      });
      return { templateSheetName: name, sources };
    });

    const wb = buildConsolidatedWorkbook(assignments);
    const name = fileName.trim().endsWith(".xlsx")
      ? fileName.trim()
      : `${fileName.trim() || "Planilha_Consolidada"}.xlsx`;
    downloadWorkbook(wb, name);
    setGenerated(true);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Consolidador de Faturas
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
          Gera uma planilha nova seguindo exatamente o modelo{" "}
          <span className="font-medium">&ldquo;Resumo da Fatura&rdquo;</span>{" "}
          (4 abas: Analítico Completo, Coparticipação, Movimentações
          Faturadas e Rateio). Envie, para o Analítico Completo e para a
          Coparticipação, a(s) planilha(s) com os dados correspondentes —
          dá para enviar mais de um arquivo por aba. Formatos conhecidos
          (Fatura Técnica, DIRF Copay Completa, Part. dos Segurados) são
          detectados e convertidos automaticamente; o sistema também tenta
          casar as demais colunas pelo nome e você pode ajustar o
          mapeamento antes de gerar.
        </p>
        <p className="mt-2 max-w-2xl rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
          🔒 Tudo acontece no seu navegador: os arquivos que você envia
          (com CPF e dados de saúde) nunca são enviados a nenhum servidor.
        </p>
      </header>

      <div className="space-y-4">
        {UPLOAD_TABS.map((name) => {
          const ts = TEMPLATE_SHEETS.find((t) => t.name === name)!;
          return (
            <SheetSlot
              key={ts.name}
              templateSheet={ts}
              state={slots[ts.name]}
              onChange={(next) => {
                setSlots((prev) => ({ ...prev, [ts.name]: next }));
                setGenerated(false);
              }}
            />
          );
        })}

        {AUTO_TABS.map(({ name, note }) => {
          const ts = TEMPLATE_SHEETS.find((t) => t.name === name)!;
          return (
            <div
              key={ts.name}
              className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/50"
            >
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                {ts.name}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {ts.description}
              </p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                ⚙️ {note}
              </p>
            </div>
          );
        })}
      </div>

      <div className="mt-8 flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-500 dark:text-slate-400">
            Nome do arquivo a gerar
          </label>
          <input
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
            className="mt-1 w-full max-w-sm rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {filledCount} de {UPLOAD_TABS.length} aba(s) com planilha
            enviada. Movimentações Faturadas é gerada automaticamente e
            Rateio sai só com o cabeçalho.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={filledCount === 0}
          className="rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
        >
          Gerar e baixar planilha
        </button>
      </div>

      {generated && (
        <p className="mt-4 text-sm text-emerald-600 dark:text-emerald-400">
          ✓ Planilha gerada e baixada. Confira a pasta de downloads do
          navegador.
        </p>
      )}
    </main>
  );
}
