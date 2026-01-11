/**
 * Google Apps Script for PT DATA 平台
 * 
 * 用於提供 PT Landscape.html 網頁應用程式的資料 API
 * 
 * 部署步驟：
 * 1. 開啟 Google Sheets: https://docs.google.com/spreadsheets/d/1rc8Cy1Wih3wI3G5Zi3gYMbMQFsoUyzm1lXBpKgHmJ48/edit
 * 2. 點選「擴充功能」>「Apps Script」
 * 3. 刪除原有程式碼，貼上此檔案內容
 * 4. 點選「部署」>「新增部署」
 * 5. 選擇「網路應用程式」
 * 6. 設定：
 *    - 執行身分：我
 *    - 誰可以存取：任何人
 * 7. 點選「部署」並複製產生的網址
 * 8. 將網址更新到 PT Landscape.html 的 GS_URL (可新增第二個變數 GS_DATA_URL)
 */

// ================================================================================
// 密碼設定
// ================================================================================
const SECRET_KEY = "55759180";
const PASSWORD_HINT = "557XXXXX0";

// 處理 GET 請求
function doGet(e) {
  // 密碼驗證
  if (e.parameter.key !== SECRET_KEY) {
    return ContentService
      .createTextOutput(JSON.stringify({ 
        error: "Unauthorized", 
        hint: PASSWORD_HINT 
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  const action = e.parameter.action;
  
  let result;
  
  switch(action) {
    case 'getSheets':
      result = getSheetNames();
      break;
    case 'getData':
      const sheetName = e.parameter.sheet;
      if (!sheetName) {
        result = { error: 'Missing sheet parameter' };
      } else {
        result = getSheetData(sheetName);
      }
      break;
    default:
      result = { error: 'Invalid action. Use: getSheets or getData' };
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// 取得所有分頁名稱
function getSheetNames() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  return sheets.map(sheet => sheet.getName());
}

// 取得指定分頁的資料
function getSheetData(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    return { error: `Sheet "${sheetName}" not found` };
  }
  
  const data = sheet.getDataRange().getValues();
  
  if (data.length < 2) {
    return [];
  }
  
  // 第一行作為欄位標題
  const headers = data[0];
  
  // 轉換為物件陣列
  const result = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const obj = {};
    
    for (let j = 0; j < headers.length; j++) {
      const header = headers[j];
      if (header) { // 跳過空白標題
        let value = row[j];
        
        // 處理日期格式
        if (value instanceof Date) {
          value = formatDate(value);
        }
        
        obj[header] = value !== undefined && value !== null ? value : '';
      }
    }
    
    result.push(obj);
  }
  
  return result;
}

// 格式化日期為 YYYY-MM-DD
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 測試函數 - 可在 Apps Script 編輯器中直接執行
function testGetSheets() {
  const result = getSheetNames();
  console.log('Sheets:', result);
}

function testGetData() {
  const result = getSheetData('Data_MTS'); // 替換為實際分頁名稱
  console.log('Data count:', result.length);
  if (result.length > 0) {
    console.log('Sample row:', result[0]);
  }
}

// ================================================================================
// POST 處理 - 寫入資料到新分頁
// ================================================================================
// ================================================================================
// POST 處理 - 寫入資料
// ================================================================================
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    
    // 1. 安全性檢查 (比對密碼)
    // 前端 payload 必須包含 { password: "..." }
    if (payload.password !== SECRET_KEY) {
       return ContentService
          .createTextOutput(JSON.stringify({ error: 'Unauthorized: Invalid Password' }))
          .setMimeType(ContentService.MimeType.JSON);
    }
    
    const action = payload.action;
    
    // Action: updateSheet (部分更新 / 覆蓋指定範圍)
    if (action === 'updateSheet') {
      const sheetName = payload.sheetName;
      const data = payload.data; // 2D Array
      
      if (!sheetName || !data) {
        return jsonResponse({ error: 'Missing sheetName or data' });
      }
      
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(sheetName);
      
      if (!sheet) {
        return jsonResponse({ error: `Sheet "${sheetName}" not found` });
      }

      // 參數: startRow (預設 1), startCol (預設 1)
      // 用戶需求: 從第 4 欄 (D欄) 開始覆蓋，保留 ABC 欄
      // 前端應傳入 startCol: 4
      const startRow = payload.startRow || 1; 
      const startCol = payload.startCol || 1;
      
      const numRows = data.length;
      if (numRows === 0) return jsonResponse({ message: "No data to write" });
      const numCols = data[0].length;
      
      // 寫入資料 (不清除整個 Sheet，只覆蓋指定範圍)
      sheet.getRange(startRow, startCol, numRows, numCols).setValues(data);
      
      return jsonResponse({
        status: 'success',
        message: `Updated ${numRows} rows in ${sheetName} starting at R${startRow}C${startCol}`,
        rowsWritten: numRows
      });
    }
    
    return jsonResponse({ error: 'Unknown action: ' + action });
      
  } catch (error) {
    return jsonResponse({ error: error.toString() });
  }
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

