import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  FileSpreadsheet,
  Archive,
  ChevronDown,
  ChevronRight,
  ClipboardList,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useStudies, api, triggerDownload } from "@/api/client";

export const Route = createFileRoute("/download-results")({
  component: DownloadResultsPage,
});

function DownloadResultsPage() {
  const { data: studies = [] } = useStudies();
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [reportOpen, setReportOpen] = useState(true);
  const [downloading, setDownloading] = useState<Record<string, boolean>>({});
  const [zipError, setZipError] = useState<Record<string, string>>({});
  const [auditLogAvailable, setAuditLogAvailable] = useState(false);

  useEffect(() => {
    api.checkAuditLogExists().then(setAuditLogAvailable);
  }, []);

  const toggle = (name: string, on: boolean) =>
    setChecked((c) => ({ ...c, [name]: on }));

  const handleCsv = (name: string) => {
    window.open(api.getMappingCsvUrl(name), "_blank");
  };

  const handleZip = async (name: string) => {
    setDownloading((d) => ({ ...d, [name]: true }));
    setZipError((e) => ({ ...e, [name]: "" }));
    try {
      const blob = await api.downloadTransformedData([name]);
      triggerDownload(blob, `${name}_transformed.zip`);
    } catch (err) {
      setZipError((e) => ({ ...e, [name]: String(err) }));
    } finally {
      setDownloading((d) => ({ ...d, [name]: false }));
    }
  };

  const selectedStudies = studies.filter((s) => checked[s.name]);

  return (
    <div className="max-w-[720px]">
      <PageHeader
        title="Download Results"
        subtitle="Export mapping tables and transformed datasets."
      />

      <h2 className="section-heading mb-3">Select studies to export</h2>
      <div className="space-y-2 mb-6">
        {studies.length === 0 && (
          <div className="text-[13px] text-text-secondary py-4 text-center">
            No studies uploaded yet.
          </div>
        )}
        {studies.map((s) => (
          <label
            key={s.name}
            className="flex items-center gap-3 p-3 bg-surface border rounded-md cursor-pointer hover:bg-[#FAFAF8]"
          >
            <input
              type="checkbox"
              checked={!!checked[s.name]}
              onChange={(e) => toggle(s.name, e.target.checked)}
              className="size-4 accent-primary"
            />
            <span className="font-semibold text-[14px] font-mono">{s.name}</span>
            <span className="text-[12px] text-text-secondary">
              ({s.variable_count} variables)
            </span>
            <span
              className={`ml-auto text-[11px] font-medium px-2 py-0.5 rounded-full ${
                s.status === "complete"
                  ? "bg-success-light text-success"
                  : s.status === "mapping"
                    ? "bg-primary-light text-primary"
                    : "bg-[#EDE8E4] text-text-secondary"
              }`}
            >
              {s.status.charAt(0).toUpperCase() + s.status.slice(1)}
            </span>
          </label>
        ))}
      </div>

      <div className="space-y-4">
        {selectedStudies.map((s) => {
          const csvDisabled = !s.has_results;
          const zipDisabled = !s.has_example_data || !s.has_results;
          return (
            <div key={s.name} className="bg-surface border rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-[14px] font-mono mb-3">{s.name}</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[13px]">Mapping table</span>
                  <button
                    onClick={() => handleCsv(s.name)}
                    disabled={csvDisabled}
                    title={csvDisabled ? "No results yet — map at least one variable in Map Studies first" : undefined}
                    className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-[13px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                  >
                    <FileSpreadsheet className="size-4" />
                    Download CSV
                  </button>
                </div>
                {csvDisabled && (
                  <div className="text-[12px] text-text-secondary -mt-2">
                    No results yet — map at least one variable in Map Studies first.
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[13px]">Transformed data</span>
                    <button
                      onClick={() => void handleZip(s.name)}
                      disabled={downloading[s.name] || zipDisabled}
                      title={zipDisabled ? "Requires example data — metadata-only studies can only export the mapping CSV" : undefined}
                      className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-[13px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                    >
                      <Archive className="size-4" />
                      {downloading[s.name] ? "Preparing…" : "Download ZIP"}
                    </button>
                  </div>
                  <div className="text-[12px] text-text-secondary mt-1">
                    {!s.has_example_data
                      ? "Metadata-only study (no example_data.csv) — use \"Download CSV\" instead."
                      : "Applies transformations defined in Map Studies"}
                  </div>
                  {zipError[s.name] && (
                    <div className="text-[12px] text-danger mt-1">{zipError[s.name]}</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {auditLogAvailable && (
        <div className="mt-4 bg-surface border rounded-lg p-4 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[14px] font-semibold">Audit trail</div>
            <div className="text-[12px] text-text-secondary mt-0.5">
              Every mapping write, across all studies — for compliance/traceability.
            </div>
          </div>
          <a
            href={api.getAuditLogUrl()}
            className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-[13px] font-medium transition-colors"
          >
            <ClipboardList className="size-4" />
            Download audit log
          </a>
        </div>
      )}

      <div className="mt-6 bg-surface border rounded-lg shadow-sm">
        <button
          onClick={() => setReportOpen((o) => !o)}
          className="w-full flex items-center justify-between p-4"
        >
          <span className="font-medium text-[14px]">About transformed exports</span>
          {reportOpen ? (
            <ChevronDown className="size-4 text-text-secondary" />
          ) : (
            <ChevronRight className="size-4 text-text-secondary" />
          )}
        </button>
        {reportOpen && (
          <div className="px-4 pb-4 text-[13px] text-text-secondary space-y-2">
            <p>
              The ZIP file contains one transformed CSV per study. Only
              variables marked <strong>Successfully mapped</strong> with
              transformation instructions have the expression applied
              row-by-row.
            </p>
            <p>
              Variables with no transformation, or marked{" "}
              <strong>Marked to reconsider</strong> or{" "}
              <strong>Marked unmappable</strong>, are excluded from the output.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
