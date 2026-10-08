# Security and incident plan

DRAFT. Everything marked **[OWNER TO FILL]** is a decision or a detail only the owner can supply.
Nothing in those blanks has been guessed. Remove this line when every blank is filled.

This tool runs on a researcher's own computer and handles participant-level health data (study
CSVs, example data, mappings and exports). It has no user accounts. The rules for who may reach
what are in [ACCESS.md](ACCESS.md).

## 1. Reporting a security problem

- Please do **not** open a public GitHub issue for a security problem or post participant data,
  keys or file contents anywhere public.
- Contact: **[OWNER TO FILL: email address or other private channel to report to]**
- GitHub's private "Report a vulnerability" button is **currently not enabled** on this repository.
  **[OWNER TO FILL: enable it (Settings, Security, Private vulnerability reporting) and say so
  here, or state that the email above is the only route]**
- What to include: what you saw, which version (see [CHANGELOG.md](CHANGELOG.md)), and how to
  reproduce it. Do not attach real participant data.
- Acknowledgement time we aim for: **[OWNER TO FILL]**

## 2. Who decides

- Person who decides what to do in an incident: **[OWNER TO FILL: name and role]**
- Backup person if they cannot be reached: **[OWNER TO FILL: name and role]**
- Technical contact at eLwazi or the hosting institution, if any: **[OWNER TO FILL, or "none"]**
- Contact for each data owner whose study is loaded (data-sharing agreements usually name one):
  **[OWNER TO FILL: where this list is kept]**

## 3. First steps in an incident

Do these first, in this order. They are safe to do while you work out what happened.

1. **Take the app offline.** From the folder that holds your compose file:
   ```bash
   docker compose down                              # built from source
   docker compose -f docker-compose.hub.yml down    # prebuilt download-and-run
   ```
   This stops the containers and keeps your data in `./harmonisation-data/`. A manual install:
   close the terminals running the backend (`python run_backend.py`) and the frontend.
2. **Disconnect the computer from the network** if you think someone else got in (Wi-Fi off or cable out).
3. **Keep the evidence.** Do not delete `harmonisation-data/` or the logs. Make a copy first with
   `scripts/backup.sh` or `scripts/backup.ps1` (see [docs/docker.md](docs/docker.md)). A backup
   holds participant data, so store it privately.
4. **Write down** the time, what you noticed, and which studies were loaded.

## 4. Rotating keys

The app stores almost no secrets. Where each one lives and how to replace it:

| Secret | Where it lives | How to rotate |
|---|---|---|
| AI provider keys (OpenAI, Anthropic, Azure OpenAI, vLLM) | Typed into the AI Configuration panel. The app does **not** save them; they are asked for again after a page reload. | Create a new key at the provider, then revoke the old one there. Also check the provider's usage page for use you did not make. |
| `GITHUB_TOKEN` (optional, used for the AfPO duplicate check) | A `.env` file next to `docker-compose.yml`, or your shell. The `.env` file is ignored by git. | Revoke the token in your GitHub account settings, create a new one with no extra permissions, update `.env`, then `docker compose up -d`. |
| `DOCKERHUB_TOKEN` (maintainers only) | A GitHub repository secret, used by the publishing workflow. | Revoke in Docker Hub, create a new access token with Read and Write access, replace the repository secret. **[OWNER TO FILL: who holds access to this]** |
| Anyone's GitHub account or maintainer access | GitHub | **[OWNER TO FILL: who can remove a maintainer, and how fast]** |

There are no passwords or login sessions to revoke: the tool has no accounts. If the app was ever
opened to a network on purpose (`MHT_BIND_ADDRESS=0.0.0.0`, see [docs/docker.md](docs/docker.md)),
treat everyone who was on that network during that time as having had access.

## 5. Telling people

- Who must be told first, and by whom: **[OWNER TO FILL]**
- Data owners and participants' representatives (the people responsible for each loaded study):
  how soon after discovery they are told: **[OWNER TO FILL: deadline, for example the hours or days
  your data-sharing agreements require]**
- Regulators or ethics committees to notify, and the deadline for each (which laws apply is an
  open owner decision, see ACCESS.md section 6): **[OWNER TO FILL]**
- What the message must contain: what happened, which studies and which kinds of data, when,
  what has been done, who to contact. **[OWNER TO FILL: template wording or its location]**

## 6. After the incident

- Update the app and its dependencies if the problem came from them (see the weekly scan in
  `.github/workflows/security-scans.yml`).
- Add a test to `tests/test_access.py` or a new test file that fails without the fix.
- Record what happened, the cause, and what changed. **[OWNER TO FILL: where incident records are kept]**
- Review this plan.

## What this plan does not cover

How long data is kept, disk encryption, and the privacy policy are separate decisions the owner
has not made yet (ACCESS.md section 6). A backup archive is not encrypted.
