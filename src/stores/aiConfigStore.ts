import { create } from "zustand";
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
    provider: "ollama",
    chat_model: "llama3.1:8b",
    embedding_model: "nomic-embed-text",
    base_url: "http://localhost:11434",
    request_timeout: 30,
  },
  setConfig: (c) => set({ config: c }),
  connectionStatus: "unconfigured",
  setConnectionStatus: (s) => set({ connectionStatus: s }),
}));
