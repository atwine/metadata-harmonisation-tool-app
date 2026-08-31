import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { FileSpreadsheet, Archive, ChevronDown, ChevronRight, ClipboardList } from "lucide-react";
import type { Step } from "react-joyride";
import { PageHeader } from "@/components/Sidebar";
import { ProductTour, TourReplayButton } from "@/components/ProductTour";
import { useProductTour } from "@/hooks/useProductTour";
import { useStudies, api, triggerDownload } from "@/api/client";

export const Route = createFileRoute("/download-results")({
  component: DownloadResultsPage,
});

// Only targets elements that always exist — the per-study export cards and
// the audit-trail card are both conditionally rendered (on selection, and on
// an async "does a log exist yet" check), so the deeper content is described
// in a closing centered step instead of pointed at directly.
const TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="study-checklist"]',
    title: "Pick studies to export",
    content: "Check off which studies you want to export.",
    placement: "right",
  },
  {
    target: '[data-tour="about-exports"]',
    title: "What's in the ZIP?",
    content:
      "Not sure what's included in the transformed-data ZIP? Expand this for the details on which variables get exported.",
    placement: "top",
  },
  {
    target: "body",
    placement: "center",
    title: "Downloading",
    content:
      "Once you check a study, you'll see Download CSV and Download ZIP buttons for it here, plus an audit-log download if any mappings have been made.",
  },
];

function DownloadResultsPage() {
  const tour = useProductTour("download-results");
  const { data: studies = [] } = useStudies();
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [reportOpen, setReportOpen] = useState(true);
  const [downloading, setDownloading] = useState<Record<string, boolean>>({});
  const [zipError, setZipError] = useState<Record<string, string>>({});
  const [auditLogAvailable, setAuditLogAvailable] = useState(false);

  useEffect(() => {
    api.checkAuditLogExists().then(setAuditLogAvailable);
  }, []);

  const toggle = (name: string, on: boolean) => setChecked((c) => ({ ...c, [name]: on }));

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
    <div className="max-w-[1200px]">
      <ProductTour steps={TOUR_STEPS} run={tour.run} onEvent={tour.handleEvent} />

      <div className="flex items-center justify-between gap-4">
        <PageHeader
          title="Download Results"
          subtitle="Export mapping tables and transformed datasets."
        />
        <TourReplayButton onClick={tour.start} />
      </div>

      <div className="max-w-2xl" data-tour="study-checklist">
        <h2 className="section-heading mb-3">Select studies to export</h2>
        <div className="space-y-2 mb-6">
          {studies.length === 0 && (
            <div className="text-base text-text-secondary py-4 text-center">
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
              <span className="font-semibold text-md font-mono">{s.name}</span>
              <span className="text-sm text-text-secondary">({s.variable_count} variables)</span>
              <span
                className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
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
      </div>

      {studies.length > 0 && selectedStudies.length === 0 && (
        <div className="border-2 border-dashed rounded-lg p-8 text-center text-base text-text-secondary mb-6">
          Select one or more studies above to see export options.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {selectedStudies.map((s) => {
          const csvDisabled = !s.has_results;
          const zipDisabled = !s.has_example_data || !s.has_mapped_variable;
          const zipDisabledReason = !s.has_example_data
            ? "Requires example data — metadata-only studies can only export the mapping CSV"
            : !s.has_mapped_variable
              ? 'No variables marked "Successfully mapped" yet — nothing to transform'
              : undefined;
          return (
            <div key={s.name} className="bg-surface border rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-md font-mono mb-3">{s.name}</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-base">Mapping table</span>
                  <button
                    onClick={() => handleCsv(s.name)}
                    disabled={csvDisabled}
                    title={
                      csvDisabled
                        ? "No results yet — map at least one variable in Map Studies first"
                        : undefined
                    }
                    className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-base font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                  >
                    <FileSpreadsheet className="size-4" />
                    Download CSV
                  </button>
                </div>
                {csvDisabled && (
                  <div className="text-sm text-text-secondary -mt-2">
                    No results yet — map at least one variable in Map Studies first.
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-base">Transformed data</span>
                    <button
                      onClick={() => void handleZip(s.name)}
                      disabled={downloading[s.name] || zipDisabled}
                      title={zipDisabledReason}
                      className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-base font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                    >
                      <Archive className="size-4" />
                      {downloading[s.name] ? "Preparing…" : "Download ZIP"}
                    </button>
                  </div>
                  <div className="text-sm text-text-secondary mt-1">
                    {!s.has_example_data
                      ? 'Metadata-only study (no example_data.csv) — use "Download CSV" instead.'
                      : !s.has_mapped_variable
                        ? 'No variables marked "Successfully mapped" yet — nothing to transform.'
                        : "Applies transformations defined in Map Studies"}
                  </div>
                  {zipError[s.name] && (
                    <div className="text-sm text-danger mt-1">{zipError[s.name]}</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-6 items-start">
        {auditLogAvailable && (
          <div className="bg-surface border rounded-lg p-4 shadow-sm flex items-center justify-between gap-4">
            <div>
              <div className="text-md font-semibold">Audit trail</div>
              <div className="text-sm text-text-secondary mt-0.5">
                Every mapping write, across all studies — for compliance/traceability.
              </div>
            </div>
            <a
              href={api.getAuditLogUrl()}
              className="inline-flex items-center gap-2 h-9 px-3 rounded-md border border-primary text-primary hover:bg-primary-light text-base font-medium transition-colors shrink-0 whitespace-nowrap"
            >
              <ClipboardList className="size-4" />
              Download audit log
            </a>
          </div>
        )}

        <div className="bg-surface border rounded-lg shadow-sm" data-tour="about-exports">
          <button
            onClick={() => setReportOpen((o) => !o)}
            className="w-full flex items-center justify-between p-4"
          >
            <span className="font-medium text-md">About transformed exports</span>
            {reportOpen ? (
              <ChevronDown className="size-4 text-text-secondary" />
            ) : (
              <ChevronRight className="size-4 text-text-secondary" />
            )}
          </button>
          {reportOpen && (
            <div className="px-4 pb-4 text-base text-text-secondary space-y-2">
              <p>
                The ZIP file contains one transformed CSV per study. Only variables marked{" "}
                <strong>Successfully mapped</strong> with transformation instructions have the
                expression applied row-by-row.
              </p>
              <p>
                Variables with no transformation, or marked <strong>Marked to reconsider</strong> or{" "}
                <strong>Marked unmappable</strong>, are excluded from the output.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
