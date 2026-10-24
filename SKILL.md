---
name: motion-graphics-video
description: "Create and revise finished branded motion-graphics films with researched company facts, official logos and colors, original or licensed EDM background music, synchronized animation, and verified MP4 delivery. Use for company introductions, technology brand films, product explainers, 動態圖形影片, or requests to improve their EDM/BGM."
---

# 動態圖形影片製作

製作可播放的動態圖形影片，讓品牌敘事、圖形動作與 EDM 配樂共同推進。依使用者需求交付完整影片；只要求修改音樂時，沿用合適的既有畫面。

## 先決定真正需要的成品

- 沿用對話中已有的公司、片長、比例、語言、曲風與交付方式。未指定的項目可提出合理預設並繼續製作；套件預設範例為 90 秒、1080p、30fps。
- 保留指定片長。若樂句不足整小節，調整編曲與尾音來符合影片；不以音樂結構為由擅自改片長。
- 若工作區已有適合的素材或製作管線，優先沿用；可重用的是字型、素材、渲染與輸出能力，不必沿用範本構圖。若既有 renderer 限制了所需動作或材質，依視覺目標選工具。

## 先設計畫面與動作，再量產鏡頭

新片或視覺重做先閱讀 [references/art-direction-and-motion.md](references/art-direction-and-motion.md)：定義主體、視覺語言、代表鏡頭、動作因果和片尾落點，再擴展全片。需要選風格或使用者提供參考作品時，搭配 [references/style-recipes.md](references/style-recipes.md) 將參考拆成可實作特徵。不要把「科技感」直接等同深色網格、細線框和跳動數字。

先做能代表成品質感的關鍵畫面與短動態片段，檢查主體大小、字級對比、視線順序、運動軌跡、速度變化及收束。未形成有效構圖時先改設計，不用粒子、掃描線、抖動或更多轉場補救。這是工作中的自我驗證，並非每次都要停下來要求使用者批准。

可用原創 [動態練習](scripts/render_motion_study.py) 檢查預備動作、錯峰、路徑接力、局部遮罩和定格收束；它是無聲視覺練習，不是所有影片的風格模板或完整配樂成片。

## 品牌與敘事

製作公司介紹時，閱讀官方公司簡介、品牌規範及相關新聞；記錄來源、發布日、查核日與數據單位。區分成果與目標、功率與容量、實測與概念示意。使用官方 LOGO 與正式配色，保留比例及留白，檢查 SVG 在實際渲染器中是否正確顯色。

把可查證的優勢轉成簡短敘事。每個章節應有主訊息與支持它的圖形動作，例如能量沿路徑移動、模組組裝、網絡連結、數據形成。維持文字可讀的停留時間，使用前後景、節奏與場景變化建立層次。

分鏡與音樂共用一份時間表；另把標題入場、組裝完成、數字定格等重要動作寫入 cue map，由 renderer 與 composer 共用，並核對最終影格與音訊 onset。先檢查分鏡圖、代表影格及短片段，再完成全片。品牌研究、畫面設計與來源格式見 [references/visual-production.md](references/visual-production.md)。

製作新聞／事件年表、增加短片資訊密度，或使用者要求沿用上一版排版時，閱讀 [references/timeline-and-revisions.md](references/timeline-and-revisions.md)。用日期、可讀時間與內容動作安排事件；修改應保留已獲偏好的視覺骨架。片尾 CTA 是內容選擇，不是必備場景。

## EDM 配樂

依題材與使用者偏好先決定配樂的鼓型、主導音色、低音、樂句與段落，再同步畫面。科技與企業影片可以採用多種電子音樂方向，不能每次都套用同一個四拍鼓／pluck 範本。連續製作時比較前次配樂，依本案實際改寫聲部；只換 BPM、調性與曲名不會建立不同的聲音身份。

環境提供 edm-music-production 時，使用該 Skill 的風格選擇、音源與音樂草稿流程製作 BGM。它的曲風起點可在獨立音樂專案生成，之後按共用時間表與本片畫面合成；保留本片片長。這個影片套件自身附帶的作曲器仍是 Melodic House 起點，其他方向需要使用相應編曲器或改寫音色／律動。

預設配樂採協和、低張力的和聲：以大／小三和弦與平順聲部移動為起點，避免二度／半音堆疊、七度／九度張力、三全音、增減和弦及未解決懸留；只有使用者明確要求張力時才採用。檢查旋律、低音、長音與回聲的實際重疊，音符符合調性不等於同時發聲協和。

旋律要考慮當下和弦、樂句走向與張力如何解決。避免把固定旋律任意疊在所有和弦上；控制跨和弦的延音、延遲與混響。為鼓、低音與主旋律留出位置，必要時使用 EQ、鼓觸發的音量起伏及聲部刪減。副旋律、琶音與效果應支援主旋律的角色。

使用合適的樂器音色或清楚控制泛音的合成器。真實鋼琴可用相容的 SoundFont／取樣樂器演奏；不要把簡單振盪器描述成真實鋼琴。提供音樂、音色庫及素材來源；音符原創與音色取樣是不同層次的來源。

音訊響度、峰值或音符檢查不能證明好聽。實際檢查開場、和弦銜接、完整節奏段、間奏與片尾；沒有可聽音訊的能力時，清楚區分已做的客觀檢查，提供可播放的配樂，不聲稱已試聽。使用者指出不和諧時，從和聲、旋律、尾音、聲部和音色查原因，再修改成品。詳細編曲與混音方法見 [references/edm-production.md](references/edm-production.md)。

使用者指出刺耳、拍點模糊或畫面不同步時，從被指出的秒數 solo 問題聲部，核對實際音源、音域、泛音、力度、主擊／回聲層級與重要動作 cue，並交付含畫面的短片段比較；保留使用者偏好的疏密。方法見 [references/audio-continuity.md](references/audio-continuity.md)。

配樂反覆被指出單調或仍有不喜歡的音色時，依 [references/edm-production.md](references/edm-production.md) 的修改流程處理主題、聲部和音源；不要只提高 BPM、調低音量或改音色名稱。

「每一拍斷掉」時，檢查 MIDI gate 是否裁掉實際 release、共同音是否逐小節重啟，以及 gate／側鏈是否一起抽空所有聲部；依 [references/audio-continuity.md](references/audio-continuity.md) 修正。用同段、相近響度的短片段比較，並以短時間窗檢查拍間空隙；不要把一秒平均音量或和弦音符檢查當作連貫性的證明。

## 可執行的製作範本

沒有既有管線時，可用以下範本開始。先閱讀 [references/local-pipeline.md](references/local-pipeline.md) 與 [references/project-schema.md](references/project-schema.md)。

```text
python <skill>/scripts/init_project.py --project <project-directory>
python <project-directory>/work/render_video.py preview --project <project-directory>
python <project-directory>/work/compose_edm.py --project <project-directory>
python <project-directory>/work/render_video.py render --project <project-directory>
python <project-directory>/work/finish_video.py --project <project-directory>
```

修改 project.json 的品牌、場景、時間與音樂設定；補入本案的官方 LOGO、來源與內容。範本提供連續運動的向量場景、可變片長／速度／調性的原創 EDM、MIDI、音訊母帶、合成與驗證功能。依需求更換或擴充場景與編曲，避免把同一版配置當作所有公司的最終設計。

## 成品檢查與交付

依 [視覺評審方法](references/art-direction-and-motion.md#視覺評審與停止條件) 檢查實際畫面與動作，修正最影響觀感的問題，再檢查最終 MP4 的片長、尺寸、幀率、全片解碼、音訊取樣率／聲道、響度／真峰值。抽查 LOGO、字幕、轉場與最後一幀；檢查淡入／淡出、意外靜音及立體聲轉單聲道。編碼成功只證明檔案有效，不能替代設計評審。

交付完整 MP4 與獨立 BGM；分鏡、來源說明、MIDI 與可編輯套件依需求提供。工作檔放在 work/，成品放在 outputs/，在聊天中使用可直接播放的影片／音訊與成品連結。報告實際完成的檢查與仍需主觀判斷的部分。
