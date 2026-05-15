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

      <div className="bg-surface rounded-lg border border-l-4 border-l-primary p-5 shadow-sm space-y-5">
        <p className="text-[14px] leading-relaxed text-text-primary">
          The Metadata Harmonisation Tool helps researchers map variables from
          multiple study datasets onto a single canonical codebook. This
          enables data pooling and cross-study comparisons across the eLwazi
          data ecosystem.
        </p>

        <div>
          <h2 className="text-[15px] font-semibold text-text-primary mb-3">General work flow</h2>
          <ol className="space-y-4 text-[13px] text-text-primary list-none">
            <li>
              <span className="font-semibold">Step 1 — Upload Target Codebook</span>
              <p className="mt-0.5 text-text-secondary leading-relaxed">
                This platform is built to harmonise incoming datasets to a single set of target variables (codebook).
                An example codebook is included by default. A new codebook can be uploaded under the Upload Codebook tab.
                New codebooks should be in <code className="font-mono text-[12px]">.csv</code> format and contain two columns:{" "}
                <code className="font-mono text-[12px]">variable_name</code> and{" "}
                <code className="font-mono text-[12px]">description</code>.
                It is recommended (but not needed) that these variables be linked to standardised ontologies.
              </p>
            </li>
            <li>
              <span className="font-semibold">Step 2 — Upload Incoming Datasets</span>
              <p className="mt-0.5 text-text-secondary leading-relaxed">
                From here, incoming study data which needs to be mapped to the target codebook can be uploaded.
                The following documents can be uploaded:
              </p>
              <ul className="mt-1.5 ml-4 space-y-1 text-text-secondary list-disc">
                <li>Study Name <span className="text-text-secondary opacity-70">(required)</span></li>
                <li>
                  Variables Table <span className="text-text-secondary opacity-70">(required)</span> — CSV with columns{" "}
                  <code className="font-mono text-[12px]">variable_name</code> and{" "}
                  <code className="font-mono text-[12px]">description</code>
                </li>
                <li>
                  Example Data <span className="text-text-secondary opacity-70">(optional)</span> — CSV whose column headers match the variable names
                </li>
                <li>
                  Contextual Documents <span className="text-text-secondary opacity-70">(optional, PDF)</span> — a study protocol or relevant documentation that helps the AI generate better descriptions
                </li>
              </ul>
            </li>
            <li>
              <span className="font-semibold">Step 3 — Map Datasets to Codebook</span>
              <p className="mt-0.5 text-text-secondary leading-relaxed">
                Once steps 1 &amp; 2 have been completed, a recommendations algorithm will suggest the most likely variable
                mappings for each added dataset. The user will be presented with an interface to select the correct
                mappings from a list of suggested mappings. The actual mapping process remains manual.
              </p>
            </li>
            <li>
              <span className="font-semibold">Step 4 — Download Mapping Results</span>
              <p className="mt-0.5 text-text-secondary leading-relaxed">
                Once the mapping process has been completed, each study that has been fully mapped will be available
                for download as a <code className="font-mono text-[12px]">.csv</code> file. The mapping result is a
                table mapping each dataset variable name to a corresponding codebook variable name.
              </p>
            </li>
          </ol>
        </div>
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
