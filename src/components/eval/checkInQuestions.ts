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

/** One question set per workflow step. Shared here so wording stays
 * consistent and each route file only needs to reference a step id. */
export const CHECK_IN_QUESTIONS: Record<string, CheckInQuestion[]> = {
  install: [
    { id: "started_ok", type: "yes_no", label: "Did the app start successfully after running the pull/run command?", followUpLabel: "What happened instead?" },
    { id: "ease", type: "scale", label: "How easy was getting it running?", lowLabel: "Very difficult", highLabel: "Very easy" },
    { id: "errors", type: "yes_no", label: "Did you hit any errors?", followUpLabel: "Paste the exact error text" },
    { id: "outside_help", type: "yes_no", label: "Did you need to search online or ask someone for help beyond our instructions?", followUpLabel: "What for?" },
    { id: "startup_minutes", type: "text", label: "Roughly how long from running the command to seeing the homepage? (e.g. \"2 minutes\")" },
  ],
  upload_codebook: [
    { id: "clarity", type: "yes_no", label: "Was it clear what file to upload here?", followUpLabel: "What was unclear?" },
    { id: "ease", type: "scale", label: "How easy was this step?", lowLabel: "Very difficult", highLabel: "Very easy" },
  ],
  upload_study: [
    { id: "clarity", type: "yes_no", label: "Was it clear what each of the three uploads (study variables, example data, context PDF) was for?", followUpLabel: "What was unclear?" },
    { id: "ease", type: "scale", label: "How easy was this step?", lowLabel: "Very difficult", highLabel: "Very easy" },
  ],
  initialise: [
    { id: "no_errors", type: "yes_no", label: "Did processing finish without errors?", followUpLabel: "Paste the error message" },
    { id: "ease", type: "scale", label: "How easy was this step?", lowLabel: "Very difficult", highLabel: "Very easy" },
  ],
  map_studies: [
    { id: "top_share", type: "choice", label: "Roughly what share of the tool's top suggestions felt right?", options: ["None", "Some", "Most", "Nearly all"] },
    { id: "confidence_match", type: "choice", label: "Did the confidence labels (Strong/Review/Verify) match your own sense of certainty?", options: ["Yes, mostly", "Somewhat", "No"] },
    { id: "transformation_preview", type: "choice", label: "If you tried a transformation (e.g. unit conversion), did the preview make sense?", options: ["Yes", "No", "Didn't try"] },
    { id: "usefulness", type: "scale", label: "How useful were the recommendations overall?", lowLabel: "Not useful", highLabel: "Very useful" },
  ],
  map_studies_afpo: [
    { id: "afpo_useful", type: "yes_no", label: "Was the ethnicity/population lookup useful?" },
  ],
  download_results: [
    { id: "complete", type: "yes_no", label: "Did the downloaded file look complete and correct?", followUpLabel: "Describe what looked wrong" },
    { id: "ease", type: "scale", label: "How easy was this step?", lowLabel: "Very difficult", highLabel: "Very easy" },
  ],
};
