# Access rules: Metadata Harmonisation Tool

Last confirmed by Mugume Twinamatsiko Atwine on 2026-10-07.

The tool has no user accounts. One researcher runs one copy on their own
computer, so the rules below are about where a request comes from, not who
is logged in.

## 1. Data

| Data | What it holds | Sensitivity |
|---|---|---|
| studies | uploaded study variable lists, example data CSVs (real participant-level rows) and context PDFs | sensitive: health |
| exports | the transformed dataset ZIP (participant-level rows), the mapping CSV and the audit log | sensitive: health |
| mappings | each variable's chosen codebook match, transformation, notes and the audit trail | internal |
| codebook | the target variable list | internal |
| workspace | running Initialise, its status, and wiping all studies and results | internal |
| ai_config | AI provider list, connection tests and model lists; API keys pass through but are not stored | internal |
| afpo | AfPO ontology lookups and the local record of submitted term requests | public |

## 2. Roles

| Role | Who they are | Scope |
|---|---|---|
| local | the researcher, using the tool's own pages (served from `localhost`) on the computer running it | all |
| website | any other website open in the researcher's browser, sending requests to `localhost` in the background | none |
| network | another device on the same network (Wi-Fi, lab LAN), or anyone on the internet if the port is forwarded | none, unless the researcher opts in (see section 6) |

How the app tells them apart:

- **network** is kept out by where the API listens. By default it listens on
  `127.0.0.1` only, so other devices can't connect at all. Setting
  `MHT_BIND_ADDRESS=0.0.0.0` opens it to the network on purpose.
- **website** is kept out by checking each request. A state-changing request
  (POST, PUT, DELETE) must come from one of the tool's own `localhost`
  origins, and every request must be addressed to `localhost` or
  `127.0.0.1` (the `Host` header), which stops DNS rebinding.

## 3. Permission grid

| Role | studies | exports | mappings | codebook | workspace | ai_config | afpo |
|---|---|---|---|---|---|---|---|
| local | view(all), create(all), delete(all) | view(all) | view(all), edit(all) | view(all), create(all) | view(all), create(all), delete(all) | view(all) | view(all), edit(all) |
| website | - | - | - | - | - | - | - |
| network | - | - | - | - | - | - | - |

## 4. Route map

| Method | Route | Data | Action |
|---|---|---|---|
| POST | /api/codebook/upload | codebook | create |
| GET | /api/codebook/meta | codebook | view |
| GET | /api/codebook/ | codebook | view |
| POST | /api/studies/upload | studies | create |
| GET | /api/studies/ | studies | view |
| DELETE | /api/studies/{study_name} | studies | delete |
| POST | /api/initialise/run | workspace | create |
| GET | /api/initialise/status | workspace | view |
| POST | /api/initialise/clear-workspace | workspace | delete |
| GET | /api/mappings/{study_name} | mappings | view |
| GET | /api/mappings/{study_name}/variable/{variable_name} | mappings | view |
| PUT | /api/mappings/{study_name}/variable/{variable_name} | mappings | edit |
| PUT | /api/mappings/{study_name}/variable/{variable_name}/reopen | mappings | edit |
| GET | /api/mappings/{study_name}/audit | mappings | view |
| POST | /api/mappings/preview-transformation | mappings | view |
| POST | /api/mappings/validate-expression | mappings | view |
| GET | /api/download/{study_name}/mapping-csv | exports | view |
| POST | /api/download/transformed-data | exports | view |
| GET | /api/download/audit-log | exports | view |
| GET | /api/ai-config/providers | ai_config | view |
| POST | /api/ai-config/test | ai_config | view |
| GET | /api/ai-config/models | ai_config | view |
| GET | /api/afpo/issue-url | afpo | view |
| POST | /api/afpo/lookup | afpo | view |
| POST | /api/afpo/gaps/submitted | afpo | edit |
| POST | /api/afpo/gaps/unsubmitted | afpo | edit |
| GET | /api/afpo/check-github | afpo | view |
| GET | /api/afpo/ontology-status | afpo | view |

No route is public: every route belongs to the local researcher only.

## 5. Abuse cases

- Someone on the same café or conference Wi-Fi opens
  `http://<laptop-ip>:8000/api/download/transformed-data` and downloads
  participant data. Covered by: network row, all `-` (API listens on
  127.0.0.1 by default).
- A website the researcher has open sends a hidden form POST to
  `http://localhost:8000/api/initialise/clear-workspace` and wipes every
  study. Covered by: website row, workspace = `-` (origin check).
- A website uploads a planted study through a form POST to
  `/api/studies/upload`. Covered by: website row, studies = `-`.
- A website uses DNS rebinding (its own domain resolving to 127.0.0.1) so
  the browser lets it read API replies, then downloads participant data.
  Covered by: website row, exports = `-` (Host header check).
- Someone calls the API directly instead of using the app's pages. Covered:
  the same three checks apply to any client.

## 6. Open questions for the owner

- Opening the API to a network (`MHT_BIND_ADDRESS=0.0.0.0`) gives everyone
  on that network full access, including participant data and deletion,
  because there are no logins. Is a warning in the README enough, or should
  network mode require a shared access token? (Issue #4 tracks real
  authentication.)
- Participant-level data sits unencrypted in `input/` and `results/` on the
  researcher's disk. Do the studies' data agreements or ethics approvals
  require disk encryption or deletion after harmonisation?
- Which data protection laws and data-sharing agreements apply to the
  studies people load (for example the Uganda and Kenya Data Protection
  Acts, POPIA, GDPR for European cohorts)? Owner to decide, with legal or
  ethics-office advice.

## 7. What this file does not cover

- Whether login itself is safe (password storage, sessions, password reset).
- Secrets: API keys or passwords committed to the code.
- Libraries with known security holes.
- Server, database and cloud settings (open database ports, public storage
  buckets, debug mode in production, CORS set to allow every site).
- Attacks on the code itself, such as SQL injection or cross-site scripting.
- Limits on repeated requests (rate limiting).
- Backups and what to do if data leaks.

Use `/security-review`, a secret scanner (gitleaks), a dependency audit
(`pip-audit`, `npm audit`) and, for apps holding sensitive data, a human
penetration test for these.
