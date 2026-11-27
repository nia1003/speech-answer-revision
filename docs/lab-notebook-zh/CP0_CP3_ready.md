Checkpoint: CP0 補充確認（計畫書第 37 版之後、CP3 之前）

What ran（沒有呼叫任何模型）:
- 「修正前版本」改用原始程式 parser_original.py。重跑全量 1,319 題，逐題與 parser_depth_reference.jsonl 完全相同。
  - 全量：$PROJECT_DIR/out/h1_check1/parser_depth_prefix_full.jsonl
  - 40 題：$PROJECT_DIR/out/h1_check1/parser_depth.jsonl（目前只有修正前版本；修正後版本要到 CP7）
  - 我自己重新實作的版本改名為 scripts/parser_depth_reimpl_unused.py，不再使用。
- CP3 程式已寫好，還沒有送出：scripts/mistral_depth.py、scripts/job_mistral.sh。
  - 設定與 CP0 相同：Mistral 2501 @ 9527884b、bf16、不量化、貪婪解碼、max_new_tokens 1024、seed 20261120、不給 few-shot、提示詞照計畫原文。
  - 每題會記錄 raw_output、parsed、parse_error、truncated（輸出到 1024 個 token 仍沒結束）、n_new_tokens。
  - 硬體：一張 RTXPRO6000 Blackwell 96GB，spot QoS。410299 不取消。
  - 戰艦上的 ~/rq4_v2 還不存在，送出前會先建立，不會覆蓋任何東西。

需要你決定的一個小規則（計畫沒寫清楚，有兩種合理做法）:
- Mistral 常把整段 JSON 包在 ```json … ``` 裡。程式現在的做法是剝掉一層外框再解析，
  並另外記錄 fenced 欄位。如果你要求「完全沒有外框才算合法 JSON」，之後可以用 fenced 欄位重算解析失敗數，不必重跑。

計畫書第 37 版裡仍互相矛盾的地方（只列出，不在程式裡繞過）:
1. 「運算資源」仍寫「Mistral-Small-24B 當 judge 需要量化才能放進單卡」，和 CP3 的 bf16 不量化設定矛盾。
2. 「運算資源」仍寫「Qwen3-Omni-30B-A3B 無法直接載入」，但「模型與推論設定」已改成可用 96GB 的卡。
3. 「待決定事項」仍列著已回答的項目：雙音軌定義、LLaMA 家族、checkpoint、第二輪歷史、答案來源、
   Mistral 版本、深度定義、檢查 1 的通過標準。答案在 checkpoints/C_model_inventory_draft.md 與 CP1 報告。
4. 「語音設計」仍寫雙音軌「技術含義尚未確定」；「模型與推論設定」的表仍寫 LLaMA 待確認，
   並保留「Ultravox 一次只傳一段 audio」的推測（實際已確認傳兩段）。
5. 「CP3 運算設定（待你確認）」：計畫書自己標成待確認，所以我還沒有送出。

Not done: CP3 沒有執行；CP7 的修正後版本沒做；軌道 A、B 沒動。

Decision needed: 確認 CP3 用一張 96GB Blackwell 跑 run1，並確認 JSON 外框的處理方式。
