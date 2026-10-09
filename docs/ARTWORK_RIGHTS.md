# Holo-Artisan 人物畫館：圖像來源與權利說明

本套件收錄 **100 幅不同的真實人物畫作**，其中 **50 幅標示 CC0、50 幅由來源標示 Public domain**。100 幅均已實際下載、以 Pillow 解碼核對，具有不同的 SHA-256，合計約 12.33 MiB。全部100幅提供人工臉部範圍。

本套件只收錄真實館藏的數位圖像；原畫區不使用 AI 仿作。完整清單、原始下載網址、典藏單位、逐件權利聲明、影像尺寸及 SHA-256，均保存在 `data/artworks.json`。`js/artworks.js` 是同一清單的瀏覽器版本，方便直接離線開啟 HTML。

## 選取標準

1. Cleveland Museum of Art：只選取官方 API 明示 `share_license_status = "CC0"`、`type = "Painting"`，且提供公開 `images.web.url` 的館藏。博物館開放取用政策允許下載、分享、改作與再利用標示 CC0 的圖像。館方政策：[Open Access](https://www.clevelandart.org/open-access)；[官方 API](https://openaccess-api.clevelandart.org/)；[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。
2. Wikimedia Commons：逐件保存檔案頁的 `LicenseShortName`、`Copyrighted`、權利連結及來源網址，只採用明確標示 Public domain 或 CC0 的檔案。館藏原件與該數位複製圖的權利聲明分别核對。凡來源標示攝影者保留著作權、CC BY、禁止商業使用或需另行授權，均不納入本清單。
3. 同一畫作的不同解析度、不同照片或裁切副本不重複計數。清單依獨立原作計數；人物群像仍為一件作品。中文標題為本展示的便利用譯，原語／英文標題另行保留。

## 本地檔案做了哪些變更

原始圖像等比例縮小至最長邊不超過 1000 像素，並轉存 JPEG。保留整幅圖像與來源原有的畫框、橢圓邊界；不裁除簽名或浮水印、不用生成圖替代真實原作。來源影像若本來含邊框，該邊框也一併保留。瀏覽器的右側回應畫作為另外的互動衍生呈現，應與中間原作明確區分。

`faceBox` 是人工在原圖上估計的臉部範圍（正規化 x、y、w、h），用於示範表情回應；不是臉部辨識結果。群像指定一位主要人物，側臉、微小臉部與高度風格化畫作的動畫效果會與正面近距離肖像不同。

## 再利用與標示

原作作者、館藏機構、下載檔案頁和權利資訊都保留於本地清單及網頁。CC0 不要求署名，本套件仍提供來源方便查核。Public domain／Public Domain Mark 是來源提供的權利狀態，不等同博物館替展示或產品背書，也不表示對全球每一法域作出法律保證。Wikimedia 的 PD-Art 頁面提示：二維公有領域作品的忠實重製在美國視為公有領域，而其他地區可能有不同规则；適用細節應以各件來源頁及預定發布地的法律為準。

- [Wikimedia：重用 PD-Art 圖像](https://commons.wikimedia.org/wiki/Commons:Reuse_of_PD-Art_photographs)
- [蒙娜麗莎來源與權利頁](https://commons.wikimedia.org/wiki/File:Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg)
- [戴珍珠耳環的少女來源與權利頁](https://commons.wikimedia.org/wiki/File:Girl_with_a_Pearl_Earring.jpg)

## 檔案核對與重新下載

本地圖像可直接使用，不需要重新下載。`python tools/download_artworks.py` 逐件驗證現有檔案與雜湊；如有缺檔，使用已記錄的原始來源恢復。重新下載需要 Pillow，且必須能連線至來源機構。程式遇到 HTTP 429 會停下並顯示 Retry-After，不會密集重試；來源撤檔或改變時，需要重新檢查來源與權利聲明。重新下載不保證未來上游檔案永久不變。

本說明核對日期：2026-10-08。
