# PT Landscape 工程開發全案規範 (Engineering Specification)
**版本**: v5.0 (Narrative + Rationale)
**目的**: 完整記錄系統架構思路、設計決策與實作細節。本文件不僅說明「做了什麼」，更解釋「為什麼這樣設計」。

---

## 1. 資料管線 (Data Pipeline)

### 1.1 設計思路
**問題**: 系統需整合兩類異質資料──「爬蟲價格表」與「人工規格表」。兩者格式不同、更新頻率不同、且 Key 可能不一致。
**解法**: 採用 **ELT (Extract, Load, Transform)** 架構，在瀏覽器端完成所有轉換，避免依賴後端服務。

### 1.2 資料擷取 (Extraction)
| 來源 | 函式 | API Endpoint | 過濾規則 | Fallback |
|---|---|---|---|---|
| Price Data | `fetchFileList` | `GS_DATA_URL?action=getSheets&key=${getGSApiKey()}` | 包含 "Data" | GitHub API |
| Spec Data | `populateSheetDropdown` | `GS_URL?action=getSheets&key=${getGSApiKey()}` | 包含 "List" | 無 |

**密碼保護機制**:
*   **驗證流程**: 所有 GS API 請求必須附帶 `key` 參數，由 Apps Script 端驗證。
*   **密碼儲存**: 使用者輸入的密碼存於 `localStorage.GS_API_KEY`。
*   **首次訪問**: 顯示密碼輸入 Overlay (含提示 `557XXXXX0`)，輸入正確後才開始載入。
*   **密碼錯誤**: API 回傳 `{error: "Unauthorized", hint: "557XXXXX0"}`。

**相關函式**:
| 函式 | 職責 |
|---|---|
| `getGSApiKey()` | 從 `gsApiKeyCache` 取得密碼 |
| `checkPasswordAndInit()` | 頁面載入時檢查密碼，無則顯示 Overlay |
| `showPasswordOverlay()` | 顯示密碼輸入畫面 |
| `submitPassword()` | 驗證並儲存密碼，啟動 `initApp()` |

**為什麼用 Google Sheets API？**
*   無需自架後端，降低維運成本。
*   業務人員可直接編輯 Sheets，即時生效。

### 1.3 資料轉換 (`mergeData`)
**合併策略**:
*   **Primary Key**: `Model #` (轉小寫，確保大小寫不敏感匹配)。
*   **Base**: 以 Price Data 為主體 (因為它包含即時價格)。
*   **Enrichment**: 用 Key 去 GS Map 撈規格欄位回填。

**Fallback Chain 設計思路**:
*   **問題**: 爬蟲欄位會隨時間演進 (`Blade Diameter` -> `Blade Range`)，舊資料可能缺少新欄位。
*   **解法**: 實作優先級鏈──若 `Blade Range` 為空，依序嘗試 `GS['Blade Diameter']` -> `CSV['Blade Diameter']`。
*   **效果**: 確保歷史資料仍可正確顯示，不影響長期趨勢分析。

**Price Tag Quantization 設計思路**:
*   **問題**: 原始價格 (如 €123.45) 太精細，無法形成有意義的 Grid 欄位。
*   **解法**: 將價格「量化」至最近的 50 單位整數。
*   **公式**:
    ```
    base = floor(price / 100) * 100
    remainder = price % 100
    if remainder <= 25: tag = base
    else if remainder <= 75: tag = base + 50
    else: tag = base + 100
    ```
*   **範例**: €123 -> 100, €145 -> 150, €189 -> 200。
*   **為什麼用 25/75 切點？** 讓每個 Bucket 涵蓋 ±25 的範圍，直覺且平衡。

### 1.4 狀態管理
| 變數 | 型態 | 設計考量 |
|---|---|---|
| `mergedData` | Array | Immutable 原始資料，避免意外污染 |
| `filteredData` | Array | Mutable，所有 View 皆讀取此變數，確保一致性 |
| `filterSelections` | Object | 各篩選器當前勾選的 Set，供 `applyFilters` 使用 |
| `activeConfig` | Object | 當前 Mode Config，決定 UI 渲染細節 |

**為什麼不用 Redux/Vuex？**
*   專案規模小，引入框架反而增加複雜度。
*   透過顯式函式呼叫鏈 (`applyFilters -> renderGrid`) 已足夠清晰。

---

## 2. 模式架構 (Mode Architecture)

### 2.1 設計思路
**問題**: 不同工具機 (MTS/TBS) 有不同的核心規格，若用同一套 Filter/Card，會顯示大量無關欄位。
**解法**: 採用 **Config-Driven** 架構，將 Filter/Spec 定義外部化為 JSON `cardConfigs`。

### 2.2 自動偵測 (`detectMode`)
*   **邏輯**: 掃描檔名，對照 `cardConfigs[].filename_patterns`。
*   **效果**: 使用者無需手動切換模式，載入 `Data_MTS_xxx` 自動套用 MTS Config。

### 2.3 設定檔差異
| Mode | Unique Filters | Unique Specs | 設計理由 |
|---|---|---|---|
| **MTS** | `Bevel`, `Slide`, `Laser` | `Bevel`, `Slide`, `Blade Diameter` | 切斷機核心為角度與滑軌 |
| **TBS** | `Watt`, `RPM` | `Watt`, `RPM`, `Blade Diameter` | 圓鋸機核心為功率與轉速 |
| **Shared** | `Blade Range`, `Soft Start`, `Power Supply`, `Accessories` | | 通用規格 |

### 2.4 擴充指南
**為什麼這樣設計？** 讓擴充成本趨近於零。
1.  在 `cardConfigs` Append 新 JSON 物件。
2.  定義 `id`, `filename_patterns`, `filters`, `specs`。
3.  **無需修改任何核心邏輯** (`setupFilters`, `renderGrid` 自動適配)。

---

## 3. 篩選引擎 (Filtering Engine)

### 3.1 設計思路
**問題**: 篩選器太多，用戶容易選出「空結果」，且不知道哪裡出錯。
**解法**: 實作「雙向連動」與「動態灰階」，引導用戶操作。

### 3.2 UI 元件 (`setupFilters`)
每個 `.filter-group` 包含：
| 元件 | 實作細節 | 設計考量 |
|---|---|---|
| Header Button | 顯示 Label + Count (僅 Platform/Brand) | Count 讓用戶一眼看出多樣性 |
| Search Input | 若 `hasSearch: true` 則注入 | 選項多時 (如 Model) 更好用 |
| [全選]/[清除] | 批次操作按鈕 | 減少重複點擊 |
| Option List | `<input type="checkbox" checked>` 生成 | 預設全選，避免空結果 |

**Option List 細節**:
*   **Sorting**: 預設字母排序；`Price Range` 按數值排序。
*   **Checked-First Ordering**: 每次勾選/取消後，`reorderFilterOptions` 會將已勾選項目排至最上方 (A-Z)，未勾選項目排在下方 (A-Z)。方便用戶快速看到當前選擇。
*   **Empty Handling**: 若資料有空值，首位插入 `(Empty)` 選項。
*   **Accessories**: 簡化為 `with XXXXX` 或 `-` 兩類，降低認知負擔。

### 3.3 雙向連動 (`calculateDependencies`)
**問題**: 用戶勾選 "Bosch" (Child) 但未勾選 "Brander" (Parent) 時，資料會被過濾為空。
**解法**: 建立 `filterDependencies` Map，勾選 Child 時自動勾選 Parent。
**效果**: 防止「無效篩選」，提升用戶體驗。

### 3.4 動態灰階 (`updateFilterOptionsVisibility`)
**問題**: 用戶不知道哪些選項在當前條件下已無效。
**解法**: 每次篩選後，計算剩餘有效選項，無效者設 `disabled`。
**效果**: 引導用戶避開「死路」。

---

## 4. 視圖架構 (View Architecture)

### 4.1 價格網格 (`renderGrid`)

#### 4.1.1 設計思路
**問題**: 如何在二維表格中呈現「通路 × 價格帶 × 品牌」的三維關係？
**解法**: 使用 Platform/Brand 作為 Row，Price Tag 作為 Column，產品卡片填入 Cell。

#### 4.1.2 資料結構
*   `matrix[Platform/Brand][priceTag-index] = item`
*   `expandedColumns = [{price, index}, ...]`

**為什麼需要 `index`？**
*   同一價格帶可能有多個產品 (如同品牌在 €150 有 3 款)。
*   使用 `price-index` 組合作為唯一 Key。

#### 4.1.3 渲染流程
```
1. 掃描 filteredData 取得所有 Price Tag
2. 對每個 Tag 計算 maxDepth (同價位最多產品數)
3. 生成 Header Row:
   - Corner: Platform/Brand 切換按鈕
   - Price Cells: 依 expandedColumns 迴圈
4. 生成 Data Rows:
   - Left Cell: Logo + 文字
   - Data Cells: createProductCard(item)
```

#### 4.1.4 Visual Anchors
**問題**: 欄位太多時，用戶容易迷失座標。
**解法**: 每 50 單位插入紅線與紅色標籤。
*   紅線條件: `col.index === 0 && price % 50 === 0`。
*   紅標籤: `<span class="boundary-label">` 顯示粗體紅字 (如 **150**)。

#### 4.1.5 Double Sticky
**問題**: 捲動時 Header 或 Left Column 會消失，用戶失去座標。
**解法**: 使用 CSS `position: sticky`。
| 元素 | CSS | z-index |
|---|---|---|
| Header | `top: 0` | 20 |
| Left Column | `left: 0` | 10 |
| Corner | `top: 0; left: 0` | 30 (雙鎖定) |

---

### 4.2 散點圖 (`updateScatterChart`)

#### 4.2.1 設計思路
**問題**: 傳統 Linear Scale 會導致熱門價格帶 (如 €200) 點位重疊，無法閱讀。
**解法**: 自幹 **Spread Axis** 演算法──基於密度的非線性座標軸。

#### 4.2.2 Spread Axis 演算法
```
Step 1: Binning
  - interval = chartSettings.tickInterval (預設 50)
  - 價格 >= 900 後改用 highInterval = 500 (避免高價區過於稀疏)
  - 每個 Bin: {startPrice, endPrice, data[], width}

Step 2: Width Calculation
  - width = max(6, bin.data.length)
  - 資料越多，Bin 越寬，點位不重疊
  - 最小 6 單位，避免標籤擠壓

Step 3: Visual X Assignment
  - bin.startX = sum of previous widths
  - 資料點在 Bin 內線性分佈:
    displayX = startX + 0.5 + (i * (width-1) / (count-1))
  - 若只有一點，置中

Step 4: Tick Map
  - tickMap[visualX] = price
  - 用於繪製刻度與格線
```

#### 4.2.3 互動控制
| 控制項 | Element ID | 選項 | 效果 |
|---|---|---|---|
| Y-Axis | `#scatterYAxis` | Brand/Platform/Type | 決定縱軸分類 |
| Color By | `#scatterColorBy` | Brand/Platform/Type/Model | 決定點位顏色 |
| Tooltip | - | - | Hover 顯示 Model, Price, Y-Value |
| Click | - | - | 呼叫 `showDetailPanel(item)` |

#### 4.2.4 參數設定 (Settings)
位於 Settings Modal > Scatter Chart 區塊：

| 參數 | 範圍 | 預設 | 作用 |
|---|---|---|---|
| **Row Height** | 30~60px | 30px | 控制 Y 軸每種類別的垂直高度間距，類別多時可調大避免擠壓。 |
| **Min Height** | 100~800px | 200px | 強制設定 Chart 容器最小高度，避免類別過少時圖表太扁。 |
| **Point Size** | 2~20px | 6px | 資料點半徑，資料密集時可調小。 |
| **Y-Axis Font** | 10~18px | 12px | Y 軸標籤文字大小 (Default + 50%)，提升可讀性。 |

**Implementation Note**:
*   上述設定變更時，需觸發 `updateScatterChart()` 重繪 Canvas。
*   `Min Height` 與 `Row Height * Categories` 取最大值決定最終高度。

---

### 4.3 矩陣熱圖 (`updatePivotTable`)

#### 4.3.1 設計思路
**問題**: 需要快速看出「哪個品牌在哪個規格區間最強？」
**解法**: 交叉列表 + 熱力圖色階。

#### 4.3.2 Cross-Tabulation
*   `matrix[rowValue][colValue] = count`
*   `rowTotals`, `colTotals`, `grandTotal`

#### 4.3.3 Heatmap Normalization
**問題**: 若用全局 Max 計算色階，大品牌的所有格子都會是深色，小品牌全是淺色，無法看出相對強弱。
**解法**: 採用 **Row-based Normalization**，讓每個品牌的「主力區間」都能呈現深色。

```
rowMax = max(matrix[row][*])
rowMin = min(matrix[row][*])
ratio = (count - rowMin) / (rowMax - rowMin)
alpha = 0.1 + 0.8 * ratio
color = rgba(16, 185, 129, alpha)  // Emerald Green
textColor = alpha > 0.5 ? white : black
```

#### 4.3.4 互動控制
| 控制項 | 效果 |
|---|---|
| Row Select | 決定列變數 (如 Brand) |
| Col Select | 決定欄變數 (如 Blade Range) |
| Swap Button | 交換 Row/Col |

---

## 5. 產品卡片 (`createProductCard`)

### 5.1 設計思路
**問題**: 如何在有限空間內呈現產品的關鍵資訊？
**解法**: 分層結構，從上到下重要性遞減。

### 5.2 HTML 結構
```html
<div class="product-card">
  <div class="card-image">      <!-- 圖片或 placeholder -->
  <div class="card-body">
    <div class="card-brand">    <!-- Logo 或文字 -->
    <div class="card-model">    <!-- Model # (+N if grouped) -->
    <div class="card-specs">    <!-- Spec Icons from config.specs -->
    <div class="card-total">    <!-- Multi-line Total -->
    <div class="card-accessories"> <!-- 配件 -->
    <div class="card-price">    <!-- €XXX.XX -->
  </div>
</div>
```

### 5.3 細節處理
*   **Image Error**: `onerror="this.style.display='none'"` 隱藏裂圖，保持介面整潔。
*   **Grouped Model**: 若同價位有多個產品，顯示 `Model +N`。
*   **Click**: 呼叫 `showDetailPanel(item)` 展開詳細資訊。

---

## 6. 詳細面板 (`showDetailPanel`)

### 6.1 設計思路
**問題**: 卡片資訊有限，用戶需要看更多細節。
**解法**: 側拉 Panel，分 Tab 呈現不同類型資訊。

### 6.2 Tabs
| Tab | 內容 | 資料來源 |
|---|---|---|
| Info | 圖片、Model、Brand、Type、Specs、Price、Platform | `item` + `activeConfig.specs` |
| Desc | 預留 (目前無資料) | - |
| Chart | 價格走勢圖 | `item.History` via Chart.js |

### 6.3 External Link
*   若 `item['Product URL']` 存在，底部顯示藍色按鈕連結至外部網頁。
*   讓用戶可直接跳轉至電商購買。

---

## 7. PDF 匯出 (`exportToPdf`)

### 7.1 設計思路
**問題**: 瀏覽器無法直接列印 Scrollable Area，且 CSS 截圖常出現黑背景。
**解法**: Off-Screen Rendering + Style Injection + Virtual Slicing。

### 7.2 Modes
| Mode | 說明 | 適用情境 |
|---|---|---|
| Single | 整張 Grid 輸出為單頁 PDF | 窄表、資料量少 |
| Split | 依 `Rows per Page` 切割，每頁補 Header | 長表、資料量多 |

### 7.3 Off-Screen Rendering
1.  Clone `#gridWrapper` 到 `left: -99999px` 的離屏容器。
2.  強制 `overflow: visible` 展開所有隱藏內容。
3.  設定 `width = scrollWidth` 確保完整寬度。

### 7.4 Style Injection (`forceStyle`)
*   (同前)

### 7.5 CSV 匯出 (`downloadCsvContext`)
*   **目的**: 讓用戶將當前篩選過後的資料 (`filteredData`) 下載為標準 CSV，以利外部工具 (Excel, Python) 分析。
*   **格式**: 包含 BOM (`\uFEFF`)，確保 Excel 開啟時中文不亂碼。
*   **處理**: 自動對欄位值進行 Quote 處理 (`"value"`) 並 Escape 內部的雙引號。

**問題**: `html2canvas` 常忽略外部 CSS，導致背景變黑。
**解法**: 遞迴遍歷 DOM，強制注入 `background-color: #ffffff !important`。
**特例**: 保留 `.boundary-label` 的紅色文字。

### 7.5 Virtual Slicing
```
1. 計算 A4 高度 (約 1123px @96dpi)
2. 將 cloneDataRows 分組，每組 N 行
3. 每組上方手動插入 Header Clone
4. 確保每頁表格都是完整的 (有標題列)
```

### 7.6 Copy for AI Context
**目標**: 將當前篩選後的資料結構化匯出，便於直接貼入 LLM (如 Gemini) 進行對話分析。

**Implementation**:
*   **Format**: CSV (精簡版)，僅包含關鍵欄位 (Model, Brand, Price, Spec, etc.) 以節省 Token。
*   **Prompt Wrapper**: 自動加上 `[Context: ...]` 和 `[Instruction]` 標籤。
*   **Source**: 直接讀取 `filteredData`，所見即所得。
*   **Clipboard**: 使用 `navigator.clipboard.writeText()`。

---

## 8. 輔助功能

### 8.1 統計列 (`updateStats`)
顯示當前 `filteredData` 的：
*   **Models**: 總筆數。
*   **Brands**: Unique Brand 數。
*   **Platforms**: Unique Platform 數。

### 8.2 縮放控制
| Scope | Variable | Controls | Effect |
|---|---|---|---|
| Grid | `zoomLevel` | `#zoomIn`, `#zoomOut` | `transform: scale()` on `#gridScrollArea` |
| Scatter | `scatterZoomLevel` | `#scatterZoomIn`, `#scatterZoomOut` | Canvas 重繪 |
| Matrix | `matrixZoomLevel` | `#matrixZoomIn`, `#matrixZoomOut` | `transform: scale()` on `#pivotWrapper` |

**為什麼三者獨立？** 不同視圖有不同閱讀需求，應各自調整。

### 8.3 Loading Overlay (`showLoading`)
**目標**: 恢復原版簡潔風格，同時提供明確的進度反饋與功能教學。

**Design**:
*   **Style**: 保留原版白色背景 (`bg-white/95`) 與藍色光暈，使用原版 Aperture SVG Icon。
*   **Visibility**: `z-index: 50` (低於 Header 的 100)，確保載入時 Header 保持可見且可操作。
*   **Toggle**: 使用 CSS `display: flex/none` 切換，不進行 DOM 動態刪除。

**Animated Progress Bar**:
*   **Feature**: 實作平滑動畫 (`requestAnimationFrame`)，數字從 0 遞增到 100，避免進度跳躍。
*   **Logic**:
    *   **10%**: 開始載入。
    *   **70%**: 價格資料 (GS Data) 載入完成。
    *   **80%**: 規格資料 (MTS List) 載入完成，開始合併。
    *   **80-95%**: **Real-time Merge Progress** (每處理 50 行資料更新一次)。
    *   **99%**: 篩選器套用完成。
    *   **100%**: 完成 (停留 0.5 秒後自動關閉)。

**Categorized Tips**:
*   **Content**: `LOADING_TIPS` 陣列包含 15+ 條技巧，分為與 **Views/Modes**, **Interaction**, **Filters**, **Features** 四大類。
*   **Display**: 每次載入隨機顯示一條，幫助用戶發現進階功能 (如 Matrix 視圖、OnlyOne 模式等)。

---

## 9. 系統架構總覽

### 9.1 模組依賴關係
```
┌─────────────────────────────────────────────────────────┐
│                    User Interaction                      │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│              Event Listeners (setupEventListeners)       │
│   View Tabs │ Filter Dropdowns │ Mode Buttons │ Zoom     │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴───────┬───────────────┐
       ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ switchView │  │ applyFilters│  │ switchMode │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │
      └───────┬───────┴───────────────┘
              ▼
┌─────────────────────────────────────────────────────────┐
│                 Render Layer                             │
│   renderGrid │ updateScatterChart │ updatePivotTable    │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                 Data Layer (filteredData)                │
└─────────────────────────────────────────────────────────┘
```

### 9.2 資料流 (Data Flow)
```
reloadData()
    │
    ├──► fetchFileList() / loadCSV()   ──► csvData
    ├──► fetchGSData()                 ──► gsData
    │
    └──► mergeData(csv, gs)
              │
              ▼
         mergedData
              │
              ▼
         setupFilters()  ──► filterSelections{}
              │
              ▼
         applyFilters()  ──► filteredData
              │
              ▼
         renderGrid() / updateScatterChart() / updatePivotTable()
```

### 9.3 核心函式職責
| 模組 | 核心函式 | 職責 |
|------|----------|------|
| **Init** | `initApp`, `reloadData` | 系統初始化、資料載入流程控制 |
| **Data** | `mergeData`, `calculateDependencies` | 資料合併、欄位依賴關係計算 |
| **Filter** | `setupFilters`, `applyFilters`, `updateFilterOptionsVisibility` | 篩選器 UI 生成、邏輯套用、有效性檢查 |
| **View** | `renderGrid`, `updateScatterChart`, `updatePivotTable` | 三大視圖渲染 |
| **Card** | `createProductCard`, `showDetailPanel` | 產品卡片生成、詳細資訊面板 |
| **Export** | `exportToPdf`, `downloadCsvContext` | PDF 匯出、CSV 資料匯出 |
| **Config** | `cardConfigs`, `detectMode`, `setActiveMode` | 模式設定、自動偵測 |

---

## 10. Gemini AI Integration (Client-Side REST API)

### 10.1 Architecture
*   **Zero-Server**: Directly calls Google Gemini REST API (`v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent`).
*   **Key Storage**: `localStorage` ('gemini_api_key').
*   **Markdown**: Responses rendered via `marked.js`.

### 10.2 Chat UI
| Component | Function |
|:---|:---|
| **Floating Button** (`#chatFab`) | Bottom-Right Fixed Button (Purple Gradient) to toggle Chat Panel. |
| **Chat Panel** (`#chatPanel`) | Fixed Panel (380x500px), resizable to Fullscreen. |
| **Header** | Gradient Background. Contains: **Download Icon** (TXT), **Fullscreen Toggle**, **Close**. |
| **API Key Bar** | Row containing: Key Icon, **Input** (Password), **Eye Toggle**, **Save** Button, **Clear** Button. |
| **Context Toggles** | Grid of 3 Buttons: **數據資料** (Top 400), **操作詢問** (Source), **記錄對話** (History). |
| **Controls** | **Mic Icon** (Voice Input, hidden in simplifications but supported in logic), **Send Button**. |

### 10.3 Context Logic
The application intelligently packages context to minimize tokens while maximizing utility.

1.  **Data Context (`btnContextData`)**:
    *   **Logic**: Filters `filteredData` to Top **400** rows.
    *   **Fields**: `Platform`, `Brand`, `Model #` (mapped to Model), `Price`.
    *   **Header**: `[DATA CONTEXT (Current View, Top 400)]`.
2.  **Manual Context (`btnContextManual`)**:
    *   **Logic**: Extracts `document.body.innerHTML`, strips `<script>` and `<svg>`, truncated to 15k chars.
    *   **Header**: `[OPERATION MANUAL CONTEXT (Source Code Fragment)]`.
3.  **History Context (`btnContextHistory`)**:
    *   **Logic**: Appends recent chat logs (limit 8000 chars), preserving `USER` / `AI` roles.
    *   **Header**: `[CONVERSATION HISTORY]`.

### 10.4 Chat History Download
*   **Trigger**: Click **Download Icon** (`fa-download`) in Header.
*   **Format**: `.txt` (Text/Plain).
*   **Content**:
    ```text
    AI Chat History
    =================
    [USER]
    Message...
    [AI]
    Message...
    ```
*   **Filename**: `AI_Chat_YYYYMMDD_HHMM.txt`.

### 10.5 Voice Input (Standard API)
*   **Web Speech API**: 使用 `webkitSpeechRecognition`。
*   **Language**: `zh-TW`。
*   **Trigger**: Mic Icon in Input Area.

### 10.6 History Management
*   **Save Logic**: 點擊 Header 下載 Icon -> Client-side generate `.txt` file (Text/Plain)。
    *   Format: `[ROLE] Message...`
*   **Clear Logic**: 按下 Clear 按鈕 -> 清空 `#chatMessages` 並重置對話記憶。
*   **Visual Feedback**: 錄音中按鈕呈紅色跳動 (`fa-beat`)。

### 10.6 Message Flow
```
1. User 輸入問題，按 Enter 或點擊 Send
2. sendChatMessage() 取得 text
3. getCombinedContext() 依 activeContexts 組合 Data/Manual/History
4. 若有 Context，組成 finalPrompt = context + "\n\n[USER QUESTION]: " + text
5. callGeminiAPI(finalPrompt, systemInstruction)
6. 收到回覆後，使用 marked.parse() 渲染 Markdown
7. appendMessage('model', formatted)
```

### 10.7 Error Handling
*   **Retry**: `callGeminiAPI` 內建 3 次指數退避重試 (1s, 2s, 4s)。
*   **Display**: 失敗時在 Messages Area 顯示紅色錯誤訊息。

### 10.8 Tips Button & Loading Screen
*   **Tips Button**: 位於 Header Data Mode 旁，點擊呼叫 `openTipsModal()`，開啟彈出視窗顯示所有功能技巧列表。
*   **Loading Screen**: 顯示隨機 Tips (`showLoading`)，已優化隨機演算法，避免連續出現相同 Tip。


