# Retry All Text Extraction Feature

## Overview
Added a "Retry All Text Extraction" button to the text extraction page that allows users to re-process all papers, including those that have already been successfully processed.

## Changes Made

### Frontend (Template)
- **File**: `src/papervisor/templates/text_extraction.html`
- Added a new "Retry All Extractions" button to the KPI dashboard
- Modified CSS to accommodate 6 items in the flexbox layout (reduced gap from 10px to 8px)
- Added JavaScript function `startRetryAll()` with confirmation dialog
- Updated `resetExtractionButton()` to handle both extract and retry buttons

### Backend (Web Server)
- **File**: `src/papervisor/web_server.py`
- Added new endpoint: `/retry_all_text_extraction` (POST)
- Added helper method: `_clear_extraction_status()` to remove previous status
- The retry process clears all extraction status and re-processes all downloaded papers

## User Experience
1. **Confirmation**: Users are prompted with "This will re-process ALL papers (including successful ones). Are you sure?"
2. **Progress**: Same progress tracking as the original extract function
3. **Status Reset**: All previous extraction statuses are cleared before starting
4. **Background Processing**: Uses the same threading mechanism as the original extraction

## Technical Details
- The retry functionality reuses the existing `_extract_texts_background()` method
- Clears the `extraction_status.json` file to force re-processing
- Both "Extract All" and "Retry All" buttons are disabled during processing
- Uses the same progress polling and UI updates as the original extraction

## Use Cases
- When extraction fails for multiple papers due to temporary issues
- When the extraction algorithm is improved and users want to re-extract all papers
- When users want to ensure all papers have the latest extraction format
- For troubleshooting extraction issues

## Button Styling
- **Extract All**: Blue button with cogs icon
- **Retry All**: Orange/warning button with redo icon
- Both buttons maintain the same size and layout as other KPI items
