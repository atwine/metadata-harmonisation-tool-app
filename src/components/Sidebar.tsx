import { Link, useLocation } from "@tanstack/react-router";
import { useState } from "react";
import {
  Home,
  FileSpreadsheet,
  FolderOpen,
  Cpu,
  GitMerge,
  Download,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useAIConfigStore } from "@/stores/aiConfigStore";
import { useTestConnection, useOllamaModels } from "@/api/client";

const NAV = [
  { to: "/", label: "Home", icon: Home },
  { to: "/upload-codebook", label: "Upload Codebook", icon: FileSpreadsheet },
  { to: "/upload-studies", label: "Upload Studies", icon: FolderOpen },
  { to: "/initialise", label: "Initialise", icon: Cpu },
  { to: "/map-studies", label: "Map Studies", icon: GitMerge },
  { to: "/download-results", label: "Download Results", icon: Download },
] as const;

function BrandDots() {
  return (
    <div className="grid grid-cols-3 gap-[3px] w-[30px] h-[30px]">
      {[
        "var(--primary)",
        "var(--accent)",
        "var(--success)",
        "var(--accent)",
        "var(--primary)",
        "var(--primary)",
        "var(--success)",
        "var(--primary)",
        "var(--accent)",
      ].map((c, i) => (
        <span
          key={i}
          className="rounded-[2px]"
          style={{ background: c, opacity: 0.85 }}
        />
      ))}
    </div>
  );
}

const PROVIDER_DEFAULTS: Record<string, { chat_model: string; embedding_model: string; base_url?: string }> = {
  ollama: { chat_model: "llama3.1:8b", embedding_model: "nomic-embed-text", base_url: "http://localhost:11434" },
  openai: { chat_model: "gpt-4o-mini", embedding_model: "text-embedding-3-small" },
  anthropic: { chat_model: "claude-3-5-haiku-20241022", embedding_model: "" },
  azure_openai: { chat_model: "", embedding_model: "" },
};

function AIConfigPanel() {
  const [open, setOpen] = useState(true);
  const { config, setConfig, connectionStatus, setConnectionStatus } = useAIConfigStore();
  const testConn = useTestConnection();

  const provider = config?.provider ?? "ollama";
  const showEmbedding = provider !== "anthropic";
  const showApiKey = provider !== "ollama";
  const showBaseUrl = provider === "ollama" || provider === "azure_openai";

  const ollamaBaseUrl = config?.base_url ?? "http://localhost:11434";
  const { data: ollamaModelsData, refetch: refetchOllamaModels } = useOllamaModels(
    ollamaBaseUrl,
    provider === "ollama",
  );
  const ollamaModels = ollamaModelsData?.models ?? [];

  const update = (patch: Partial<typeof config>) =>
    setConfig({ ...(config ?? { provider: "ollama", chat_model: "", embedding_model: "", request_timeout: 30 }), ...patch } as NonNullable<typeof config>);

  const handleTest = () => {
    if (!config) return;
    setConnectionStatus("unconfigured");
    testConn.mutate(config, {
      onSuccess: (res) => {
        setConnectionStatus(res.connected ? "connected" : "failed");
        if (res.connected && provider === "ollama") {
          refetchOllamaModels();
        }
      },
      onError: () => setConnectionStatus("failed"),
    });
  };

  const useOllamaDropdowns = provider === "ollama" && ollamaModels.length > 0;

  return (
    <div className="px-3 py-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between text-[13px] font-medium tracking-widest text-text-secondary uppercase px-1 hover:text-text-primary"
      >
        <span>AI Configuration</span>
        {open ? (
          <ChevronDown className="size-4" />
        ) : (
          <ChevronRight className="size-4" />
        )}
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          {/* Provider */}
          <div>
            <label className="label-caption">Provider</label>
            <select
              value={provider}
              onChange={(e) => {
                const p = e.target.value as typeof provider;
                const defs = PROVIDER_DEFAULTS[p] ?? { chat_model: "", embedding_model: "" };
                update({ provider: p, ...defs });
              }}
              className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
            >
              <option value="ollama">Ollama (Local)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="azure_openai">Azure OpenAI</option>
            </select>
          </div>

          {/* Base URL (Ollama / Azure) */}
          {showBaseUrl && (
            <div>
              <label className="label-caption">Base URL</label>
              <input
                value={config?.base_url ?? ""}
                onChange={(e) => update({ base_url: e.target.value })}
                placeholder="http://localhost:11434"
                className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
              />
            </div>
          )}

          {/* Chat model — dropdown for Ollama when models are loaded */}
          <div>
            <label className="label-caption">Chat model</label>
            {useOllamaDropdowns ? (
              <select
                value={config?.chat_model ?? ""}
                onChange={(e) => update({ chat_model: e.target.value })}
                className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
              >
                {ollamaModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            ) : (
              <input
                value={config?.chat_model ?? ""}
                onChange={(e) => update({ chat_model: e.target.value })}
                placeholder="llama3.1:8b"
                className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
              />
            )}
          </div>

          {/* Embedding model — dropdown for Ollama when models are loaded */}
          {showEmbedding && (
            <div>
              <label className="label-caption">Embedding model</label>
              {useOllamaDropdowns ? (
                <select
                  value={config?.embedding_model ?? ""}
                  onChange={(e) => update({ embedding_model: e.target.value })}
                  className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
                >
                  {ollamaModels.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              ) : (
                <input
                  value={config?.embedding_model ?? ""}
                  onChange={(e) => update({ embedding_model: e.target.value })}
                  placeholder="nomic-embed-text"
                  className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
                />
              )}
            </div>
          )}

          {/* API Key (non-Ollama) */}
          {showApiKey && (
            <div>
              <label className="label-caption">API Key</label>
              <input
                type="password"
                value={config?.api_key ?? ""}
                onChange={(e) => update({ api_key: e.target.value })}
                placeholder="sk-..."
                className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
              />
            </div>
          )}

          {/* ── Request Timeout ─────────────────────────────── */}
          <div className="pt-2 border-t">
            <div className="text-[13px] font-medium tracking-widest text-text-secondary uppercase mb-2">
              ⏱ Request Timeout
            </div>
            <label className="label-caption">Timeout (seconds)</label>
            <div className="mt-1 flex items-center gap-1.5">
              <button
                onClick={() => update({ request_timeout: Math.max(5, (config?.request_timeout ?? 30) - 5) })}
                className="size-9 rounded border text-text-secondary hover:bg-[#F5F0EE] text-base font-bold flex items-center justify-center"
              >
                −
              </button>
              <input
                type="number"
                min={5}
                max={120}
                value={config?.request_timeout ?? 30}
                onChange={(e) => {
                  const v = Math.min(120, Math.max(5, Number(e.target.value)));
                  update({ request_timeout: v });
                }}
                className="flex-1 h-9 text-center text-[14px] rounded border bg-surface"
              />
              <button
                onClick={() => update({ request_timeout: Math.min(120, (config?.request_timeout ?? 30) + 5) })}
                className="size-9 rounded border text-text-secondary hover:bg-[#F5F0EE] text-base font-bold flex items-center justify-center"
              >
                +
              </button>
            </div>
          </div>

          {/* ── Connection Test ──────────────────────────────── */}
          <div className="pt-2 border-t">
            <div className="text-[13px] font-medium tracking-widest text-text-secondary uppercase mb-2">
              🔍 Connection Test
            </div>
            <button
              onClick={handleTest}
              disabled={testConn.isPending}
              className="w-full h-11 text-[14px] rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
            >
              {testConn.isPending ? "Testing connection…" : "Test Connection"}
            </button>

            {/* Result feedback */}
            {testConn.isSuccess && testConn.data && (
              <div className={`mt-2 text-[13px] font-medium flex items-start gap-1.5 ${
                testConn.data.connected ? "text-success" : "text-danger"
              }`}>
                <span>{testConn.data.connected ? "✅" : "❌"}</span>
                <span>
                  {testConn.data.connected ? "Connection verified" : "Connection failed"}
                  {testConn.data.message && (
                    <span className="font-normal opacity-80"> — {testConn.data.message}</span>
                  )}
                </span>
              </div>
            )}
            {testConn.isError && (
              <div className="mt-2 text-[13px] text-danger">
                ❌ {(testConn.error as Error).message}
              </div>
            )}
            {connectionStatus === "connected" && !testConn.isPending && (
              <div className="mt-1.5 flex items-center gap-1.5 text-[13px] text-text-secondary">
                <span className="size-2 rounded-full bg-success inline-block" />
                Connected — {config?.chat_model}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  const location = useLocation();
  return (
    <aside className="fixed top-0 left-0 h-screen w-80 bg-surface border-r flex flex-col z-30">
      <div className="px-4 py-3 flex items-center gap-3">
        <BrandDots />
        <div className="leading-tight">
          <div className="text-[17px] font-semibold text-text-primary">
            Metadata Harmonisation
          </div>
          <div className="text-[13px] text-text-secondary">
            eLwazi Open Data Science Platform
          </div>
        </div>
      </div>
      <div className="border-t" />
      <div className="px-3 pt-3 pb-1">
        <span className="text-[13px] font-medium tracking-widest text-text-secondary uppercase">
          Workflow
        </span>
      </div>
      <nav className="flex-1 px-2 space-y-0.5">
        {NAV.map(({ to, label, icon: Icon }) => {
          const active =
            to === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(to);
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-2.5 text-[15px] px-3 py-2 rounded-md transition-colors border-l-[3px] ${
                active
                  ? "bg-primary-light border-primary text-primary font-medium"
                  : "border-transparent text-text-primary hover:bg-[#F5F0EE]"
              }`}
            >
              <Icon className="size-5" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="border-t" />
      <div className="overflow-y-auto flex-shrink-0 max-h-[60vh]">
        <AIConfigPanel />
      </div>
      <div className="border-t" />
      <div className="px-4 py-2 text-[13px] text-text-secondary shrink-0">v0.5.0</div>
    </aside>
  );
}

export function PageHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <header className="mb-6">
      <h1 className="page-title">{title}</h1>
      <div className="page-title-underline" />
      {subtitle && (
        <p className="mt-3 text-[14px] text-text-secondary max-w-3xl">
          {subtitle}
        </p>
      )}
    </header>
  );
}
