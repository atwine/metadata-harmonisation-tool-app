import { create } from "zustand";

interface WizardState {
  currentStudy: string | null;
  setCurrentStudy: (s: string | null) => void;
  relationalModeEnabled: boolean;
  toggleRelationalMode: () => void;
  operatorName: string;
  setOperatorName: (n: string) => void;
  // Off by default (issue #18) — AfPO population/ethnicity mapping is an
  // opt-in pathway, not something every study wants forced on it.
  afpoMappingEnabled: boolean;
  toggleAfpoMapping: () => void;
}

export const useWizardStore = create<WizardState>((set) => ({
  currentStudy: "cohort_2019",
  setCurrentStudy: (s) => set({ currentStudy: s }),
  relationalModeEnabled: true,
  toggleRelationalMode: () => set((st) => ({ relationalModeEnabled: !st.relationalModeEnabled })),
  operatorName: "",
  setOperatorName: (n) => set({ operatorName: n }),
  afpoMappingEnabled: false,
  toggleAfpoMapping: () => set((st) => ({ afpoMappingEnabled: !st.afpoMappingEnabled })),
}));
