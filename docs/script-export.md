# Transform your full dataset with a downloaded script

The app only transforms the small example-data file you uploaded with each study. If you have the **full dataset**
(too big, or too sensitive, to upload), download a small Python script from the app and run it on your own computer.
It applies the same mappings and transformations you confirmed in Map Studies. Your full data never goes through the app.

This is a first, rough version. It repeats exactly what the app does on the example data and tells you what it could not convert.

## What you need

- Python 3.8 or newer.
- pandas 1.5 or newer: `pip install pandas`.
- The script was written and tested against pandas 2.2 on Python 3.12. Older versions are accepted but untested.

## Get the script

1. Open **Download Results** and tick the study.
2. Click **Download script** in that study's card. You get `transform_<study>.py`.

The button works once at least one variable is marked **Successfully mapped**. The script holds your mappings only, never any data.
If you change a mapping later, download the script again.

## Run it

```
python transform_CH_SIB.py --input my_full_data.csv --output out.csv
```

| Option | What it does |
|---|---|
| `--input` | Your full data file (CSV). Required. |
| `--output` | Where the transformed CSV is written. Required. |
| `--report BASE` | Writes the report to `BASE.txt` and `BASE.json`. Default: the output name plus `_report` (`out_report.txt`). |
| `--sep` | Column separator. By default the script guesses between comma, semicolon, tab and pipe. |
| `--encoding` | Text encoding. By default it tries UTF-8 (a BOM is fine) and falls back to latin-1 with a printed notice. |

Large files are read in chunks of 50,000 rows, so memory use stays flat. The file is read three times (work out column types, count results, write the output), so very large files take a few times longer than a single read.

## What you get

Worked example with `example_data/CH_SIB` (mappings: `sbsmk` as a lookup rule, `wt` times 2.2046, `age` and `pt` copied):

```
$ python transform_CH_SIB.py --input example_data.csv --output script_out.csv
Using separator "," and encoding utf-8-sig.
Study CH_SIB: 10 rows, 4 variables written to script_out.csv
Successes: 40, errors: 0, cells left empty because they could not be converted: 0, variables skipped: 0
Warning: No transformation for age -> Age; copied through.
Warning: No transformation for pt -> Participant ID; copied through.
Results report (may contain participant values, keep it private): script_out_report.txt and script_out_report.json
```

The output CSV was identical, cell for cell, to the app's own `CH_SIB_transformed.csv` for the same input:

```
Smoking Status,Weight lb,Age,Participant ID
Former,173.28155999999998,64,FAKE2190
Smoker,178.13168000000002,40,FAKE5126
Never,146.60590000000002,55,FAKE4118
```

The columns are named after the codebook variables, in the same order as the app's transformed CSV.

## The results report

After every run the script writes `<output>_report.txt` (for people) and `<output>_report.json` (for programs). It says:

- per variable: the rule used (math, lookup, or none), the output column, how many rows were converted, came out empty, or were errors;
- for lookup rules: every value the rule had never seen, with how many rows had it (for example `"X" appeared 42 times, not in the rule`). Those cells are left empty. The list shows the 50 most frequent values and says how many more there were;
- for math rules and plain copies: the first 5 input values that could not be converted;
- variables that were skipped, and why (source column not found in your file, or two variables mapped to the same output column);
- the same `Validation Report` lines the app writes, so you can compare.

**The report contains raw values from your data and may hold participant information.** The warning is printed at the top of the file.
It is saved only on your computer and the app never receives it. Keep it as private as the data.

## When something goes wrong

| Message or exit code | Meaning |
|---|---|
| exit 0 | Done. Check the report for empty cells. |
| exit 1 | The output or report could not be written (folder missing, no permission, file open elsewhere). |
| exit 2, "Input file not found" or "empty" | Wrong path, or an empty file. |
| exit 2, "Only one column was found" | The separator guess was wrong. Re-run with `--sep ";"` (or the separator your file uses). |
| exit 2, "text looks garbled" or "could not be decoded" | Re-run with `--encoding cp1252`, `latin-1` or `utf-16`. |
| exit 2, "None of the mapped columns were found" | The file is not the study's data, or the column names differ. Nothing is written except the report. |
| `Source column missing: <name>` (warning) | That variable is skipped. The rest still runs. |

A variable whose transformation instruction is invalid does not stop the run: each of its cells is counted as an error and left empty, as in the app.

## How it matches the app

The conversion rules are copied from the app (`backend/core/transformation_utils.py` and `transform_engine.py`): only
`+ - * /`, unary minus, numbers and the name `x`; `eval` and `exec` are never used. A test runs the in-app engine and the
generated script on the same input and requires the outputs to match cell for cell (`tests/test_script_parity.py`).

Study names, variable names and instructions are written into the script as JSON data, never as code, so a hostile
name or instruction cannot run anything (`tests/test_script_behaviour.py`).

Known small differences:

- If a variable has an unknown transformation type, the app repeats its warning once per row; the script says it once.
- A true/false column that also has empty cells may be read differently from the app (the app keeps Python booleans, the script reads text).
- On a very large file the app reads everything at once, and pandas may then mix types within one column; the script reads in chunks but fixes each column's type first, so results can differ for such mixed columns.

## Not in this version

Date handling, "treat 999 as empty" rules, combining columns, a dry-run mode, other languages (R, SAS, Stata) and running the script from inside the app.
