import { create } from "zustand";
import type { QueryClient } from "@tanstack/react-query";
import { BASE, QUERY_KEYS } from "@/api/client";
import type { AIConfig } from "@/types";

export const DEFAULT_PROMPT =
  "As an AI, you're given the task of translating short variable names from a public health study into the most likely full variable name.";

export interface LogLine {
  text: string;
  type: "info" | "ok" | "running" | "error";
}

export type RunResult = "idle" | "success" | "error";

interface InitialiseState {
  prompt: string;
  setPrompt: (p: string) => void;
  forceRerun: boolean;
  setForceRerun: (v: boolean) => void;
  running: boolean;
  log: LogLine[];
  runResult: RunResult;
  startRun: (config: AIConfig, queryClient: QueryClient) => Promise<void>;
  resetRun: () => void;
}

// The run lives here, not in the Initialise page component: the stream keeps
// being read after the user navigates elsewhere, so the page has to be able
// to show its progress (and refuse a second, overlapping run) when they come
// back. In-memory only — a full page reload still starts fresh.
export const useInitialiseStore = create<InitialiseState>((set, get) => ({
  prompt: DEFAULT_PROMPT,
  setPrompt: (p) => set({ prompt: p }),
  forceRerun: false,
  setForceRerun: (v) => set({ forceRerun: v }),
  running: false,
  log: [],
  runResult: "idle",

  resetRun: () => {
    if (get().running) return;
    set({ log: [], runResult: "idle" });
  },

  startRun: async (config, queryClient) => {
    if (get().running) return;

    const appendLog = (line: LogLine) => set((s) => ({ log: [...s.log, line] }));
    set({ running: true, runResult: "idle", log: [] });
    let sawError = false;
    let sawComplete = false;

    const body = {
      ai_config: config,
      init_prompt: get().prompt,
      force_rerun: get().forceRerun,
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
      set({ running: false, runResult: sawError || !sawComplete ? "error" : "success" });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.initialiseStatus });
    }
  },
}));
