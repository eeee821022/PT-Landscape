# 新增樞紐圖表分析視圖到 PT Landscape

## 目標
在 PT Landscape.html 中新增第三個視圖模式「樞紐分析」，參考 `寵物分析表TEST.html` 的實現邏輯。

## 目前架構
PT Landscape 已有兩個視圖：
- **Landscape Grid** - 以價格為 X 軸，平台/品牌為 Y 軸的產品分佈圖
- **Scatter Chart** - 散點圖分析

## 樞紐分析功能概述（從源檔案提取）

### 核心功能
1. **多層行分組**：支援 1-4 層的巢狀分組（主分組 + 3 層次分組）
2. **動態數據欄位**：可新增多個數據欄位，每個欄位可選擇：
   - 欄位來源
   - 聚合函數（COUNT, UNIQUE, SUM, AVG, MAX, MIN, MEDIAN, STDEV, VAR, X%）
   - 格式/X 值
3. **自動生成樞紐表格**：根據選擇的行和欄生成 HTML 表格
4. **匯出功能**：CSV 匯出、截圖下載

---

## 實現計劃

### Phase 1: 新增視圖切換按鈕

#### [MODIFY] [PT Landscape.html](file:///d:/OneDrive/Python_File/網頁_PT資料庫/PT%20Landscape.html)

在 `viewTabs` (Line ~1032) 新增第三個視圖按鈕：
```html
<button class="view-tab" data-view="pivot">
  <i class="fas fa-table mr-1"></i>樞紐分析
</button>
```

---

### Phase 2: 新增樞紐分析 HTML 區塊

在 Scatter Chart 區塊後新增樞紐分析容器：

```html
<!-- 樞紐分析視圖 -->
<div id="pivotWrapper" style="display: none;">
  <div class="bg-white p-4 rounded-lg shadow-md mb-4">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- 列設定 -->
      <div class="space-y-3">
        <h3 class="text-sm font-semibold text-gray-700 border-b pb-1">列 (Row)</h3>
        <div>
          <label class="block text-xs font-medium text-gray-600">主要分組</label>
          <select id="pivotRowMainSelect" class="mt-1 block w-full py-2 px-3 border rounded text-sm"></select>
        </div>
        <!-- 次要分組 (可選) -->
        <div>
          <label class="block text-xs font-medium text-gray-600">次要分組（可選）</label>
          <select id="pivotRowSubSelect" class="mt-1 block w-full py-2 px-3 border rounded text-sm"></select>
        </div>
      </div>
      
      <!-- 欄設定 -->
      <div class="space-y-3">
        <h3 class="text-sm font-semibold text-gray-700 border-b pb-1">欄 (Column) - 數據欄位</h3>
        <div id="pivotColumnsContainer" class="space-y-2 max-h-64 overflow-y-auto"></div>
        <button id="addPivotColumnBtn" class="w-full py-1.5 px-3 text-sm bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded">
          + 新增數據欄
        </button>
      </div>
    </div>
  </div>
  
  <!-- 樞紐表格顯示區 -->
  <div class="bg-white p-4 rounded-lg shadow-lg overflow-x-auto">
    <div class="flex justify-end mb-2 gap-2">
      <button id="pivotExportCSV" class="text-xs bg-blue-600 text-white px-3 py-1.5 rounded">匯出 CSV</button>
    </div>
    <div id="pivotTableContainer" class="text-sm">
      <p class="text-gray-500">請選擇列和欄以生成樞紐分析表</p>
    </div>
  </div>
</div>
```

---

### Phase 3: 實現 JavaScript 邏輯

新增以下函數：

1. **`initPivotControls()`** - 初始化樞紐分析控制項（填充下拉選單）
2. **`addPivotColumnField()`** - 動態新增數據欄位
3. **`getPivotColumns()`** - 獲取已配置的欄位列表
4. **`updatePivotTable()`** - 生成樞紐表格
5. **`calculateAggregation(data, field, aggFunc)`** - 計算聚合值
6. **`exportPivotToCSV()`** - 匯出 CSV

---

### Phase 4: 整合視圖切換邏輯

修改 `switchView()` 函數以支援 `pivot` 視圖。

---

## 適用於 PT Data 的樞紐分析欄位建議

對於 PT Landscape 專案，最有價值的分析可能是：

| 行分組建議 | 用途 |
|-----------|------|
| Brand | 按品牌分析 |
| Platform | 按平台分析 |
| Price Range | 按價格區間分析 |
| Platform Type | Brander vs Retailer |

| 數據欄位建議 | 聚合函數 | 用途 |
|-------------|---------|------|
| Model # | COUNT | 產品數量 |
| Price | AVG / MIN / MAX | 價格統計 |
| Brand | COUNT UNIQUE | 品牌數量 |

---

## 預估工時

| 階段 | 複雜度 | 預估工具調用 |
|------|-------|-------------|
| Phase 1: 視圖按鈕 | 低 | ~2 |
| Phase 2: HTML 區塊 | 中 | ~3 |
| Phase 3: JS 邏輯 | 高 | ~10 |
| Phase 4: 視圖整合 | 中 | ~3 |
| **總計** | | **~18** |

---

## 風險與考量

1. **效能**：大量資料時樞紐計算可能較慢
2. **欄位適用性**：PT Data 的欄位與寵物分析表不同，需調整預設值
3. **樣式一致性**：需確保樞紐表格的樣式與現有 UI 一致

---

## 請確認
1. 是否同意此實現計劃？

### Phase 5: 恢復自動載入功能

1.  **修改 `initApp`**:
    *   在取得檔案列表後，自動觸發第一個檔案的載入（或點擊 `loadDataBtn`）。
    *   移除「請手動點擊 Load」的狀態等待。

2.  **Debug "按鈕無反應"**:
    *   確保 `setupEventListeners` 在 DOM Ready 後被正確呼叫。
    *   檢查是否有 JS 錯誤導致事件綁定失敗。

