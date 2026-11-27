#!/bin/bash
# Formal run (GO_CRITERIA v2), text part that needs no Mistral: smoke (shard 0/400) -> checks -> full text shards 0-2/3 -> wait.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_full_qwen
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
r=$(waitlog s2f_r23_smoke.log); [ "$r" = "1" ] || { echo "SMOKE FAILED"; exit 1; }
scp -q ${R}:rq4_v2/$D/round23_qwen_smoke_shard0.jsonl $D/ || exit 1
python3 - <<'PY' || { echo "SMOKE CHECK FAILED"; exit 1; }
import json, sys
R=[json.loads(l) for l in open("out/stage2_full_qwen/round23_qwen_smoke_shard0.jsonl")]
n=len(R); bad=[r for r in R if r.get("r3_error") or not r.get("r3") or r["r3"].get("raw_output") is None]
tr=sum(r["truncated"] for r in R); tr3=sum(r["r3"]["truncated"] for r in R if r.get("r3"))
from collections import Counter; print("rows", n, Counter((r["dataset"], r["evidence_type"]) for r in R), "r3 bad", len(bad), "r2 trunc", tr, "r3 trunc", tr3)
for r in R[:6]: print(r["dataset"], r["evidence_type"], "|", r["user2_text"][:60], "|| r3:", r["r3"]["raw_output"][:60])
sys.exit(1 if n < 10 or bad or tr > 0.05 * n else 0)
PY
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/s2f_r23_text\$i.log ] && exit 1; sbatch -o logs/s2f_r23_text\$i.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_pass1.jsonl \$i 3 text text; done" || { echo "FULL SUBMIT FAILED"; exit 1; }
echo "FULL_TEXT_SUBMITTED $(date)"
for i in 0 1 2; do r=$(waitlog s2f_r23_text$i.log); [ "$r" = "1" ] || { echo "FULL TEXT $i FAILED"; exit 1; }; done
ssh $R "cd ~/rq4_v2; wc -l $D/round23_qwen_text_shard?.jsonl; grep -c 'ERROR' logs/s2f_r23_text?.log"
echo "FULL_TEXT_DONE $(date)"
