import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import type { Step } from "react-joyride";
import { PageHeader, WORKFLOW_STEPS } from "@/components/Sidebar";
import { ProductTour, TourReplayButton } from "@/components/ProductTour";
import { useProductTour } from "@/hooks/useProductTour";

export const Route = createFileRoute("/")({
  component: HomePage,
});

const TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="welcome"]',
    title: "Welcome",
    content:
      "This tool maps variables from study datasets onto a single canonical codebook, so data from different studies can be pooled and compared. This quick tour points out where everything lives.",
    placement: "bottom",
  },
  {
    target: '[data-tour="workflow-nav"]',
    title: "The 5-step workflow",
    content:
      "Every study goes through these five steps in order, top to bottom: upload a codebook, upload studies, initialise the AI, map variables, then download results.",
    placement: "right",
  },
  {
    target: '[data-tour="ai-config"]',
    title: "AI Configuration",
    content:
      "Set up your AI provider here before running anything — Ollama (local, free), or a hosted option like OpenAI. It's collapsed by default; click to expand it.",
    placement: "right",
  },
  {
    target: '[data-tour="getting-started"]',
    title: "Getting started",
    content: 'Click "Go" on any card to jump straight into that step.',
    placement: "top",
  },
];

function HomePage() {
  const tour = useProductTour("home");

  return (
    <div className="max-w-[1200px]">
      <ProductTour steps={TOUR_STEPS} run={tour.run} onEvent={tour.handleEvent} />

      <div className="flex items-center justify-between gap-4">
        <PageHeader title="About This Tool" />
        <TourReplayButton onClick={tour.start} />
      </div>

      {/* Welcome — fully visible, generously sized, nothing hidden behind a click.
          Spans the same width as the card grid below and justified, so the
          block reads as one aligned unit with it rather than a narrower column. */}
      <div className="text-justify" data-tour="welcome">
        <p className="text-lg leading-relaxed text-text-primary">
          The Metadata Harmonisation Tool helps researchers map variables from multiple study
          datasets onto a single canonical codebook — so data from different studies can be pooled
          and compared side by side.
        </p>
        <p className="text-lg leading-relaxed text-text-primary mt-4">
          It's part of the eLwazi Open Data Science Platform's data ecosystem, built for researchers
          working with African health study data who need their variables harmonised to a shared
          standard.
        </p>
      </div>

      {/* Getting started — substantial, equal-height cards that fill the width
          properly. These are the entry point, ordered top-to-bottom by step.
          Sourced from the same WORKFLOW_STEPS the step strip on every other
          workflow page reads from, so this list and that strip can't drift. */}
      <div className="mt-10" data-tour="getting-started">
        <h2 className="text-lg font-semibold text-text-primary mb-4">Getting started</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-4">
          {WORKFLOW_STEPS.map(({ icon: Icon, title, desc, to }, i) => (
            <Link
              key={title}
              to={to}
              className="bg-surface border rounded-lg p-6 shadow-sm hover:border-primary hover:shadow-md transition-all flex flex-col"
            >
              <div className="size-11 rounded-md bg-primary-light text-primary flex items-center justify-center">
                <Icon className="size-6" />
              </div>
              <div className="mt-4 text-xs font-medium tracking-wide text-text-secondary uppercase">
                Step {i + 1}
              </div>
              <div className="mt-0.5 font-semibold text-lg">{title}</div>
              <div className="text-base text-text-secondary mt-1">{desc}</div>
              <div className="mt-4 pt-3 border-t text-base font-medium text-primary flex items-center gap-1">
                Go <ArrowRight className="size-3.5" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
