# Scripts

All pipeline code, kept flat as used during the experiments. Grouped by filename prefix:

| Prefix | Purpose |
|---|---|
| `build_*`, `make_*`, `numwords.py`, `rewrite_trunc.py` | Build item sets from GSM8K and MuSiQue; reasoning-depth labels; number-to-words normalization for speech |
| `tts_*` | Speech synthesis: Chatterbox voice cloning (main), Gemini and Kokoro TTS (alternatives), text normalization for TTS |
| `asr_*` | Whisper transcription of synthesized audio to verify each spoken question |
| `baseline_*`, `run_*`, `kimi_cut_msgend.py` | Stage 1 inference: first-round answers from the five models in text and speech |
| `score_*`, `parser_*`, `judge_*`, `apply_judge.py`, `run_judge_mathsdp.py`, `mistral_depth.py` | Grading: rule-based answer extraction and Mistral-Small-24B LLM judge (correctness, answer extraction, stance) |
| `summarize_stage1.py`, `steps_accuracy_table.py`, `plot_*`, `smoke_report.py`, `cp3_report.py` | Stage 1 summaries, paired McNemar tests, and figures |
| `stage2_*` | Stage 2 smoke runs: evidence generation (invalid / valid / unsupported), verification, round-2 inference |
| `t12_*` | Stage 2 measurement checks (T1/T2): prompt-wrapper contrast and forced-final-answer comparison |
| `s2f_*` | Stage 2 formal run (Qwen2.5-Omni-7B): runners, merging, checks, and the pre-registered metrics script `s2f_metrics.py` |
| `diag_*` | Diagnostics for individual models and failure modes |
| `job_*.sh`, `*_chain*.sh` | Slurm job files and job chains used on the lab GPU cluster |

Cluster-specific values (remote host, user name) have been replaced with placeholders such as `$REMOTE_HOST`. Model weights, raw outputs, and synthesized audio are not included in this repository.
