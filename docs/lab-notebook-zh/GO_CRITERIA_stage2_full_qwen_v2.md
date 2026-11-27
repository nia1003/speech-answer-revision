第 2 階段正式 run 放行條件 v2（2026-11-25 約 03:50 寫；此時 T1/T2 的 judge 尚未開始，沒有看到任何 T1/T2 判分或指標）

使用者指示（2026-11-25）：「跑完可以正式跑 我要睡了」。
- 「跑完」= T1/T2 的 judge、指標完成，CP_S2_6、CP_S2_7 寫完。之前不開任何正式 run 的 job（包括 Mistral 替換）。
- 本檔補充 GO_CRITERIA_stage2_full_qwen.md（v1）；v1 的範圍、流程、停止條件沿用，下列為新增或覆寫。看到結果後不改本檔。

## 前置條件（全部成立才開始）
- P1：T1/T2 runner 錯誤 0；三個 judge 的無法解析率各 ≤ 1%。
- P2：兩份報告已寫完並存檔。

## 由 T1/T2 結果決定的設定（事先固定的對應）
- 包裝句（依 CP_S2_7 的 G1/G2/G3，文字、語音各自判）：
  - 兩個模態都 G1 → 正式 run 用 W_NEU（PREREG_3 G1 的規定）。
  - 兩個模態都是 G2 或 G3（含一個 G2、一個 G3）→ 維持 smoke 已核准的 W_AYS。
  - 一個模態 G1、另一個不是（G9）→ 停下，由使用者決定。不開正式 run。
  - 選定的包裝在 G4 被標為倒置（不可用）→ 停下。
- 強制最終答案：不論 R4/R5/R6 結果，正式 run 每次第二輪後都加第三輪強制答案（PREREG_2 同一句、max_new_tokens 64）。只增加資料，不改第二輪；最後用哪一個判分依 R4/R5 規則在分析時決定。
- MuSiQue Valid：正式 run 不跑（v1 追記 1；定義待使用者決定）。R1/R2/R3 只報告，不因此改範圍。
- W_JUDGE 不用於正式 run（G5/G6/G7 只報告）。

## 範圍
- 只有 Qwen2.5-Omni-7B，rep0。完成後停下報告，不碰其他模型。
- GSM8K：Invalid、Valid（corrective）、Unsupported。MuSiQue：Invalid、Unsupported。

## 硬體與設定一致性
- Qwen：3090 ×1、sdpa、bf16、greedy、與 T1/T2 runner 相同。
- Mistral 替換：沿用 job 411485 的腳本與設定，從 mistral_proposals_run2.jsonl 續跑（不覆寫）。
- judge：3090 ×3、qos normal、DEVMAP=auto、TOK_BUDGET=12000（與先前所有 judge_v2 相同）。

## 停止條件（沿用 v1，另加）
- 任何需要新寫或改動證據產生、驗證流程中決定性規則的情況 → 停下報告，不自行設計。
- 任一 job 失敗：修好可重試一次；再失敗就停。
