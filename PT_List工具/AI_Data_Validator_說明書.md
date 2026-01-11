# AI Data Validator 使用說明書

> **版本:** v4.0 | 5-Round Voting with URL-based Validation  
> **最後更新:** 2026-01-11

---

## 📋 目錄

1. [系統架構](#系統架構)
2. [部署流程](#部署流程)
3. [核心功能](#核心功能)
4. [驗證流程](#驗證流程)
5. [投票機制](#投票機制)
6. [Prompt 設定](#prompt-設定)
7. [使用步驟](#使用步驟)
8. [常見問題](#常見問題)

---

## 系統架構

### Gemini Canvas 架構

> ⚠️ **重要概念:** 本系統使用 **Gemini Canvas** 作為 API 橋接層

```
┌─────────────────────────────────────────────────────────────┐
│                     Gemini Canvas                            │
│              (Gem: AI_Data_Validator_Web2)                  │
│                                                              │
│   ┌───────────────────┐    ┌────────────────────────┐       │
│   │   主程式 HTML     │    │    Prompt JS 檔案      │       │
│   │   (直接上傳)      │    │    (從 GitHub 抓取)    │       │
│   │                   │    │                        │       │
│   │ AI_Data_Validator │    │ miterSaw_Prompt.js    │       │
│   │ _Web - Gemini版   │    │ tableSaw_Prompt.js    │       │
│   └───────────────────┘    └────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                       Gemini AI API
```

### 檔案部署方式

| 檔案類型 | 儲存位置 | 部署方式 |
|---------|---------|---------|
| **主程式 HTML** | 本地 | 手動上傳到 Gemini Canvas |
| **Prompt JS 檔案** | GitHub Pages | 程式自動從 GitHub 抓取 |
| **PT DATA** | Google Sheets | 透過 GAS API 讀取 |

### Prompt GitHub URL

```
https://eeee821022.github.io/PT-Landscape/PT_List工具/miterSaw_Prompt.js
https://eeee821022.github.io/PT-Landscape/PT_List工具/tableSaw_Prompt.js
```

---

## 部署流程

### 更新 Prompt 時

```bash
# 1. 編輯本地 Prompt 檔案
# 2. Push 到 GitHub
git add "PT_List工具/miterSaw_Prompt.js" "PT_List工具/tableSaw_Prompt.js"
git commit -m "Update prompts"
git push

# 3. 等待 GitHub Pages 更新 (1-2 分鐘)
# 4. Gemini Canvas 會自動抓取新 Prompt
```

### 更新主程式時

1. 編輯本地 `AI_Data_Validator_Web - Gemini版.html`
2. 開啟 Gemini Canvas 的 Gem
3. 重新上傳 HTML 檔案

> ⚠️ **注意:** 主程式 HTML 不需要上傳到 GitHub

---

## 核心功能

### ✅ 雙模式驗證系統 (v4.0)

| 機型類型 | 輪數 | 說明 |
|---------|------|------|
| **現有機型** (在 PT DATA 中) | 5 輪 | URL-based + Google Search |
| **新增機型** (不在 PT DATA 中) | 4 輪 | Google Search + Model Knowledge |

### ✅ 5-Round URL-based 驗證 (現有機型)

| Round | 模式 | URL 選擇 |
|-------|------|----------|
| R1 | `[URL:min]` | 最低價 Product URL |
| R2 | `[URL:max]` | 最高價 Product URL |
| R3 | `[URL:q3]` | Q3 (75%) 價格 URL |
| R4 | `[URL:q2]` | Q2 (50%) 價格 URL |
| R5 | `[Google]` | Google Search 驗證 |

### ✅ URL 不足時的 Fallback 規則

| URL 數量 | 配置 |
|---------|------|
| 4 URLs | URL×4 + Search×1 |
| 3 URLs | URL×3 + Search×2 |
| 2 URLs | URL×2 + Search×2 + Knowledge×1 |
| 1 URL | URL×1 + Search×2 + Knowledge×2 |

### ✅ 4-Round 驗證 (新增機型)

---

## 核心功能

### ✅ 4 輪平行驗證

| Round | 模式 | 說明 |
|-------|------|------|
| R1 | `[Google]` | 使用 Google Search 驗證規格 |
| R2 | `[Google]` | 使用 Google Search 驗證規格 |
| R3 | `[Model]` | 使用 AI 內建知識驗證 |
| R4 | `[Model]` | 使用 AI 內建知識驗證 |

### ✅ 投票機制

- **原始值:** 2 票
- **R1-R4 各:** 1 票
- **空值/無效值:** 0 票
- **最高票者勝**

### ✅ Lock Cols (鎖定欄位)

指定不讓 AI 修改的欄位（預設: A, B, D, T）

### ✅ Log 記錄

每輪 API 呼叫都會獨立記錄，可下載 Prompt 和 AI 回覆

---

## 驗證流程

```
┌─────────────────────────────────────────────────────────────┐
│                     載入 Google Sheet                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   依品牌分組 + 分批處理                       │
│                  (每批 CHUNK_SIZE = 10)                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   同時發送 4 個 API 請求                      │
│   ┌─────────┬─────────┬─────────┬─────────┐                 │
│   │   R1    │   R2    │   R3    │   R4    │                 │
│   │ Google  │ Google  │ Model   │ Model   │                 │
│   └─────────┴─────────┴─────────┴─────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   逐欄位投票合併結果                          │
│         (原始=2票, R1-R4各=1票, 最高票者勝)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     輸出最終結果                             │
│              (標記 Corrected / Confirmed)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 投票機制

### 情境範例

#### 情境 1: 原始欄位有值

```
欄位: Watt
原始: "1800W" → 2 票
R1:   "1400W" → 1 票
R2:   "1800W" → 1 票
R3:   "1800W" → 1 票  
R4:   "1400W" → 1 票

結果: "1800W" (4 票) > "1400W" (2 票)
```

#### 情境 2: 原始欄位為空

```
欄位: Type
原始: ""       → 0 票
R1:   "Miter"  → 1 票
R2:   "Miter"  → 1 票
R3:   "Floor"  → 1 票
R4:   "Miter"  → 1 票

結果: "Miter" (3 票) → 採用 (≥2 票共識)
```

#### 情境 3: 沒有共識

```
欄位: Released Year
原始: ""     → 0 票
R1:   "2022" → 1 票
R2:   "2023" → 1 票
R3:   "2021" → 1 票
R4:   ""     → 0 票

結果: 沒有 ≥2 票的選項 → 留空
```

---

## Prompt 設定

### 檔案位置

`miterSaw_Prompt.js`

### 兩種 Prompt 模板

| 模板 | 用於 | 關鍵指令 |
|------|------|---------|
| `systemPromptTemplate` | R1, R2 (Google) | "USE Google Search to verify" |
| `systemPromptTemplateNoSearch` | R3, R4 (Model) | "Use your built-in knowledge" |

### Google Search Prompt 特點

- 積極驗證和修正資料
- 可以新增市場上的新產品
- 使用搜尋結果作為依據

### Model-only Prompt 特點

- 保守策略: 不確定就留空
- 不新增新產品
- 只用 AI 訓練資料中的知識

---

## 使用步驟

### 1️⃣ 設定連線

1. 輸入 **Gemini API Key**
2. 輸入 **GAS Script URL**
3. 點擊 **CONN** 連線

### 2️⃣ 選擇資料

1. 選擇 **Region** (USA, DEU, TW, JP)
2. 選擇 **Sheet** (資料表)
3. 資料會自動載入並顯示

### 3️⃣ 設定參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| Model | 選擇 AI 模型 | gemini-2.5-flash-preview |
| Lock Cols | 鎖定不修改的欄位 | A,B,D,T |
| Prompt | 選擇 Prompt 設定檔 | Miter Saw Validator |

### 4️⃣ 執行驗證

1. 點擊 **START AUDIT**
2. 觀察進度: `[1/30] Bosch - Sending 4 API calls...`
3. 等待完成

### 5️⃣ 輸出結果

- **Copy Data**: 複製到剪貼簿
- **Download CSV**: 下載 CSV 檔案
- **Download Log**: 下載 Prompt/Reply Log

---

## 常見問題

### Q: 為什麼要用 4 輪而不是 3 輪?

**A:** 4 輪 = 2 (Google Search) + 2 (Model Knowledge)

- Google Search 可以找到最新資料，但可能不穩定
- Model Knowledge 穩定但可能過時
- 混合使用可以互相校驗

### Q: 投票時原始值為什麼算 2 票?

**A:** 原始資料通常是人工輸入或之前驗證過的，給予較高權重。這樣 AI 必須有 3/4 的共識才能覆蓋原始值。

### Q: Lock Cols 要鎖哪些欄位?

**A:** 建議鎖定:
- A (Brand Logo) - 圖片欄位
- B (Image) - 圖片欄位  
- D (Image URL) - 原始圖片連結
- T (Total) - 計算欄位

### Q: API 錯誤 401 怎麼辦?

**A:** API Key 無效或未設定。請確認:
1. API Key 已正確輸入
2. API Key 有 Gemini API 權限
3. 未超過配額限制

### Q: 結果欄位是空的怎麼辦?

**A:** 可能原因:
1. 4 輪結果都不同，沒有共識
2. AI 無法從搜尋/知識中確認該值
3. 這是正常行為 — "寧願空白也不亂填"

---

## 版本歷史

| 版本 | 日期 | 更新內容 |
|------|------|---------|
| v4.0 | 2026-01-11 | 5-Round URL-based 驗證, Gemini Canvas 架構文檔, Trust Ranking, Batch-per-Round 優化 |
| v3.5 | 2024-12-21 | 4-Round 混合驗證, A/B Prompt |
| v3.4 | 2024-12-21 | Auto-Retry Fix, 投票機制 |
| v3.3 | 2024-12-20 | Google Search Grounding |

---

*Generated by AI Data Validator Documentation*
