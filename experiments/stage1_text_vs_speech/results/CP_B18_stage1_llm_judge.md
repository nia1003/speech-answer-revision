Checkpoint：CP_B18 第 1 階段改用 LLM judge 重新判分：五個模型（2026-11-23）

決定（使用者）：「Yes, use LLM judge」，五個模型改用同一個 judge 判分。設定和 smoke 過程見 DECISION_2026-11-22_llm_judge_stage1.md。

What ran
- Judge：Mistral-Small-24B-Instruct-2501 @ 9527884b。
  - 設定：bf16、greedy、max_new_tokens 96、zero-shot，prompt v2（scripts/judge_correct_v2.py）。
- 輸入：五個模型 × 9,889 筆，共 49,445 筆（out/judge_stage1/judge_input_full.jsonl）。
  - 每筆給 judge 題目、標準答案（MuSiQue 加 aliases）和模型的回答，不給規則判分的結果。
- 工作：
  - 410851（shard 0，3×3090）：24,723 筆，2.9 小時。
  - 411114（shard 1，3×3090）：24,722 筆，2.9 小時。
  - 原本送到 Blackwell spot 的 410852 一直沒排到，已取消。
- 套用結果：scripts/apply_judge.py 產生新的判分檔，verdict 改成 judge 的結果，舊的規則判分保留在 rule_verdict。
- 彙整：summarize_stage1.py，程式沒有修改。

Raw data（本機）
- out/judge_stage1/judge_full_v2.jsonl：judge 原始輸出，49,445 筆，key 都不重複。
- out/judge_stage1/judged_{qwen25omni,ultravox,llamaomni2,kimiaudio,glm4voice}.jsonl：每個檔 9,889 筆。
- out/stage1_summary_5models_judge.txt：彙整結果。
- out/judge_stage1/agreement_full_v2.txt：規則判分和 judge 的一致性。不一致的筆數列在 full_v2_disagree.jsonl。
- judge 輸出無法解析：3 筆，記為 judge_fail，算答錯。
  - 原因是 judge 在 final_answer 裡不停重複，寫到 96 token 的上限。
  - 這 3 筆是 ultravox A_bc、ultravox A_a、kimi A_q 各 1 筆。
- 規則判分的檔案都沒有修改。
- log 沒有 Traceback 或 OOM。

Computed results

正確率（judge；括號內是規則判分的結果）：
| 模型 | A_q | C_q | A_a | A_bc | C_b |
|---|---|---|---|---|---|
| Qwen2.5-Omni | 86.2 (79.0) | 83.9 (77.0) | 6.2 (6.3) | 58.4 (54.6) | 59.9 (56.0) |
| Ultravox | 85.7 (77.0) | 76.0 (69.1) | 13.7 (13.3) | 65.5 (70.9) | 58.2 (60.2) |
| LLaMA-Omni2 | 54.1 (46.3) | 38.4 (34.6) | 7.9 (7.0) | 58.5 (51.1) | 55.6 (47.9) |
| Kimi-Audio | 79.8 (74.0) | 81.7 (79.1) | 8.7 (9.3) | 62.2 (64.0) | 62.7 (59.1) |
| GLM-4-Voice | 37.8 (35.4) | 27.4 (25.9) | 8.9 (8.7) | 43.9 (38.6) | 42.3 (35.9) |

語音 vs 文字（同題配對；差距 = 語音 − 文字，單位為百分點）：
| 模型 | GSM8K judge | p | 規則 | MuSiQue judge | p | 規則 |
|---|---|---|---|---|---|---|
| Qwen2.5-Omni | −2.3 | 0.014 | −2.0 | +1.4 | 0.097 | +1.4 |
| Ultravox | −9.7 | 3e-16 | −8.0 | −7.4 | 3e-13 | −10.7 |
| LLaMA-Omni2 | −15.7 | 1e-22 | −11.8 | −2.9 | 0.002 | −3.2 |
| Kimi-Audio | +2.0 | 0.11 | +5.1 (p 1e-4) | +0.5 | 0.65 | −4.9 (p 1e-6) |
| GLM-4-Voice | −10.3 | 1e-12 | −9.6 | −1.6 | 0.14 | −2.7 (p 0.005) |

依深度的差距（judge）：
| 模型 | GSM8K 1–2／3／4／5+ | MuSiQue 2／3／4 hop |
|---|---|---|
| Qwen | −2.6／−1.1／−3.4／−1.8 | +1.9／+1.2／+0.5 |
| Ultravox | −9.2／−7.4／−10.3／−13.8 | −8.3／−7.4／−4.4 |
| LLaMA-Omni2 | −16.4／−12.6／−20.7／−10.2 | −3.4／−1.6／−4.0 |
| Kimi | −0.2／+3.3／+4.8／+0.4 | −0.2／+0.9／+2.0 |
| GLM | −13.7／−11.8／−5.9／−7.6 | −2.0／−0.4／−2.5 |
- 每格題數和 CP_B17 相同。

規則判分和 judge 的一致性：
- 整體：43,979/49,442 一致（89.0%）。
- 規則判對、judge 判錯：2,019 筆。
- 規則判錯、judge 判對：3,444 筆。
- GSM8K：
  - 規則判錯、judge 判對有 746 筆。其中 484 筆的回答裡可以找到標準答案的數字，剩下的多半是數字寫成英文詞或中文。原因是規則只取最後一個數字，例如「$6 if you buy 2 tubs and 4 packets」會取到 4。
  - 規則判對、judge 判錯只有 40 筆。
- MuSiQue：兩個方向都有不一致，方向會隨模型和模態而不同，見下方 Anomalies。

Compared with plan
- 符合計畫：用計畫指定的 judge（Mistral-Small-24B），五個模型用同一套判分，並且並列報告規則判分。
- 還沒符合計畫：
  - 檢查 3 要求每個資料集各 50 筆的人工對照，而且要雙人盲標。抽樣檔已經準備好，還沒有標。
  - 在人工對照完成之前，不能宣稱 judge 夠準確，judge 的誤差率目前未知。
- GSM8K 的部分偏離計畫：計畫的優先方法是數值抽取加 deterministic 判分。這次 GSM8K 也改用 judge，是依照使用者要五個模型全面改判的決定。規則判分的結果並列保留。

Anomalies／判讀（都未經人工驗證）
- **結論會隨判分方式改變。** 和 CP_B17 相比，有三處不一樣：
  1. Kimi 的 GSM8K 從「語音比文字好 +5.1，顯著」變成 +2.0，不顯著（p 0.11）。
  2. Kimi 的 MuSiQue 從 −4.9（顯著）變成 +0.5（p 0.65）。
  3. GLM 的 MuSiQue 從 −2.7（p 0.005）變成 −1.6（p 0.14）。
- 原因：規則判分會被回答的長度影響，而回答長度又會隨模態改變。
  - Kimi 在 MuSiQue 的回答長度中位數：文字條件 36 個字，語音條件只有 3 個字。
  - 長回答常常把段落裡的許多實體都列出來，標準答案剛好出現在其中，就被規則判對。例如答案是 1810 的回答，因為也提到 1839 而被判對。
  - 短回答只要和標準答案的寫法稍有不同，就被規則判錯。例如「William McKinley」對上標準答案「President McKinley」。
  - 回答長度中位數（A_bc／C_b）：Qwen 50/50、Ultravox 34/37、LLaMA-Omni2 17/18、Kimi 36/3、GLM 46/48。只有 Kimi 的落差很大。
- Ultravox 的 MuSiQue 差距從 −10.7 縮小到 −7.4。它在 A_bc 有 266 筆規則判對、judge 判錯，比其他模型都多。
- 兩種判分方式都一致的結論：
  - Ultravox、LLaMA-Omni2、GLM 在 GSM8K 的語音條件明顯比文字差。
  - Ultravox 在 MuSiQue 的語音條件也明顯比文字差。
  - Qwen 只差一點。
- Judge 已知的錯誤類型（從 smoke 看到的）：
  - 標準答案粒度的爭議，兩個方向都有。太寬鬆的例子：Latin 對 Medieval Latin。太嚴格的例子：12 March 1952 對 1952。
  - 從抽查看到的其他太嚴格的例子：「2001 Nissan Altima」對 Nissan Altima、「22 times」被判為沒有答案。
  - 這些錯誤的比率要等人工對照才知道。
- 截斷的筆數和 CP_B17 相同。
- A_a 在兩種判分下都只有 6–14%。

沒有做
- 人工驗證集還沒有標。
  - 已準備 out/judge_stage1/human_val_100_blind.csv：GSM8K 50 筆、MuSiQue 50 筆。
  - 分層方式：資料集 × 模型 × run（A_q／C_q 或 A_bc／C_b），每格 5 筆，seed 20261123。
  - 檔案裡不顯示判分結果。答案對照在 human_val_100_key.jsonl，標註時不要打開。
  - 這 100 筆裡有 15 筆是規則判分和 judge 不一致的。
- 沒有算 bootstrap 信賴區間，也沒有做迴歸或多重比較校正。
- 沒有計算各模型、各模態的 judge 誤差率。這要等人工標註。

Decision needed
1. 人工驗證：計畫要求雙人盲標。要由你和另一位標註者標這 100 筆嗎？還是先由你一個人標？
2. 主分析要用哪一種判分當主結果：judge（另外並列規則判分），還是等人工驗證完再決定？
3. 下一步：補統計（信賴區間、迴歸），還是進入第 2 階段？
