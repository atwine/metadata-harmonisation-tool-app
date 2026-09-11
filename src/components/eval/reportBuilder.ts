import type { StepAnswer } from "@/stores/evalStore";
import { CHECK_IN_QUESTIONS, STEP_TITLES } from "./checkInQuestions";
import { SUS_STATEMENTS, OPEN_ENDED, BACKGROUND, computeSusScore } from "./questionnaireContent";

/** Turns one step's recorded answer into a Markdown block using the same
 * question wording shown in the popup, so the GitHub issue reads like a
 * transcript rather than a dump of ids and raw values. */
function formatStepSection(step: string, answer: StepAnswer): string {
  const title = STEP_TITLES[step] ?? step;
  if (answer.skipped) {
    return `### ${title}\n_Skipped by the participant._`;
  }

  const questions = CHECK_IN_QUESTIONS[step] ?? [];
  const lines = questions.map((q) => {
    const value = answer.answers[q.id];
    if (value === undefined) return null;
    const note = answer.answers[`${q.id}_note`];
    const noteSuffix = note ? ` — "${note}"` : "";
    return `- **${q.label}** ${value}${noteSuffix}`;
  }).filter(Boolean);

  return `### ${title}\n${lines.join("\n") || "_No answers recorded._"}`;
}

/** The final questionnaire's flat answer record (keys like sus_0, open_3,
 * background_role — see eval-questionnaire.tsx) formatted back into a
 * readable block, with the computed SUS score up top. */
function formatQuestionnaireSection(
  answers: Record<string, string | number> | null,
  skipped: boolean,
): string {
  if (skipped || !answers) {
    return "### Evaluation Report (questionnaire)\n_Skipped by the participant._";
  }

  const susAnswers: Record<number, number> = {};
  SUS_STATEMENTS.forEach((_, i) => {
    const v = answers[`sus_${i}`];
    if (typeof v === "number") susAnswers[i] = v;
  });
  const susScore = computeSusScore(susAnswers);

  const lines: string[] = ["### Evaluation Report (questionnaire)"];
  lines.push(
    susScore !== null
      ? `**SUS score: ${susScore.toFixed(1)} / 100**`
      : "_SUS score not computed — not every statement was answered._",
  );

  lines.push("", "**Part A — quick reactions**");
  SUS_STATEMENTS.forEach((statement, i) => {
    const v = answers[`sus_${i}`];
    if (v !== undefined) lines.push(`- ${statement} → ${v}/5`);
  });

  lines.push("", "**Part B — in their own words**");
  OPEN_ENDED.forEach((q, i) => {
    const v = answers[`open_${i}`];
    if (v) lines.push(`- **${q}**\n  ${v}`);
  });

  lines.push("", "**Part C — background**");
  BACKGROUND.forEach((q) => {
    const v = answers[`background_${q.id}`];
    if (v) lines.push(`- **${q.label}** ${v}`);
  });

  if (answers.other_comments) {
    lines.push("", "**Part D — anything else**", String(answers.other_comments));
  }

  return lines.join("\n");
}

/** Builds the {sections_markdown, has_skips} payload the backend needs to
 * assemble the full GitHub issue body (see backend/core/eval_report_builder.py). */
export function buildReportSections(
  stepAnswers: Record<string, StepAnswer>,
  questionnaireAnswers: Record<string, string | number> | null,
  questionnaireSkipped: boolean,
): { sections_markdown: string[]; has_skips: boolean } {
  const stepOrder = ["install", "upload_codebook", "upload_study", "initialise", "map_studies", "map_studies_afpo", "download_results"];

  const sections = stepOrder
    .filter((step) => stepAnswers[step])
    .map((step) => formatStepSection(step, stepAnswers[step]));

  sections.push(formatQuestionnaireSection(questionnaireAnswers, questionnaireSkipped));

  const has_skips =
    Object.values(stepAnswers).some((a) => a.skipped) || questionnaireSkipped;

  return { sections_markdown: sections, has_skips };
}
