import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import { History } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import "./globals.css";

// Runs before paint so an explicit theme choice applies immediately —
// otherwise the page would flash the OS-preferred theme first.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var t = localStorage.getItem("theme");
    if (t === "light" || t === "dark") {
      document.documentElement.setAttribute("data-theme", t);
    }
  } catch (e) {}
})();
`;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  axes: ["opsz", "SOFT"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Polyagentic Research Assistant",
  description: "A supervised multi-agent LangGraph workflow that researches, drafts, and critiques a report on any topic.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-paper text-ink">
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <header className="border-b border-rule bg-paper/90 backdrop-blur supports-[backdrop-filter]:bg-paper/75 sticky top-0 z-20">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
            <Link href="/" className="flex items-center gap-2 min-w-0 shrink">
              <span
                aria-hidden
                className="shrink-0 size-6 rounded-sm border border-accent/40 bg-accent-wash text-accent flex items-center justify-center font-display italic text-sm"
              >
                R
              </span>
              <span className="font-display italic text-base sm:text-lg tracking-tight truncate">
                Polyagentic Research Assistant
              </span>
            </Link>
            <nav className="flex items-center gap-1 shrink-0">
              <Link
                href="/research"
                className="px-2.5 sm:px-3 py-1.5 rounded-md text-sm text-ink-muted hover:text-ink hover:bg-paper-recessed transition-colors"
              >
                New
              </Link>
              <Link
                href="/history"
                className="px-2.5 sm:px-3 py-1.5 rounded-md text-sm text-ink-muted hover:text-ink hover:bg-paper-recessed transition-colors flex items-center gap-1.5"
              >
                <History className="size-4" />
                <span className="hidden sm:inline">History</span>
              </Link>
              <span className="w-px h-5 bg-rule mx-1" aria-hidden />
              <ThemeToggle />
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-rule py-6">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 text-xs text-ink-muted flex items-center justify-between font-mono">
            <span>LangGraph &middot; FastAPI &middot; Next.js</span>
            <a
              href="https://github.com/virtualvasu/polyagentic-research-assistant"
              className="hover:text-ink transition-colors"
            >
              Source
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
