# Evaluation Plan: Metadata Harmonisation Tool

**Document status**: Draft for team discussion   
**Created Date**: 16 June 2026   
**Author**: Atwine Mugume

---

## 1\. Overview

This document describes the evaluation strategy for the Metadata Harmonisation Tool. The evaluation covers four areas: (1) recommendation accuracy against expert ground truth, (2) scalability under increasing dataset size, (3) end-to-end usability including installation, and (4) African Population Ontology (AfPO) coverage. A supplementary sub-experiment within the recommendation accuracy evaluation tests whether RAG-generated descriptions improve mapping outcomes.

The evaluation design draws on established methodologies from comparable tools. Salimi et al. (2025) evaluated embedding-based variable matching using a manually curated ground truth schema (PASSIONATE) across Parkinson's Disease cohorts. Li et al. (2024) used top-k hit ratio and Mean Reciprocal Rank (MRR) to benchmark LLM ensemble models against lexical baselines. CDEMapper (Wang et al., 2025\) used clinician-validated mappings of 494 data elements across four clinical domains. Kokash et al. (2025) measured agreement between LLM-generated mappings and expert assessment, reaching 78–92% agreement. These precedents inform our metric selection and experimental design.

---

## 2\. Evaluation 1: Recommendation Accuracy

### 2.1 Objective

Measure how accurately the tool's ranked recommendations identify the correct target codebook variable for each study variable.

### 2.2 Ground Truth: Available Public Datasets

Before creating ground truth from scratch, we investigated whether published datasets with expert-validated variable mappings are already available. Two strong candidates exist:

**Option A: CDEMapper Evaluation Dataset (recommended first choice)**

- Source: Wang et al. (2025), GitHub repository: [https://github.com/BIDS-Xu-Lab/CDE-Mapping-Tool/tree/main/EvaluationData](https://github.com/BIDS-Xu-Lab/CDE-Mapping-Tool/tree/main/EvaluationData)  
- Contents: 494 data elements across 4 clinical domains (Eye, Stroke, Alzheimer's Disease / Related Dementias, COVID-19), manually mapped to NIH Common Data Element collections by two annotators with disagreements resolved by discussion. 264 entries have finalised gold-standard mappings.  
- Licence: Publicly available on GitHub.  
- Adaptation needed: The gold-standard maps source variables to NIH CDE collections, not to a custom target codebook. To use this with our tool, we would create a target codebook from the mapped NIH CDEs and treat the source variables as the incoming study. The mapping relationships are preserved.  
- Advantage: Ground truth already exists. No expert mapping effort required. Evaluation code (Jupyter notebooks) is also available for reference.

**Option B: PASSIONATE Schema (Salimi et al., 2025\)**

- Source: Zenodo: [https://doi.org/10.5281/ZENODO.10218362](https://doi.org/10.5281/ZENODO.10218362)  
- Contents: Manually curated Parkinson's Disease variable mapping schema covering variables from the GERAS EU and JP cohorts. Designed as a ground truth for embedding-based harmonisation evaluation.  
- Licence: Publicly available on Zenodo.  
- Advantage: Designed specifically for evaluating embedding-based variable matching — closely aligned with our tool's approach.

**Option C: CINECA Synthetic Cohorts (no existing ground truth)**

- Source: [https://www.cineca-project.eu/cineca-synthetic-datasets](https://www.cineca-project.eu/cineca-synthetic-datasets) (CC-BY licence). Africa H3ABioNet v1 specifically: [https://www.cineca-project.eu/synthetic-data/sdc-africa-h3abionet-v1](https://www.cineca-project.eu/synthetic-data/sdc-africa-h3abionet-v1)  
- Contents: Multiple open-access synthetic datasets including Africa H3ABioNet v1 (100 samples based on the H3Africa core phenotype model), CH\_SIB (already bundled with our tool), Canada CHILD, and Europe UK1.  
- Adaptation needed: No expert mappings exist. A domain expert would need to manually map each dataset's variables to the target codebook to create ground truth.  
- Advantage: The Africa H3ABioNet dataset is directly relevant to the DS-I Africa context and may contain ethnicity/population data useful for the AfPO evaluation (Evaluation 4).

**Recommendation**: Use Option A (CDEMapper) as the primary accuracy benchmark since it requires no new expert mapping. Supplement with Option C (CINECA Africa H3ABioNet) to test generalisation to African health data — this requires expert mapping but the dataset is small (manageable effort). The bundled CH\_SIB dataset can serve as a third test case.

**Team action required**: (1) Download and inspect the CDEMapper and PASSIONATE datasets to confirm they are usable with our tool's input format. (2) Decide whether to invest expert mapping effort in the CINECA Africa H3ABioNet dataset. (3) Identify who will adapt the CDEMapper data into our tool's expected CSV format.

### 2.2.1 Creating Your Own Ground Truth (if needed)

If the public datasets above do not cover the domains or variable types relevant to DS-I Africa, you may need to create ground truth from scratch. Follow this procedure:

1. Select 1–2 additional datasets from DS-I Africa consortium partners.  
2. For each dataset, one or more domain experts independently map every study variable to the target codebook. Each variable receives one of three labels: (a) correctly maps to a specific target variable, (b) maps to a target variable but requires transformation, or (c) no valid mapping exists.  
3. Where two experts map the same dataset, compute inter-rater agreement (Cohen's kappa) to establish ground truth reliability. Disagreements are resolved by discussion.  
4. The resulting mapping table becomes the gold standard against which tool output is compared.

### 2.2.2 Does the Number of Variables Matter?

Yes. A dataset with 20 study variables mapped against a codebook of 30 targets is a different test from 200 variables against 30 targets. More study variables increase the chance of ambiguous or overlapping matches, and more target variables give the ranking algorithm more candidates to sort through. To account for this, report accuracy metrics separately per dataset and note the variable counts. If using the CDEMapper data, its four domains range from small to moderately sized, providing natural variation.

### 2.2.1 Instructions for Expert Mappers

> **What you are doing**: You are creating a "correct answer key" for this evaluation. Your mappings will be treated as the ground truth against which the tool's automated recommendations are judged.  
>   
> **What you will receive**: A study variables CSV file (containing variable names and descriptions) and a target codebook CSV file (containing the variables you should map to).  
>   
> **Steps**:  
> 

> 1. Open both files side by side (in Excel, Google Sheets, or any spreadsheet tool).  
> 2. For each variable in the study file, find the best matching variable in the target codebook. Use your domain knowledge — consider what the variable measures, not just its name.  
> 3. Record your mapping in the provided template spreadsheet. For each study variable, fill in:  
>    - **study\_variable\_name**: Copy the exact variable name from the study file.  
>    - **mapped\_codebook\_variable**: The target codebook variable you believe is the correct match. If no reasonable match exists, write "UNMAPPABLE".  
>    - **mapping\_label**: One of three values:  
>      - `direct_match` — The study variable maps directly to the target with no transformation needed.  
>      - `match_with_transformation` — The study variable maps to the target but the values need conversion (e.g., months to years, different category labels).  
>      - `no_match` — No target variable adequately represents this study variable.  
>    - **confidence**: How confident are you in this mapping? Write `high`, `medium`, or `low`.  
>    - **notes**: Any reasoning or caveats (e.g., "variable name is ambiguous but description confirms this is BMI").  
> 4. Work independently. Do not consult other mappers or the tool's recommendations while creating your mappings.  
> 5. There is no time limit, but please note approximately how long the task took you (in minutes).

>   
> **What to look out for**:  
> 

> - Variables with abbreviated or unclear names (e.g., "ht" could mean height or hypertension). Use the description column to disambiguate. If the description is also unclear, flag this in your notes.  
> - Variables that could plausibly map to more than one target. Pick the best match and note the alternative in the notes column.  
> - Variables that exist in the study but have no equivalent in the target codebook. Label these "UNMAPPABLE" — do not force a match.

### 2.3 Metrics

| Metric | Definition | Precedent |
| :---- | :---- | :---- |
| **Top-1 accuracy** | Proportion of variables where the correct target is the tool's first recommendation | Li et al. (2024), Mallya et al. (2025) |
| **Top-3 accuracy** | Proportion where the correct target appears in the top 3 recommendations | Li et al. (2024) |
| **Top-5 accuracy** | Proportion where the correct target appears in the top 5 recommendations | Li et al. (2024) |
| **Mean Reciprocal Rank (MRR)** | Average of 1/rank for the correct target across all variables. MRR \= 1.0 means the correct answer is always ranked first. | Li et al. (2024) reported 0.73; De la Torre (2025) reported 0.98 |
| **Confidence threshold precision** | For each confidence band (Strong ≥80%, Review 60–79%, Verify \<60%), what proportion of recommendations in that band are actually correct? | Novel to this tool |

### 2.4 Sub-Experiment: LLM Stratification

Different LLMs produce different embedding spaces and different generated descriptions. A recommendation that works well with nomic-embed-text may not work as well with text-embedding-3-small, and vice versa. Stratifying the accuracy evaluation across models answers the question: "Does our approach work in general, or only with a specific model?"

**Embedding models to test:**

| Provider | Embedding Model | Notes |
| :---- | :---- | :---- |
| Ollama (local) | nomic-embed-text | Default. Free, runs offline. |
| Ollama (local) | mxbai-embed-large | Alternative open-source embedding model. |
| OpenAI | text-embedding-3-small | Cloud-based. Requires API key. |
| OpenAI | text-embedding-3-large | Higher-dimensional variant. |

**Chat models to test (for RAG description generation):**

| Provider | Chat Model | Notes |
| :---- | :---- | :---- |
| Ollama (local) | llama3.1:8b | Default. Consumer-grade hardware. |
| Ollama (local) | llama3.1:70b | Larger model, requires more capable hardware. |

**Procedure**: For each embedding model, run the full recommendation pipeline on the same dataset and compute Top-1, Top-3, Top-5 accuracy and MRR. For each chat model, run the RAG description generation on the same set of undescribed variables and measure downstream recommendation accuracy. Present results in a matrix (model × metric) so readers can see which combinations perform best.

**Practical note**: You do not need to test every combination of chat model × embedding model. Pick 2–3 embedding models and 2–3 chat models. The most important comparisons are: (a) local default (llama3.1:8b \+ nomic-embed-text) and (b) variation across open-source embedding models to show whether the approach is model-sensitive or robust.

### 2.5 Sub-Experiment: RAG Description Impact

To test whether the RAG pipeline improves recommendation quality, run the recommendation engine under two conditions for any dataset where variables originally lack descriptions:

- **Condition A**: Use RAG-generated descriptions (the tool's default workflow).  
- **Condition B**: Use variable names only (descriptions left blank).

Compare Top-1 accuracy and MRR between conditions. The difference quantifies the RAG pipeline's contribution to recommendation quality.

**Note**: This sub-experiment is only meaningful for datasets where variables lack descriptions. If all variables already have human-authored descriptions, this comparison cannot be made.

### 2.5 Procedure

> **Who runs this**: The evaluation coordinator (not the expert mappers — they must not see the tool's output before completing their own mappings).  
>   
> **Steps**:  
> 

> 1. Load each evaluation dataset into the tool using the Upload Studies page.  
> 2. Run the full pipeline by clicking Initialise. The tool will generate descriptions (if needed), compute embeddings, and produce recommendations.  
> 3. Go to the Map Studies page. For each study variable, the tool displays a ranked list of recommended target variables with confidence scores. **Do not confirm any mappings.** Instead, record the following in a spreadsheet:  
>    - **study\_variable\_name**: The variable being mapped.  
>    - **rank\_1\_recommendation**: The tool's top recommendation.  
>    - **rank\_1\_confidence**: The confidence score (percentage) for the top recommendation.  
>    - **rank\_2\_recommendation** through **rank\_5\_recommendation**: The next four recommendations.  
>    - **rank\_2\_confidence** through **rank\_5\_confidence**: Their confidence scores.  
>    - **gold\_standard\_target**: The correct answer from the expert mapping (Section 2.2).  
>    - **gold\_standard\_rank**: The position at which the correct answer appears in the tool's list. If the correct answer does not appear in the top 10, write "not found".  
>    - **confidence\_band**: Which label the tool assigned to the top recommendation — "Strong", "Review", or "Verify".  
> 4. After recording all variables, compute the metrics in Section 2.3 using the spreadsheet data.  
> 5. For the RAG sub-experiment (Section 2.4), delete the description column from the study variables CSV so that all descriptions are blank, then repeat steps 1–4 from scratch. Compare the two sets of results.

>   
> **What to look out for**:  
> 

> - If the tool's top recommendation matches the gold standard, that counts as a Top-1 hit. If the gold standard appears at rank 3, it counts as a Top-3 hit but not Top-1.  
> - Pay attention to the confidence bands. If a variable is labelled "Strong" but the mapping is wrong, or labelled "Verify" but the mapping is correct, record these — they test whether the confidence labels are trustworthy.  
> - For the RAG sub-experiment, use the exact same dataset both times. The only difference should be the presence or absence of descriptions.

---

## 3\. Evaluation 2: Scalability

### 3.1 Objective

Determine how the tool performs as dataset size increases, and whether it can handle datasets typical of multi-site African health research consortia.

### 3.2 Experimental Design

#### 3.2.1 Variable Count Scaling

Generate synthetic datasets with increasing numbers of variables: 50, 100, 250, 500, and 1,000 variables. Use the existing target codebook (which contains approximately 30 variables) as the mapping target. For each dataset size, measure:

| Metric | What it captures |
| :---- | :---- |
| **Embedding generation time** | Time to embed all study variables (wall-clock, seconds) |
| **Recommendation computation time** | Time to compute ranked recommendations for all variables (wall-clock, seconds) |
| **Full pipeline time** | Total time from initialisation to recommendation output |
| **Peak memory usage** | Maximum resident set size during processing (MB) |

Run each configuration 3 times and report mean and standard deviation to account for variability.

> **Who runs this**: The evaluation coordinator or a developer comfortable with running scripts and reading system monitoring tools.  
>   
> **How to measure wall-clock time**: Use a stopwatch, phone timer, or the system clock. For each measurement:  
> 

> 1. Note the exact start time (e.g., 14:03:22) immediately before clicking the Initialise button.  
> 2. Watch the tool's progress indicators. Note the exact end time when the tool displays the completion message (e.g., "Recommendations generated").  
> 3. Record the elapsed time in seconds. Example: started 14:03:22, finished 14:05:47 \= 145 seconds.  
> 4. If the tool shows separate progress bars for each stage (description generation, embedding, recommendations), record the time for each stage individually as well as the total.

>   
> **How to measure memory usage**: Before starting the tool, open your system's activity monitor (Task Manager on Windows, Activity Monitor on Mac, `htop` or `top` on Linux). Filter for the Python/Streamlit process. Record the peak memory value that appears during processing. If you are comfortable with command-line tools, you can use `psutil` in Python or `/usr/bin/time -v` on Linux for a more precise measurement.  
>   
> **How to generate synthetic datasets**: If you do not have real datasets at every size point, duplicate and rename rows from an existing study variables file to reach the target count. Vary the variable names (e.g., append numbers: "var\_001", "var\_002") so the tool treats them as distinct variables. The descriptions can be copied from the original or left blank (to also test the RAG pipeline at scale).  
>   
> **What to look out for**:  
> 

> - Does the tool crash or freeze at any dataset size? If so, record the size at which it fails and any error messages.  
> - Does the progress bar stall at any particular stage? This identifies bottlenecks.  
> - Close other applications during timing runs to reduce background noise in your measurements.  
> - Repeat each run 3 times. If one run is dramatically different from the others (e.g., twice as slow), note it and check whether something else was using system resources.

#### 3.2.2 Context Document Size Scaling

For the RAG pipeline, vary the size of the input PDF document: 5, 20, 50, and 100 pages. Use a fixed set of 50 variables.

> **How to create PDFs of different lengths**: Take a real study protocol or data dictionary PDF. Use a PDF editor or command-line tool (e.g., `pdftk`) to extract the first 5, 20, 50, and 100 pages into separate files. If the original document is shorter than 100 pages, duplicate its content to reach the target length.  
>   
> **What to measure** (same wall-clock approach as Section 3.2.1):  
> 

> - Time from clicking Initialise to description generation completing (this captures text extraction \+ chunk embedding \+ context retrieval \+ LLM calls).  
> - Total RAG pipeline time.  
> - Note the number of text chunks the tool creates for each PDF size (visible in the tool's logs or terminal output).

#### 3.2.3 AI Provider Comparison

Run the same dataset (e.g., 100 variables) on two provider configurations:

- **Ollama (local)**: Llama 3.1 8B (chat) \+ nomic-embed-text (embeddings), running on a specified hardware configuration (document CPU, RAM, GPU if applicable).  
- **OpenAI (cloud)**: GPT-4 (chat) \+ text-embedding-3-small (embeddings).

>   
> **How to switch providers**: Open the tool's sidebar and change the AI provider setting. Enter the required API key for cloud providers. Verify the connection test passes before running the pipeline.  
>   
> **What to measure**:  
> 

> - Wall-clock time for the full pipeline (same method as Section 3.2.1).  
> - Recommendation accuracy: after running the pipeline with each provider, record the ranked recommendations for each variable and compare against the gold standard from Evaluation 1\. Compute Top-1 accuracy and MRR for each provider.  
> - Note the exact models used (including version strings) and the hardware specification.

>   
> **What to look out for**:  
> 

> - Cloud providers may be faster for embedding generation but introduce network latency. Note your internet speed if possible.  
> - If a provider fails or times out during a run, record the error and the number of variables processed before failure.

**Hardware specification**: Document the exact machine used for benchmarking (CPU model, RAM, GPU if applicable, OS). This is essential for reproducibility.

### 3.2.4 Automated Logging (Internal Instrumentation)

Rather than relying on participants to use stopwatches, we should instrument the tool itself to capture timing and hardware information automatically. This produces more accurate data and reduces user burden — the participant simply runs the tool and sends us the resulting log file.

**What the logging script should capture:**

| Data point | How to capture | When |
| :---- | :---- | :---- |
| **Hardware profile** | CPU model, core count, total RAM, GPU model (if any), OS and version, Python version | Once at tool startup |
| **AI provider and models** | Provider name, chat model name/version, embedding model name/version | Once at initialisation |
| **Stage start/end timestamps** | `time.perf_counter()` before and after each pipeline stage | Per stage |
| **Embedding generation time** | Total time and per-variable average for embedding all study \+ codebook variables | During embedding stage |
| **Recommendation computation time** | Total time for computing all pairwise distances and ranking | During recommendation stage |
| **RAG pipeline time** | Text extraction time, chunking time, chunk embedding time, context retrieval time per variable, LLM call time per variable | During description generation |
| **Variable counts** | Number of study variables, number of codebook variables, number of variables needing RAG descriptions | At initialisation |
| **PDF metadata** | Page count, file size in bytes, number of text chunks created | During RAG preprocessing |
| **Peak memory usage** | `tracemalloc` peak or `psutil.Process().memory_info().rss` sampled at end of each stage | Per stage |
| **Errors and retries** | Any API timeouts, retry attempts, rate limit hits | As they occur |

**Output format**: Write all entries to a single JSON Lines file (`logs/benchmark_log.jsonl`) with timestamps. Each line is a self-contained event. Example:

{"event": "hardware\_profile", "timestamp": "2026-07-01T10:00:00Z", "cpu": "Apple M2 Pro", "cores": 10, "ram\_gb": 16, "gpu": "Apple M2 Pro (integrated)", "os": "macOS 14.5", "python": "3.11.9"}

{"event": "stage\_start", "timestamp": "2026-07-01T10:00:05Z", "stage": "embedding\_generation", "study": "CH\_SIB", "n\_study\_vars": 50, "n\_codebook\_vars": 30}

{"event": "stage\_end", "timestamp": "2026-07-01T10:01:45Z", "stage": "embedding\_generation", "duration\_seconds": 100.3, "peak\_memory\_mb": 412}

**Implementation note**: This logging should be added to the tool's codebase as a lightweight module that runs alongside the existing pipeline. It should not affect performance. The user's only action is to locate and send the log file after the run.

**Team action required**: Decide whether to implement the logging module before running evaluations (recommended — saves significant manual effort) or fall back to the manual stopwatch approach described in the participant instructions.

### 3.2.5 Hardware Recording (for Participants Without Internal Logging)

If the automated logging module is not yet implemented, participants must record their hardware manually. Include this form at the start of any scalability test:

> **Machine Specification Form** (fill in before starting any timed runs)  
> 

| Item | Your machine |
| :---- | :---- |
| Computer make and model (e.g., "Dell XPS 15 9530") |  |
| Operating system and version (e.g., "Windows 11 23H2", "Ubuntu 22.04") |  |
| CPU model (e.g., "Intel i7-13700H", "Apple M2 Pro") |  |
| Number of CPU cores |  |
| Total RAM (GB) |  |
| GPU model, if any (e.g., "NVIDIA RTX 4060", "None") |  |
| GPU VRAM, if applicable (GB) |  |
| Internet connection speed, if testing cloud providers (e.g., "50 Mbps down") |  |
| Python version (run `python --version` in terminal) |  |
| Ollama version, if applicable (run `ollama --version`) |  |

>   
> **How to find this information**:  
> 

> - **Windows**: Settings → System → About. For GPU: Task Manager → Performance → GPU.  
> - **Mac**: Apple menu → About This Mac. For GPU: same screen.  
> - **Linux**: Run `lscpu`, `free -h`, and `lspci | grep -i vga` in terminal.

>   
> This information is essential. Two identical datasets can produce very different timing results on different hardware. Without this data, the timing numbers are not interpretable.

### 3.3 Reporting

Present results as line plots (variable count on x-axis, time on y-axis) with error bars. If scaling is approximately linear, state this explicitly. If there are bottlenecks (e.g., embedding generation dominates at large scale), identify them.

---

## 4\. Evaluation 3: End-to-End Usability

### 4.1 Objective

Answer the question: "If someone picks up this tool tomorrow, can they install it and harmonise their data?"

### 4.2 Participants

Recruit 2–5 participants who were not involved in building the tool. Ideal participants are researchers or data managers in the DS-I Africa consortium or similar health research settings. Participants should have basic technical competence (comfortable with CSV files and command-line/Docker basics) but no prior experience with this tool.

**Team action required**: Identify and recruit participants.

### 4.3 Task Design

Each participant performs the same structured task sequence, working independently with only the tool's README and documentation for guidance.

#### Phase 1: Installation

Participants install the tool from scratch following the README instructions. Two installation paths should be tested:

- **Path A: Docker installation** — Pull and run the Docker container.  
- **Path B: Local Python installation** — Clone the repository, install dependencies, configure Ollama, run the Streamlit app.

You will be assigned one of these paths. If time permits, you may try both.

> **Instructions for Participants — Installation**  
>   
> **Before you begin**:  
> 

> 1. Open a blank document or the provided "Installation Log" template. You will use this to take notes throughout.  
> 2. Start a timer on your phone or note the current time on your clock (e.g., "Started at 10:15 AM"). You will stop it when the tool is fully running in your browser.  
> 3. Make sure you have a stable internet connection (needed to download the tool and AI models).

>   
> **What to do**:  
> 

> 1. Open the tool's README file (you will be given a link to the GitHub repository).  
> 2. Follow the installation instructions for your assigned path (Docker or Local Python). Use only the README — do not search for help online or ask the team.  
> 3. Your goal is to see the tool's home page running in your web browser.

>   
> **What to record as you go**:  
> 

> - **Timestamps**: Note the time when you start each major step (e.g., "10:15 — started cloning repository", "10:18 — started installing dependencies", "10:25 — started downloading Ollama models").  
> - **Errors**: If something goes wrong (an error message, a command that does not work, a step that is confusing), write down exactly what happened. Copy and paste the error message if possible. Note whether you were able to resolve it yourself or got stuck.  
> - **Confusion points**: If a step in the README is unclear, too vague, or missing information, note which step and what was confusing. For example: "Step 3 says 'configure your environment' but doesn't say what to put in the .env file."  
> - **End time**: When the tool's home page appears in your browser, stop your timer and record the total time.

>   
> **After installation, fill in this summary**:  
> 

| Question | Your answer |
| :---- | :---- |
| Did the tool start successfully? (yes/no) |  |
| Total installation time (minutes) |  |
| How many errors did you encounter? |  |
| Describe each error briefly |  |
| Which README steps were unclear? |  |
| What operating system are you using? (Windows/Mac/Linux \+ version) |  |
| Installation path (Docker / Local Python) |  |

>   
> **Important**: If you get completely stuck and cannot proceed after 15 minutes on a single step, record where you got stuck and move on to Phase 2 using a pre-installed version that we will provide as a backup.

#### Phase 2: Harmonisation Task

Once installed, each participant completes a full harmonisation cycle using a provided test dataset (e.g., CH\_SIB).

> **Instructions for Participants — Harmonisation Task**  
>   
> **Before you begin**:  
> 

> 1. You will be given a ZIP file containing test data: a target codebook (CSV), study variables (CSV), example data (CSV), and a context PDF document. Extract these files to a folder on your computer.  
> 2. Open your "Task Log" template (provided). You will record timestamps and observations throughout.  
> 3. Start your timer or note the current time.

>   
> **What to do — follow these steps in order**:  
>   
> **Step 1: Upload Target Codebook**  
> 

> - In the tool, navigate to the "Upload Codebook" page.  
> - Upload the file `target_variables.csv` from the test data.  
> - Note the time: \_\_\_\_  
> - Did anything go wrong? (yes/no, describe if yes): \_\_\_\_

>   
> **Step 2: Upload Study Data**  
> 

> - Navigate to the "Upload Studies" page.  
> - Enter a study name (use "test\_study").  
> - Upload the study variables CSV, the example data CSV, and the context PDF.  
> - Note the time: \_\_\_\_  
> - Did anything go wrong? (yes/no, describe if yes): \_\_\_\_

>   
> **Step 3: Initialise**  
> 

> - Navigate to the "Initialise" page and click the button to start processing.  
> - **Important timing point**: Note the exact time you click Initialise: \_\_\_\_  
> - Wait for processing to complete. Note the exact time it finishes: \_\_\_\_  
> - Elapsed time for initialisation: \_\_\_\_ seconds  
> - Did you see any error messages during processing? (yes/no, describe if yes): \_\_\_\_

>   
> **Step 4: Map Study Variables**  
> 

> - Navigate to the "Map Studies" page.  
> - For each variable the tool presents, review the recommended mappings and select the one you think is correct.  
> - Work through all variables. For each one, use your judgement — there is no right or wrong answer from your perspective. We will compare your choices to an expert answer key later.  
> - **What to look out for while mapping**:  
>   - Are the recommendations sensible? Do the top suggestions feel relevant to the variable?  
>   - Is the confidence label (Strong/Review/Verify) helpful? Does it match your own sense of how obvious the mapping is?  
>   - Is the interface clear about what to do next, or do you find yourself guessing?  
>   - If the tool offers a transformation option, try applying one (e.g., a unit conversion or category relabelling). Note whether the preview made sense.  
>   - If you see an ethnicity-related variable and an AfPO lookup appears, try using it. Note whether the results were meaningful.  
> - Note the time when you finish mapping all variables: \_\_\_\_

>   
> **Step 5: Download Results**  
> 

> - Navigate to the "Download Results" page and download the output file.  
> - Note the time: \_\_\_\_  
> - Open the downloaded file and check that it contains your mappings. Does it look complete? (yes/no): \_\_\_\_

>   
> **After completing all steps, fill in this summary**:  
> 

| Question | Your answer |
| :---- | :---- |
| Did you complete all 5 steps? (yes/no, note where you stopped if not) |  |
| Total time from Step 1 to Step 5 (minutes) |  |
| How many variables did you map? |  |
| How many times did you change your mind and re-select a mapping? |  |
| How many times did you need to ask someone for help? |  |
| What was confusing? |  |
| What worked well? |  |
| Did the tool crash or freeze at any point? (describe) |  |

#### Phase 3: Post-Task Questionnaire

> **Instructions for Participants — Questionnaire**  
>   
> Please complete this questionnaire immediately after finishing the harmonisation task, while the experience is fresh.  
>   
> **Part A: System Usability Scale (SUS)**  
>   
> For each statement below, circle a number from 1 (Strongly Disagree) to 5 (Strongly Agree). Do not overthink your answers — give your first reaction.  
> 

| \# | Statement | 1 | 2 | 3 | 4 | 5 |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | I think that I would like to use this tool frequently. |  |  |  |  |  |
| 2 | I found the tool unnecessarily complex. |  |  |  |  |  |
| 3 | I thought the tool was easy to use. |  |  |  |  |  |
| 4 | I think that I would need the support of a technical person to be able to use this tool. |  |  |  |  |  |
| 5 | I found the various functions in this tool were well integrated. |  |  |  |  |  |
| 6 | I thought there was too much inconsistency in this tool. |  |  |  |  |  |
| 7 | I would imagine that most people would learn to use this tool very quickly. |  |  |  |  |  |
| 8 | I found the tool very cumbersome to use. |  |  |  |  |  |
| 9 | I felt very confident using the tool. |  |  |  |  |  |
| 10 | I needed to learn a lot of things before I could get going with this tool. |  |  |  |  |  |

>   
> **Part B: Open-Ended Questions**  
>   
> Please answer in your own words. There are no right or wrong answers — we want your honest experience.  
> 

> 1. What was the most confusing part of the entire process (installation and/or harmonisation)?  
> 2. Was there a point where you were unsure what to do next? If so, what were you trying to do?  
> 3. Did the tool's recommendations match your expectations? Were they helpful, or did you feel you were overriding them most of the time?  
> 4. If you could change one thing about the tool, what would it be?  
> 5. Would you use this tool for your own harmonisation work? Why or why not?  
> 6. How does this compare to how you currently harmonise data (if applicable)? Is it faster, slower, easier, harder?

>   
> **Part C: Background (for analysis purposes)**  
> 

| Question | Your answer |
| :---- | :---- |
| What is your role? (e.g., researcher, data manager, statistician) |  |
| How many years of experience do you have working with health research data? |  |
| Have you done data harmonisation before? (never / once or twice / regularly) |  |
| How comfortable are you with command-line tools? (not at all / somewhat / very) |  |
| How comfortable are you with Docker? (not at all / somewhat / very) |  |

### 4.4 Analysis

Report SUS scores per participant and the group mean. Summarise qualitative feedback thematically. Identify recurring pain points — these become actionable improvement items regardless of the paper's evaluation section.

---

## 5\. Evaluation 4: AfPO Coverage

### 5.1 Objective

Measure the proportion of real-world African population and ethnicity values that the tool's AfPO integration can match, and document gaps for ontology improvement.

### 5.2 Data Requirements

Obtain 1–3 datasets containing ethnicity, population, tribe, or ancestry columns with real values (not synthetic). These may come from DS-I Africa consortium partners or publicly available African cohort studies.

**Team action required**: Identify datasets with ethnicity/population columns that can be used for this evaluation.

### 5.3 Metrics

| Metric | Definition |
| :---- | :---- |
| **Match rate** | Proportion of unique input values that receive an exact AfPO match |
| **Gap rate** | Proportion of unique values with no AfPO match (1 − match rate) |
| **Gap term inventory** | Full list of unmatched terms, categorised by likely cause: spelling variant, missing synonym, genuinely absent from AfPO |
| **Coverage by dataset** | Match rate reported per dataset, to show variation across regions/studies |

### 5.4 Procedure

> **Who runs this**: The evaluation coordinator or a team member with access to the ethnicity datasets.  
>   
> **Steps**:  
> 

> 1. Load a dataset into the tool that contains an ethnicity, population, or ancestry column.  
> 2. Upload the target codebook and study variables as normal. Include example data that contains the ethnicity column.  
> 3. During the mapping step, map the study's ethnicity variable to the corresponding target codebook variable (e.g., "ethnicity" → "ethnicity"). The tool should automatically trigger the AfPO lookup interface.  
> 4. The AfPO lookup will display the unique values from the ethnicity column and attempt to match each one against the AfPO ontology.  
> 5. For each value, record in a spreadsheet:  
>    - **input\_value**: The ethnicity/population term from the dataset (e.g., "Baganda", "Zulu", "Yoruba").  
>    - **matched**: yes or no.  
>    - **afpo\_id**: If matched, the AfPO identifier returned (e.g., "AfPO:0000042").  
>    - **afpo\_label**: If matched, the canonical label returned.  
>    - **gap\_category** (fill in after the run): If unmatched, categorise the term as one of:  
>      - `spelling_variant` — The population exists in AfPO but under a different spelling (e.g., "Bagisu" vs "BaGisu").  
>      - `missing_synonym` — The population exists in AfPO but this particular name/synonym is not listed.  
>      - `genuinely_absent` — The population does not appear in AfPO at all.  
> 6. Repeat for each dataset.  
> 7. Compute match rate and gap rate per dataset.

>   
> **What to look out for**:  
> 

> - Capitalisation and spelling differences. If a term fails to match, try checking AfPO manually (search the OBO file or the AfPO GitHub) to see if a slightly different spelling exists. This helps distinguish spelling variants from genuinely missing terms.  
> - Terms that are broad categories (e.g., "African", "Black") rather than specific population names. These may not be in AfPO's scope. Note them separately.  
> - If the tool surfaces the gap reporting button (to open a GitHub issue), try clicking it for at least one unmatched term to verify the feature works. Note whether the pre-filled issue template is accurate.

### 5.5 Contribution to AfPO

Unmatched terms that represent genuinely missing populations can be submitted as GitHub issues to the AfPO repository using the tool's built-in gap reporting feature. Document how many terms were submitted and whether any were accepted into subsequent AfPO releases. This positions the evaluation as a contribution to the ontology itself.

---

## 6\. Summary of Required Resources

| Resource | What is needed | Status |
| :---- | :---- | :---- |
| **Expert mappers** | 1–2 domain experts to create gold-standard variable mappings | To be recruited |
| **Evaluation datasets** | 2–3 datasets (at least 1 beyond CH\_SIB); ideally with ethnicity columns | To be identified |
| **Usability participants** | 2–5 researchers unfamiliar with the tool | To be recruited |
| **Hardware for benchmarking** | A documented machine for reproducible timing measurements | Available (specify) |
| **Ethnicity data** | Real-world population/ethnicity columns for AfPO evaluation | To be identified |

---

## 7\. Evaluation Timeline (Suggested)

| Week | Activity |
| :---- | :---- |
| 1 | Finalise datasets, recruit expert mappers and usability participants |
| 2–3 | Expert mappers create gold-standard variable mappings |
| 4 | Run Evaluation 1 (recommendation accuracy) and Evaluation 2 (scalability) |
| 5 | Run Evaluation 3 (usability study) and Evaluation 4 (AfPO coverage) |
| 6 | Analyse results, write results section |

---

## 8\. How to Submit Your Results

> **For all participants (expert mappers, usability testers, evaluation coordinators)**:  
> 

> 1. Collect all your files: completed spreadsheets, log documents, questionnaire responses, and any screenshots of errors.  
> 2. Name your files using this convention: `[your_name]_[evaluation_number]_[description]`. For example: `jane_eval3_installation_log.xlsx`, `peter_eval1_gold_standard_mappings.csv`.  
> 3. Send all files to \[TO BE FILLED — coordinator email\] with the subject line "MHT Evaluation — \[Your Name\] — \[Evaluation Number\]".  
> 4. If you have questions during the evaluation, contact \[TO BE FILLED — coordinator name and contact\] before making assumptions. Record any questions you had even if you resolved them yourself — this helps us improve the documentation.

>   
> **Deadlines**: \[TO BE FILLED based on timeline agreed with team\]

---

## 9\. References

- De la Torre, L. et al. (2025). Transformer-based pipeline for clinical lab unit harmonization. (MRR 0.98 on 7.5B entries)  
- Kokash, N. et al. (2025). Ontology- and LLM-based data harmonization for federated learning in healthcare. *Frontiers in Digital Health*. (78–92% expert agreement)  
- Li, Z. et al. (2024). A natural language processing approach to support biomedical data harmonization: Leveraging large language models. *PLOS One*. (MRR 0.73, top-k accuracy)  
- Mallya, S. et al. (2025). NLP-based harmonization in cardiovascular cohorts. (top-k accuracy, AUC)  
- Richesson, R. et al. (2018). D2Refine Platform usability study. *JMIR Medical Informatics*.  
- Salimi, Y. et al. (2025). Evaluating language model embeddings for Parkinson's disease cohort harmonization. *Scientific Reports*. (PASSIONATE gold standard)  
- Wang, Y. et al. (2025). CDEMapper: Enhancing NIH Common Data Element Normalization using Large Language Models. *JAMIA*. (494 data elements, clinician validation)

