# Codebook builder: help users who have no target codebook

**Status:** idea, written up for later. Not planned for a release yet. Target window: before the grant ends (July 2027).
**Labels:** `enhancement`, `idea`, `usability`

## The problem

Step 1 of the app is "Upload Target Codebook". It assumes the user already knows what a codebook is and has one in the right
format (`variable_name`, `description`, and optional `dType`, `Unit`, `Categories`, `Unit Example`, ontology columns). Many
first-time users do not. The app ships a sample codebook and format notes, but a person who has never harmonised data has to
build a codebook by hand before they can do anything else.

Example: a researcher has two studies. Study A has columns `age, sex, wt, ht, sbp`. Study B has `AGE, GENDER, weight_kg, height_cm, bp_sys`.
They want one dataset with five shared variables. They do not know how to write the target list that both studies map to.

## The idea

On step 1, add a second path: **"I don't have a codebook, help me make one"**. The app reads one study's variable list (or data),
drafts a description, type and (where it can tell) categories for each variable, and the user decides what stays. The result is
loaded as the target codebook and can be downloaded and shared.

## Decisions already made (owner, 2026-10-08)

| Question | Decision |
|---|---|
| What does the first version start from? | One study's variable list or data. Several studies and starter templates come later. |
| Where does it live? | A second path inside step 1 (two buttons: "I have a codebook" and "I don't have one, help me make it"). The five-step flow stays the same. |
| Data and online AI | The app is built for local use. If the user chooses an online AI provider, show a clear notice before the first call saying what will be sent and to whom, and let them decide. A person confirms every description, so no extra privacy settings. |
| Sharing | The first version includes a download button, so the same codebook can be sent to other sites and every group maps to the same target. |

## How it would work (first version)

1. **Choose the path.** Step 1 shows "I have a codebook" (today's upload, unchanged) and "I don't have one, help me make it".
2. **Show us one study.** The user drops a study file: a variables CSV (needs `variable_name`) or a data CSV (the column names are the variables). Same size limits and CSV checks as the study upload.
3. **Draft.** The app lists every variable. For each one it proposes:
   - a description (the app's existing description generator, using the same prompt style and the AI the user already configured);
   - a type (`float`, `integer`, `string`, `boolean`, `datetime`) inferred from the data when data is given;
   - categories, only for columns with a small number of distinct values;
   - nothing for units: the app asks, it does not guess.
   Anything it is unsure of is marked "needs your input".
4. **Clarify.** An editable table. The user fills in blanks and corrects wrong guesses. Nothing is final until they confirm.
5. **Choose.** The user ticks the variables they want in the target codebook. Typically a handful out of dozens.
6. **Build and load.** The app writes the chosen rows as a normal target codebook (same format and checks as an uploaded one), loads it, and offers "Download this codebook". The study file used here is offered as the first study so it is not uploaded twice.

## What already exists and can be reused

- The codebook format and validation (`backend/core/validation.py`, `CodebookVariable` in `backend/models/schemas.py`) and the upload route (`POST /api/codebook/upload`).
- The AI description generator (`backend/core/descriptions.py`) and the AI connection settings.
- The study upload and its CSV reading (`backend/routers/studies.py`, `read_csv_robust`).
- The check-in pop-up and tour machinery, for the new screens.

## What is new

- A backend route that reads a study file and returns draft rows (no AI needed for names, types and categories; AI only for descriptions).
- A route that turns the confirmed rows into the stored codebook (reusing the existing save path).
- A frontend screen on step 1 with the editable table, the tick boxes and the download button.
- The notice for online AI providers (shown only when one is selected).
- Tests (see below) and a short "What is a codebook?" explainer on step 1.

## Later phases (not in the first version)

- **Several studies at once:** list every variable and how many studies contain it, so the user ticks the shared ones. Group similar names (`wt`, `weight_kg`) with the app's existing similarity search.
- **Starter templates and standards:** common health variables to start from; import from REDCap or CDISC dictionaries.
- **Ontology suggestions:** the sample codebook has ontology columns; the AI could suggest codes for the user to accept.
- **Version and compare:** a version number inside the shared codebook, so sites can tell when they are on different versions.

## How we would test it

Use the same method as the script export: naive-user habits and hostile inputs.
- Files with odd encodings, decimal commas, duplicate column names, header only, thousands of columns, a data file with real-looking IDs and free text (these must never be offered as categories or sent to the AI as values).
- Variable names with quotes, newlines, formulas (`=cmd|...`) and very long text: the generated codebook must open safely in Excel and parse back unchanged.
- A study with a column of 10,000 distinct values: must not become a giant category list.
- The user abandons halfway, goes back, changes the file, or switches AI provider mid-way.
- No AI available: the builder still works, with blank descriptions to fill in.
- The built codebook must pass the same validation as an uploaded one, and a full harmonisation run on it must work end to end with real Ollama models.
- A check on a screen reader and keyboard use, since the new screen is a form.

## Not in scope

Building a standards body's codebook for the user, automatic mapping without a person confirming, and sending any data anywhere the user has not chosen.

## Open questions for later

- Should "needs your input" blocks stop the user from continuing, or only warn?
- How many example values per column may the AI see when the user picks an online provider (suggest: none by default, a short list only for small categorical columns)?
- Should the builder also accept an Excel file, since the owner mentioned "the target Excel file"? (The app is CSV only today.)

## Effort and dependencies

First version: roughly one week of focused work including tests and the explainer. Depends on nothing else, but the step-1 check-in answers from the first testers ("Was it clear what file to upload here?") should confirm how big this barrier is before work starts.
