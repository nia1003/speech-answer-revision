# Research Plan: Evidence-Sensitive Answer Revision in Spoken Language Models

English summary of the research plan v1.0 (2026-11-19). The full plan in Traditional Chinese is in [proposal_v1.0_2026-11-19_zh.md](proposal_v1.0_2026-11-19_zh.md). This is a working draft for lab discussion, not a statement of established findings.

## 1. Positioning

It is already known that text and audio language models can be swayed by a follow-up such as "Are you sure?". The question here is different: **when a user challenges a spoken assistant, can the model distinguish pressure that carries no information from feedback that genuinely corrects it?** And does having already stated an answer make the model resist harmful flips while also making it less willing to fix real mistakes?

Central claim to test: *answer stability is not the same as reliability.* A good system should rarely abandon a correct answer under unsupported pressure, and should often fix a wrong answer when given valid new evidence.

Planned contributions:

- **C1** An evidence-sensitive revision framework that separates harmful yielding from rational correction.
- **C2** A controlled commitment × evidence comparison that tests for commitment-related rigidity.
- **C3** An account of how reasoning demand and initial uncertainty moderate revision behavior.
- **C4** Audio, text, and transcript controls that separate speech-perception errors from differences in decision-making.

## 2. Research questions and hypotheses

| RQ | Question | Hypothesis |
|---|---|---|
| RQ1 | Does prior answer commitment change revision behavior? | Stating an answer lowers revision overall, possibly reducing both harmful yielding and beneficial correction. |
| RQ2 | Does the model revise selectively according to evidence quality? | Valid evidence increases correct revisions; unsupported or misleading challenges should cause few harmful flips. Main test: Evidence × Commitment interaction. |
| RQ3 | Do reasoning demand and initial uncertainty moderate revision? | Harder or more uncertain items are more vulnerable to unsupported challenges; domain effects may shrink after controlling for baseline accuracy. |
| RQ4 | Do spoken and text follow-ups differ in evidence discrimination? | There may be modality-specific differences, which must be checked against ASR errors and model architecture. |

Competing explanations to rule out: response length, visibility of the original answer, prompt position, output format, context truncation, speech-recognition errors, and item difficulty.

## 3. Design

**Outcomes.** For each sample: original answer and correctness, follow-up content, evidence validity, final answer and correctness, whether the answer changed, and refusals. Transitions are classified as C→C, C→W, W→C, and W→W; ambiguous or unextractable answers are labeled separately rather than counted as correct or wrong.

**Evidence quality.**
- E0 *Unsupported challenge* — e.g., "Are you sure?", with no new verifiable information.
- E1 *Invalid evidence* — a specific but falsifiable wrong step or counterexample.
- E2 *Valid corrective evidence* — verifiable evidence that actually overturns the original wrong answer.
- A neutral, length-matched control turn as a baseline.

**Commitment.** C1 answer stated; C2 answer plus justification; with a length-matched control and an answer-withheld diagnostic.

**Tasks and modality.** Math (GSM8K, single- and multi-step) and factual QA (MuSiQue, 2–4 hops); text vs. clean TTS vs. human speech, with a transcript-of-actual-audio condition to control for listening errors.

## 4. Experiments

- **Experiment 0 — Audit and replication.** Recompute earlier results (initial accuracy, flip rates, C→W, W→C, timing, text vs. audio, speaker effects) under one schema, and check judge labels against human annotation.
- **Experiment 1 — Evidence × Commitment (main).** Matched prompts for C1/C2 × E0/E1/E2 on the same items; primary analyses on C→W under E0/E1 and W→C under E2.
- **Experiment 2 — Moderators.** Math vs. factual × low/high reasoning demand; item difficulty and sampling entropy.
- **Experiment 3 — Speech specificity.** The same lexical content as text, clean TTS, and human recording, with ASR transcripts as a fidelity check.
- **Experiment 4 — Within-utterance interruption** (only for systems that support true streaming barge-in); otherwise reported as a simulated intervention.

## 5. Metrics and analysis

- **Unsupported yielding** U = P(C→W | initially correct, unsupported challenge).
- **Rational correction** R = P(W→C | initially wrong, valid evidence).

Both are always reported together rather than combined into one score. Analysis uses item-clustered confidence intervals and mixed-effects logistic regression (Evidence, Commitment, their interaction, difficulty, modality; item random intercepts; models as fixed effects). Risk differences with 95% CIs are the main presentation; secondary tests are corrected for multiple comparisons. Null results for speaker gender or emotion are reported with equivalence tests (e.g., ±5 pp) rather than p > 0.05 alone.

## 6. Quality assurance and reproducibility

A rubric covers answer extraction, correctness, evidence validity, whether the evidence was used, and undecidable cases. Stratified samples from every cell are double-blind annotated, and the LLM judge is calibrated against them. Every run logs model version, prompt hash, seed, decoding settings, audio hash, transcripts, timestamps, and errors.

## 7. Decision rules

| Outcome | Implication |
|---|---|
| Commitment lowers both U and R | Evidence of commitment-related rigidity; run causal ablations |
| Commitment lowers U but not R | Commitment may act as a defense; study adaptive timing |
| Timing effect disappears after controlling prompt length and position | Contribution becomes a benchmark-confound correction |
| Math effect disappears after difficulty matching | Focus on difficulty-aware revision |
| Speech–text differences explained by ASR | Focus on separating perception from decision |
| No stable main effect, opposite across models | Report model heterogeneity |

## 8. Milestones

M1 data audit → M2 literature matrix → M3 pilot (120 items, 2 models, 1,440 responses) → M4 scale decision → M5 full analysis → M6 paper.

## Selected references

- Sharma et al. Towards Understanding Sycophancy in Language Models. ICLR 2024.
- Yao et al. Hearing is Believing? Evaluating and Analyzing Audio Language Model Sycophancy with SYAUDIO. arXiv:2601.23149, 2026.
- Measuring Sycophancy of Language Models in Multi-turn Dialogues. Findings of EMNLP 2025.
- Accounting for Sycophancy in Language Model Uncertainty Estimation. Findings of NAACL 2025.
- Sycophancy Suppression Can Impair Rational Updating. Findings of EMNLP 2026.
- Do Audio LLMs Really LISTEN, or Just Transcribe? EACL 2026.

References are from the planning draft and still need to be checked against their final published versions.
