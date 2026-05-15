import { createFileRoute, Link } from "@tanstack/react-router";
import { FileSpreadsheet, Cpu, GitMerge, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <div className="max-w-5xl">
      <PageHeader title="About This Tool" />

      <div className="bg-surface rounded-lg border border-l-4 border-l-primary p-5 shadow-sm">
        <p className="text-[14px] leading-relaxed text-text-primary">
          The Metadata Harmonisation Tool helps researchers map variables from
          multiple study datasets onto a single canonical codebook. This
          enables data pooling and cross-study comparisons across the eLwazi
          data ecosystem.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-6">
        {[
          {
            icon: FileSpreadsheet,
            title: "Codebook",
            desc: "Upload your target variable list",
          },
          {
            icon: Cpu,
            title: "AI Recommendations",
            desc: "Semantic matching via embeddings",
          },
          {
            icon: GitMerge,
            title: "Manual Review",
            desc: "Operator-confirmed mappings with audit trail",
          },
        ].map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="bg-surface border rounded-lg p-5 shadow-sm"
          >
            <div className="size-9 rounded-md bg-primary-light text-primary flex items-center justify-center">
              <Icon className="size-5" />
            </div>
            <div className="mt-3 font-semibold text-[14px]">{title}</div>
            <div className="text-[13px] text-text-secondary mt-1">{desc}</div>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <Link
          to="/upload-codebook"
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary-hover px-5 h-10 rounded-md text-[14px] font-medium transition-colors"
        >
          Get Started <ArrowRight className="size-4" />
        </Link>
      </div>
    </div>
  );
}
