# Security Audit — metadata-harmonisation-tool-app

Audit date: 2026-07-13
Scope: full repository (React/TanStack Start frontend, FastAPI backend, npm/bun and pip dependencies). Audit-only — no fixes applied.

## Summary

| #   | Finding                                                                                                       | Category                              | Severity |
| --- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------- | -------- |
| 1   | No authentication/authorization on any backend API endpoint                                                   | Auth gap                              | High     |
| 2   | SSRF via user-supplied `base_url` for Ollama/Azure OpenAI providers                                           | SSRF                                  | High     |
| 3   | `undici` (transitive, via wrangler/miniflare) — multiple high-severity CVEs                                   | Dependency CVE                        | High     |
| 4   | `ws` (transitive, via wrangler/miniflare) — DoS via memory exhaustion                                         | Dependency CVE                        | High     |
| 5   | `vite` — `server.fs.deny` bypass on Windows / arbitrary file read                                             | Dependency CVE                        | High     |
| 6   | `@cloudflare/vite-plugin` / `wrangler` / `miniflare` — high-severity advisories (dev dependency chain)        | Dependency CVE                        | High     |
| 7   | `js-yaml` — quadratic-complexity DoS via merge-key aliases                                                    | Dependency CVE                        | Medium   |
| 8   | Path-prefix check without separator in `safe_delete_dir`/`safe_delete_file` (`storage/files.py`)              | Path traversal (defense-in-depth gap) | Medium   |
| 9   | `esbuild` — arbitrary file read on Windows dev server                                                         | Dependency CVE                        | Low      |
| 10  | `@babel/core` — arbitrary file read via sourceMappingURL                                                      | Dependency CVE                        | Low      |
| 11  | No rate limiting / abuse protection on upload or AI endpoints beyond a per-process 60 req/min AI call limiter | Resource exhaustion                   | Low      |
| 12  | No CVEs found in current Python dependency set (pip-audit clean)                                              | Info                                  | Info     |
| 13  | No hardcoded secrets/API keys found in source                                                                 | Info                                  | Info     |

---

## 1. No authentication/authorization on backend API endpoints (High)

**Location:** `backend/main.py`, all files under `backend/routers/`

None of the routers (`codebook`, `studies`, `initialise`, `mappings`, `download`, `ai_config`) require any form of authentication. Any client that can reach the FastAPI service can upload files, delete studies (`DELETE /api/studies/{study_name}`), trigger AI-provider calls, and exfiltrate data via `/api/download/*`. The CORS policy is restricted to `localhost` origins (`main.py:20-28`), which limits browser-based cross-origin abuse, but does nothing to stop a party with direct network access to the API (e.g. on a shared host, in a container network, or if the service is ever exposed beyond localhost).

**Impact:** Full read/write/delete access to all study data and AI provider credentials-in-transit for anyone who can reach the API.

---

## 2. SSRF via user-supplied `base_url` (High)

**Location:** `backend/core/config.py:33,68,74,80-84`, `backend/routers/ai_config.py:66-79`

`ModelConfig.get_client()` passes the client-supplied `base_url` directly into `openai.OpenAI(base_url=...)`, `anthropic.Anthropic(base_url=...)`, and `openai.AzureOpenAI(azure_endpoint=...)` with no allow-list or scheme/host validation. Similarly, `GET /api/ai-config/ollama-models?base_url=...` (`ai_config.py:65-79`) takes an arbitrary `base_url` query parameter and has the server (`ollama.Client(host=base_url)`) make an outbound request to it, returning parsed response data to the caller.

Because this couples with finding #1 (no auth), any caller can direct the backend server to make HTTP requests to arbitrary hosts (internal network services, cloud metadata endpoints such as `169.254.169.254`, etc.) and receive a reflected response, plus optionally exfiltrate the configured API key to an attacker-controlled `base_url`.

**Impact:** Internal network reconnaissance, cloud metadata service access, credential exfiltration.

---

## 3–6. High-severity transitive dependency CVEs (npm) (High)

**Location:** `package.json` / `package-lock.json` / `bun.lock` — `npm audit` output, 2026-07-13

Detected via `npm audit` (9 total advisories: 6 high, 1 moderate-listed-as-high-group, 2 low):

- **undici** (`>=7.23.0 <7.28.0`, pulled in via `wrangler`/`miniflare`): multiple GHSA advisories including TLS certificate validation bypass (GHSA-vmh5-mc38-953g, high), WebSocket fragment-count DoS bypass (GHSA-vxpw-j846-p89q, high), cross-origin request routing via SOCKS5 proxy pool reuse (GHSA-hm92-r4w5-c3mj, high), HTTP header injection via Set-Cookie decoding (GHSA-p88m-4jfj-68fv, moderate), cross-user cache information disclosure (GHSA-pr7r-676h-xcf6, moderate).
- **ws** (`>=8.0.0 <8.21.0`, via `wrangler`/`miniflare`): memory exhaustion DoS from tiny fragments (GHSA-96hv-2xvq-fx4p, high); uninitialized memory disclosure (GHSA-58qx-3vcg-4xpx, moderate).
- **vite** (`>=7.0.0 <=7.3.4`): `server.fs.deny` bypass on Windows alternate paths (GHSA-fx2h-pf6j-xcff, high); NTLMv2 hash disclosure via UNC path handling (GHSA-v6wh-96g9-6wx3, moderate).
- **wrangler**, **miniflare**, **@cloudflare/vite-plugin**: flagged high due to the above transitive chain.

All are **dev/build-time dependencies** (Cloudflare Vite plugin, Wrangler, Vite dev server) rather than runtime production dependencies, which limits exploitability to local development and CI environments, but should still be tracked. Fix availability: run `npm audit fix` / `bun update` to pull patched ranges once upstream `wrangler`/`miniflare` release compatible updates.

---

## 7. `js-yaml` quadratic-complexity DoS (Medium)

**Location:** `package-lock.json` / `bun.lock`, transitive dependency, range `>=4.0.0 <=4.1.1`

GHSA-h67p-54hq-rp68: crafted YAML with repeated merge-key aliases can cause quadratic-time parsing, a DoS vector if this package ever parses untrusted YAML. Currently only reachable through the build toolchain (Wrangler config parsing), so exploitability at runtime is low, but worth tracking for an upstream fix.

---

## 8. Path-prefix check without separator boundary (Medium — defense-in-depth gap)

**Location:** `backend/storage/files.py:39-56` (`safe_delete_dir`, `safe_delete_file`); similar pattern also present in `backend/routers/studies.py:116-121` and `backend/routers/download.py:24-27`

The traversal guard is implemented as:

```python
if str(resolved).startswith(str(allowed)) and ...
```

`str.startswith()` on a resolved path is not boundary-safe: a sibling directory whose name has `allowed` as a literal prefix (e.g. an `allowed` of `.../input` matching a path `.../input_evil`) would pass the check even though it is outside the intended directory. In this codebase `safe_delete_dir`/`safe_delete_file` are currently unused (dead code) and every caller of the prefix-check pattern first passes the name through `sanitise_study_name()`, which strips all characters outside `[\w\s-]` (removing `/`, `.`, etc.) before the check runs, so the practical exploitability today is low. This is flagged as defense-in-depth: if `sanitise_study_name` is ever bypassed, refactored, or these helper functions are wired up to a new caller that skips sanitisation, the prefix check alone would not stop traversal into a same-prefixed sibling directory.

---

## 9. `esbuild` arbitrary file read (Low)

**Location:** `package-lock.json` / `bun.lock`, range `>=0.27.3 <0.28.1`

GHSA-g7r4-m6w7-qqqr: esbuild's dev server can allow arbitrary file reads on Windows. Dev-only, low CVSS (2.5).

---

## 10. `@babel/core` arbitrary file read (Low)

**Location:** `package-lock.json` / `bun.lock`, range `<=7.29.0`

GHSA-4x5r-pxfx-6jf8: arbitrary file read via crafted `sourceMappingURL` comments during build-time source-map processing. Build-time only, low CVSS (3.2).

---

## 11. No rate limiting / resource limits beyond AI calls (Low)

**Location:** `backend/routers/studies.py`, `backend/routers/codebook.py`

Upload endpoints enforce file-size caps (10MB/50MB/100MB) but there is no per-client rate limiting on uploads, study creation, or CSV parsing (`read_csv_robust` in `storage/files.py:85-96` runs `clevercsv.Sniffer` and `pandas.read_csv` on attacker-controlled content). Combined with no-auth (#1), a client could repeatedly upload large/adversarial CSV files to exhaust disk or CPU. The only rate limiter in the codebase is the 60 req/min sliding window in `AIProviderWrapper` (`backend/core/ai_provider.py:45-52`), which only throttles outbound AI provider calls, not inbound upload/study endpoints.

---

## 12. Python dependency CVE scan — clean (Info)

**Tooling:** `pip-audit -r backend/requirements.txt` (resolved via a clean venv on 2026-07-13)

No known vulnerabilities were found in the resolved dependency set (fastapi, uvicorn, pandas, numpy, scipy, pdfminer.six, python-dotenv, openai, anthropic, ollama, clevercsv, python-multipart, and their transitive deps — see full resolved version list in the pip-audit run). Note `requirements.txt` pins no versions, so this reflects whatever is latest-resolvable today; re-run `pip-audit` before each release since unpinned deps can silently drift to a vulnerable version later.

---

## 13. No hardcoded secrets found (Info)

Searched all source files (`backend/`, `src/`) and config/history-visible files (`.gitignore`, `.lovable/project.json`, `.claude/settings.local.json`) for API keys, tokens, passwords, and connection strings. All `api_key` references are user-supplied at runtime (stored client-side in `src/stores/aiConfigStore.ts` / posted to the backend), validated only by regex format in `backend/core/config.py:66,72,78`, and never committed. No `.env` files are tracked in git. No secrets were found in `git log --all` filenames either.

**Note:** API keys submitted through the frontend (`src/components/Sidebar.tsx:194`) are held in browser state/localStorage-backed stores and sent to the backend over plain HTTP by default (`http://localhost:*`); this is acceptable for local-only use but would need TLS and secret-handling review before any non-local deployment.
