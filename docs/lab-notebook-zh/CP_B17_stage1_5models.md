Checkpoint：CP_B17 第 1 階段全量：五個模型 × 文字／語音（2026-11-22）

決定（使用者）：「五個模型跑完再跟我說」、「smoke 跑完就自己跑全量」、「維持 1.0」、「能修正就修正」，以及「都用切30秒看他會怎樣」（LLaMA-Omni2 那 5 題）。

What ran
- 題目：GSM8K test 全部 1,319 題，MuSiQue dev answerable 全部 2,417 題，共 3,736 題，五個模型都相同，沒有取子集。
- 每個模型 9,889 筆：
  - GSM8K：A_q（文字問題）、C_q（語音問題）。
  - MuSiQue：A_a（只給問題）、A_bc（段落和問題都是文字）、C_b（段落是文字，問題是語音）。
- 語音：out/tts_speech_final_view（Chatterbox；GSM8K 用 textnorm v3，205 題用 v4）。
- 共同設定：greedy、文字上限 1,024 token、不加 repetition penalty、各模型的官方 system prompt（官方範例沒有就不加）、sdpa。
- 判分：scripts/score_baseline_v2.py。規則判分，截斷判為答錯。
- 統計：配對 McNemar 精確檢定。
- 彙整：scripts/summarize_stage1.py。輸出存成 out/stage1_summary_5models.txt。
- 各模型的細節見 CP_B13（Qwen）、CP_B14（Ultravox）、CP_B15（LLaMA-Omni2）、CP_B16（Kimi）的草稿，以及本檔的 GLM 段。

Raw data（本機）
| 模型 | 判分檔 | 筆數 |
|---|---|---|
| Qwen2.5-Omni-7B | out/full/scored_full_textA_qwen25omni_sdpa_v2.jsonl + out/full_speechC/scored_full_speechC_qwen25omni_sdpa_v2.jsonl | 6,153 + 3,736 |
| Ultravox v0.4 | out/full_ultravox/scored_full_ultravox_sdpa_v2.jsonl | 9,889 |
| LLaMA-Omni2-7B | out/full_llamaomni2/scored_full_llamaomni2_sdpa_withchunk_v2.jsonl | 9,889（5 題用 chunk 版） |
| Kimi-Audio-7B-Instruct | out/full_kimiaudio/scored_full_kimiaudio_sdpa_cut_v2.jsonl | 9,889（在 <\|im_msg_end\|> 截斷） |
| GLM-4-Voice-9B | out/full_glm4voice/scored_full_glm4voice_sdpa_v2.jsonl | 9,889 |
- 原始輸出都保留，沒有修改。
- 所有 log 都沒有 Traceback、OOM 或 CUDA 錯誤。

Computed results

正確率（括號內是截斷筆數）：
| 模型 | A_q | C_q | A_a | A_bc | C_b |
|---|---|---|---|---|---|
| Qwen2.5-Omni | 79.0% (2) | 77.0% (1) | 6.3% (0) | 54.6% (0) | 56.0% (1) |
| Ultravox | 77.0% (7) | 69.1% (8) | 13.3% (231) | 70.9% (22) | 60.2% (28) |
| LLaMA-Omni2 | 46.3% (0) | 34.6% (1) | 7.0% (0) | 51.1% (0) | 47.9% (0) |
| Kimi-Audio | 74.0% (16) | 79.1% (2) | 9.3% (6) | 64.0% (20) | 59.1% (0) |
| GLM-4-Voice | 35.4% (0) | 25.9% (0) | 8.7% (1) | 38.6% (3) | 35.9% (1) |

語音 vs 文字（同題配對；差距 = 語音 − 文字，單位為百分點）：
| 模型 | GSM8K 差距 | 文字對語音錯／文字錯語音對 | p | MuSiQue 差距 | 文字對語音錯／文字錯語音對 | p |
|---|---|---|---|---|---|---|
| Qwen2.5-Omni | −2.0 | 92/66 | 0.046 | +1.4 | 158/193 | 0.069 |
| Ultravox | −8.0 | 190/85 | 2e-10 | −10.7 | 385/127 | 3e-31 |
| LLaMA-Omni2 | −11.8 | 302/147 | 2e-13 | −3.2 | 245/167 | 1e-4 |
| Kimi-Audio | +5.1 | 116/183 | 1e-4 | −4.9 | 353/234 | 1e-6 |
| GLM-4-Voice | −9.6 | 246/120 | 4e-11 | −2.7 | 297/231 | 0.005 |

依深度的差距（GSM8K：1–2／3／4／5 步以上；MuSiQue：2／3／4 hop）：
| 模型 | GSM8K | MuSiQue |
|---|---|---|
| Qwen | −3.1／−1.4／−2.1／−0.4 | +1.3／+2.0／+1.0 |
| Ultravox | −6.9／−6.3／−9.3／−11.1 | −10.7／−10.1／−11.6 |
| LLaMA-Omni2 | −10.7／−10.2／−14.5／−10.2 | −3.3／−1.6／−6.2 |
| Kimi | +4.7／+4.9／+7.6／+1.8 | −5.7／−4.6／−3.2 |
| GLM | −13.7／−11.0／−5.9／−4.9 | −1.8／−4.5／−2.2 |
- 每格的題數：GSM8K 422／364／290／225（另有 18 題沒有 <<>>，不列入）；MuSiQue 1,252／760／405。

GLM-4-Voice 段（新）
- 410638–410640：使用修正後的 baseline_others.py（只解碼文字 token、連續 78 個語音 token 就停止），見 DECISION_2026-11-22。
- 平均每筆 10.2 秒。截斷 5 筆，都是重複迴圈或表情符號迴圈。
- **輸出有一部分是中文**：A_q 1.9%、C_q 5.7%、A_a 4.4%、A_bc 18.5%、C_b 15.8%。
  - 官方 system prompt 沒有指定語言。
  - 規則判分用英文答案比對，所以中文回答幾乎都判為答錯。這些中文回答在 MuSiQue 有 781 筆判錯、47 筆判對。
  - 因此 GLM 的 MuSiQue 正確率被系統性低估。文字和語音的中文比例相近（18.5% vs 15.8%），所以對差距的影響比較小，但不是零。
  - C_q 另有 13 筆判為 undeterminable（中文數字，抽不到阿拉伯數字）。

Compared with plan
- 符合第 1 階段設計：同一 checkpoint、文字和語音、全部題目、greedy、上限 1,024，並報告截斷。
- 偏離計畫或需要寫進限制的地方：
  1. TTS 用 Chatterbox，不是計畫書寫的 Gemini TTS（CP_B8）。GSM8K 的數字改寫成英文詞（v3／v4），所以語音的差距也包含數字改寫的影響。
  2. Ultravox 沒有用官方預設的 repetition_penalty 1.1，改用 1.0，和其他模型一致。
  3. Kimi 的輸出在第一個 <|im_msg_end|> 截斷。官方程式只在 text_eos 停止。不截斷的話，A_bc 是 55.8%，截斷版是 64.0%。
  4. LLaMA-Omni2 有 5 題音訊超過 30 秒，用切 30 秒分段的方式補跑（模型沒有用這種輸入訓練過）。只取前 30 秒的版本也是 0/5。
  5. GLM 用 3,072 的總預算（約對應 1,024 個文字 token），並在文字講完後提早停止；greedy 下文字不變，smoke 驗證 200/200 相同。
  6. 判分用規則，沒有用 Mistral judge。

Anomalies／判讀（都未驗證）
- 語音的影響依模型差很多，方向也不同：GSM8K 從 −11.8 到 +5.1 個百分點。Kimi 是唯一語音比文字好的模型（GSM8K）。
- 差距沒有一致地隨深度變大：
  - Ultravox 在 GSM8K 有一點遞增的趨勢。
  - GLM 在 GSM8K 反而是淺題差距比較大。
  - 這些都只是描述，每格題數有限。
- A_a 只有 6–13%，表示 MuSiQue 的答案多半要靠段落，記憶洩漏有限。
- 規則判分有系統性偏差：
  - LLaMA-Omni2 習慣把數字寫成英文詞，MuSiQue 判分沒有轉換。
  - GLM 有一部分用中文回答。
  - 兩者的絕對正確率都被低估。比較同一模型的文字和語音，受到的影響比較小。

沒有做
- 沒有算 bootstrap 信賴區間，也沒有做多重比較校正或迴歸（步數＋長度）。
- 沒有人工抽查「文字對、語音錯」的題目。
- GLM 的中文回答沒有處理（沒有翻譯、沒有用 LLM judge，也沒有改提示重跑）。
- 沒有用 Mistral judge 複核 MuSiQue。
- 計畫書的 TTS 段落沒有更新（那是使用者的文件）。

Decision needed
1. GLM 中文回答怎麼處理：(a) 照實報告，列為限制；(b) 用 LLM judge 判分（不管語言）；(c) 加上「Answer in English」重跑，但這會偏離官方 prompt。
2. 判分要不要全面改成 LLM judge（Mistral）？這可以同時解決數字詞和中文的問題，五個模型用同一套判分。
3. 下一步：進入第 2 階段（多輪修訂），還是先補統計（信賴區間、迴歸）和人工抽查？
