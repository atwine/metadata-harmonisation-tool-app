# Preparing your input files

Read this **before** you open the tool. Getting your files into the right shape is the
step that takes testers the longest, and it's easy to do up front.

You need one **target codebook** (the list of standard variables you're mapping *to*) and one
**study variables file** per study (the list of variables you're mapping *from*). Two more
files are optional and improve the AI's suggestions.

## Rules that apply to every CSV

- Save as **CSV, UTF-8 encoded**. (In Excel: *Save As → CSV UTF-8*.) A file that isn't UTF-8 is rejected.
- The first row must be a **header row**.
- Column names must match **exactly as written below, including capitalisation**
  (`variable_name`, not `Variable_Name` or `Variable Name`).
- Comma, semicolon and tab separators are all detected automatically.

## 1. Target codebook (Upload Codebook page)

| Column | Status | What it holds |
|---|---|---|
| `variable_name` | **Required** | The standard variable's name |
| `description` | **Required** | A plain-language description of what it measures |
| `dType` | Optional | Data type: `float`, `integer`, `string`, `boolean` (other values are accepted but get default handling) |
| `Unit` | Optional | The unit or format the values use |
| `Categories` | Optional | The allowed values, for categorical variables |
| `Unit Example` | Optional | An example value in that unit |

**What "optional" means:** an optional column can be left out of the file entirely. The upload
still succeeds and shows a "Recommended column missing" note. Fill them in if you have them.

**Why `description` matters:** the tool matches by meaning, and the description carries most of
the weight (80% description, 20% variable name). A codebook with empty descriptions matches poorly.
The upload only rejects a file that has *neither* `variable_name` nor `description`, but include both.

Size limit: 10 MB. Extra columns (for example ontology codes, as in the example file below) are allowed.

A working example: [`example_data/target_variables.csv`](../example_data/target_variables.csv).

### Coming from a REDCap data dictionary?

A REDCap export won't upload as-is. The quickest conversion:

| REDCap column | Becomes |
|---|---|
| Variable / Field Name | `variable_name` |
| Field Label | `description` |

Rename those two columns and the file will upload. Add `dType`, `Unit` and `Categories` afterwards
only if you want the extra suggestions; they're optional.

## 2. Study variables file (Upload Studies page)

| Column | Status | What it holds |
|---|---|---|
| `variable_name` | **Required** | The variable's name as it appears in your study dataset |
| `description` | Optional | What the variable means. **If missing or empty, the AI writes one during Initialise** (using your context PDF, if you supplied one) |

Size limit: 10 MB. Duplicate names produce a warning, not an error.

Working examples: [`example_data/ACE_Uganda/dataset_variables.csv`](../example_data/ACE_Uganda/dataset_variables.csv).

## 3. Example data CSV (optional)

A CSV of real (or realistic) rows from the study, so the AI can see what actual values look like.
Its column names must match the `variable_name` values in the study variables file. Limit: 100 MB.

## 4. Context document PDF (optional)

**One PDF per study**, usually the protocol, the case report forms (CRFs) or a data dictionary.
The AI reads it to write descriptions for variables that don't have one. Consent forms rarely help.

- To use several documents, merge them into a single PDF first.
- **Bigger PDFs make Initialise slower.** Prefer the two or three most informative documents over everything you have.
- Limit: 50 MB. The file must be a real PDF.
