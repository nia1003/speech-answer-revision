Checkpoint 草稿：CP_B14 第 1 階段全量 Ultravox v0.4（2026-11-21）。最後會併入五模型的總報告。

What ran：
- 410624–410626：scripts/job_full_ultravox.sh，跑 baseline_ultravox.py。
- 設定：sdpa、greedy、max_new_tokens 1024、repetition_penalty 1.0（見 DECISION_2026-11-21_ultravox_rep_penalty）、model card 的 system prompt。
- 判分：scripts/score_baseline_v2.py，和 Qwen 相同。

Raw data：
- out/full_ultravox/：full_ultravox_sdpa_shard{0,1,2}.jsonl（3,298／3,295／3,296），合併檔共 9,889 筆。
- out/full_ultravox/scored_full_ultravox_sdpa_v2.jsonl。
- 三份 log 都沒有 Traceback、OOM 或 CUDA 錯誤。

Computed results：
| run | n | 答對 | 正確率 | 截斷 |
|---|---|---|---|---|
| A_q | 1,319 | 1,016 | 77.0% | 7 |
| C_q | 1,319 | 911 | 69.1% | 8 |
| A_a | 2,417 | 322 | 13.3% | 231 |
| A_bc | 2,417 | 1,713 | 70.9% | 22 |
| C_b | 2,417 | 1,455 | 60.2% | 28 |

配對 McNemar 精確檢定：
- GSM8K（A_q vs C_q）：文字對、語音錯 190；文字錯、語音對 85；p＝2.2e-10。
- MuSiQue（A_bc vs C_b）：文字對、語音錯 385；文字錯、語音對 127；p＝3.3e-31。

判讀（未驗證）：
- Ultravox 的語音降幅比 Qwen 大很多：GSM8K −7.9 個百分點，MuSiQue −10.7 個百分點。Qwen 分別是 −2.0 和 +1.4。

沒有做：
- 依步數／長度的細分。
- 文字對、語音錯的人工抽查。
- bootstrap 信賴區間。
