決定紀錄：Kimi-Audio 輸出在第一個 <|im_msg_end|> 截斷後判分（2026-11-21，Claude 依「五模型設定一致」原則決定，待使用者複核）

- 現象（smoke 80，out/smoke_others/scored_kimiaudio.jsonl）：
  - kimia_infer 的 text 模式只在 kimia_text_eos 停止（官方 generate 也一樣，kimia.py 第 136 行）。
  - 模型答完後常輸出 <|im_msg_end|>（訊息結束 token，出現在文字流裡），接著繼續自問自答，直到 1024 上限。
  - 含 <|im_msg_end|> 的輸出：A_bc 21/40、A_a 1/40，A_q／C_q／C_b 都是 0/40。
  - 截斷 7 筆（A_bc 6、A_a 1），全部屬於這種情況。
- 決定：
  - 判分前，在第一個 <|im_msg_end|> 截斷 raw_output。
  - truncated 重新計算為「沒有 <|im_msg_end|> 且達到 1024 token」。
  - 理由：其他模型都在各自的回合結束 token 停止（例如 Ultravox 的 <|eot_id|>），這樣處理對等。
- 為什麼不重跑：greedy 解碼下，<|im_msg_end|> 之前的 token 和「在那裡停止」完全相同，截斷就等同於提早停止。
- 原始輸出不修改。截斷後的結果另存新檔，判分時產生。
- 影響：
  - 不截斷的話，後面亂接的文字可能剛好含正確答案，造成誤判答對。
  - 這是 Kimi 的文字輸入條件（A_bc、A_a）特有的問題，限制裡要寫明。
