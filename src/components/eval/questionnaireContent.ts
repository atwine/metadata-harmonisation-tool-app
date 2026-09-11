/** Shared between the questionnaire page (renders these) and the report
 * builder (labels the answers when formatting the GitHub issue body) — one
 * place for the actual wording. */

export const SUS_STATEMENTS = [
  "I think that I would like to use this tool frequently.",
  "I found the tool unnecessarily complex.",
  "I thought the tool was easy to use.",
  "I think that I would need the support of a technical person to be able to use this tool.",
  "I found the various functions in this tool were well integrated.",
  "I thought there was too much inconsistency in this tool.",
  "I would imagine that most people would learn to use this tool very quickly.",
  "I found the tool very cumbersome to use.",
  "I felt very confident using the tool.",
  "I needed to learn a lot of things before I could get going with this tool.",
];

export const OPEN_ENDED = [
  "What was the most confusing part of the entire process (installation and/or harmonisation)?",
  "Was there a point where you were unsure what to do next? If so, what were you trying to do?",
  "Did the tool's recommendations match your expectations? Were they helpful, or did you feel you were overriding them most of the time?",
  "If you could change one thing about the tool, what would it be?",
  "Would you use this tool for your own harmonisation work? Why or why not?",
  "How does this compare to how you currently harmonise data (if applicable)? Is it faster, slower, easier, harder?",
];

export const BACKGROUND: { id: string; label: string; options?: string[] }[] = [
  { id: "role", label: "What is your role? (e.g., researcher, data manager, statistician)" },
  { id: "experience_years", label: "How many years of experience do you have working with health research data?" },
  {
    id: "harmonisation_experience",
    label: "Have you done data harmonisation before?",
    options: ["Never", "Once or twice", "Regularly"],
  },
  {
    id: "cli_comfort",
    label: "How comfortable are you with command-line tools?",
    options: ["Not at all", "Somewhat", "Very"],
  },
  {
    id: "docker_comfort",
    label: "How comfortable are you with Docker?",
    options: ["Not at all", "Somewhat", "Very"],
  },
];

/** Standard SUS formula: odd (1-indexed) items contribute (rating-1), even
 * items contribute (5-rating), summed and scaled to 0-100. Returns null if
 * fewer than all 10 were answered — a partial score would be misleading. */
export function computeSusScore(susAnswers: Record<number, number>): number | null {
  if (Object.keys(susAnswers).length < SUS_STATEMENTS.length) return null;
  let total = 0;
  for (let i = 0; i < SUS_STATEMENTS.length; i++) {
    const rating = susAnswers[i];
    if (rating == null) return null;
    total += i % 2 === 0 ? rating - 1 : 5 - rating;
  }
  return total * 2.5;
}
