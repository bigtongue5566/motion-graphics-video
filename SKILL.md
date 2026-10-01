---
name: motion-graphics-video
description: "Create and revise finished branded motion-graphics films with researched company facts, official logos and colors, original or licensed EDM background music, synchronized animation, and verified MP4 delivery. Use for company introductions, technology brand films, product explainers, 動態圖形影片, or requests to improve their EDM/BGM."
---

# 動態圖形影片製作

製作可播放的動態圖形影片，讓品牌敘事、圖形動作與 EDM 配樂共同推進。依使用者需求交付完整影片；只要求修改音樂時，沿用合適的既有畫面。

## 先決定真正需要的成品

- 沿用對話中已有的公司、片長、比例、語言、曲風與交付方式。未指定的項目可提出合理預設並繼續製作；套件預設範例為 90 秒、1080p、30fps。
- 保留指定片長。若樂句不足整小節，調整編曲與尾音來符合影片；不以音樂結構為由擅自改片長。
- 若工作區已有適合的素材或製作管線，優先沿用。腳本範本是起點，應依題材修改圖形、文字、場景與樂句。

## 品牌與敘事

製作公司介紹時，閱讀官方公司簡介、品牌規範及相關新聞；記錄來源、發布日、查核日與數據單位。區分成果與目標、功率與容量、實測與概念示意。使用官方 LOGO 與正式配色，保留比例及留白，檢查 SVG 在實際渲染器中是否正確顯色。

把可查證的優勢轉成簡短敘事。每個章節應有主訊息與支持它的圖形動作，例如能量沿路徑移動、模組組裝、網絡連結、數據形成。維持文字可讀的停留時間，使用前後景、節奏與場景變化建立層次。

分鏡與音樂共用一份時間表。先檢查分鏡圖、代表影格及短片段，再完成全片。品牌研究、畫面設計與來源格式見 [references/visual-production.md](references/visual-production.md)。

## EDM 配樂

科技與企業形象影片可從 Melodic House／旋律型 EDM 起步；曲風、強度與速度依題材及使用者偏好調整。以明確和弦、可記住的旋律、四拍鼓、低音與疏密變化支撐畫面。

旋律要考慮當下和弦、樂句走向與張力如何解決。避免把固定旋律任意疊在所有和弦上；控制跨和弦的延音、延遲與混響。為鼓、低音與主旋律留出位置，必要時使用 EQ、鼓觸發的音量起伏及聲部刪減。副旋律、琶音與效果應支援主旋律的角色。

使用合適的樂器音色或清楚控制泛音的合成器。真實鋼琴可用相容的 SoundFont／取樣樂器演奏；不要把簡單振盪器描述成真實鋼琴。提供音樂、音色庫及素材來源；音符原創與音色取樣是不同層次的來源。

音訊響度、峰值或音符檢查不能證明好聽。實際檢查開場、和弦銜接、完整節奏段、間奏與片尾；沒有可聽音訊的能力時，清楚區分已做的客觀檢查，提供可播放的配樂，不聲稱已試聽。使用者指出不和諧時，從和聲、旋律、尾音、聲部和音色查原因，再修改成品。詳細編曲與混音方法見 [references/edm-production.md](references/edm-production.md)。

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

直接檢查最終 MP4：片長、尺寸、幀率、全片解碼、音訊取樣率／聲道、響度／真峰值；抽查每章畫面、LOGO、字幕、轉場與最後一幀。檢查音樂的淡入／淡出、意外靜音及立體聲轉單聲道的情況。修正編碼或音訊問題後重新檢查受影響項目。

交付完整 MP4 與獨立 BGM；分鏡、來源說明、MIDI 與可編輯套件依需求提供。工作檔放在 work/，成品放在 outputs/，在聊天中使用可直接播放的影片／音訊與成品連結。報告實際完成的檢查與仍需主觀判斷的部分。
