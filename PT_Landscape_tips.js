
// PT Landscape Tips Configuration
// User-friendly tips for floating loading screen and Help modal.

window.TIPS_CONFIG = [
    // --- 資料讀取 (Data Loading) ---
    {
        "category": "資料讀取",
        "color": "bg-gray-500",
        "text": "篩選左側箭頭可以收折/展開上面檔案讀取相關區塊，讓畫面更寬敞，專注於數據分析。"
    },
    {
        "category": "資料讀取",
        "color": "bg-gray-500",
        "text": "發現資料沒更新？按住 Ctrl+F5 強制重新整理，確保您看到的是最新數據。"
    },

    // --- 篩選 (Filtering) ---
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "篩選設定完成後，網址會自動記錄當前狀態。您可以直接複製網址儲存這次的篩選設定，下次打開即恢復原狀。"
    },
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "想要找特定品牌？直接勾選 Brand (例如 Bosch)，系統會自動勾選所有相關平台，一次顯示該品牌所有產品。"
    },
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "想要跨品牌比較？勾選 Bosch 後再手動勾選 Atika (Platform)，兩者的產品會同時顯示 (聯集模式)。"
    },
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "篩選條件太亂了？按一下「清除」按鈕，馬上還您一個乾淨的畫面。"
    },
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "只關心特定預算？在 Price Range 輸入您的預算範圍，超出範圍的產品會自動隱藏。"
    },
    {
        "category": "篩選",
        "color": "bg-blue-500",
        "text": "找不到特定型號？在 Model # 欄位輸入關鍵字，立刻就能搜出來。"
    },

    // --- 通用顯示 (General Display) ---
    {
        "category": "通用顯示",
        "color": "bg-green-500",
        "text": "圖表太小看不清？使用上方的「Zoom」按鈕，可以自由放大縮小所有圖表。"
    },
    {
        "category": "通用顯示",
        "color": "bg-green-500",
        "text": "需要報告素材？點擊 PDF Export，將當前的精美圖表直接匯出成文件。"
    },
    {
        "category": "通用顯示",
        "color": "bg-green-500",
        "text": "發現有趣的數據？目前的篩選狀態會自動同步到網址，與同事分享連結，他們就能看到一模一樣的畫面！"
    },

    // --- 地圖顯示 (Landscape) ---
    {
        "category": "地圖顯示",
        "color": "bg-emerald-500",
        "text": "在 Landscape 模式上方，您可以勾選 Spec、Features 或 Logo 顯示選項，自由控制產品卡片要呈現的詳細程度。"
    },
    {
        "category": "地圖顯示",
        "color": "bg-emerald-500",
        "text": "想看最便宜的產品？切換到「Lowest」模式，系統會自動在每個價格帶中只保留最低價代表。"
    },
    {
        "category": "地圖顯示",
        "color": "bg-emerald-500",
        "text": "想知道細節？點擊任何一張產品卡片，可以看到完整的規格表和歷史價格走勢。"
    },
    {
        "category": "地圖顯示",
        "color": "bg-emerald-500",
        "text": "表格裡的紅色直線是什麼？那是每 €50 的分隔線，幫您快速判斷產品的價格定位。"
    },

    // --- 散佈圖顯示 (Scatter) ---
    {
        "category": "散佈圖顯示",
        "color": "bg-orange-500",
        "text": "切換至 Scatter 模式，可以觀察價格與規格(如轉速、功率)的分布關係，快速找出高規低價的 CP 值產品。"
    },
    {
        "category": "散佈圖顯示",
        "color": "bg-orange-500",
        "text": "想知道哪些產品評論最多？使用「Size」下拉選單選擇「Comments」，評論越多的產品點越大！"
    },
    {
        "category": "散佈圖顯示",
        "color": "bg-orange-500",
        "text": "想找高評分產品？「Size」選「Score」，★5 的產品會顯示成最大的點，方便一眼辨識。"
    },
    {
        "category": "散佈圖顯示",
        "color": "bg-orange-500",
        "text": "想看哪個型號跨最多平台銷售？「Size」選「Model Count」，跨平台越多的型號點越大！"
    },

    // --- 矩陣顯示 (Matrix) ---
    {
        "category": "矩陣顯示",
        "color": "bg-amber-500",
        "text": "想要宏觀分析？切換右上角的「Matrix」模式，用熱力圖快速找出哪個品牌在特定價格帶的產品最多。"
    },
    {
        "category": "矩陣顯示",
        "color": "bg-amber-500",
        "text": "想換個分析維度？試試左上角的「Row / Column」切換鈕，可以依照不同屬性重組矩陣。"
    },
    {
        "category": "矩陣顯示",
        "color": "bg-amber-500",
        "text": "「Compare」選項可切換色階範圍：Row 看每行最強區間，Column 比較同欄競爭，Global 看全局絕對值。"
    },
    {
        "category": "矩陣顯示",
        "color": "bg-amber-500",
        "text": "「Data」選項可切換數據類型：Count 看筆數、Comments 看評論總數、Score 看平均評分、Model Count 看獨立型號數。"
    },
    {
        "category": "矩陣顯示",
        "color": "bg-amber-500",
        "text": "Count vs Model Count 差異：Count 計算所有 listing 數量，Model Count 只計算不重複的型號，避免同型號多次上架被重複計算。"
    },

    // --- AI助手 (AI) ---
    {
        "category": "AI助手",
        "color": "bg-purple-500",
        "text": "有問題懶得找？點擊右下角的紫色按鈕，問問 AI 助理「哪個品牌最划算？」。"
    },
    {
        "category": "AI助手",
        "color": "bg-purple-500",
        "text": "想了解更多玩法？點開 AI 面板，選擇「操作詢問」，AI 會教您怎麼使用此工具。"
    }
];
