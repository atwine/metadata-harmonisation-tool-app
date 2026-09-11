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

export type CheckInQuestion =
  | { id: string; type: "yes_no"; label: string; followUpLabel?: string }
  | { id: string; type: "scale"; label: string; lowLabel: string; highLabel: string }
  | { id: string; type: "choice"; label: string; options: string[] }
  | { id: string; type: "text"; label: string };

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

  const submit = () => {
    recordStepAnswer(step, { skipped: false, answers: values, answeredAt: new Date().toISOString() });
    setOpen(false);
  };

  const setValue = (id: string, v: string | number) => setValues((prev) => ({ ...prev, [id]: v }));

  return (
    <Dialog open={open} onOpenChange={(o) => !o && skip()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          {questions.map((q) => (
            <div key={q.id}>
              <label className="text-sm font-medium text-text-primary">{q.label}</label>

              {q.type === "yes_no" && (
                <div className="mt-2 flex gap-2">
                  {["Yes", "No"].map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setValue(q.id, opt)}
                      className={`h-9 px-4 rounded-md border text-sm font-medium transition-colors ${
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

              {q.type === "yes_no" && values[q.id] === "No" && q.followUpLabel && (
                <input
                  type="text"
                  placeholder={q.followUpLabel}
                  value={(values[`${q.id}_note`] as string) ?? ""}
                  onChange={(e) => setValue(`${q.id}_note`, e.target.value)}
                  className="mt-2 w-full text-sm p-2 rounded-md border bg-surface"
                />
              )}

              {q.type === "scale" && (
                <div className="mt-2">
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => setValue(q.id, n)}
                        className={`size-9 rounded-md border text-sm font-medium transition-colors ${
                          values[q.id] === n
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-surface hover:bg-accent-light"
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between text-xs text-text-secondary mt-1">
                    <span>{q.lowLabel}</span>
                    <span>{q.highLabel}</span>
                  </div>
                </div>
              )}

              {q.type === "choice" && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {q.options.map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setValue(q.id, opt)}
                      className={`h-9 px-3 rounded-md border text-sm font-medium transition-colors ${
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

              {q.type === "text" && (
                <textarea
                  rows={2}
                  value={(values[q.id] as string) ?? ""}
                  onChange={(e) => setValue(q.id, e.target.value)}
                  className="mt-2 w-full text-sm p-2 rounded-md border bg-surface"
                />
              )}
            </div>
          ))}
        </div>

        <DialogFooter className="mt-2">
          <button
            onClick={skip}
            className="h-9 px-4 rounded-md text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            Skip for now
          </button>
          <button
            onClick={submit}
            className="h-9 px-4 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-sm font-medium transition-colors"
          >
            Submit
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
