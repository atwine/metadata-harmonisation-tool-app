import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { FileSpreadsheet, Table as TableIcon, FileText, Trash2, FolderOpen } from "lucide-react";
import type { Step } from "react-joyride";
import { PageHeader } from "@/components/Sidebar";
import { ProductTour, TourReplayButton } from "@/components/ProductTour";
import { useProductTour } from "@/hooks/useProductTour";
import { useStudies, useUploadStudy, useDeleteStudy } from "@/api/client";
import type { Study } from "@/types";
import { StepCheckIn } from "@/components/eval/StepCheckIn";
import { CHECK_IN_QUESTIONS } from "@/components/eval/checkInQuestions";
import { useForceCheckIn } from "@/components/eval/useForceCheckIn";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";

export const Route = createFileRoute("/upload-studies")({
  component: UploadStudiesPage,
});

const TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="study-name"]',
    title: "Name the study",
    content:
      "Give this study a short, unique name — you'll use it to identify it everywhere else in the app.",
    placement: "right",
  },
  {
    target: '[data-tour="variables-dropzone"]',
    title: "Study Variables CSV",
    content: "The only required file — the list of variable names found in this study's dataset.",
    placement: "right",
  },
  {
    target: '[data-tour="add-study-btn"]',
    title: "Add it",
    content: "Once you've filled these in, click here to add the study.",
    placement: "top",
  },
  {
    target: '[data-tour="uploaded-studies"]',
    title: "Your studies",
    content:
      "Every study you've added shows up here, with its status and how many variables it has. You can delete one anytime with the trash icon — there's a confirmation step, so it's hard to trigger by accident.",
    placement: "left",
  },
];

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
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${map[status]}`}>
      {label[status]}
    </span>
  );
}

interface DropzoneProps {
  icon: typeof FileSpreadsheet;
  label: string;
  hint?: string;
  /** Shown on hover — a fuller explanation for someone new to the tool who
   * isn't sure what belongs in this drop zone. */
  tooltip: string;
  file?: File | null;
  onFile: (f: File) => void;
  accept: string;
}

function Dropzone({ icon: Icon, label, hint, tooltip, file, onFile, accept }: DropzoneProps) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
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
                  <div className="text-base font-medium text-primary">{file.name}</div>
                  <div className="text-xs text-text-secondary">{(file.size / 1024).toFixed(0)} KB</div>
                </>
              ) : (
                <>
                  <div className="text-base">{label}</div>
                  {hint && <div className="text-xs text-text-secondary">{hint}</div>}
                </>
              )}
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-[260px]">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function UploadStudiesPage() {
  const [studyName, setStudyName] = useState("");
  const [variablesFile, setVariablesFile] = useState<File | null>(null);
  const [exampleFile, setExampleFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const tour = useProductTour("upload-studies");
  const forceCheckIn = useForceCheckIn("upload_study");

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
      },
    );
  };

  const handleDelete = (name: string) => {
    deleteStudy.mutate(name);
  };

  return (
    <div>
      <ProductTour steps={TOUR_STEPS} run={tour.run} onEvent={tour.handleEvent} />
      <StepCheckIn
        step="upload_study"
        title="Quick check-in: Upload Study Data"
        questions={CHECK_IN_QUESTIONS.upload_study}
        trigger={upload.isSuccess || forceCheckIn}
      />

      <div className="flex items-center justify-between gap-4">
        <PageHeader
          title="Upload Studies"
          subtitle="Add each study dataset that needs to be mapped to the codebook."
        />
        <TourReplayButton onClick={tour.start} />
      </div>

      <div className="grid grid-cols-[400px_1fr] gap-6">
        {/* LEFT: add new study */}
        <div className="bg-surface border rounded-lg p-6 shadow-sm h-fit">
          <h2 className="section-heading mb-4">Add New Study</h2>
          <div className="space-y-3">
            <div data-tour="study-name">
              <label className="label-caption">Study name</label>
              <input
                value={studyName}
                onChange={(e) => setStudyName(e.target.value)}
                placeholder="e.g. cohort_2024"
                className="mt-1 w-full h-9 px-3 rounded-md border bg-surface text-base"
              />
            </div>
            <div data-tour="variables-dropzone">
              <Dropzone
                icon={FileSpreadsheet}
                label="Drop CSV or click · required"
                hint="Study Variables CSV · max 10 MB"
                tooltip="Drop a CSV with this study's variable names here (one per row) — the list of columns/fields that exist in this study's dataset. Click to browse your computer instead of dragging. Required — max 10 MB."
                file={variablesFile}
                onFile={setVariablesFile}
                accept=".csv"
              />
            </div>
            <Dropzone
              icon={TableIcon}
              label="Example Data CSV"
              hint="optional · max 100 MB"
              tooltip="Drop a CSV with a few real (or realistic) example rows of this study's actual data — helps the AI understand what real values for each variable look like, for a better match. Click to browse instead of dragging. Optional — max 100 MB."
              file={exampleFile}
              onFile={setExampleFile}
              accept=".csv"
            />
            <Dropzone
              icon={FileText}
              label="Context Document PDF"
              hint="optional · max 50 MB"
              tooltip="Drop a PDF with background info about the study — a protocol, data dictionary, or codebook — used to help generate better variable descriptions automatically. Click to browse instead of dragging. Optional — max 50 MB."
              file={pdfFile}
              onFile={setPdfFile}
              accept=".pdf"
            />
            {upload.isError && (
              <div className="p-2 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
                {(upload.error as Error).message}
              </div>
            )}
            <button
              data-tour="add-study-btn"
              onClick={handleAdd}
              disabled={!canSubmit || upload.isPending}
              className="w-full h-10 bg-primary text-primary-foreground hover:bg-primary-hover rounded-md text-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {upload.isPending ? "Uploading…" : "Add Study"}
            </button>
          </div>
        </div>

        {/* RIGHT: study list */}
        <div data-tour="uploaded-studies">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="section-heading">Uploaded Studies</h2>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
              {studies.length}
            </span>
          </div>
          {studies.length === 0 ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {[0, 1].map((i) => (
                <div
                  key={i}
                  className="border-2 border-dashed rounded-lg p-8 min-h-[132px] flex flex-col items-center justify-center gap-2 text-center"
                >
                  <FolderOpen className="size-6 text-text-secondary/40" />
                  {i === 0 && (
                    <p className="text-base text-text-secondary">
                      Studies you add will appear here
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {studies.map((s) => (
                <div key={s.name} className="bg-surface border rounded-lg p-4 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-md font-mono">{s.name}</div>
                    {statusChip(s.status)}
                  </div>
                  <div className="text-sm text-text-secondary mt-1">
                    {s.variable_count} variables
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <div className="flex gap-2">
                      {s.has_example_data && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-accent-light text-accent">
                          Example data
                        </span>
                      )}
                      {s.has_context_pdf && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary-light text-primary">
                          Context PDF
                        </span>
                      )}
                    </div>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <button
                          aria-label="delete"
                          className="size-8 rounded-md text-danger hover:bg-primary-light flex items-center justify-center"
                        >
                          <Trash2 className="size-4" />
                        </button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete "{s.name}"?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This permanently deletes the uploaded files, {s.variable_count} variable
                            {s.variable_count === 1 ? "" : "s"}, and any mapping progress for "
                            {s.name}". This cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => handleDelete(s.name)}
                            className="bg-danger text-white hover:bg-danger/90"
                          >
                            Yes, delete study
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
