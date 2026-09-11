import { useCallback, useEffect, useState } from "react";
import { STATUS, type EventData } from "react-joyride";
import { isEvalBuild } from "@/lib/evalBuild";

const STORAGE_PREFIX = "tour-seen:";

/**
 * Tracks whether a given page tour has been seen before (localStorage,
 * per-browser) and auto-starts it on first visit. `start()` lets a page
 * offer a manual "Take a tour" replay regardless of seen-state.
 *
 * In the eval testing build, tours never auto-start — they collided with
 * the disclosure dialog and step check-in popups that also want the
 * screen on first load, and the tour's overlay could block those from
 * being dismissed. Manual "Take a tour" still works.
 */
export function useProductTour(tourId: string) {
  const storageKey = `${STORAGE_PREFIX}${tourId}`;
  const [run, setRun] = useState(false);

  useEffect(() => {
    if (isEvalBuild()) return;

    let seen = false;
    try {
      seen = localStorage.getItem(storageKey) === "1";
    } catch {
      // localStorage unavailable (private browsing, etc) — just don't auto-run.
    }
    if (!seen) setRun(true);
  }, [storageKey]);

  const markSeen = useCallback(() => {
    try {
      localStorage.setItem(storageKey, "1");
    } catch {
      // ignore — worst case the tour auto-plays again next visit
    }
  }, [storageKey]);

  const handleEvent = useCallback(
    (data: EventData) => {
      if (data.status === STATUS.FINISHED || data.status === STATUS.SKIPPED) {
        setRun(false);
        markSeen();
      }
    },
    [markSeen],
  );

  const start = useCallback(() => setRun(true), []);

  return { run, handleEvent, start };
}
