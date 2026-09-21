import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBEDDING_MODEL } from "@/lib/ollamaDefaults";
import type { AIConfig } from "@/types";

export type ConnectionStatus = "unconfigured" | "checking" | "connected" | "failed";

interface AIConfigState {
  config: AIConfig | null;
  setConfig: (c: AIConfig) => void;
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (s: ConnectionStatus) => void;
  // True while the connection is (or was last seen) working. Persisted so a
  // page reload can quietly re-check it instead of making the user redo it.
  resumeConnection: boolean;
}

const stripKeys = (config: AIConfig | null): AIConfig | null =>
  config && {
    ...config,
    chat: { ...config.chat, api_key: undefined },
    embedding: config.embedding && { ...config.embedding, api_key: undefined },
  };

// Saved in sessionStorage: survives reloads and accidental page switches, and
// is gone once the browser tab is closed. API keys are deliberately never
// saved — providers that need one ask for it again.
export const useAIConfigStore = create<AIConfigState>()(
  persist(
    (set) => ({
      config: {
        chat: {
          provider: "ollama",
          model: OLLAMA_CHAT_MODEL,
          base_url: OLLAMA_BASE_URL,
        },
        embedding: {
          provider: "ollama",
          model: OLLAMA_EMBEDDING_MODEL,
          base_url: OLLAMA_BASE_URL,
        },
        request_timeout: 30,
      },
      setConfig: (c) => set({ config: c }),
      connectionStatus: "unconfigured",
      setConnectionStatus: (s) =>
        set({
          connectionStatus: s,
          resumeConnection: s === "connected" || s === "checking",
        }),
      resumeConnection: false,
    }),
    {
      name: "mht-ai-config",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({ config: stripKeys(s.config), resumeConnection: s.resumeConnection }),
      // Restored from the sidebar after the first render (rather than at
      // module load) so server-rendered and client HTML can't disagree.
      skipHydration: true,
    },
  ),
);
