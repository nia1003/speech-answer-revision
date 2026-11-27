Checkpoint: CP_X1 查證 GSM-Symbolic 與 MuSiQue 拆解，能否做「同一題、只差步數」（2026-11-21，只讀、不改計畫）

What ran:
- 從 HF 下載 apple/GSM-Symbolic 的 main、p1、p2 三個 parquet（只放在 scratchpad，沒有放進專案）。
- 讀本機的 MuSiQue dev（data/raw/musique/data/musique_ans_v1.0_dev.jsonl）裡的 question_decomposition 欄位。

## GSM-Symbolic（apple/GSM-Symbolic，論文 arXiv 2410.05229）

Raw data:
| 版本 | 題數 | 模板數 | 每個模板的實例數 | 解答平均行數 |
|---|---|---|---|---|
| main（原題模板化） | 5,000 | 100 | 50 | 3.59 |
| P1（多一個條件） | 5,000 | 100（與 main 相同） | 50 | 4.61 |
| P2（多兩個條件） | 2,500 | 50（main 與 P1 都有） | 50 | 5.50 |

- 100 個模板都來自 GSM8K test：original_question 與我們的 gsm8k_test[original_id] 逐字相同，100/100。所以這 100 題都在我們已經跑過的 1,319 題裡。
- 授權：CC BY-NC-ND 4.0（非商業、禁止改作）。研究內部合成語音應該可以，但合成的音訊不能公開散布。若要發表音訊資料，要另外確認。
- 解答裡沒有 <<>> 標記，所以步驟數要改用解答行數，或人工標註。
- 例子（original_id 11，instance 0）：
  - main：Ava 買 1 打 danish（$17／打）、8 打 tart（$74）、3 打 scone（$113），總共多少？答案 948（4 行解答）。
  - P1：Nadia 買 2 打 croissant（$14）、8 打 macaron（$82）、8 打 brownie（$112），**打九折**後總共多少？答案 1422（5 行解答）。
  - P2：Nadia 買 60 個 donut（$14／打）、60 個 mini cupcake（$25／打）、24 個 mini cheesecake，**打八折後付了 $1540，問 cheesecake 每打多少錢**。答案 865（6 行解答，而且題目結構變了：已知總價、反推單價）。

Computed results／判讀:
- 同一個模板確實有三個長度版本，main → P1 → P2 的解答行數是 3.6 → 4.6 → 5.5。
- **但不是「同一題只差步數」**：
  1. 同一個 instance 編號在三個版本裡的人名、物品、數字都不一樣（各自重新抽樣）。
  2. P2 會改變題目結構，例如從順著算改成反推，不只是多一步。
- 可以做到的是「同一個模板、不同步數」：在模板層級比較，人名和數字的差異靠 50 個實例平均掉。
- 規模：P2 只有 50 個模板，所以三個版本都有的比較單位是 50 個模板（每個 50 個實例）。

## MuSiQue 拆解（question_decomposition）

Raw data:
- 每題都附有單步小題：小題文字、小題答案，以及對應的支持段落位置。後面的小題用「#1」「#2」引用前面的答案。
  - 例：3hop1「Stan 配音者的出生地」拆成三個小題：
    1. The Hobbit >> part of the series → South Park
    2. who does the voice of stan on #1 → Trey Parker
    3. #2 >> place of birth → Denver
- 推理鏈的類型（2,417 題）：
  - 2hop：1,252 題
  - 3hop1：568 題
  - 3hop2：192 題
  - 4hop1：246 題
  - 4hop2：64 題
  - 4hop3：95 題
- **直線鏈**（每一步只接上一步的答案）：2hop、3hop1、4hop1 全部是，共 2,066 題。
- **非直線**：3hop2、4hop2、4hop3 全部不是，共 351 題。例如 4hop3 的第 3 步是獨立的，第 4 步同時用到 #2 和 #3。
- 6,404 個小題中，有 2,304 個（36%）是知識庫寫法（「X >> relation」），不是完整的自然問句。

Computed results／判讀:
- **直線鏈可以截短**：一題 4hop1 的前 2 步、前 3 步，本身就是一條 2 hop、3 hop 的鏈，而且每一步都有標準答案（小題答案）。這樣就能做到「同一條推理鏈、只差步數」，比 GSM-Symbolic 更乾淨：人名、內容都相同。
- 可用的題數：
  - 4hop1 的 246 題，可以造出 2、3、4 hop 三個版本。
  - 3hop1 的 568 題，可以造出 2、3 hop 兩個版本。
- 要做的工作：
  1. 把截短後的小題串回一個通順的完整問句。36% 是知識庫寫法，需要模型改寫再抽查，例如用 Qwen2.5-7B-Instruct 改寫、人工抽查 10%。
  2. 段落改成只給截短後用到的那幾段（每一步的支持段落位置都有標）。
  3. 截短版的問題要另外合成語音。
- 非直線的 351 題沒辦法這樣截。

沒有做:
- 沒有改計畫。
- 沒有建立新題目，也沒有合成任何新音訊。
- GSM-Symbolic 的模板（GitHub）沒有下載。
- 沒有查 P1、P2 的 GitHub 模板是否能固定人名和數字，只改加上去的條件。如果可以，就能做到真正的同一題只差步數。

Decision needed:
1. 要不要把「同一題、只差步數」加成補充分析（超出凍結計畫）。
2. 如果要加，選哪個：
   - (a) MuSiQue 截短：4hop1 的 246 題 ×3 個版本，加上 3hop1 的 568 題 ×2 個版本。
   - (b) GSM-Symbolic：50 個模板 × main／P1／P2。
   - (c) 兩個都做。
   - 若選 (b)，要先去 GitHub 看模板能不能固定數字。
