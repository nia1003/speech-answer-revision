#!/bin/bash
#SBATCH -J uv_smoke
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 6:00:00
# Ultravox v0_4 sdpa, smoke 80, all 5 runs (A_q, C_q, A_a, A_bc, C_b), final speech view; plus the longest audio (GSM8K 1077, 37 s).
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
P=$HOME/rq4_dualcheck/envs/ultravox/bin/python
for o in out/smoke80_ultravox_sdpa.jsonl out/uv_longaudio_1077.jsonl; do if [ -e $o ]; then echo "$o EXISTS, abort"; exit 1; fi; done
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
$P -u scripts/baseline_ultravox.py data/smoke80_items.jsonl out/tts_speech_final_view out/smoke80_ultravox_sdpa.jsonl || exit 1
ONLY_IDS=1077 RUNS=C_q $P -u scripts/baseline_ultravox.py data/full_items.jsonl out/tts_speech_final_view out/uv_longaudio_1077.jsonl || exit 1
echo UVSMOKE_JOB_END
