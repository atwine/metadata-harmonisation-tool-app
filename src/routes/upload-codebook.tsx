import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  UploadCloud,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/upload-codebook")({
  component: UploadCodebookPage,
});

function UploadCodebookPage() {
  const [validationOpen, setValidationOpen] = useState(false);
  const filename = "elwazi_codebook_v3.csv";
  const filesize = "84 KB";
  // TODO: wire up real upload + parsing
  const rows = [
    ["age_years", "Age of participant in years", "integer"],
    ["sex", "Biological sex", "string"],
    ["weight_kg", "Weight in kilograms", "float"],
    ["height_cm", "Height in centimeters", "float"],
    ["bmi", "Body mass index", "float"],
  ];

  return (
    <div className="max-w-[720px] mx-auto">
      <PageHeader
        title="Upload Target Codebook"
        subtitle="Upload the canonical variable list that all study datasets will be mapped to."
      />

      <div className="border-2 border-dashed border-border rounded-lg p-8 text-center bg-surface hover:border-primary transition-colors cursor-pointer">
        <UploadCloud className="size-8 text-text-secondary mx-auto" />
        <div className="mt-3 text-[14px] text-text-primary">
          Drop your codebook CSV here, or click to browse
        </div>
        <div className="text-[12px] text-text-secondary mt-1">
          CSV only · max 10 MB
        </div>
        <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-light text-primary text-[12px] font-medium">
          {filename} · {filesize}
        </div>
      </div>

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
            {rows.map((r, i) => (
              <tr
                key={i}
                style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
              >
                <td className="px-3 h-9 font-mono text-[12px]">{r[0]}</td>
                <td className="px-3 h-9">{r[1]}</td>
                <td className="px-3 h-9 text-text-secondary">{r[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
            <div className="flex items-center gap-2 text-accent">
              <AlertTriangle className="size-4" />
              Recommended column missing: Unit
            </div>
            <div className="flex items-center gap-2 text-success">
              <CheckCircle2 className="size-4" />
              No critical errors
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center gap-3">
        <button className="bg-primary text-primary-foreground hover:bg-primary-hover h-10 px-5 rounded-md text-[14px] font-medium transition-colors">
          Upload Codebook
        </button>
        <span className="inline-flex items-center gap-1 text-[12px] font-medium text-success bg-success-light px-3 py-1 rounded-full">
          ✓ Codebook ready · 142 variables
        </span>
      </div>
    </div>
  );
}
