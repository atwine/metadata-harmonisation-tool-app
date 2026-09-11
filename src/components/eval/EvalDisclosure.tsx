import { isEvalBuild } from "@/lib/evalBuild";
import { useEvalStore } from "@/stores/evalStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

/** Shown once, before anything else, in the testing build only. Cannot be
 * dismissed via the corner X / escape / outside click — only by clicking
 * "I understand" — so nobody can click past it by accident and later say
 * they were never told. */
export function EvalDisclosure() {
  const acknowledged = useEvalStore((s) => s.disclosureAcknowledged);
  const acknowledge = useEvalStore((s) => s.acknowledgeDisclosure);

  if (!isEvalBuild() || acknowledged) return null;

  return (
    <Dialog open onOpenChange={() => {}}>
      <DialogContent
        className="max-w-lg [&>button]:hidden"
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>This is a testing build</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-3 text-left text-text-primary text-base pt-2">
              <p>
                While you use it, we collect: how long each step takes, your computer's
                hardware specs, and your answers to a few short questions at each step.
              </p>
              <p className="font-medium">
                We do not collect the contents of your files — not your variable names, not
                your data values, not your PDF text. Only performance numbers and your
                written answers.
              </p>
              <p>
                When you're done, clicking "Submit Report" posts everything — including your
                written answers — as a public GitHub issue under your own GitHub account. You
                review it before it's submitted.
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <button
            onClick={acknowledge}
            className="w-full sm:w-auto inline-flex items-center justify-center h-10 px-6 rounded-md bg-primary text-primary-foreground hover:bg-primary-hover text-base font-medium transition-colors"
          >
            I understand, continue
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
