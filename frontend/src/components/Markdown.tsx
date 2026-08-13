import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { clsx } from "clsx";

export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div
      className={clsx(
        "prose prose-sm sm:prose-base max-w-none",
        "prose-headings:font-semibold prose-headings:tracking-tight",
        "prose-a:text-accent prose-a:no-underline hover:prose-a:underline",
        "prose-pre:bg-surface-muted prose-code:text-accent",
        "dark:prose-invert",
        className
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
