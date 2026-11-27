"""Plot accuracy by step bin from steps_accuracy_table.py's CSV (2026-11-23). One figure per scorer (rule / judge),
two panels (GSM8K, MuSiQue), 10 lines (5 models x text solid / speech dashed), Wilson 95% CI error bars,
n under each x label, legend outside, >=10pt fonts, PNG + PDF.
usage: python3 plot_steps_accuracy.py <csv> <out_dir>"""
import sys, csv, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
rows = list(csv.DictReader(open(sys.argv[1]))); out = pathlib.Path(sys.argv[2])
MODELS = [("qwen25omni", "Qwen2.5-Omni", "#2a78d6"), ("ultravox", "Ultravox", "#eb6834"), ("llamaomni2", "LLaMA-Omni2", "#1baf7a"),
          ("kimiaudio", "Kimi-Audio", "#eda100"), ("glm4voice", "GLM-4-Voice", "#d55181")]
BINS = {"gsm8k": ["1-2", "3", "4", "5+"], "musique": ["2", "3", "4"]}
TITLE = {"gsm8k": "GSM8K (text A_q / speech C_q)", "musique": "MuSiQue (text A_bc / speech C_b)"}
XLAB = {"gsm8k": "Reasoning steps (<<>> in gold solution)", "musique": "Hops"}
SC = {"rule": "Rule scoring (CP_B17)", "judge": "LLM judge, Mistral-Small-24B prompt v2 (CP_B18)"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "legend.fontsize": 10})
for scorer in ("rule", "judge"):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
    for ax, ds in zip(axes, ("gsm8k", "musique")):
        bins = BINS[ds]; nmods = len(MODELS) * 2
        for mi, (m, name, col) in enumerate(MODELS):
            for si, mod in enumerate(("text", "speech")):
                pts = {r["step_bin"]: r for r in rows if r["scorer"] == scorer and r["dataset"] == ds and r["model"] == m and r["modality"] == mod}
                off = (mi * 2 + si - (nmods - 1) / 2) * 0.025       # small dodge so error bars don't overlap
                xs = [i + off for i in range(len(bins))]
                y = [100 * float(pts[b]["accuracy"]) for b in bins]
                lo = [y[i] - 100 * float(pts[b]["wilson95_low"]) for i, b in enumerate(bins)]
                hi = [100 * float(pts[b]["wilson95_high"]) - y[i] for i, b in enumerate(bins)]
                ax.errorbar(xs, y, yerr=[lo, hi], color=col, ls="-" if mod == "text" else "--", marker="o" if mod == "text" else "^",
                            ms=5, lw=1.8, elinewidth=1, capsize=2.5, alpha=0.95)
        n = {r["step_bin"]: r["n"] for r in rows if r["scorer"] == scorer and r["dataset"] == ds}
        ax.set_xticks(range(len(bins))); ax.set_xticklabels([f"{b}\nn={int(n[b]):,}" for b in bins])
        ax.set_title(TITLE[ds]); ax.set_xlabel(XLAB[ds]); ax.set_ylim(0, 100); ax.grid(axis="y", color="#e1e0d9", lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Accuracy (%)")
    h = [Line2D([], [], color=c, lw=2.5, label=nm) for _, nm, c in MODELS] + [Line2D([], [], color="none", label="")] + \
        [Line2D([], [], color="#555", ls="-", marker="o", label="Text"), Line2D([], [], color="#555", ls="--", marker="^", label="Speech")]
    fig.legend(handles=h, loc="center left", bbox_to_anchor=(0.86, 0.5), frameon=False)
    fig.suptitle(f"Accuracy by reasoning depth — {SC[scorer]}; error bars = Wilson 95% CI", fontsize=12)
    fig.tight_layout(rect=(0, 0, 0.85, 0.95))
    for ext in ("png", "pdf"):
        fig.savefig(out / f"steps_accuracy_{scorer}.{ext}", dpi=200, bbox_inches="tight")
    print("saved", scorer)
