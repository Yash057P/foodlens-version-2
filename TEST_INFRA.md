# FoodLens IEEE Manuscript Test Infrastructure (`TEST_INFRA.md`)

## 1. Executive Summary

This document specifies the architecture, test categories, coverage criteria, and execution protocol for the automated verification suite of the FoodLens IEEE conference manuscript (`paper/main.tex`, `paper/references.bib`, `paper/tables/`, `paper/figures/`).

The verification harness is implemented in `scripts/verify_paper.py`. It is an opaque-box, 4-tier automated test harness designed to guarantee that all structural, scholastic, quantitative, and compilation requirements from `ORIGINAL_REQUEST.md`, `PROJECT.md`, and the 1015-line peer review are rigorously enforced.

---

## 2. 4-Tier Test Architecture

```
+-----------------------------------------------------------------------------+
|                          scripts/verify_paper.py                            |
+-----------------------------------------------------------------------------+
       |
       +---> [Tier 1: Feature Coverage] (37 Sub-checks, >= 5 per Feature)
       |     - F1: Required IEEE Sections (10 checks)
       |     - F2: Food-101 & EfficientNet Citations in Bib & In-Text (6 checks)
       |     - F3: Model Comparison Table Metrics (5 checks)
       |     - F4: TTA & Confidence Ablation Tables (6 checks)
       |     - F5: Dedicated Limitations Section (5 checks)
       |     - F6: Confusion Matrix Placement in Appendix (5 checks)
       |
       +---> [Tier 2: Boundary & Corner Cases] (4 Sub-checks)
       |     - 2.1: Regex Promotional Language Audit (Zero Occurrences)
       |     - 2.2: Undefined References / Citations Audit ([?], ??, Missing Labels)
       |     - 2.3: LaTeX Preamble Package Completeness (\usepackage{url})
       |     - 2.4: Math Delimiter Syntax Audit ($101 \times 101$, $3 \times 3$)
       |
       +---> [Tier 3: Cross-Feature Consistency] (3 Sub-checks)
       |     - 3.1: Table IV Numeric Consistency & Rationale Validation (EffNet < DenseNet)
       |     - 3.2: In-Text Citations \cite{key} vs references.bib Bidirectional Integrity
       |     - 3.3: TTA & Confidence Ablation Tables Numeric Row Parsing
       |
       +---> [Tier 4: Full PDF Compilation & Layout] (4 Sub-checks)
             - 4.1: Clean 4-Pass Build via cmd /c (pdflatex -> bibtex -> pdflatex -> pdflatex)
             - 4.2: Output PDF Freshness & Non-Zero File Size (> 50 KB)
             - 4.3: BibTeX Compilation Log (main.blg) Zero Fatal Errors
             - 4.4: LaTeX Compilation Log (main.log) Zero Fatal Errors
```

---

## 3. Granular Test Suite Specification

### Tier 1: Feature Coverage (>= 5 Sub-checks Per Feature)

| ID | Feature Category | Test Case | Target Requirement | Pass Criteria |
|---|---|---|---|---|
| **1.1.1** | F1: IEEE Sections | Introduction | R1, review §12 | `\section{Introduction}` present |
| **1.1.2** | F1: IEEE Sections | Related Work | R1, review §12 | `\section{Related Work}` present |
| **1.1.3** | F1: IEEE Sections | System Architecture | R1, review §12 | `\section{System Architecture}` present |
| **1.1.4** | F1: IEEE Sections | Methodology | R1, review §12 | `\section{Methodology}` present |
| **1.1.5** | F1: IEEE Sections | Experimental Setup | R4, review §14 | `\section{Experimental Setup}` present |
| **1.1.6** | F1: IEEE Sections | Results and Discussion | R1, review §12 | `\section{Results and Discussion}` present |
| **1.1.7** | F1: IEEE Sections | Deployment/Privacy/Limitations | R1, review §12 | `\section{Deployment, Privacy, and Limitations}` present |
| **1.1.8** | F1: IEEE Sections | Conclusion | R1, review §12 | `\section{Conclusion}` present |
| **1.1.9** | F1: IEEE Sections | Bibliography | R2, review §1 | `\bibliography{references}` present |
| **1.1.10** | F1: IEEE Sections | Appendix | R1, review §12 | `\appendix` or `\section*{Appendix}` present |
| **1.2.1** | F2: Citations | Food-101 in BibTeX | R2, review §1 | Entry with key `food101` (Bossard et al.) in `references.bib` |
| **1.2.2** | F2: Citations | EfficientNet in BibTeX | R2, review §1 | Entry for Tan & Le (ICML 2019) in `references.bib` |
| **1.2.3** | F2: Citations | Food-101 in-text cite | R2, review §1 | `\cite{...food101...}` present in body text |
| **1.2.4** | F2: Citations | EfficientNet in-text cite | R2, review §1 | `\cite{...tan...}` or `\cite{...efficientnet...}` present in body text |
| **1.2.5** | F2: Citations | Foundational Model Bib Entries | R2, review §1 | Dedicated entries for ResNet (He et al.), MobileNetV2 (Sandler et al.), DenseNet (Huang et al.) |
| **1.2.6** | F2: Citations | Section Distribution | R2, review §1 | Active in-text citations appear across $\ge 3$ distinct sections |
| **1.3.1** | F3: Model Comparison | Table Existence | R3, review §2 | Model comparison table located in `main.tex` or `tables/` |
| **1.3.2** | F3: Model Comparison | CPU Latency Column | R3, review §2 | Table header contains `Latency` / `Inference Time` column |
| **1.3.3** | F3: Model Comparison | Parameter Count Column | R3, review §2 | Table header contains `Parameters` / `Params (M)` column |
| **1.3.4** | F3: Model Comparison | Accuracy Columns | R3, review §2 | Table header contains `Top-1` and `Top-3` columns |
| **1.3.5** | F3: Model Comparison | Architectures Included | R3, review §2 | Rows present for: Custom CNN, ResNet50, MobileNetV2, DenseNet121, EfficientNetB0 |
| **1.4.1** | F4: Ablation Tables | TTA Table Existence | R3, review §7 | TTA ablation table located in `main.tex` or `tables/table_tta_ablation.tex` |
| **1.4.2** | F4: Ablation Tables | TTA Variants | R3, review §7 | Table specifies: Baseline (No TTA), Flip, Crop, and 3-Way Ensemble |
| **1.4.3** | F4: Ablation Tables | TTA Metrics | R3, review §7 | Table specifies Latency (ms) and Accuracy / Variance columns |
| **1.4.4** | F4: Ablation Tables | Confidence Table Existence | R3, review §8 | Confidence ablation table located in `main.tex` or `tables/table_confidence_ablation.tex` |
| **1.4.5** | F4: Ablation Tables | Threshold Parameters | R3, review §8 | Table specifies threshold sweeps ($\tau \in [0.30, 0.70]$, $\Delta \in [0.05, 0.20]$) |
| **1.4.6** | F4: Ablation Tables | Trade-off Metrics | R3, review §8 | Table specifies Coverage (%), Rejection Rate (%), and Retained Accuracy (%) |
| **1.5.1** | F5: Limitations | Section Header | R1, review §29 | `\section{Limitations}` or `\subsection{Limitations}` exists |
| **1.5.2** | F5: Limitations | Closed-Set Discussion | R1, review §29 | Explicit discussion of closed-set 101-class limitation & out-of-distribution inputs |
| **1.5.3** | F5: Limitations | Recipe Variance Discussion | R1, review §29 | Explicit discussion of preparation diversity, ingredient substitutions, regional recipes |
| **1.5.4** | F5: Limitations | Clinical Safety Disclaimer | R2, review §4, §20 | Explicit disclaimer that system is non-medical and cannot guarantee clinical allergen safety |
| **1.5.5** | F5: Limitations | Logical Positioning | R1, review §29 | Limitations section situated prior to Conclusion |
| **1.6.1** | F6: Confusion Matrix | Figure Referenced | R1, review §10 | `fig_confusion_full` referenced in LaTeX source |
| **1.6.2** | F6: Confusion Matrix | Relocated to Appendix | R1, review §10 | Figure inclusion is located inside an Appendix section |
| **1.6.3** | F6: Confusion Matrix | Removed from Body | R1, review §10 | Figure inclusion removed from main Results & Discussion body |
| **1.6.4** | F6: Confusion Matrix | Caption Math Syntax | R1, review §26 | Caption cleanly describes $101 \times 101$ matrix with valid math syntax |
| **1.6.5** | F6: Confusion Matrix | Asset Files Exist | R1, review §10 | `fig_confusion_full.pdf` and `.png` exist on disk |

---

### Tier 2: Boundary & Corner Cases

| ID | Test Name | Target Defect | Enforcement Logic |
|---|---|---|---|
| **2.1** | Promotional Words Audit | Startup/marketing buzzwords (review §4, §16, §18) | Case-insensitive regex search for forbidden terms in active LaTeX text (comments excluded): `massive`, `production-ready`, `guarantee`, `hallucination`, `glassmorphism`, `mini-product`, `O(1)`. Exact line numbers reported. |
| **2.2** | Undefined References Audit | Broken cross-references (review §22, M5) | Scans `main.log` for undefined references/citations; parses all `\ref{}` / `\pageref{}` and verifies corresponding `\label{}` exists; scans for literal `[?]` or `??`. |
| **2.3** | `\usepackage{url}` in Preamble | Fatal underscore crash in BibTeX URLs (survey 3, §3.4) | Verifies `\usepackage{url}` is loaded prior to `\begin{document}` to prevent TeX math subscript crashes on raw underscores in URLs. |
| **2.4** | Math Delimiter Syntax Audit | Missing math mode delimiters (survey 3, §3.1, §3.2) | Verifies dimensional expressions ($101 \times 101$, $224 \times 224$, $3 \times 3$, $2 \times 2$) use proper enclosing `$...$`; flags unescaped raw `\times`. |

---

### Tier 3: Cross-Feature Consistency

| ID | Test Name | Cross-Module Contract | Enforcement Logic |
|---|---|---|---|
| **3.1** | Model Comparison Numeric Rationale | Benchmark Scripts (M1) $\leftrightarrow$ Table IV $\leftrightarrow$ Section VI.B Narrative | Extracts numeric Parameters and CPU Latency. Verifies: EfficientNetB0 parameters ($\approx 4.0\text{M} - 5.3\text{M}$) $<$ DenseNet121 parameters ($\approx 7.0\text{M} - 8.0\text{M}$); EfficientNetB0 latency $<$ DenseNet121 latency. Confirms empirical justification for model selection. |
| **3.2** | In-Text Citations vs `references.bib` | `paper/main.tex` $\leftrightarrow$ `paper/references.bib` | Extracts all `\cite{keys}` and verifies $100\%$ match entries in `references.bib`. Ensures zero unresolved citation keys and reports unused keys. |
| **3.3** | Ablation Tables Numeric Rows | Benchmark Scripts (M1) $\leftrightarrow$ `paper/tables/*.tex` | Verifies TTA table has $\ge 3$ numeric data rows (Latency, Accuracy/Variance) and Confidence table has $\ge 3$ numeric data rows ($\tau$, $\Delta$, Coverage, Rejection, Accuracy). |

---

### Tier 4: Full PDF Compilation & Layout

| ID | Test Name | Build Toolchain | Enforcement Logic |
|---|---|---|---|
| **4.1** | Clean 4-Pass Build Sequence | MiKTeX `pdflatex` & `bibtex` | Executes clean 4-pass sequence via `cmd /c`: `pdflatex -interaction=nonstopmode -disable-installer main.tex && bibtex main && pdflatex -interaction=nonstopmode -disable-installer main.tex && pdflatex -interaction=nonstopmode -disable-installer main.tex`. Returns exit code 0. |
| **4.2** | Fresh Output PDF | Output Artifact | Verifies `main.pdf` is freshly written (modification timestamp updated during current build run) and size $> 50\text{ KB}$. |
| **4.3** | Zero Fatal BibTeX Errors | `main.blg` | Inspects `main.blg` ensuring absence of "I found no \citation commands" and 0 error messages reported. |
| **4.4** | Zero Fatal LaTeX Errors | `main.log` | Inspects `main.log` ensuring zero fatal error lines starting with `! `. |

---

## 4. Execution Protocol & CLI Options

The verification harness can be invoked from the repository root:

```bash
# Run all 4 tiers (standard gate)
python scripts/verify_paper.py

# Run specific tier
python scripts/verify_paper.py --tier 1
python scripts/verify_paper.py --tier 2
python scripts/verify_paper.py --tier 3
python scripts/verify_paper.py --tier 4

# Run static tiers 1-3 skipping PDF compilation
python scripts/verify_paper.py --skip-compile

# Export machine-readable JSON results
python scripts/verify_paper.py --json test_report.json
```

### Exit Codes
- `0`: All executed tests in selected tier(s) passed.
- `1`: One or more tests failed (detailed diagnostic messages printed to stderr/stdout).

---

## 5. Current Baseline Test Execution Report

Executed on initial unmodified manuscript state:

```
================================================================================
FoodLens IEEE Manuscript 4-Tier Verification Report
================================================================================

--- Tier 1: Feature Coverage (16/37 Passed) ---
  [PASS] 1.1.1: Section: Introduction exists
  [FAIL] 1.1.2: Section: Related Work exists (Missing)
  [FAIL] 1.1.3: Section: System Architecture exists (Heading mismatch)
  [FAIL] 1.1.4: Section: Methodology exists (Heading mismatch)
  [FAIL] 1.1.5: Section: Experimental Setup exists (Missing)
  [FAIL] 1.1.6: Section: Results and Discussion exists (Titled 'Extensive Product Evaluation')
  [FAIL] 1.1.7: Section: Deployment/Privacy/Limitations exists (Missing)
  [PASS] 1.1.8: Section: Conclusion exists
  [PASS] 1.1.9: Bibliography inclusion exists
  [PASS] 1.1.10: Appendix section exists
  [PASS] 1.2.1: Food-101 (Bossard et al.) defined in references.bib
  [FAIL] 1.2.2: EfficientNet (Tan & Le) defined in references.bib (Missing)
  [FAIL] 1.2.3: In-text citation for Food-101 exists (Zero in-text citations)
  [FAIL] 1.2.4: In-text citation for EfficientNet exists (Zero in-text citations)
  [FAIL] 1.2.5: Foundational backbones in references.bib (Dedicated entries missing)
  [FAIL] 1.2.6: Active citations distributed across >= 3 sections (Found 0)
  [PASS] 1.3.1: Model Comparison Table exists
  [FAIL] 1.3.2: Model Comparison Table contains CPU Latency column (Missing)
  [FAIL] 1.3.3: Model Comparison Table contains Parameter Count column (Missing)
  [PASS] 1.3.4: Model Comparison Table contains Top-1 and Top-3 accuracy columns
  [PASS] 1.3.5: Model Comparison Table includes all 5 candidate architectures
  [FAIL] 1.4.1: TTA Ablation Table exists (Missing)
  [FAIL] 1.4.2: TTA Ablation Table specifies transformation variants (Missing)
  [FAIL] 1.4.3: TTA Ablation Table contains latency and accuracy metrics (Missing)
  [FAIL] 1.4.4: Confidence Threshold Ablation Table exists (Missing)
  [FAIL] 1.4.5: Confidence Table specifies threshold parameters (Missing)
  [FAIL] 1.4.6: Confidence Table specifies coverage/rejection trade-offs (Missing)
  [FAIL] 1.5.1: Dedicated Limitations section exists (Missing)
  [FAIL] 1.5.2: Limitations discusses closed-set & OOD inputs (Missing)
  [FAIL] 1.5.3: Limitations discusses recipe variance (Missing)
  [FAIL] 1.5.4: Limitations provides clinical safety disclaimer (Missing)
  [FAIL] 1.5.5: Limitations section positioned before Conclusion (Missing)
  [PASS] 1.6.1: Full 101x101 Confusion Matrix figure referenced in LaTeX
  [FAIL] 1.6.2: Full Confusion Matrix placed in Appendix section (Resides in body)
  [FAIL] 1.6.3: Full Confusion Matrix removed from main body (Still in body)
  [FAIL] 1.6.4: Confusion Matrix figure caption describes 101x101 matrix (Broken math syntax)
  [PASS] 1.6.5: Confusion Matrix asset file exists on disk

--- Tier 2: Boundary & Corner Cases (0/4 Passed) ---
  [FAIL] 2.1: Zero promotional words (Found 11 occurrences: massive, production-ready, guarantee, etc.)
  [FAIL] 2.2: Zero undefined references or citations (tbl:smoke undefined)
  [FAIL] 2.3: \usepackage{url} present in LaTeX preamble (Missing)
  [FAIL] 2.4: Proper math delimiter syntax ($101 \times 101$, $3 \times 3$) (5 math syntax errors)

--- Tier 3: Cross-Feature Consistency (0/3 Passed) ---
  [FAIL] 3.1: Model comparison table contains valid numeric CPU latency and parameter counts
  [FAIL] 3.2: Every in-text \cite{key} has a matching entry in references.bib (0 citations found)
  [FAIL] 3.3: TTA and Confidence ablation tables contain valid numeric rows (Tables missing)

--- Tier 4: Full PDF Compilation & Layout (0/4 Passed) ---
  [FAIL] 4.1: Clean build sequence via cmd /c (Exit code 1)
  [FAIL] 4.2: Output PDF freshly generated (Stale prior build artifact)
  [FAIL] 4.3: main.blg has zero fatal BibTeX errors (No citations found)
  [FAIL] 4.4: main.log has zero fatal LaTeX syntax errors (Missing $ inserted, missing \item)
```

---

## 6. Implementation Guidance for Milestone Workers

- **Worker M1 (Quantitative Benchmarks & Tables)**:
  - Generate `table_model_comparison.tex` with `Latency (ms)` and `Params (M)` columns. Ensure EfficientNetB0 has lower latency and fewer parameters than DenseNet121.
  - Generate `table_tta_ablation.tex` with at least 3 rows: Baseline (No TTA), Horizontal Flip, 10% Center Crop, and 3-Way Ensemble.
  - Generate `table_confidence_ablation.tex` with threshold sweeps for $\tau$ and $\Delta$, with Coverage (%), Rejection (%), and Retained Accuracy (%) columns.
- **Worker M2 (Content, Tone, Claims, Citations)**:
  - Add foundational entries to `paper/references.bib` (Tan & Le 2019, He et al. 2016, Sandler et al. 2018, Huang et al. 2017).
  - Add in-text `\cite{...}` commands across $\ge 3$ sections in `paper/main.tex`.
  - Eliminate promotional buzzwords listed in Tier 2.1.
  - Reconstruct Section V (Experimental Setup).
- **Worker M3 (IEEE Restructuring & Layout)**:
  - Add `\usepackage{url}` to preamble.
  - Fix broken math mode: `$101 \times 101$`, `$3 \times 3$`, `$2 \times 2$`.
  - Fix `\ref{tbl:smoke}` $\rightarrow$ `\ref{tbl:confused}`.
  - Relocate Figure 3 (`fig_confusion_full`) to Appendix A.
  - Restructure sections into Sections I through VIII + Appendix.
- **Worker M4 (Final Gate Verification)**:
  - Run `python scripts/verify_paper.py` to confirm 100% pass rate across all 48 tests.
