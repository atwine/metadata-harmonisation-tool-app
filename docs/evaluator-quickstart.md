# Testing the Metadata Harmonisation Tool: Quickstart for Evaluators

Thanks for helping test this. Once everything is installed, a full harmonisation run
and a short questionnaire at the end take about **20 to 30 minutes**. Everything
runs on your own machine; nothing about your actual data ever leaves it.

**Read "Before you start" first.** The first-time download is large (about 7 GB), and how
long it takes depends on your internet speed. Start it ahead of time, not at the start of your session.

## What this testing build does differently from the real app

This is a special build, used only for this evaluation. The version everyone else
uses does not have any of this in it. While you use it, it:

- Times each step (install, upload, initialise, map, download) and records your
  computer's hardware specs and which AI settings you used. **Never** the contents
  of your files: not variable names, not data values, not PDF text. Only
  performance numbers.
- Asks 1 to 2 short questions after each step ("was this clear?", "how easy was this?"),
  plus a longer questionnaire at the very end. Every question can be skipped.
  Skipping is itself useful information to us, so don't feel obligated to answer
  everything.
- Ends with a **"Submit Report"** button. Clicking it opens a pre-filled GitHub
  issue in your browser with everything above. You review it, then click GitHub's
  own Submit button yourself, under your own GitHub account. Nothing is sent
  automatically or in the background.

You'll see all of this explained again on-screen the first time you open the app,
before anything is collected.

## Before you start

**What you need**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and
  **running** (open it and wait for "Docker Desktop is running" before continuing).
- **About 15 GB of free disk space** and about 8 GB of free RAM.
- A GitHub account, to submit your report at the end.
- Test data (see "Test data" below). If you have your own study data, you can use that instead.

You do **not** need to install Python, Node, or Ollama separately.

**How big the first download is, and how long it takes**

The first time, your computer downloads the app and a local AI engine from Docker Hub
(about 4.4 GB), and then the AI models (about 2.3 GB). That is **about 7 GB in total**, and it
takes up about 15 GB of disk once unpacked. How long it takes depends only on your internet
connection:

| Your connection | Rough time for the first download |
|---|---|
| Fast (about 100 Mbit/s or more, 10 MB/s or more) | about 10 to 15 minutes |
| Typical (about 20 Mbit/s, 2.5 MB/s) | about 45 minutes |
| Slow (about 8 Mbit/s, 1 MB/s) | 2 hours or more |

Tips:

- **Start the download before your testing session**, for example the evening before.
  You can stop it (`Ctrl+C`) and run the same command again; it continues where it left off.
- A wired connection or a fast network (for example at your institution) makes a big difference.
- The progress bars can sit still for minutes on the big pieces. That is normal. Wait.
- **You only do this once.** After that, the app and the AI models are stored on your
  computer, so later runs do not download them again and start in seconds.

## Getting it running

1. Download this one file.

   Mac or Linux:
   ```bash
   curl -O https://raw.githubusercontent.com/atwine/metadata-harmonisation-tool-app/eval/instrumentation-build/docker-compose.eval.yml
   ```
   Windows (PowerShell). Note it is `curl.exe`, not `curl`; plain `curl` is a different
   command in PowerShell and fails with "missing mandatory parameters":
   ```bash
   curl.exe -O https://raw.githubusercontent.com/atwine/metadata-harmonisation-tool-app/eval/instrumentation-build/docker-compose.eval.yml
   ```
   If that link doesn't work for you, open it in the repo on GitHub and use the
   "Download raw file" button instead. Either way, you just need this one file
   saved somewhere on your computer.
2. Open a terminal in the folder where you saved it, and run the big download first:
   ```bash
   docker compose -f docker-compose.eval.yml pull
   ```
   This is the slow part (see the table above). When it finishes, start the app:
   ```bash
   docker compose -f docker-compose.eval.yml up
   ```
3. The first `up` also downloads the AI models (about 2.3 GB). Wait until you see
   `models ready — serving.` in the terminal.
4. Open **http://localhost:8080** in your browser. Type `localhost`, not `127.0.0.1`: the
   app refuses requests from any other address on purpose, and it can only be opened
   from the computer it runs on.

Every run after the first is fast: nothing gets downloaded again.

## When you're done

```bash
docker compose -f docker-compose.eval.yml down
```

This stops everything but keeps your progress and the downloaded models, so if
you come back later you can just `up` again without waiting.

## Test data

If you don't have your own dataset, use the sample data that comes with the project. It is
in the **`example_data`** folder of the repository (nothing is built into the app itself).
You can get it in either of two ways:

- **The whole repository as one ZIP (easiest).** Download
  <https://github.com/atwine/metadata-harmonisation-tool-app/archive/refs/heads/eval/instrumentation-build.zip>,
  unzip it, and open the `example_data` folder inside. It is small. Or, if you use Git,
  `git clone` the repository and use its `example_data` folder.
- **Just the files you need**, from
  <https://github.com/atwine/metadata-harmonisation-tool-app/tree/eval/instrumentation-build/example_data>
  (open a file, then use "Download raw file").

Which file goes where in the app:

| App step | File to upload |
|---|---|
| 1. Upload Codebook | `example_data/target_variables.csv` |
| 2. Upload Studies, study variables | `example_data/CH_SIB/dataset_variables.csv` |
| 2. Upload Studies, example data (optional) | `example_data/CH_SIB/example_data.csv` |
| 2. Upload Studies, context PDF (optional) | `example_data/CH_SIB/CINECA synthetic cohort Europe CH SIB.pdf` |

Use any study name you like, for example `CH_SIB`. There are two more sample studies
(`ACE_Uganda` and `AfPO_Uganda_Clinical`) in the same folder if you want to try more.

## Questions or something breaks

Note down what happened (a screenshot or the exact error text helps) and let the
evaluation coordinator know. That's useful feedback either way, even if you can't
get past it. If you get stuck for more than 15 minutes on a single step, it's fine
to stop there and mention where in your report. Slow downloads are not a failure on
your side: just tell us how long the first download took.
