import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { isEvalBuild } from "@/lib/evalBuild";
import { useEvalStore } from "@/stores/evalStore";

export const Route = createFileRoute("/eval-questionnaire")({
  component: EvalQuestionnairePage,
});

const SUS_STATEMENTS = [
  "I think that I would like to use this tool frequently.",
  "I found the tool unnecessarily complex.",
  "I thought the tool was easy to use.",
  "I think that I would need the support of a technical person to be able to use this tool.",
  "I found the various functions in this tool were well integrated.",
  "I thought there was too much inconsistency in this tool.",
  "I would imagine that most people would learn to use this tool very quickly.",
  "I found the tool very cumbersome to use.",
  "I felt very confident using the tool.",
  "I needed to learn a lot of things before I could get going with this tool.",
];

const OPEN_ENDED = [
  "What was the most confusing part of the entire process (installation and/or harmonisation)?",
  "Was there a point where you were unsure what to do next? If so, what were you trying to do?",
  "Did the tool's recommendations match your expectations? Were they helpful, or did you feel you were overriding them most of the time?",
  "If you could change one thing about the tool, what would it be?",
  "Would you use this tool for your own harmonisation work? Why or why not?",
  "How does this compare to how you currently harmonise data (if applicable)? Is it faster, slower, easier, harder?",
];

const BACKGROUND: { id: string; label: string; options?: string[] }[] = [
  { id: "role", label: "What is your role? (e.g., researcher, data manager, statistician)" },
  { id: "experience_years", label: "How many years of experience do you have working with health research data?" },
  {
    id: "harmonisation_experience",
    label: "Have you done data harmonisation before?",
    options: ["Never", "Once or twice", "Regularly"],
  },
  {
    id: "cli_comfort",
    label: "How comfortable are you with command-line tools?",
    options: ["Not at all", "Somewhat", "Very"],
  },
  {
    id: "docker_comfort",
    label: "How comfortable are you with Docker?",
    options: ["Not at all", "Somewhat", "Very"],
  },
];

function ScaleRow({ value, onChange }: { value?: number; onChange: (n: number) => void }) {
  return (
    <div className="flex gap-1.5 shrink-0">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          className={`size-9 rounded-md border text-sm font-medium transition-colors ${
            value === n
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-surface hover:bg-accent-light"
          }`}
        >
          {n}
        </button>
      ))}
    </div>
  );
}

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
          className={`h-9 px-3 rounded-md border text-sm font-medium transition-colors ${
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

function EvalQuestionnairePage() {
  const setQuestionnaire = useEvalStore((s) => s.setQuestionnaire);
  const alreadySubmitted = useEvalStore(
    (s) => s.questionnaireAnswers !== null || s.questionnaireSkipped,
  );
  const [susAnswers, setSusAnswers] = useState<Record<number, number>>({});
  const [openAnswers, setOpenAnswers] = useState<Record<number, string>>({});
  const [backgroundAnswers, setBackgroundAnswers] = useState<Record<string, string>>({});

  if (!isEvalBuild()) {
    return <div className="max-w-[800px] text-text-secondary">This page isn't available.</div>;
  }

  if (alreadySubmitted) {
    return (
      <div className="max-w-[800px]">
        <PageHeader title="Evaluation Report" />
        <div className="bg-success-light border border-l-4 border-l-success rounded-md p-4 flex items-start gap-3 mt-4">
          <CheckCircle2 className="size-5 text-success mt-0.5" />
          <div className="text-base">
            Thanks — your questionnaire response has been recorded for this session.
          </div>
        </div>
      </div>
    );
  }

  const submit = (skipped: boolean) => {
    const answers: Record<string, string | number> = {};
    Object.entries(susAnswers).forEach(([i, v]) => (answers[`sus_${i}`] = v));
    Object.entries(openAnswers).forEach(([i, v]) => (answers[`open_${i}`] = v));
    Object.entries(backgroundAnswers).forEach(([k, v]) => (answers[`background_${k}`] = v));
    setQuestionnaire(answers, skipped);
  };

  return (
    <div className="max-w-[800px]">
      <PageHeader
        title="Evaluation Report"
        subtitle="This is the important part for our research — it takes about 5 minutes."
      />

      <section className="mt-6">
        <h2 className="section-heading mb-3">Part A — Quick reactions</h2>
        <p className="text-sm text-text-secondary mb-4">
          For each statement, pick a number from 1 (Strongly Disagree) to 5 (Strongly Agree).
          Don't overthink it — first reaction is best.
        </p>
        <div className="space-y-4">
          {SUS_STATEMENTS.map((statement, i) => (
            <div
              key={i}
              className="flex items-center justify-between gap-4 bg-surface border rounded-md p-3"
            >
              <span className="text-sm">{statement}</span>
              <ScaleRow
                value={susAnswers[i]}
                onChange={(n) => setSusAnswers((a) => ({ ...a, [i]: n }))}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="section-heading mb-3">Part B — In your own words</h2>
        <div className="space-y-4">
          {OPEN_ENDED.map((q, i) => (
            <div key={i}>
              <label className="text-sm font-medium">{q}</label>
              <textarea
                rows={2}
                value={openAnswers[i] ?? ""}
                onChange={(e) => setOpenAnswers((a) => ({ ...a, [i]: e.target.value }))}
                className="mt-1.5 w-full text-sm p-2 rounded-md border bg-surface"
              />
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="section-heading mb-3">Part C — A bit about you</h2>
        <div className="space-y-4">
          {BACKGROUND.map((q) => (
            <div key={q.id}>
              <label className="text-sm font-medium">{q.label}</label>
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
                  className="mt-1.5 w-full text-sm p-2 rounded-md border bg-surface"
                />
              )}
            </div>
          ))}
        </div>
      </section>

      <div className="mt-8 flex items-center justify-end gap-3 border-t pt-4">
        <button
          onClick={() => submit(true)}
          className="h-10 px-4 rounded-md text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
        >
          Skip for now
        </button>
        <button
          onClick={() => submit(false)}
          className="h-10 px-6 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-sm font-medium transition-colors"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
