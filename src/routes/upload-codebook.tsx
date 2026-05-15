import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import {
  UploadCloud,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useCodebook, useCodebookMeta, useUploadCodebook } from "@/api/client";
import type { CodebookVariable } from "@/types";

export const Route = createFileRoute("/upload-codebook")({
  component: UploadCodebookPage,
});

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function CodebookTable({ rows }: { rows: CodebookVariable[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px] min-w-[600px]">
        <thead>
          <tr className="bg-primary text-primary-foreground">
            <th className="text-left px-3 h-9 font-medium whitespace-nowrap">variable_name</th>
            <th className="text-left px-3 h-9 font-medium">description</th>
            <th className="text-left px-3 h-9 font-medium whitespace-nowrap">dType</th>
            <th className="text-left px-3 h-9 font-medium">Unit</th>
            <th className="text-left px-3 h-9 font-medium">Categories</th>
            <th className="text-left px-3 h-9 font-medium whitespace-nowrap">Unit Example</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.variable_name} style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}>
              <td className="px-3 h-8 font-mono text-[11px] whitespace-nowrap">{r.variable_name}</td>
              <td className="px-3 h-8">{r.description}</td>
              <td className="px-3 h-8 text-text-secondary">{r.dType ?? "—"}</td>
              <td className="px-3 h-8 text-text-secondary">{r.unit ?? "—"}</td>
              <td className="px-3 h-8 text-text-secondary">{r.categories ?? "—"}</td>
              <td className="px-3 h-8 text-text-secondary">{r.unit_example ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UploadCodebookPage() {
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [formatOpen, setFormatOpen] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: codebook } = useCodebook();
  const { data: meta } = useCodebookMeta();
  const upload = useUploadCodebook();

  const rows = codebook ?? [];
  const warnings = upload.data?.warnings ?? [];

  const handleFile = (f: File) => {
    if (!f.name.endsWith(".csv")) return;
    setPendingFile(f);
  };

  const handleUpload = () => {
    if (!pendingFile) return;
    upload.mutate(pendingFile, { onSuccess: () => setPendingFile(null) });
  };

  return (
    <div>
      <PageHeader
        title="Upload Target Codebook"
        subtitle="Upload the canonical variable list that all study datasets will be mapped to."
      />

      {/* ── Last upload banner ─────────────────────────────── */}
      {meta?.exists && meta.filename && (
        <div className="mb-5 flex items-start gap-3 px-4 py-3 rounded-md bg-primary-light border border-primary/30 text-[13px]">
          <Info className="size-4 text-primary mt-0.5 shrink-0" />
          <span className="text-text-primary">
            Last codebook upload:{" "}
            <strong>{meta.filename}</strong> —{" "}
            {meta.row_count} variables
            {meta.uploaded_at && (
              <span className="text-text-secondary"> • {formatTimestamp(meta.uploaded_at)}</span>
            )}
          </span>
        </div>
      )}

      {/* ── Two-column layout ──────────────────────────────── */}
      <div className="grid grid-cols-2 gap-6 items-start">

        {/* LEFT: upload form */}
        <div className="space-y-4">
          <p className="text-[13px] text-text-secondary">
            To upload a new codebook, complete the form below.
          </p>

          {/* Drop zone */}
          <div
            className="border-2 border-dashed border-border rounded-lg p-6 text-center bg-surface hover:border-primary transition-colors cursor-pointer"
            onClick={() => inputRef.current?.click()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
            onDragOver={(e) => e.preventDefault()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            <UploadCloud className="size-7 text-text-secondary mx-auto" />
            <div className="mt-2 text-[13px] font-medium text-text-primary">
              {pendingFile ? pendingFile.name : "Target Codebook"}
            </div>
            <div className="text-[11px] text-text-secondary mt-0.5">
              {pendingFile
                ? `${(pendingFile.size / 1024).toFixed(0)} KB — ready to upload`
                : "Drag and drop file here · CSV only · max 10 MB"}
            </div>
            {!pendingFile && (
              <span className="mt-3 inline-block px-3 py-1 rounded border text-[12px] text-text-primary hover:bg-[#F5F0EE]">
                Browse files
              </span>
            )}
          </div>

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={!pendingFile || upload.isPending}
            className="w-full h-10 rounded-md border-2 border-primary text-primary font-medium text-[14px] hover:bg-primary-light transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {upload.isPending ? "Uploading…" : "Upload Codebook"}
          </button>

          {/* Success / error feedback */}
          {upload.isSuccess && (
            <div className="flex items-center gap-2 text-[12px] text-success">
              <CheckCircle2 className="size-4" />
              Uploaded — {upload.data.row_count} variables loaded
            </div>
          )}
          {warnings.map((w, i) => (
            <div key={i} className="flex items-center gap-2 text-[12px] text-accent">
              <AlertTriangle className="size-4 shrink-0" />
              {w}
            </div>
          ))}
          {upload.isError && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200 text-[12px] text-red-700">
              {(upload.error as Error).message}
            </div>
          )}

          {/* ── Format help expander ───────────────────────── */}
          <div className="border rounded-lg bg-surface shadow-sm">
            <button
              onClick={() => setFormatOpen((o) => !o)}
              className="w-full flex items-center justify-between px-4 py-3 text-[13px] font-medium"
            >
              <span>Codebook CSV format (required columns)</span>
              {formatOpen
                ? <ChevronDown className="size-4 text-text-secondary" />
                : <ChevronRight className="size-4 text-text-secondary" />
              }
            </button>
            {formatOpen && (
              <div className="px-4 pb-4 space-y-2 border-t text-[12px] text-text-primary">
                <ul className="mt-3 space-y-1.5 list-disc list-inside text-text-secondary">
                  <li>
                    <strong className="text-text-primary">Required:</strong>{" "}
                    <code className="font-mono">variable_name</code>,{" "}
                    <code className="font-mono">description</code>
                  </li>
                  <li>
                    <strong className="text-text-primary">Optional:</strong>{" "}
                    <code className="font-mono">dType</code>,{" "}
                    <code className="font-mono">Unit</code>,{" "}
                    <code className="font-mono">Categories</code>,{" "}
                    <code className="font-mono">Unit Example</code>
                  </li>
                  <li>
                    <strong className="text-text-primary">dType supports:</strong>{" "}
                    <code className="font-mono">float</code>,{" "}
                    <code className="font-mono">integer</code>,{" "}
                    <code className="font-mono">string</code>,{" "}
                    <code className="font-mono">boolean</code>{" "}
                    (other values accepted but default handling applies)
                  </li>
                  <li>
                    <strong className="text-text-primary">Study variables CSV:</strong>{" "}
                    must also have <code className="font-mono">variable_name</code>,{" "}
                    <code className="font-mono">description</code> (description may be empty)
                  </li>
                  <li>
                    <strong className="text-text-primary">Example data CSV (optional):</strong>{" "}
                    column names must match <code className="font-mono">variable_name</code>{" "}
                    in the variables CSV
                  </li>
                </ul>

                {/* Sample format image */}
                <div className="mt-4">
                  <p className="text-[11px] text-text-secondary mb-2">Example of expected CSV format:</p>
                  <img
                    src="/sample_data.png"
                    alt="Sample codebook CSV format"
                    className="w-full rounded border shadow-sm"
                  />
                </div>

              </div>
            )}
          </div>
        </div>

        {/* RIGHT: current codebook preview */}
        <div>
          <h2 className="section-heading mb-3">Target Codebook</h2>
          {rows.length === 0 ? (
            <div className="border rounded-lg bg-surface p-8 text-center text-[13px] text-text-secondary">
              No codebook uploaded yet.
            </div>
          ) : (
            <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
              <CodebookTable rows={rows.slice(0, 10)} />
              <div className="px-3 py-2 border-t text-[11px] text-text-secondary">
                Showing 10 of {rows.length} variables
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
