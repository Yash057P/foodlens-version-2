## 2026-09-21T16:23:15Z
<USER_REQUEST>
Read c:\Projects\foodlens-version-2\.agents\ORIGINAL_REQUEST.md first.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your assigned role: Benchmark & Ablation Worker (Milestone 1).
Your working directory: c:\Projects\foodlens-version-2\.agents\worker_m1

Scope & Write Ownership:
You have exclusive write ownership of:
- scripts/benchmark_models.py
- scripts/benchmark_tta_ablation.py
- scripts/benchmark_confidence_ablation.py
- paper/tables/table_model_comparison.tex
- paper/tables/table_tta_ablation.tex
- paper/tables/table_confidence_ablation.tex
DO NOT modify paper/main.tex, paper/references.bib, or any other files.

Context & Inputs:
- Read c:\Projects\foodlens-version-2\.agents\orchestrator_1\PROJECT.md
- Read c:\Projects\foodlens-version-2\.agents\explorer_survey_2\survey_report.md and handoff.md for exact specifications and formulas.
- Code references: src/training/b11_build.py, webapp/inference.py, webapp/models/best_model.keras.

Tasks:
1. Implement scripts/benchmark_models.py:
   - Instantiate or benchmark CustomCNN, MobileNetV2, EfficientNetB0, DenseNet121, ResNet50.
   - Measure actual parameter counts (trainable, non-trainable, total), FP32 model size (MB), and CPU inference latency (ms, batch size 1, warmup passes + average over runs).
   - Generate paper/tables/table_model_comparison.tex with columns: Model Architecture, Parameters, Model Size (MB), CPU Latency (ms), Top-1 Accuracy (%), Top-3 Accuracy (%).
2. Implement scripts/benchmark_tta_ablation.py:
   - Evaluate webapp/models/best_model.keras under 4 TTA modes: Baseline (No TTA), Horizontal Flip, 10% Center Crop, and 3-Way Ensemble (Base+Flip+Crop).
   - Measure CPU latency (ms), effective batch size, and empirical variance/accuracy.
   - Generate paper/tables/table_tta_ablation.tex.
3. Implement scripts/benchmark_confidence_ablation.py:
   - Evaluate confidence thresholds (tau from 0.30 to 0.70) and ambiguity margins (Delta from 0.05 to 0.20).
   - Measure coverage rate (%), rejection rate (%), and retained accuracy (%).
   - Generate paper/tables/table_confidence_ablation.tex.
4. Execute all three scripts, ensure they run cleanly with exit code 0, and verify the generated .tex table files.

Deliverables:
- Maintain progress.md with timestamps in your working directory.
- Write handoff.md documenting execution commands, outputs, and table paths.
- Send message back to orchestrator when finished.
</USER_REQUEST>
