# Plain Log

Plain Log 是一款簡潔、以文字為主的 WordPress 佈景主題，適合撰寫個人日誌與技術筆記。公開維護者為 [ww7argentina-debug](https://github.com/ww7argentina-debug/plain-log)。

## 功能特色

- WordPress 傳統佈景主題，首頁以時間順序呈現以文字為主的文章索引
- 首頁、單篇文章、彙整、搜尋、頁面、索引頁及 404 頁面採用一致的響應式閱讀版面
- 適合以文章 ID 設定固定網址，並支援分類、標籤、年份及月份彙整
- 提供所有文章的彙整索引、搜尋，以及分類與標籤的瀏覽索引
- 單篇文章與頁面版型支援 WordPress 原生內容分頁
- 依 WordPress 核心提供留言功能，啟用時支援巢狀回覆
- 以漸進增強方式為程式碼區塊加入視覺行號與「複製」按鈕
- 依系統偏好使用深色模式，並提供列印樣式及具備基本無障礙支援的響應式版面
- 提供簡體中文（`zh_CN`）與繁體中文（`zh_TW`）翻譯
- 依中文語系選用系統字型，不內建字型，也不載入遠端字型
- 不使用建置系統或第三方前端執行階段相依套件

## 系統需求

- WordPress 7.0 或更新版本
- PHP 7.4 或更新版本

Plain Log 已在 WordPress 7.0.x 上測試。使用本佈景主題不需要 Node.js、npm、Composer、外掛或建置步驟。

## 安裝方式

1. 下載發行版本的 ZIP 檔案。
2. 在 WordPress 後台前往 **外觀 → 佈景主題 → 新增 → 上傳佈景主題**。
3. 上傳 `plain-log.zip`。
4. 啟用 Plain Log。

使用 Git 的讀者也可以將儲存庫複製到 `wp-content/themes/plain-log`，再於 WordPress 啟用佈景主題。

## 建議的網站設定

Plain Log 只提供呈現方式與版型；啟用時不會建立頁面或變更 WordPress 設定。

若要使用完整的導覽與內容查找版面，請自行建立下列選用頁面：

| 頁面 | 網址代稱 |
| --- | --- |
| 彙整 | `archive` |
| 搜尋 | `search` |
| 分類 | `categories` |
| 標籤 | `tags` |
| 關於 | `about` |

建議的主選單為**首頁、彙整、搜尋、關於**。只有對應的分類與標籤頁面已發佈時，頁尾才會顯示其連結；RSS 連結使用 WordPress 的文章訂閱摘要。

建議將文章固定網址設為 `/p/%post_id%/`，請自行前往 **設定 → 固定網址** 調整。這只是建議，並非使用本佈景主題的必要條件。Plain Log 啟用時不會變更固定網址、討論或其他網站設定。請透過 WordPress 的討論設定管理留言與引用通知（pingback）。

## 內容與導覽

一般文章包含標題、內容、一個主要分類，以及選用的標籤。關於頁等靜態內容請使用頁面。目前的 Plain Log 設計不包含精選圖片功能。

WordPress `<!--nextpage-->` 支援單篇文章與頁面的內容分頁。此功能沿用 WordPress 核心的多頁內容機制，並非自訂分頁系統。

## 程式碼區塊

程式碼區塊會保留原有空白與縮排；內容過寬時可在區塊內水平捲動。單篇文章包含程式碼時，Plain Log 會以漸進增強方式加入視覺行號與「複製」按鈕。複製的程式碼不含行號。Plain Log 不提供語法高亮。

## 留言

Plain Log 遵循 WordPress 的討論設定，不會擅自變更。留言關閉且文章沒有既有留言時，不顯示留言介面；留言開放時，提供 WordPress 核心的留言列表與表單。若日後關閉留言，既有留言仍會顯示。

巢狀回覆使用 WordPress 核心的 `comment-reply` 指令碼。佈景主題刻意不顯示留言者大頭貼。Plain Log 不加入第三方留言系統，也不自行實作留言送出邏輯。

## 在地化與字型

原始 gettext 訊息 ID 使用英文。Plain Log 隨附：

- 簡體中文（`zh_CN`）
- 臺灣繁體中文（`zh_TW`）

網站前台的中文語系會優先選用裝置已安裝的系統字型。`zh-TW` 與 `zh-Hant` 優先使用 PingFang TC、Noto Sans TC 與 Microsoft JhengHei；`zh-CN` 與 `zh-Hans` 優先使用 PingFang SC、Noto Sans SC 與 Microsoft YaHei；`zh-HK` 優先使用 PingFang HK、Noto Sans HK 及繁體中文系統字型作為備用。實際顯示的字型取決於裝置上已安裝的字型。本佈景主題未隨附 `zh_HK` 翻譯。

Plain Log 不內建字型檔案，也不向 Google Fonts 或其他遠端字型服務發出請求。

## 隱私與相依套件

Plain Log 不加入分析、遙測、廣告、第三方追蹤、遠端字型或外部 CDN 資源。啟用留言時，留言資料由 WordPress 核心依網站的討論與隱私設定處理。

本佈景主題不需要第三方前端執行階段相依套件，也沒有建置系統。

## 已知限制

Plain Log 不提供語法高亮、目錄、精選圖片介面、SEO 引擎、分析功能、佈景主題設定面板、頁面建構器或 AJAX 搜尋。

## 開發

本佈景主題使用 PHP、CSS、`theme.json` 及少量原生 JavaScript，不需要建置系統。歷史上凍結的 V1 規格與專案開發規則分別記錄於 [`SPEC.md`](SPEC.md) 與 [`AGENTS.md`](AGENTS.md)。

## 授權條款

Plain Log 依 [GPL-2.0-or-later](LICENSE) 授權。原作者 wwintj 與其他貢獻者的歷史貢獻保留於 Git 提交紀錄。
