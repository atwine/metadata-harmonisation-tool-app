import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface StepAnswer {
  skipped: boolean;
  answers: Record<string, string | number>;
  answeredAt: string;
}

interface EvalState {
  disclosureAcknowledged: boolean;
  acknowledgeDisclosure: () => void;

  // Keyed by step id (e.g. "upload_codebook") — records whether that step's
  // check-in has already been shown, so a page revisit or reload doesn't
  // re-prompt for the same step.
  stepAnswers: Record<string, StepAnswer>;
  recordStepAnswer: (step: string, answer: StepAnswer) => void;

  questionnaireAnswers: Record<string, string | number> | null;
  questionnaireSkipped: boolean;
  setQuestionnaire: (answers: Record<string, string | number>, skipped: boolean) => void;

  reportSubmitted: boolean;
  markReportSubmitted: () => void;

  reset: () => void;
}

export const useEvalStore = create<EvalState>()(
  persist(
    (set) => ({
      disclosureAcknowledged: false,
      acknowledgeDisclosure: () => set({ disclosureAcknowledged: true }),

      stepAnswers: {},
      recordStepAnswer: (step, answer) =>
        set((s) => ({ stepAnswers: { ...s.stepAnswers, [step]: answer } })),

      questionnaireAnswers: null,
      questionnaireSkipped: false,
      setQuestionnaire: (answers, skipped) =>
        set({ questionnaireAnswers: answers, questionnaireSkipped: skipped }),

      reportSubmitted: false,
      markReportSubmitted: () => set({ reportSubmitted: true }),

      reset: () =>
        set({
          disclosureAcknowledged: false,
          stepAnswers: {},
          questionnaireAnswers: null,
          questionnaireSkipped: false,
          reportSubmitted: false,
        }),
    }),
    { name: "mht-eval-session" },
  ),
);
