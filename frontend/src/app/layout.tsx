import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import { FlaskConical, History } from "lucide-react";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Polyagentic Research Assistant",
  description: "A supervised multi-agent LangGraph workflow that researches, drafts, and critiques a report on any topic.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <header className="border-b border-border bg-surface/80 backdrop-blur supports-[backdrop-filter]:bg-surface/60 sticky top-0 z-20">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
              <FlaskConical className="size-5 text-accent" strokeWidth={2} />
              <span>Polyagentic Research Assistant</span>
            </Link>
            <nav className="flex items-center gap-1">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-md text-sm text-muted hover:text-foreground hover:bg-surface-muted transition-colors"
              >
                New Research
              </Link>
              <Link
                href="/history"
                className="px-3 py-1.5 rounded-md text-sm text-muted hover:text-foreground hover:bg-surface-muted transition-colors flex items-center gap-1.5"
              >
                <History className="size-4" />
                History
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border py-6">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 text-xs text-muted flex items-center justify-between">
            <span>LangGraph &middot; FastAPI &middot; Next.js</span>
            <a
              href="https://github.com/virtualvasu/polyagentic-research-assistant"
              className="hover:text-foreground transition-colors"
            >
              Source
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
