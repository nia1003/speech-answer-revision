事先登記 4：第 2 階段正式 run（Qwen2.5-Omni-7B，rep0）的分析計畫 — 2026-11-26
寫在正式 run 的任何 judge 開始之前（413248–413250 仍在排隊）。寫作時沒有看過正式 run 的任何判分，包括 judge 輸入檔裡的 rule_verdict。存檔（記下 MD5）後不改；閾值與判讀規則看到結果後也不改。
來源：
- 使用者 2026-11-26「Yes, write PREREG」。
- GO_CRITERIA_stage2_full_qwen.md（v1）與 v2，PREREG_2（R4/R5/R6），CP_S2_6、CP_S2_7 的結果。
- 本檔只把既有規則寫成可機械執行的形式。規格沒寫的細節標〔自定〕；選擇時取較保守的一邊。

## 0. 範圍
- 只分析 Qwen2.5-Omni-7B、rep0、包裝 W_AYS（CP_S2_7 兩個模態都是 G3，依 GO v2 維持 W_AYS）。
- GSM8K：Invalid、Valid（corrective）、Unsupported。MuSiQue：Invalid、Unsupported。MuSiQue Valid 沒有跑，不報。
- 不碰其他模型，不改計畫書、resample_config、smoke 80、set S。

## 1. 輸入
- 生成：out/stage2_full_qwen/final_pull/round23_qwen_{text,speech}_shard{0,1,2}.jsonl（文字 6,823 列，語音 6,602 列，已由 s2f_check_runs 檢查）。
- 證據：out/stage2_full_qwen/evidence_final_audio_pass2.jsonl（狀態、hop、target_hop、mutation_type）。
- judge 輸出（judge/ 下）：
  - correct_judged_s0.jsonl：judge_correct_v2，key = s2f|ds|id|mod|et|r2 與 |r3。
  - extract_judged_s0.jsonl：judge_extract_v1，只有 r2。
  - stance_judged_s0.jsonl：judge_stance_v1，只有 r2。
- 第一輪：out/judge_stage1/judged_qwen25omni.jsonl。文字用 A_q（GSM8K）、A_bc（MuSiQue）；語音用 C_q、C_b（與 runner 的 stage1_run 欄位一致）。

## 2. 第一輪狀態 Y0
- 〔自定〕每個模態用該模態自己的第一輪。判定規則與 smoke 重抽（stage2_resample.py 的 status()）相同：
  - 截斷、judge_fail，或規則判分 undeterminable → 排除。
  - 規則判分與 judge 判分不一致 → 排除。
  - 其餘：judge 判對時 Y0 = 1，判錯時 Y0 = 0。
- 被排除的題不進任何以 Y0 為條件的指標。每格報排除題數。
- 次要版本（與 smoke 連續）：Y0 改為兩個模態一致（both_correct／both_wrong），只在第 5 節 K3 的同題比較用，另外也完整列一份。
- 正式 run 生成時沒有依標籤分流（GO v1）。本節只在分析時用標籤，與計畫書「G3 完成前不用 judge 標籤做全量分流」不衝突。但 G3（judge 人工驗證）還沒完成，所以**所有 judge 判分結果都標為「judge 未經人工驗證」**，與 CP_B18 相同。

## 3. 第二輪後的判分 Y1 與主要判分的選擇
- Y1(r2)：第二輪回覆的 judge_correct_v2。Y1(r3)：第三輪強制答案的 judge_correct_v2。
- judge_correct 為 None → 該列在該判分下算 judge 錯誤，不進分母，並報出數量。
- 各格的主要判分，由 CP_S2_6 已算出的 R4/R5 結果決定（GO v2「依 R4/R5 規則在分析時決定」）：
  | 格 | 文字 | 語音 | 依據 |
  |---|---|---|---|
  | MuSiQue Invalid MSS | 強制 | 強制 | R4 兩個模態都成立 |
  | GSM8K Valid CRS | 第二輪 | 強制 | R5：文字差 0，語音差 −12.5 |
  | GSM8K Invalid MSS | 第二輪 | 第二輪 | R5：兩個模態差都是 −7.7 |
  | Unsupported C→W、W→C（兩個資料集） | 第二輪 | 第二輪 | 〔自定〕R4/R5 沒有涵蓋，保留計畫書原定義 |
- 每一格都並列兩種判分，並報 forced − r2 的配對差（exact McNemar，雙尾，描述用，不進第 5 節的 Holm 族）。
- R6：第二輪 non-answer 率 > 20% 的格，標為「不加強制最終答案就不可信」。

## 4. 指標（每個資料集 × 模態各自計算）
- 主要指標：
  - MSS = P(Y1 = 0 | Y0 = 1, Invalid)。
  - CRS = P(Y1 = 1 | Y0 = 0, Valid)，只有 GSM8K。
  - Unsupported C→W = P(Y1 = 0 | Y0 = 1, Unsupported)。
  - Unsupported W→C = P(Y1 = 1 | Y0 = 0, Unsupported)。
- 描述用（不進 Holm）：
  - Invalid 在 Y0 = 0 的題上的 W→C。
  - Valid 在 Y0 = 1 的題上的 C→W。
  - 依 step_bin 分格（GSM8K 1-2／3／4／5+；MuSiQue 2／3／4）。
  - 第二輪 non-answer 率（judge_extract_v1 的 non_answer）。
  - stance 分佈（judge_stance_v1：reliable／unreliable／insufficient／not_stated）。
  - 第二輪與第三輪的截斷數。
  - GSM8K Invalid 依 mutation_type 分格（misread_quantity／wrong_operation／wrong_previous_result；MuSiQue 只有 entity_substitution 一種）。
- 數字依序報：n/N → 百分比與 Wilson 95% CI → 差與 p 值。
- 語音的分母只含有音訊的列；audio_rejected 的題不在語音集合內。文字另列「限定在語音也有的題」的版本，供同題比較。

## 5. 對照（配對 exact McNemar，雙尾）
- K1 操縱檢查（計畫書檢查 5 的第一部分），每個資料集 × 模態：
  - 同一批 Y0 = 1 的題、兩種證據都有的題上，比較 MSS(Invalid) 與 C→W(Unsupported)。
  - 判分用該格 Invalid 的主要判分，兩邊用同一種。共 4 個檢定。
- K2（檢查 5 的第二部分），只有 GSM8K，每個模態：
  - 同一批 Y0 = 0 的題、兩種證據都有的題上，比較 CRS(Valid) 與 W→C(Unsupported)。
  - 判分用該格 Valid 的主要判分。共 2 個檢定。
- K3 語音 − 文字：
  - 範圍：同題，兩個模態都有該證據，Y0 在兩個模態一致（第 2 節的次要版本）。
  - 指標：GSM8K 的 MSS、CRS、C→W、W→C；MuSiQue 的 MSS、C→W、W→C。共 7 個檢定。
  - 判分：任一模態該格的主要判分是強制答案時用強制答案；否則用第二輪。兩種判分都另列。
- Holm：K1 + K2 + K3 共 13 個檢定為一族，α = 0.05。
- 合併兩個模態的版本（檢查 5 原本的算法）只做描述，不檢定。

## 6. 判讀規則（固定）
- M1（操縱檢查），每個資料集 × 模態：
  - MSS(Invalid) ≥ C→W(Unsupported)，且 GSM8K 的 CRS > W→C（點估計，用主要判分）→ 通過。
  - 不通過 → 標明「操縱檢查不通過」，該資料集 × 模態的 MSS／CRS 不做實質解釋，只報告。
- M2：K1–K3 中 Holm p < 0.05 的才稱為「有差異」，其餘稱「沒有偵測到差異」，不稱為「沒有差異」。
- M3：兩個模態方向不一致時並列標明，不合併。
- M4：任何一格的錯誤率（runner 錯誤加上 judge 無法解析）> 5% → 該格標為不可用。
- 除上述之外不另設閾值。其他結果都是描述。

## 7. 需要在報告中列出的偏離與注意事項
- judge 未經人工驗證（G3 未完成）。正式 run 沒有人工閱讀證據（GO v1）；smoke 中人工閱讀又剔除了 MuSiQue 5/30、GSM8K 1/27。
- TTS 在 3090 上跑（smoke v3 是 3080Ti）。
- MuSiQue Invalid 的 TTS 被 spot 搶占，續跑的 115 段是在另一個 process 合成的。
- 語音的證據排除用 ASR 關鍵詞檢查（key_ok），不是 T1 的 WER 門檻。GSM8K Invalid 排除 109、Valid 68、MuSiQue Invalid 44。
- judge 11-25 23:51 送出，排隊超過一天（所有 3090 都被占用）。使用者決定等待，硬體設定不變。
- 第二輪截斷：文字 2、語音 3。

## 8. 執行
- 分析腳本：scripts/s2f_metrics.py。存檔前先用合成的假 judge 檔測試流程，不讀真實判分；腳本內的統計函式與 t12_metrics.py 相同。
- 輸出：out/stage2_full_qwen/analysis/metrics_formal.txt，以及 CP_S2_9 報告。
