# FoodLens LaTeX Toolchain and Compilation Survey Report

**Specialist Role:** LaTeX Toolchain Survey Specialist  
**Working Directory:** `c:\Projects\foodlens-version-2\.agents\explorer_survey_3`  
**Date/Timestamp:** 2026-09-21T16:18:00Z  

---

## Executive Summary

An exhaustive investigation of the LaTeX compilation environment, pdflatex/bibtex toolchain on Windows, package dependencies, document structure, and build sequence was conducted for the FoodLens IEEE manuscript (`c:\Projects\foodlens-version-2\paper\main.tex`).

Key findings:
1. **Toolchain Availability**: `pdflatex` (MiKTeX-pdfTeX 4.23, pdfTeX 3.141592653-2.6-1.40.28) and `bibtex` (MiKTeX-BibTeX 4.2, BibTeX 0.99e) from MiKTeX 25.12 (64-bit) are installed and fully accessible in the system PATH on Windows.
2. **Current Compilation Status**: Compiling `paper/main.tex` in its current unmodified state fails with exit code 1 due to:
   - **Line 146**: Missing math mode opening delimiter in `\caption{Full  \times 101$ ...}` causing `! Missing $ inserted.`.
   - **Line 171**: Truncated math mode expressions `\times 3$` and `\times 2$` causing `! Missing $ inserted.`.
   - **Line 139 / Label Mismatch**: `Table~\ref{tbl:smoke}` references a non-existent label (`tbl:confused` exists in `tables/table_confused_classes.tex`).
   - **Zero In-Text Citations**: `main.tex` loads `\usepackage{cite}` and `\bibliography{references}` but contains 0 `\cite{...}` commands. This causes `bibtex main` to fail with exit code 1 (`I found no \citation commands---while reading file main.aux`) and generate an empty bibliography that triggers `! LaTeX Error: Something's wrong--perhaps a missing \item.` in subsequent pdflatex runs.
   - **Missing `url` Package**: `references.bib` contains URLs with unescaped underscores (`datasets_extra`, `_modules`). Without `\usepackage{url}` in the preamble, `IEEEtran`'s fallback `\url` command causes TeX to treat underscores as subscript commands outside math mode, triggering fatal syntax errors.
3. **Assets and Package Integrity**:
   - All 5 figures referenced exist in both high-resolution PDF (vector/embedded) and PNG formats in `paper/figures/`.
   - All 4 included table fragments exist in `paper/tables/`.
   - Global packages (`IEEEtran.cls`, `IEEEtran.bst`, `cite`, `amsmath`, `booktabs`, `tikz`, etc.) are pre-installed in MiKTeX and load without package installation errors.
4. **Clean Build Sequence Verified**: In an isolated test workspace (`.agents/explorer_survey_3/build_test`), fixing the four syntax/preamble issues and applying a standard 4-pass build sequence resulted in **exit code 0 across all steps** and generated a clean 8-page IEEE-compliant PDF.
5. **Environment Idiosyncrasy**: The Windows environment runs **PowerShell 5.1**, where the `&&` operator is a syntax error (`The token '&&' is not a valid statement separator in this version.`). Chained execution requires either semicolon checks (`cmd1; if ($LASTEXITCODE -eq 0) { cmd2 }`) or delegation to `cmd /c`.

---

## 1. Toolchain and Environment Inventory

### 1.1 Binary Locations and Versions

| Binary | Exact Filesystem Path | Version Details | Engine / Distribution |
|---|---|---|---|
| `pdflatex.exe` | `C:\Users\Admin\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe` | MiKTeX-pdfTeX 4.23 (pdfTeX 3.141592653-2.6-1.40.28) | MiKTeX 25.12 (64-bit) |
| `bibtex.exe` | `C:\Users\Admin\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe` | MiKTeX-BibTeX 4.2 (BibTeX 0.99e) | MiKTeX 25.12 (64-bit) |
| `kpsewhich.exe`| `C:\Users\Admin\AppData\Local\Programs\MiKTeX\miktex\bin\x64\kpsewhich.exe`| MiKTeX 25.12 | Kpathsea path resolver |
| `initexmf.exe` | `C:\Users\Admin\AppData\Local\Programs\MiKTeX\miktex\bin\x64\initexmf.exe` | MiKTeX 25.12 | MiKTeX Configuration Manager |
| `mpm.exe` | `C:\Users\Admin\AppData\Local\Programs\MiKTeX\miktex\bin\x64\mpm.exe` | MiKTeX Package Manager 4.5 | MiKTeX Package Manager |

### 1.2 MiKTeX System Configuration
- **Operating System:** Windows 10.0.26200 (Build 26100.9444)
- **PowerShell Version:** 5.1.26100.9444 (`$PSVersionTable.PSVersion`)
- **Installation Mode:** User install (`C:\Users\Admin\AppData\Local\Programs\MiKTeX`)
- **Configuration Root:** `C:\Users\Admin\AppData\Roaming\MiKTeX`
- **Data Root:** `C:\Users\Admin\AppData\Local\MiKTeX`
- **Shared Setup:** No (Single user, non-admin runtime)
- **Diagnostic Warning:** `pdflatex: major issue: So far, you have not checked for MiKTeX updates.`
  *(Note: Emitted to standard error on execution; does not halt execution or alter exit codes when syntax is clean).*

---

## 2. Directory and File Inspection (`paper/`)

The manuscript directory `c:\Projects\foodlens-version-2\paper\` was comprehensively inspected.

### 2.1 File Catalog

```
c:\Projects\foodlens-version-2\paper\
├── FoodLens_Project_Content.md      # Full source project reference content (21,270 bytes)
├── Paper.md                         # Markdown transcription of original paper (30,931 bytes)
├── main.tex                         # IEEE LaTeX manuscript (17,573 bytes, 212 lines)
├── references.bib                   # BibTeX bibliographic database (2,614 bytes, 66 lines)
├── main.aux, main.bbl, main.blg     # Intermediate TeX artifacts from previous compilation
├── main.log                         # Compilation log from previous run (33,655 bytes)
├── main.pdf                         # Output PDF generated from previous run (1,512,187 bytes)
├── figures/                         # Figures directory (10 files)
│   ├── fig_confused_pair.pdf        # Vector comparison: steak vs filet mignon (14,204 bytes)
│   ├── fig_confused_pair.png        # Raster version (40,912 bytes)
│   ├── fig_confusion_full.pdf       # 101x101 Confusion Matrix (87,399 bytes)
│   ├── fig_confusion_full.png       # Raster version (509,743 bytes)
│   ├── fig_misclassified.pdf        # Visual examples of misclassifications (922,308 bytes)
│   ├── fig_misclassified.png        # Raster version (3,093,653 bytes)
│   ├── fig_top3_example.pdf         # Top-3 UI output preview (212,722 bytes)
│   ├── fig_top3_example.png         # Raster version (222,183 bytes)
│   ├── fig_warning_curve.pdf        # Calibration warning curve (18,292 bytes)
│   └── fig_warning_curve.png        # Raster version (103,694 bytes)
└── tables/                          # LaTeX table fragments (5 files)
    ├── table_test_performance.tex   # Overall classification metrics (461 bytes, label tbl:testperf)
    ├── table_per_class.tex          # 15 Best / 15 Worst class metrics (2,237 bytes, label tbl:perclass)
    ├── table_confused_classes.tex   # Top confused dish pairs (598 bytes, label tbl:confused)
    ├── table_worst_classes.tex      # Worst 10 classes by recall (498 bytes, label tbl:worst)
    └── classification_report_full.txt # Complete 101-class sklearn report (6,934 bytes)
```

### 2.2 Class and Style File Resolution
- **IEEE Document Class**: `\documentclass[conference]{IEEEtran}`
  - Resolved by MiKTeX from: `C:/Users/Admin/AppData/Local/Programs/MiKTeX/tex/latex/ieeetran/IEEEtran.cls` (v1.8b, 2015/08/26).
  - No local copy is needed in `paper/`.
- **BibTeX Style File**: `\bibliographystyle{IEEEtran}`
  - Resolved by MiKTeX from: `C:/Users/Admin/AppData/Local/Programs/MiKTeX/bibtex/bst/ieeetran/IEEEtran.bst` (v1.14, 2015/08/26).
  - No local copy is needed in `paper/`.
- **Preamble Packages Loaded**:
  - `cite`
  - `amsmath`, `amssymb`, `amsfonts`
  - `algorithmic`
  - `graphicx`
  - `textcomp`
  - `xcolor`
  - `booktabs`
  - `longtable`
  - `tikz` (with libraries: `shapes.geometric`, `arrows.meta`, `positioning`, `fit`, `backgrounds`)
  - `lipsum`
  All packages above are present in the MiKTeX installation and load with 0 missing-package prompts.

---

## 3. Compilation Failure Analysis on Current `paper/main.tex`

When executing `pdflatex -interaction=nonstopmode main.tex` in `paper/`, the compiler halts with exit code 1. A detailed analysis of all errors and warnings follows:

### 3.1 Error 1: Broken Math Mode in Caption (Line 146)
- **Code snippet**:
  ```latex
  145: \makebox[\textwidth][c]{\includegraphics[width=1.1\textwidth]{figures/fig_confusion_full.pdf}}
  146: \caption{Full  \times 101$ confusion matrix for the production EfficientNetB0 model. The strong diagonal indicates robust general performance, while off-diagonal clusters highlight challenging inter-class similarities.}
  147: \label{fig:confmatrix}
  ```
- **Error in Log**:
  ```
  ! Missing $ inserted.
  <inserted text> $
  l.146 ...ht challenging inter-class similarities.}
  ```
- **Root Cause**: The string `Full  \times 101$` uses the math-only operator `\times` in text mode, and is missing the opening `$101`.
- **Fix**: Change `Full  \times 101$` to `Full $101 \times 101$`.

### 3.2 Error 2: Broken Math Mode in Convolutions Description (Line 171)
- **Code snippet**:
  ```latex
  171: A custom, from-scratch 5-layer Convolutional Neural Network was constructed as a baseline. The architecture utilized successive  \times 3$ convolutions, ReLU activations, and  \times 2$ Max Pooling layers, culminating in a Global Average Pooling layer and a fully connected dense output.
  ```
- **Error in Log**:
  ```
  ! Missing $ inserted.
  <inserted text> $
  l.171 ... architecture utilized successive  \times
                                                     3$ convolutions, ReLU act...
  ! Missing $ inserted.
  <inserted text> $
  l.171 ...nvolutions, ReLU activations, and  \times
                                                     2$ Max Pooling layers, cu...
  ```
- **Root Cause**: ` \times 3$` and ` \times 2$` have missing opening delimiters and numbers.
- **Fix**: Change to `$3 \times 3$` and `$2 \times 2$`.

### 3.3 Error 3: Zero In-Text Citations & Empty Bibliography Loop (Line 208-209)
- **Code snippet**:
  ```latex
  208: \bibliographystyle{IEEEtran}
  209: \bibliography{references}
  ```
- **BibTeX Error**:
  ```
  This is BibTeX, Version 0.99e (MiKTeX 25.12)
  The top-level auxiliary file: main.aux
  The style file: IEEEtran.bst
  I found no \citation commands---while reading file main.aux
  Done.
  (There was 1 error message)
  ```
- **pdflatex Error on subsequent run**:
  ```
  (main.bbl
  ! LaTeX Error: Something's wrong--perhaps a missing \item.
  l.24 \end{thebibliography}
  )
  ```
- **Root Cause**: There are zero `\cite{...}` commands in `main.tex`. `main.aux` has no `\citation` entries. BibTeX fails with exit code 1 and writes an empty `\begin{thebibliography}{}\end{thebibliography}` without any `\bibitem`. When `pdflatex` processes the empty environment, LaTeX throws `! LaTeX Error: Something's wrong--perhaps a missing \item.`.
- **Fix**: Add in-text citations as required by R2 (e.g. `\cite{food101}`, `\cite{suddul2023}`, etc.) or `\nocite{*}`. Once `\bibitem` entries exist, `bibtex` and `pdflatex` succeed without errors.

### 3.4 Error 4: Missing `url` Package Triggering Fatal Underscore Math Mode in References
- **Code snippet (`references.bib`)**:
  ```bibtex
  @inproceedings{food101,
    ...
    note = {Official data set: \url{https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/}}
  }
  @misc{food101torch,
    ...
    note = {\url{https://docs.pytorch.org/vision/2.0/_modules/torchvision/datasets/food101.html}...}
  }
  ```
- **Error in Log**:
  ```
  ! Missing $ inserted.
  <inserted text> $
  l.44 ...n.ee.ethz.ch/cvl/datasets_extra/food-101/}
  ! Missing $ inserted.
  l.49 ...modules/torchvision/datasets/food101.html}
  ```
- **Root Cause**: `\usepackage{url}` is NOT loaded in the preamble of `main.tex`. In `IEEEtran.cls`, the fallback definition `\providecommand{\url}[1]{#1}` leaves raw text active. Raw underscores (`datasets_extra`, `_modules`) in text mode trigger TeX math mode subscript errors.
- **Fix**: Add `\usepackage{url}` to the preamble of `main.tex`. The `url` package parses underscores verbatim.

### 3.5 Warning 5: Undefined Reference Label (Line 139)
- **Code snippet**:
  ```latex
  139: Understanding the limitations of the product is critical. We analyzed the most frequently confused dish pairs to calibrate our Ambiguity Delta algorithm. Table~\ref{tbl:smoke} lists the top confused pairs.
  140: 
  141: \input{tables/table_confused_classes.tex}
  ```
- **Warning in Log**:
  ```
  LaTeX Warning: Reference `tbl:smoke' on page 3 undefined on input line 139.
  ```
- **Root Cause**: `table_confused_classes.tex` defines `\label{tbl:confused}`, but `main.tex` references `\ref{tbl:smoke}`.
- **Fix**: Change `Table~\ref{tbl:smoke}` to `Table~\ref{tbl:confused}`.

### 3.6 Warning 6: Overfull `\hbox` in Benchmark Table (Lines 185–201)
- **Code snippet**:
  ```latex
  185: \begin{table}[ht]
  ...
  190: \begin{tabular}{lccccc}
  191: \toprule
  192: Model & Top-1 & Top-3 & Prec & Rec & F1 \\
  ...
  201: \end{table}
  ```
- **Warning in Log**:
  ```
  Overfull \hbox (13.00423pt too wide) in paragraph at lines 190--201
  ```
- **Root Cause**: 6 columns of data in `\small` slightly exceed the single-column width of IEEEtran (~252pt).
- **Remedy**: Use `\footnotesize` or `\setlength{\tabcolsep}{4pt}`, or span across both columns with `\begin{table*}`.

---

## 4. Exact Build Command Sequence

To achieve clean compilation without fatal structural errors, resolve references, and generate properly numbered bibliography items, the exact sequence of commands is:

```
Step 1: pdflatex -interaction=nonstopmode -disable-installer main.tex
Step 2: bibtex main
Step 3: pdflatex -interaction=nonstopmode -disable-installer main.tex
Step 4: pdflatex -interaction=nonstopmode -disable-installer main.tex
```

### Purpose of Each Step:
1. **Pass 1 (`pdflatex`)**: Parses `main.tex`, imports inputs (`tables/*.tex`), writes layout references and citation keys to `main.aux`.
2. **Pass 2 (`bibtex`)**: Parses `main.aux` and `references.bib`, selects cited entries using `IEEEtran.bst`, and writes formatted `\bibitem` entries into `main.bbl`.
3. **Pass 3 (`pdflatex`)**: Reads `main.bbl` into the `thebibliography` environment, converts `\cite{...}` keys to numbered brackets (e.g. `[1]`), and formats the reference list.
4. **Pass 4 (`pdflatex`)**: Resolves any shifted page cross-references (such as Table/Figure numbers and page numbers) resulting from the addition of the bibliography text.

### Verification of Build Sequence:
In the test workspace (`.agents/explorer_survey_3/build_test`), after applying the syntax fixes and `\usepackage{url}`, executing this exact 4-step sequence yielded:
- **Pass 1 Exit Code:** `0`
- **Pass 2 (bibtex) Exit Code:** `0`
- **Pass 3 Exit Code:** `0`
- **Pass 4 Exit Code:** `0`
- **Output PDF:** `main.pdf` successfully generated (8 pages, 1,514,584 bytes, 0 undefined references, 0 missing item errors).

---

## 5. Environment and Platform Idiosyncrasies (Windows / PowerShell / MiKTeX)

1. **PowerShell 5.1 Pipeline Syntax (`&&` Unsupported)**:
   - On this machine, PowerShell version is **5.1** (`Major: 5, Minor: 1, Build: 26100`).
   - Using the POSIX / Bash chaining operator `&&` results in a parser error:
     `The token '&&' is not a valid statement separator in this version.`
   - **Recommended execution pattern in PowerShell**:
     ```powershell
     pdflatex -interaction=nonstopmode main.tex
     if ($LASTEXITCODE -eq 0) { bibtex main }
     if ($LASTEXITCODE -eq 0) { pdflatex -interaction=nonstopmode main.tex }
     if ($LASTEXITCODE -eq 0) { pdflatex -interaction=nonstopmode main.tex }
     ```
     Or execute via `cmd /c`:
     ```powershell
     cmd /c "pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex"
     ```

2. **Headless Execution and MiKTeX Package Prompts**:
   - In unattended agent scripts, if an unknown package is requested, MiKTeX may invoke its GUI Package Installer dialog or hang waiting for console input if set to prompt mode.
   - Always supply `-interaction=nonstopmode` and `-disable-installer` (or verify package existence beforehand) to guarantee automated non-blocking execution.

3. **Current Working Directory (`Cwd`) Sensitivity**:
   - In `main.tex`, all external inputs are defined using relative paths (`tables/table_test_performance.tex`, `figures/fig_warning_curve.png`).
   - Execution commands must always set the working directory to `c:\Projects\foodlens-version-2\paper`. Running `pdflatex c:\Projects\...\paper\main.tex` from the workspace root will fail because pdfTeX will attempt to resolve `tables/...` relative to the workspace root rather than `paper/`.

4. **Vector vs. Raster Graphics (`.pdf` vs `.png`)**:
   - All 5 figure assets exist in both `.pdf` (vector) and `.png` (raster) formats in `figures/`.
   - `main.tex` currently imports `figures/fig_warning_curve.png` with a hardcoded `.png` extension, while importing other figures as `.pdf`.
   - Omitting the file extension (e.g. `\includegraphics[width=\linewidth]{figures/fig_warning_curve}`) is standard best practice in LaTeX with `pdfTeX`, allowing the engine to automatically pick vector `.pdf` for crisp rendering at publication zoom.

---

## 6. Required Action Items for Paper Restructuring Team

When rewriting `paper/main.tex` to satisfy R1, R2, R3, and R4:

1. **Add `\usepackage{url}`**: Place immediately after `\usepackage{cite}` in `main.tex` to safely render URL entries in `references.bib`.
2. **Add Missing IEEE Citations to `references.bib`**:
   - EfficientNet (Tan & Le, ICML 2019)
   - ResNet (He et al., CVPR 2016)
   - MobileNetV2 (Sandler et al., CVPR 2018)
   - DenseNet (Huang et al., CVPR 2017)
3. **Embed In-Text `\cite{...}` Calls**: Ensure all foundational models and Food-101 are cited in the body text (resolving BibTeX exit code 1).
4. **Fix Math Syntax Errors**: Ensure all dimensions use standard math delimiters (`$101 \times 101$`, `$3 \times 3$`, `$2 \times 2$`).
5. **Fix Table Label Reference**: Ensure `Table~\ref{tbl:confused}` matches the label in `table_confused_classes.tex`.
6. **Execute Build via Valid PowerShell Syntax**: Use `cmd /c "pdflatex ... && bibtex ..."` or semicolon conditional logic.
