Checkpoint: H1 檢查 1（MuSiQue 部分）hop 數與 question decomposition 是否一致

What ran（沒有呼叫任何模型）:
- 照官方 download_data.sh 的 Google Drive 連結下載 musique_v1.0.zip
  （sha256 98f839bf2fd5319f5c688aed77901a6d5c30b3b9f9f691ab9a8ecafb045ee0cd），解壓到 $PROJECT_DIR/data/raw/musique/data/。
- 對 musique_ans_v1.0_dev.jsonl 全部題目做檢查：
  - id 前綴的 hop 數與 question_decomposition 的步數是否相同；
  - supporting 段落數是否等於 hop 數；
  - 子問題裡的 #k 參照是否只指向前面的步驟；
  - 依 #k 參照算出的最長依賴鏈長度（與 GSM8K 的「依賴深度」同一個定義）。

Key numbers:
- MuSiQue-Ans dev＝2,417 題，全部 answerable。計畫裡「待核實」的 2,417 已確認。
- hop 數與分解步數不一致：0 題；supporting 段落數與 hop 數不一致：0 題；#k 參照異常：0 題。

| 類型 | 題數 | 步數（hop） | 最長依賴鏈 |
|---|---|---|---|
| 2hop | 1,252 | 2 | 2 |
| 3hop1 | 568 | 3 | 3 |
| 3hop2 | 192 | 3 | 2 |
| 4hop1 | 246 | 4 | 4 |
| 4hop2 | 64 | 4 | 3 |
| 4hop3 | 95 | 4 | 3 |

Compared with plan: 「hop 數與 decomposition 一致」這一點完全相符。
但計畫把 MuSiQue 的 2／3／4-hop 當成「依賴深度」，這一點不成立。

Anomalies（必停：計畫本身的矛盾）:
- 351 題（3hop2、4hop2、4hop3，佔 14.5%）的 hop 數大於最長依賴鏈。它們有兩個平行的分支再合併，
  正是計畫在 GSM8K 那邊說的「步數多不等於依賴長」。
- 如果照計畫用 hop 數當 H1 的深度軸，3-hop 這一層有 25% 的題目實際依賴深度是 2，
  4-hop 這一層有 39% 的題目實際依賴深度是 3。深度軸會混入「平行步驟多」與「串行鏈長」兩種東西。
- 依賴鏈長度可以直接從資料集的 #k 參照算出來，不需要模型或人工。

Not done:
- 沒有抽 MuSiQue 的 40 題：計畫沒有寫 MuSiQue 的抽樣規則（種子、分層要用 hop 數還是依賴鏈、子類型怎麼配），
  有兩種以上合理做法，所以不猜。
- 沒有決定 grounded 或 question-only（計畫「待決定事項」）。
- 沒有下載其他資料或跑任何模型。

Decision needed:
1. MuSiQue 的 H1 深度軸用哪一個？
   a. 最長依賴鏈（2／3／4），與 GSM8K 的依賴深度定義一致；hop 數改當 A1 的對照定義。
   b. 維持 hop 數，依賴鏈只當 A1 的對照。
   c. 只用 2hop、3hop1、4hop1（hop 數＝依賴鏈的 2,066 題），平行結構的 351 題排除或另外報告。
2. MuSiQue 40 題的抽樣規則（種子、每層題數、子類型是否要配額）。

Proposed next step: 你決定 1、2 後，我照規則抽 MuSiQue 40 題並停在對應 CP1 的檢查點。
