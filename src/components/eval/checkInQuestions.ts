import type { CheckInQuestion } from "./StepCheckIn";

/** Human-readable step titles, shared between the check-in popups and the
 * report builder (so the GitHub issue body uses the same names). */
export const STEP_TITLES: Record<string, string> = {
  install: "Installation",
  upload_codebook: "Upload Target Codebook",
  upload_study: "Upload Study Data",
  initialise: "Initialise",
  map_studies: "Map Studies",
  map_studies_afpo: "Map Studies — ethnicity/population lookup",
  download_results: "Download Results",
};

/** The route each step's check-in lives on — used to send a participant
 * back to a step they skipped past before they can submit the final
 * report. */
export const STEP_ROUTES: Record<string, string> = {
  install: "/",
  upload_codebook: "/upload-codebook",
  upload_study: "/upload-studies",
  initialise: "/initialise",
  map_studies: "/map-studies",
  map_studies_afpo: "/map-studies",
  download_results: "/download-results",
};

/** Every step whose check-in must be resolved (answered or skipped) before
 * the final report can be submitted. map_studies_afpo is excluded — it's
 * only relevant when the AfPO toggle was on, checked separately. */
export const REQUIRED_STEPS = [
  "install",
  "upload_codebook",
  "upload_study",
  "initialise",
  "map_studies",
  "download_results",
];

/** One question set per workflow step. Shared here so wording stays
 * consistent and each route file only needs to reference a step id. */
export const CHECK_IN_QUESTIONS: Record<string, CheckInQuestion[]> = {
  install: [
    {
      id: "started_ok",
      type: "yes_no",
      label: "Did the app start successfully after running the pull/run command?",
      followUpLabel: "What happened instead?",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was getting it running?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
    {
      id: "errors",
      type: "yes_no",
      label: "Did you hit any errors?",
      followUpLabel: "Paste the exact error text",
      followUpOn: "Yes",
    },
    {
      id: "outside_help",
      type: "yes_no",
      label: "Did you need to search online or ask someone for help beyond our instructions?",
      followUpLabel: "What for?",
      followUpOn: "Yes",
    },
    {
      id: "startup_minutes",
      type: "text",
      label: 'Roughly how long from running the command to seeing the homepage? (e.g. "2 minutes")',
    },
  ],
  upload_codebook: [
    {
      id: "clarity",
      type: "yes_no",
      label: "Was it clear what file to upload here?",
      followUpLabel: "What was unclear?",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was this step?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
  ],
  upload_study: [
    {
      id: "clarity",
      type: "yes_no",
      label:
        "Was it clear what each of the three uploads (study variables, example data, context PDF) was for?",
      followUpLabel: "What was unclear?",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was this step?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
  ],
  // Shown when the run finished successfully — there is nothing to ask about
  // errors, so ask whether they had to tweak anything to get there instead.
  initialise: [
    {
      id: "changes_needed",
      type: "yes_no",
      label:
        "Did you need to change anything to get this working (for example, edit the initialisation prompt)?",
      followUpLabel: "What did you change?",
      followUpOn: "Yes",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was this step?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
  ],
  // Shown instead when the run failed.
  initialise_failed: [
    {
      id: "error_text",
      type: "text",
      label:
        "Processing didn't finish. What went wrong? (paste the error message shown on the page, or describe what you saw)",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was this step?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
  ],
  map_studies: [
    {
      id: "top_share",
      type: "choice",
      label: "Roughly what share of the tool's top suggestions felt right?",
      options: ["None", "Some", "Most", "Nearly all"],
    },
    {
      id: "confidence_match",
      type: "choice",
      label: "Did the confidence labels (Strong/Review/Verify) match your own sense of certainty?",
      options: ["Yes, mostly", "Somewhat", "No"],
    },
    {
      id: "transformation_preview",
      type: "choice",
      label: "If you tried a transformation (e.g. unit conversion), did the preview make sense?",
      options: ["Yes", "No", "Didn't try"],
    },
  ],
  map_studies_afpo: [
    { id: "afpo_useful", type: "yes_no", label: "Was the ethnicity/population lookup useful?" },
  ],
  download_results: [
    {
      id: "complete",
      type: "yes_no",
      label: "Did the downloaded file look complete and correct?",
      followUpLabel: "Describe what looked wrong",
    },
    {
      id: "ease",
      type: "scale",
      label: "How easy was this step?",
      lowLabel: "Very difficult",
      highLabel: "Very easy",
    },
  ],
};

/** Every question a step can ask across its variants (initialise has a
 * success set and a `_failed` set), de-duplicated by id — so the report
 * builder finds the wording for whichever variant the participant saw. */
export function questionsForStep(step: string): CheckInQuestion[] {
  const all = [
    ...(CHECK_IN_QUESTIONS[step] ?? []),
    ...(CHECK_IN_QUESTIONS[`${step}_failed`] ?? []),
  ];
  return all.filter((q, i) => all.findIndex((o) => o.id === q.id) === i);
}
