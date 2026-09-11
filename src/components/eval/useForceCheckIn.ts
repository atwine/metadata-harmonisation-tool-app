import { useEffect, useState } from "react";

/** True when the URL carries ?checkin=<step> — how the "you still need to
 * answer this" notice on the final report page sends someone back to a
 * step's check-in even if the step's own normal completion signal (e.g.
 * "all variables mapped") never fired, because they moved on before
 * finishing it. Plain query-string read (not the router's typed search)
 * so it works from any page without each route declaring validateSearch. */
export function useForceCheckIn(step: string): boolean {
  const [force, setForce] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("checkin") === step) setForce(true);
  }, [step]);

  return force;
}
