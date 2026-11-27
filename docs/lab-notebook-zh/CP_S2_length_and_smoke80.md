Checkpoint: CP_S2 長度切點、步數 × 長度題數表、冒煙 80 題抽樣

What ran（沒有呼叫任何模型）: $PROJECT_DIR/scripts/build_step_tables.py，照計畫 2026-11-20 新版「步數與抽樣的細則」與「題目配置」。
- GSM8K 總步數＝parser_original.py 抽出的 <<>> 標記數，不排除任何標記；沒有 <<>> 的 18 題不進主分析。
- 平行步數＝總步數 − 最長串接（GSM8K 用 parser_original 的深度；MuSiQue 用 #k 參照）。
- 長度＝題目文字字元數。四分位切點用 statistics.quantiles(n=4, method="inclusive")（與 numpy 預設的線性內插相同）；GSM8K 用主分析的 1,301 題。
  分箱：Q1 ≤ 第一切點，Q2 ≤ 第二切點，Q3 ≤ 第三切點，Q4 其餘。
- 抽樣：每個資料集各用 random.Random(20261120)；分層照計畫列出的順序；每層候選依題號排序後 rng.sample。

Raw data:
- 逐題欄位：$PROJECT_DIR/out/step_axis/item_steps.jsonl（3,736 列：total_steps、longest_chain、parallel_steps、question_chars、len_q）
- 切點：$PROJECT_DIR/out/step_axis/length_quartile_cutpoints.json
  - GSM8K（1,301 題）：168 / 223 / 291（用全部 1,319 題算是 168 / 222 / 291）
  - MuSiQue（2,417 題）：72 / 94 / 127
- 題數表（原始計數）：$PROJECT_DIR/out/step_axis/gsm8k_steps_x_lenq.csv、musique_steps_x_lenq.csv

GSM8K
| 總步數 | Q1 | Q2 | Q3 | Q4 | 合計 |
|---|---|---|---|---|---|
| 1 | 21 | 20 | 14 | 10 | 65 |
| 2 | 144 | 94 | 61 | 58 | 357 |
| 3 | 100 | 105 | 92 | 67 | 364 |
| 4 | 44 | 74 | 91 | 81 | 290 |
| 5 | 17 | 23 | 48 | 50 | 138 |
| 6 | 1 | 9 | 13 | 34 | 57 |
| 7 | 0 | 3 | 4 | 14 | 21 |
| 8 | 0 | 0 | 0 | 9 | 9 |

MuSiQue
| hop | Q1 | Q2 | Q3 | Q4 | 合計 |
|---|---|---|---|---|---|
| 2 | 585 | 402 | 220 | 45 | 1,252 |
| 3 | 29 | 192 | 268 | 271 | 760 |
| 4 | 0 | 9 | 115 | 281 | 405 |

- 冒煙 80 題題號：$PROJECT_DIR/out/step_axis/smoke80_ids.jsonl（dataset、stratum、id）
  - MuSiQue 子類型抽到：2hop 14；3hop1 10、3hop2 3；4hop1 7、4hop2 3、4hop3 3
  - GSM8K 各層實際步數：≤2 層 10 題全是 2 步（沒抽到 1 步）；3、4 層各 10；≥5 層 5 步 6 題、6 步 4 題

Computed results:
- MuSiQue 4-hop 在長度 Q1 是 0 題、Q2 只有 9 題；2-hop 在 Q4 只有 45 題。分層比較（同一長度區間比較不同 hop）在 Q1、Q4 做不到。
  依計畫「有格子題數太少，就改用回歸，不用分層」，MuSiQue 主分析應改用回歸。
- GSM8K 6 步以上在 Q1 只有 1 題，7–8 步集中在 Q4。若把 ≥5 步合成一層，Q1 有 18 題。
- 冒煙 80 題按長度四分位：MuSiQue Q1–Q4 為 11／8／10／11，GSM8K 為 4／13／12／11。
- 新的 GSM8K 40 題與舊的 gsm8k_depth_smoke_40.jsonl 重疊 0 題（舊檔是按依賴深度抽的，已不再使用）。

Compared with plan: 照新版規則執行，沒有偏離。

Anomalies:
- 「格子太少」沒有數字門檻。MuSiQue 有 0 題的格子，這不需要門檻就能判斷；GSM8K 的 1 題、3 題格子算不算太少，計畫沒寫。
- 抽樣程序（rng.sample、候選依題號排序、兩個資料集各自重設種子）是我定的實作細節，計畫只寫了種子。換一種程序會抽到不同的題。

計畫仍未清理的地方（只列出）:
1. 「Human-in-the-loop 檢查點」還保留整張 CP0–CP8 表，但「檢查 1」一節已寫「不再有 CP3 到 CP8」。
2. 「參考文獻」表裡 MuSiQue、GSM8K 仍寫「需確認題數」（已確認）。
3. 「待決定事項」仍列著已回答或已不需要的項目。
4. 「語音設計」仍寫「雙音軌技術含義尚未確定」，模型表的 LLaMA 仍寫「待確認」。

Not done: 沒有產生冒煙 80 題的題目文字檔（軌道 B 證據生成時才需要）；沒有跑任何模型；MuSiQue grounded／question-only 未定。

Decision needed:
1. 確認抽樣程序與這 80 題，之後凍結。
2. 「格子太少」的門檻（例如每格少於 30 題就用回歸），或直接定 MuSiQue 用回歸、GSM8K 用分層加回歸。

Proposed next step: 確認後，軌道 B 可以開始（80 題的三種證據）；但 MuSiQue 證據要先決定 grounded 或 question-only。
