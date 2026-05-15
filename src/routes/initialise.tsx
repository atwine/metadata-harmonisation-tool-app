import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Play,
  Trash2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/initialise")({
  component: InitialisePage,
});

const DEFAULT_PROMPT =
  "As an AI, you're given the task of translating short variable names from a public health study into the most likely full variable name.";

function InitialisePage() {
  const [tipsOpen, setTipsOpen] = useState(false);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);

  const studies = [
    {
      name: "cohort_2019",
      descriptions: true,
      embeddings: true,
      recommendations: true,
      pid: true,
    },
    {
      name: "cohort_2021",
      descriptions: true,
      embeddings: true,
      recommendations: false,
      pid: false,
    },
  ];

  const Cell = ({ ok }: { ok: boolean }) =>
    ok ? (
      <CheckCircle2 className="size-4 text-success" />
    ) : (
      <XCircle className="size-4 text-text-secondary" />
    );

  return (
    <div className="max-w-[800px]">
      <PageHeader
        title="Initialise"
        subtitle="Generate AI embeddings and build semantic recommendations for all studies."
      />

      {/* connection banner */}
      <div className="bg-success-light border border-l-4 border-l-success rounded-md p-4 flex items-start gap-3">
        <CheckCircle2 className="size-5 text-success mt-0.5" />
        <div className="text-[13px]">
          Connected to OpenAI · chat: gpt-4o-mini · embedding:
          text-embedding-3-small
        </div>
      </div>

      {/* prompt */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[13px] font-medium">
            Initialisation Prompt
          </label>
          <button
            onClick={() => setPrompt(DEFAULT_PROMPT)}
            className="text-[12px] text-primary hover:underline"
          >
            Reset to default
          </button>
        </div>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full text-[13px] p-3 rounded-md border bg-surface font-mono"
        />

        <div className="mt-2 bg-surface border rounded-md">
          <button
            onClick={() => setTipsOpen((o) => !o)}
            className="w-full flex items-center justify-between p-3"
          >
            <span className="text-[13px] font-medium">Prompt tips</span>
            {tipsOpen ? (
              <ChevronDown className="size-4 text-text-secondary" />
            ) : (
              <ChevronRight className="size-4 text-text-secondary" />
            )}
          </button>
          {tipsOpen && (
            <ul className="px-4 pb-3 text-[13px] text-text-primary space-y-1 list-disc list-inside">
              <li>Mention the study domain (e.g., maternal health, TB).</li>
              <li>List common abbreviations used in the dataset.</li>
              <li>Specify the target unit system (SI vs Imperial).</li>
              <li>Avoid ambiguous synonyms in the prompt itself.</li>
            </ul>
          )}
        </div>
      </div>

      {/* studies table */}
      <div className="mt-6">
        <h2 className="section-heading mb-2">Studies</h2>
        <div className="bg-surface border rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-primary text-primary-foreground">
                <th className="text-left px-3 h-9 font-medium">Study Name</th>
                <th className="text-left px-3 h-9 font-medium">Descriptions</th>
                <th className="text-left px-3 h-9 font-medium">Embeddings</th>
                <th className="text-left px-3 h-9 font-medium">
                  Recommendations
                </th>
                <th className="text-left px-3 h-9 font-medium">PID+Date</th>
              </tr>
            </thead>
            <tbody>
              {studies.map((s, i) => (
                <tr
                  key={s.name}
                  style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
                >
                  <td className="px-3 h-9 font-mono text-[12px]">{s.name}</td>
                  <td className="px-3 h-9">
                    <Cell ok={s.descriptions} />
                  </td>
                  <td className="px-3 h-9">
                    <Cell ok={s.embeddings} />
                  </td>
                  <td className="px-3 h-9">
                    <Cell ok={s.recommendations} />
                  </td>
                  <td className="px-3 h-9">
                    <Cell ok={s.pid} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* run button */}
      <div className="mt-6">
        <button className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-[14px] font-medium flex items-center justify-center gap-2 transition-colors">
          <Play className="size-4" />
          Run Recommendation Engine
        </button>
        <p className="text-[12px] text-text-secondary mt-2 text-center">
          This will generate descriptions, embeddings, and semantic matches for
          all uninitialised studies.
        </p>
      </div>

      {/* progress log */}
      <div
        className="mt-4 rounded-md p-3 font-mono text-[13px] text-white overflow-y-auto"
        style={{ background: "#1A1A1A", height: 160 }}
      >
        <div>[✓] PDF conversion complete</div>
        <div>[✓] Descriptions generated for cohort_2019 (47/47)</div>
        <div className="text-accent">
          [→] Generating embeddings for cohort_2021...
        </div>
      </div>

      <div className="border-t my-6" />

      {/* clear workspace */}
      <div className="flex flex-col items-end gap-1">
        <button className="inline-flex items-center gap-2 h-9 px-4 rounded-md border border-danger text-danger hover:bg-primary-light text-[13px] font-medium transition-colors">
          <Trash2 className="size-4" />
          Clear Workspace
        </button>
        <span className="text-[12px] text-text-secondary">
          Deletes all uploaded files and results. This cannot be undone.
        </span>
      </div>
    </div>
  );
}
