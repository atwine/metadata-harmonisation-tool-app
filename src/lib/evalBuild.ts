/** True only in the testing build sent out for evaluation — set via
 * VITE_EVAL_BUILD in the eval Docker image's env. False (and every eval-only
 * UI piece hidden) in the normal build everyone else runs. */
export function isEvalBuild(): boolean {
  return (import.meta.env.VITE_EVAL_BUILD as string | undefined) === "true";
}
