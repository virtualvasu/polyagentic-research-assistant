"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Trash2 } from "lucide-react";

export function DeleteReportButton({ id }: { id: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  return (
    <button
      onClick={async () => {
        if (!confirm("Delete this saved report?")) return;
        setBusy(true);
        await fetch(`/api/reports/${id}`, { method: "DELETE" });
        router.push("/history");
        router.refresh();
      }}
      disabled={busy}
      className="shrink-0 inline-flex items-center gap-1.5 rounded-sm border border-danger/30 px-3.5 py-2 text-sm font-medium text-danger hover:bg-danger-wash disabled:opacity-50"
    >
      <Trash2 className="size-4" />
      {busy ? "Deleting…" : "Delete"}
    </button>
  );
}
