import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";

/** Known low/high label pairs get a proper word for every point on the
 * scale, not just the two ends — picking 1 vs 5 shouldn't require doing
 * mental math from only the edge labels. Keyed by highLabel since that's
 * unique per scale used in this app. Unrecognised pairs fall back to
 * showing just the edges + "Neutral" in the middle. */
const SCALE_WORDS: Record<string, string[]> = {
  "Very easy": ["Very difficult", "Difficult", "Neutral", "Easy", "Very easy"],
  "Very useful": ["Not useful", "Slightly useful", "Moderately useful", "Useful", "Very useful"],
  "Strongly Agree": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
};

function wordsFor(lowLabel: string, highLabel: string): string[] {
  return SCALE_WORDS[highLabel] ?? [lowLabel, "", "Neutral", "", highLabel];
}

/** A 1-5 scale where hovering (or focusing, for keyboard/touch users) a
 * number shows what that point actually means — added after a participant
 * misread a scale's direction from the edge labels alone and picked the
 * opposite of what they meant. */
export function ScaleRow({
  value,
  onChange,
  lowLabel,
  highLabel,
}: {
  value?: number;
  onChange: (n: number) => void;
  lowLabel: string;
  highLabel: string;
}) {
  const words = wordsFor(lowLabel, highLabel);

  return (
    <TooltipProvider delayDuration={150}>
      <div>
        <div className="flex gap-3 shrink-0">
          {[1, 2, 3, 4, 5].map((n) => (
            <Tooltip key={n}>
              <TooltipTrigger asChild>
                <button
                  onClick={() => onChange(n)}
                  className={`size-10 rounded-md border text-base font-medium transition-colors ${
                    value === n
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-surface hover:bg-accent-light"
                  }`}
                >
                  {n}
                </button>
              </TooltipTrigger>
              {words[n - 1] && <TooltipContent>{words[n - 1]}</TooltipContent>}
            </Tooltip>
          ))}
        </div>
        <div className="flex justify-between text-sm text-text-secondary mt-1.5">
          <span>{lowLabel}</span>
          <span>{highLabel}</span>
        </div>
      </div>
    </TooltipProvider>
  );
}
