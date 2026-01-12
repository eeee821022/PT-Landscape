
import pandas as pd
import os
import re
import sys
import io

# Force UTF-8 for stdout
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# File Paths
SOURCE_FILE = r"d:\OneDrive\Python_File\網頁_PT資料庫\PT爬蟲工具\PT Data 清理 - Miter Saw_Data.csv"
TARGET_FILE = r"d:\OneDrive\Python_File\網頁_PT資料庫\PT 機型整理 - MTS List 完整.csv"
OUTPUT_FILE = r"d:\OneDrive\Python_File\網頁_PT資料庫\PT 機型整理 - MTS List 完整_Normalized.csv"

def normalize_string(s):
    if not isinstance(s, str):
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()


def main():
    print(f"Script started. Python version: {sys.version}")

    print("Loading Source Data (Clean Dictionary)...")
    try:
        source_df = pd.read_csv(SOURCE_FILE)
    except Exception as e:
        print(f"Error loading source file: {e}")
        return

    # Build Clean Model Dictionary by Brand
    # brand_models = { "makita": {"ls004g", "dls713"...}, "bosch": {...} }
    brand_models = {}
    clean_model_lookup = {} # normalized -> original clean name (e.g. 'ls004g' -> 'LS004G')

    for idx, row in source_df.iterrows():
        raw_brand = str(row.get('品牌', '')).strip()
        raw_model = str(row.get('機型', '')).strip()
        exclude = str(row.get('排除更新', '')).strip()

        # Skip invalid or excluded rows if necessary (User didn't strictly say skip excluded, but likely we want valid models)
        if not raw_brand or raw_brand.lower() == 'nan' or not raw_model or raw_model.lower() == 'nan':
            continue
            
        # Normalize Brand
        brand_key = normalize_string(raw_brand)
        if brand_key not in brand_models:
            brand_models[brand_key] = set()
        
        # Normalize Model
        mod_key = normalize_string(raw_model)
        brand_models[brand_key].add(mod_key)
        
        # Store original formatting for retrieval
        clean_model_lookup[(brand_key, mod_key)] = raw_model

    print(f"Built clean model list for {len(brand_models)} brands.")

    print("Loading Target Data (To be Corrected)...")
    try:
        target_df = pd.read_csv(TARGET_FILE)
    except Exception as e:
        print(f"Error loading target file: {e}")
        return

    updated_count = 0
    
    print("Processing Target Rows...")
    for idx, row in target_df.iterrows():
        original_model = str(row.get('Model #', '')).strip()
        brand = str(row.get('Brand', '')).strip()
        
        if not original_model or not brand:
            continue

        brand_key = normalize_string(brand)
        model_key = normalize_string(original_model)
        
        new_model_name = None

        if brand_key in brand_models:
            candidates = brand_models[brand_key]
            
            # Strategy 1: Exact Match (Normalized)
            if model_key in candidates:
                new_model_name = clean_model_lookup[(brand_key, model_key)]
            else:
                # Strategy 2: Substring Match
                # Check if a clean model is a substring of the target (e.g. Clean="LS004G" in Target="LS004G 36V")
                # Or vice versa (less likely to be correct if clean is very short)
                
                # Sort candidates by length (descending) to match longest valid model first
                sorted_candidates = sorted(list(candidates), key=len, reverse=True)
                
                for cand in sorted_candidates:
                    # Clean is inside Dirty (e.g. 'ls004g' in 'ls004g36v')
                    if cand in model_key and len(cand) > 3: 
                        new_model_name = clean_model_lookup[(brand_key, cand)]
                        break
                    # Dirty is inside Clean (e.g. 'dls713' in 'dls713z') - Optional, be careful
                    # if model_key in cand:
                    #     new_model_name = clean_model_lookup[(brand_key, cand)]
                    #     break
        
        # Apply Update
        if new_model_name and new_model_name != original_model:
            target_df.at[idx, 'Model #'] = new_model_name
            updated_count += 1
            # print(f"Updated: {original_model} -> {new_model_name}")

    print(f"Total Rows Updated: {updated_count}")

    print("Saving Output...")
    target_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
