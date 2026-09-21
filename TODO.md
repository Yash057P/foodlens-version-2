# FoodLens Project - TODO & Issue Tracker

This document tracks the pending tasks and accepted deviations for the FoodLens mini-project, serving as a local issue tracker.

## 📌 Open Issues / Pending Tasks

### [ ] Issue #1: Train Remaining Candidate Models
**Description:** 
Currently, only `EfficientNetB0` has been trained and integrated. The project synopsis requires a 5-model comparison.
**Tasks:**
- [ ] Train Custom CNN from scratch.
- [ ] Train ResNet50 using transfer learning.
- [ ] Train MobileNetV2 using transfer learning.
- [ ] Train DenseNet121 using transfer learning.
- [ ] Save models and compare validation metrics (accuracy, inference time, size) against the existing EfficientNetB0 baseline.

### [ ] Issue #2: Resolve Web Framework Deviation (Flask vs. Streamlit)
**Description:**
The synopsis explicitly stated the UI would be built using **Streamlit**. The current working implementation is built with **Flask** and HTML/JS. 
**Tasks:**
- [ ] *Decision Required:* Either migrate the existing Flask web application over to Streamlit to strictly match the synopsis, OR officially accept the Flask implementation as a permanent upgrade to the project stack.

---

## ✅ Closed / Accepted Items

### [x] Accepted Feature: Calories and Allergens
**Note:** The initial synopsis (Page 6) stated the system would *not* estimate calories or allergens. However, this was successfully implemented in the `ingredients.json` and web UI. 
**Resolution:** User has reviewed this scope creep and determined it works well. It will be kept as an "extra/bonus" feature. No removal is necessary.

### [x] Deprioritized: IEEE Paper & LaTeX Documentation
**Note:** The codebase includes a `paper/` directory with a LaTeX manuscript mapping out evaluation objectives. 
**Resolution:** User has explicitly stated to ignore the paper generation and focus purely on completing the functional mini-project (the code and the application). Evaluation tables and LaTeX compilation tasks are officially removed from the critical path. 
