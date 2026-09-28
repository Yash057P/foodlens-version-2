# Project: FoodLens IEEE Manuscript Rewrite & Restructuring

## Architecture
- **Document Model**: IEEEtran two-column conference format (`paper/main.tex`, `paper/references.bib`, `paper/figures/`, `paper/tables/`).
- **Benchmark Suite**: Python execution scripts (`scripts/benchmark_models.py`, `scripts/benchmark_tta_ablation.py`, `scripts/benchmark_confidence_ablation.py`) measuring actual parameter counts, model sizes, and CPU inference latencies.
- **Verification Harness**: Automated E2E verification suite (`scripts/verify_paper.py`) testing structural requirements, tone/marketing removals, citation validity, and PDF compilation via `pdflatex` and `bibtex`.

## Feature Inventory
Every feature from ORIGINAL_REQUEST.md and the survey phase is enumerated here with its assigned milestone.
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | M1-Bench-Models | Script and execute measurement of actual parameters, model size, and CPU latency for architectures in `b11_build.py` | M1 | R3, review #2 |
| 2 | M1-Bench-TTA | Script and execute TTA ablation measurement (latency and variance across No TTA, Flip, Crop, 3-way) | M1 | R3, review #7 |
| 3 | M1-Bench-Conf | Script and execute confidence ($\tau$) and ambiguity ($\Delta$) threshold sweep and ablation | M1 | R3, review #8 |
| 4 | M1-Table-Gen | Generate LaTeX tables in `paper/tables/` (`table_model_comparison.tex`, `table_tta_ablation.tex`, `table_confidence_ablation.tex`) | M1 | R3, review #2, #7, #8 |
| 5 | M2-Bib-Expand | Add missing foundational citations (Tan & Le, He et al., Sandler et al., Huang et al., Deng et al., Lowe, Dalal & Triggs, Kingma & Ba, Bossard et al.) to `paper/references.bib` | M2 | R2, review #1 |
| 6 | M2-InText-Cite | Insert active in-text `\cite{...}` commands across all sections in `paper/main.tex` | M2 | R2, review #1 |
| 7 | M2-Tone-Cleanup | Remove promotional/marketing language ("massive", "production-ready", "mini-product", "O(1) guarantees", "hallucinations", "glassmorphism") | M2 | R2, review #9, #10 |
| 8 | M2-Claims-Downgrade | Scientifically defensible rewrite of privacy (stateless in-memory) and allergen safety (disclaimers, database dependency) | M2 | R2, review #4 |
| 9 | M2-Setup-Recon | Reconstruct Section V (Experimental Setup) from code: hyperparameters, 2-phase transfer, mixed float16, data splits (Track A & Track B) | M2 | R4, review #3 |
| 10 | M2-Model-Justify | Justify EfficientNetB0 selection over DenseNet121 based on CPU latency (+71.5% for DenseNet) and parameters (+73.2% for DenseNet) | M2 | R3, review #2 |
| 11 | M3-IEEE-Restruct | Restructure sections into standard IEEE format (Sections I through VIII, References, Appendix) | M3 | R1, review #12 |
| 12 | M3-Float-Appendix | Relocate full 101x101 confusion matrix (Fig. 3) to Appendix A; eliminate redundant Table V; integrate Fig. 5 into Section VI | M3 | R1, review #5, #6 |
| 13 | M3-Syntax-Preamble | Fix math delimiter syntax errors (`$101 \times 101$`, `$224 \times 224$`), fix `\ref{tbl:confused}`, add `\usepackage{url}` | M3 | R1, survey #3 |
| 14 | M3-Pagination-Fix | Eliminate blank spaces on pages 5 and 8; balance column heights on final pages | M3 | R1, review #5, #11 |
| 15 | M4-Compile-Verify | Compile `paper/main.tex` with `pdflatex` and `bibtex` with 0 fatal errors, generating clean `main.pdf` | M4 | Programmatic |
| 16 | E2E-Test-Infra | Build opaque-box automated test harness covering Tiers 1–4 acceptance criteria | E2E-Track | Dual Track |
| 17 | M4-Adversarial-Audit | Adversarial coverage hardening and forensic audit verification for final gate | M4 | Dual Track / Audit |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Test Suite | Automated verification harness (`scripts/verify_paper.py`) covering all acceptance criteria | none | IN_PROGRESS |
| M1 | Benchmarks & Ablations | Benchmark scripts (`scripts/`), measurements, and LaTeX tables generation (`paper/tables/`) | none | IN_PROGRESS |
| M2 | Content, Tone, Claims & Citations | `paper/references.bib` expansion, in-text citations, scientific tone, setup reconstruction, claims rewrite | M1 | PLANNED |
| M3 | IEEE Restructuring & Layout | Section reorganization in `paper/main.tex`, moving Fig. 3 to Appendix, eliminating Table V, fixing syntax & pagination | M2 | PLANNED |
| M4 | Final Compilation & Adversarial Gate | Full PDF compilation with `pdflatex` and `bibtex`, 100% E2E test pass, Reviewer approval, Challenger check, Auditor CLEAN | M3, E2E | PLANNED |

## Interface Contracts
### Benchmark Scripts (M1) ↔ LaTeX Tables (M2/M3)
- `scripts/benchmark_models.py` outputs JSON / stdout and writes `paper/tables/table_model_comparison.tex` containing:
  - Architecture names: Custom CNN, MobileNetV2, EfficientNetB0, DenseNet121, ResNet50.
  - Columns: Parameters, Model Size (MB), CPU Latency (ms), Top-1 Accuracy (%), Top-3 Accuracy (%).
- `scripts/benchmark_tta_ablation.py` writes `paper/tables/table_tta_ablation.tex`:
  - Configurations: No TTA (Base), Horizontal Flip, Center Crop, 3-Way Ensemble.
  - Columns: Variant, Batch Size, CPU Latency (ms), Accuracy / Variance.
- `scripts/benchmark_confidence_ablation.py` writes `paper/tables/table_confidence_ablation.tex`:
  - Threshold $\tau$ (0.30 to 0.70) and $\Delta$ (0.05 to 0.20): Coverage (%), Rejection Rate (%), Retained Accuracy (%).

### E2E Test Harness ↔ Manuscript Build
- Command: `python scripts/verify_paper.py`
- Checks:
  1. PDF exists and compiled without errors via `pdflatex` + `bibtex`.
  2. Zero promotional words ("massive", "production-ready", "guarantee", "hallucination") in text.
  3. All foundational citations present in `references.bib` and cited via `\cite{}`.
  4. Table IV contains Latency and Parameter columns.
  5. Dedicated Limitations section present.
  6. Fig. 3 relocated to Appendix.

## Code Layout
- `paper/main.tex`: Primary IEEE LaTeX manuscript (owned by M2 and M3 Workers).
- `paper/references.bib`: BibTeX bibliography (owned by M2 Worker).
- `paper/tables/`: LaTeX table files (owned by M1 Worker).
- `paper/figures/`: Manuscript visual assets (read-only).
- `scripts/benchmark_*.py`: Quantitative measurement and ablation scripts (owned by M1 Worker).
- `scripts/verify_paper.py`: Automated E2E verification test harness (owned by E2E Worker).
