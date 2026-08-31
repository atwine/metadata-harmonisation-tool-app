import { Joyride, type EventData, type Step } from "react-joyride";
import { HelpCircle } from "lucide-react";

/** Themed react-joyride instance — matches the app's terracotta/cream palette
 * instead of Joyride's default black/white. */
export function ProductTour({
  steps,
  run,
  onEvent,
}: {
  steps: Step[];
  run: boolean;
  onEvent: (data: EventData) => void;
}) {
  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      scrollToFirstStep
      onEvent={onEvent}
      locale={{ back: "Back", close: "Close", last: "Done", next: "Next", skip: "Skip tour" }}
      options={{
        buttons: ["back", "skip", "primary"],
        showProgress: true,
        skipBeacon: true,
        // Without this, clicking anywhere on the dimmed backdrop silently
        // advances to the next step (react-joyride's default) instead of
        // doing nothing — easy to trigger by accident since the overlay
        // covers the whole viewport, and the user has no idea they just
        // skipped a step's content.
        overlayClickAction: false,
        primaryColor: "var(--primary)",
        textColor: "var(--text-primary)",
        backgroundColor: "var(--surface)",
        arrowColor: "var(--surface)",
        overlayColor: "rgba(45, 45, 45, 0.5)",
        zIndex: 10000,
      }}
      styles={{
        tooltip: { borderRadius: 8, fontSize: 14 },
        tooltipTitle: { fontWeight: 600 },
        buttonPrimary: { backgroundColor: "var(--primary)", borderRadius: 6, fontSize: 14 },
        buttonBack: { color: "var(--text-secondary)", fontSize: 14 },
        buttonSkip: { color: "var(--text-secondary)", fontSize: 14 },
      }}
    />
  );
}

/** Small "Take a tour" replay trigger — pages that own a useProductTour()
 * pass its `start` here so a first-time tour can always be replayed later. */
export function TourReplayButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-primary transition-colors"
    >
      <HelpCircle className="size-4" />
      Take a tour
    </button>
  );
}
