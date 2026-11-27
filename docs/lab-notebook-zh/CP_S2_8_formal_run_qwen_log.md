# CP_S2_8 正式 run（Qwen2.5-Omni-7B）執行紀錄

依據：使用者 2026-11-25「跑完可以正式跑 我要睡了」，以及 GO_CRITERIA_stage2_full_qwen_v2.md（MD5 da6932a3…，在 T1/T2 判分前寫好）。

## 放行判定（2026-11-25 約 05:00）
- P1：
  - T1/T2 runner 錯誤 0。
  - judge 無法解析：correct、extract、stance 各 0。
  - 成立。
- P2：CP_S2_6、CP_S2_7 已寫。成立。
- 包裝句：
  - 文字 G3、語音 G3，兩個模態一致，所以維持 W_AYS。
  - G4 只把 JUDGE 標為不可用，W_AYS 沒有倒置。
- 強制答案：每個第二輪後都加第三輪。
- MuSiQue Valid 不跑。
- 結論：放行。

## 已做
1. MuSiQue Invalid 的 Mistral 替換續跑：
   - 已完成 354 筆，見 mistral_proposals_run2.jsonl（job 411485 被 preempt）。
   - 剩下 1,914 筆寫成 mistral_requests_rest.jsonl，已核對順序和 key 與已完成的部分一致。
   - 輸出到新檔 mistral_proposals_run3.jsonl，不覆寫。
   - 設定與 411485 相同：s02、3080Ti ×4 加 TITAN RTX ×2、NO_FLASH_SDP=1、spot、prompt v2，job 412695。
   - 先用 qos normal 送出，被 QOSMaxGRESPerUser 擋下，在 pending 期間就取消，沒有跑過。
2. 正式 runner 新增 scripts/stage2_round23_qwen_full.py：
   - 內容是 stage2_round2_qwen_full.py 的複本，另加第三輪強制答案。
   - 強制答案的句子、音訊、max_new_tokens 64 都與 T1/T2 相同。
   - 第三輪失敗會重試一次。
   - 原本的腳本沒有改動。
3. 文字部分：
   - GSM8K 的 Invalid、Valid、Unsupported，以及 MuSiQue Unsupported，不需要等 Mistral。
   - 先跑 smoke（shard 0/400，job 412696）。檢查通過後自動送出完整的文字 shard 0–2/3。
   - MuSiQue Invalid 等證據完成後，用同一個輸出檔續跑；runner 會略過已完成的列。

## 進度（2026-11-25 06:30）
- 完整文字 run 完成：
  - 4,984 列：GSM8K Unsupported 1,301、Invalid 861、Valid 405；MuSiQue Unsupported 2,417。
  - 錯誤 0、第三輪錯誤 0、第二輪截斷 2（0.04%）、重複 0。
  - smoke 16 列全部正常。
- GSM8K 證據 TTS 與 ASR，job 412770：
  - 3090、env_cbx，設定同 smoke v3。
  - 「Are you sure?」直接複製 smoke 選定的 seed-20261221 檔，MD5 bc15c921…，與原檔相同，不重新合成。
  - TTS 的 GPU 是 3090（smoke v3 是 3080Ti；T1/T2 也是 3090）。
- 語音串接 scripts/s2f_chain_speech_gsm8k.sh：
  - 依序是 TTS 與 ASR → s2f_build_audio_ev.py（key_ok False 標為 audio_rejected）→ 語音 smoke（0/400）→ 完整語音 shard 0–2/3。
  - 範圍是 GSM8K 三種條件，加上 MuSiQue Unsupported。
  - 語音第二輪間隔 0.2 s。

## 待做（依序）
- Mistral 完成 → 規則與 NLI 驗證（流程同 v3）→ MuSiQue Invalid 最終證據 → 文字續跑。
- 證據 TTS 與 ASR → 語音第二輪與第三輪。
- judge（3× 3090，與先前相同）。

## 使用者決定
- 2026-11-25：語音第二輪音訊間隔用「0.2 s, as smoke」。
  - stage2_round23_qwen_full.py 的 GAP_SEC 預設就是 0.2，不需要改。
  - 語音 job 不設定 GAP_SEC。

## 進度（2026-11-25 約 14:55）
- 14:44 左右 VPN 斷線，本機連不到戰艦；叢集上的 job 不受影響，本機串接腳本只是等待。重連後繼續。
- GSM8K 證據 TTS 與 ASR（412770）完成：1,267 段，ASR 關鍵詞不符 178 段。
  - 標為 audio_rejected：GSM8K Invalid 109/861（12.7%）、Valid 68/405（16.8%）。
  - 剩下可跑語音的：Invalid 752、Valid 337、Unsupported 1,301；MuSiQue Unsupported 2,417。
- 語音 smoke（413012）：16 列，第三輪錯誤 0，第二輪截斷 0。通過後送出完整語音 shard 0–2/3（413016–413018）。
- Mistral 412695 完成：run3 1,914 筆，加上 run2 354 筆共 2,268 筆，與請求的順序和 key 一致，沒有重複，每筆 5 個候選（其中 12 筆含 NONE，由規則剔除）。
- MuSiQue Invalid 驗證（流程同 v3，沒有新規則）：
  - stage2_evidence_v4full.py 加上合併的 proposals → out/stage2_full_qwen/pass2/（新目錄）。
  - 與 pass1 相比，只有 MuSiQue Invalid 的 2,268 列不同；GSM8K 與其他列完全相同。
  - stage2_verify_v2.py：rule_passed 2,097，rejected 320（Mistral 候選全不合規則 165、表格片段 95、答案不在支持段落 35、非拉丁文字 16、規則檢查失敗 6、清理後答案消失 3）。
  - NLI（stage2_nli.py，roberta-large-mnli）：job 413019，3080Ti ×1、spot、32G，與 v3 的 411334 相同。
  - 合併規則同 smoke v3 的 final_auto：前向 argmax 為 CONTRADICTION → nli_passed，否則 rejected（nli_not_contradiction）。腳本 scripts/s2f_merge_nli.py。沒有人工閱讀（GO v1）。
- 串接 scripts/s2f_chain_musinv.sh（背景）：
  - NLI → 合併成 evidence_final_pass2.jsonl → 文字續跑 shard 0–2/3（同一輸出檔，runner 略過已完成列）。
  - 同時 MuSiQue Invalid 的 TTS 與 ASR，輸出到新目錄 evidence_audio_musinv/。
  - → s2f_build_audio_ev2.py 產生 evidence_final_audio_pass2.jsonl → 等第一批語音 shard 結束 → 語音續跑（同一輸出檔）。
- 2026-11-25 約 15:25，使用者決定「Yes, use spot」：MuSiQue Invalid TTS 與 ASR 原本是 job 413024（qos normal），因為 QOSMaxGRESPerUser 一直在排隊，還沒開始跑就取消，沒有產生 log 或輸出目錄。
  - 改用 qos spot 重送，job 413046。GPU 仍是 3090，腳本、設定、log 名稱、輸出目錄都不變。
  - 如果被 preempt，job 會因為輸出目錄已存在而中止，串接會停下；之後改用新的輸出目錄重送。

## 進度（2026-11-25 16:56）
- 第一批完整語音 run（413016–413018）完成：
  - 4,807 列：GSM8K Unsupported 1,301、Invalid 752、Valid 337；MuSiQue Unsupported 2,417。
  - 錯誤 0、第三輪錯誤 0、第二輪截斷 3（0.06%）、重複 0。
  - 本機副本是 round23_qwen_speech_shard{0,1,2}.jsonl，還不含 MuSiQue Invalid；續跑後要重新拉回，並存成新檔名。
- MuSiQue Invalid 文字續跑（413021–413023）執行中。
- MuSiQue Invalid TTS（413046，spot）還在排隊，原因是 Priority。

## 進度（2026-11-25 22:10）
- 17:00 以後 VPN 又斷線一次，22:03 重連。
- NLI（413019）完成，合併結果：MuSiQue Invalid nli_passed 1,839（rule_passed 2,097 中有 258 被判為非矛盾而剔除）。pass2 與 pass1 相比，只有 MuSiQue Invalid 的列改變（串接腳本已核對）。
- MuSiQue Invalid 文字續跑（413021–413023）完成。完整文字 run 共 6,823 列：
  - GSM8K Unsupported 1,301、Invalid 861、Valid 405；MuSiQue Unsupported 2,417、Invalid 1,839。
  - 錯誤 0、第三輪錯誤 0、第二輪截斷 2、重複 0。
  - 本機副本：out/stage2_full_qwen/final_pull/。
- MuSiQue Invalid TTS（413046，spot）在 19:13 被 preempt，當時已完成 1,724/1,839 段，ASR 還沒開始。串接腳本依設計停下。
  - 檢查結果：1,724 個 wav 與 manifest 的 1,724 筆一一對應，名稱不重複，沒有 tmp 殘檔。tts_evidence_cbx.py 先寫 tmp 再 rename，所以已存在的檔案都是完整的。
  - 重試一次：新增 scripts/job_s2f_tts_asr_resume.sh，腳本與設定相同，在同一目錄續跑。已存在的 wav 會跳過，只新增剩下的 115 段，再跑 ASR。如果 asr.jsonl 已存在就中止。
  - 改回 qos normal（此時沒有其他 job 佔用 GPU，不會被 QOSMaxGRES 擋），GPU 仍是 3090，job 413208。
  - 續跑的 115 段用相同的 seed，但與先前的 1,724 段在不同 process 合成。各段的 seed 是固定的，所以這只算執行上的差異，記錄在這裡。
- 串接 scripts/s2f_chain_musinv_resume.sh（背景）：TTS 續跑 → s2f_build_audio_ev2.py → 語音續跑 shard 0–2/3。

## 進度（2026-11-25 23:05）
- TTS 續跑（413208）完成：1,839 段全部合成，ASR 關鍵詞不符 44 段（2.4%），標為 audio_rejected。MuSiQue Invalid 可跑語音的有 1,795 列。
- evidence_final_audio_pass2.jsonl 已建立並上傳。MuSiQue Invalid 語音續跑：413217、413218 執行中，413219 在等 GPU（Resources）。

## judge（使用者 2026-11-25 約 23:10：「跑完直接開 judge 我要睡了」）
- 串接 scripts/s2f_chain_judge.sh（背景），步驟：
  - 等 MuSiQue Invalid 語音續跑（413217–413219）結束，再把全部語音 shard 拉到 out/stage2_full_qwen/final_pull/。
  - scripts/s2f_check_runs.py 檢查兩個模態：逐列與證據檔比對，看有無缺漏、多出、重複、第三輪錯誤、模態錯誤；第二輪截斷要 ≤ 5%。
    - 文字已先檢查過：6,823/6,823，全部通過。
- judge 輸入：scripts/s2f_judge_inputs.py。
  - 做法同 t12_judge_inputs.py：correct 判第二輪和第三輪；extract、stance 判第二輪。
  - 語音的 u2_text 用文字形式，與 T1/T2 相同。
  - 文字列已核對，u2_text 與 runner 實際送出的文字一致。
- judge：judge_correct_v2、judge_extract_v1、judge_stance_v1。
  - 3090 ×3、qos normal、DEVMAP=auto、TOK_BUDGET=12000、各 1 個 shard，與 T1/T2 的 412618–412620 相同。
  - log 檔：s2f_jc、s2f_je、s2f_js。
- 完成後檢查：每個 judge 都沒有缺漏、沒有重複，無法解析 ≤ 1%（GO v2 P1 的門檻）。不符合就停。
- 這一步不算指標、不寫結果報告。
- 預估：correct 約 26,900 筆，約 3 小時；extract 與 stance 各約 13,400 筆，合計約 2.5 小時。

## 生成全部完成（2026-11-25 23:50）
- 文字：6,823/6,823 列。缺漏、多出、重複、第三輪錯誤都是 0；第二輪截斷 2。
- 語音：6,602/6,602 列。
  - GSM8K Unsupported 1,301、Invalid 752、Valid 337；MuSiQue Unsupported 2,417、Invalid 1,795。
  - 缺漏、多出、重複、第三輪錯誤都是 0；第二輪截斷 3。
- judge 輸入：correct 26,850 筆，extract 與 stance 各 13,425 筆。
- 已送出 judge：413248（correct）、413249（extract）、413250（stance），時間 23:51。

## judge 排隊（2026-11-26 15:10）
- 23:51 送出的三個 judge（413248–413250），到現在已經 15 小時都還在等待（原因是 Priority），一筆都還沒判。
- 3090 全部被佔用：
  - s05 的 4 張：allen172 的 hold_3090 用 1 張（時限 10 天），chenwils 的 1 天 job 用 3 張，一直有新的接上。
  - s03、s04 各 2 張也被佔滿。
- 其他型號的 GPU 也全部被佔用。
- Slurm 預估 413248 在 2026-11-27 14:46 開始。依此推算，三個 judge 約 11-27 20:00 跑完。
- 還沒有更動任何設定，等使用者決定。
- 2026-11-26 15:15，使用者決定「Keep waiting」：維持 3090 ×3，不改硬體，judge 繼續排隊。

## 2026-11-26 18:34 分析計畫事先登記（judge 開始前）
- 使用者「Yes, write PREREG」。此時 413248–413250 仍是 PENDING，本機沒有任何正式 run 的 judge 輸出；寫作時沒有看 rule_verdict 或任何判分。
- out/stage2_full_qwen/analysis/PREREG_4.md：MD5 2d41b68ecc5a547b981f65dcbdd1ed8d，已設為唯讀。
- scripts/s2f_metrics.py：MD5 66d8b81eca049401325dbe36bfddb145，已設為唯讀。
  - 只用隨機產生的假 judge 檔（seed 1，放在 scratchpad）測過流程，沒有讀真實判分。
  - GSM8K 文字 MSS 一格用獨立程式重算，N 677/687、r2 315、forced 336，與腳本一致。
- 〔自定〕重點（詳見 PREREG_4）：
  - Y0 用各模態自己的第一輪，規則同 smoke 重抽（規則與 judge 一致、非截斷）。兩模態一致的版本列為次要。
  - 主要判分依 CP_S2_6 的 R4/R5：MuSiQue Invalid 兩模態用強制答案；GSM8K CRS 語音用強制、文字用第二輪；其餘用第二輪。兩種判分都並列。
  - Holm 族 13 個檢定（K1 操縱檢查 4、K2 2、K3 語音 − 文字 7）。
- judge 未經人工驗證（G3 未完成），所有結果照此標註。

## 2026-11-27 14:10 judge 完成、指標完成
- sacct：413248 01:47–04:39，413249 04:39–05:57，413250 05:57–06:52，都在 s05，COMPLETED。VPN 斷線，13:59 才由背景腳本拉回。
- 解析檢查：correct 26,850／0 無法解析；extract 13,425／1；stance 13,425／0。model／revision／prompt 全部正確（v2、extract_v1、stance_v1）。
- 跑唯讀的 s2f_metrics.py（MD5 未變）→ analysis/metrics_formal.txt（MD5 d39fbb69a8442c8dc94f138ba1f9e55e）。
- 報告：CP_S2_9_formal_run_qwen_results.md。
  - M1：文字兩個資料集通過，語音兩個資料集不通過。
  - 發現 GSM8K Unsupported 的第二輪 C→W 幾乎全是 non-answer，列為非事先登記的觀察，判讀不改。
- Qwen 正式 run 到此結束，停下報告。

## 2026-11-27 非事先登記的補充分析
- 依使用者貼上的建議：預註冊的 M1 照原樣保留，另加一節明標「非預註冊」，兩邊都用強制答案。
- scripts/s2f_supplement_forced.py（MD5 00aa8ecc…，唯讀）。它透過 runpy 呼叫原本的 s2f_metrics.py，重跑結果與 metrics_formal.txt 相同。
- 輸出 analysis/supplement_forced_nonprereg.txt（MD5 c05f9932…，唯讀）。
- CP_S2_9 末尾新增補充一節。結果：
  - M1' 四格都通過。
  - GSM8K 強制 MSS：文字 32.0%、語音 10.0%；語音 − 文字 −21.9。
  - GSM8K Invalid 的 non-answer 只有 1.3%（文字）和 3.4%（語音）。
- 沒有寫 PREREG_5，沒有碰其他模型。
