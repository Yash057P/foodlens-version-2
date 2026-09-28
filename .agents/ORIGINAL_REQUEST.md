# Original User Request

## Initial Request — 2026-09-21T16:10:49Z

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full multi-agent team

Rewrite and restructure the FoodLens IEEE manuscript (`paper/main.tex`) to address all critical, high, and structural issues raised in the provided review. The goal is to transform it from a promotional project report into a rigorous, reproducible, and well-formatted academic research paper.

Working directory: c:\Projects\foodlens-version-2
Integrity mode: demo

## Requirements

### R1. Restructure and Format
Reorganize the LaTeX sections to match a standard IEEE research format: Introduction, Related Work, System Architecture, Methodology, Experimental Setup, Results & Discussion, Deployment/Privacy/Limitations, Conclusion, References, and Appendix. Move large figures (e.g., the 101x101 confusion matrix) to the Appendix and fix pagination imbalances.

### R2. Tone, Claims, and Citations
Remove all marketing language (e.g., "production-ready", "O(1) guarantees", "hallucinations"). Rewrite claims regarding privacy and allergen safety to be scientifically defensible. Add proper IEEE citations (in `references.bib` and in-text) for all foundational technologies (Food-101, EfficientNet, ResNet, etc.).

### R3. Benchmark and Ablation Experiments
Write and execute Python scripts to measure the actual parameter counts, model sizes, and CPU inference latency for the architectures defined in `src/training/b11_build.py`. Use these metrics to update the Model Comparison table, justifying the selection of EfficientNetB0. Additionally, script an ablation experiment for the Test-Time Augmentation (TTA) and confidence thresholds, and document the results in new tables within the paper.

### R4. Experimental Setup Details
Read the source code (`inference.py`, `b11_build.py`, `b12_train_util.py`) to accurately reconstruct and document the Experimental Setup (hyperparameters, dataset splits, architecture layers, software versions).

## Acceptance Criteria

### Content and Tone
- [ ] No promotional phrases (e.g., "massive", "production-ready") remain in the text.
- [ ] The claim regarding "preventing hallucinations" is explicitly downgraded to avoiding generative fabrication but acknowledging database dependency.
- [ ] A dedicated "Limitations" section is present.
- [ ] In-text citations exist for Food-101 and EfficientNet.

### Quantitative Verification
- [ ] The Model Comparison table contains newly generated metrics for CPU Latency and Parameter Count.
- [ ] A new table or list exists documenting the TTA/confidence ablation results.

### Programmatic Verification
- [ ] The paper compiles successfully using `pdflatex -interaction=nonstopmode main.tex` and `bibtex main` without fatal structural errors, producing an updated `main.pdf`.
