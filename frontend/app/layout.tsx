import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { ShieldAlert, Users } from "lucide-react";

export const metadata: Metadata = {
  title: "TalentCouncil HRMS - Hiring Council Evaluation",
  description: "Multi-agent hiring council evaluation and audit support",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
        <header className="border-b bg-white shadow-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-bold text-xl text-slate-900">
              <Users className="w-6 h-6 text-indigo-600" />
              <span>TalentCouncil</span>
            </Link>
            <div className="flex items-center gap-4 text-sm text-slate-600">
              <span className="flex items-center gap-1 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                <ShieldAlert className="w-3.5 h-3.5" />
                Human confirmation required
              </span>
            </div>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        <footer className="border-t bg-white py-4 text-center text-xs text-slate-500">
          TalentCouncil • Multi-Agent Hiring Decision Support • Audit-Ready
        </footer>
      </body>
    </html>
  );
}

