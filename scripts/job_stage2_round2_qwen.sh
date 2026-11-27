#!/bin/bash
#SBATCH -J s2_qwen_r2
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 0-12:00:00
# Stage 2 smoke step 4, Qwen2.5-Omni-7B (same env/settings as stage 1): round-1 rerun (check 3), round 2 rep 0, rep 1 (check 6).
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
D=out/stage2_smoke_v3; PY=$HOME/rq4_dualcheck/envs/qwen25omni/bin/python
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
for o in $D/round1_rerun_qwen.jsonl $D/round2_qwen_rep0.jsonl $D/round2_qwen_rep1.jsonl; do [ -e $o ] && { echo "$o EXISTS, abort"; exit 1; }; done
MODE=round1 $PY -u scripts/stage2_round2_qwen.py $D/smoke80_v2_ids.jsonl $D/smoke80_evidence_final_audio.jsonl $D/evidence_audio $D/round1_rerun_qwen.jsonl || exit 1
MODE=round2 REP=0 $PY -u scripts/stage2_round2_qwen.py $D/smoke80_v2_ids.jsonl $D/smoke80_evidence_final_audio.jsonl $D/evidence_audio $D/round2_qwen_rep0.jsonl || exit 1
MODE=round2 REP=1 $PY -u scripts/stage2_round2_qwen.py $D/smoke80_v2_ids.jsonl $D/smoke80_evidence_final_audio.jsonl $D/evidence_audio $D/round2_qwen_rep1.jsonl || exit 1
echo JOB_END
