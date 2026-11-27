#!/bin/bash
#SBATCH -J s2a_r2
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 0-08:00:00
# Ablation round 2 (out/stage2_ablation_musique/PREREG.md), text only.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
D=out/stage2_ablation_musique
$HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/stage2_ablation_round2.py $D/conditions.jsonl $D/round2.jsonl || exit 1
echo JOB_END
