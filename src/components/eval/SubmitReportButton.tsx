import { useState } from "react";
import { Github, ExternalLink, AlertTriangle } from "lucide-react";
import { api } from "@/api/client";
import { useEvalStore } from "@/stores/evalStore";
import { buildReportSections } from "./reportBuilder";

/** Bundles every check-in answer + the questionnaire into a pre-filled
 * GitHub issue and opens it in a new tab — same no-credentials pattern as
 * the AfPO gap reporter. The participant reviews the pre-filled form and
 * clicks GitHub's own Submit button themselves, under their own account. */
export function SubmitReportButton() {
  const stepAnswers = useEvalStore((s) => s.stepAnswers);
  const questionnaireAnswers = useEvalStore((s) => s.questionnaireAnswers);
  const questionnaireSkipped = useEvalStore((s) => s.questionnaireSkipped);
  const reportSubmitted = useEvalStore((s) => s.reportSubmitted);
  const markReportSubmitted = useEvalStore((s) => s.markReportSubmitted);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = buildReportSections(stepAnswers, questionnaireAnswers, questionnaireSkipped);
      const { url } = await api.getEvalReportUrl(payload);
      window.open(url, "_blank", "noopener,noreferrer");
      markReportSubmitted();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={() => void handleClick()}
        disabled={loading}
        className="inline-flex items-center gap-2 h-11 px-6 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-base font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Github className="size-4" />
        {loading ? "Preparing…" : reportSubmitted ? "Open report again" : "Submit Report"}
      </button>
      <p className="text-sm text-text-secondary mt-2 max-w-md">
        Opens a pre-filled GitHub issue in a new tab. Nothing is sent until you review it and
        click GitHub's own Submit button, under your own GitHub account. If you'd like to
        include the full performance log, attach{" "}
        <code className="text-xs bg-surface border rounded px-1">logs/benchmark_log.jsonl</code>{" "}
        before submitting.
      </p>
      {reportSubmitted && (
        <p className="text-sm text-success mt-1.5 flex items-center gap-1.5">
          <ExternalLink className="size-3.5" />
          Report opened — remember to review and click Submit on GitHub's page.
        </p>
      )}
      {error && (
        <p className="text-sm text-danger mt-1.5 flex items-center gap-1.5">
          <AlertTriangle className="size-3.5" />
          Couldn't prepare the report: {error}
        </p>
      )}
    </div>
  );
}
