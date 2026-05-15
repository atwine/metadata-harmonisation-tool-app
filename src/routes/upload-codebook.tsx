import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import {
  UploadCloud,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useCodebook, useUploadCodebook } from "@/api/client";

export const Route = createFileRoute("/upload-codebook")({
  component: UploadCodebookPage,
});

function UploadCodebookPage() {
  const [validationOpen, setValidationOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: codebook } = useCodebook();
  const upload = useUploadCodebook();

  const handleFile = (f: File) => {
    if (!f.name.endsWith(".csv")) return;
    setPendingFile(f);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleUpload = () => {
    if (!pendingFile) return;
    upload.mutate(pendingFile);
  };

  const response = upload.data;
  const warnings = response?.warnings ?? [];
  const rows = codebook ?? [];

  const displayFile = pendingFile
    ? `${pendingFile.name} · ${(pendingFile.size / 1024).toFixed(0)} KB`
    : response
      ? `${rows.length} variables loaded`
      : null;

  return (
    <div className="max-w-[720px] mx-auto">
      <PageHeader
        title="Upload Target Codebook"
        subtitle="Upload the canonical variable list that all study datasets will be mapped to."
      />

      <div
        className="border-2 border-dashed border-border rounded-lg p-8 text-center bg-surface hover:border-primary transition-colors cursor-pointer"
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        <UploadCloud className="size-8 text-text-secondary mx-auto" />
        <div className="mt-3 text-[14px] text-text-primary">
          Drop your codebook CSV here, or click to browse
        </div>
        <div className="text-[12px] text-text-secondary mt-1">
          CSV only · max 10 MB
        </div>
        {displayFile && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-light text-primary text-[12px] font-medium">
            {displayFile}
          </div>
        )}
      </div>

      {rows.length > 0 && (
        <div className="mt-6 bg-surface border rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-primary text-primary-foreground">
                <th className="text-left px-3 h-9 font-medium">variable_name</th>
                <th className="text-left px-3 h-9 font-medium">description</th>
                <th className="text-left px-3 h-9 font-medium">dType</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 10).map((r, i) => (
                <tr
                  key={r.variable_name}
                  style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
                >
                  <td className="px-3 h-9 font-mono text-[12px]">{r.variable_name}</td>
                  <td className="px-3 h-9">{r.description}</td>
                  <td className="px-3 h-9 text-text-secondary">{r.dType ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length > 10 && (
            <div className="px-3 py-2 text-[12px] text-text-secondary border-t">
              … and {rows.length - 10} more rows
            </div>
          )}
        </div>
      )}

      {(warnings.length > 0 || upload.isSuccess) && (
        <div className="mt-4 bg-surface border rounded-lg shadow-sm">
          <button
            onClick={() => setValidationOpen((o) => !o)}
            className="w-full flex items-center justify-between p-4"
          >
            <span className="flex items-center gap-2 font-medium text-[14px]">
              <ShieldCheck className="size-4 text-primary" />
              Validation
            </span>
            {validationOpen ? (
              <ChevronDown className="size-4 text-text-secondary" />
            ) : (
              <ChevronRight className="size-4 text-text-secondary" />
            )}
          </button>
          {validationOpen && (
            <div className="px-4 pb-4 space-y-2 text-[13px]">
              {warnings.map((w, i) => (
                <div key={i} className="flex items-center gap-2 text-accent">
                  <AlertTriangle className="size-4" />
                  {w}
                </div>
              ))}
              {warnings.length === 0 && (
                <div className="flex items-center gap-2 text-success">
                  <CheckCircle2 className="size-4" />
                  No issues found
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {upload.isError && (
        <div className="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-[13px] text-red-700">
          {(upload.error as Error).message}
        </div>
      )}

      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={handleUpload}
          disabled={!pendingFile || upload.isPending}
          className="bg-primary text-primary-foreground hover:bg-primary-hover h-10 px-5 rounded-md text-[14px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {upload.isPending ? "Uploading…" : "Upload Codebook"}
        </button>
        {upload.isSuccess && (
          <span className="inline-flex items-center gap-1 text-[12px] font-medium text-success bg-success-light px-3 py-1 rounded-full">
            ✓ Codebook ready · {response!.row_count} variables
          </span>
        )}
      </div>
    </div>
  );
}
