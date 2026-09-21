"""Compute FOODLENS real held-out metrics and paper figures from cached predictions.

Reads only actually-measured artifacts:
  data/preprocessed/food101_preds.npz        (Y: 25,250 labels, probs: 25,250x101)
  data/preprocessed/full_test_cache.npz      (X: 25,250 RGB images, Y labels)
  webapp/data/classes_101.json               (index <-> class name mapping)

Everything written is computed from those files - no numbers are invented.
"""
import json
import sys
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.metrics import precision_score, recall_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FIGS = PAPER / "figures"
TABLES = PAPER / "tables"
META = ROOT / "webapp" / "data" / "classes_101.json"

for _d in (FIGS, TABLES):
    _d.mkdir(parents=True, exist_ok=True)

PRED = ROOT / "data" / "preprocessed" / "food101_preds.npz"
CACHE = ROOT / "data" / "preprocessed" / "full_test_cache.npz"

print("loading cached predictions ...", flush=True)
d = np.load(PRED)
Y = d["Y"]
P = d["probs"]
assert P.shape == (25250, 101), P.shape

cmap = json.load(open(META, encoding="utf-8"))["index_to_name"]
NAMES = [cmap[str(i)] for i in range(101)]
IDX = {n: i for i, n in enumerate(NAMES)}

y_pred = P.argmax(1)
top3 = np.argsort(P, axis=1)[:, -3:]
top5 = np.argsort(P, axis=1)[:, -5:]

acc1 = accuracy_score(Y, y_pred)
acc3 = float(np.mean([Y[i] in top3[i] for i in range(len(Y))]))
acc5 = float(np.mean([Y[i] in top5[i] for i in range(len(Y))]))
prec = precision_score(Y, y_pred, average="macro", zero_division=0)
rec = recall_score(Y, y_pred, average="macro", zero_division=0)
f1 = f1_score(Y, y_pred, average="macro", zero_division=0)

print(f"Top-1 {acc1:.4f} | Top-3 {acc3:.4f} | Top-5 {acc5:.4f}")
print(f"Macro P {prec:.4f} | Macro R {rec:.4f} | Macro F1 {f1:.4f}")

report = classification_report(
    Y, y_pred, target_names=NAMES, digits=4, zero_division=0
)
print(report)
(report_public := PAPER / "tables" / "classification_report_full.txt")
report_public.write_text(report, encoding="utf-8")

per_class = {}
for i in range(101):
    tp = int(np.sum((Y == i) & (y_pred == i)))
    fp = int(np.sum((Y != i) & (y_pred == i)))
    fn = int(np.sum((Y == i) & (y_pred != i)))
    sup = int(np.sum(Y == i))
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    per_class[NAMES[i]] = {
        "accuracy": round(tp / sup, 4), "precision": round(p, 4),
        "recall": round(r, 4), "f1": round(f, 4), "support": sup,
    }

ppl = sorted(per_class.items(), key=lambda kv: kv[1]["accuracy"])
worst10 = ppl[:10]
best10 = ppl[-10:][::-1]
print("\nWorst 10:")
for n, v in worst10:
    print(f"  {n:24s} acc={v['accuracy']} f1={v['f1']}")

print("\nBest 10:")
for n, v in best10:
    print(f"  {n:24s} acc={v['accuracy']} f1={v['f1']}")

cm = confusion_matrix(Y, y_pred)

confused = []
for a in range(101):
    for b in range(101):
        if a != b and cm[a, b] > 0:
            confused.append((int(cm[a, b]), NAMES[a], NAMES[b]))
confused.sort(reverse=True)
print("\nMost confused (true -> predicted):")
for cnt, a, b in confused[:12]:
    print(f"  {a:22s} -> {b:22s} {cnt}")

# warning-policy illustration on the held-out test predictions (NOT the
# validation-selected threshold; shown only as a behavioural illustration)
print("\nwarning behaviour illustration on test predictions:")
for tau in (0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6):
    keep = P.max(1) >= tau
    cov = float(keep.mean())
    acc_keep = float(accuracy_score(Y[keep], y_pred[keep])) if keep.any() else float("nan")
    print(f"  tau={tau:.2f} coverage={cov:.3f} top1@retained={acc_keep:.4f}")

out = {
    "model": "EfficientNetB0",
    "dataset": "Food-101 (101 classes)",
    "test_size": int(len(Y)),
    "top1": round(acc1, 4),
    "top3": round(acc3, 4),
    "top5": round(acc5, 4),
    "macro_precision": round(prec, 4),
    "macro_recall": round(rec, 4),
    "macro_f1": round(f1, 4),
    "per_class": per_class,
    "worst_classes": [[n, v["accuracy"]] for n, v in worst10],
    "best_classes": [[n, v["accuracy"]] for n, v in best10],
    "most_confused": [[n, a, b] for n, a, b in confused[:15]],
    "warning_illustration": {
        str(tau): {
            "coverage": round(float((P.max(1) >= tau).mean()), 4),
            "retained_top1": round(
                float(accuracy_score(Y[P.max(1) >= tau], y_pred[P.max(1) >= tau])), 4
            )
            if (P.max(1) >= tau).any()
            else None,
        }
        for tau in (0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6)
    },
}
(ROOT / "results" / "food101_metrics.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("\n-> results/food101_metrics.json")

# ----------------------------------------------------------------------------
# FIGURES (all from real data)
# ----------------------------------------------------------------------------

plt.rcParams.update({"font.size": 9, "figure.dpi": 150})

# 1. Full confusion matrix (high resolution)
fig, ax = plt.subplots(figsize=(20, 18))
im = ax.imshow(cm, cmap="Blues", aspect="equal")
ax.set_xticks(range(101)); ax.set_yticks(range(101))
ax.set_xticklabels(NAMES, rotation=90, fontsize=4)
ax.set_yticklabels(NAMES, fontsize=4)
ax.set_xlabel("Predicted class")
ax.set_ylabel("True class")
ax.set_title("EfficientNetB0 confusion matrix on Food-101 test set (25,250 images)")
fig.colorbar(im, fraction=0.02, pad=0.01)
fig.savefig(FIGS / "fig_confusion_full.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGS / "fig_confusion_full.pdf", bbox_inches="tight")
plt.close(fig)

# 2. Focused view of the most confused classes
conf_a = confused[0][1]; conf_b = confused[0][2]
ia, ib = IDX[conf_a], IDX[conf_b]
focus = sorted({ia, ib})
fig, ax = plt.subplots(figsize=(3.6, 3.2))
sel = cm[np.ix_(focus, focus)]
im = ax.imshow(sel, cmap="Reds")
ax.set_xticks(range(2)); ax.set_yticks(range(2))
ax.set_xticklabels([conf_a, conf_b], fontsize=8)
ax.set_yticklabels([conf_a, conf_b], fontsize=8)
for i in range(2):
    for j in range(2):
        ax.text(j, i, int(sel[i, j]), ha="center", va="center", fontsize=9)
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
ax.set_title(f"Most confused pair: {conf_a} vs {conf_b}")
fig.tight_layout()
fig.savefig(FIGS / "fig_confused_pair.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGS / "fig_confused_pair.pdf", bbox_inches="tight")
plt.close(fig)

# 3. Misclassified example montage (9 images) - uses real test pixels
X = np.load(CACHE)["X"]
mis_idx = np.where(y_pred != Y)[0]
montage = []
labels, preds = [], []
for i in mis_idx:
    if len(montage) == 9:
        break
    if (P[i].max() >= 0.5):  # confident but wrong - informative for error analysis
        montage.append(i); labels.append(NAMES[Y[i]]); preds.append(NAMES[y_pred[i]])
if len(montage) < 9:
    for i in mis_idx:
        if len(montage) == 9:
            break
        if i not in montage:
            montage.append(i); labels.append(NAMES[Y[i]]); preds.append(NAMES[y_pred[i]])
fig, axes = plt.subplots(3, 3, figsize=(7.5, 7.5))
for ax, i, t, p in zip(axes.ravel(), montage, labels, preds):
    ax.imshow(X[i])
    ax.set_title(f"true: {t.replace('_',' ')}\npred: {p.replace('_',' ')}", fontsize=7)
    ax.axis("off")
fig.suptitle("Representative misclassified images (held-out test set)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(FIGS / "fig_misclassified.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGS / "fig_misclassified.pdf", bbox_inches="tight")
plt.close(fig)

# 4. Top-3 prediction example (pizza test image)
i0 = int(np.where(Y == IDX["pizza"])[0][0])
fig, axes = plt.subplots(1, 2, figsize=(7, 3.2), gridspec_kw={"width_ratios": [1, 1.5]})
axes[0].imshow(X[i0])
axes[0].set_title(f"test image (true: pizza)")
axes[0].axis("off")
order = np.argsort(P[i0])[::-1][:3]
axes[1].barh([0, 1, 2][::-1], [round(float(P[i0][o]), 3) for o in order[::-1]], color="steelblue")
axes[1].set_yticks([0, 1, 2]); axes[1].set_yticklabels([NAMES[o].replace("_", " ") for o in order[::-1]], fontsize=8)
axes[1].set_xlim(0, 1)
axes[1].set_xlabel("model score")
axes[1].set_title("Top-3 model scores")
fig.tight_layout()
fig.savefig(FIGS / "fig_top3_example.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGS / "fig_top3_example.pdf", bbox_inches="tight")
plt.close(fig)

# 5. Warning illustration curve (coverage and retained accuracy vs tau)
taus = np.linspace(0.2, 0.9, 71)
covs = [(P.max(1) >= t).mean() for t in taus]
accs = [accuracy_score(Y[P.max(1) >= t], y_pred[P.max(1) >= t]) if (P.max(1) >= t).any() else np.nan for t in taus]
fig, ax1 = plt.subplots(figsize=(4.5, 3.2))
ax1.plot(taus, [c * 100 for c in covs], label="retained coverage (%)", color="tab:blue")
ax1.set_xlabel("warning threshold $\\tau$")
ax1.set_ylabel("coverage (%)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.set_ylim(0, 105)
ax2 = ax1.twinx()
ax2.plot(taus, [a * 100 if a == a else np.nan for a in accs], label="top-1 accuracy of retained (%)", color="tab:red")
ax2.set_ylabel("retained accuracy (%)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")
ax2.set_ylim(0, 105)
ax1.axvline(0.45, color="grey", ls="--", lw=0.8)
ax1.text(0.455, 5, "app req. $\\tau=0.45$", fontsize=7, color="grey")
fig.suptitle("Warning policy behaviour (illustrated on test predictions)", fontsize=10)
fig.tight_layout()
fig.savefig(FIGS / "fig_warning_curve.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGS / "fig_warning_curve.pdf", bbox_inches="tight")
plt.close(fig)

print("\nfigures written to", FIGS)

# ----------------------------------------------------------------------------
# LaTeX TABLE SNIPPETS (values from measured data)
# ----------------------------------------------------------------------------

def pct(x, d=2):
    return f"{100 * x:.{d}f}\\%"


rows = []
for n, v in per_class.items():
    rows.append((n, pct(v["accuracy"]), pct(v["precision"]), pct(v["recall"]), pct(v["f1"]), int(v["support"])))
rows.sort(key=lambda r: -float(r[1].replace("\\%", "")))
sel = rows[:15] + [("(\\dots)", "--", "--", "--", "--", "--")] + rows[-15:]
body = "\n".join(
    f"{n.replace('_', chr(92)+'textunderscore')} & {a} & {p} & {r} & {f} & {s} \\\\"
    for n, a, p, r, f, s in sel
)
tbl = (
    "\\begin{table*}[t]\n\\centering\n\\caption{Per-class test performance of the deployed "
    "EfficientNetB0 model: the 15 best and 15 worst classes of 101 by accuracy "
    "(support = 250 test images per class).}\n"
    "\\label{tbl:perclass}\n\\small\n"
    "\\begin{tabular}{lccccr}\n\\toprule\nClass & Acc & Prec & Rec & F1 & Supp \\\\\n\\midrule\n"
    + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
)
(TABLES / "table_per_class.tex").write_text(tbl, encoding="utf-8")

with open(ROOT / "results" / "food101_metrics.json") as f:
    summary = json.load(f)
fs = [
    ("\\textbf{Test images}", f"{summary['test_size']:,}"),
    ("\\textbf{Top-1 accuracy}", pct(summary["top1"])),
    ("\\textbf{Top-3 accuracy}", pct(summary["top3"])),
    ("\\textbf{Top-5 accuracy}", pct(summary["top5"])),
    ("\\textbf{Macro precision}", pct(summary["macro_precision"])),
    ("\\textbf{Macro recall}", pct(summary["macro_recall"])),
    ("\\textbf{Macro F1-score}", pct(summary["macro_f1"])),
]
body = "\n".join(f"{k} & {v} \\\\" for k, v in fs)
tbl = (
    "\\begin{table}[t]\n\\centering\n\\caption{Measured held-out test performance.}\n"
    "\\label{tbl:testperf}\n\\begin{tabular}{lc}\n\\toprule\nMetric & Value \\\\\n\\midrule\n"
    + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
)
(TABLES / "table_test_performance.tex").write_text(tbl, encoding="utf-8")

worst_rows = "\n".join(
    f"{n.replace('_', chr(92)+'textunderscore')} & {pct(a)} \\\\" for n, a in summary["worst_classes"]
)
tbl = (
    "\\begin{table}[t]\n\\centering\n\\caption{Worst-performing classes (by per-class accuracy on "
    "the held-out test set).}\n\\label{tbl:worst}\n\\begin{tabular}{lc}\n\\toprule\nClass & Accuracy \\\\\n\\midrule\n"
    + worst_rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
)
(TABLES / "table_worst_classes.tex").write_text(tbl, encoding="utf-8")

conf_rows = "\n".join(
    f"{a.replace('_', chr(92)+'textunderscore')} & {b.replace('_', chr(92)+'textunderscore')} & {c} \\\\"
    for c, a, b in summary["most_confused"][:8]
)
tbl = (
    "\\begin{table}[t]\n\\centering\n\\caption{Most confused classes (true label predicted as a "
    "different class), counted on the held-out test set.}\n\\label{tbl:confused}\n"
    "\\begin{tabular}{lcc}\n\\toprule\nTrue class & Predicted class & Images \\\\\n\\midrule\n"
    + conf_rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
)
(TABLES / "table_confused_classes.tex").write_text(tbl, encoding="utf-8")

print("tables written to", TABLES)
print("\nDONE")