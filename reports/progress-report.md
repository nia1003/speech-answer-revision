# Progress Report (as of 2026-11-27)

This report summarizes the two completed stages. Detailed records in Traditional Chinese are in [`docs/lab-notebook-zh/`](../docs/lab-notebook-zh/) (Stage 1: `CP_B17`, `CP_B18`; Stage 2: `CP_S2_*`, `PREREG_*`). **All judge-based numbers are provisional: the LLM judge has not yet been validated against human labels.**

## 1. Setup

| Item | Setting |
|---|---|
| Models | Qwen2.5-Omni-7B, Kimi-Audio-7B, GLM-4-Voice-9B, LLaMA-Omni2-7B, Ultravox v0.4 |
| Items | GSM8K test (1,319; reasoning steps 1–2 / 3 / 4 / 5+) and MuSiQue-Ans validation, answerable (2,417; 2 / 3 / 4 hops) |
| Speech input | Questions cloned with Chatterbox TTS, verified by Whisper transcription; numbers normalized to spoken form |
| Decoding | Greedy, text output |
| Grading | Rule-based extraction and Mistral-Small-24B-Instruct-2501 judge (bf16, greedy, zero-shot), reported side by side |
| Statistics | Paired exact McNemar tests; Wilson 95% CIs; Holm correction within pre-registered families |

## 2. Stage 1: Does speaking the question change accuracy?

Accuracy (LLM judge; rule-based grading in parentheses):

| Model | GSM8K text | GSM8K speech | MuSiQue text | MuSiQue speech |
|---|---:|---:|---:|---:|
| Qwen2.5-Omni | 86.2 (79.0) | 83.9 (77.0) | 58.4 (54.6) | 59.9 (56.0) |
| Ultravox | 85.7 (77.0) | 76.0 (69.1) | 65.5 (70.9) | 58.2 (60.2) |
| LLaMA-Omni2 | 54.1 (46.3) | 38.4 (34.6) | 58.5 (51.1) | 55.6 (47.9) |
| Kimi-Audio | 79.8 (74.0) | 81.7 (79.1) | 62.2 (64.0) | 62.7 (59.1) |
| GLM-4-Voice | 37.8 (35.4) | 27.4 (25.9) | 43.9 (38.6) | 42.3 (35.9) |

Paired speech − text gaps (pp, LLM judge) and by reasoning depth:

| Model | GSM8K | p | MuSiQue | p | GSM8K by steps 1–2 / 3 / 4 / 5+ | MuSiQue by hops 2 / 3 / 4 |
|---|---:|---:|---:|---:|---|---|
| Qwen2.5-Omni | −2.3 | 0.014 | +1.4 | 0.097 | −2.6 / −1.1 / −3.4 / −1.8 | +1.9 / +1.2 / +0.5 |
| Ultravox | −9.7 | 3e-16 | −7.4 | 3e-13 | −9.2 / −7.4 / −10.3 / −13.8 | −8.3 / −7.4 / −4.4 |
| LLaMA-Omni2 | −15.7 | 1e-22 | −2.9 | 0.002 | −16.4 / −12.6 / −20.7 / −10.2 | −3.4 / −1.6 / −4.0 |
| Kimi-Audio | +2.0 | 0.11 | +0.5 | 0.65 | −0.2 / +3.3 / +4.8 / +0.4 | −0.2 / +0.9 / +2.0 |
| GLM-4-Voice | −10.3 | 1e-12 | −1.6 | 0.14 | −13.7 / −11.8 / −5.9 / −7.6 | −2.0 / −0.4 / −2.5 |

Observations:
- The speech penalty is large for Ultravox, LLaMA-Omni2, and GLM-4-Voice on math, and small or absent for Qwen2.5-Omni and Kimi-Audio.
- The gap does not grow consistently with reasoning depth, so the loss is not simply proportional to the number of reasoning steps.
- Rule-based and judge grades agree on 89.0% of 49,442 responses. The rule grader misses numbers written as words and picks the wrong number in multi-number answers. Changing the grader reversed three conclusions (Kimi-Audio GSM8K and MuSiQue, GLM-4-Voice MuSiQue), so grading choice must be reported.

Figures: [`experiments/stage1_text_vs_speech/results/figures/`](../experiments/stage1_text_vs_speech/results/figures/).

## 3. Stage 2: Does the model revise its answer for the right reasons?

**Design (Qwen2.5-Omni-7B, formal run).** After the model's first answer, a second turn delivers one of three kinds of follow-up, in text or speech:
- *Unsupported* — doubt without new information ("Are you sure?").
- *Invalid evidence* — a specific but wrong claim (GSM8K: misread quantity, wrong operation, or wrong previous result; MuSiQue: substituted entity).
- *Valid corrective evidence* — GSM8K only; the MuSiQue definition is being revised.

A third turn asks for a forced final answer. Metrics were fixed in a pre-registration written before any judge output was read:
- **MSS** (misleading susceptibility) = P(wrong after | correct before, invalid evidence)
- **CRS** (correction rate) = P(correct after | wrong before, valid evidence)
- **Unsupported C→W / W→C** = harmful flips and spontaneous corrections after unsupported doubt

**Results** (primary grading; n/N with Wilson 95% CI):

| Metric | Text | Speech |
|---|---|---|
| GSM8K MSS | 261/687 = 38.0% [34.4, 41.7] | 119/589 = 20.2% [17.2, 23.6] |
| GSM8K CRS | 54/134 = 40.3% [32.4, 48.8] | 34/127 = 26.8% [19.8, 35.1] |
| GSM8K unsupported C→W | 26.7% | 27.5% |
| MuSiQue MSS | 370/933 = 39.7% [36.6, 42.8] | 131/931 = 14.1% [12.0, 16.5] |
| MuSiQue unsupported C→W | 12.5% | 16.3% |

Paired speech − text comparisons (Holm-corrected over 13 pre-registered tests):
- MSS is lower in speech: GSM8K −17.9 pp (p = 1.2e-13), MuSiQue −24.4 pp (p = 5.5e-34).
- Unsupported C→W on MuSiQue is higher in speech: +3.3 pp (p = 0.036).
- Valid evidence produces far more corrections than unsupported doubt (GSM8K text +38.8 pp, speech +26.8 pp; both p < 10⁻⁸).

**Interpretation and caveats.**
- The pre-registered manipulation check passed for text on both datasets but failed for speech, so the speech MSS and CRS are reported but not interpreted.
- A post-hoc look explains part of the failure: almost all GSM8K "unsupported C→W" cases are non-answers ("Yeah, I'm pretty sure…") without a restated number. With forced final answers, unsupported C→W drops to about 1%. The check compared metrics on different grading scales, which is a design flaw recorded in the report rather than corrected after the fact.
- In speech, the model labeled invalid evidence as unreliable far more often (MuSiQue 79.4% vs. 15.4% in text). Because unsupported doubt also caused slightly more harmful flips in speech, "less misled in speech" cannot yet be read as better evidence discrimination.

Full numbers: [`experiments/stage2_evidence_revision/results/metrics_formal.txt`](../experiments/stage2_evidence_revision/results/metrics_formal.txt); pre-registration: [`PREREG_4.md`](../experiments/stage2_evidence_revision/results/PREREG_4.md).

## 4. Next steps

1. Double-blind human annotation of judge outputs (50 per dataset) before any claims rely on the judge.
2. Redefine valid evidence for MuSiQue so that it is sufficient to overturn a multi-hop answer.
3. Fix the manipulation check to use the same grading scale on both sides, then extend Stage 2 to the other four models.
4. Add the answer-commitment manipulation (answer only vs. answer plus justification) from the research plan.
