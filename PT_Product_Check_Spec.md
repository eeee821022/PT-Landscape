# PT Product Check 工程開發規範 (Engineering Specification)
**版本**: v1.3
**目的**: 記錄 PT Product Check (Gemini Search Auditor) 的系統架構與實作細節。

---

## 1. 系統概述

### 1.1 功能簡介
PT Product Check 是一個使用 **Gemini AI + Google Search** 自動化檢查產品配件資訊的網頁工具。

**核心功能**:
| 功能 | 說明 |
|---|---|
| 自動連線 GS | 從 PT DATA 平台載入產品資料 |
| AI 配件檢查 | 使用 Gemini 造訪產品頁面，擷取配件資訊 |
| **品牌/機型驗證** | 自動比對 Check 分頁標準清單，支援模糊匹配與修正 |
| **平行處理** | 支援 **4 批次** 平行處理 (Concurrency) |
| **自動重試** | 失敗批次自動重試機制 (最多 5 輪) |
| 資料匯出 | 支援複製 TSV 與下載 CSV (基於 Index 對應確保完整性) |

---

## 2. 品牌/機型驗證機制 (v1.3 更新)

### 2.1 設計原則
| 原則 | 說明 |
|---|---|
| 只填空白 | AI 回傳的 Brand/Model 只在原欄位為空時回填 |
| Index 對應 | AI 結果依原始行號 (Index) 對應，無需依賴 Model # |
| 模糊匹配 | 支援後綴包含 (e.g., "M18 FMS305 Set" -> "M18 FMS305") |
| **強制 Mismatch** | 若 AI 修正了 Model #，系統強制將 Audit Status 改為 "Mismatch" |

### 2.2 驗證流程 (ValidateAndMerge)
1. **正規化 (Normalization)**: 去除空白與連字號，轉小寫。
2. **Brand 驗證**:
   - Exact Match
   - Fuzzy Match (Contains)
3. **Model # 驗證**:
   - Exact Match
   - Normalized Match (e.g. `gcm 18v-216` == `GCM18V216`)
   - **Fuzzy Match (Includes)**: 檢查 AI 值是否包含 Check 值 (e.g. `M18 Set` includes `M18`)
   - 修正: 若有匹配但字串不完全一致，自動修正為 Check 表標準值。
4. **強制 Mismatch 邏輯 (v1.3)**:
   - 若 AI 回傳的 Model # 與原始輸入不同 (正規化後比對)，即使 AI 回報 "OK"，系統也會強制將 Audit Status 改為 "Mismatch"。
   - Audit Reason 會更新為: `Input mismatch '原始輸入' vs found 'AI結果'`。

### 2.3 UI 標記 (v1.3 更新)
| 標記 | 樣式 | 說明 |
|---|---|---|
| `_brandFilled` / `_modelFilled` / `_accFilled` | **綠字 + 淺綠底** | 原本空白，由 AI 補上 |
| `_brandInvalid` / `_modelInvalid` | **紅字 + 淺紅底** | 無效/不在 Check 表內 |
| `_brandCorrected` / `_modelCorrected` | 無特殊樣式 | 僅為大小寫修正，不需警示 |

---

## 3. 處理架構 (Parallel Audit Loop)

### 3.1 批次與重試
```javascript
const PARALLEL_BATCHES = 4; // 同時發送 4 個請求
const CHUNK_SIZE = 10;      // 每批 10 筆資料 (固定)
const CHECK_SHEET_MAX_RETRIES = 5; // 失敗批次最多重試 5 輪 (Loop)
```

**流程**:
1. 將資料切分成每批 10 筆 (CHUNK_SIZE)。
2. **第一輪**: 平行處理所有批次。
3. **重試輪 (While Loop)**:
   - 收集所有狀態為 `failed` 或 `pending` 的批次。
   - 再次平行處理。
   - 直到所有成功或達到最大重試次數。

### 3.2 資料合併與匯出
- **嚴格 Index 對應**: 
  - 由於原始資料可能有相同的 Model # 或空的 Model #，不能依賴 Model # 作為 Key。
  - 系統在開始 Audit 時為每行注入 `_originalIndex`。
  - 完成後，依據 `_originalIndex` 將修正後的資料寫回主 `rawRows` 狀態。
- **匯出**: 
  - Copy/Download 功能直接讀取主 `rawRows`，確保匯出的資料與螢幕上看到的完全一致 (包括原本缺漏但被 AI 補上的行)。

---

## 4. AI Prompt 策略 (v1.3) - 外部 JS 檔案

### 4.1 Prompt 來源優先順序
| 優先順序 | 來源 | 說明 |
|---|---|---|
| 1 | **GitHub Raw** | `https://raw.githubusercontent.com/.../productCheck_Prompt.js` |
| 2 | Google Sheet | `Prompt` 分頁的 `Content` 欄位 |
| 3 | Local File | `productCheck_Prompt.js` (本地備案) |
| 4 | Hardcoded | 程式碼內建最小化 Fallback |

### 4.2 Prompt 檔案格式
檔案路徑: `PT_DATA工具/productCheck_Prompt.js`
```javascript
var PRODUCT_CHECK_PROMPT = \`*** SYSTEM COMMAND: PRODUCT ACCESSORY CHECKER ***
...
\`;
```

### 4.3 核心規則
- **Model Extraction**: 明確指示提取核心型號，忽略 "Set", "Plus", "Bundle", "Set-MFT", "UG-Set" 等銷售後綴。
- **Output Schema**: 強制 JSON Array 格式，必須與輸入數量 1:1 對應。
- **Accessories**: 僅分類為 Blade, Stand, Battery, Bundle。
- **Mismatch 判定**: 若頁面上的 Model 與輸入不符，必須回傳 "Mismatch" 狀態並填入正確的 Model。

---

## 5. 更新記錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1.0 | 2026-01-10 | 初版，新增 GS API 密碼保護 |
| v1.1 | 2026-01-11 | 新增品牌/機型驗證機制 |
| v1.2 | 2026-01-11 | 新增平行處理、重試機制、Index 對應匯出修復、模糊匹配 Model 邏輯 |
| v1.3 | 2026-01-11 | **Prompt 外部化** (GitHub JS)、**強制 Mismatch 邏輯**、**UI 標記優化** (綠色填補/紅色無效) |
