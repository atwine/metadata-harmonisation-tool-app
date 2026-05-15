import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ChevronDown, ChevronRight, Clock } from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useWizardStore } from "@/stores/wizardStore";

export const Route = createFileRoute("/map-studies")({
  component: MapStudiesPage,
});

function MapStudiesPage() {
  const {
    currentStudy,
    setCurrentStudy,
    relationalModeEnabled,
    toggleRelationalMode,
    operatorName,
    setOperatorName,
  } = useWizardStore();
  const [statusFilter, setStatusFilter] = useState("To do");
  const [sort, setSort] = useState<"difficulty" | "original">("difficulty");
  const [marking, setMarking] = useState("Successfully mapped");
  const [transformOpen, setTransformOpen] = useState(true);
  const [auditOpen, setAuditOpen] = useState(false);

  return (
    <div className="max-w-[1200px]">
      <PageHeader title="Map Studies" />

      {/* toolbar */}
      <div className="flex items-center gap-3 border-b pb-3 mb-4">
        <label className="text-[13px] text-text-secondary">Study:</label>
        <select
          value={currentStudy ?? ""}
          onChange={(e) => setCurrentStudy(e.target.value)}
          className="h-9 w-[220px] px-3 rounded-md border bg-surface text-[13px]"
        >
          <option value="cohort_2019">cohort_2019</option>
          <option value="cohort_2021">cohort_2021</option>
        </select>
        <input
          value={operatorName}
          onChange={(e) => setOperatorName(e.target.value)}
          placeholder="Operator name (audit)"
          className="h-9 w-[200px] px-3 rounded-md border bg-surface text-[13px]"
        />
        <div className="flex-1" />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-9 px-3 rounded-md border bg-surface text-[13px]"
        >
          <option>To do</option>
          <option>Successfully mapped</option>
          <option>Marked to reconsider</option>
          <option>Marked unmappable</option>
        </select>
        <div className="inline-flex rounded-md border overflow-hidden">
          {(["difficulty", "original"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSort(s)}
              className={`h-9 px-3 text-[12px] font-medium transition-colors ${
                sort === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-surface text-text-primary hover:bg-[#F5F0EE]"
              }`}
            >
              {s === "difficulty" ? "By difficulty" : "Original order"}
            </button>
          ))}
        </div>
      </div>

      {/* progress */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-[13px] text-text-secondary">
          12 / 47 variables mapped
        </span>
        <div className="w-[240px] h-1.5 rounded-full bg-border overflow-hidden">
          <div
            className="h-full bg-primary"
            style={{ width: `${(12 / 47) * 100}%` }}
          />
        </div>
      </div>

      {/* variable selector */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-[13px] font-medium">Select variable:</label>
        <select
          defaultValue="age_months"
          className="h-9 flex-1 max-w-md px-3 rounded-md border bg-surface text-[13px] font-mono"
        >
          <option>age_months</option>
          <option>weight_kg</option>
          <option>sex_01</option>
        </select>
      </div>

      {/* variable detail */}
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div className="bg-surface border rounded-lg p-4 shadow-sm">
          <div className="text-[12px] uppercase tracking-wide text-text-secondary font-medium mb-2">
            Variable
          </div>
          <table className="w-full text-[13px]">
            <tbody>
              <tr style={{ background: "#FAFAF8" }}>
                <td className="px-2 h-8 text-text-secondary w-32">
                  variable_name
                </td>
                <td className="px-2 h-8 font-mono">age_months</td>
              </tr>
              <tr>
                <td className="px-2 h-8 text-text-secondary">description</td>
                <td className="px-2 h-8">Age of participant in months</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="bg-surface border rounded-lg p-4 shadow-sm">
          <div className="text-[12px] uppercase tracking-wide text-text-secondary font-medium mb-2">
            Example Data
          </div>
          <pre
            className="font-mono text-[12px] p-2.5 rounded text-text-primary"
            style={{ background: "#F4F0ED" }}
          >
            {`24 ; 36 ; 48 ; 60 ; 36
72 ; 24 ; 48 ; 12 ; 36`}
          </pre>
        </div>
      </div>

      {/* mapping form */}
      <div className="mt-4 bg-surface border rounded-lg p-5 shadow-sm space-y-5">
        {/* row 1 */}
        <div>
          <label className="text-[13px] font-medium block mb-1.5">
            Codebook match
          </label>
          <select className="h-9 w-full px-3 rounded-md border bg-surface text-[13px]">
            <option>Age (years) - 87%</option>
            <option>Age at diagnosis - 71%</option>
            <option>Age at baseline - 64%</option>
            <option className="text-text-secondary">
              Weight (kg) - 41% (used)
            </option>
          </select>
        </div>

        {/* row 2 confidence */}
        <div className="flex items-center gap-3">
          <span className="text-[18px] font-semibold bg-primary-light text-primary px-2.5 py-1 rounded-md">
            87%
          </span>
          <div className="w-[200px] h-2 rounded-full bg-border overflow-hidden">
            <div className="h-full bg-primary" style={{ width: "87%" }} />
          </div>
          <span className="inline-flex items-center gap-1.5 text-[12px] font-medium">
            <span className="size-2 rounded-full bg-success" /> Strong
          </span>
        </div>

        {/* row 3 relational */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={toggleRelationalMode}
              className={`relative w-9 h-5 rounded-full transition-colors ${
                relationalModeEnabled ? "bg-primary" : "bg-border"
              }`}
              aria-label="toggle relational mode"
            >
              <span
                className={`absolute top-0.5 size-4 rounded-full bg-white transition-all ${
                  relationalModeEnabled ? "left-4" : "left-0.5"
                }`}
              />
            </button>
            <span className="text-[13px] font-medium">Relational Mode</span>
          </div>
          <div
            className={`grid grid-cols-2 gap-3 transition-opacity ${
              relationalModeEnabled
                ? "opacity-100"
                : "opacity-40 pointer-events-none"
            }`}
          >
            <div>
              <label className="text-[12px] text-text-secondary">
                Patient ID:
              </label>
              <select className="mt-1 h-9 w-full px-3 rounded-md border bg-surface text-[13px]">
                <option>participant_id - 94%</option>
                <option>study_id - 78%</option>
              </select>
            </div>
            <div>
              <label className="text-[12px] text-text-secondary">Date:</label>
              <select className="mt-1 h-9 w-full px-3 rounded-md border bg-surface text-[13px]">
                <option>visit_date - 89%</option>
                <option>collection_date - 72%</option>
              </select>
            </div>
            <div className="col-span-2 bg-accent-light rounded p-2.5 text-[12px] text-text-primary">
              Map each variable to the patient identifier and date columns in
              this study for relational export.
            </div>
          </div>
        </div>

        {/* row 4 mapping */}
        <div>
          <label className="text-[14px] font-medium block mb-2">
            Can this variable be mapped?
          </label>
          <div className="flex items-center gap-4 flex-wrap">
            {[
              { label: "To do", color: "#9C9590" },
              { label: "Successfully mapped", color: "var(--success)" },
              { label: "Marked to reconsider", color: "var(--accent)" },
              { label: "Marked unmappable", color: "var(--primary)" },
            ].map((opt) => (
              <label
                key={opt.label}
                className="inline-flex items-center gap-2 text-[13px] cursor-pointer"
              >
                <input
                  type="radio"
                  name="marking"
                  checked={marking === opt.label}
                  onChange={() => setMarking(opt.label)}
                  className="accent-primary"
                />
                <span
                  className="size-2 rounded-full"
                  style={{ background: opt.color }}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>

        {/* row 5 notes */}
        <div>
          <label className="text-[13px] font-medium block mb-1.5">Notes</label>
          <input
            placeholder="Optional notes about this mapping..."
            className="h-9 w-full px-3 rounded-md border bg-surface text-[13px]"
          />
        </div>

        {/* row 6 transformation */}
        <div className="border rounded-md">
          <button
            onClick={() => setTransformOpen((o) => !o)}
            className="w-full flex items-center justify-between p-3"
          >
            <span className="text-[13px] font-medium">Transformation</span>
            {transformOpen ? (
              <ChevronDown className="size-4 text-text-secondary" />
            ) : (
              <ChevronRight className="size-4 text-text-secondary" />
            )}
          </button>
          {transformOpen && (
            <div className="grid grid-cols-2 gap-5 p-4 border-t">
              <div className="space-y-3">
                <Field label="Type:">
                  <select className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]">
                    <option>Direct</option>
                    <option>Categorical</option>
                  </select>
                </Field>
                <Field label="Source type:">
                  <select className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]">
                    <option>integer</option>
                    <option>float</option>
                    <option>string</option>
                    <option>boolean</option>
                  </select>
                </Field>
                <Field label="Target type:">
                  <select className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]">
                    <option>float</option>
                    <option>integer</option>
                    <option>string</option>
                    <option>boolean</option>
                  </select>
                </Field>
                <Field label="Expression:">
                  <input
                    defaultValue="x/12"
                    className="h-8 w-full px-2 rounded-md border bg-surface text-[12px] font-mono"
                  />
                </Field>
                <Field label="Examples:">
                  <div className="flex gap-2">
                    <select className="h-8 flex-1 px-2 rounded-md border bg-surface text-[12px]">
                      <option>Months → Years (x/12)</option>
                      <option>Keep as is (x)</option>
                      <option>Scale up (x*100)</option>
                    </select>
                    <button className="h-8 px-3 text-[12px] rounded-md border border-primary text-primary hover:bg-primary-light font-medium">
                      Apply
                    </button>
                  </div>
                </Field>
                <span className="inline-flex items-center gap-1 text-[12px] font-medium text-success bg-success-light px-2.5 py-0.5 rounded-full">
                  ✓ Valid expression
                </span>
              </div>
              <div>
                <div className="text-[13px] font-medium mb-2">Preview</div>
                <table className="w-full text-[12px] border rounded overflow-hidden">
                  <thead>
                    <tr className="bg-primary text-primary-foreground">
                      <th className="text-left px-2 h-8 font-medium">
                        Original
                      </th>
                      <th className="text-left px-2 h-8 font-medium">
                        Transformed
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      [24, 2.0],
                      [36, 3.0],
                      [48, 4.0],
                      [60, 5.0],
                    ].map(([a, b], i) => (
                      <tr
                        key={i}
                        style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
                      >
                        <td className="px-2 h-7 font-mono">{a}</td>
                        <td className="px-2 h-7 font-mono">{b}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="text-[12px] text-text-secondary mt-2">
                  Transformed 10/10 · 0 blanks
                </div>
              </div>
            </div>
          )}
        </div>

        {/* submit */}
        <button
          className="w-full h-10 rounded-md text-[14px] font-medium text-white transition-colors hover:opacity-90"
          style={{ background: "var(--success)" }}
        >
          Submit
        </button>
      </div>

      {/* audit trail */}
      <div className="mt-4 bg-surface border rounded-lg shadow-sm">
        <button
          onClick={() => setAuditOpen((o) => !o)}
          className="w-full flex items-center justify-between p-3"
        >
          <span className="flex items-center gap-2 text-[13px] font-medium">
            <Clock className="size-4 text-text-secondary" />
            Audit trail (last 5 writes)
          </span>
          {auditOpen ? (
            <ChevronDown className="size-4 text-text-secondary" />
          ) : (
            <ChevronRight className="size-4 text-text-secondary" />
          )}
        </button>
        {auditOpen && (
          <div className="px-3 pb-3 space-y-2">
            {[1, 2].map((i) => (
              <pre
                key={i}
                className="font-mono text-[11px] text-white p-2 rounded overflow-hidden"
                style={{
                  background: "#1A1A1A",
                  maxHeight: 80,
                }}
              >
{`{
  "timestamp": "2025-05-15T10:24:0${i}Z",
  "study": "cohort_2019",
  "study_var": "age_months",
  "codebook_var": "age_years",
  "marked": "Successfully mapped",
  "operator": "j.mokoena"
}`}
              </pre>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[110px_1fr] items-center gap-2">
      <label className="text-[12px] text-text-secondary">{label}</label>
      {children}
    </div>
  );
}
