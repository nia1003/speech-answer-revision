#!/bin/bash
#SBATCH -J full_uv
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 3-00:00:00
# Stage 1 full, Ultravox v0_4 sdpa: text A_q / A_a / A_bc and speech C_q / C_b (final speech view). usage: sbatch job_full_ultravox.sh <k>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
$HOME/rq4_dualcheck/envs/ultravox/bin/python -u scripts/baseline_ultravox.py data/speech_full_shards/full_items_shard$1.jsonl out/tts_speech_final_view out/full_ultravox_sdpa_shard$1.jsonl
echo FULLUV_JOB_END $1
