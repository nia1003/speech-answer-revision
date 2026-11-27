"""Plain-English version of plot_steps_accuracy.py (2026-11-23, user: no internal codes, readable English, one dataset
per figure). Same CSV, same data. Writes 4 figures: {gsm8k,musique} x {rule,judge}, PNG + PDF.
usage: python3 plot_steps_accuracy_v2.py <csv> <out_dir>"""
import sys, csv, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
rows = list(csv.DictReader(open(sys.argv[1]))); out = pathlib.Path(sys.argv[2])
MODELS = [("qwen25omni", "Qwen2.5-Omni", "#2a78d6"), ("ultravox", "Ultravox", "#eb6834"), ("llamaomni2", "LLaMA-Omni2", "#1baf7a"),
          ("kimiaudio", "Kimi-Audio", "#eda100"), ("glm4voice", "GLM-4-Voice", "#d55181")]
BINS = {"gsm8k": ["1-2", "3", "4", "5+"], "musique": ["2", "3", "4"]}
TITLE = {"gsm8k": "GSM8K (math word problems): accuracy by number of reasoning steps",
         "musique": "MuSiQue (multi-hop questions): accuracy by number of hops"}
XLAB = {"gsm8k": "Number of calculation steps in the reference solution",
        "musique": "Number of hops (facts that must be chained to reach the answer)"}
MODLAB = {"gsm8k": ("Question as text", "Question as speech"),
          "musique": ("Passages and question as text", "Passages as text, question as speech")}
SCORER = {"rule": "Scored by automatic answer matching", "judge": "Scored by an LLM judge"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11, "legend.fontsize": 10})
for scorer in ("rule", "judge"):
    for ds in ("gsm8k", "musique"):
        fig, ax = plt.subplots(figsize=(9.5, 5.6)); bins = BINS[ds]; nl = len(MODELS) * 2
        for mi, (m, name, col) in enumerate(MODELS):
            for si, mod in enumerate(("text", "speech")):
                pts = {r["step_bin"]: r for r in rows if r["scorer"] == scorer and r["dataset"] == ds and r["model"] == m and r["modality"] == mod}
                off = (mi * 2 + si - (nl - 1) / 2) * 0.025
                y = [100 * float(pts[b]["accuracy"]) for b in bins]
                lo = [y[i] - 100 * float(pts[b]["wilson95_low"]) for i, b in enumerate(bins)]
                hi = [100 * float(pts[b]["wilson95_high"]) - y[i] for i, b in enumerate(bins)]
                ax.errorbar([i + off for i in range(len(bins))], y, yerr=[lo, hi], color=col, ls="-" if mod == "text" else "--",
                            marker="o" if mod == "text" else "^", ms=5, lw=1.8, elinewidth=1, capsize=2.5)
        n = {r["step_bin"]: int(r["n"]) for r in rows if r["scorer"] == scorer and r["dataset"] == ds}
        ax.set_xticks(range(len(bins))); ax.set_xticklabels([f"{b}\n({n[b]:,} questions)" for b in bins])
        ax.set_xlabel(XLAB[ds]); ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0, 100)
        ax.grid(axis="y", color="#e1e0d9", lw=0.8); ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"{TITLE[ds]}\n{SCORER[scorer]}", loc="left")
        tl, sl = MODLAB[ds]
        h = [Line2D([], [], color=c, lw=2.5, label=nm) for _, nm, c in MODELS] + [Line2D([], [], color="none", label="")] + \
            [Line2D([], [], color="#555", ls="-", marker="o", label=tl), Line2D([], [], color="#555", ls="--", marker="^", label=sl)]
        ax.legend(handles=h, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
        fig.text(0.01, 0.005, "Error bars: 95% confidence intervals. Same questions for every model and both input types.",
                 fontsize=10, color="#555")
        fig.tight_layout(rect=(0, 0.03, 1, 1))
        for ext in ("png", "pdf"):
            fig.savefig(out / f"accuracy_by_steps_{ds}_{scorer}.{ext}", dpi=200, bbox_inches="tight")
        plt.close(fig); print("saved", ds, scorer)
