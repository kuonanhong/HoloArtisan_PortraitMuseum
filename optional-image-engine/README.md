# Holo-Artisan：離線 CPU 神經人像回應引擎

本附件包含 **LivePortrait 四組真實預訓練權重（519,927,141 bytes）**、所需網路架構原始碼、CPU 推論程式、HTTP 介面及已生成的範例。它會依照觀眾情緒、注視方向、畫作的回覆文字，重新合成人像區域的像素。原圖的其他區域保留，接縫以羽化遮罩融合。

它是學習式特徵變形與 SPADE 神經影像合成；不是擴散式任意文字生圖，也不是光學全像硬體。Qwen 在瀏覽器生成對話；這個獨立引擎把情緒與注視方向映射為人像表情控制，並依回覆長度、問句狀態調整說話嘴型。嘴型不是音素級唇語同步，也沒有把文字送往雲端。沒有連接此引擎時，網頁使用明確標示的 Canvas 程序式動畫。

## 安裝與啟動

建議桌機／筆電、Python 3.11 或 3.12、至少 4 GB 可用記憶體。權重已附上，不必重新下載。第一次安裝 Python 套件需要網路；安裝完成後推論完全離線。此附件不包含每種作業系統的 Python 安裝程式或二進位套件。

Linux / Windows 的 CPU PyTorch 安裝指令（先進入本目錄）：

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python server.py --preload
```

macOS 的 PyTorch wheel 使用 PyPI。引擎仍明確指定 CPU，不使用 MPS 或 GPU：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.6.0
python -m pip install -r requirements.txt
python server.py --preload
```

完成安裝後，Linux/macOS 可用 `./start.sh`，Windows 可雙擊 `start.bat`。網頁與引擎應在**同一台電腦**。請以 localhost 開啟網頁，或在 `https://kuonanhong.github.io` 開啟部署版本，再按網頁的本機神經影像連接按鈕。瀏覽器可能顯示本機網路存取提示。

服務位址固定預設為 `http://127.0.0.1:8766`，只監聽本機回送介面。手機的瀏覽器版本仍可獨立使用離線 Qwen 與程序式動畫；本附件沒有宣稱可在 iOS／Android 直接執行 PyTorch。此 CPU 引擎已在 Linux x86_64、Python 3.12、PyTorch 2.6.0+cpu 實測；Windows、macOS 是可移植原始碼與安裝指引，未在本次環境實機驗證。

## 已做的實際驗證

`examples/` 含蒙娜麗莎、戴珍珠耳環的少女各四種情緒的神經合成結果及原圖／喜怒哀樂比較圖。`examples/validation.json` 記錄 8 次 CPU 推論，4 個執行緒，單張約 5.6–7.1 秒；這是本次執行環境的結果，不是手機或所有電腦的速度承諾。網路連線建立函式在這組驗證中被封鎖。生成圖有獨立 SHA-256，和原圖確實不同。

約 1.3 億參數的網路不適合宣稱在普通手機上即時生成。每次回覆生成一張新表情影像；網頁可在等待時繼續顯示動畫。換畫後需重新擷取特徵；相同人像會快取一次特徵，最多保留一張。

**裁切品質會影響效果。** `faceBox` 是畫作內人工估計的臉部矩形；伺服器會擴大為包含頭髮與部分肩膀的方形。中央人物、多人、側臉、非常抽象的人像可能失敗或出現痕跡。這次以兩幅著名人物畫確認生成效果，不代表其餘館藏均已經逐一驗證神經表情品質。無人物作品應繼續使用網頁的注視焦點導覽。

## HTTP 介面

`GET /health` 回傳 `ok / engine / device / loaded`。

`POST /respond` 的 Content-Type 必須是 `application/json`：

```json
{
  "image": "data:image/jpeg;base64,...",
  "faceBox": {"x": 0.34, "y": 0.145, "w": 0.28, "h": 0.25},
  "emotion": "delight",
  "gaze": {"x": 0.7, "y": 0.45},
  "dialogue": "你注意到了我的微笑，這讓我很開心。",
  "intensity": 0.8
}
```

`faceBox` 與 `gaze` 使用原始畫作正規化座標 0–1。情緒接受 `joy / anger / sadness / delight` 或 `喜 / 怒 / 哀 / 樂`。回傳 `image` 是 PNG data URL，另附 `seconds / neural / cropPixels / controls`。HTTP 介面只接收上傳影像，不接收檔案路徑或下載 URL。影像上限 5 MiB、16 MP，推論前縮至最長邊 2048；JSON 上限 7 MiB。連接前端建議逾時至少 120 秒。

CORS 允許本機 `http://localhost`、`http://127.0.0.1` 及 `https://kuonanhong.github.io`；其他網站會被拒絕。從 `file://` 開啟的網頁通常帶 `Origin: null`，因此需要改用套件附帶的本機靜態伺服器。服務不儲存上傳影像或對話。

命令列也可直接生成：

```bash
python render.py ../assets/art/mona-lisa.jpg mona-response.png --face-box 0.34 0.145 0.28 0.25 --emotion delight --gaze 0.7 0.45 --dialogue "Hello, you noticed my smile."
```

## 來源與授權

- 官方程式：[KlingAIResearch/LivePortrait](https://github.com/KlingAIResearch/LivePortrait)，固定 commit `9b294b3d0536135442ea73cb01e6cb3ca7029dd3`。
- 官方模型：[KlingTeam/LivePortrait](https://huggingface.co/KlingTeam/LivePortrait)，固定 revision `82a4fa6735ca58432b6ce39301b4b9ee066dea47`。模型卡標示 MIT。
- MIT 授權全文見 `LIVEPORTRAIT-LICENSE.txt`，程式與權重來源／SHA-256 見 `code-manifest.json`、`weights-manifest.json`。
- 官方明確提醒 InsightFace 的偵測權重限非商業研究；本附件**沒有包含或呼叫 InsightFace、landmark 偵測器或其權重**。以提供的人工臉部區域取代自動偵測。
- 表情控制係數改寫自同一 MIT 程式的 `src/gradio_pipeline.py`，神經網路架構保留上游實作。`engine.py` 將輸入裁切、CPU 推論、合成及限制組合成精簡介面。
- 範例畫作來源與公有領域標示見 `examples/SOURCE_ARTWORKS.json`。`examples/` 的回應影像是修改後的示範衍生圖，不能當作館方提供的原始畫作。
- 論文：[LivePortrait: Efficient Portrait Animation with Stitching and Retargeting Control](https://arxiv.org/abs/2407.03168)。

Python 執行依賴的授權與測試版本見 `runtime-licenses/`。這些套件由安裝步驟取得，本附件沒有重新打包各作業系統的執行檔。合併主套件與本附件後，可執行 `python verify.py` 重現 8 張影像的離線 CPU 驗證。

需要修復遺失權重時才執行 `python download_weights.py`；這會從上述固定官方 URL 下載並核對雜湊。正常使用不執行任何下載。
