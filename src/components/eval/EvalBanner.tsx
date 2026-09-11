import { FlaskConical } from "lucide-react";
import { isEvalBuild } from "@/lib/evalBuild";

/** Fixed top bar shown only in the testing build, so nobody can mistake it
 * for the production tool — even if they got here via the wrong link. */
export function EvalBanner() {
  if (!isEvalBuild()) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[9999] h-9 bg-accent text-accent-foreground flex items-center justify-center gap-2 text-sm font-medium">
      <FlaskConical className="size-4" />
      TESTING BUILD — for evaluation only, not for real study data
    </div>
  );
}
