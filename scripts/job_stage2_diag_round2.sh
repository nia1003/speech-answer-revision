#!/bin/bash
#SBATCH -J s2d_r2
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 0-04:00:00
# Diagnostics a/b: Qwen round 2 (smoke runner unchanged) on the 20 MuSiQue both-wrong items, text + speech.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
B=out/stage2_diag_musique
for d in probe ceiling; do
  [ -e $B/$d/round2_qwen.jsonl ] && { echo "$B/$d/round2_qwen.jsonl EXISTS, abort"; exit 1; }
  MODE=round2 REP=0 $HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/stage2_round2_qwen.py $B/ids_musique_both_wrong.jsonl $B/$d/evidence_final.jsonl $B/$d $B/$d/round2_qwen.jsonl || exit 1
done
echo JOB_END
