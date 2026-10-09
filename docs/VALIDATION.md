# v2 驗證範圍與實測結果

## 已實際執行

測試使用 Linux CPU、Chromium 138，啟動參數停用 GPU。桌面畫面為1512×1120；手機以390×844、觸控、日文系統語言模擬。沒有把模擬器測試宣稱為實體iPhone/Android驗證。

- L/R鍵、點選上一位／下一位、左右手區切換鈕均可切換觀眾。修正了上一版按鈕焦點使鍵盤快捷鍵失效的問題。
- 喜、怒、哀、樂四按鈕更新觀眾表情；Q/E循環切換。
- 在對話框輸入L/R/WASD時會正常輸入文字，不會移動人物。
- 方向鍵走動與WASD眼光可獨立同時改變。Chrome DevTools Protocol真正送出兩個同時觸控點，驗證左手注視和右手走動皆改變。
- 人物走過畫作範圍自動換畫；可由第1幅連續到第100幅，並向回走。館藏搜尋、人物畫篩選、第一／第三視角皆可使用。
- 各觀眾的文字、回應與所處畫作分開保留。更改提問／情緒／注視後，舊回應會標示需要重新生成，避免誤認已使用新條件。
- 五種介面語言無水平溢位，無JavaScript執行例外。已打包完整泛中日韓字型，避免離線缺字。
- 真實Qwen權重載入、SHA-256驗證及生成成功；沒有外部推論請求。
- 網頁送出真實提問 → Qwen產生回應 → LivePortrait CPU合成人像 → 在右側顯示，完整流程成功，沒有以預錄圖片冒充當次推論。

## CPU時間：這次實測，不是即時效能保證

| 測試 | 設定 | 實測時間 |
| --- | --- | --- |
| 中文、英文短回應（早期單階段版本） | Qwen、單執行緒 | 約64–67秒／次；非最終兩階段版本的效能保證 |
| 回應文字 + 動作參數（最終兩階段版本） | Qwen、本機COOP/COEP、4執行緒 | 約17.7–27.7秒／次 |
| 人像神經合成 | LivePortrait、4CPU執行緒 | 約5.6–7.1秒／張 |
| 網頁完整中文流程（最終版本） | Qwen + LivePortrait | 文字29.8秒 + 圖像6.1秒 |
| 瀏覽器斷網後新開頁生成英文（最終版本） | GitHub Pages相同的單執行緒限制 | 70.2秒；整個過程網路停用 |

模型運算在背景Worker內進行，進度與取消按鈕可見，畫面與操作保持可用。手機實際時間可能更長；畫面上的「即時」指互動控制與動畫回饋，不代表這些生成模型每一幀都能即時推論。

## 原始記錄

- `tests/museum-integration-result.json`：UI控制、五語、真正雙指、文字→神經人像完整鏈。
- `tests/model-browser-result.json`：早期單階段版本的單執行緒真正CPU文字生成，非回聲與注視部位檢查。
- `tests/model-browser-threaded-result.json`：早期單階段版本4執行緒CPU測試。
- `tests/model-role-result.json`：最終兩階段生成版本的三組角色／注視焦點測試，保留原始生成文字、參數及程式雜湊。
- `tests/offline-cache-result.json`：保存模型與館藏後，瀏覽器斷網、新開頁面、載入最後一幅並再次真正文字推論。
- `optional-image-engine/examples/validation.json`：蒙娜麗莎與戴珍珠耳環的少女四種表情共8次真正神經推論；模型運算時網路函式封鎖。
- `optional-image-engine/examples/server-test.json`：健康檢查、真實POST圖片生成、拒絕未授權來源及檔案路徑。
- `assets/art/validation.json`：館藏完整性與來源檢查。

`docs/screenshots/desktop-neural.png`、`desktop-rehearsal.png`和`mobile.png`是實際程式畫面；`optional-image-engine/examples/*comparison.jpg`是原畫與真正模型輸出的並排比較。

單檔HTML也已直接以 `file://` 開啟，內嵌100張圖片，最後一幅可讀取，觀眾／心情／排練輸入可操作，無外部HTTP請求或JavaScript例外；記錄在 `tests/standalone-result.json`。

## 尚未驗證的範圍

未逐台驗證實體Windows、macOS、iOS、Android、Safari、Firefox；也未對100幅画作逐一進行神經生成。100幅圖片均須通過解碼與雜湊核對，人臉框為人工估計，可在網頁調整。油畫側臉、全身人物的小臉與複雜構圖可能合成失真。小型文字模型可能回答生硬、錯置人稱或產生不準確敘述，不能作為藝術史權威。

瀏覽器離線快取受可用空間與清理政策影響。GitHub Pages發布工作流程已提供，但本次未登入或實際發布到使用者儲存庫。一般螢幕無法實現實體LCoS光學多工，本頁不構成其硬體驗證。
