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
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useInitialiseStatus, useClearWorkspace } from "@/api/client";
import { useAIConfigStore } from "@/stores/aiConfigStore";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export const Route = createFileRoute("/initialise")({
  component: InitialisePage,
});

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
  const [confirmClear, setConfirmClear] = useState(false);
  const [runResult, setRunResult] = useState<RunResult>("idle");
  const [alreadyDoneNotice, setAlreadyDoneNotice] = useState(false);

  const { data: statusData, refetch: refetchStatus } = useInitialiseStatus();
  const clearWorkspace = useClearWorkspace();
  const { config, connectionStatus } = useAIConfigStore();

  const studies = statusData?.studies ?? [];

  const allAlreadyInitialised =
    !!statusData?.codebook_embedded &&
    studies.length > 0 &&
    studies.every((s) => s.recommendations_ready && s.pid_date_ready);

  const appendLog = (line: LogLine) =>
    setLog((prev) => [...prev, line]);

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
          const dataLine = part
            .split("\n")
            .find((l) => l.startsWith("data:"));
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
    setConfirmClear(false);
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
    <div className="max-w-[800px]">
      <PageHeader
        title="Initialise"
        subtitle="Generate AI embeddings and build semantic recommendations for all studies."
      />

      {/* connection banner */}
      {connectionStatus === "connected" && config ? (
        <div className="bg-success-light border border-l-4 border-l-success rounded-md p-4 flex items-start gap-3">
          <CheckCircle2 className="size-5 text-success mt-0.5" />
          <div className="text-[13px]">
            Chat: {config.chat.model} ({providerLabel[config.chat.provider] ?? config.chat.provider})
            {config.embedding
              ? ` · Embedding: ${config.embedding.model} (${providerLabel[config.embedding.provider] ?? config.embedding.provider})`
              : ""}
          </div>
        </div>
      ) : (
        <div className="bg-accent-light border border-l-4 border-l-accent rounded-md p-4 flex items-start gap-3">
          <AlertTriangle className="size-5 text-accent mt-0.5" />
          <div className="text-[13px]">
            AI not configured. Open the AI Configuration panel in the sidebar and test
            your connection before running.
          </div>
        </div>
      )}

      {/* prompt */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[13px] font-medium">Initialisation Prompt</label>
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

        <label className="mt-3 flex items-center gap-2 text-[13px] cursor-pointer select-none">
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
      </div>

      {alreadyDoneNotice && (
        <div className="mt-3 bg-danger-light border border-l-4 border-l-danger rounded-md p-4 flex items-start gap-3">
          <XCircle className="size-5 text-danger mt-0.5" />
          <div className="text-[13px]">
            All studies are already initialised — recommendations have already been
            generated. Check "Force re-run" above if you want to regenerate them, or
            head to Map Studies to continue.
          </div>
        </div>
      )}

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
                <th className="text-left px-3 h-9 font-medium">Recommendations</th>
                <th className="text-left px-3 h-9 font-medium">PID+Date</th>
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
                  <tr
                    key={s.name}
                    style={{ background: i % 2 ? "#FAFAF8" : "#FFFFFF" }}
                  >
                    <td className="px-3 h-9 font-mono text-[12px]">{s.name}</td>
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
      </div>

      {/* run button */}
      <div className="mt-6">
        <button
          onClick={() => void handleRun()}
          disabled={running || connectionStatus !== "connected"}
          className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-[14px] font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play className="size-4" />
          {running ? "Running…" : "Run Recommendation Engine"}
        </button>
        <p className="text-[12px] text-text-secondary mt-2 text-center">
          This will generate descriptions, embeddings, and semantic matches for all
          uninitialised studies.
        </p>
      </div>

      {/* progress log */}
      <div
        className="mt-4 rounded-md p-3 font-mono text-[13px] text-white overflow-y-auto"
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
          <div className="text-[13px] font-medium">
            {runResult === "success"
              ? "Recommendation engine finished successfully. You can head to Map Studies."
              : "Recommendation engine failed — see the error above for details."}
          </div>
        </div>
      )}

      <div className="border-t my-6" />

      {/* clear workspace */}
      <div className="flex flex-col items-end gap-1">
        {confirmClear ? (
          <div className="flex items-center gap-3">
            <span className="text-[13px] text-danger font-medium">
              Delete all files and results?
            </span>
            <button
              onClick={handleClear}
              className="h-9 px-4 rounded-md bg-danger text-white text-[13px] font-medium"
            >
              Yes, clear
            </button>
            <button
              onClick={() => setConfirmClear(false)}
              className="h-9 px-4 rounded-md border text-[13px]"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmClear(true)}
            className="inline-flex items-center gap-2 h-9 px-4 rounded-md border border-danger text-danger hover:bg-primary-light text-[13px] font-medium transition-colors"
          >
            <Trash2 className="size-4" />
            Clear Workspace
          </button>
        )}
        <span className="text-[12px] text-text-secondary">
          Deletes all uploaded files and results. This cannot be undone.
        </span>
      </div>
    </div>
  );
}
