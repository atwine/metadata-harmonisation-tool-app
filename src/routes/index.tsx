import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { PageHeader, WORKFLOW_STEPS } from "@/components/Sidebar";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <div className="max-w-[1200px]">
      <PageHeader title="About This Tool" />

      {/* Welcome — fully visible, generously sized, nothing hidden behind a click.
          Spans the same width as the card grid below and justified, so the
          block reads as one aligned unit with it rather than a narrower column. */}
      <div className="text-justify">
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
      <div className="mt-10">
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
