Checkpoint: CP_B10 Chatterbox，合成前把分數／比例改寫成文字（2026-11-21）

決定（使用者）：分數改寫成分數詞。

What ran:
- 新增 scripts/tts_textnorm.py，只套用在 GSM8K 題目送給 TTS 的文字上，文字條件的輸入不變：
  - 分數：「3/4」改成 three quarters，「1/2」改成 one half，「7/13」改成 seven thirteenths；分母大於 20 時改成「a over b」。
  - 帶分數：「1 1/2」改成 one and a half。但冒號後面的不算帶分數，例如「16:00 2/3」是時間接分數。
  - 比例：只改含 "ratio" 的句子，「5:6」改成 5 to 6。不改時間。
- MuSiQue 不改。原因是它的斜線是名稱和日期（"Directive 10/2"、"9/11"、段落中的 "775/778"）。
- 受影響的 GSM8K 題目共 103 題：含分數 97 題、比例 6 題。這已經涵蓋主分析的 96 題分數題和 smoke 裡的分數題。
- 410575（1×3090，s04）：
  - scripts/tts_chatterbox_norm.py：模型、設定、種子、切段都和 tts_chatterbox.py 相同。
  - scripts/asr_cbx_norm.py：Whisper large-v3 轉寫後，和**原題**的數字比對。兩邊都把英文數字、分數詞轉成數字，"a to b" 轉成 a:b，並去掉 $ 和 %。
- 輸出放在新資料夾，舊的 out/tts_chatterbox 沒有動。

Raw data:
- $PROJECT_DIR/out/cbx_norm/tts_chatterbox_norm/：question/ 103 個 wav，以及 manifest.jsonl（記錄送給 TTS 的文字）。
- $PROJECT_DIR/out/cbx_norm/asr_cbx_norm.jsonl：103 筆，每筆有原題、TTS 文字、轉寫、比對結果。log 在 tts_cbxn.log，沒有錯誤。
- 先前讀錯的題目，這次 Whisper 聽到：
  - 879：「one quarter as much…three quarters as much」，正確。
  - 898：「one fifth times more」，正確。
  - 871：「two-fifths…seven-thirteenths」，正確。
  - 319：「1 to 3」，正確。
  - 737：「1 half an ounce」，讀對了；比對不一致是比對程式的問題（見下方第 2 類）。

Computed results:
- 比對程式判定不一致的有 10/103（先前沒有改寫時，91 段分數題中 86 段不一致）。逐筆看過後分成兩類：
  1. **真的讀錯或聽錯，3 題：**
     - 116：「120」聽成「100」。
     - 177：原文寫「200$」，聽成「2,000 honors」。原題把 $ 放在數字後面。
     - 729：時間「8:00」「16:00」聽成「8,000」「16,000」。時間沒有改寫。
  2. **其實讀對了，是比對程式的問題，7 題：** 49、463、737、772、906、1088、1208。
     - 這幾題 Whisper 寫成「3 quarters」「1 fifth」「1 half」「1 third」「1 16th」「11 eighths」。
     - 數字加分數詞的寫法，numwords 沒有轉換，所以判成不一致。
- 真正錯的是 3/103（2.9%）。分數本身全部讀對。
- 速度：平均音長 12.6 秒，合成共 884 秒（約 15 分鐘）。

Anomalies:
1. 時間（「8:00」「16:00」）可能被讀成「八千」「一萬六千」。這是 Whisper 的寫法，沒有人工試聽，還不能確定 TTS 怎麼讀。主分析中含時間的題目至少有 23、729、862、952、953、1195。
2. 數字放在 $ 前面的寫法（「200$」「6000$」）會被讀錯。
3. 116 的「120」聽成「100」，屬於一般數字的偶發錯誤；先前也看過「125」聽成「105」（885）。

沒有做:
- 沒有人工試聽。
- 沒有改寫時間和「數字$」。
- 沒有修比對程式（第 2 類的 7 題已經人工判讀）。
- 沒有合成全量題目。
- 沒有跑任何模型的語音條件。

Decision needed:
1. 時間要不要也改寫（例如「8:00」改成 eight o'clock，「16:00」改成 four p.m. 或 sixteen hundred），還是先人工試聽 729 再決定。
2. 「200$」這類寫法要不要改成「$200」再合成。
3. 規則確定後，是否開始合成全量 3,736 題的題目音訊（估計 6–8 小時）。合成後用同一套 Whisper 檢查，不一致的題目再人工確認。
