import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  FileSpreadsheet,
  Archive,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/download-results")({
  component: DownloadResultsPage,
});

const STUDIES = [
  { name: "cohort_2019", variables: 47 },
  { name: "cohort_2021", variables: 52 },
];

function DownloadResultsPage() {
  const [checked, setChecked] = useState<Record<string, boolean>>({
    cohort_2019: true,
    cohort_2021: true,
  });
  const [reportOpen, setReportOpen] = useState(true);

  return (
    <div className="max-w-[720px]">
      <PageHeader
        title="Download Results"
        subtitle="Export mapping tables and transformed datasets."
      />

      <h2 className="section-heading mb-3">Select studies to export</h2>
      <div className="space-y-2 mb-6">
        {STUDIES.map((s) => (
          <label
            key={s.name}
            className="flex items-center gap-3 p-3 bg-surface border rounded-md cursor-pointer hover:bg-[#FAFAF8]"
          >
            <input
              type="checkbox"
              checked={!!checked[s.name]}
              onChange={(e) =>
                setChecked((c) => ({ ...c, [s.name]: e.target.checked }))
              }
              className="size-4 accent-primary"
            />
            <span className="font-semibold text-[14px] font-mono">{s.name}</span>
            <span className="text-[12px] text-text-secondary">
              ({s.variables} variables)
            </span>
            <span className="ml-auto text-[11px] font-medium px-2 py-0.5 rounded-full bg-success-light text-success">
              Complete
            </span>
          </label>
        ))}
      </div>

      <div className="space-y-4">
        {STUDIES.filter((s) => checked[s.name]).map((s) => (
          <div
            key={s.name}
            className="bg-surface border rounded-lg p-4 shadow-sm"
          >
            <h3 className="font-semibold text-[14px] font-mono mb-3">
              {s.name}
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[13px]">Mapping table</span>
                <button className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-[13px] font-medium transition-colors">
                  <FileSpreadsheet className="size-4" />
                  Download CSV
                </button>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[13px]">Transformed data</span>
                  <button className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-[13px] font-medium transition-colors">
                    <Archive className="size-4" />
                    Download ZIP
                  </button>
                </div>
                <div className="text-[12px] text-text-secondary mt-1">
                  Applies transformations defined in Map Studies
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-surface border rounded-lg shadow-sm">
        <button
          onClick={() => setReportOpen((o) => !o)}
          className="w-full flex items-center justify-between p-4"
        >
          <span className="font-medium text-[14px]">Validation Report</span>
          {reportOpen ? (
            <ChevronDown className="size-4 text-text-secondary" />
          ) : (
            <ChevronRight className="size-4 text-text-secondary" />
          )}
        </button>
        {reportOpen && (
          <div className="px-4 pb-4">
            <table className="w-full text-[13px] border rounded overflow-hidden">
              <thead>
                <tr className="bg-primary text-primary-foreground">
                  <th className="text-left px-3 h-9 font-medium">Variable</th>
                  <th className="text-left px-3 h-9 font-medium">Successes</th>
                  <th className="text-left px-3 h-9 font-medium">Errors</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["age_months", 47, 0],
                  ["sex_01", 45, 2],
                  ["bmi_value", 47, 0],
                ].map((r, i) => (
                  <tr
                    key={i}
                    style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
                  >
                    <td className="px-3 h-9 font-mono text-[12px]">{r[0]}</td>
                    <td className="px-3 h-9 text-success">{r[1]}</td>
                    <td className="px-3 h-9 text-danger">{r[2]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 text-[13px] text-text-secondary">
              Total: 139 successful · 2 errors
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
