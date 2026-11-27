決定紀錄：第 1 階段改用 LLM judge 判分（2026-11-22）

- 決定（使用者）：「Yes, use LLM judge」，五個模型都用同一個 judge 重新判分。
- Judge：mistralai/Mistral-Small-24B-Instruct-2501 @ 9527884be6e5616bdd54de542f9ae13384489724
  - 和 CP3 是同一個 revision。
  - 設定：bf16、greedy、max_new_tokens 96、seed 20261120、zero-shot，每筆輸出呼叫一次。
- 環境：沿用 ~/rq4_Ajudge/env（唯讀）。GPU 是 3×3090（device_map=auto），或 Blackwell 單卡。
- 輸入：只給 judge 題目、標準答案（MuSiQue 加 aliases）和模型的回答，不給規則判分的結果。
  - 輸入檔：out/judge_stage1/judge_input_full.jsonl，共 49,445 筆，截斷 350 筆，和 CP_B17 一致。
- 判分規則：
  - 回答用任何語言都可以，數字寫成英文詞也可以。
  - 沒有最終答案、在幾個候選答案之間猶豫，或還沒給出答案就被截斷，都判為答錯。
- Smoke：200 筆，每個模型 × 每種 run 各隨機抽 8 筆，seed 20261122。
  - v1（scripts/judge_correct.py）：解析失敗 0 筆，和規則判分一致 171/200。
    - 人工看了 29 筆不一致：約 19 筆是規則判錯，judge 判對。
    - judge 的錯誤：把標準答案填進 final_answer（John Cena 題）、把含標準答案的清單判錯、對過寬的答案太寬鬆。
  - v2（scripts/judge_correct_v2.py）：只加三條通用規則。
    1. 最終答案只能取自回答本身。
    2. 包含標準答案的清單不算猶豫。
    3. 比標準答案更精確、但包含標準答案的答案算對；比標準答案更寬，或只講到一部分，算錯。
  - v2 結果：和規則判分一致 177/200。上面四種錯誤消失；剩下的是標準答案粒度的爭議，兩個方向都有：
    - 太寬鬆：Latin vs Medieval Latin。
    - 太嚴格：12 March 1952 vs 1952、48°F vs upper 40s–lower 50s。
  - 不再為了這 200 筆繼續調整 prompt，避免對樣本過擬合。剩下的誤差交給人工驗證集估計。
- 全量：v2，410851（shard 0/2，3×3090）、410852（shard 1/2，Blackwell spot）。
  - 輸出：out/judge_stage1/judge_full_v2_s{0,1}.jsonl。
- 限制：
  - bf16 批次推論在極少數情況下可能和 batch size 1 的結果差一個 token。
  - 計畫書檢查 3 要求的人工對照（每個資料集 50 筆，雙人盲標）還沒做。
  - 規則判分的結果全部保留，兩種判分會並列報告。
- 2026-11-23 更新：
  - 原本送到 Blackwell spot 的 410852 一直沒排到，已取消，shard 1 改由 411114 在 3×3090 上執行。
  - 兩個 shard 都完成，共 49,445 筆，其中 3 筆 judge 輸出無法解析。
  - 結果見 CP_B18。
