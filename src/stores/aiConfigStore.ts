import { create } from "zustand";
import { OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBEDDING_MODEL } from "@/lib/ollamaDefaults";
import type { AIConfig } from "@/types";

type ConnectionStatus = "unconfigured" | "connected" | "failed";

interface AIConfigState {
  config: AIConfig | null;
  setConfig: (c: AIConfig) => void;
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (s: ConnectionStatus) => void;
}

export const useAIConfigStore = create<AIConfigState>((set) => ({
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
  setConnectionStatus: (s) => set({ connectionStatus: s }),
}));
