import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { CheckCircle2, Pencil, AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { isEvalBuild } from "@/lib/evalBuild";
import { useEvalStore } from "@/stores/evalStore";
import { SUS_STATEMENTS, OPEN_ENDED, BACKGROUND } from "@/components/eval/questionnaireContent";
import { SubmitReportButton } from "@/components/eval/SubmitReportButton";
import { ScaleRow } from "@/components/eval/ScaleRow";

export const Route = createFileRoute("/eval-questionnaire")({
  component: EvalQuestionnairePage,
});

function ChoiceRow({
  options,
  value,
  onChange,
}: {
  options: string[];
  value?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`h-10 px-4 rounded-md border text-base font-medium transition-colors ${
            value === opt
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-surface hover:bg-accent-light"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

/** Parses the flat stored record (keys like sus_0, open_3, background_role
 * — see reportBuilder.ts) back into the three local maps the form edits, so
 * "Edit answers" reopens the form pre-filled instead of blank. */
function hydrateFromStored(stored: Record<string, string | number> | null) {
  const sus: Record<number, number> = {};
  const open: Record<number, string> = {};
  const background: Record<string, string> = {};
  if (stored) {
    for (const [key, value] of Object.entries(stored)) {
      if (key.startsWith("sus_") && typeof value === "number") {
        sus[Number(key.slice(4))] = value;
      } else if (key.startsWith("open_")) {
        open[Number(key.slice(5))] = String(value);
      } else if (key.startsWith("background_")) {
        background[key.slice("background_".length)] = String(value);
      }
    }
  }
  return { sus, open, background };
}

function EvalQuestionnairePage() {
  const setQuestionnaire = useEvalStore((s) => s.setQuestionnaire);
  const storedAnswers = useEvalStore((s) => s.questionnaireAnswers);
  const questionnaireSkipped = useEvalStore((s) => s.questionnaireSkipped);
  const alreadySubmitted = storedAnswers !== null || questionnaireSkipped;

  const [viewingForm, setViewingForm] = useState(false);
  const [susAnswers, setSusAnswers] = useState<Record<number, number>>(() => hydrateFromStored(storedAnswers).sus);
  const [openAnswers, setOpenAnswers] = useState<Record<number, string>>(() => hydrateFromStored(storedAnswers).open);
  const [backgroundAnswers, setBackgroundAnswers] = useState<Record<string, string>>(() => hydrateFromStored(storedAnswers).background);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isEvalBuild()) {
    return <div className="max-w-[800px] text-text-secondary">This page isn't available.</div>;
  }

  const startEditing = () => {
    const hydrated = hydrateFromStored(storedAnswers);
    setSusAnswers(hydrated.sus);
    setOpenAnswers(hydrated.open);
    setBackgroundAnswers(hydrated.background);
    setViewingForm(true);
  };

  if (alreadySubmitted && !viewingForm) {
    return (
      <div className="max-w-[800px]">
        <PageHeader title="Evaluation Report" />
        <div className="bg-success-light border border-l-4 border-l-success rounded-md p-4 flex items-start gap-3 mt-4">
          <CheckCircle2 className="size-5 text-success mt-0.5" />
          <div className="text-base">
            {questionnaireSkipped
              ? "You skipped the questionnaire for this session."
              : "Thanks — your questionnaire response has been recorded for this session."}
          </div>
        </div>
        <button
          onClick={startEditing}
          className="mt-3 inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
        >
          <Pencil className="size-3.5" />
          {questionnaireSkipped ? "Fill it in instead" : "Made a mistake? Edit your answers"}
        </button>
        <div className="mt-6">
          <SubmitReportButton />
        </div>
      </div>
    );
  }

  const submit = (skipped: boolean) => {
    if (!skipped) {
      const missing = SUS_STATEMENTS.length - Object.keys(susAnswers).length;
      if (missing > 0) {
        setValidationError(
          `Please answer all of Part A before submitting — ${missing} statement${missing === 1 ? "" : "s"} still unanswered. (You can always use "Skip for now" instead if you'd rather not fill this in at all.)`,
        );
        return;
      }
    }
    setValidationError(null);
    const answers: Record<string, string | number> = {};
    Object.entries(susAnswers).forEach(([i, v]) => (answers[`sus_${i}`] = v));
    Object.entries(openAnswers).forEach(([i, v]) => (answers[`open_${i}`] = v));
    Object.entries(backgroundAnswers).forEach(([k, v]) => (answers[`background_${k}`] = v));
    setQuestionnaire(answers, skipped);
    setViewingForm(false);
  };

  return (
    <div className="max-w-[800px]">
      <PageHeader
        title="Evaluation Report"
        subtitle="This is the important part for our research — it takes about 5 minutes."
      />

      <section className="mt-6">
        <div className="flex items-baseline justify-between">
          <h2 className="section-heading mb-3">Part A — Quick reactions</h2>
          <span className="text-sm text-text-secondary">Required</span>
        </div>
        <p className="text-base text-text-secondary mb-4">
          For each statement, pick a number from 1 (Strongly Disagree) to 5 (Strongly Agree).
          Don't overthink it — first reaction is best.
        </p>
        <div className="space-y-4">
          {SUS_STATEMENTS.map((statement, i) => (
            <div key={i} className="bg-surface border rounded-md p-4">
              <p className="text-base mb-3">{statement}</p>
              <ScaleRow
                value={susAnswers[i]}
                onChange={(n) => setSusAnswers((a) => ({ ...a, [i]: n }))}
                lowLabel="Strongly Disagree"
                highLabel="Strongly Agree"
              />
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-baseline justify-between">
          <h2 className="section-heading mb-3">Part B — In your own words</h2>
          <span className="text-sm text-text-secondary">Optional, but appreciated</span>
        </div>
        <div className="space-y-4">
          {OPEN_ENDED.map((q, i) => (
            <div key={i}>
              <label className="text-base font-medium">{q}</label>
              <textarea
                rows={2}
                value={openAnswers[i] ?? ""}
                onChange={(e) => setOpenAnswers((a) => ({ ...a, [i]: e.target.value }))}
                className="mt-1.5 w-full text-base p-2.5 rounded-md border bg-surface"
              />
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-baseline justify-between">
          <h2 className="section-heading mb-3">Part C — A bit about you</h2>
          <span className="text-sm text-text-secondary">Optional</span>
        </div>
        <div className="space-y-4">
          {BACKGROUND.map((q) => (
            <div key={q.id}>
              <label className="text-base font-medium">{q.label}</label>
              {q.options ? (
                <div className="mt-1.5">
                  <ChoiceRow
                    options={q.options}
                    value={backgroundAnswers[q.id]}
                    onChange={(v) => setBackgroundAnswers((a) => ({ ...a, [q.id]: v }))}
                  />
                </div>
              ) : (
                <input
                  type="text"
                  value={backgroundAnswers[q.id] ?? ""}
                  onChange={(e) =>
                    setBackgroundAnswers((a) => ({ ...a, [q.id]: e.target.value }))
                  }
                  className="mt-1.5 w-full text-base p-2.5 rounded-md border bg-surface"
                />
              )}
            </div>
          ))}
        </div>
      </section>

      {validationError && (
        <div className="mt-6 bg-danger-light border border-l-4 border-l-danger rounded-md p-4 flex items-start gap-3">
          <AlertTriangle className="size-5 text-danger mt-0.5 shrink-0" />
          <div className="text-base">{validationError}</div>
        </div>
      )}

      <div className="mt-8 flex items-center justify-end gap-3 border-t pt-4">
        {alreadySubmitted && (
          <button
            onClick={() => setViewingForm(false)}
            className="h-10 px-4 rounded-md text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          onClick={() => submit(true)}
          className="h-10 px-4 rounded-md text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
        >
          Skip for now
        </button>
        <button
          onClick={() => submit(false)}
          className="h-10 px-6 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-base font-medium transition-colors"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
