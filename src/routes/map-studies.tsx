import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Clock, Lock, Globe } from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useWizardStore } from "@/stores/wizardStore";
import {
  useStudies,
  useMappings,
  useVariableDetail,
  useAudit,
  useSaveMapping,
  useReopenMapping,
  useAfpoLookup,
  useAfpoMarkGapSubmitted,
  api,
  type TransformationPreviewResponse,
  type ValidateExpressionResponse,
  type AfpoLookupResult,
  type GithubCheckResponse,
} from "@/api/client";

export const Route = createFileRoute("/map-studies")({
  component: MapStudiesPage,
});

const MARKINGS = [
  { label: "To do", color: "#9C9590" },
  { label: "Successfully mapped", color: "var(--success)" },
  { label: "Marked to reconsider", color: "var(--accent)" },
  { label: "Marked unmappable", color: "var(--primary)" },
] as const;

type Marking = (typeof MARKINGS)[number]["label"];

// AfPO population/ethnicity ontology mapping — triggered when the mapped
// codebook variable name suggests population/ethnicity data (matches the
// reference app's trigger exactly).
const ETHNICITY_KEYWORDS = ["ethnicity", "ethnic", "population", "tribe", "ancestry", "race"];

function MapStudiesPage() {
  const {
    currentStudy,
    setCurrentStudy,
    relationalModeEnabled,
    toggleRelationalMode,
    operatorName,
    setOperatorName,
  } = useWizardStore();

  const [statusFilter, setStatusFilter] = useState<string>("To do");
  const [sort, setSort] = useState<"difficulty" | "original">("difficulty");
  const [selectedVar, setSelectedVar] = useState<string>("");
  const [transformOpen, setTransformOpen] = useState(false);
  const [auditOpen, setAuditOpen] = useState(false);

  // Form state
  const [codebookMatch, setCodebookMatch] = useState<string>("");
  const [marking, setMarking] = useState<Marking>("To do");
  const [notes, setNotes] = useState("");
  const [pidVar, setPidVar] = useState("");
  const [dateVar, setDateVar] = useState("");
  const [transformType, setTransformType] = useState<"Direct" | "Categorical">("Direct");
  const [sourceDtype, setSourceDtype] = useState("float");
  const [targetDtype, setTargetDtype] = useState("float");
  const [expression, setExpression] = useState("");
  const [preview, setPreview] = useState<TransformationPreviewResponse | null>(null);
  const [exprValidation, setExprValidation] = useState<ValidateExpressionResponse | null>(null);
  const [previewing, setPreviewing] = useState(false);

  // AfPO population/ethnicity mapping sub-section state
  const [afpoInput, setAfpoInput] = useState("");
  const [afpoResults, setAfpoResults] = useState<AfpoLookupResult[] | null>(null);
  const [afpoGapEdits, setAfpoGapEdits] = useState<Record<string, string>>({});
  const [afpoSubmittedGaps, setAfpoSubmittedGaps] = useState<Set<string>>(new Set());
  const [afpoGithubCheck, setAfpoGithubCheck] = useState<Record<string, GithubCheckResponse | { status: "checking" }>>({});

  const study = currentStudy ?? "";

  const { data: studies = [] } = useStudies();
  const { data: mappingsData, refetch: refetchMappings } = useMappings(study, statusFilter === "All" ? undefined : statusFilter);
  const { data: detail, isLoading: detailLoading } = useVariableDetail(study, selectedVar);
  const { data: auditData } = useAudit(study, 5);
  const saveMapping = useSaveMapping();
  const reopenMapping = useReopenMapping();
  const afpoLookup = useAfpoLookup();
  const afpoMarkSubmitted = useAfpoMarkGapSubmitted();

  const records = mappingsData?.records ?? [];

  const sortedRecords = [...records].sort((a, b) => {
    if (sort === "difficulty") {
      return (b.best_confidence ?? 0) - (a.best_confidence ?? 0);
    }
    return 0;
  });

  // Auto-select first variable when list changes
  useEffect(() => {
    if (sortedRecords.length > 0 && !selectedVar) {
      setSelectedVar(sortedRecords[0].study_var);
    }
  }, [sortedRecords, selectedVar]);

  // Reset form when variable detail loads
  useEffect(() => {
    if (!detail) return;
    const m = detail.existing_mapping;

    // Mirror the reference app: the codebook-match dropdown has no "none"
    // placeholder and simply defaults to its first (best-confidence) option,
    // so a fresh "To do" variable arrives pre-matched to its top recommendation
    // instead of forcing the user to reopen the dropdown and pick it manually.
    // Skip recommendations already claimed by another variable, same as the
    // reference's duplicate filtering — unless it's this variable's own saved match.
    const topAvailable =
      detail.recommendations.find(
        (r) => !detail.already_used_codebook_vars.includes(r.codebook_var)
      )?.codebook_var ??
      detail.recommendations[0]?.codebook_var ??
      "";
    setCodebookMatch(m.codebook_var || topAvailable);

    setMarking((m.marked as Marking) ?? "To do");
    setNotes(m.notes ?? "");
    setPidVar(m.patient_id_var ?? "");
    setDateVar(m.date_var ?? "");
    setTransformType(m.transformation_type ?? "Direct");
    setSourceDtype(m.source_dtype ?? "float");
    setTargetDtype(m.target_dtype ?? "float");
    setExpression(m.transformation_instructions ?? "");
    setPreview(null);
    setExprValidation(null);

    // AfPO section: pre-populate from this variable's example data, and
    // reset lookup results — a new variable means a fresh lookup.
    const uniqueExampleValues = Array.from(
      new Set(detail.example_data.map((v) => v.trim()).filter(Boolean))
    );
    setAfpoInput(uniqueExampleValues.join("\n"));
    setAfpoResults(null);
    setAfpoGapEdits({});
    setAfpoSubmittedGaps(new Set());
    setAfpoGithubCheck({});
  }, [detail]);

  const handleValidateExpr = async () => {
    if (!expression) return;
    const res = await api.validateExpression(expression);
    setExprValidation(res);
  };

  const handlePreview = async () => {
    if (!detail || !expression) return;
    setPreviewing(true);
    try {
      const res = await api.previewTransformation({
        example_data: detail.example_data.slice(0, 10),
        transformation_type: transformType,
        transformation_instructions: expression,
        source_dtype: sourceDtype,
        target_dtype: targetDtype,
      });
      setPreview(res);
    } finally {
      setPreviewing(false);
    }
  };

  const isEthnicityVar =
    !!codebookMatch &&
    ETHNICITY_KEYWORDS.some((kw) => codebookMatch.toLowerCase().includes(kw));

  const handleAfpoLookup = () => {
    if (!study || !selectedVar) return;
    const values = Array.from(
      new Set(afpoInput.split("\n").map((v) => v.trim()).filter(Boolean))
    );
    if (values.length === 0) return;
    afpoLookup.mutate(
      { study, variable_name: selectedVar, values },
      {
        onSuccess: (data) => {
          setAfpoResults(data.results);
          setAfpoGapEdits(
            Object.fromEntries(
              data.results.filter((r) => !r.afpo_id).map((r) => [r.input_value, r.input_value])
            )
          );
          setAfpoSubmittedGaps(new Set());
        },
      }
    );
  };

  // The actual submission — opens the pre-filled GitHub issue tab and marks
  // the gap locally submitted. Only reached once nothing live on GitHub is
  // blocking it (see handleAfpoSubmitGap), or the human explicitly chose
  // "Submit anyway" past a closed prior request.
  const proceedWithAfpoSubmit = (originalValue: string) => {
    if (!study || !selectedVar) return;
    const submittedAs = (afpoGapEdits[originalValue] || originalValue).trim() || originalValue;

    // Open the tab synchronously (inside the click handler) so popup blockers
    // don't intervene, then navigate it once the backend-built URL resolves —
    // the issue template lives server-side (backend/core/afpo_gap_reporter.py)
    // so there's one source of truth for its wording instead of a duplicate here.
    const popup = window.open("", "_blank", "noopener,noreferrer");
    api.afpoIssueUrl(submittedAs, study, selectedVar)
      .then((data) => {
        if (popup) popup.location.href = data.url;
      })
      .catch(() => {
        popup?.close();
      });

    afpoMarkSubmitted.mutate({ study, variable_name: selectedVar, value: originalValue });
    setAfpoSubmittedGaps((prev) => new Set(prev).add(originalValue));
  };

  // The cross-installation dedup guard: before letting anyone file a new
  // request, ask GitHub itself whether one already exists — a local flag
  // only knows what *this* installation has done, but every installation
  // of this app points at the same shared h3abionet/afpo repo.
  const handleAfpoSubmitGap = async (originalValue: string) => {
    if (!study || !selectedVar) return;
    const submittedAs = (afpoGapEdits[originalValue] || originalValue).trim() || originalValue;

    setAfpoGithubCheck((prev) => ({ ...prev, [originalValue]: { status: "checking" } }));
    let result: GithubCheckResponse;
    try {
      result = await api.afpoCheckGithub(submittedAs);
    } catch {
      result = { status: "unavailable", issues: [], from_cache: false };
    }
    setAfpoGithubCheck((prev) => ({ ...prev, [originalValue]: result }));

    // open_exists: blocked, nothing more to do — the UI shows the existing
    // issue link instead of the Submit button.
    // closed_exists: also don't auto-submit — ambiguous (merged? declined?
    // duplicate?), so a human decides via the "Submit anyway" action.
    // none / unavailable: nothing found (or couldn't check) — proceed.
    if (result.status === "open_exists" || result.status === "closed_exists") return;
    proceedWithAfpoSubmit(originalValue);
  };

  const handleSubmit = () => {
    if (!study || !selectedVar) return;

    // Figure out which variable to move to next, based on the list as it
    // stands right now — waiting for the post-save refetch would leave the
    // user staring at the just-submitted variable in the meantime.
    const currentIndex = sortedRecords.findIndex((r) => r.study_var === selectedVar);
    const remaining = sortedRecords.filter((r) => r.study_var !== selectedVar);
    const nextVar = remaining[currentIndex]?.study_var ?? remaining[0]?.study_var ?? "";

    const afpoValuesMapped = afpoResults
      ? Object.fromEntries(
          afpoResults.filter((r) => r.afpo_id).map((r) => [r.input_value, r.afpo_id as string])
        )
      : undefined;
    const afpoValuesGaps = afpoResults
      ? afpoResults.filter((r) => !r.afpo_id).map((r) => r.input_value)
      : undefined;

    saveMapping.mutate(
      {
        study,
        variable: selectedVar,
        body: {
          codebook_var: codebookMatch || undefined,
          marked: marking,
          notes: notes || undefined,
          transformation_type: expression ? transformType : undefined,
          transformation_instructions: expression || undefined,
          source_dtype: sourceDtype,
          target_dtype: targetDtype,
          patient_id_var: pidVar || undefined,
          date_var: dateVar || undefined,
          operator_name: operatorName || undefined,
          afpo_values_mapped: afpoValuesMapped,
          afpo_values_gaps: afpoValuesGaps,
        },
      },
      {
        onSuccess: () => {
          void refetchMappings();
          setNotes("");
          setTransformOpen(false);
          setSelectedVar(nextVar);
        },
      }
    );
  };

  const handleReopen = () => {
    if (!study || !selectedVar) return;
    reopenMapping.mutate(
      { study, variable: selectedVar },
      {
        onSuccess: () => {
          // The variable moves back to "To do" server-side — switch the filter
          // to match so it's visible (and editable) right away, on the same variable.
          setStatusFilter("To do");
        },
      }
    );
  };

  // The confidence shown must track whichever codebook_var is actually
  // selected — not just always the top recommendation — since the user can
  // override the auto-picked match with a different one from the dropdown.
  const topConfidence =
    detail?.recommendations.find((r) => r.codebook_var === codebookMatch)?.confidence ??
    detail?.recommendations[0]?.confidence ??
    0;

  const confidenceLabel =
    topConfidence >= 80 ? "Strong" : topConfidence >= 50 ? "Moderate" : "Weak";

  const confidenceColor =
    topConfidence >= 80
      ? "var(--success)"
      : topConfidence >= 50
        ? "var(--accent)"
        : "#9C9590";

  return (
    <div className="max-w-[1200px]">
      <PageHeader title="Map Studies" />

      {/* toolbar */}
      <div className="flex items-center gap-3 border-b pb-3 mb-4 flex-wrap">
        <label className="text-[13px] text-text-secondary">Study:</label>
        <select
          value={study}
          onChange={(e) => {
            setCurrentStudy(e.target.value);
            setSelectedVar("");
          }}
          className="h-9 w-[220px] px-3 rounded-md border bg-surface text-[13px]"
        >
          <option value="">— select study —</option>
          {studies.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name}
            </option>
          ))}
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
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setSelectedVar("");
          }}
          className="h-9 px-3 rounded-md border bg-surface text-[13px]"
        >
          <option>To do</option>
          <option>Successfully mapped</option>
          <option>Marked to reconsider</option>
          <option>Marked unmappable</option>
        </select>
        <span className="text-[12px] font-medium text-text-secondary bg-[#F5F0EE] px-2 py-1 rounded-full">
          {sortedRecords.length} in this view
        </span>
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
      {mappingsData && (
        <div className="flex items-center gap-3 mb-4">
          <span className="text-[13px] text-text-secondary">
            {mappingsData.mapped} / {mappingsData.total} variables mapped overall
          </span>
          <div className="w-[240px] h-1.5 rounded-full bg-border overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${mappingsData.progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* variable selector */}
      <div className="mb-1">
        <p className="text-[12px] text-text-secondary">
          The status filter above changes which variables the dropdown below lists —
          open it to step through every variable marked{" "}
          <strong>"{statusFilter}"</strong>.
        </p>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <label className="text-[13px] font-medium">Select variable:</label>
        <select
          value={selectedVar}
          onChange={(e) => setSelectedVar(e.target.value)}
          className="h-9 flex-1 max-w-md px-3 rounded-md border bg-surface text-[13px] font-mono"
        >
          {sortedRecords.length === 0 && (
            <option value="">— no variables —</option>
          )}
          {sortedRecords.map((r) => (
            <option key={r.study_var} value={r.study_var}>
              {r.study_var}
              {r.best_confidence !== undefined
                ? ` (${r.best_confidence}%)`
                : ""}
            </option>
          ))}
        </select>
      </div>

      {!study && (
        <div className="text-[13px] text-text-secondary py-8 text-center">
          Select a study to begin mapping.
        </div>
      )}

      {study && !selectedVar && sortedRecords.length === 0 && !detailLoading && (
        <div className="text-[13px] text-success py-8 text-center font-medium">
          No variables left in "{statusFilter}" — nice work. Switch the status filter above
          to review other variables.
        </div>
      )}

      {study && detailLoading && (
        <div className="text-[13px] text-text-secondary py-8 text-center">
          Loading…
        </div>
      )}

      {study && detail && !detailLoading && (
        <>
          {/* variable detail */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="bg-surface border rounded-lg p-4 shadow-sm">
              <div className="text-[12px] uppercase tracking-wide text-text-secondary font-medium mb-2">
                Variable
              </div>
              <table className="w-full text-[13px]">
                <tbody>
                  <tr style={{ background: "#FAFAF8" }}>
                    <td className="px-2 h-8 text-text-secondary w-32">variable_name</td>
                    <td className="px-2 h-8 font-mono">{detail.variable.variable_name}</td>
                  </tr>
                  <tr>
                    <td className="px-2 h-8 text-text-secondary">description</td>
                    <td className="px-2 h-8">{detail.variable.description ?? "—"}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="bg-surface border rounded-lg p-4 shadow-sm">
              <div className="text-[12px] uppercase tracking-wide text-text-secondary font-medium mb-2">
                Example Data
              </div>
              {detail.example_data.length > 0 ? (
                <pre
                  className="font-mono text-[12px] p-2.5 rounded text-text-primary whitespace-pre-wrap break-words"
                  style={{ background: "#F4F0ED" }}
                >
                  {detail.example_data.join(" ; ")}
                </pre>
              ) : (
                <span className="text-[12px] text-text-secondary">No example data available</span>
              )}
            </div>
          </div>

          {/* mapping form — editable only while reviewing "To do"; everything
              else is read-only with a "Reopen for edit" gate, so browsing an
              already-decided category can't silently overwrite it via a
              Submit button that's just sitting there. */}
          {statusFilter !== "To do" ? (
            <div className="mt-4 bg-surface border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 text-[13px] font-medium text-text-secondary">
                <Lock className="size-4" />
                Marked "{detail.existing_mapping.marked}" — reviewing read-only.
              </div>
              <table className="w-full text-[13px] border rounded-md overflow-hidden">
                <tbody>
                  <tr style={{ background: "#FAFAF8" }}>
                    <td className="px-2 h-9 text-text-secondary w-44">Codebook match</td>
                    <td className="px-2 h-9 font-mono">
                      {detail.existing_mapping.codebook_var || "—"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2 h-9 text-text-secondary">Notes</td>
                    <td className="px-2 h-9">{detail.existing_mapping.notes || "—"}</td>
                  </tr>
                  <tr style={{ background: "#FAFAF8" }}>
                    <td className="px-2 h-9 text-text-secondary">Transformation</td>
                    <td className="px-2 h-9 font-mono">
                      {detail.existing_mapping.transformation_instructions
                        ? `${detail.existing_mapping.transformation_type}: ${detail.existing_mapping.transformation_instructions}`
                        : "—"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2 h-9 text-text-secondary">Patient ID / Date</td>
                    <td className="px-2 h-9 font-mono">
                      {detail.existing_mapping.patient_id_var || "—"} /{" "}
                      {detail.existing_mapping.date_var || "—"}
                    </td>
                  </tr>
                </tbody>
              </table>

              {reopenMapping.isError && (
                <div className="p-2 rounded-md bg-red-50 border border-red-200 text-[12px] text-red-700">
                  {(reopenMapping.error as Error).message}
                </div>
              )}

              <button
                onClick={handleReopen}
                disabled={reopenMapping.isPending}
                className="w-full h-10 rounded-md text-[14px] font-medium border border-primary text-primary hover:bg-primary-light transition-colors disabled:opacity-50"
              >
                {reopenMapping.isPending ? "Reopening…" : "Reopen for edit"}
              </button>
              <p className="text-[12px] text-text-secondary text-center">
                Moves this variable back to "To do" so you can safely change its mapping.
              </p>
            </div>
          ) : (
          <div className="mt-4 bg-surface border rounded-lg p-5 shadow-sm space-y-5">
            {/* codebook match */}
            <div>
              <label className="text-[13px] font-medium block mb-1.5">
                Codebook match
              </label>
              <select
                value={codebookMatch}
                onChange={(e) => {
                  setCodebookMatch(e.target.value);
                  setPreview(null);
                }}
                className="h-9 w-full px-3 rounded-md border bg-surface text-[13px]"
              >
                <option value="">— none —</option>
                {detail.recommendations.map((r) => {
                  const isUsed = detail.already_used_codebook_vars.includes(r.codebook_var);
                  return (
                    <option key={r.codebook_var} value={r.codebook_var}>
                      {r.description} — {r.confidence}%{isUsed ? " (used)" : ""}
                    </option>
                  );
                })}
              </select>
            </div>

            {/* confidence */}
            {codebookMatch && (
              <div className="flex items-center gap-3">
                <span className="text-[18px] font-semibold bg-primary-light text-primary px-2.5 py-1 rounded-md">
                  {topConfidence}%
                </span>
                <div className="w-[200px] h-2 rounded-full bg-border overflow-hidden">
                  <div
                    className="h-full transition-all"
                    style={{ width: `${topConfidence}%`, background: confidenceColor }}
                  />
                </div>
                <span className="inline-flex items-center gap-1.5 text-[12px] font-medium">
                  <span className="size-2 rounded-full" style={{ background: confidenceColor }} />
                  {confidenceLabel}
                </span>
              </div>
            )}

            {/* relational mode */}
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
                  relationalModeEnabled ? "opacity-100" : "opacity-40 pointer-events-none"
                }`}
              >
                <div>
                  <label className="text-[12px] text-text-secondary">Patient ID:</label>
                  <select
                    value={pidVar}
                    onChange={(e) => setPidVar(e.target.value)}
                    className="mt-1 h-9 w-full px-3 rounded-md border bg-surface text-[13px]"
                  >
                    <option value="">— none —</option>
                    {detail.pid_recommendations.map((r) => (
                      <option key={r.variable_name} value={r.variable_name}>
                        {r.variable_name} — {r.confidence}%
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[12px] text-text-secondary">Date:</label>
                  <select
                    value={dateVar}
                    onChange={(e) => setDateVar(e.target.value)}
                    className="mt-1 h-9 w-full px-3 rounded-md border bg-surface text-[13px]"
                  >
                    <option value="">— none —</option>
                    {detail.date_recommendations.map((r) => (
                      <option key={r.variable_name} value={r.variable_name}>
                        {r.variable_name} — {r.confidence}%
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2 bg-accent-light rounded p-2.5 text-[12px] text-text-primary">
                  Map each variable to the patient identifier and date columns in this study for relational export.
                </div>
              </div>
            </div>

            {/* marking */}
            <div>
              <label className="text-[14px] font-medium block mb-2">
                Can this variable be mapped?
              </label>
              <div className="flex items-center gap-4 flex-wrap">
                {MARKINGS.map((opt) => (
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
                    <span className="size-2 rounded-full" style={{ background: opt.color }} />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            {/* notes */}
            <div>
              <label className="text-[13px] font-medium block mb-1.5">Notes</label>
              <input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes about this mapping..."
                className="h-9 w-full px-3 rounded-md border bg-surface text-[13px]"
              />
            </div>

            {/* AfPO population/ethnicity mapping — only when the matched codebook
                variable looks like it holds population/ethnicity data. Entirely
                optional: doesn't block Submit either way. */}
            {isEthnicityVar && (
              <div className="border-t pt-5">
                <div className="flex items-center gap-2 mb-1.5">
                  <Globe className="size-4 text-primary" />
                  <span className="text-[14px] font-medium">AfPO Population Mapping</span>
                </div>
                <p className="text-[12px] text-text-secondary mb-3">
                  This variable appears to contain population or ethnicity data. Enter the
                  values found in your dataset to map them to the African Population Ontology
                  (AfPO).
                </p>
                <label className="text-[12px] text-text-secondary block mb-1">
                  Ethnicity/population values found in this column (one per line):
                </label>
                <textarea
                  rows={5}
                  value={afpoInput}
                  onChange={(e) => setAfpoInput(e.target.value)}
                  className="w-full text-[13px] p-2.5 rounded-md border bg-surface font-mono"
                />
                <button
                  onClick={handleAfpoLookup}
                  disabled={afpoLookup.isPending || !afpoInput.trim()}
                  className="mt-2 h-9 px-3 text-[13px] rounded-md border border-primary text-primary hover:bg-primary-light font-medium disabled:opacity-50"
                >
                  {afpoLookup.isPending ? "Looking up…" : "Look up in AfPO"}
                </button>

                {afpoResults && (
                  <div className="mt-4 space-y-4">
                    {afpoResults.some((r) => r.afpo_id) && (
                      <div>
                        <div className="text-[13px] font-medium text-success mb-1.5">Matched</div>
                        <table className="w-full text-[12px] border rounded overflow-hidden">
                          <thead>
                            <tr className="bg-primary text-primary-foreground">
                              <th className="text-left px-2 h-8 font-medium">Input Value</th>
                              <th className="text-left px-2 h-8 font-medium">AfPO ID</th>
                              <th className="text-left px-2 h-8 font-medium">Canonical Name</th>
                              <th className="text-left px-2 h-8 font-medium">Matched Via</th>
                              <th className="text-left px-2 h-8 font-medium">Confidence</th>
                            </tr>
                          </thead>
                          <tbody>
                            {afpoResults.filter((r) => r.afpo_id).map((r, i) => (
                              <tr key={r.input_value} style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}>
                                <td className="px-2 h-8 font-mono">{r.input_value}</td>
                                <td className="px-2 h-8 font-mono">{r.afpo_id}</td>
                                <td className="px-2 h-8">{r.canonical_name}</td>
                                <td className="px-2 h-8">{r.matched_via}</td>
                                <td className="px-2 h-8">{r.confidence}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {afpoResults.some((r) => !r.afpo_id) && (
                      <div>
                        <div className="text-[13px] font-medium text-accent mb-1">
                          Not found in AfPO — these are gaps
                        </div>
                        <p className="text-[12px] text-text-secondary mb-2">
                          You can edit the term below before submitting. Each gap is
                          independent — submit in any order.
                        </p>
                        <div className="space-y-2">
                          {afpoResults.filter((r) => !r.afpo_id).map((r) => {
                            const alreadySubmitted = r.already_submitted || afpoSubmittedGaps.has(r.input_value);
                            const check = afpoGithubCheck[r.input_value];
                            const checking = check?.status === "checking";
                            const openBlock = check?.status === "open_exists" ? check : undefined;
                            const closedBlock = check?.status === "closed_exists" ? check : undefined;
                            const unavailable = check?.status === "unavailable" ? check : undefined;
                            const buttonDisabled = alreadySubmitted || checking || !!openBlock || !!closedBlock;
                            const buttonLabel = alreadySubmitted
                              ? "Already submitted ✓"
                              : checking
                              ? "Checking GitHub…"
                              : "Submit to AfPO";
                            return (
                              <div key={r.input_value} className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-[12px] px-2 py-1.5 rounded bg-accent-light text-text-primary font-mono shrink-0">
                                    {r.input_value}
                                  </span>
                                  <input
                                    value={afpoGapEdits[r.input_value] ?? r.input_value}
                                    onChange={(e) =>
                                      setAfpoGapEdits((prev) => ({ ...prev, [r.input_value]: e.target.value }))
                                    }
                                    disabled={alreadySubmitted}
                                    className="h-9 flex-1 px-2 rounded-md border bg-surface text-[12px] font-mono disabled:opacity-60"
                                  />
                                  {r.search_issues_url && (
                                    <a
                                      href={r.search_issues_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="h-9 px-3 flex items-center text-[12px] rounded-md border text-text-secondary hover:bg-[#F5F0EE] font-medium shrink-0 whitespace-nowrap"
                                    >
                                      Search existing
                                    </a>
                                  )}
                                  <button
                                    onClick={() => handleAfpoSubmitGap(r.input_value)}
                                    disabled={buttonDisabled}
                                    className="h-9 px-3 text-[12px] rounded-md border border-primary text-primary hover:bg-primary-light font-medium disabled:opacity-50 disabled:cursor-not-allowed shrink-0 whitespace-nowrap"
                                  >
                                    {buttonLabel}
                                  </button>
                                </div>

                                {openBlock && openBlock.issues[0] && (
                                  <p className="text-[11px] text-accent pl-1">
                                    Already requested on GitHub — see{" "}
                                    <a
                                      href={openBlock.issues[0].url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-primary hover:underline"
                                    >
                                      issue #{openBlock.issues[0].number}
                                    </a>
                                    .
                                  </p>
                                )}

                                {closedBlock && closedBlock.issues[0] && (
                                  <p className="text-[11px] text-text-secondary pl-1">
                                    A request for this term was already filed and closed — check{" "}
                                    <a
                                      href={closedBlock.issues[0].url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-primary hover:underline"
                                    >
                                      issue #{closedBlock.issues[0].number}
                                    </a>{" "}
                                    before resubmitting.{" "}
                                    <button
                                      onClick={() => proceedWithAfpoSubmit(r.input_value)}
                                      className="text-primary hover:underline font-medium"
                                    >
                                      Submit anyway
                                    </button>
                                  </p>
                                )}

                                {unavailable && (
                                  <p className="text-[11px] text-text-secondary pl-1">
                                    Could not verify against GitHub (rate-limited or offline) — submitted without a live duplicate check.
                                  </p>
                                )}

                                {r.already_submitted && r.previously_submitted_at && !afpoSubmittedGaps.has(r.input_value) && (
                                  <p className="text-[11px] text-text-secondary pl-1">
                                    Already submitted to AfPO on{" "}
                                    {new Date(r.previously_submitted_at).toLocaleDateString()} — check{" "}
                                    <a
                                      href={r.search_issues_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-primary hover:underline"
                                    >
                                      existing issues
                                    </a>{" "}
                                    before filing another.
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* transformation */}
            <div className="border rounded-md">
              <button
                onClick={() => setTransformOpen((o) => !o)}
                className="w-full flex items-center justify-between p-3"
              >
                <span className="flex items-center gap-2 text-[13px] font-medium">
                  Transformation
                  {!transformOpen && (
                    <span className="text-[12px] font-normal text-text-secondary">
                      {expression
                        ? `— ${transformType}: ${expression}`
                        : "— none configured"}
                    </span>
                  )}
                </span>
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
                      <select
                        value={transformType}
                        onChange={(e) => {
                          setTransformType(e.target.value as "Direct" | "Categorical");
                          setPreview(null);
                          setExprValidation(null);
                        }}
                        className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]"
                      >
                        <option value="Direct">Direct</option>
                        <option value="Categorical">Categorical</option>
                      </select>
                    </Field>
                    {transformType === "Direct" && (
                      <>
                        <Field label="Source type:">
                          <select
                            value={sourceDtype}
                            onChange={(e) => setSourceDtype(e.target.value)}
                            className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]"
                          >
                            <option value="integer">integer</option>
                            <option value="float">float</option>
                            <option value="string">string</option>
                            <option value="boolean">boolean</option>
                          </select>
                        </Field>
                        <Field label="Target type:">
                          <select
                            value={targetDtype}
                            onChange={(e) => setTargetDtype(e.target.value)}
                            className="h-8 w-full px-2 rounded-md border bg-surface text-[12px]"
                          >
                            <option value="float">float</option>
                            <option value="integer">integer</option>
                            <option value="string">string</option>
                            <option value="boolean">boolean</option>
                          </select>
                        </Field>
                      </>
                    )}
                    <Field label={transformType === "Direct" ? "Expression:" : "Mapping:"}>
                      <input
                        value={expression}
                        onChange={(e) => {
                          setExpression(e.target.value);
                          setPreview(null);
                          setExprValidation(null);
                        }}
                        onBlur={() => {
                          if (expression && transformType === "Direct") {
                            void handleValidateExpr();
                          }
                        }}
                        placeholder={
                          transformType === "Direct"
                            ? "e.g. x/12"
                            : '{"1": "Male", "2": "Female"}'
                        }
                        className="h-8 w-full px-2 rounded-md border bg-surface text-[12px] font-mono"
                      />
                    </Field>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => void handlePreview()}
                        disabled={!expression || previewing || detail.example_data.length === 0}
                        className="h-8 px-3 text-[12px] rounded-md border border-primary text-primary hover:bg-primary-light font-medium disabled:opacity-50"
                      >
                        {previewing ? "…" : "Preview"}
                      </button>
                      {exprValidation && (
                        <span
                          className={`text-[12px] font-medium ${
                            exprValidation.valid ? "text-success" : "text-danger"
                          }`}
                        >
                          {exprValidation.valid ? "✓ Valid" : `✗ ${exprValidation.message}`}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* preview table */}
                  <div>
                    <div className="text-[13px] font-medium mb-2">Preview</div>
                    {preview ? (
                      <>
                        <table className="w-full text-[12px] border rounded overflow-hidden">
                          <thead>
                            <tr className="bg-primary text-primary-foreground">
                              <th className="text-left px-2 h-8 font-medium">Original</th>
                              <th className="text-left px-2 h-8 font-medium">Transformed</th>
                            </tr>
                          </thead>
                          <tbody>
                            {preview.preview.map((row, i) => (
                              <tr key={i} style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}>
                                <td className="px-2 h-7 font-mono">{row.original}</td>
                                <td
                                  className={`px-2 h-7 font-mono ${!row.transformed ? "text-text-secondary" : ""}`}
                                >
                                  {row.transformed || "—"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="text-[12px] text-text-secondary mt-2">
                          Transformed {preview.transformed_count}/{preview.preview.length} ·{" "}
                          {preview.blank_count} blanks
                        </div>
                        {!preview.valid && preview.error && (
                          <div className="text-[12px] text-danger mt-1">{preview.error}</div>
                        )}
                      </>
                    ) : (
                      <div className="text-[12px] text-text-secondary italic">
                        Enter an expression and click Preview.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* submit */}
            {saveMapping.isError && (
              <div className="p-2 rounded-md bg-red-50 border border-red-200 text-[12px] text-red-700">
                {(saveMapping.error as Error).message}
              </div>
            )}
            {saveMapping.isSuccess && (
              <div className="text-[12px] text-success">Saved successfully.</div>
            )}
            <button
              onClick={handleSubmit}
              disabled={saveMapping.isPending}
              className="w-full h-10 rounded-md text-[14px] font-medium text-white transition-colors hover:opacity-90 disabled:opacity-50"
              style={{ background: "var(--success)" }}
            >
              {saveMapping.isPending ? "Saving…" : "Submit"}
            </button>
          </div>
          )}
        </>
      )}

      {/* audit trail */}
      {study && (
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
              {(auditData?.records ?? []).length === 0 ? (
                <div className="text-[12px] text-text-secondary py-2">No audit entries yet.</div>
              ) : (
                (auditData?.records ?? []).map((entry, i) => (
                  <pre
                    key={i}
                    className="font-mono text-[11px] text-white p-2 rounded overflow-auto"
                    style={{ background: "#1A1A1A", maxHeight: 80 }}
                  >
                    {JSON.stringify(entry, null, 2)}
                  </pre>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[110px_1fr] items-center gap-2">
      <label className="text-[12px] text-text-secondary">{label}</label>
      {children}
    </div>
  );
}
