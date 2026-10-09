/** The tester's own operating system, as their browser reports it. The report's hardware
 * line comes from inside Docker, so on Windows and Mac it would say "Linux" (Docker's own
 * virtual machine); this gives the real one. One of a fixed set of short names, nothing
 * else about the browser is sent. */
export type HostOs = "Windows" | "macOS" | "Linux" | "Android" | "iOS" | "Other";

export function detectHostOs(): HostOs {
  if (typeof navigator === "undefined") return "Other";
  const nav = navigator as Navigator & { userAgentData?: { platform?: string } };
  const platform = (nav.userAgentData?.platform || navigator.platform || "").toLowerCase();
  const ua = (navigator.userAgent || "").toLowerCase();
  if (/android/.test(ua)) return "Android";
  if (/iphone|ipad|ipod/.test(ua)) return "iOS";
  if (/^win/.test(platform) || /windows/.test(ua)) return "Windows";
  if (/mac|darwin/.test(platform) || /macintosh|mac os/.test(ua)) return "macOS";
  if (/linux|x11|cros/.test(platform) || /linux|x11/.test(ua)) return "Linux";
  return "Other";
}
