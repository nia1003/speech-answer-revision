# When Should Spoken Language Models Change Their Minds?

**Evidence-sensitive answer revision in spoken human–AI interaction**
Undergraduate research, Speech Processing Laboratory, National Taiwan University · Advisor: Prof. Hung-yi Lee · Researcher: Liang-Chieh (Nia) Lee
Status: work in progress (November 2026). Results are preliminary and the LLM judge has not yet been validated against human labels.

## Overview

When a user pushes back on a spoken assistant ("Are you sure?"), the assistant can either hold its answer or change it. Changing an answer is harmful when the original answer was right and the challenge carries no real information, but it is exactly what we want when the original answer was wrong and the user supplies valid evidence. A low "flip rate" alone therefore does not mean a model is reliable.

This project studies whether speech-language models can tell these situations apart. We ask:

1. **Perception vs. reasoning.** How much accuracy do speech-language models lose when the same question is spoken instead of typed, and does the loss grow with reasoning depth?
2. **Evidence sensitivity.** After answering, does a model yield to unsupported or misleading challenges, and does it correct itself when given valid evidence?
3. **Modality.** Does a spoken challenge change these behaviors compared with the same challenge in text?

We evaluate five open speech-language models (Qwen2.5-Omni-7B, Kimi-Audio-7B, GLM-4-Voice-9B, LLaMA-Omni2-7B, Ultravox v0.4) on GSM8K (math, 1,319 questions) and MuSiQue-Ans (multi-hop factual QA, 2,417 questions), with questions spoken by cloned voices (Chatterbox TTS, verified with Whisper ASR) and responses graded by Mistral-Small-24B-Instruct.

## Key results so far

**Stage 1: text vs. speech accuracy (5 models, 3,736 paired questions).** Spoken questions reduce accuracy for most models, and the size of the gap depends strongly on the model and task. Paired McNemar tests (speech − text, percentage points):

| Model | GSM8K | MuSiQue |
|---|---:|---:|
| Qwen2.5-Omni | −2.3 (p = 0.014) | +1.4 (p = 0.10) |
| Ultravox v0.4 | **−9.7** (p < 10⁻¹⁵) | **−7.4** (p < 10⁻¹²) |
| LLaMA-Omni2 | **−15.7** (p < 10⁻²¹) | −2.9 (p = 0.002) |
| Kimi-Audio | +2.0 (p = 0.11) | +0.5 (p = 0.65) |
| GLM-4-Voice | **−10.3** (p < 10⁻¹¹) | −1.6 (p = 0.14) |

Switching from rule-based to LLM-judge grading changed three of these conclusions (e.g., Kimi-Audio's GSM8K advantage for speech lost significance), which is why grading is reported both ways.

**Stage 2: answer revision under challenge (Qwen2.5-Omni-7B, pre-registered analysis).** After the model's first answer, a follow-up turn presents unsupported doubt, invalid (misleading) evidence, or valid corrective evidence. On paired items, the model was misled by invalid evidence far less often when the challenge was spoken (GSM8K 20.2% vs. 38.0% in text; MuSiQue 14.1% vs. 39.7%; Holm-adjusted p < 10⁻¹²), and it flagged invalid evidence as unreliable much more often in speech. However, unsupported doubt also caused slightly more harmful flips in speech on MuSiQue (+3.3 pp), and the pre-registered manipulation check failed in the speech condition, so the speech results are reported but not yet interpreted. See [reports/progress-report.md](reports/progress-report.md).

## Repository structure

```
proposal/
├── proposal.md                      Research plan (English summary of plan v1.0, 2026-11-19)
├── proposal_v1.0_2026-11-19_zh.md   Full plan in Traditional Chinese
└── experiment-spec-v2_2026-10-24_zh.md   Earlier experiment specification
reports/
└── progress-report.md               Progress report (English)
experiments/
├── stage1_text_vs_speech/results/   5-model accuracy summaries, judge agreement, figures
└── stage2_evidence_revision/results/ Pre-registration, formal-run metrics and report
scripts/                             All pipeline code (see scripts/README.md)
data/                                Item sets (GSM8K + MuSiQue) and reference files
docs/lab-notebook-zh/                Checkpoint and decision records (Traditional Chinese)
```

Large artifacts (raw model outputs, synthesized audio, judge outputs, model weights) are not included.

## Methodology highlights

- **Paired design.** Every question is asked in both text and speech, so modality effects are tested within item (exact McNemar tests, Holm correction).
- **Audio quality control.** Each synthesized question is transcribed with Whisper and rejected if it does not match the text, so speech errors are not caused by bad audio.
- **Pre-registration.** For each stage-2 analysis, metrics, decision rules, and multiple-comparison families were written and hashed before any judge outputs were read; post-hoc analyses are labeled as such.
- **Grading transparency.** Rule-based and LLM-judge grades are reported side by side, together with their agreement (89.0% overall) and the cases where conclusions change.

## Limitations

- The LLM judge has not yet been validated against double-blind human labels.
- Stage 2 has been run on one model (Qwen2.5-Omni-7B) so far.
- Questions are spoken by synthetic (cloned) voices, not human recordings.

## Related work

The plan builds on studies of sycophancy (Sharma et al., ICLR 2024; SYCON-Bench, Findings of EMNLP 2025), audio-model sycophancy (SYAUDIO, arXiv:2601.23149), and rational updating under user pressure. See [proposal/proposal.md](proposal/proposal.md) for the literature positioning.
