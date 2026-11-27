#!/bin/bash
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 3-00:00:00
# Stage 1 baseline for llamaomni2 | glm4voice | kimiaudio (scripts/baseline_others.py).
# usage: sbatch job_baseline_other.sh <model> smoke        -> smoke 80, out/smoke80_<model>_sdpa.jsonl
#        sbatch job_baseline_other.sh <model> <k>          -> full shard k of 3, out/full_<model>_sdpa_shard<k>.jsonl
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
P=$HOME/rq4_dualcheck/envs/$1/bin/python
if [ "$2" = smoke ]; then IN=data/smoke80_items.jsonl; OUT=out/smoke80_$1_sdpa.jsonl
  if [ -e $OUT ]; then echo "$OUT EXISTS, abort"; exit 1; fi
else IN=data/speech_full_shards/full_items_shard$2.jsonl; OUT=out/full_$1_sdpa_shard$2.jsonl; fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
$P -u scripts/baseline_others.py $1 $IN out/tts_speech_final_view $OUT || exit 1
echo BASE_JOB_END $1 $2
