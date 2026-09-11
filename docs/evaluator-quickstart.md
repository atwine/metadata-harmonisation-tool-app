# Testing the Metadata Harmonisation Tool — Quickstart for Evaluators

Thanks for helping test this. The whole thing — install, a full harmonisation run,
and a short questionnaire at the end — takes about **20–30 minutes**. Everything
runs on your own machine; nothing about your actual data ever leaves it.

## What this testing build does differently from the real app

This is a special build, used only for this evaluation — the version everyone else
uses does not have any of this in it. While you use it, it:

- Times each step (install, upload, initialise, map, download) and records your
  computer's hardware specs and which AI settings you used. **Never** the contents
  of your files — not variable names, not data values, not PDF text. Only
  performance numbers.
- Asks 1–2 short questions after each step ("was this clear?", "how easy was this?"),
  plus a longer questionnaire at the very end. Every question can be skipped —
  skipping is itself useful information to us, so don't feel obligated to answer
  everything.
- Ends with a **"Submit Report"** button. Clicking it opens a pre-filled GitHub
  issue in your browser with everything above — you review it, then click GitHub's
  own Submit button yourself, under your own GitHub account. Nothing is sent
  automatically or in the background.

You'll see all of this explained again on-screen the first time you open the app,
before anything is collected.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and
  **running** (open it and wait for "Docker Desktop is running" before continuing).
- ~8GB free RAM, a few GB free disk space (for the bundled local AI models).
- A GitHub account, to submit your report at the end.

You do **not** need to install Python, Node, or Ollama separately, and you do
**not** need to clone the repository or download any source code.

## Getting it running

1. Download this one file (right-click → Save As, or `curl` it):
   ```bash
   curl -O https://raw.githubusercontent.com/atwine/metadata-harmonisation-tool-app/eval/instrumentation-build/docker-compose.eval.yml
   ```
   If that link doesn't work for you, open it in the repo on GitHub and use the
   "Download raw file" button instead — either way, you just need this one file
   saved somewhere on your computer.
2. Open a terminal in the folder where you saved it, and run:
   ```bash
   docker compose -f docker-compose.eval.yml pull
   docker compose -f docker-compose.eval.yml up
   ```
3. The first run downloads the AI models (several GB — this is the slow part,
   several minutes). Wait until you see `models ready — serving.` in the terminal.
4. Open **http://localhost:8080** in your browser.

Every run after the first is fast — nothing gets re-downloaded.

## When you're done

```bash
docker compose -f docker-compose.eval.yml down
```

This stops everything but keeps your progress and the downloaded models, so if
you come back later you can just `up` again without waiting.

## Test data

If you don't have your own dataset handy, sample data is bundled with the app —
look for it on the Upload Studies page, or ask the coordinator for the test ZIP
(target codebook, study variables, example data, and a context PDF).

## Questions or something breaks

Note down what happened (a screenshot or the exact error text helps) and let the
evaluation coordinator know — that's useful feedback either way, even if you can't
get past it. If you get stuck for more than 15 minutes on a single step, it's fine
to stop there and mention where in your report.
