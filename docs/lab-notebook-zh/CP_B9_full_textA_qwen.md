Checkpoint: CP_B9 Qwen2.5-Omni-7B 全量文字條件 A（sdpa）（2026-11-21）

What ran:
- 410510（2×3090，s05）：scripts/baseline_qwen_v3.py。
- 設定：attn_implementation="sdpa"、greedy、max_new_tokens 1024、官方 system prompt、v2 空行分隔。
- 輸入：全量 3,736 題。
  - GSM8K 1,319 題：A_q。
  - MuSiQue 2,417 題：A_a（只給問題）與 A_bc（附段落），兩種都跑。
  - 共 6,153 次，全部完成（BASELINE_DONE），log 裡沒有錯誤。
- 判分：scripts/score_baseline_v2.py（規則判分；GSM8K 的輸出沒有阿拉伯數字時，才把英文數字詞轉成數字）。

Raw data:
- $PROJECT_DIR/out/full/full_textA_qwen25omni_sdpa.jsonl（6,153 筆）、full_textA_qwen.log
- $PROJECT_DIR/out/full/scored_full_textA_qwen25omni_sdpa_v2.jsonl（6,153 筆，有判定、步驟數、長度四分位）
- 截斷 2 筆：
  - GSM8K 1183：一直重複數蘋果。
  - GSM8K 1239：算完後接著又開始「It seems there…」。
- 無法判定 1 筆：GSM8K 463，模型反問 Ashley 訂了多少。
- 與 smoke 的一致性：smoke 的 120 筆在全量中的輸出和 sdpa smoke 逐字相同（120/120）。

Computed results:
| run | 題數 | 答對 | 正確率 | 截斷 | "other other"／"Human:" | 平均生成 token | 平均秒數 |
|---|---|---|---|---|---|---|---|
| GSM8K A_q | 1,319 | 1,042 | 79.0% | 2 | 0／0 | 162 | 6.4 |
| GSM8K A_q 主分析（排除 18 題沒有 <<>>） | 1,301 | 1,029 | 79.1% | — | — | — | — |
| MuSiQue A_a（只給問題） | 2,417 | 153 | 6.3% | 0 | 0／0 | 76 | 3.0 |
| MuSiQue A_bc（附段落） | 2,417 | 1,319 | 54.6% | 0 | 0／0 | 70 | 2.8 |

依步驟數（主分析題目）:
- GSM8K（<<>> 數）：

  | 步驟數 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|
  | 答對 | 57/65 | 308/357 | 288/364 | 216/290 | 103/138 | 37/57 | 14/21 | 6/9 |
  | 正確率 | 87.7% | 86.3% | 79.1% | 74.5% | 74.6% | 64.9% | 66.7% | 66.7% |

- MuSiQue A_bc（hop 數）：2-hop 752/1,252＝60.1%；3-hop 398/760＝52.4%；4-hop 169/405＝41.7%。
- MuSiQue A_a：2-hop 7.8%；3-hop 5.7%；4-hop 3.0%。

依題目長度四分位（Q1 → Q4）:
- GSM8K：84.1%、82.6%、78.3%、71.2%。
- MuSiQue A_bc：59.8%、59.2%、51.4%、47.7%。
- 步驟數和長度彼此相關，上面兩張表都只是描述統計。要分開兩者的影響，得用計畫中的迴歸。

Anomalies:
1. MuSiQue 只給問題時正確率 6.3%，和 smoke 的 0/40 一致：模型多半拒答，或要求補充資訊。
2. 規則判分的限制還在：同一段輸出有阿拉伯數字、答案卻用英文數字寫時，會判錯。MuSiQue 的別名比對可能低估答對數。兩者都還沒有人工抽查。

沒有做:
- 沒有跑語音條件，因為還在等 TTS 的決定（見 CP_B8）。
- 沒有跑其他 4 個模型。
- 沒有跑迴歸。
- 沒有人工抽查判分。

Decision needed:
1. MuSiQue 的正式設定（只給問題 6.3%、附段落 54.6%）。
2. 判分要不要先人工抽查一批，例如每個 run 50 筆，再跑其他模型。
