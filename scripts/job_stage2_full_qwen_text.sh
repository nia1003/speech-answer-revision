#!/bin/bash
#SBATCH -J s2f_qwen_t
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
# Stage 2 FULL run, Qwen2.5-Omni-7B, round 2, given modalities, one item shard. usage: sbatch job.sh <evidence_file> <k> <N> <MODS> <tag>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
D=out/stage2_full_qwen
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
MODE=round2 REP=0 MODS=$4 SHARD=$2/$3 $HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/stage2_round2_qwen_full.py $D/ids.jsonl $1 $D/evidence_audio $D/round2_qwen_$5_shard$2.jsonl || exit 1
echo JOB_END
