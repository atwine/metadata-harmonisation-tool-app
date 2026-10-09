import type { ReactNode } from "react";
import { Info } from "lucide-react";
import { isEvalBuild } from "@/lib/evalBuild";

/** Where the sample files live. They are in the project's example_data folder, not inside
 * the app, so a tester with no data of their own needs a pointer. Testing build only. */
const SAMPLE_DATA_URL =
  "https://github.com/atwine/metadata-harmonisation-tool-app/tree/eval/instrumentation-build/example_data";

export function SampleDataNote({ children }: { children: ReactNode }) {
  if (!isEvalBuild()) return null;
  return (
    <div className="mb-5 flex items-start gap-3 px-4 py-3 rounded-md bg-accent-light border border-accent/30 text-base">
      <Info className="size-4 text-accent mt-0.5 shrink-0" />
      <span className="text-text-primary">
        {children}{" "}
        <a
          href={SAMPLE_DATA_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline"
        >
          Get the sample files
        </a>
      </span>
    </div>
  );
}
