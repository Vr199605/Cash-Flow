// Normaliza texto para comparar cabeçalhos vindos de planilhas diferentes
// (maiúsculas/minúsculas, acentos, espaços duplos, pontuação leve).
export function normalizeHeader(value: unknown): string {
  const s = String(value ?? "").trim();
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // remove acentos
    .toUpperCase()
    .replace(/[._-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Tenta casar automaticamente cada coluna do modelo com uma coluna da
 * planilha enviada. Primeiro tenta igualdade exata (normalizada), depois
 * uma correspondência por inclusão (uma string contém a outra).
 */
export function autoMapColumns(
  templateColumns: string[],
  sourceHeaders: string[]
): Record<string, number | null> {
  const normSource = sourceHeaders.map(normalizeHeader);
  const mapping: Record<string, number | null> = {};

  for (const col of templateColumns) {
    const normCol = normalizeHeader(col);
    let idx = normSource.findIndex((h) => h === normCol);

    if (idx === -1) {
      idx = normSource.findIndex(
        (h) => h.length > 0 && (h.includes(normCol) || normCol.includes(h))
      );
    }

    mapping[col] = idx !== -1 ? idx : null;
  }

  return mapping;
}
