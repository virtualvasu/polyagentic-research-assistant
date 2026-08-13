import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { clsx } from "clsx";

export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div
      className={clsx(
        "prose prose-sm sm:prose-base max-w-none",
        "prose-headings:font-display prose-headings:italic prose-headings:font-normal prose-headings:tracking-tight",
        "prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-3 prose-h2:first:mt-0",
        "prose-p:leading-relaxed prose-li:leading-relaxed",
        "prose-a:text-accent prose-a:no-underline hover:prose-a:underline",
        "prose-strong:font-semibold",
        "prose-pre:bg-paper-recessed prose-code:text-accent-strong prose-code:font-mono prose-code:before:content-none prose-code:after:content-none",
        "prose-blockquote:border-accent/40 prose-blockquote:text-ink-muted prose-blockquote:not-italic",
        "prose-hr:border-rule",
        "dark:prose-invert",
        className
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
