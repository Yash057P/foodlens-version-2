# FoodLens Enhancement Roadmap

This classification reflects the real engineering, data, validation, and external-service work required. A UI mock alone does not count as completion.

## Big tasks

- **Instance segmentation and portion estimation**: requires a segmentation model, multi-item training data, physical scale or depth calibration, volume estimation, and nutrition validation.
- **Reverse recipe generation**: requires a vision-language model, recipe corpus, grounded evaluation, and strong uncertainty controls because recipes cannot be recovered exactly from appearance.
- **Freshness and quality analysis**: requires a separate labelled dataset and classifier for each ingredient/domain, plus safety-focused validation.
- **Live AR scanning**: requires continuous video inference, object tracking, mobile GPU optimization, and stable spatial overlays.
- **Health app integration**: requires platform-specific Apple Health or Android Health Connect applications, permissions, account linking, and review of sensitive health-data handling.

## Medium tasks — implemented

- **Personalized allergy and diet guardrails**: stored locally in the browser and cross-referenced against the deterministic ingredient knowledge base. Results are explicitly described as possible concerns, not medical guarantees.
- **Active-learning feedback loop**: users can confirm or correct a prediction. Labels, confidence, model version, and timestamp persist in the `foodlens-feedback` Docker volume. Photos are retained only when the user explicitly opts in. Corrections are candidates for a reviewed future training cycle; they do not automatically retrain the live model.
- **Explainability and uncertainty**: Grad-CAM, prediction entropy, top-1 margin, adjustable confidence thresholds, and image-quality warnings are available in the live result view.
- **Error-analysis dashboard**: the app presents held-out top-k metrics, weakest classes, major confusion pairs, and the recorded TTA ablation with repository provenance.
- **Feedback dataset pipeline**: users may explicitly opt in to retain a correction photo. The exporter creates a pending-human-review manifest; automatic retraining is intentionally not performed.

## Small scoped task — implemented

- **Nearby restaurant discovery**: opens a location-aware Google Maps search for the predicted dish so users can compare nearby ratings. FoodLens does not claim to own or calculate those rankings.
- **TTA comparison and report export**: compares one-view and three-view predictions for the current image and downloads a structured JSON inference report.
- **Architecture cost benchmark**: measures parameter count, estimated FP32 weight size, and CPU latency. Random weights mean it does not claim comparative accuracy.

## Not yet implemented

The big tasks remain research and product-development tracks. Temperature
calibration is now fitted from a seeded 11,363-image development split, evaluated
on all 25,250 official test images, and applied during live inference. Standard FP16 TFLite export remains blocked by unsupported ops in
the current mixed-precision graph and should not be presented as complete.
