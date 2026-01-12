# Pivot Chart Analysis Feature Walkthrough

We have successfully added a new **Pivot Chart Analysis** view to the PT Landscape application. This feature allows for dynamic data analysis using nested row grouping and customizable data columns.

## Feature Overview

### 1. New View Tab
A new "Pivot Analysis" tab has been added to the main view switcher.

### 2. Pivot Configuration
- **Row Grouping**:
  - Support for up to 4 levels of nesting (Main, Sub, L3, L4).
  - Select fields like `Brand`, `Platform`, etc.
- **Data Columns**:
  - Dynamic addition of multiple data columns.
  - **Fields**: proper selection of any data field.
  - **Aggregations**:
    - `COUNT`, `UNIQUE`
    - `SUM`, `AVG`, `MAX`, `MIN`
    - `MEDIAN`, `STDEV`, `VAR`
    - `X%` (Percentage of specific value)
  - **Formatting**: Custom format strings (e.g., `#,##0 元`).

### 3. Dynamic Table Generation
The table automatically updates when configurations change, showing:
- Hierarchical row labels with indentation.
- "count" column for group size.
- Calculated metrics for each column.
- Recursive totals and subtotals.

## Verification

We verified the feature using browser automation:
1.  **UI Structure**: Confirmed the presence of the new tab and configuration panels.
2.  **Logic Logic**:
    - Select "Brand" as Main Group.
    - Add "Price" column with "Average" aggregation.
    - Verified that the table renders correctly with calculated values.

### Screenshots
![Pivot Analysis UI](/pivot_analysis_test_final_1767687384420.png)

## Integration Details
- **Data Source**: Uses the same filtered dataset as the Grid and Scatter views (`filteredData`).
- **Initialization**: detailed controls are initialized automatically when data is loaded.

## Next Steps

## Debugging Notes (2025/01/06)
- **Google Sheets Loading Fix**:
  - Problem: `initPivotControls` was undefined due to scope issues, causing `initApp` to crash.
  - Fix: Moved Pivot Analysis functions into the main script block.
- **Auto-Load Restoration**:
  - Problem: Auto-load was disabled during debugging, causing UI to feel "dead" until manual load.
  - Fix: Modified `initApp` to automatically call `loadAllData()` when the file list is retrieved.
- **Robustness**:
  - Added timeout (10s) and abort controller to `fetchFileList` to prevent indefinite hanging.
  - `fetchSheetsBtn` (Refresh) now reloads the file list as well.
