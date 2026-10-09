# Access audit: Metadata Harmonisation Tool

Audited 2026-10-07 on `main` (c298838) with the `access-guard-audit` skill.
Rules: [`ACCESS.md`](ACCESS.md). Proof: [`tests/test_access.py`](test_access.py),
output before the fixes in [`docs/access-audit-before.txt`](access-audit-before.txt).

28 routes from `app.routes`, all mapped in `ACCESS.md` section 4. The API has
no logins (known, issue #4), so the intended rule is "only the researcher on
the computer running it". Three gaps break that rule. All three reach
participant-level health data or destroy work without any login, so all
three are critical under the skill's scale.

## Findings

### F1 (critical): anyone on the same network can download participant data and delete studies
- Route: all 28, through port 8000
- Who gets in who shouldn't: any device on the same Wi-Fi or LAN as the
  researcher (a café, a conference, a university network)
- Data exposed: every uploaded study, including example data with real
  participant rows, the transformed dataset ZIP, mappings and the audit log;
  also delete study and clear workspace
- Rule broken: ACCESS.md grid, network row = `-`
- Why it happens: `docker-compose.yml` and `docker-compose.hub.yml` publish
  `"8000:8000"` and `"8080:8080"`, which Docker binds on every network
  interface, and `run_backend.py` runs uvicorn with `host="0.0.0.0"`. The
  README warns against exposing the API, but the default setup does exactly
  that.
- Suggested fix: listen on 127.0.0.1 by default (`"127.0.0.1:8000:8000"` in
  both compose files, `host="127.0.0.1"` in `run_backend.py`), with an
  `MHT_BIND_ADDRESS` setting to open it on purpose on a trusted network.
- Proven by: `test_run_backend_listens_on_localhost_by_default`,
  `test_compose_publishes_on_localhost_by_default[docker-compose.yml]`,
  `test_compose_publishes_on_localhost_by_default[docker-compose.hub.yml]`

### F2 (critical): any website the researcher visits can wipe the workspace, overwrite the codebook and plant studies
- Routes: POST /api/initialise/clear-workspace, POST /api/codebook/upload,
  POST /api/studies/upload
- Who gets in who shouldn't: any web page open in the researcher's browser,
  through a hidden form or background request to `localhost:8000`
- Data exposed or changed: clear-workspace deletes every study, result and
  log; codebook upload silently replaces the target codebook every mapping is
  built on; studies upload adds fake studies
- Rule broken: ACCESS.md grid, website row = `-`
- Why it happens: browsers send "simple" requests (no body, form posts with
  files) to any address without asking first. CORS only stops the page from
  reading the reply, and these three routes do their damage without needing
  to. The JSON routes are safe: FastAPI refuses the plain-text bodies a
  website can send (422), and PUT and DELETE are blocked by the CORS
  preflight.
- Suggested fix: refuse POST, PUT and DELETE requests whose `Origin` isn't
  one of the tool's own `localhost` origins.
- Proven by: `test_access_rule[website POST /api/initialise/clear-workspace -> deny ...]`,
  `test_access_rule[website POST /api/codebook/upload -> deny ...]`,
  `test_access_rule[website POST /api/studies/upload -> deny ...]`,
  `test_website_cannot_wipe_the_workspace`

### F3 (critical): a website can read participant data through DNS rebinding
- Route: all 28
- Who gets in who shouldn't: a malicious website that points its own domain
  at 127.0.0.1 (DNS rebinding). The browser then treats the API as part of
  that site, so the page can call any route and read the reply.
- Data exposed: everything F1 exposes, from anywhere on the internet, even
  when the API listens only on 127.0.0.1
- Rule broken: ACCESS.md grid, website row = `-`
- Why it happens: the API answers requests addressed to any host name. It
  never checks the `Host` header.
- Suggested fix: only answer requests addressed to `localhost` or
  `127.0.0.1` (Starlette's `TrustedHostMiddleware`), extendable through the
  same opt-in setting as F1.
- Proven by: 28 `test_access_rule[rebinding ... -> deny ...]` cases,
  `test_rebinding_site_cannot_read_studies`

## Stricter than the rules

None. The researcher on their own computer can use every route.

## Other observations (outside access control)

Not findings under this audit's scope, but worth a look with
`/security-review`:

- `GET /api/ai-config/models` takes the vLLM API key as a URL query
  parameter (`?api_key=`), so it can end up in server and proxy logs and
  browser history. A request header or POST body keeps it out of URLs.
- `GET /api/ai-config/models` and `POST /api/ai-config/test` connect to any
  `base_url` they are given. Once F1 and F3 are fixed only the researcher can
  call them, which removes most of the risk.

## Open questions

See `ACCESS.md` section 6: whether network mode should need a shared token,
disk encryption and deletion duties for participant data, and which data
protection laws and agreements apply.
