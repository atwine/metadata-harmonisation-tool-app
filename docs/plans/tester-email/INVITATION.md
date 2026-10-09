Subject: Help test the Metadata Harmonisation Tool (30 minutes, plus a one-time download)

Dear [name],

We are testing a tool that helps researchers harmonise variables from different health study datasets into one shared list, so the data can be compared side by side. It runs entirely on your own computer, and we would be grateful if you could try it and tell us what works and what doesn't.

**What we are asking**

- Install it (it runs in Docker) and do one full run on sample data, or on your own variable lists if you prefer.
- It takes about 20 to 30 minutes once it is installed.
- You answer one or two short questions after each step, and a slightly longer form at the end. Every question can be skipped.
- At the end you submit a report as a GitHub issue from your own account. You see the whole text first and press GitHub's Submit button yourself. Nothing is sent automatically.

**Please start the download before your testing session**

The first time, your computer downloads about 7 GB (the app plus a local AI engine and its models) and needs about 15 GB of free disk space. How long that takes depends only on your internet connection: about 15 minutes on a fast connection, about an hour on a typical one, and a couple of hours on a slow one. You can stop it and run the same command again, and it carries on where it left off. After that, the app starts in seconds and nothing is downloaded again.

**What you need**

- Docker Desktop, installed and running
- About 15 GB of free disk space and about 8 GB of free RAM
- A GitHub account, for the final report
- The test files (the guide explains where to get them)

**The guide, step by step**

https://github.com/atwine/metadata-harmonisation-tool-app/blob/eval/instrumentation-build/docs/evaluator-quickstart.md

Two things from the guide that trip people up: on Windows use `curl.exe` (not `curl`) to download the file, and open the app at http://localhost:8080 (type `localhost`, not `127.0.0.1`).

**What is collected, and what is not**

The testing version records how long each step takes, your computer's hardware and operating system, which AI settings you used, and the answers you type. It never records the contents of your files: not variable names, not data values, not text from a PDF. Your written answers become a public GitHub issue that anyone can read, so please leave out names and personal details. This version is for evaluation only, so please do not load real participant data into it. The sample files are enough.

**Two things you may notice**

- A Yes/No column mapped to the "boolean" type without a rule turns every value into True, and a decimal mapped to "integer" is cut off (78.6 becomes 78). We know about both, so you do not need to report them.
- If something else breaks, please tell us. A screenshot or the exact error text helps a lot, and "I got stuck here" is useful feedback too. If you are stuck for more than 15 minutes on one step, you can stop there and say where in your report.

**When and who to ask**

Please send your report by [date]. Questions go to [your name, email or phone].

Thank you for your time. It will make the tool better for the researchers who use it after you.

[Your name]
[Your role and project]
