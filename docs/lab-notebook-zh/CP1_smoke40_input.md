Checkpoint: CP1 產生 gsm8k_depth_smoke_40.jsonl（同時附 CP0 確認清單）

What ran:
- 下載 GSM8K test.jsonl：https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl
  → $PROJECT_DIR/data/raw/gsm8k_test.jsonl，1,319 行，sha256 3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14
- $PROJECT_DIR/scripts/make_smoke40.py：照計畫的固定題號（淺 14／中 13／深 13）取題，idx＝0 起算行號；
  solution＝answer 在 #### 之前的部分，去頭尾空白。
- 輸出 $PROJECT_DIR/data/gsm8k_depth_smoke_40.jsonl

Key numbers:
- 列數 40；idx 與計畫清單完全相同、無重複（程式內 assert）。
- 每列只有 idx、question、solution 三個欄位；沒有程式深度、Claude 深度或任何標籤。
- 前 3 行範例：
  - 800：Pierson 278 分… solution 第一行就是 "Pierson = <<278=278>>278 points"（計畫已記錄：程式會把它算成一步）
  - 1061：Betsy／Donovan 代數題，多數步驟沒有 <<>>，還有 "<<+18=18>>" 這種怪標記
  - 990：冷氣溫度題（題目較長，截斷顯示）

Compared with plan: 相符。

Anomalies:
- 1061 的 "<<+18=18>>" 是以正負號開頭的算式；目前的數字 regex 會把它當成一步。這是程式規則的問題，留到 CP2／CP7，不在這一步改。

Not done:
- 沒有呼叫任何模型、沒有跑程式深度（CP2）、沒有跑 Mistral。
- MuSiQue 還沒下載（軌道 B 與 H1 的 MuSiQue 部分才需要）。

Decision needed（CP0，第一次呼叫模型前必須由你確認，確認後凍結）:
1. Mistral repo id 與 revision：mistralai/Mistral-Small-24B-Instruct-2501 @ 9527884be6e5616bdd54de542f9ae13384489724
   （戰艦快取裡的版本，也是 A 實驗判官用的那一個）。bf16，不量化。
2. 深度定義：一行＝一步；最後的比較算一步（505 會是深度 3）。
3. 通過標準：完全一致率 ≥ 0.8；差距 ≤ 1 層 ≥ 0.95；兩次執行深度改變 ≤ 2 題；解析失敗 0 題。
4. 解碼：貪婪（do_sample=False），max_new_tokens＝1024（40 題的 JSON 含逐步列表，256 會截斷），seed 20261120，
   不給 few-shot，提示詞用計畫原文。
5. 輸出目錄：$PROJECT_DIR/out/h1_check1/（本機）；實際在戰艦 ~/rq4_v2/ 跑，跑完拉回。
6. 跑的位置：戰艦 GPU（Mistral 24B bf16 需要約 48GB）。目前 2×48GB 正被 A 實驗判官的排隊工作佔著順位，
   舊 A 實驗的判官工作 410299 還在排隊（spot，2×RTX6000Ada，原因 Priority）；它與 CP3 的 Mistral 會搶同一種卡。

Proposed next step: 你確認 CP1 輸入正確與 CP0 五項後，我跑 CP2（程式深度修正前版本，不需要 GPU），
重現計畫記載的全量分佈與 40 題的程式欄，停在 CP2 報告。
