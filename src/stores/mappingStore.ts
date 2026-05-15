import { create } from "zustand";
import type { VariableDraft } from "@/types";

interface MappingState {
  drafts: Record<string, VariableDraft>;
  setDraft: (key: string, d: VariableDraft) => void;
  clearDraft: (key: string) => void;
}

export const useMappingStore = create<MappingState>((set) => ({
  drafts: {},
  setDraft: (key, d) => set((st) => ({ drafts: { ...st.drafts, [key]: d } })),
  clearDraft: (key) =>
    set((st) => {
      const { [key]: _, ...rest } = st.drafts;
      return { drafts: rest };
    }),
}));
