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
import { useTestConnection } from "@/api/client";

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
    <div className="grid grid-cols-3 gap-[3px] w-[26px] h-[26px]">
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
  const [open, setOpen] = useState(false);
  const { config, setConfig, connectionStatus, setConnectionStatus } = useAIConfigStore();
  const testConn = useTestConnection();

  const provider = config?.provider ?? "ollama";
  const showEmbedding = provider !== "anthropic";
  const showApiKey = provider !== "ollama";
  const showBaseUrl = provider === "ollama" || provider === "azure_openai";

  const update = (patch: Partial<typeof config>) =>
    setConfig({ ...(config ?? { provider: "ollama", chat_model: "", embedding_model: "", request_timeout: 60 }), ...patch } as NonNullable<typeof config>);

  const handleTest = () => {
    if (!config) return;
    setConnectionStatus("unconfigured");
    testConn.mutate(config, {
      onSuccess: (res) => setConnectionStatus(res.connected ? "connected" : "failed"),
      onError: () => setConnectionStatus("failed"),
    });
  };

  const statusLabel =
    connectionStatus === "connected"
      ? `Connected — ${config?.chat_model ?? ""}`
      : connectionStatus === "failed"
        ? "Connection failed"
        : "Not configured";

  const statusColor =
    connectionStatus === "connected"
      ? "bg-success"
      : connectionStatus === "failed"
        ? "bg-danger"
        : "bg-primary";

  return (
    <div className="px-3 py-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between text-[10px] font-medium tracking-widest text-text-secondary uppercase px-1 hover:text-text-primary"
      >
        <span>AI Configuration</span>
        {open ? (
          <ChevronDown className="size-3" />
        ) : (
          <ChevronRight className="size-3" />
        )}
      </button>
      {open && (
        <div className="mt-3 space-y-2">
          <div>
            <label className="label-caption">Provider</label>
            <select
              value={provider}
              onChange={(e) => {
                const p = e.target.value as typeof provider;
                const defs = PROVIDER_DEFAULTS[p] ?? { chat_model: "", embedding_model: "" };
                update({ provider: p, ...defs });
              }}
              className="mt-0.5 w-full h-8 text-xs px-2 rounded-md border bg-surface"
            >
              <option value="ollama">Ollama (Local)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="azure_openai">Azure OpenAI</option>
            </select>
          </div>
          <div>
            <label className="label-caption">Chat model</label>
            <input
              value={config?.chat_model ?? ""}
              onChange={(e) => update({ chat_model: e.target.value })}
              placeholder="llama3.1:8b"
              className="mt-0.5 w-full h-8 text-xs px-2 rounded-md border bg-surface"
            />
          </div>
          {showEmbedding && (
            <div>
              <label className="label-caption">Embedding model</label>
              <input
                value={config?.embedding_model ?? ""}
                onChange={(e) => update({ embedding_model: e.target.value })}
                placeholder="nomic-embed-text"
                className="mt-0.5 w-full h-8 text-xs px-2 rounded-md border bg-surface"
              />
            </div>
          )}
          {showApiKey && (
            <div>
              <label className="label-caption">API Key</label>
              <input
                type="password"
                value={config?.api_key ?? ""}
                onChange={(e) => update({ api_key: e.target.value })}
                placeholder="sk-..."
                className="mt-0.5 w-full h-8 text-xs px-2 rounded-md border bg-surface"
              />
            </div>
          )}
          {showBaseUrl && (
            <div>
              <label className="label-caption">Base URL</label>
              <input
                value={config?.base_url ?? ""}
                onChange={(e) => update({ base_url: e.target.value })}
                placeholder="http://localhost:11434"
                className="mt-0.5 w-full h-8 text-xs px-2 rounded-md border bg-surface"
              />
            </div>
          )}
          <button
            onClick={handleTest}
            disabled={testConn.isPending}
            className="w-full h-8 text-xs rounded-md border border-primary text-primary font-medium hover:bg-primary-light transition-colors disabled:opacity-50"
          >
            {testConn.isPending ? "Testing…" : "Test Connection"}
          </button>
          {testConn.isSuccess && testConn.data && !testConn.data.connected && (
            <div className="text-[11px] text-danger">{testConn.data.message}</div>
          )}
          <div className="flex items-center gap-2 text-[11px] pt-1">
            <span className={`size-2 rounded-full ${statusColor}`} />
            <span className="text-text-secondary">{statusLabel}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  const location = useLocation();
  return (
    <aside className="fixed top-0 left-0 h-screen w-60 bg-surface border-r flex flex-col z-30">
      <div className="px-4 py-3 flex items-center gap-3">
        <BrandDots />
        <div className="leading-tight">
          <div className="text-[14px] font-semibold text-text-primary">
            Metadata Harmonisation
          </div>
          <div className="text-[10px] text-text-secondary">
            eLwazi Open Data Science Platform
          </div>
        </div>
      </div>
      <div className="border-t" />
      <div className="px-3 pt-3 pb-1">
        <span className="text-[10px] font-medium tracking-widest text-text-secondary uppercase">
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
              className={`flex items-center gap-2.5 text-[13px] px-3 py-2 rounded-md transition-colors border-l-[3px] ${
                active
                  ? "bg-primary-light border-primary text-primary font-medium"
                  : "border-transparent text-text-primary hover:bg-[#F5F0EE]"
              }`}
            >
              <Icon className="size-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="border-t" />
      <AIConfigPanel />
      <div className="border-t" />
      <div className="px-4 py-2 text-[11px] text-text-secondary">v0.5.0</div>
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
