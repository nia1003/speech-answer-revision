#!/bin/bash
#SBATCH -J full_C_qwen
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 3-00:00:00
# Stage 1 full speech condition, Qwen2.5-Omni-7B sdpa: GSM8K C_q (v3/v4 audio), MuSiQue C_b (text paragraphs + audio question).
# usage: sbatch job_full_speech_qwen.sh <k>   (item shard k of 3; resumable)
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
RUNS=C_q,C_b $HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/baseline_qwen_v3.py data/speech_full_shards/full_items_shard$1.jsonl out/tts_speech_final_view out/full_speechC_qwen25omni_sdpa_shard$1.jsonl
echo FULLC_JOB_END $1
