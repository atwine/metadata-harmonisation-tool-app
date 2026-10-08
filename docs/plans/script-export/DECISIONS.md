# Decisions for the owner

These are the owner's calls. Devin does not choose. Fill in the **Answer** line, or write
"recommended" to accept the suggestion. Phase 1 onward is blocked until D1 to D5 are answered.

## D1. What does the researcher download?
- A. One `.py` file with the mappings embedded as a JSON block. One file to move around. *(Recommended)*
- B. A `.py` file plus a separate `mappings.json`. The mappings can be edited by hand, but two files can get out of sync.
- C. A ZIP holding the script, mappings and a short README.

Answer: ______

## D2. What must be installed on the researcher's machine?
- A. Python 3 only (standard library `csv` module). Nothing to install, but slower and no pandas-style dtype handling; parity has to be matched by hand.
- B. Python 3 plus pandas. Matches the app's behaviour most easily, but one `pip install`. *(Recommended)*

Answer: ______

## D3. Share code with the in-app engine, or copy it?
- A. Copy the small conversion helpers into the generated script, leave the engine alone. Lowest risk to the app. Parity test guards drift. *(Recommended)*
- B. Move the helpers into one shared module that both use. No drift, but changes shared code the whole app relies on (needs the blast-radius check).

Answer: ______

## D4. One script per study, or one for all selected studies?
- A. One script per study, with the study's name in the file name. Matches how the data arrives (one file per study). *(Recommended)*
- B. One script holding all selected studies, picked with `--study`.

Answer: ______

## D5. What do the script's error messages look like?
- A. Same wording as the app's validation report. *(Recommended)*
- B. New, shorter wording for the command line.

Answer: ______

## D6. Does this go to the testing build too? (not blocking)
- A. Not yet. Decide after testers have used the app. *(Recommended)*
- B. Yes, copy it over with `git cherry-pick -x` once it is merged to development and staging.

Answer: ______
