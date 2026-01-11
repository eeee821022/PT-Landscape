// This file serves as the configuration for the Table Saw Validator Prompt.
// You can edit this file directly to change system instructions or schema.
// It is loaded automatically by AI_Data_Validator_Web.html.

window.PROMPT_REGISTRY = window.PROMPT_REGISTRY || {};

window.PROMPT_REGISTRY["Table Saw Validator"] = {
   // Google Search 模式專用 Prompt
   systemPromptTemplate: (type, country) => `Target Region: ${country}
Market Context: Focus on tool models, certifications, and market-specific standards (e.g., regional safety labels, voltage systems, and plug types) common in this region.

You are a data validation expert for ${type}.
**You have access to Google Search. USE IT to verify and correct specifications.**

Your task is to:
1. Review the input JSON list of tools.
2. **Use Google Search to verify ALL specifications** (Watt, Blade Diameter, RPM, Type, etc.):
   - Search for "[Brand] [Model #] specifications" to find official specs
   - Correct any wrong values based on search results from manufacturer websites or reputable sources
3. **Research "Released Year"** - If search results are unclear or model is very new (2024-2025), leave EMPTY.
4. Append any NEWER **{{BRAND}}** models of the same class that are missing from the list for the ${country} market.
5. If a value is clearly invalid or missing, you MUST fill it based on Google Search results.

STRICT DATA SCHEMA (You MUST use these exact allowed values):

### NUMERIC FORMATTING RULES (CRITICAL):
1. **Watt, RPM, Voltage (if numeric)**:
   - Output **ONLY DIGITS**.
   - **NO UNITS** (e.g. write "1500", NOT "1500W").
   - **NO COMMAS** (e.g. write "2500", NOT "2,500").
   - Decimals are allowed.

2. **Blade Diameter**:
   - **ALWAYS CONVERT to MM** (Millimeters).
   - If source is in Inches (e.g. 10", 12"), convert to MM (e.g. 254, 305).
   - Output **INTEGER ONLY** (No decimals for MM).
   - Example: 10" -> 254; 8-1/4" -> 210.

3. **Rip Capacity, Max Depth of Cut**:
   - Output in MM.
   - If source is in Inches, convert to MM.

- Type (Table Saw style):
  * "1.Benchtop" = Benchtop/portable table saw, sits on a workbench or stand
  * "2.Floor" = Floor-standing/stationary machine with integrated stand or legs
  * "3.Multi Function" = Combination miter saw and table saw in one unit (flip-over/combi saws)

- Power Supply (Format: "Cordless [Voltage]" or leave empty for corded):
  * Examples: "Cordless 18V", "Cordless 18V2", "Cordless 36V", "Cordless 54V"
  * Leave EMPTY for AC corded tools

- Soft Start:
  * "Soft Start" = Has soft start feature
  * Leave EMPTY if no soft start

- Others (Comma-separated list of features, ONLY include features that are CONFIRMED):
  * "E Brake" = Electric Brake - Blade stops quickly after power off
  * "Speed Ctrl" = Variable Speed Control
  * "IoT" = Smart/Connected features - Bluetooth, WiFi, app connectivity
  * "Dado Compatible" = Accepts dado blades
  * "Mobile Base" = Includes mobile base with wheels
  * "Flesh Detection" = SawStop or similar flesh-detection technology
  
  IMPORTANT: 
  - Do NOT assume features that are not explicitly confirmed.
  - If unsure, do NOT include the feature.


IMPORTANT INSTRUCTIONS:
- Target Brand: **{{BRAND}}**
- Fill empty columns based on Model #.
- **"Released Year" ACCURACY IS CRITICAL: Only use verified data. Empty is better than wrong.**
- VERIFY existing values; only change if WRONG.
- Return a JSON object with:
   - "corrected": [ ... list of objects with SAME count as input ... ]
   - "new_items": [ ... list of new model objects ... ]

Output VALID JSON only.`,

   // Model 知識模式專用 Prompt (不使用 Google Search)
   systemPromptTemplateNoSearch: (type, country) => `Target Region: ${country}
Market Context: Focus on tool models, certifications, and market-specific standards (e.g., regional safety labels, voltage systems, and plug types) common in this region.

You are a data validation expert for ${type}.
**Use your built-in knowledge to verify and correct specifications. Do NOT make up values you are unsure about.**

Your task is to:
1. Review the input JSON list of tools.
2. **Use your training data knowledge to verify specifications** (Watt, Blade Diameter, RPM, Type, etc.):
   - Only fill values you are CONFIDENT about from your training data
   - If unsure, leave the field EMPTY rather than guessing
3. **"Released Year"** - Only fill if you are certain, otherwise leave EMPTY.
4. Do NOT invent new models. Only validate existing data.
5. Be conservative: if a value seems wrong but you're not 100% sure, keep the original.

STRICT DATA SCHEMA (You MUST use these exact allowed values):

### NUMERIC FORMATTING RULES (CRITICAL):
1. **Watt, RPM, Voltage (if numeric)**:
   - Output **ONLY DIGITS**.
   - **NO UNITS** (e.g. write "1500", NOT "1500W").
   - **NO COMMAS** (e.g. write "2500", NOT "2,500").
   - Decimals are allowed.

2. **Blade Diameter**:
   - **ALWAYS CONVERT to MM** (Millimeters).
   - If source is in Inches (e.g. 10", 12"), convert to MM (e.g. 254, 305).
   - Output **INTEGER ONLY** (No decimals for MM).

3. **Rip Capacity, Max Depth of Cut**:
   - Output in MM.

- Type (Table Saw style):
  * "1.Benchtop" = Benchtop/portable table saw, sits on a workbench or stand
  * "2.Floor" = Floor-standing/stationary machine with integrated stand or legs
  * "3.Multi Function" = Combination miter saw and table saw in one unit (flip-over/combi saws)

- Power Supply (Format: "Cordless [Voltage]" or leave empty for corded):
  * Examples: "Cordless 18V", "Cordless 36V", "Cordless 54V"
  * Leave EMPTY for AC corded tools

- Soft Start:
  * "Soft Start" = Has soft start feature
  * Leave EMPTY if no soft start

- Others (Comma-separated list of features, ONLY include features that are CONFIRMED):
  * "E Brake", "Speed Ctrl", "IoT", "Dado Compatible", "Mobile Base", "Flesh Detection"
  
  IMPORTANT: Do NOT assume features. If unsure, do NOT include.

IMPORTANT INSTRUCTIONS:
- Target Brand: **{{BRAND}}**
- Fill empty columns based on Model # ONLY if you are confident.
- **Be conservative: Empty is better than wrong.**
- Return a JSON object with:
   - "corrected": [ ... list of objects with SAME count as input ... ]
   - "new_items": [] (Do NOT add new items in Model-only mode)

Output VALID JSON only.`,

   // URL 模式專用 Prompt (造訪每筆資料的 Product URL 抓取規格)
   systemPromptTemplateUrl: (type, country) => `Target Region: ${country}
You are extracting specifications from product pages for ${type} products.

**IMPORTANT: Each item has a "_productUrl" field. Visit that URL to extract specifications.**

Your task:
1. For EACH item in the input JSON, visit its "_productUrl" to extract specifications.
2. Focus on these key specifications:
   - Watt (power)
   - Blade Diameter (in MM)
   - RPM (rotations per minute)
   - Type (1.Benchtop / 2.Floor / 3.Multi Function)
   - Rip Capacity (in MM)
   - Max Depth of Cut (in MM)
   - Power Supply (Cordless XXV or empty for corded)
   - Soft Start (if available)
   - Others (E Brake, Speed Ctrl, IoT, Dado Compatible, Mobile Base, Flesh Detection)
3. If a specification is NOT found on the page, leave it **EMPTY** (do not guess).
4. Extract the EXACT values from the page, converting units as needed:
   - Convert inches to MM for Blade Diameter, Rip Capacity, Depth of Cut
   - Remove units from Watt/RPM (just numbers)

### NUMERIC FORMATTING RULES:
1. **Watt, RPM**: Output ONLY DIGITS (e.g. "1500", NOT "1500W")
2. **Blade Diameter, Rip Capacity, Depth**: Convert to MM, INTEGER ONLY

Return a JSON object with:
- "corrected": [ ... list of objects with SAME count as input ... ]
- "new_items": []

Output VALID JSON only.`,

   defaultSchema: {
      "Type": ["1.Benchtop", "2.Floor", "3.Multi Function"],
      "Power Supply": ["Cordless 18V", "Cordless 18V2", "Cordless 36V", "Cordless 54V"]
   }
};

console.log("Loaded Prompt: Table Saw Validator");
