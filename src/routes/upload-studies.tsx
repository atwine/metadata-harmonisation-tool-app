import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import {
  FileSpreadsheet,
  Table as TableIcon,
  FileText,
  Trash2,
} from "lucide-react";
import { PageHeader } from "@/components/Sidebar";
import { useStudies, useUploadStudy, useDeleteStudy } from "@/api/client";
import type { Study } from "@/types";

export const Route = createFileRoute("/upload-studies")({
  component: UploadStudiesPage,
});

function statusChip(status: Study["status"]) {
  const map: Record<Study["status"], string> = {
    uploaded: "bg-[#EDE8E4] text-text-secondary",
    initialised: "bg-accent-light text-accent",
    mapping: "bg-primary-light text-primary",
    complete: "bg-success-light text-success",
  };
  const label: Record<Study["status"], string> = {
    uploaded: "Uploaded",
    initialised: "Initialised",
    mapping: "Mapping",
    complete: "Complete",
  };
  return (
    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${map[status]}`}>
      {label[status]}
    </span>
  );
}

interface DropzoneProps {
  icon: typeof FileSpreadsheet;
  label: string;
  hint?: string;
  file?: File | null;
  onFile: (f: File) => void;
  accept: string;
}

function Dropzone({ icon: Icon, label, hint, file, onFile, accept }: DropzoneProps) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div
      className="border-2 border-dashed rounded-md p-3 h-20 flex items-center gap-3 hover:border-primary transition-colors cursor-pointer bg-background/50"
      onClick={() => ref.current?.click()}
      onDrop={(e) => {
        e.preventDefault();
        const f = e.dataTransfer.files[0];
        if (f) onFile(f);
      }}
      onDragOver={(e) => e.preventDefault()}
    >
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <Icon className="size-5 text-text-secondary shrink-0" />
      <div className="leading-tight">
        {file ? (
          <>
            <div className="text-[13px] font-medium text-primary">{file.name}</div>
            <div className="text-[11px] text-text-secondary">
              {(file.size / 1024).toFixed(0)} KB
            </div>
          </>
        ) : (
          <>
            <div className="text-[13px]">{label}</div>
            {hint && <div className="text-[11px] text-text-secondary">{hint}</div>}
          </>
        )}
      </div>
    </div>
  );
}

function UploadStudiesPage() {
  const [studyName, setStudyName] = useState("");
  const [variablesFile, setVariablesFile] = useState<File | null>(null);
  const [exampleFile, setExampleFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const { data: studies = [] } = useStudies();
  const upload = useUploadStudy();
  const deleteStudy = useDeleteStudy();

  const canSubmit = studyName.trim() && variablesFile;

  const handleAdd = () => {
    if (!canSubmit) return;
    upload.mutate(
      {
        name: studyName.trim(),
        variables: variablesFile!,
        exampleData: exampleFile ?? undefined,
        contextPdf: pdfFile ?? undefined,
      },
      {
        onSuccess: () => {
          setStudyName("");
          setVariablesFile(null);
          setExampleFile(null);
          setPdfFile(null);
        },
      }
    );
  };

  const handleDelete = (name: string) => {
    setDeleteTarget(null);
    deleteStudy.mutate(name);
  };

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
                value={studyName}
                onChange={(e) => setStudyName(e.target.value)}
                placeholder="e.g. cohort_2024"
                className="mt-1 w-full h-9 px-3 rounded-md border bg-surface text-[13px]"
              />
            </div>
            <Dropzone
              icon={FileSpreadsheet}
              label="Drop CSV or click · required"
              hint="Study Variables CSV"
              file={variablesFile}
              onFile={setVariablesFile}
              accept=".csv"
            />
            <Dropzone
              icon={TableIcon}
              label="Example Data CSV"
              hint="optional"
              file={exampleFile}
              onFile={setExampleFile}
              accept=".csv"
            />
            <Dropzone
              icon={FileText}
              label="Context Document PDF"
              hint="optional · max 50 MB"
              file={pdfFile}
              onFile={setPdfFile}
              accept=".pdf"
            />
            {upload.isError && (
              <div className="p-2 rounded-md bg-red-50 border border-red-200 text-[12px] text-red-700">
                {(upload.error as Error).message}
              </div>
            )}
            <button
              onClick={handleAdd}
              disabled={!canSubmit || upload.isPending}
              className="w-full h-10 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-[14px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {upload.isPending ? "Uploading…" : "Add Study"}
            </button>
          </div>
        </div>

        {/* RIGHT: study list */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="section-heading">Uploaded Studies</h2>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
              {studies.length}
            </span>
          </div>
          <div className="space-y-3">
            {studies.map((s) => (
              <div key={s.name} className="bg-surface border rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-[14px] font-mono">{s.name}</div>
                  {statusChip(s.status)}
                </div>
                <div className="text-[12px] text-text-secondary mt-1">
                  {s.variable_count} variables
                </div>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex gap-2">
                    {s.has_example_data && (
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-accent-light text-accent">
                        Example data
                      </span>
                    )}
                    {s.has_context_pdf && (
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
                        Context PDF
                      </span>
                    )}
                  </div>
                  {deleteTarget === s.name ? (
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] text-danger">Delete?</span>
                      <button
                        onClick={() => handleDelete(s.name)}
                        className="text-[12px] text-danger font-medium hover:underline"
                      >
                        Yes
                      </button>
                      <button
                        onClick={() => setDeleteTarget(null)}
                        className="text-[12px] text-text-secondary hover:underline"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      aria-label="delete"
                      onClick={() => setDeleteTarget(s.name)}
                      className="size-8 rounded-md text-danger hover:bg-primary-light flex items-center justify-center"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
            {studies.length === 0 && (
              <div className="text-[13px] text-text-secondary text-center py-8">
                No studies uploaded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
