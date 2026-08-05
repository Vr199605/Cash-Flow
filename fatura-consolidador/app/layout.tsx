import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Consolidador de Faturas",
  description:
    "Gera planilhas de fatura seguindo um modelo fixo, a partir de arquivos que você envia — tudo processado no navegador.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
        {children}
      </body>
    </html>
  );
}
