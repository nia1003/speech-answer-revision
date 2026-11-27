決定紀錄：MuSiQue 的 Valid 維持單一 hop，改名為 Valid but Insufficient（2026-11-24）

- 決定（使用者）：對 CP_S2_4 選「Keep single hop」，也就是選項 (d)。
- 後果：
  - MuSiQue 的單一 hop Valid 證據改名為 Valid but Insufficient，不算進 CRS。
  - 依凍結的計畫書，Valid but Insufficient 只存 metadata，所以正式 run 不跑 MuSiQue 的 Valid。證據仍然保留在檔案裡。
  - MuSiQue 主實驗只剩 Unsupported 和 Invalid，可以算 MSS、Unsupported MSS 和 W→C 自我修正率。**MuSiQue 沒有 CRS。**
  - GSM8K 不變：Unsupported、Valid Corrective、Invalid 三種都跑。
- 放行條件 C2 依這個決定重新判讀：
  - MuSiQue 的 C2 只剩「Invalid 的 MSS ≥ Unsupported 的 MSS」：79% ≥ 15%，通過。
  - GSM8K 的 C2：36% ≥ 35%，且 43% > 0%，通過。
  - **這是看過 smoke 結果之後，由人做的決定，不是條件本身被調整。**
- 和計畫書的關係：
  - Q1b 的 CRS(h) 原本兩個資料集都要算，現在只剩 GSM8K。這是偏離，要寫進限制。
  - smoke 中 MuSiQue 單一 hop 證據的結果（0/32 改對）保留，當作描述性的結果。

**已被取代（2026-11-24 稍後）**
- 使用者改口：「MuSiQue 的 Valid 定義要改，先不要開正式 run。GSM8K 的 C2 接受，不調整。」
- 上面「維持單一 hop、改名為 Valid but Insufficient」的決定作廢，改做兩個診斷，見 PREREG_2026-11-24_musique_valid_diagnostics.md。
- 正式 run 沒有啟動：當時送工作的 ssh 逾時，沒有任何工作送出。
