# Holo-Artisan v2 離線生成模型說明

## 實際包含的模型

本附件已包含 **Qwen2.5-0.5B-Instruct / Q4_K_M GGUF** 的真實已訓練權重，並非只提供下載連結或預錄回答。來源為 Qwen 官方發布，Apache-2.0 授權；固定版本 `9217f5db79a29953eb74d5343926648285ec7e67`。原始權重 491,400,032 bytes，SHA-256：`74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`。

此模型約 0.49B 參數，具中文、英語、日語、韓語、西班牙語等多語能力。最終版不用預設回答範例。先由模型自由生成畫中人物的對話，再由同一模型生成表情與動作JSON；兩段皆是真實推論。解碼只約束第一人稱起首：中文「我」、英文“I”、日文「私」、韓文「저」、西文“Yo”，沒有預先寫好的完整回答。

選用原因是 CPU 可執行、多語及開放授權之間的實用取捨；**不宣稱它是所有任務中最好的模型**。比分類器大的原因是本版真的要生成語句。0.5B 模型的推理、事實正確性、長對話及語言流暢度，均比大型模型有限；回應是虛構藝術對話，並非人物原話或經考證之藝術史。

## 如何工作

1. 使用者明確按下載入後，頁面讀取同一網站／本地資料夾內的八個權重分段，每段不超過64 MiB；HTTPS與localhost 會逐段驗證SHA-256。
2. `wllama 3.8.1` 在 Web Worker 中，透過 llama.cpp WebAssembly 執行模型。設定 `n_gpu_layers: 0`；標準GitHub Pages為 `n_threads: 1`，本地HTTP若提供COOP/COEP標頭，最多使用4個CPU執行緒，完全不使用GPU或雲端推論API。
3. 每次將「作品名稱、手動輸入文字、觀眾情緒、注視焦點與座標、語言」送入本地模型，先生成第一人稱對話。第二次推論閱讀該對話與觀眾情緒，產生表情及動作JSON。程式合併成 `text`、`emotion`、`gesture`；情緒和動作由模型選擇，並非直接複製操作按鈕的值。
4. 文字結果與動作參數傳给畫作呈現層。**Qwen 是文字模型，不是圖片生成模型，也沒有直接看圖。** 人物表情、視線與動作如何呈現，見主程式／圖像呈現文件。不得把 Canvas 動畫說成擴散模型生成的新照片。

模型接受文字和館藏中繼資料，沒有攝影機、麥克風或臉部識別。手動輸入文字在此瀏覽器分頁中處理；生成介面無任何外部推論端點。不要把此設計直接等同完整醫療隱私法規認證。

## 啟動與跨平台

- GitHub Pages：完整資料夾保持相對路徑，HTTPS開啟，按「載入離線AI」。所有分段都能以普通Git檔案發布；不要使用無法由Pages直接供應的LFS指標替代權重。
- 電腦離線：先解壓，執行 `python tools/serve.py`，再開 `http://localhost:8000`。模型、WASM、圖片都在本地，不需要互聯網。
- 手機：可直接開GitHub Pages；真正離線使用前，必須先取得整包資產，或依主指南建立離線快取。僅開過首頁不代表491MB模型已下載。
- **直接雙擊 file:// HTML 不支援模型載入**：瀏覽器安全模型限制模組、Worker和讀檔。頁面會明確提示啟動本地HTTP，不會假裝AI已啟動。
- 包含本地 Safari 相容 WASM，避開套件預設的CDN；舊版瀏覽器仍可能缺少WebAssembly SIMD／例外處理等功能。
- 實際已測：桌面Chromium 138、禁用GPU、1與4個CPU執行緒、阻擋全部外部網路。Safari／iPhone與不同Android機型尚未在實機驗證，因此不保證所有手机皆可載入。

## 記憶體與速度

權重約469 MiB，但瀏覽器載入時還有 Blob、WASM、KV cache 和頁面圖像。建議使用可供瀏覽器使用至少1.5–2 GB記憶體的裝置；這是保守使用建議，不是最低需求認證。單執行緒生成可能需數十秒或更久，手機與Safari相容模式可能更慢。介面保留取消按鈕，移動、觀眾切換不應被 Worker 阻塞。此設計不提供「毫秒級即時生成」保證。

最終版實測：Chromium138、CPU四執行緒，三組完整「對話＋表情JSON」生成各為27.7、21.6、17.7秒。`elapsedMs`包含兩次推論。標準GitHub Pages通常只有單執行緒，可能明顯較慢；最終版的單執行緒時間請以主驗證報告為準。這些不是手機測速。

最終版語句品質、第一人稱、注視部位、原始生成文字／控制JSON、完整提示及程式SHA-256，在 `tests/model-role-result.json`。早期 `model-browser-result.json` 與 `model-browser-threaded-result.json`保留為執行器與外部網路阻擋測試紀錄，並已標示為舊提示／舊單次生成流程；不能將其時間當成最終版兩次推論流程的時間。不能以某一環境的測速保證所有设备相同。

小模型仍可能冗長、措辭不自然，或把提示中的座標說出來；測試也觀察到這種情況。最終三組測試都以畫中人物第一人稱回答並提及相關注視部位，但不代表任意問題都有可靠回答。未加入預錄回答替代模型輸出。

## 程式介面

```js
await HoloGenerator.load(({ stage, percent }) => updateProgress(stage, percent));
const result = await HoloGenerator.generate({
  artwork: { id: 'mona-lisa', title: 'Mona Lisa', artist: 'Leonardo da Vinci' },
  utterance: '妳為什麼微笑？',
  emotion: 'sadness',
  gaze: { x: 0.5, y: 0.35, label: '嘴角與微笑' },
  language: 'zh-TW'
}, wholeTextSoFar => updateText(wholeTextSoFar));
// result = { text, emotion, gesture, source: 'local-llm', elapsedMs, ... }
HoloGenerator.cancel();
```

`emotion`可為joy、anger、sadness、delight；`gesture`可為smile、nod、listen、reassure、wonder。模型失敗會拋出明確錯誤；不會以規則模板冒充生成結果。對話階段最多72 tokens、控制階段最多40 tokens，保留1024 token上下文以控制CPU負擔。`rawText`與`rawControls`是各階段的原始模型輸出；`raw`是程式合併後的JSON，不是另一次模型生成。

本地另含 OpenCC-js 1.4.2（MIT）將偶爾生成的簡體中文字轉為繁體；這是字形轉換，不是額外模型或預錄回答。

## 可重現性與授權

- `model/manifest.json`：每段bytes和SHA-256，以及原始完整檔案雜湊。
- `model/runtime-manifest.json`：本地執行套件版本、來源、檔案雜湊。
- `tools/model_download.py`：從固定官方版本重新下載、驗證並分段。
- `model/QWEN-LICENSE`：模型Apache-2.0授權。
- `vendor/model-wllama/LICENCE`、`LLAMA-LICENSE`：執行器及llama.cpp之MIT授權。
- 程式使用公開資料及使用者輸入，不會微調或重新訓練Qwen。

主要來源：

- Qwen官方模型卡：https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- Qwen官方GGUF：https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
- wllama作者程式與文件：https://github.com/ngxson/wllama
- wllama套件：https://www.npmjs.com/package/@wllama/wllama
- llama.cpp：https://github.com/ggml-org/llama.cpp

## 最終斷網測試

最終兩階段版本另通過 `tests/offline-cache-result.json`：先保存554,405,005 bytes的148個本機網站資產，再啟用瀏覽器斷網模式，另開頁面讀取第100幅畫、重新載入真實模型並生成英文回答。單執行緒70.2秒，無JavaScript例外。完整GUI中文→人像鏈另測得29.8秒文字生成，加6.1秒神經人像；此為測試環境數據，非每台裝置保證。
