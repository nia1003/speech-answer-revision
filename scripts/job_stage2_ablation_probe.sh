#!/bin/bash
#SBATCH -J s2a_probe
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 0-04:00:00
# Ablation probe (out/stage2_ablation_musique/PREREG.md), Qwen2.5-Omni-7B text, 120 items of S.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
D=out/stage2_ablation_musique
[ -e $D/probe.jsonl ] && { echo "$D/probe.jsonl EXISTS, abort"; exit 1; }
$HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/stage2_ablation_probe.py $D/S_ids.jsonl $D/probe.jsonl || exit 1
echo JOB_END
