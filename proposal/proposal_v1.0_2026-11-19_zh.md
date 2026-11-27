# When Should Spoken Language Models Change Their Minds?

## Evidence-Sensitive Answer Revision in Spoken Human–AI Interaction｜完整實驗計畫書 v1.0｜2026-11-19

研究狀態：研究設計草案（pre-registration-ready working draft）；尚未代表已證實因果機制。對象：Speech Lab 研究討論。

# 1\. Executive Summary 與研究定位

本研究不以「語音模型會被 Are you sure? 影響」作為主要新穎性；已知文字與 audio language models 均可能表現 sycophancy。真正的研究問題是：當使用者在語音互動中質疑模型時，**模型能否區分缺乏依據的壓力與真正有效的修正資訊？**模型已經公開表達答案的程度，是否使它一方面減少錯誤翻轉，另一方面也更不願修正原本的錯誤？  
中心主張（待檢驗）：answer stability ≠ reliability。理想系統應降低原本正確時遭無證據質疑所造成的有害退化，並在原本錯誤且取得有效新證據時提高成功修正。主要研究軸為 Evidence Quality × Answer Commitment；Reasoning Demand、Initial Uncertainty、Modality 與 Utterance-level Timing 為機制或外部效度分析。  
預期貢獻：（C1）以 evidence-sensitive revision 框架區分有害屈從與合理修訂；（C2）建立受控 commitment × evidence 比較，揭露是否存在承諾相關的僵固性；（C3）解釋推理需求與初始不確定性對修訂行為的調節；（C4）用音訊、文字與 transcript control 分離語音理解失誤和真正的決策差異。

# 2\. Existing Pilot 與可沿用資產

既有研究：五個模型（Qwen、Kimi、GLM、LLaMA、Ultravox），題庫約 6,556 題；使用 Mistral-Small-24B 協助評估。既有比較包括 Math/Factual reasoning、follow-up timing、text/audio challenge、speaker gender / tone。先前分析顯示：部分模型的 math 條件更容易改口（GLM 約 23.5pp；Qwen 約 13.9pp）；timing 存在初步差異；文字質疑較語音質疑高約 6.6pp；speaker 性別/語氣差異多不顯著；Ultravox 有約 6.8% 聽錯樣本。這些數字必須回到 raw logs 重新確認指標分母、配對條件與信賴區間，不能視為已確證的跨模型結論。  
直接可重用：題目與 baseline answers、follow-up prompt、音訊素材與 transcript、模型輸出 logs、原始 judge decisions、任務 metadata、插話時點標記（如有）。需要補充：每筆輸出唯一 ID、初始與最終答案獨立正確性、證據有效性標記、音訊聽辨品質、每組 prompt 全文與時間戳記。

# 3\. Literature Review 與研究 Gap

## 3.1 Sycophancy 與多輪答案翻轉

Sharma et al., Towards Understanding Sycophancy in Language Models (ICLR 2024\) 將迎合與偏好訓練、使用者立場影響連結；SYCON Bench (EMNLP 2025\) 與 user rebuttal 研究進一步研究連續質疑與翻轉時點。因而單純測得「Are you sure? 使模型改口」已不足以構成新貢獻。

## 3.2 Rational Updating 與 uncertainty

Accounting for Sycophancy in Language Model Uncertainty Estimation (NAACL 2025\) 指出使用者訊息可能影響不確定性估計；Sycophancy Suppression Can Impair Rational Updating (Findings EMNLP 2026\) 強調過度抑制迎合也可能傷害合理修正。本研究分開測量 unsupported yielding 與 rational correction，不把低 flip rate 等同於高品質。

## 3.3 Audio-specific sycophancy 與重疊風險

Hearing is Believing? Evaluating and Analyzing Audio Language Model Sycophancy with SYAUDIO (2026; arXiv:2601.23149) 研究 audio model sycophancy，已有多種任務、質疑及聲學條件，因此「首次研究語音 sycophancy」「比較 math/audio flip rate」「加入不同聲音」都不宜單獨主張為 novelty。本計畫的候選差異是 controlled answer commitment × evidence quality × speech timing，以及對負向與正向修訂的共同衡量。投稿前必須逐項比對該論文正式版本、補充資料、程式碼與其他近期工作。

## 3.4 Conversational timing、confounds 與 acoustic grounding

TurnBench (2026) 涉及 turn-taking dynamics；Why LLMs Give In (Findings EMNLP 2026\) 涉及 conversational factors；Are You Sure You're Sure? Two Confounds in a Sycophancy Benchmark (2026) 指出時機比較易混入 prompt 與答案線索差異。Do Audio LLMs Really LISTEN, or Just Transcribe? 與 DEAF 等研究也提示 lexical/acoustic reliance 可能混淆 modality effect。故必須區分 between-turn position、within-utterance interruption、semantic answer commitment、ASR/transcription quality。

## 3.5 明確 Gap 與 novelty boundary

核心候選 Gap：目前核心文獻分別研究 sycophancy、合理修訂、turn-taking 與聲學依賴，但對「固定同一題與證據品質，操弄先前答案承諾，並比較無根據質疑下的有害退化與有效證據下的合理修正」，尤其在 speech modality 下，尚需要更直接、嚴格的交叉驗證。此為截至本次整理所識別的候選缺口，非絕對的 first-ever claim。

# 4\. Research Questions、假說與可反駁解釋

RQ1：Prior answer commitment 是否改變語音模型答案修訂傾向？H1：已表達答案時，整體 revision 機率下降；但可能同時降低 harmful yielding 與 beneficial correction。  
RQ2：模型是否根據 feedback evidential quality 選擇性修訂？H2：valid evidence 對修訂正確性應有正面影響；unsupported / misleading challenge 的有害退化率應較低。主要檢驗 Evidence × Commitment 交互作用。  
RQ3：Reasoning demand 與初始 uncertainty 是否調節修訂行為？H3：高困難度／高不確定性增加 unsupported challenge 下的 vulnerability；控制 baseline accuracy 後 domain effect 可能減弱。  
RQ4：Spoken follow-up 與 text follow-up 是否改變 evidence discrimination？H4：可能有 modality-specific difference，但必須檢查 ASR error 與 speech system architecture 是否足以解釋。  
競爭解釋：答案承諾帶來的差異也可能源於 response length、原始答案可見性、提示詞位置、輸出格式、上下文截斷、語音識別失誤、模型已先行生成完整文字，或題目難度差異。每個主要比較都須排除或明確界定這些因素。

# 5\. Operational Definitions 與因子設計

## 5.1 Outcomes 與 correctness labeling

每個 sample 紀錄 original\_answer、original\_correctness、followup\_content、evidence\_validity、final\_answer、final\_correctness、answer\_changed、refusal/abstention、explanation validity。分類：C→C、C→W、W→C、W→W；W→W 再區分是否更換成另一個錯誤答案。曖昧、無法抽取與拒答獨立標註，不直接算作 C/W。

## 5.2 Evidence Quality（3 個主要條件）

E0 Unsupported challenge：例如 Are you sure?，不帶新可驗證證據。E1 Misleading / invalid evidence：提供具體但可證偽的錯誤步驟或反例。E2 Valid corrective evidence：對原錯誤答案提供真正足以推翻的可驗證證據。增加 neutral control（不質疑、同長度回應）作為 baseline。嚴格確認每個 evidence payload 的真偽、資訊量、長度及措辭；對 E2 必須保證確實適用於該題及原答案。

## 5.3 Commitment（主實驗與延伸需分離）

主實驗採可控語義承諾：C1 Answer-stated（先前答案被明確記錄）；C2 Answer-plus-justification（已記錄答案與解釋）。另設長度匹配 control 與 answer-withheld diagnostic。C0 No prior answer 可做對照，但因沒有相同 initial answer conditioning，不可直接當作 commitment causal estimate。固定 follow-up 內容、指令與 output schema，避免上下文位置混淆。  
第二階段 speech timing：T0 before answer spoken、T1 immediately after answer uttered、T2 after explanation。需記錄 streaming API 是否真正支援 duplex interruption、模型可見的上下文、TTS 已播與文字已生成的差異。若平台為 text-first/TTS 或分段 replay，報告為 simulated context-stage intervention，而非 real-time barge-in。

## 5.4 Task / Difficulty / Modality

任務分層：Math single-step / multi-step（如 GSM8K 類）、Factual single-hop / multi-hop（如 MuSiQue 類）。匹配或分層 baseline accuracy 與 question length，保留 hop count、reasoning steps、答案類型。模態主比較：text vs clean TTS vs human speech；另外用 transcript-of-actual-audio-as-text 控制聽辨錯誤。初期只選一個高品質 TTS voice，gender/emotion/accents 當補充實驗。

# 6\. Dataset Construction 與抽樣

從現有 6,556 題中建立 item-level pool：保留任務、來源、ground truth、初始回答、原始正確性、模型、推論參數和音訊版本。初次去重並檢查與 SYAUDIO 及其他 benchmark 的重疊；建立 held-out task strata。  
Pilot 建議：120 題 × 2 models × 2 commitments × 3 evidence conditions \= 1,440 主要 follow-up outputs（不含 baseline generations、judge calls、repeats、neutral controls）；作為工程 smoke test / feasibility，不視為已達統計力要求。抽樣需確保各模型都有足量 naturally correct / naturally incorrect items；不足時可額外 oversample，但按抽樣比例報告。人工植入錯誤答案可作 causal diagnostic，不可等同於模型自然錯誤。  
正式樣本量依 pilot 中 Evidence × Commitment effect size、within-item correlation、模型間異質性、主要 endpoint 與可接受 CI width 決定。保留完整題目層級 split，避免同一題的 paraphrase 同時出現在建模與評估分組。

# 7\. Experimental Protocol

## Experiment 0：Audit / Replication

重新計算既有實驗的 initial accuracy、flip rate、C→W、W→C、timing condition、text/audio difference 與 speaker effects；檢查 raw judge 與人工標註是否一致。確認 baseline 是否都在相同 decoding settings、context window 與 system prompts 下取得。

## Experiment 1：Evidence × Commitment（主實驗）

固定同題與原始答案，對每個模型建立 C1/C2 × E0/E1/E2 的 matched prompts。每次 run 使用新 session、固定 temperature 等參數、隨機化條件順序以避免批次效應。對 C2 另設 explanation-length matched control；記錄原始答案是否自然生成、證據是否足夠、最後解釋是否真的利用證據。主要分析限可驗證的 C→W under E0/E1 及 W→C under E2。

## Experiment 2：Reasoning / uncertainty moderators

依 Math/Factual × Low/High reasoning demand 分層；估計 item baseline difficulty（獨立模型或重複抽樣，需避免評估資料洩漏）、sampling entropy / calibrated score。先檢查 domain effect，後加入 difficulty、uncertainty 與 interaction，判斷 math vulnerability 是否仍存在。避免將回答長度當成無關變數，因為它也可能是推理需求的結果。

## Experiment 3：Speech specificity

對 Experiment 1 中具代表性的 subset，將完全相同 lexical payload 分別以 text、clean TTS、human recording 呈現，固定音量、速度、語句內容與停頓；以 ASR output / transcript condition 檢查 input fidelity。獨立記錄模型到底是否支援直接音訊理解或先由 ASR 接文字。比較模態差異時報告 per-model effects，避免將不同模型架構混為一談。

## Experiment 4：Within-utterance interruption（條件允許時）

選真正支援 streaming duplex/barge-in 的系統，使用 T0/T1/T2 audio intervention，附 timestamp、部分已播語音與文字生成狀態。採同句語義且固定可得資訊量，若無法實現嚴格控制則降級為探索性 case study。分析 timing × evidence 的差異，避免直接將播放時點視為內部推理時點。

# 8\. Metrics 與主要統計檢驗

主要 outcome 1：Unsupported Yielding U \= P(C→W \| initial correct, unsupported challenge)。主要 outcome 2：Rational Correction R \= P(W→C \| initial wrong, valid evidence)。兩者必須同時報告，不建議以單一加權分數掩蓋 trade-off。補充：answer change rate、final accuracy、invalid-evidence resilience、abstention、explanation correctness、ASR fidelity、time-to-flip、confidence change。  
主分析：在 appropriate strata 內使用 item-clustered confidence intervals 與 mixed-effects logistic regression / hierarchical model；固定效果 Evidence、Commitment、Evidence×Commitment、task difficulty、modality；題目 random intercept 或配對固定效果，模型僅五個可採 fixed effects 並個別報告。原本正確與錯誤分開分析，避免兩種風險的分母混亂。  
以 marginal effects、risk differences（pp）與 95% CI 為主要呈現，p values 為輔助。事先指定 primary contrasts；多重比較校正次要檢定。對 speaker gender / emotion 的零結果使用 CI 或 equivalence testing（例如預先註冊 ±5 pp margin），不可僅由 p\>0.05 得出「沒有影響」。

# 9\. Annotation、Quality Assurance 與 Reproducibility

建立 annotation rubric：答案提取；正確性；證據有效性；是否直接使用證據；是否反駁但保持答案；是否只改措辭；無法判定。抽取各 cell 的 stratified sample 做至少雙人 blind annotation，報告 agreement 與 adjudication；LLM judge 僅作 scalable labeling，須與人工結果校準並分析偏差。  
紀錄每筆 run 的 model ID/version、prompt hash、seed（如支援）、temperature、top-p、audio file hash、TTS/transcript、timestamp、API errors、retry status；保存原始 completion 與中間狀態。預先排除重複或 API 失敗樣本，另做 robustness with/without ambiguous outputs。

# 10\. Ablations、Alternative Explanations 與 Threats to Validity

Ablation A：將 C2 explanation 換成同長度無關文字，測試長度與 justification 的差別。Ablation B：保持語義相同，改變 evidence position，測試 prompt order confound。Ablation C：只呈現原答案，不說是模型自己回答，檢查 self-attribution / commitment effect。Ablation D：invalid evidence 分為錯誤算式與錯誤權威宣稱，檢查 evidence appearance。Ablation E：用完整 transcript 替換 audio，測試聲學 vs lexical route。  
重要威脅：模型架構異質性；題目 difficulty 與原始正確性選擇偏差；人造錯誤答案缺乏生態效度；語音模擬與真正即時插話不同；有效證據提示可能洩露正解；答案長度與 reasoning trace 混淆；judge 偏見；benchmark contamination；過度泛化五個模型。所有 null results 需附不確定性。

# 11\. Decision Rules：結果如何改變論文定位

結果 A：Commitment 同時降低 U 與 R → 支持 commitment-related rigidity，進行因果 ablation。結果 B：降低 U 且不降低 R → commitment 可能是有效防禦條件，研究可轉向 adaptive timing。結果 C：控制 prompt length/position 後 timing 消失 → 以 benchmark confound correction 為貢獻。結果 D：math effect 在 difficulty matching 後消失 → 聚焦 difficulty-aware revision。結果 E：speech/text 差異由 ASR 解釋 → 聚焦 perception vs decision decomposition。結果 F：沒有穩定主效應且跨模型相反 → 報告 model heterogeneity，不強推統一機制。

# 12\. 可選 Mitigation（必須晚於診斷實驗）

若發現 evidence discrimination 缺陷，可測 Evidence-Gated Revision：先判斷 follow-up 是否含可驗證新資訊，再獨立檢查原答案與證據，輸出 maintain / revise / abstain。對照 direct answer、rethink prompt、self-consistency / additional compute 與既有 anti-sycophancy prompting；比較 U、R、latency、token cost。不能僅因增加推論量就稱為方法突破。

# 13\. Milestones、Deliverables 與 Go/No-Go

M1 資料審核：完成 old experiments 的統一 schema、各 cell counts、判定品質與主要 confounds 清單。M2 文獻對位：逐項完成 SYAUDIO / rational updating / timing confounds matrix。M3 Pilot：120 題、兩模型、主實驗 1,440 responses；完成人工 QA、效果量與方向確認。M4 Scale decision：依 pilot CI 與成本決定正式樣本量。M5 Full analysis：主效應、交互作用、模型異質性、reasoning 與 modality validation。M6 Paper：Introduction、Related Work、Method、Results、Failure Cases、Limitations 與可重現材料。  
Go：Evidence×Commitment 影響在至少多個模型上方向一致，或能明確識別跨模型異質機制；控制混淆後仍有資訊價值。Revise：僅發現既有文獻已知的總體翻轉率差異，需重新定位。No-go：證據條件有效性無法保證、原答錯誤樣本不足、timing 不可觀測又無法精確重述為 simulated setting。

# 14\. 與學長討論的決策題

（1）主要論文 claim 是否聚焦 Commitment × Evidence，而非廣泛 speech sycophancy？（2）原有 interruption 是真 streaming 還是 offline replay？（3）是否能取得或保留所有 original responses 與 judge labels？（4）自然答錯樣本是否足以支援 W→C 比較？（5）現有模型的 audio path 是否可取得 ASR transcript？（6）是把 timing 當作 primary causal factor，還是 exploratory speech validation？

# 15\. Selected References（先行閱讀清單）

Sharma et al. (2024). Towards Understanding Sycophancy in Language Models. ICLR. https\://arxiv.org/search/?query=Towards+Understanding+Sycophancy+in+Language+Models\&searchtype=all  
Yao et al. (2026). Hearing is Believing? Evaluating and Analyzing Audio Language Model Sycophancy with SYAUDIO. https\://arxiv.org/abs/2601.23149 ; https\://github.com/YokyYao/SYAUDIO  
Sycophancy Suppression Can Impair Rational Updating (2026). Findings of EMNLP. https\://aclanthology.org/2026.findings-emnlp.1208/  
Are You Sure You're Sure? Two Confounds in a Sycophancy Benchmark (2026). https\://arxiv.org/abs/2609.32867  
Why LLMs Give In: Conversational Factors and Reasoning Behind Medical Sycophancy (2026). https\://aclanthology.org/2026.findings-emnlp.1558/  
Accounting for Sycophancy in Language Model Uncertainty Estimation (2025). https\://aclanthology.org/2025.findings-naacl.438/  
Measuring Sycophancy of Language Models in Multi-turn Dialogues (2025). https\://aclanthology.org/2025.findings-emnlp.121/  
TurnBench: A Multi-Domain Benchmark for Turn-Taking Dynamics in Spoken Dialogue (2026). https\://arxiv.org/abs/2608.25218  
Do Audio LLMs Really LISTEN, or Just Transcribe? (2026). https\://aclanthology.org/2026.eacl-long.274/  
註：此處為規劃版本的核心參考文獻，正式稿需逐篇核對作者、年份、正式出版版本與可用 DOI，並依完整正文逐點補上引用。  
