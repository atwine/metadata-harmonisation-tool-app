import { useEffect, useState } from "react";
import { isEvalBuild } from "@/lib/evalBuild";
import { useEvalStore } from "@/stores/evalStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { ScaleRow } from "./ScaleRow";

type CheckInQuestionBase =
  | {
      id: string;
      type: "yes_no";
      label: string;
      followUpLabel?: string;
      /** Which answer reveals the follow-up text box — e.g. "No" for "Was
       * this clear?" (the problem answer), "Yes" for "Did you hit any
       * errors?" (the problem answer is the other way round). Defaults to
       * "No" since that's the more common case among these questions. */
      followUpOn?: "Yes" | "No";
    }
  | { id: string; type: "scale"; label: string; lowLabel: string; highLabel: string }
  | { id: string; type: "choice"; label: string; options: string[] }
  | {
      id: string;
      type: "multi";
      label: string;
      options: string[];
      /** Small helper line under the question. */
      hint?: string;
    }
  | { id: string; type: "text"; label: string };

/** A question that only appears once an earlier question has a given answer
 * (for example "where did the problem happen?" only after "yes, I hit errors"). */
export type CheckInQuestion = CheckInQuestionBase & {
  showIf?: { id: string; equals: string };
};

/** A short, dismissable check-in shown once a step completes. Two ways out:
 * answer it, or hit "Skip for now" — both are recorded (a skip is itself a
 * data point), and either way it never re-prompts for the same step. No
 * countdown timer — a rushed answer under time pressure is worse data than
 * an honest skip. */
export function StepCheckIn({
  step,
  title,
  questions,
  trigger,
}: {
  step: string;
  title: string;
  questions: CheckInQuestion[];
  /** Becomes true once the page considers this step "done". */
  trigger: boolean;
}) {
  const alreadyAnswered = useEvalStore((s) => !!s.stepAnswers[step]);
  const recordStepAnswer = useEvalStore((s) => s.recordStepAnswer);
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string | number>>({});

  useEffect(() => {
    if (trigger && !alreadyAnswered && isEvalBuild()) setOpen(true);
  }, [trigger, alreadyAnswered]);

  if (!isEvalBuild() || alreadyAnswered) return null;

  const skip = () => {
    recordStepAnswer(step, { skipped: true, answers: {}, answeredAt: new Date().toISOString() });
    setOpen(false);
  };

  const isVisible = (q: CheckInQuestion) => !q.showIf || values[q.showIf.id] === q.showIf.equals;
  const visibleQuestions = questions.filter(isVisible);

  const submit = () => {
    // Drop answers to questions that are hidden again (for example the
    // participant changed "Yes" to "No" after ticking boxes).
    const keep = new Set(visibleQuestions.flatMap((q) => [q.id, `${q.id}_note`]));
    const answers = Object.fromEntries(Object.entries(values).filter(([k]) => keep.has(k)));
    recordStepAnswer(step, {
      skipped: false,
      answers,
      answeredAt: new Date().toISOString(),
    });
    setOpen(false);
  };

  const toggleMulti = (id: string, option: string, options: string[]) => {
    // Built from the latest state, so two quick taps in a row both count.
    setValues((prev) => {
      const current = String(prev[id] ?? "")
        .split(", ")
        .filter(Boolean);
      const next = current.includes(option)
        ? current.filter((o) => o !== option)
        : [...current, option];
      return { ...prev, [id]: options.filter((o) => next.includes(o)).join(", ") };
    });
  };

  const setValue = (id: string, v: string | number) => setValues((prev) => ({ ...prev, [id]: v }));

  return (
    <Dialog open={open} onOpenChange={(o) => !o && skip()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          {visibleQuestions.map((q) => (
            <div key={q.id}>
              <label className="text-base font-medium text-text-primary">{q.label}</label>

              {q.type === "yes_no" && (
                <div className="mt-2 flex gap-2">
                  {["Yes", "No"].map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setValue(q.id, opt)}
                      className={`h-10 px-4 rounded-md border text-base font-medium transition-colors ${
                        values[q.id] === opt
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-surface hover:bg-accent-light"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}

              {q.type === "yes_no" &&
                values[q.id] === (q.followUpOn ?? "No") &&
                q.followUpLabel && (
                  <input
                    type="text"
                    placeholder={q.followUpLabel}
                    value={(values[`${q.id}_note`] as string) ?? ""}
                    onChange={(e) => setValue(`${q.id}_note`, e.target.value)}
                    className="mt-2 w-full text-base p-2.5 rounded-md border bg-surface"
                  />
                )}

              {q.type === "scale" && (
                <div className="mt-2">
                  <p className="text-sm text-text-secondary mb-2">
                    1 = {q.lowLabel} · 5 = {q.highLabel}
                  </p>
                  <ScaleRow
                    value={values[q.id] as number | undefined}
                    onChange={(n) => setValue(q.id, n)}
                    lowLabel={q.lowLabel}
                    highLabel={q.highLabel}
                  />
                </div>
              )}

              {q.type === "choice" && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {q.options.map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setValue(q.id, opt)}
                      className={`h-10 px-4 rounded-md border text-base font-medium transition-colors ${
                        values[q.id] === opt
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-surface hover:bg-accent-light"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}

              {q.type === "multi" && (
                <div className="mt-2">
                  {q.hint && <p className="text-sm text-text-secondary mb-2">{q.hint}</p>}
                  <div className="flex flex-wrap gap-2">
                    {q.options.map((opt) => {
                      const picked = String(values[q.id] ?? "")
                        .split(", ")
                        .includes(opt);
                      return (
                        <button
                          key={opt}
                          aria-pressed={picked}
                          onClick={() => toggleMulti(q.id, opt, q.options)}
                          className={`h-10 px-4 rounded-md border text-base font-medium transition-colors ${
                            picked
                              ? "bg-primary text-primary-foreground border-primary"
                              : "bg-surface hover:bg-accent-light"
                          }`}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {q.type === "text" && (
                <textarea
                  rows={2}
                  value={(values[q.id] as string) ?? ""}
                  onChange={(e) => setValue(q.id, e.target.value)}
                  className="mt-2 w-full text-base p-2.5 rounded-md border bg-surface"
                />
              )}
            </div>
          ))}
        </div>

        {visibleQuestions.some((q) => q.type === "text" || (q.type === "yes_no" && q.followUpLabel)) && (
          <p className="text-sm text-text-secondary">
            Anything you type is included in a public GitHub report — please leave out names and
            personal details.
          </p>
        )}

        <DialogFooter className="mt-2">
          <button
            onClick={skip}
            className="h-10 px-4 rounded-md text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            Skip for now
          </button>
          <button
            onClick={submit}
            className="h-10 px-4 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-base font-medium transition-colors"
          >
            Submit
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
