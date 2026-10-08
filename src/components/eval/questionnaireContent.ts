/** Shared between the questionnaire page (renders these) and the report
 * builder (labels the answers when formatting the GitHub issue body) — one
 * place for the actual wording.
 *
 * Part A and Part B follow the shorter set suggested in the team review
 * (replacing the 10-statement System Usability Scale and the six longer open
 * questions). */

export interface RatingQuestion {
  label: string;
  lowLabel: string;
  highLabel: string;
}

export const RATING_QUESTIONS: RatingQuestion[] = [
  { label: "How easy was the software to use?", lowLabel: "Very difficult", highLabel: "Very easy" },
  {
    label: "How easy was it to learn how to use the software?",
    lowLabel: "Very difficult",
    highLabel: "Very easy",
  },
  {
    label: "How easy was it to find the information or features you needed?",
    lowLabel: "Very difficult",
    highLabel: "Very easy",
  },
  {
    label: "How well did the software support the task(s) you wanted to accomplish?",
    lowLabel: "Not at all well",
    highLabel: "Extremely well",
  },
  {
    label: "Overall, how would you rate your experience using the software?",
    lowLabel: "Very poor",
    highLabel: "Excellent",
  },
];

export const OPEN_ENDED = [
  "What did you find most useful about the software?",
  "Was there any content or information that was unclear, missing, or difficult to understand?",
  "Were there any features or functionality that you felt were missing or could be improved?",
  "Were there any aspects of the software's structure, layout, or navigation that you found confusing or difficult to use?",
  "Do you have any additional recommendations for consideration to improve the usefulness and usability of the tool?",
];

export const BACKGROUND: { id: string; label: string; options?: string[] }[] = [
  { id: "role", label: "What is your role? (e.g., researcher, data manager, statistician)" },
  {
    id: "harmonisation_experience",
    label: "Have you done data harmonisation before?",
    options: ["Never", "Once or twice", "Regularly"],
  },
  {
    id: "cli_frequency",
    label: "How often did you use the command line while using the tool?",
    options: ["Never", "A few times", "Often"],
  },
  {
    id: "ai_comfort",
    label: "How comfortable are you with using AI tools?",
    options: ["Not at all", "Somewhat", "Very"],
  },
  {
    id: "docker_comfort",
    label: "How comfortable are you with Docker?",
    options: ["Not at all", "Somewhat", "Very"],
  },
];
