"""
PT Crawler Manager - Premium UI V3
Features:
- Dark theme based on bambu.ipynb StyleGuide
- Unified Model Selector
- Two tabs: Crawler (Platform Grid) and Data Editor (Custom Table with Images)
"""

import customtkinter as ctk
import json
import os
import io
import threading
import webbrowser
import math
import pandas as pd
from datetime import datetime
from PIL import Image
from tkinter import filedialog
import requests
from csv_utils import CSVHandler, FIXED_COLUMNS
from crawler_manager import CrawlerManager

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

CONFIG_FILE = "config.json"
LOGO_DIR = "../logos"
DEFAULT_CSV = "PT_Data.csv"

# Google Sheets Config
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxayHvvpWggMF8yEtYJxhYjoCe8kR65SxIQwQkHbc7S2XCRs-VxOXWzGEgKClG56vQfLA/exec"
GS_API_KEY = "55759180"  # API Password
GOOGLE_SHEET_ID = "1rc8Cy1Wih3wI3G5Zi3gYMbMQFsoUyzm1lXBpKgHmJ48"
SERVICE_ACCOUNT_FILE = r"D:\OneDrive\Python_File\網頁_PT資料庫\gen-lang-client-0398103701-3388d165b966.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# ================================================================================
# StyleGuide
# ================================================================================
class StyleGuide:
    class Global:
        APPEARANCE_MODE = "dark"
        FONT_FAMILY_CHINESE = "Microsoft JhengHei"
        COLOR_PRIMARY = "#007ACC"
        COLOR_MAIN_BG = "#1E1E1E"
        COLOR_SIDEBAR_BG = "#252526"
        COLOR_FRAME_BG = "#2D2D2D"
        COLOR_WIDGET_BG = "#3C3C3C"
        COLOR_TEXT_PRIMARY = "#FFFFFF"
        COLOR_TEXT_SECONDARY = "#A0A0A0"
        COLOR_SUCCESS = "#4CAF50"
        COLOR_WARNING = "#FFC107"
        CORNER_RADIUS = 8
    class Window:
        TITLE = "PT Crawler Manager"
        GEOMETRY = "1400x800"
    class Layout:
        MAIN_PAD = 15

class Font:
    LARGE_TITLE = (StyleGuide.Global.FONT_FAMILY_CHINESE, 24, "bold")
    SUB_TITLE = (StyleGuide.Global.FONT_FAMILY_CHINESE, 16, "bold")
    BUTTON = (StyleGuide.Global.FONT_FAMILY_CHINESE, 14, "bold")
    UI = (StyleGuide.Global.FONT_FAMILY_CHINESE, 13)
    SMALL = (StyleGuide.Global.FONT_FAMILY_CHINESE, 11)

StyleGuide.Font = Font

# ================================================================================
# Platform Card (Fixed layout - no overlap)
# ================================================================================
class PlatformCard(ctk.CTkFrame):
    def __init__(self, master, platform_name, parent_app, **kwargs):
        super().__init__(master, fg_color=StyleGuide.Global.COLOR_WIDGET_BG, 
                         corner_radius=StyleGuide.Global.CORNER_RADIUS, **kwargs)
        self.platform_name = platform_name
        self.parent_app = parent_app
        self.use_custom_url = ctk.BooleanVar(value=False)
        self.custom_url = ctk.StringVar(value="")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        self.var_selected = ctk.BooleanVar(value=False)
        self.chk = ctk.CTkCheckBox(self, text="", variable=self.var_selected, 
                                    width=24, height=24, checkbox_width=18, checkbox_height=18)
        self.chk.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        
        gear_btn = ctk.CTkButton(self, text="⚙", width=28, height=28,
                                  fg_color="transparent", hover_color=StyleGuide.Global.COLOR_FRAME_BG,
                                  command=self.open_settings)
        gear_btn.grid(row=0, column=1, padx=8, pady=8, sticky="e")
        
        self.logo_image = self._load_logo(platform_name)
        if self.logo_image:
            lbl = ctk.CTkLabel(self, text="", image=self.logo_image)
            lbl.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10))
        else:
            lbl = ctk.CTkLabel(self, text=platform_name, font=StyleGuide.Font.UI,
                               text_color=StyleGuide.Global.COLOR_TEXT_PRIMARY)
            lbl.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10))

    def _load_logo(self, name):
        for ext in [".png", ".jpg", ".jpeg"]:
            path = os.path.join(LOGO_DIR, name + ext)
            if os.path.exists(path):
                try:
                    pil_img = Image.open(path)
                    pil_img.thumbnail((144, 81))
                    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(144, 81))
                except:
                    pass
        return None

    def open_settings(self):
        SettingsModal(self.parent_app, self.platform_name, self)

    def get_run_config(self, global_model):
        if self.use_custom_url.get():
            url = self.custom_url.get()
        else:
            models = self.parent_app.config_data.get("platforms", {}).get(self.platform_name, {}).get("models", {})
            url = models.get(global_model, "")
        return {"platform": self.platform_name, "url": url}

# ================================================================================
# Settings Modal
# ================================================================================
class SettingsModal(ctk.CTkToplevel):
    def __init__(self, parent, platform_name, card):
        super().__init__(parent)
        self.title(f"Settings: {platform_name}")
        self.geometry("400x200")
        self.configure(fg_color=StyleGuide.Global.COLOR_FRAME_BG)
        self.card = card
        
        self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text=f"{platform_name} 設定", 
                     font=StyleGuide.Font.SUB_TITLE).grid(row=0, column=0, columnspan=2, pady=20)
        
        self.use_custom_var = ctk.BooleanVar(value=card.use_custom_url.get())
        chk = ctk.CTkCheckBox(self, text="使用自訂網址", variable=self.use_custom_var,
                               command=self.toggle_custom)
        chk.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(self, text="網址:", font=StyleGuide.Font.UI).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.entry_url = ctk.CTkEntry(self, textvariable=card.custom_url, width=300)
        self.entry_url.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        self.toggle_custom()
        
        ctk.CTkButton(self, text="確定", command=self.destroy,
                      fg_color=StyleGuide.Global.COLOR_PRIMARY).grid(row=3, column=0, columnspan=2, pady=20)

    def toggle_custom(self):
        self.card.use_custom_url.set(self.use_custom_var.get())
        self.entry_url.configure(state="normal" if self.use_custom_var.get() else "disabled")

# ================================================================================
# Data Editor Row (Custom table row with image, inline edit, checkbox)
# ================================================================================
# Column widths (approximate)
# Column widths
# Column widths
COL_WIDTHS = {
    "img": 60, 
    "date": 90,
    "platform": 80,
    "model": 100,
    "accessories": 100,
    "brand": 100, 
    "title": 400,
    "sku": 100,
    "url": 60,
    "exclude": 50,
    "price_old": 80,   # New
    "price_new": 80    # New
}

class DataEditorRow(ctk.CTkFrame):
    """Single row in the data editor table."""
    def __init__(self, master, row_data, idx, parent_app, price_col, **kwargs):
        super().__init__(master, fg_color=StyleGuide.Global.COLOR_WIDGET_BG, height=60, **kwargs)
        self.row_data = row_data
        self.idx = idx
        self.parent_app = parent_app
        self.grid_propagate(False)
        
        # Configure columns: Title (col 6) gets weight 1
        self.grid_columnconfigure(0, weight=0) # Image
        self.grid_columnconfigure(1, weight=0) # Date
        self.grid_columnconfigure(2, weight=0) # Platform
        self.grid_columnconfigure(3, weight=0) # Model
        self.grid_columnconfigure(4, weight=0) # Accessories
        self.grid_columnconfigure(5, weight=0) # Brand
        self.grid_columnconfigure(6, weight=1) # Title (Expand)
        self.grid_columnconfigure(7, weight=0) # SKU
        self.grid_columnconfigure(8, weight=0) # URL
        self.grid_columnconfigure(9, weight=0) # Exclude
        self.grid_columnconfigure(10, weight=0) # Price Old
        self.grid_columnconfigure(11, weight=0) # Price New
        
        # 0. Image
        self.img_label = ctk.CTkLabel(self, text="⏳", width=COL_WIDTHS["img"], height=50,
                                       fg_color=StyleGuide.Global.COLOR_FRAME_BG)
        self.img_label.grid(row=0, column=0, padx=5, pady=5)
        
        # 1. Date Created
        date_val = str(row_data.get("Date Created", "") or row_data.get("建立時間", ""))[:10]
        ctk.CTkLabel(self, text=date_val, font=StyleGuide.Font.SMALL, width=COL_WIDTHS["date"]).grid(row=0, column=1, padx=2)

        # 2. Platform
        plat_val = str(row_data.get("Platform", "") or row_data.get("平台", ""))
        ctk.CTkLabel(self, text=plat_val, font=StyleGuide.Font.SMALL, width=COL_WIDTHS["platform"]).grid(row=0, column=2, padx=2)

        # 3. Model #
        model_val = str(row_data.get("Model #", "") or row_data.get("機型", ""))
        self.model_entry = ctk.CTkEntry(self, width=COL_WIDTHS["model"], height=28, font=StyleGuide.Font.SMALL)
        self.model_entry.insert(0, model_val)
        self.model_entry.grid(row=0, column=3, padx=2, pady=5)
        self.model_entry.bind("<FocusOut>", lambda e: self._update_field("Model #", self.model_entry.get()))
        self.model_entry.bind("<Return>", lambda e: self._update_field("Model #", self.model_entry.get()))

        # 4. Accessories
        self.acc_entry = ctk.CTkEntry(self, width=COL_WIDTHS["accessories"], height=28, font=StyleGuide.Font.SMALL)
        self.acc_entry.insert(0, str(row_data.get("Accessories", "") or row_data.get("配件", "") or ""))
        self.acc_entry.grid(row=0, column=4, padx=2, pady=5)
        self.acc_entry.bind("<FocusOut>", lambda e: self._update_field("Accessories", self.acc_entry.get()))
        self.acc_entry.bind("<Return>", lambda e: self._update_field("Accessories", self.acc_entry.get()))

        # 5. Brand
        lbl_brand = ctk.CTkLabel(self, text=str(row_data.get("Brand", "") or row_data.get("品牌", "") or "")[:15], 
                                  font=StyleGuide.Font.SMALL, width=COL_WIDTHS["brand"], anchor="center")
        lbl_brand.grid(row=0, column=5, padx=2, pady=5)
        
        # 6. Title
        raw_title = str(row_data.get("Title", "") or row_data.get("標題", "") or "")
        display_title = raw_title
        if len(display_title) > 80: # Allow more chars since width is larger
            display_title = display_title[:80] + "..."
            
        lbl_title = ctk.CTkLabel(self, text=display_title, font=StyleGuide.Font.SMALL, anchor="w")
        lbl_title.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        
        # 7. SKU
        lbl_sku = ctk.CTkLabel(self, text=str(row_data.get("SKU", "") or "")[:15], 
                               font=StyleGuide.Font.SMALL, width=COL_WIDTHS["sku"], anchor="center")
        lbl_sku.grid(row=0, column=7, padx=2, pady=5)
        
        # 8. URL
        url = row_data.get("Product URL", "") or row_data.get("網址", "")
        btn_link = ctk.CTkButton(self, text="連結" if url else "-", 
                                 width=COL_WIDTHS["url"], height=28, 
                                 fg_color=StyleGuide.Global.COLOR_PRIMARY if url else StyleGuide.Global.COLOR_FRAME_BG,
                                 state="normal" if url else "disabled",
                                 command=lambda u=url: webbrowser.open(u) if u else None)
        btn_link.grid(row=0, column=8, padx=5, pady=5)
        
        # 9. Exclude
        is_excl = (row_data.get("Exclude Update", "N") == "Y") or (row_data.get("排除更新", "N") == "Y")
        self.exclude_var = ctk.BooleanVar(value=is_excl)
        self.chk_exclude = ctk.CTkCheckBox(self, text="", variable=self.exclude_var,
                                            width=24, height=24, checkbox_width=20, checkbox_height=20,
                                            command=self._on_exclude_change)
        self.chk_exclude.grid(row=0, column=9, padx=5, pady=5)
        
        # 10+. Price Columns (Dynamic)
        # price_col passed as list now: [latest, previous] or just [latest]
        if isinstance(price_col, list):
            # We display up to 2 prices. 
            # If we have 2: [latest, previous] -> We want Previous in Col 10, Latest in Col 11?
            # User said "List the second one... column called Date". 
            # Usually users want Old Left, New Right to scan. 
            # Let's sort them: Oldest -> Newest.
            # But the logic calling this will pass them.
            # Let's assume passed as [latest_date, previous_date].
            
            prices_to_show = price_col[:2]
            # No reverse: Show Latest then Previous (Left -> Right)
            
            current_col = 10
            for p_col in prices_to_show:
                price_val = str(row_data.get(p_col, ""))
                
                # Highlight logic: Green for latest
                color = StyleGuide.Global.COLOR_SUCCESS if p_col == price_col[0] else StyleGuide.Global.COLOR_TEXT_PRIMARY
                
                lbl = ctk.CTkLabel(self, text=price_val, font=StyleGuide.Font.SMALL, 
                                   width=COL_WIDTHS["price_new"], anchor="center", 
                                   text_color=color)
                lbl.grid(row=0, column=current_col, padx=5, pady=5)
                current_col += 1
        else:
             # Fallback
             pass

    def set_image(self, ctk_img):
        if self.winfo_exists():
            self.img_label.configure(text="", image=ctk_img)

    def set_image_error(self):
        if self.winfo_exists():
            self.img_label.configure(text="❌")

    def set_image_none(self):
        if self.winfo_exists():
            self.img_label.configure(text="-")

    def _update_field(self, field, value):
        sku = self.row_data.get("SKU", "")
        self.row_data[field] = value
        if self.parent_app.csv_handler:
            self.parent_app.csv_handler.update_row(sku, field, value)

    def _on_exclude_change(self):
        new_val = "Y" if self.exclude_var.get() else "N"
        self._update_field("Exclude Update", new_val)

# ================================================================================
# Main Application
# ================================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(StyleGuide.Global.APPEARANCE_MODE)
        self.title(StyleGuide.Window.TITLE)
        self.geometry(StyleGuide.Window.GEOMETRY)
        self.configure(fg_color=StyleGuide.Global.COLOR_MAIN_BG)
        
        self.config_data = self.load_config()
        self.crawler_manager = CrawlerManager(log_callback=self.log_message)
        self.csv_handler = None
        self.cards = []
        self.editor_data = []
        self.editor_rows = []
        self.image_cache = {}
        self.gs_sheet_list = []  # Google Sheets list
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_area()
        
        # Auto-fetch Google Sheets list on startup
        self.after(500, self.fetch_gs_sheets)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_csv_path": DEFAULT_CSV, "platforms": {}}

    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=2, ensure_ascii=False)

    def _get_all_models(self):
        models = set()
        for pdata in self.config_data.get("platforms", {}).values():
            for m in pdata.get("models", {}).keys():
                models.add(m)
        return sorted(list(models)) if models else ["Default"]

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0,
                               fg_color=StyleGuide.Global.COLOR_SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)
        
        ctk.CTkLabel(sidebar, text="PT Crawler", font=StyleGuide.Font.LARGE_TITLE).pack(pady=30)
        
        ctk.CTkLabel(sidebar, text="Google Sheets:", font=StyleGuide.Font.UI).pack(pady=(10, 5), padx=20, anchor="w")
        
        ctk.CTkLabel(sidebar, text="選擇分頁:", font=StyleGuide.Font.SMALL,
                     text_color=StyleGuide.Global.COLOR_TEXT_SECONDARY).pack(pady=(5, 2), padx=20, anchor="w")
        self.gs_sheet_var = ctk.StringVar(value="(連線中...)")
        self.gs_sheet_dropdown = ctk.CTkComboBox(sidebar, values=["(連線中...)"], 
                                                  variable=self.gs_sheet_var, width=200)
        self.gs_sheet_dropdown.pack(pady=2, padx=20, fill="x")
        
        ctk.CTkButton(sidebar, text="📥 Load Data", command=self.load_from_gs,
                      fg_color=StyleGuide.Global.COLOR_SUCCESS, width=200, height=35,
                      font=StyleGuide.Font.BUTTON).pack(pady=10, padx=20, fill="x")

        
        ctk.CTkFrame(sidebar, height=2, fg_color=StyleGuide.Global.COLOR_WIDGET_BG).pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(sidebar, text="Model (機型):", font=StyleGuide.Font.UI).pack(pady=(5, 5), padx=20, anchor="w")
        self.global_model_var = ctk.StringVar(value=self._get_all_models()[0] if self._get_all_models() else "")
        self.model_combo = ctk.CTkComboBox(sidebar, values=self._get_all_models(), 
                                            variable=self.global_model_var, width=200,
                                            command=self.on_model_change)
        self.model_combo.pack(padx=20, fill="x")
        
        ctk.CTkFrame(sidebar, height=2, fg_color=StyleGuide.Global.COLOR_WIDGET_BG).pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(sidebar, text="Select All", command=self.select_all,
                      fg_color=StyleGuide.Global.COLOR_WIDGET_BG).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(sidebar, text="Deselect All", command=self.deselect_all,
                      fg_color=StyleGuide.Global.COLOR_FRAME_BG).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(sidebar, text="▶ RUN SELECTED", command=self.run_crawl,
                      fg_color=StyleGuide.Global.COLOR_SUCCESS, font=StyleGuide.Font.BUTTON,
                      height=40).pack(pady=15, padx=20, fill="x")
        
        ctk.CTkFrame(sidebar, height=2, fg_color=StyleGuide.Global.COLOR_WIDGET_BG).pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(sidebar, text="Open config.json", command=self.open_config,
                      fg_color=StyleGuide.Global.COLOR_FRAME_BG).pack(pady=10, padx=20, fill="x")

    def create_main_area(self):
        main_frame = ctk.CTkFrame(self, fg_color=StyleGuide.Global.COLOR_MAIN_BG)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=StyleGuide.Layout.MAIN_PAD, 
                        pady=StyleGuide.Layout.MAIN_PAD)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        tab_bar = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
        tab_bar.grid(row=0, column=0, sticky="ew")
        
        self.tab_var = ctk.StringVar(value="crawler")
        ctk.CTkButton(tab_bar, text="🔍 爬蟲", command=lambda: self.switch_tab("crawler"),
                      fg_color=StyleGuide.Global.COLOR_FRAME_BG, width=120).pack(side="left", padx=5)
        ctk.CTkButton(tab_bar, text="📝 資料編輯", command=lambda: self.switch_tab("editor"),
                      fg_color=StyleGuide.Global.COLOR_WIDGET_BG, width=120).pack(side="left", padx=5)
        
        self.content_frame = ctk.CTkFrame(main_frame, fg_color=StyleGuide.Global.COLOR_FRAME_BG,
                                          corner_radius=StyleGuide.Global.CORNER_RADIUS)
        self.content_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self.switch_tab("crawler")
        
        log_frame = ctk.CTkFrame(main_frame, fg_color=StyleGuide.Global.COLOR_FRAME_BG, height=100)
        log_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.log_text = ctk.CTkTextbox(log_frame, height=80, fg_color=StyleGuide.Global.COLOR_WIDGET_BG)
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

    def switch_tab(self, tab_name):
        self.tab_var.set(tab_name)
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if tab_name == "crawler":
            self.build_crawler_tab()
        else:
            self.build_editor_tab()
            
            # Restore state if editor_data exists
            if self.editor_data:
                # Refresh price columns from data
                self.detect_price_cols()
                # Update headers
                self.update_headers(getattr(self, 'price_cols', []))
                
                # Repopulate filters dropdowns
                try:
                    dates = sorted(list(set(str(row.get("Date Created", "") or row.get("建立時間", "")) for row in self.editor_data if row)))
                    if hasattr(self, 'combo_date'): self.combo_date.configure(values=["All"] + dates)
                    
                    plats = sorted(list(set(str(row.get("Platform", "") or row.get("平台", "")) for row in self.editor_data if row)))
                    if hasattr(self, 'combo_platform'): self.combo_platform.configure(values=["All"] + plats)
                except Exception as e:
                    print(f"Error repopulating filters: {e}")

                # Apply persistent filter to restore view without resetting
                self.after(50, self.apply_filter)

    def on_model_change(self, selected_model=None):
        """Refresh platform grid when model changes."""
        if self.tab_var.get() == "crawler":
            self.build_crawler_tab()

    def build_crawler_tab(self):
        # Clear existing content first
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Filter platforms by selected model
        selected_model = self.global_model_var.get()
        platforms_config = self.config_data.get("platforms", {})
        platforms = [
            p_name for p_name, p_data in platforms_config.items()
            if p_data.get("models", {}).get(selected_model)
        ]
        
        cols = 6
        self.cards = []
        for i, p_name in enumerate(platforms):
            card = PlatformCard(scroll, p_name, self)
            card.grid(row=i//cols, column=i%cols, padx=8, pady=8)
            self.cards.append(card)
        
        for col in range(cols):
            scroll.grid_columnconfigure(col, weight=1)

    def build_editor_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        
        # Toolbar
        toolbar = ctk.CTkFrame(frame, fg_color="transparent", height=50)
        toolbar.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(toolbar, text="📤 Upload", command=self.upload_to_gs,
                      fg_color=StyleGuide.Global.COLOR_SUCCESS, width=100).pack(side="left", padx=5)
        
        # Initialize Persistent Variables (if not exists)
        if not hasattr(self, 'filter_date_var'): self.filter_date_var = ctk.StringVar(value="All")
        if not hasattr(self, 'filter_platform_var'): self.filter_platform_var = ctk.StringVar(value="All")
        if not hasattr(self, 'filter_text_var'): self.filter_text_var = ctk.StringVar(value="")
        if not hasattr(self, 'sort_var'): self.sort_var = ctk.StringVar(value="Date Created")

        # Filter controls
        ctk.CTkLabel(toolbar, text="日期:", font=StyleGuide.Font.UI).pack(side="left", padx=(15, 5))
        self.combo_date = ctk.CTkComboBox(toolbar, values=["All"], variable=self.filter_date_var, 
                                          width=120, command=self.apply_filter)
        self.combo_date.pack(side="left", padx=5)

        ctk.CTkLabel(toolbar, text="平台:", font=StyleGuide.Font.UI).pack(side="left", padx=(15, 5))
        self.combo_platform = ctk.CTkComboBox(toolbar, values=["All"], variable=self.filter_platform_var,
                                              width=120, command=self.apply_filter)
        self.combo_platform.pack(side="left", padx=5)
        
        ctk.CTkLabel(toolbar, text="標題搜尋:", font=StyleGuide.Font.UI).pack(side="left", padx=(15, 5))
        self.entry_filter = ctk.CTkEntry(toolbar, width=120, placeholder_text="關鍵字...", textvariable=self.filter_text_var)
        self.entry_filter.pack(side="left", padx=5)
        self.entry_filter.bind("<Return>", lambda e: self.apply_filter())
        ctk.CTkButton(toolbar, text="Go", command=self.apply_filter, width=40,
                      fg_color=StyleGuide.Global.COLOR_PRIMARY).pack(side="left", padx=5)

        # Sort controls
        ctk.CTkLabel(toolbar, text="排序:", font=StyleGuide.Font.UI).pack(side="left", padx=(15, 5))
        # sort_var already initialized above
        sort_combo = ctk.CTkComboBox(toolbar, values=["Date Created", "Brand", "Title", "SKU", "Exclude Update", "Price Tag"], 
                                      variable=self.sort_var, width=120)
        sort_combo.pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="Sort", command=self.sort_editor_data, width=60,
                      fg_color=StyleGuide.Global.COLOR_WIDGET_BG).pack(side="left", padx=5)
        
        # Pagination Controls
        self.btn_prev = ctk.CTkButton(toolbar, text="<", width=40, command=self.prev_page, state="disabled")
        self.btn_prev.pack(side="left", padx=(20, 5))
        
        self.lbl_page = ctk.CTkLabel(toolbar, text="Page 1/1", font=StyleGuide.Font.UI, width=80)
        self.lbl_page.pack(side="left", padx=5)
        
        self.btn_next = ctk.CTkButton(toolbar, text=">", width=40, command=self.next_page, state="disabled")
        self.btn_next.pack(side="left", padx=5)
        
        # Loading label
        self.loading_label = ctk.CTkLabel(toolbar, text="", font=StyleGuide.Font.SMALL,
                                          text_color=StyleGuide.Global.COLOR_WARNING)
        self.loading_label.pack(side="left", padx=20)
        
        # Table Header Frame (Init empty, filled by update_headers)
        self.header_frame = ctk.CTkFrame(frame, fg_color=StyleGuide.Global.COLOR_FRAME_BG, height=35)
        self.header_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.header_frame.grid_propagate(False)
        
        # Initial headers render
        self.update_headers()

        # Scrollable Table Body
        self.table_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.table_scroll.grid(row=2, column=0, sticky="nsew", pady=5)
        self.table_scroll.grid_columnconfigure(0, weight=1)
        
        # State variables (only initialize if not already set)
        if not hasattr(self, 'editor_rows'):
            self.editor_rows = []
        if not hasattr(self, 'current_page'):
            self.current_page = 1
        if not hasattr(self, 'page_size'):
            self.page_size = 50
        if not hasattr(self, 'total_pages'):
            self.total_pages = 1
        if not hasattr(self, 'price_cols'):
            self.price_cols = []
        if not hasattr(self, 'active_filter'):
            self.active_filter = ""
        if not hasattr(self, 'filtered_data'):
            self.filtered_data = []

    def detect_price_cols(self):
        """Analyze editor_data to find and sort date columns (YYYYMMDD)."""
        if not self.editor_data:
            self.price_cols = []
            return

        all_keys = set()
        for row in self.editor_data:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        
        # Filter for 8-digit date strings starting with '20'
        date_cols = [k for k in all_keys if len(k) == 8 and k.isdigit() and k.startswith("20")]
        date_cols.sort(reverse=True)
        self.price_cols = date_cols

    def update_headers(self, price_labels=None):
        for widget in self.header_frame.winfo_children():
            widget.destroy()
            
        cols_count = 12 # Up to 2 prices
        for i in range(cols_count):
            self.header_frame.grid_columnconfigure(i, weight=1 if i == 6 else 0)

        # Base Headers
        headers = [
            ("圖片", COL_WIDTHS["img"]), 
            ("日期", COL_WIDTHS["date"]), 
            ("平台", COL_WIDTHS["platform"]), 
            ("機型", COL_WIDTHS["model"]), 
            ("配件", COL_WIDTHS["accessories"]), 
            ("品牌", COL_WIDTHS["brand"]), 
            ("標題 (Title)", 0), 
            ("SKU", COL_WIDTHS["sku"]),
            ("連結", COL_WIDTHS["url"]),
            ("排除", COL_WIDTHS["exclude"]),
        ]
        
        # Dynamic Price Headers
        if price_labels:
            # price_labels is [latest, previous]
            # User wants Latest (Left), Previous (Right)
            
            # Show Latest
            if len(price_labels) > 0:
                headers.append((price_labels[0], COL_WIDTHS["price_new"]))
            else:
                headers.append(("最新價格", COL_WIDTHS["price_new"]))

            # Show Previous (if exists)
            if len(price_labels) > 1:
                headers.append((price_labels[1], COL_WIDTHS["price_old"]))
            else:
                headers.append(("", COL_WIDTHS["price_old"])) # Spacer
        else:
            headers.append(("最新價格", COL_WIDTHS["price_new"]))
            headers.append(("", COL_WIDTHS["price_old"]))

        for col, (text, width) in enumerate(headers):
            lbl = ctk.CTkLabel(self.header_frame, text=text, font=StyleGuide.Font.UI, 
                               fg_color=StyleGuide.Global.COLOR_FRAME_BG, anchor="center")
            if width > 0:
                lbl.configure(width=width)
            lbl.grid(row=0, column=col, padx=2, pady=5, sticky="ew" if col == 6 else "")

    def apply_filter(self, _=None):
        # Gather filter values
        date_filter = self.filter_date_var.get()
        plat_filter = self.filter_platform_var.get()
        text_query = self.filter_text_var.get().lower().strip()
        
        self.filtered_data = []
        
        for row in self.editor_data:
            # 1. Date Filter
            if date_filter != "All":
                row_date = str(row.get("Date Created", "") or row.get("建立時間", ""))
                # Handle flexible date matching (e.g. 2026-01-07)
                if not row_date.startswith(date_filter):
                    continue
            
            # 2. Platform Filter
            if plat_filter != "All":
                row_plat = str(row.get("Platform", "") or row.get("平台", ""))
                if row_plat != plat_filter:
                    continue
            
            # 3. Text Search (Title/Model/Brand)
            if text_query:
                # Search in specific fields for better accuracy? Or just all
                # User hated "What is search", so make it unobtrusive.
                found = False
                for k, v in row.items():
                    if text_query in str(v).lower():
                        found = True
                        break
                if not found:
                    continue
            
            self.filtered_data.append(row)
        
        self.log_message(f"Filter: Date={date_filter}, Plat={plat_filter}, Text={text_query} -> {len(self.filtered_data)}")
        self.total_pages = math.ceil(len(self.filtered_data) / self.page_size) if self.filtered_data else 1
        self.current_page = 1
        self.render_table()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()

    def load_csv_for_editor(self):
        csv_path = self.entry_csv.get()
        if not csv_path or not os.path.exists(csv_path):
            self.log_message("CSV not found. Run crawler first or select a valid file.")
            return
        
        self.csv_handler = CSVHandler(filepath=csv_path)
        df = self.csv_handler.get_dataframe()
        self.editor_data = df.to_dict('records')
        
        # Detect Price Columns: Look for columns that look like YYYYMMDD
        all_cols = df.columns.tolist()
        date_candidates = []
        for c in all_cols:
            if c.isdigit() and len(c) == 8 and c.startswith("20"):
                 date_candidates.append(c)
        
        self.price_cols = []
        if date_candidates:
            date_candidates.sort(reverse=True)
            self.price_cols = date_candidates[:2] # Get top 2
        else:
             fixed = {"Date Created", "Platform", "Model #", "Accessories", "Brand", "Title", "SKU", "Product URL", "Image URL", "Exclude Update", "Repeat check", "Price Tag"}
             candidates = [c for c in df.columns if c not in fixed]
             if candidates:
                 self.price_cols = [candidates[0]]

        # Update Headers with actual dates
        self.update_headers(self.price_cols)

        # Populate Filters
        # Dates
        # Try both English and Chinese keys
        dates = set()
        platforms = set()
        
        for row in self.editor_data:
            d = row.get("Date Created") or row.get("建立時間")
            if d: dates.add(str(d))
            
            p = row.get("Platform") or row.get("平台")
            if p: platforms.add(str(p))
            
        sorted_dates = sorted(list(dates), reverse=True)
        sorted_plats = sorted(list(platforms))
        
        self.combo_date.configure(values=["All"] + sorted_dates)
        self.combo_platform.configure(values=["All"] + sorted_plats)
        self.filter_date_var.set("All")
        self.filter_platform_var.set("All")

        self.filtered_data = list(self.editor_data)
        self.total_pages = math.ceil(len(self.filtered_data) / self.page_size) if self.filtered_data else 1
        
        self.render_table()
        self.log_message(f"Loaded {len(self.editor_data)} rows. Price cols: {self.price_cols}")

    def render_table(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
        self.editor_rows = []
        
        if not self.filtered_data:
            return

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.filtered_data[start_idx:end_idx]
        
        self.lbl_page.configure(text=f"Page {self.current_page}/{self.total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < self.total_pages else "disabled")
        
        self.loading_label.configure(text=f"Rendering {len(page_data)} rows...")
        
        for i, row in enumerate(page_data):
            # Pass list of price columns
            row_widget = DataEditorRow(self.table_scroll, row, i, self, self.price_cols)
            row_widget.grid(row=i, column=0, sticky="ew", pady=2)
            self.editor_rows.append(row_widget)
        
        threading.Thread(target=self._load_page_images, args=(page_data,), daemon=True).start()
        self.loading_label.configure(text="")

    def _load_page_images(self, page_data):
        for i, row in enumerate(page_data):
            if i >= len(self.editor_rows): break
            
            url = row.get("Image URL", "")
            if url:
                try:
                    if url in self.image_cache:
                        ctk_img = self.image_cache[url]
                    else:
                        resp = requests.get(url, timeout=5)
                        if resp.status_code == 200:
                            pil_img = Image.open(io.BytesIO(resp.content))
                            pil_img.thumbnail((50, 50))
                            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
                            self.image_cache[url] = ctk_img
                        else:
                            ctk_img = None
                    
                    if ctk_img:
                        self.after(0, lambda idx=i, img=ctk_img: self.editor_rows[idx].set_image(img) if idx < len(self.editor_rows) else None)
                    else:
                        self.after(0, lambda idx=i: self.editor_rows[idx].set_image_error() if idx < len(self.editor_rows) else None)
                except:
                    self.after(0, lambda idx=i: self.editor_rows[idx].set_image_error() if idx < len(self.editor_rows) else None)
            else:
                self.after(0, lambda idx=i: self.editor_rows[idx].set_image_none() if idx < len(self.editor_rows) else None)

    def sort_editor_data(self):
        if not self.editor_data:
            return
        
        sort_key = self.sort_var.get()
        
        if hasattr(self, '_last_sort_key') and self._last_sort_key == sort_key:
            self._sort_reverse = not getattr(self, '_sort_reverse', False)
        else:
            self._sort_reverse = False
        self._last_sort_key = sort_key
        
        self.editor_data.sort(key=lambda x: str(x.get(sort_key, "")), reverse=self._sort_reverse)
        
        direction = "↓" if self._sort_reverse else "↑"
        self.log_message(f"Sorted by {sort_key} {direction}")
        
        self.current_page = 1
        self.render_table()

    def save_csv_changes(self):
        if self.csv_handler:
            self.csv_handler.save()
            self.log_message("Changes saved to CSV.")

    def browse_csv(self):
        path = filedialog.askopenfilename(defaultextension=".csv", 
                                           filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if path:
            self.entry_csv.delete(0, "end")
            self.entry_csv.insert(0, path)
            self.config_data["last_csv_path"] = path
            self.save_config()

    def select_all(self):
        for c in self.cards:
            c.var_selected.set(True)

    def deselect_all(self):
        for c in self.cards:
            c.var_selected.set(False)

    def run_crawl(self):
        # Use current selected sheet name for CSV filename
        sheet_name = self.gs_sheet_var.get()
        if not sheet_name or sheet_name in ["(連線中...)", "(無分頁)"]:
            self.log_message("Error: Please select a Google Sheets tab first.")
            return
        
        # Construct CSV path from sheet name
        csv_path = f"PT Data 平台 - {sheet_name}.csv"
        
        global_model = self.global_model_var.get()
        self.log_message(f"Using model: {global_model}")
        self.log_message(f"CSV file: {csv_path}")
        
        tasks = []
        for card in self.cards:
            if card.var_selected.get():
                cfg = card.get_run_config(global_model)
                platform_name = cfg["platform"]
                
                if platform_name == "Bauhaus":
                    self.log_message("Requesting Bauhaus CSV file...")
                    bauhaus_file = filedialog.askopenfilename(
                        title="請選擇 Bauhaus 平台資料 (Select Bauhaus CSV Data)",
                        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
                    )
                    if not bauhaus_file:
                        self.log_message("Warning: Skipped Bauhaus (No file selected)")
                        continue
                        
                    tasks.append((platform_name, bauhaus_file))
                    
                elif cfg["url"]:
                    tasks.append((platform_name, cfg["url"]))
                else:
                    self.log_message(f"Warning: Skipped {platform_name} (No URL for '{global_model}')")
        
        if not tasks:
            self.log_message("Error: No valid tasks selected.")
            return
        
        # Define callback to refresh editor after crawl completes
        def on_crawl_complete():
            self.log_message("📋 爬蟲完成！更新預覽資料...")
            # Refresh UI on main thread
            self.after(0, self._refresh_editor_after_crawl)
        
        self.crawler_manager.run_batch(tasks, csv_path, 
                                        editor_data=self.editor_data,
                                        update_callback=on_crawl_complete)

    def open_config(self):
        if os.path.exists(CONFIG_FILE):
            os.startfile(CONFIG_FILE)

    def log_message(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
    
    def _refresh_editor_after_crawl(self):
        """Refresh editor data after crawl completes."""
        if not self.editor_data:
            self.log_message("⚠️ 沒有資料可顯示")
            return
        
        # Update filtered_data
        self.filtered_data = list(self.editor_data)
        self.total_pages = math.ceil(len(self.editor_data) / self.page_size) if self.editor_data else 1
        self.current_page = 1
        
        # Detect price columns
        if self.editor_data:
            all_cols = list(self.editor_data[0].keys())
            date_candidates = [c for c in all_cols if str(c).isdigit() and len(str(c)) == 8 and str(c).startswith("20")]
            if date_candidates:
                date_candidates.sort(reverse=True)
                self.price_cols = date_candidates[:2]
        
        # Update UI if we're on editor tab
        if self.tab_var.get() == "editor" and hasattr(self, 'header_frame'):
            self.update_headers(self.price_cols)
            self.render_table()
        
        self.log_message(f"✅ 資料已更新！共 {len(self.editor_data)} 筆")
    
    # =========================================================================
    # Google Sheets Integration
    # =========================================================================
    def fetch_gs_sheets(self):
        """Fetch list of sheets from Google Sheets via Apps Script."""
        self.log_message("正在取得 Google Sheets 分頁清單...")
        
        def task():
            try:
                url = f"{APPS_SCRIPT_URL}?action=getSheets&key={GS_API_KEY}"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if isinstance(data, list):
                    self.gs_sheet_list = data
                    self.log_message(f"✅ 取得 {len(data)} 個分頁")
                    
                    # Update dropdown on main thread
                    self.after(0, lambda: self.gs_sheet_dropdown.configure(values=data))
                    if data:
                        self.after(0, lambda: self.gs_sheet_var.set(data[0]))
                elif isinstance(data, dict) and "error" in data:
                    self.log_message(f"❌ API 錯誤: {data['error']}")
                else:
                    self.log_message(f"❌ 未知回應格式")
                    
            except Exception as e:
                self.log_message(f"❌ 取得分頁失敗: {e}")
                
        threading.Thread(target=task, daemon=True).start()
    
    def load_from_gs(self):
        """Load data from selected Google Sheets tab."""
        sheet_name = self.gs_sheet_var.get()
        if not sheet_name or sheet_name == "(連線中...)" or sheet_name == "(無分頁)":
            self.log_message("⚠️ 請先選擇分頁")
            return
        
        self.log_message(f"正在從 Google Sheets 載入: {sheet_name}")
        
        def task():
            try:
                url = f"{APPS_SCRIPT_URL}?action=getData&sheet={requests.utils.quote(sheet_name)}&key={GS_API_KEY}"
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                
                if isinstance(data, list) and data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    self.log_message(f"📥 載入 {len(df)} 筆資料")
                    
                    # Store in editor_data format
                    self.editor_data = df.to_dict('records')
                    
                    # Detect price columns
                    all_cols = df.columns.tolist()
                    date_candidates = [c for c in all_cols if str(c).isdigit() and len(str(c)) == 8 and str(c).startswith("20")]
                    
                    if date_candidates:
                        date_candidates.sort(reverse=True)
                        self.price_cols = date_candidates[:2]
                    else:
                        self.price_cols = []
                    
                    # Populate filter dropdowns
                    dates = set()
                    platforms = set()
                    for row in self.editor_data:
                        d = row.get("Date Created") or row.get("建立時間")
                        if d: dates.add(str(d))
                        p = row.get("Platform") or row.get("平台")
                        if p: platforms.add(str(p))
                    
                    sorted_dates = sorted(list(dates), reverse=True)
                    sorted_plats = sorted(list(platforms))
                    
                    # Update UI on main thread - consolidate into one function
                    def update_ui():
                        # Set filtered data and pagination
                        self.filtered_data = list(self.editor_data)
                        self.total_pages = math.ceil(len(self.editor_data) / self.page_size) if self.editor_data else 1
                        self.current_page = 1
                        
                        # Update headers
                        self.update_headers(self.price_cols)
                        
                        # Update filter dropdowns
                        self.combo_date.configure(values=["All"] + sorted_dates)
                        self.combo_platform.configure(values=["All"] + sorted_plats)
                        
                        # Render table
                        self.render_table()
                        
                    self.after(0, update_ui)
                    
                    self.log_message(f"✅ 載入完成！Price cols: {self.price_cols}")
                elif isinstance(data, dict) and "error" in data:
                    self.log_message(f"❌ 載入失敗: {data['error']}")
                else:
                    self.log_message(f"❌ 分頁為空或格式錯誤")
                    
            except Exception as e:
                self.log_message(f"❌ 載入錯誤: {e}")
                
        threading.Thread(target=task, daemon=True).start()
    
    def upload_to_gs(self):
        """Upload edited data back to Google Sheets."""
        if not self.editor_data:
            self.log_message("⚠️ 沒有資料可上傳")
            return
        
        # Get current sheet name
        sheet_name = self.gs_sheet_var.get()
        model = self.global_model_var.get()
        today = datetime.now().strftime("%Y%m%d")
        
        # Determine Mode: Create New or Update Existing
        target_sheet_name = None
        is_update_mode = False
        
        if sheet_name and sheet_name not in ["(連線中...)", "(無分頁)"]:
            # Update existing sheet
            target_sheet_name = sheet_name
            is_update_mode = True
            self.log_message(f"準備回寫至現有分頁: {target_sheet_name} (從 D 欄開始覆蓋)")
        else:
            # Create new sheet
            target_sheet_name = f"{model}_{today}"
            self.log_message(f"準備建立新分頁: {target_sheet_name}")
        
        def task():
            try:
                # Authenticate
                creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                client = gspread.authorize(creds)
                self.log_message("✓ 連接 Google API 成功")
                
                spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
                
                # Check target sheet
                if is_update_mode:
                    try:
                        worksheet = spreadsheet.worksheet(target_sheet_name)
                    except gspread.exceptions.WorksheetNotFound:
                        self.log_message(f"❌ 找不到分頁: {target_sheet_name}")
                        return
                else:
                    # Create/Overwrite new sheet logic
                    try:
                        existing = spreadsheet.worksheet(target_sheet_name)
                        spreadsheet.del_worksheet(existing)
                    except: pass
                    worksheet = spreadsheet.add_worksheet(title=target_sheet_name, rows=1000, cols=20)
                
                # Prepare Data
                df = pd.DataFrame(self.editor_data)
                
                # Columns to SKIP (Keep in sheet)
                skip_cols = ["Repeat check", "Image", "Price Tag"]
                
                # Columns to WRITE (Dynamic)
                # 1. Date columns (Newest first)
                all_cols = list(df.columns)
                date_cols = [c for c in all_cols if len(c) == 8 and c.isdigit() and c.startswith("20")]
                date_cols.sort(reverse=True)
                
                # 2. Standard columns
                std_cols = ["Date Created", "Platform", "Model #", "Accessories", "Brand", "Title", "SKU", "Product URL", "Image URL", "Exclude Update", "Audit Status", "Audit Reason"]
                
                # 3. Construct Final Order
                final_cols = []
                for c in std_cols:
                    if c in df.columns: final_cols.append(c)
                
                # Add dates (if not already in std_cols - unlikely but safe)
                for c in date_cols:
                    if c not in final_cols: final_cols.append(c)
                    
                # Add any others
                for c in all_cols:
                    if c not in final_cols and c not in skip_cols:
                        final_cols.append(c)
                        
                df_export = df[final_cols]
                
                # Prepare payload
                header = df_export.columns.tolist()
                data_rows = df_export.fillna("").astype(str).values.tolist()
                all_data = [header] + data_rows
                
                if is_update_mode:
                    # Update starting from D1 (Column 4)
                    # We assume A, B, C are Fixed. We overwrite D onwards.
                    # Adjust range string based on data size
                    row_count = len(all_data)
                    col_count = len(header)
                    # Convert col index to letter (simple approach for < 26 cols, assumes standard)
                    # D is col 4. 
                    # End col? gspread handles range if we give start cell
                    self.log_message(f"寫入 {row_count} 筆資料至 {target_sheet_name}!D1...")
                    worksheet.update('D1', all_data, value_input_option='RAW')
                else:
                    # New sheet: Write everything (ignoring skip_cols is weird here but user only asked for update)
                    # If creating new, maybe we should write all? 
                    # But user context is Audit. Let's write what we have.
                    self.log_message(f"寫入新分頁 {target_sheet_name}...")
                    worksheet.update('A1', all_data, value_input_option='RAW')
                    
                self.log_message(f"✅ 上傳成功！")
                
                if not is_update_mode:
                    self.after(0, self.fetch_gs_sheets)
                    
            except Exception as e:
                self.log_message(f"❌ 上傳錯誤: {e}")
                print(e)
                
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
