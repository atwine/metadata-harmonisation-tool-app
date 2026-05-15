import { createFileRoute } from "@tanstack/react-router";
import {
  FileSpreadsheet,
  Table as TableIcon,
  FileText,
  Trash2,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";

export const Route = createFileRoute("/upload-studies")({
  component: UploadStudiesPage,
});

interface StudyCard {
  name: string;
  variables: number;
  status: "Uploaded" | "Initialised" | "Mapping" | "Complete";
  hasExample: boolean;
  hasContext: boolean;
}

const STUDIES: StudyCard[] = [
  {
    name: "cohort_2019",
    variables: 47,
    status: "Initialised",
    hasExample: true,
    hasContext: true,
  },
  {
    name: "cohort_2021",
    variables: 52,
    status: "Mapping",
    hasExample: true,
    hasContext: false,
  },
];

function statusChip(status: StudyCard["status"]) {
  const map: Record<StudyCard["status"], string> = {
    Uploaded: "bg-[#EDE8E4] text-text-secondary",
    Initialised: "bg-accent-light text-accent",
    Mapping: "bg-primary-light text-primary",
    Complete: "bg-success-light text-success",
  };
  return (
    <span
      className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${map[status]}`}
    >
      {status}
    </span>
  );
}

function Dropzone({
  icon: Icon,
  label,
  hint,
}: {
  icon: typeof FileSpreadsheet;
  label: string;
  hint?: string;
}) {
  return (
    <div className="border-2 border-dashed rounded-md p-3 h-20 flex items-center gap-3 hover:border-primary transition-colors cursor-pointer bg-background/50">
      <Icon className="size-5 text-text-secondary shrink-0" />
      <div className="leading-tight">
        <div className="text-[13px]">{label}</div>
        {hint && (
          <div className="text-[11px] text-text-secondary">{hint}</div>
        )}
      </div>
    </div>
  );
}

function UploadStudiesPage() {
  return (
    <div>
      <PageHeader
        title="Upload Studies"
        subtitle="Add each study dataset that needs to be mapped to the codebook."
      />

      <div className="grid grid-cols-[400px_1fr] gap-6">
        {/* LEFT: add new study */}
        <div className="bg-surface border rounded-lg p-6 shadow-sm h-fit">
          <h2 className="section-heading mb-4">Add New Study</h2>
          <div className="space-y-3">
            <div>
              <label className="label-caption">Study name</label>
              <input
                placeholder="e.g. cohort_2024"
                className="mt-1 w-full h-9 px-3 rounded-md border bg-surface text-[13px]"
              />
            </div>
            <Dropzone
              icon={FileSpreadsheet}
              label="Drop CSV or click · required"
              hint="Study Variables CSV"
            />
            <Dropzone
              icon={TableIcon}
              label="Example Data CSV"
              hint="optional"
            />
            <Dropzone
              icon={FileText}
              label="Context Document PDF"
              hint="optional · max 50 MB"
            />
            <button className="w-full h-10 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-[14px] font-medium transition-colors">
              Add Study
            </button>
          </div>
        </div>

        {/* RIGHT: study list */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="section-heading">Uploaded Studies</h2>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
              {STUDIES.length}
            </span>
          </div>
          <div className="space-y-3">
            {STUDIES.map((s) => (
              <div
                key={s.name}
                className="bg-surface border rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-[14px] font-mono">
                    {s.name}
                  </div>
                  {statusChip(s.status)}
                </div>
                <div className="text-[12px] text-text-secondary mt-1">
                  {s.variables} variables
                </div>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex gap-2">
                    {s.hasExample && (
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-accent-light text-accent">
                        Example data
                      </span>
                    )}
                    {s.hasContext && (
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
                        Context PDF
                      </span>
                    )}
                  </div>
                  <button
                    aria-label="delete"
                    className="size-8 rounded-md text-danger hover:bg-primary-light flex items-center justify-center"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
