# 旋律型 EDM 編曲與修正

## 實用起點

Melodic House 是科技企業影片的可用方向，通常可先試 118–126 BPM，四拍鼓配柔和鍵盤、主旋律、和弦與低音。這是選擇起點，不是其他曲風的限制。90 秒、120 BPM 恰為 45 小節；60 秒為 30 小節。指定長度不是整小節時，用最後一段樂句與淡出收束。

範本以 G 大調 I–V–vi–IV 為基礎，可移調。簡單三和弦與接近的排列先建立穩定感，再依需要加入七和弦、延伸音、懸留與經過音。不是所有音符都必須是三和弦音：張力若有意安排、得到解決就可成立。範本的和弦音檢查只驗證它自己的簡單編曲；修改成更豐富的樂曲時，也應修改允許的音符與張力說明。

## 檢查不和諧的原因

1. 比較旋律重拍／長音與當下和弦。固定循環的旋律可能只對部分和弦有效。
2. 看持續音、延遲、混響是否把上一個和弦帶進下一個；保留共同音，其餘尾音縮短、淡出或重新配音。
3. 檢查低音根音與和弦是否一致，和弦轉位是否在不合適的低音域造成混濁。
4. 分別檢查主旋律、琶音、背景和弦；多個都在中高頻密集活動時，先減少聲部。
5. 檢查失諧、FM 深度、非整數泛音、過亮齒波與長尾。不要只靠增加混響掩蓋刺耳的音色。

## 音色與來源

乾淨的鍵盤開場、柔和的 pluck、短和弦切分與深低音比大量金屬音色更容易形成穩定層次。合成器要控制最高泛音、濾波、起音、釋音與失諧量。鼓組與過渡噪聲也要分配頻段。

真實鋼琴可使用 GeneralUser GS 音色庫與 FluidSynth；作者公開授權允許音樂製作。使用前讀取現行授權，保存本次下載來源及 SHA-256。作者在此案查閱的相容性文件中推薦 FluidSynth；TinySoundFont 不完整支援調變器，不能假設它會呈現相同音色。可用其他合適取樣樂器取代。

範本沒有下載聲音的隱藏網路行為。沒有 SoundFont 時使用合成鍵盤；結果的音色來源會如實記錄為 synthesized keys。若追求自然鋼琴，補入相容取樣樂器並設定 music.soundfont 與 music.fluidsynth。

樂曲原創、使用樂器取樣、使用第三方歌曲是不同事實。配樂說明清楚記錄實際方式；使用第三方樂曲時保存其授權，不能把它寫成原創。

## 律動、段落與混音

- 主旋律有可辨識的輪廓與呼應。四或八小節的樂句可用變化維持注意力，不必每章都換一首音樂。
- intro 建立身份，groove 加入律動，build 增加期待，drop 展開，break 減少密度，outro 解決到終止和弦。角色可重排或省略。
- 低音與大鼓在節拍上錯開，或用短側鏈壓縮／音量 ducking 留出空間。非低音聲部可適量高通，避免一律切掉太多基音。
- 高頻效果只作點綴；重拍的 crash、短上升與留白要配合關鍵轉場，不要每幾秒全聲部一起衝滿。
- 混響／延遲的長度與節拍、和弦時間兼容。避免把高音效果做得和主旋律同樣前景。
- 企業影片的起始母帶目標可設約 −16 LUFS、真峰值上限 −2 dBTP，為 AAC 留餘裕。這些是可調製作值，不是所有平台的強制標準。檢查完成版 AAC 的實際峰值。

## 聽感檢查

有聽音能力時，分別聽完整歌曲、重點樂句及影片中的配合效果，檢查和弦變化、刺耳頻率、重拍、間奏及片尾；也檢查單聲道與較小音量。沒有聽音能力時，用符號與訊號檢查排除可辨識錯誤，提供可播放結果並如實說明，不宣稱音訊量測已證明悅耳。

## 本流程參考的原始教學

- [Ableton：Make a Melodic House Track](https://www.ableton.com/en/blog/make-a-melodic-house-track-in-10-minutes-on-ableton-move/)
- [Ableton Learning Music：Voicings](https://learningmusic.ableton.com/advanced-topics/voicings.html)
- [Ableton Making Music：Melody Contour](https://makingmusic.ableton.com/creating-melodies-1-contour)
- [iZotope：9 Tips to Produce an EDM Drop](https://www.izotope.com/community/blog/9-tips-to-produce-an-edm-drop-that-hits-harder)
- [iZotope：Unmasking Your Mix](https://www.izotope.com/community/blog/unmasking-your-mix-with-neutron)
- [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS)
- [FluidSynth](https://www.fluidsynth.org/)
