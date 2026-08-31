import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Play,
  Trash2,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Globe,
} from "lucide-react";
import type { Step } from "react-joyride";
import { PageHeader } from "@/components/Sidebar";
import { ProductTour, TourReplayButton } from "@/components/ProductTour";
import { useProductTour } from "@/hooks/useProductTour";
import { useInitialiseStatus, useClearWorkspace } from "@/api/client";
import { useAIConfigStore } from "@/stores/aiConfigStore";
import { useWizardStore } from "@/stores/wizardStore";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export const Route = createFileRoute("/initialise")({
  component: InitialisePage,
});

const TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="afpo-toggle"]',
    title: "Optional: AfPO mapping",
    content:
      "Turn this on only if this study has population/ethnicity data you want matched against the African Population Ontology. Off by default.",
    placement: "bottom",
  },
  {
    target: '[data-tour="init-prompt"]',
    title: "Initialisation prompt",
    content:
      'Tune this to help the AI understand your study\'s domain — see "Prompt tips" below for ideas.',
    placement: "right",
  },
  {
    target: '[data-tour="run-button"]',
    title: "Run it",
    content:
      "Once your AI provider is configured (sidebar), click here to generate descriptions, embeddings, and match recommendations for every uploaded study.",
    placement: "top",
  },
  {
    target: '[data-tour="studies-status"]',
    title: "Track progress",
    content: "Checkmarks here show what's been generated for each study as the run progresses.",
    placement: "left",
  },
  {
    target: '[data-tour="danger-zone"]',
    title: "Danger Zone",
    content:
      "Wipes the codebook, every study, and every mapping result. There's a confirmation dialog, so it's hard to trigger by accident.",
    placement: "top",
  },
];

const DEFAULT_PROMPT =
  "As an AI, you're given the task of translating short variable names from a public health study into the most likely full variable name.";

interface LogLine {
  text: string;
  type: "info" | "ok" | "running" | "error";
}

type RunResult = "idle" | "success" | "error";

function InitialisePage() {
  const [tipsOpen, setTipsOpen] = useState(false);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [forceRerun, setForceRerun] = useState(false);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<LogLine[]>([]);
  const [runResult, setRunResult] = useState<RunResult>("idle");
  const [alreadyDoneNotice, setAlreadyDoneNotice] = useState(false);

  const { data: statusData, refetch: refetchStatus } = useInitialiseStatus();
  const clearWorkspace = useClearWorkspace();
  const { config, connectionStatus } = useAIConfigStore();
  const { afpoMappingEnabled, toggleAfpoMapping } = useWizardStore();
  const tour = useProductTour("initialise");

  const studies = statusData?.studies ?? [];

  const allAlreadyInitialised =
    !!statusData?.codebook_embedded &&
    studies.length > 0 &&
    studies.every((s) => s.recommendations_ready && s.pid_date_ready);

  const appendLog = (line: LogLine) => setLog((prev) => [...prev, line]);

  const handleRun = async () => {
    if (!config) return;

    if (!forceRerun && allAlreadyInitialised) {
      setAlreadyDoneNotice(true);
      return;
    }
    setAlreadyDoneNotice(false);

    setRunning(true);
    setRunResult("idle");
    setLog([]);
    let sawError = false;
    let sawComplete = false;

    const body = {
      ai_config: config,
      init_prompt: prompt,
      force_rerun: forceRerun,
    };

    try {
      const resp = await fetch(`${BASE}/api/initialise/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!resp.ok || !resp.body) {
        appendLog({ text: `Error: ${resp.statusText}`, type: "error" });
        sawError = true;
        setRunning(false);
        setRunResult("error");
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";

        for (const part of parts) {
          const dataLine = part.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          try {
            const ev = JSON.parse(dataLine.slice(5)) as {
              step: string;
              status: string;
              message: string;
            };
            const type: LogLine["type"] =
              ev.status === "done"
                ? "ok"
                : ev.status === "error"
                  ? "error"
                  : ev.status === "running"
                    ? "running"
                    : "info";
            if (type === "error") sawError = true;
            if (ev.step === "complete" && ev.status === "done") sawComplete = true;
            appendLog({ text: ev.message, type });
          } catch {
            /* skip malformed SSE */
          }
        }
      }
    } catch (err) {
      appendLog({ text: `Connection error: ${String(err)}`, type: "error" });
      sawError = true;
    } finally {
      setRunning(false);
      setRunResult(sawError || !sawComplete ? "error" : "success");
      void refetchStatus();
    }
  };

  const handleClear = () => {
    clearWorkspace.mutate(undefined, {
      onSuccess: () => void refetchStatus(),
    });
  };

  const Cell = ({ ok }: { ok: boolean }) =>
    ok ? (
      <CheckCircle2 className="size-4 text-success" />
    ) : (
      <XCircle className="size-4 text-text-secondary" />
    );

  const providerLabel: Record<string, string> = {
    ollama: "Ollama",
    vllm: "vLLM",
    openai: "OpenAI",
    anthropic: "Anthropic",
    azure_openai: "Azure OpenAI",
  };

  return (
    <div className="max-w-[1200px]">
      <ProductTour steps={TOUR_STEPS} run={tour.run} onEvent={tour.handleEvent} />

      <div className="flex items-center justify-between gap-4">
        <PageHeader
          title="Initialise"
          subtitle="Generate AI embeddings and build semantic recommendations for all studies."
        />
        <TourReplayButton onClick={tour.start} />
      </div>

      {/* connection banner */}
      {connectionStatus === "connected" && config ? (
        <div className="bg-success-light border border-l-4 border-l-success rounded-md p-4 flex items-start gap-3">
          <CheckCircle2 className="size-5 text-success mt-0.5" />
          <div className="text-base">
            Chat: {config.chat.model} ({providerLabel[config.chat.provider] ?? config.chat.provider}
            )
            {config.embedding
              ? ` · Embedding: ${config.embedding.model} (${providerLabel[config.embedding.provider] ?? config.embedding.provider})`
              : ""}
          </div>
        </div>
      ) : (
        <div className="bg-accent-light border border-l-4 border-l-accent rounded-md p-4 flex items-start gap-3">
          <AlertTriangle className="size-5 text-accent mt-0.5" />
          <div className="text-base">
            AI not configured. Open the AI Configuration panel in the sidebar and test your
            connection before running.
          </div>
        </div>
      )}

      {alreadyDoneNotice && (
        <div className="mt-3 bg-danger-light border border-l-4 border-l-danger rounded-md p-4 flex items-start gap-3">
          <XCircle className="size-5 text-danger mt-0.5" />
          <div className="text-base">
            All studies are already initialised — recommendations have already been generated. Check
            "Force re-run" above if you want to regenerate them, or head to Map Studies to continue.
          </div>
        </div>
      )}

      {/* AfPO opt-in (issue #18) — off by default; not every study wants the
          population/ethnicity ontology pathway forced on it. Read on Map
          Studies to gate whether the AfPO section renders at all. */}
      <div
        className="mt-3 border rounded-md p-4 flex items-center justify-between gap-4"
        data-tour="afpo-toggle"
      >
        <div className="flex items-start gap-3">
          <Globe className="size-5 text-primary mt-0.5" />
          <div>
            <div className="text-base font-medium">AfPO population/ethnicity mapping</div>
            <p className="text-sm text-text-secondary mt-0.5">
              When enabled, Map Studies offers an extra step for variables that look like
              population/ethnicity data: matching values against the African Population Ontology,
              with one-click submission of any unmatched terms. Off by default — turn on only if
              this study needs it.
            </p>
          </div>
        </div>
        <button
          onClick={toggleAfpoMapping}
          className={`relative w-9 h-5 rounded-full transition-colors shrink-0 ${
            afpoMappingEnabled ? "bg-primary" : "bg-border"
          }`}
          aria-label="toggle AfPO population/ethnicity mapping"
        >
          <span
            className={`absolute top-0.5 size-4 rounded-full bg-white transition-all ${
              afpoMappingEnabled ? "left-4" : "left-0.5"
            }`}
          />
        </button>
      </div>

      {/* two columns: controls on the left, live status/output on the right */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start mt-6">
        {/* LEFT: configuration + run */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-base font-medium">Initialisation Prompt</label>
            <button
              onClick={() => setPrompt(DEFAULT_PROMPT)}
              className="text-sm text-primary hover:underline"
            >
              Reset to default
            </button>
          </div>
          <textarea
            data-tour="init-prompt"
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full text-base p-3 rounded-md border bg-surface font-mono"
          />

          <div className="mt-2 bg-surface border rounded-md">
            <button
              onClick={() => setTipsOpen((o) => !o)}
              className="w-full flex items-center justify-between p-3"
            >
              <span className="text-base font-medium">Prompt tips</span>
              {tipsOpen ? (
                <ChevronDown className="size-4 text-text-secondary" />
              ) : (
                <ChevronRight className="size-4 text-text-secondary" />
              )}
            </button>
            {tipsOpen && (
              <ul className="px-4 pb-3 text-base text-text-primary space-y-1 list-disc list-inside">
                <li>Mention the study domain (e.g., maternal health, TB).</li>
                <li>List common abbreviations used in the dataset.</li>
                <li>Specify the target unit system (SI vs Imperial).</li>
                <li>Avoid ambiguous synonyms in the prompt itself.</li>
              </ul>
            )}
          </div>

          <label className="mt-3 flex items-center gap-2 text-base cursor-pointer select-none">
            <input
              type="checkbox"
              checked={forceRerun}
              onChange={(e) => {
                setForceRerun(e.target.checked);
                if (e.target.checked) setAlreadyDoneNotice(false);
              }}
              className="rounded"
            />
            Force re-run (overwrite existing results)
          </label>

          <div className="mt-6">
            <button
              data-tour="run-button"
              onClick={() => void handleRun()}
              disabled={running || connectionStatus !== "connected"}
              className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-md font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="size-4" />
              {running ? "Running…" : "Run Recommendation Engine"}
            </button>
            <p className="text-sm text-text-secondary mt-2 text-center">
              This will generate descriptions, embeddings, and semantic matches for all
              uninitialised studies.
            </p>
          </div>
        </div>

        {/* RIGHT: live status/output */}
        <div data-tour="studies-status">
          <h2 className="section-heading mb-2">Studies</h2>
          <div className="bg-surface border rounded-lg overflow-x-auto shadow-sm">
            <table className="w-full text-base">
              <thead>
                <tr className="bg-primary text-primary-foreground">
                  <th className="text-left px-3 h-9 font-medium whitespace-nowrap">Study</th>
                  <th className="text-left px-3 h-9 font-medium whitespace-nowrap">Desc</th>
                  <th className="text-left px-3 h-9 font-medium whitespace-nowrap">Embed</th>
                  <th className="text-left px-3 h-9 font-medium whitespace-nowrap">Recs</th>
                  <th className="text-left px-3 h-9 font-medium whitespace-nowrap">PID+Date</th>
                </tr>
              </thead>
              <tbody>
                {studies.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-text-secondary">
                      No studies uploaded yet.
                    </td>
                  </tr>
                ) : (
                  studies.map((s, i) => (
                    <tr key={s.name} style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}>
                      <td className="px-3 h-9 font-mono text-sm">{s.name}</td>
                      <td className="px-3 h-9">
                        <Cell ok={s.descriptions_generated} />
                      </td>
                      <td className="px-3 h-9">
                        <Cell ok={s.embeddings_ready} />
                      </td>
                      <td className="px-3 h-9">
                        <Cell ok={s.recommendations_ready} />
                      </td>
                      <td className="px-3 h-9">
                        <Cell ok={s.pid_date_ready} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* progress log */}
          <div
            className="mt-4 rounded-md p-3 font-mono text-base text-white overflow-y-auto"
            style={{ background: "#1A1A1A", height: 160 }}
          >
            {log.length === 0 ? (
              <div className="text-text-secondary opacity-50">Waiting to start…</div>
            ) : (
              log.map((l, i) => (
                <div
                  key={i}
                  className={
                    l.type === "ok"
                      ? "text-green-400"
                      : l.type === "error"
                        ? "text-red-400"
                        : l.type === "running"
                          ? "text-yellow-300"
                          : "text-white"
                  }
                >
                  {l.type === "ok" ? "[✓] " : l.type === "error" ? "[✗] " : "[→] "}
                  {l.text}
                </div>
              ))
            )}
          </div>

          {/* run result banner — the whole point being: don't leave the user guessing
              once the black log box goes quiet */}
          {!running && runResult !== "idle" && (
            <div
              className={`mt-3 rounded-md p-4 flex items-start gap-3 border border-l-4 ${
                runResult === "success"
                  ? "bg-success-light border-l-success"
                  : "bg-danger-light border-l-danger"
              }`}
            >
              {runResult === "success" ? (
                <CheckCircle2 className="size-5 text-success mt-0.5" />
              ) : (
                <XCircle className="size-5 text-danger mt-0.5" />
              )}
              <div className="text-base font-medium">
                {runResult === "success"
                  ? "Recommendation engine finished successfully. You can head to Map Studies."
                  : "Recommendation engine failed — see the error above for details."}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* danger zone */}
      <div
        className="mt-8 border border-danger/30 bg-danger-light/40 rounded-lg p-4"
        data-tour="danger-zone"
      >
        <h2 className="text-base font-semibold text-danger mb-2">Danger Zone</h2>
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-text-secondary">
            Deletes all uploaded files and results. This cannot be undone.
          </span>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <button className="inline-flex items-center gap-2 h-9 px-4 rounded-md border border-danger text-danger hover:bg-white text-base font-medium transition-colors shrink-0 whitespace-nowrap">
                <Trash2 className="size-4" />
                Clear Workspace
              </button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear workspace?</AlertDialogTitle>
                <AlertDialogDescription asChild>
                  <div className="space-y-2">
                    <p>
                      This permanently deletes the uploaded codebook, every mapping result, and all{" "}
                      {studies.length} uploaded {studies.length === 1 ? "study" : "studies"}
                      {studies.length > 0 && (
                        <>
                          {" "}
                          (
                          <span className="font-medium">
                            {studies.map((s) => s.name).join(", ")}
                          </span>
                          )
                        </>
                      )}
                      . This cannot be undone.
                    </p>
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleClear}
                  className="bg-danger text-white hover:bg-danger/90"
                >
                  Yes, clear workspace
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}
