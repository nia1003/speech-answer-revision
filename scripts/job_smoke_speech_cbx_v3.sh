#!/bin/bash
#SBATCH -J smk_Cq_v3
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 6:00:00
# speech smoke, GSM8K C_q only, with v3 question audio (all numbers as words; out/tts_full_v3). Qwen2.5-Omni-7B sdpa.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
V=out/tts_cbx_v3_view
if [ -e $V ]; then echo "VIEW EXISTS, abort"; exit 1; fi
mkdir -p $V/question
for f in $HOME/rq4_v2/out/tts_full_v3/question/gsm8k_*.wav; do ln -s $f $V/question/; done
python3 -c "
import json,glob
with open('$V/manifest.jsonl','w') as f:
  for p in sorted(glob.glob('out/tts_full_v3/manifest_shard*.jsonl')):
    for l in open(p):
      m=json.loads(l); m['kind']='question'; f.write(json.dumps(m)+'\n')"
ls $V/question | wc -l
OUT=out/smoke80_speech_cbx_v3_qwen25omni_sdpa.jsonl
if [ -e $OUT ]; then echo "OUT EXISTS, abort"; exit 1; fi
RUNS=C_q $HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/baseline_qwen_v3.py data/smoke80_items.jsonl $V $OUT
echo SMKV3_JOB_END
