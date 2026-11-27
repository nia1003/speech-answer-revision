Checkpoint 草稿：CP_B16 第 1 階段全量 Kimi-Audio-7B-Instruct（2026-11-22）。最後會併入五模型的總報告。

What ran：
- 410732–410734：scripts/job_baseline_other.sh kimiaudio {0,1,2}。
- 設定：kimi_generate 包裝（只多一行，處理沒有音訊的情況）、text_temperature 0、max_new_tokens 1024、無 system prompt。
- C_b 的輸入是兩則 user 訊息：先段落文字，再語音問題。
- 後處理：scripts/kimi_cut_msgend.py，在第一個 <|im_msg_end|> 截斷（見 DECISION_2026-11-21_kimi_msg_end_cut）。
- 判分：scripts/score_baseline_v2.py。依既定規則，截斷判為答錯。

Raw data：
- out/full_kimiaudio/：shard 0–2 共 9,889 筆，沒有 skipped。
  - full_kimiaudio_sdpa.jsonl：原始合併檔，未修改。
  - full_kimiaudio_sdpa_cut.jsonl：截斷後的版本，保留 raw_output_uncut 欄位。
- 判分結果：scored_full_kimiaudio_sdpa_cut_v2.jsonl（主結果）、scored_full_kimiaudio_sdpa_uncut_v2.jsonl（參考）。
- log 沒有錯誤。

Computed results（主結果：截斷版）：
| run | n | 答對 | 正確率 | 截斷 | 未截斷版的答對 | 未截斷版的截斷 |
|---|---|---|---|---|---|---|
| A_q | 1,319 | 976 | 74.0% | 16 | 974 | 23 |
| C_q | 1,319 | 1,043 | 79.1% | 2 | 1,043 | 2 |
| A_a | 2,417 | 224 | 9.3% | 6 | 224 | 42 |
| A_bc | 2,417 | 1,548 | 64.0% | 20 | 1,349 | 488 |
| C_b | 2,417 | 1,429 | 59.1% | 0 | 1,429 | 0 |

配對 McNemar 精確檢定（截斷版）：
- GSM8K：文字對、語音錯 116；文字錯、語音對 183；p＝1.3e-4。語音反而比較高。
- MuSiQue：文字對、語音錯 353；文字錯、語音對 234；p＝1.0e-6。

判讀（未驗證）：
- 截斷規則對 A_bc 的影響很大。不截斷時有 488 筆跑到 1,024 上限，判為答錯，正確率會低 8 個百分點。
- Kimi 在 GSM8K 語音比文字高 5.1 個百分點。可能是文字輸入不是它的主要訓練情境，例如文字輸入常接著自問自答。
