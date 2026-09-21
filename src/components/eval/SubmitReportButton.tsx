import { useState } from "react";
import { Github, ExternalLink, AlertTriangle, ArrowRight } from "lucide-react";
import { api } from "@/api/client";
import { useEvalStore } from "@/stores/evalStore";
import { useWizardStore } from "@/stores/wizardStore";
import { buildReportSections } from "./reportBuilder";
import { REQUIRED_STEPS, STEP_ROUTES, STEP_TITLES } from "./checkInQuestions";

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
  const sessionId = useEvalStore((s) => s.sessionId);
  const afpoMappingEnabled = useWizardStore((s) => s.afpoMappingEnabled);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requiredSteps = afpoMappingEnabled
    ? [...REQUIRED_STEPS, "map_studies_afpo"]
    : REQUIRED_STEPS;
  const missingSteps = requiredSteps.filter((step) => !stepAnswers[step]);

  const handleClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...buildReportSections(stepAnswers, questionnaireAnswers, questionnaireSkipped),
        session_id: sessionId,
      };
      const { url } = await api.getEvalReportUrl(payload);
      window.open(url, "_blank", "noopener,noreferrer");
      markReportSubmitted();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  if (missingSteps.length > 0) {
    return (
      <div className="bg-accent-light border border-l-4 border-l-accent rounded-md p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="size-5 text-accent mt-0.5 shrink-0" />
          <div>
            <p className="text-base font-medium">
              A few steps still need your reaction before you can submit the report.
            </p>
            <p className="text-sm text-text-secondary mt-1">
              You can still answer these even if you didn't finish that step — "I got stuck here" is
              useful feedback too.
            </p>
            <div className="mt-3 space-y-2">
              {missingSteps.map((step) => (
                <a
                  key={step}
                  href={`${STEP_ROUTES[step]}?checkin=${step}`}
                  className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline mr-4"
                >
                  {STEP_TITLES[step] ?? step}
                  <ArrowRight className="size-3.5" />
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-text-secondary mb-2">
        Anonymous session ID: <code className="bg-surface border rounded px-1">{sessionId}</code> —
        random, not linked to your name, just lets separate submissions be told apart.
      </p>
      <button
        onClick={() => void handleClick()}
        disabled={loading}
        className="inline-flex items-center gap-2 h-11 px-6 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-base font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Github className="size-4" />
        {loading ? "Preparing…" : reportSubmitted ? "Open report again" : "Submit Report"}
      </button>
      <p className="text-sm text-text-secondary mt-2 max-w-md">
        Opens a pre-filled GitHub issue in a new tab. <strong>It will be public</strong> — anyone
        can read what you wrote, so check it for names and personal details. Nothing is sent until
        you review it and click GitHub's own Submit button, under your own GitHub account. If you'd
        like to include the full performance log, attach{" "}
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
