#!/bin/bash
#SBATCH -J tts_v4
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 2:00:00
# v4 patch: resynthesize GSM8K 205 (tts_textnorm_v4), Whisper check, then build the final speech view:
# question/ = GSM8K v3 wavs (205 from v4) + MuSiQue wavs from out/tts_full (CP_B11).
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
V=out/tts_speech_final_view
for p in out/tts_full_v4 $V; do if [ -e $p ]; then echo "$p EXISTS, abort"; exit 1; fi; done
env_cbx/bin/python -u scripts/tts_full_v4_cbx.py $HOME/rq4_v2 0 1 205 || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_v4_cbx.py $HOME/rq4_v2 0 || exit 1
mkdir -p $V/question
for f in $HOME/rq4_v2/out/tts_full_v3/question/gsm8k_*.wav; do [ "$(basename $f)" = gsm8k_205.wav ] || ln -s $f $V/question/; done
ln -s $HOME/rq4_v2/out/tts_full_v4/question/gsm8k_205.wav $V/question/
for f in $HOME/rq4_v2/out/tts_full/question/musique_*.wav; do ln -s $f $V/question/; done
python3 -c "
import json,glob
with open('$V/manifest.jsonl','w') as f:
  for p in sorted(glob.glob('out/tts_full_v3/manifest_shard*.jsonl'))+sorted(glob.glob('out/tts_full/manifest_shard*.jsonl'))+['out/tts_full_v4/manifest_shard0.jsonl']:
    for l in open(p):
      m=json.loads(l)
      if 'tts_full/' in p and m['dataset']=='gsm8k': continue
      if 'tts_full_v3' in p and str(m['id'])=='205': continue
      m['kind']='question'; m['source']=p; f.write(json.dumps(m)+'\n')"
echo "wavs: $(ls $V/question | wc -l), manifest: $(wc -l < $V/manifest.jsonl)"
echo TTSV4_JOB_END
