#!/bin/bash
#SBATCH -J smk_C_cbx
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 6:00:00
# speech-condition smoke 80 with the full Chatterbox question audio (out/tts_full), Qwen2.5-Omni-7B sdpa; C_q + C_b only
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
V=out/tts_cbx_view
if [ ! -e $V ]; then
  mkdir -p $V && ln -s $HOME/rq4_v2/out/tts_full/question $V/question
  python3 -c "
import json,glob
with open('$V/manifest.jsonl','w') as f:
  for p in sorted(glob.glob('out/tts_full/manifest_shard*.jsonl')):
    for l in open(p):
      m=json.loads(l); m['kind']='question'; f.write(json.dumps(m)+'\n')"
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
RUNS=C_q,C_b $HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/baseline_qwen_v3.py data/smoke80_items.jsonl $V out/smoke80_speech_cbx_qwen25omni_sdpa.jsonl
echo SMKC_JOB_END
