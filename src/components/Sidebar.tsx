import { Link, useLocation } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Home,
  FileSpreadsheet,
  FolderOpen,
  Cpu,
  GitMerge,
  Download,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Layers,
} from "lucide-react";
import { OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBEDDING_MODEL } from "@/lib/ollamaDefaults";
import { useAIConfigStore } from "@/stores/aiConfigStore";
import { useTestConnection, useProviderModels } from "@/api/client";
import type { AIConfig, AIProviderId, ProviderSlot } from "@/types";
import type { SlotTestResult } from "@/api/client";

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

const PROVIDER_LABELS: Record<AIProviderId, string> = {
  ollama: "Ollama (Local)",
  vllm: "vLLM (Self-hosted)",
  openai: "OpenAI",
  anthropic: "Anthropic",
  azure_openai: "Azure OpenAI",
};

const CHAT_PROVIDERS: AIProviderId[] = ["ollama", "vllm", "openai", "anthropic", "azure_openai"];
const EMBEDDING_PROVIDERS: AIProviderId[] = ["ollama", "vllm", "openai", "azure_openai"];

const SLOT_DEFAULTS: Record<"chat" | "embedding", Partial<Record<AIProviderId, Partial<ProviderSlot>>>> = {
  chat: {
    ollama: { model: OLLAMA_CHAT_MODEL, base_url: OLLAMA_BASE_URL },
    vllm: { model: "", base_url: "" },
    openai: { model: "gpt-4o-mini", base_url: undefined },
    anthropic: { model: "claude-3-5-haiku-20241022", base_url: undefined },
    azure_openai: { model: "", base_url: "" },
  },
  embedding: {
    ollama: { model: OLLAMA_EMBEDDING_MODEL, base_url: OLLAMA_BASE_URL },
    vllm: { model: "", base_url: "" },
    openai: { model: "text-embedding-3-small", base_url: undefined },
    azure_openai: { model: "", base_url: "" },
  },
};

function hasLiveModelList(provider: AIProviderId) {
  return provider === "ollama" || provider === "vllm";
}
function showsApiKey(provider: AIProviderId) {
  // Required for these; vLLM only needs one if the server was launched with
  // --api-key, so it's shown but optional there.
  return provider === "openai" || provider === "anthropic" || provider === "azure_openai" || provider === "vllm";
}
function apiKeyRequired(provider: AIProviderId) {
  return provider === "openai" || provider === "anthropic" || provider === "azure_openai";
}
function needsBaseUrl(provider: AIProviderId) {
  return provider === "ollama" || provider === "vllm" || provider === "azure_openai";
}

function ProviderSlotEditor({
  role,
  slot,
  providers,
  onChange,
}: {
  role: "chat" | "embedding";
  slot: ProviderSlot;
  providers: AIProviderId[];
  onChange: (slot: ProviderSlot) => void;
}) {
  const { data: modelsData } = useProviderModels(
    slot.provider,
    slot.base_url ?? "",
    slot.api_key,
    hasLiveModelList(slot.provider),
  );
  const models = modelsData?.models ?? [];
  const useDropdown = hasLiveModelList(slot.provider) && models.length > 0;

  const update = (patch: Partial<ProviderSlot>) => onChange({ ...slot, ...patch });

  // Ollama tags models with a suffix (e.g. "nomic-embed-text:latest") that our
  // untagged defaults (e.g. "nomic-embed-text") won't exactly match — once the
  // live list loads, resolve the default to the matching tagged name.
  useEffect(() => {
    if (!useDropdown) return;
    if (models.includes(slot.model)) return;
    const match = models.find((m) => m === slot.model || m.startsWith(`${slot.model}:`));
    if (match) update({ model: match });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useDropdown, models.join("|"), slot.model]);

  return (
    <div className="border rounded-md bg-surface p-3">
      <div className="flex items-center gap-2 mb-2.5">
        {role === "chat" ? (
          <MessageSquare className="size-4 text-primary" />
        ) : (
          <Layers className="size-4 text-primary" />
        )}
        <span className="text-[14px] font-medium">
          {role === "chat" ? "Chat model" : "Embedding model"}
        </span>
      </div>

      <label className="label-caption">Provider</label>
      <select
        value={slot.provider}
        onChange={(e) => {
          const p = e.target.value as AIProviderId;
          const defs = SLOT_DEFAULTS[role][p] ?? { model: "" };
          onChange({ provider: p, model: defs.model ?? "", base_url: defs.base_url });
        }}
        className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
      >
        {providers.map((p) => (
          <option key={p} value={p}>{PROVIDER_LABELS[p]}</option>
        ))}
      </select>

      {needsBaseUrl(slot.provider) && (
        <div className="mt-2">
          <label className="label-caption">Base URL</label>
          <input
            value={slot.base_url ?? ""}
            onChange={(e) => update({ base_url: e.target.value })}
            placeholder={slot.provider === "vllm" ? "http://<host>:8000" : OLLAMA_BASE_URL}
            className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
          />
        </div>
      )}

      <div className="mt-2">
        <label className="label-caption">Model</label>
        {useDropdown ? (
          <select
            value={slot.model}
            onChange={(e) => update({ model: e.target.value })}
            className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
          >
            <option value="">— select model —</option>
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        ) : (
          <input
            value={slot.model}
            onChange={(e) => update({ model: e.target.value })}
            placeholder="model name"
            className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
          />
        )}
      </div>

      {showsApiKey(slot.provider) && (
        <div className="mt-2">
          <label className="label-caption">
            API Key{!apiKeyRequired(slot.provider) && " (optional)"}
          </label>
          <input
            type="password"
            value={slot.api_key ?? ""}
            onChange={(e) => update({ api_key: e.target.value })}
            placeholder={apiKeyRequired(slot.provider) ? "sk-..." : "leave blank if the server doesn't require one"}
            className="mt-1 w-full h-10 text-[14px] px-2 rounded-md border bg-surface"
          />
        </div>
      )}
    </div>
  );
}

function SlotFeedback({ label, result }: { label: string; result: SlotTestResult }) {
  return (
    <div className={`text-[13px] font-medium flex items-start gap-1.5 ${
      result.connected ? "text-success" : "text-danger"
    }`}>
      <span>{result.connected ? "✅" : "❌"}</span>
      <span>
        {label} {result.connected ? "connected" : "unavailable"}
        <span className="font-normal opacity-80"> — {result.message}</span>
      </span>
    </div>
  );
}

function AIConfigPanel() {
  const [open, setOpen] = useState(true);
  const { config, setConfig, connectionStatus, setConnectionStatus } = useAIConfigStore();
  const testConn = useTestConnection();

  const chatSlot: ProviderSlot = config?.chat ?? {
    provider: "ollama",
    model: OLLAMA_CHAT_MODEL,
    base_url: OLLAMA_BASE_URL,
  };
  const embeddingSlot: ProviderSlot = config?.embedding ?? {
    provider: "ollama",
    model: OLLAMA_EMBEDDING_MODEL,
    base_url: OLLAMA_BASE_URL,
  };

  const updateConfig = (patch: Partial<AIConfig>) =>
    setConfig({
      ...(config ?? { chat: chatSlot, embedding: embeddingSlot, request_timeout: 30 }),
      ...patch,
    } as AIConfig);

  const handleTest = () => {
    if (!config) return;
    setConnectionStatus("unconfigured");
    testConn.mutate(config, {
      onSuccess: (res) => setConnectionStatus(res.connected ? "connected" : "failed"),
      onError: () => setConnectionStatus("failed"),
    });
  };

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
          <ProviderSlotEditor
            role="chat"
            slot={chatSlot}
            providers={CHAT_PROVIDERS}
            onChange={(s) => updateConfig({ chat: s })}
          />
          <ProviderSlotEditor
            role="embedding"
            slot={embeddingSlot}
            providers={EMBEDDING_PROVIDERS}
            onChange={(s) => updateConfig({ embedding: s })}
          />

          {/* ── Request Timeout ─────────────────────────────── */}
          <div className="pt-2 border-t">
            <div className="text-[13px] font-medium tracking-widest text-text-secondary uppercase mb-2">
              ⏱ Request Timeout
            </div>
            <label className="label-caption">Timeout (seconds)</label>
            <div className="mt-1 flex items-center gap-1.5">
              <button
                onClick={() => updateConfig({ request_timeout: Math.max(5, (config?.request_timeout ?? 30) - 5) })}
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
                  updateConfig({ request_timeout: v });
                }}
                className="flex-1 h-9 text-center text-[14px] rounded border bg-surface"
              />
              <button
                onClick={() => updateConfig({ request_timeout: Math.min(120, (config?.request_timeout ?? 30) + 5) })}
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

            {/* Result feedback — one line per slot, so a partial failure is obvious */}
            {testConn.isSuccess && testConn.data && (
              <div className="mt-2 space-y-1.5">
                <SlotFeedback label="Chat model" result={testConn.data.chat} />
                {testConn.data.embedding && (
                  <SlotFeedback label="Embedding model" result={testConn.data.embedding} />
                )}
              </div>
            )}
            {testConn.isError && (
              <div className="mt-2 text-[13px] text-danger">
                ❌ {(testConn.error as Error).message}
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
      <div className="px-4 py-2 text-[13px] text-text-secondary shrink-0">v0.8.0</div>
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
