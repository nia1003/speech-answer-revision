Checkpoint 草稿：CP_B15 第 1 階段全量 LLaMA-Omni2-7B（2026-11-22）。最後會併入五模型的總報告。

What ran：
- 410634–410636：scripts/job_baseline_other.sh llamaomni2 {0,1,2}。
  - 主跑會跳過音訊超過 30 秒的 5 題 C_q：GSM8K 144、640、1077、1199、1209。
- 410739：用 LONG_MODE 補跑這 5 題，跑了 chunk 和 trim 兩種版本（見 DECISION_2026-11-22）。
- 設定：sdpa、greedy、max_new_tokens 1024、無 system prompt（官方範例沒有）。
- 判分：scripts/score_baseline_v2.py。

Raw data：
- out/full_llamaomni2/：三份 shard（3,295／3,294／3,295）加 5 筆 _skipped。
- 合併檔：
  - full_llamaomni2_sdpa_main.jsonl：9,884 筆。
  - full_llamaomni2_sdpa_withchunk.jsonl：9,889 筆，等於 main 加上 chunk 版的 5 題。
- long5_llamaomni2_{chunk,trim}_sdpa.jsonl，各 5 筆。
- 判分結果：scored_full_llamaomni2_sdpa_withchunk_v2.jsonl、scored_long5_trim_v2.jsonl。
- log 沒有 Traceback、OOM 或 CUDA 錯誤。

Computed results（主結果，5 題用 chunk 版）：
| run | n | 答對 | 正確率 | 截斷 |
|---|---|---|---|---|
| A_q | 1,319 | 611 | 46.3% | 0 |
| C_q | 1,319 | 456 | 34.6% | 1 |
| A_a | 2,417 | 168 | 7.0% | 0 |
| A_bc | 2,417 | 1,236 | 51.1% | 0 |
| C_b | 2,417 | 1,158 | 47.9% | 0 |

配對 McNemar 精確檢定：
- GSM8K：文字對、語音錯 302；文字錯、語音對 147；p＝2.1e-13。
- MuSiQue：文字對、語音錯 245；文字錯、語音對 167；p＝1.4e-4。

長音訊 5 題：
- chunk 版 0/5 答對，trim 版 0/5 答對。
- 同樣 5 題，文字條件 A_q 答對 2 題（144、1199）。
- chunk 版的輸出都有回應題目內容，看起來不是亂碼。

注意：
- LLaMA-Omni2 習慣把數字寫成英文詞。MuSiQue 判分沒有把數字詞轉成數字，答案是年份或數字的題目可能被少算。總報告會評估這個影響。
