#!/bin/bash
#SBATCH -J s2_probe
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 0-04:00:00
# Diagnostic a probe (PREREG_2026-11-24): Qwen2.5-Omni-7B text sub-question probing on the 20 MuSiQue both-wrong smoke items.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
D=out/stage2_diag_musique; mkdir -p $D
[ -e $D/probe.jsonl ] && { echo "$D/probe.jsonl EXISTS, abort"; exit 1; }
$HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/stage2_probe_qwen.py out/stage2_smoke_v3/smoke80_v2_ids.jsonl $D/probe.jsonl || exit 1
echo JOB_END
