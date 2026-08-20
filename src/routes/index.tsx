import { createFileRoute, Link } from "@tanstack/react-router";
import {
  FileSpreadsheet,
  FolderOpen,
  GitMerge,
  Download,
  ArrowRight,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/")({
  component: HomePage,
});

const STEPS = [
  {
    icon: FileSpreadsheet,
    step: "Step 1",
    title: "Upload Codebook",
    desc: "Set the target variable list",
    to: "/upload-codebook" as const,
  },
  {
    icon: FolderOpen,
    step: "Step 2",
    title: "Upload Studies",
    desc: "Add the datasets to be mapped",
    to: "/upload-studies" as const,
  },
  {
    icon: GitMerge,
    step: "Step 3",
    title: "Map Studies",
    desc: "Review AI-suggested mappings",
    to: "/map-studies" as const,
  },
  {
    icon: Download,
    step: "Step 4",
    title: "Download Results",
    desc: "Export the mapped datasets",
    to: "/download-results" as const,
  },
];

function HomePage() {
  return (
    <div className="max-w-[1200px]">
      <PageHeader title="About This Tool" />

      {/* Welcome — fully visible, generously sized, nothing hidden behind a click.
          Spans the same width as the card grid below and justified, so the
          block reads as one aligned unit with it rather than a narrower column. */}
      <div className="text-justify">
        <p className="text-[18px] leading-relaxed text-text-primary">
          The Metadata Harmonisation Tool helps researchers map variables from
          multiple study datasets onto a single canonical codebook — so data
          from different studies can be pooled and compared side by side.
        </p>
        <p className="text-[18px] leading-relaxed text-text-primary mt-4">
          It's part of the eLwazi Open Data Science Platform's data ecosystem,
          built for researchers working with African health study data who
          need their variables harmonised to a shared standard.
        </p>
      </div>

      {/* Getting started — substantial, equal-height cards that fill the width
          properly. These are the entry point, ordered top-to-bottom by step. */}
      <div className="mt-10">
        <h2 className="text-[17px] font-semibold text-text-primary mb-4">Getting started</h2>
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          {STEPS.map(({ icon: Icon, step, title, desc, to }) => (
            <Link
              key={title}
              to={to}
              className="bg-surface border rounded-lg p-6 shadow-sm hover:border-primary hover:shadow-md transition-all flex flex-col"
            >
              <div className="size-11 rounded-md bg-primary-light text-primary flex items-center justify-center">
                <Icon className="size-6" />
              </div>
              <div className="mt-4 text-[13px] font-medium tracking-wide text-text-secondary uppercase">
                {step}
              </div>
              <div className="mt-0.5 font-semibold text-[18px]">{title}</div>
              <div className="text-[15px] text-text-secondary mt-1">{desc}</div>
              <div className="mt-4 pt-3 border-t text-[15px] font-medium text-primary flex items-center gap-1">
                Go <ArrowRight className="size-3.5" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
