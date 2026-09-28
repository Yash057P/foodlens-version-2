# Chrome Web Store Listing: FoodLens AI

## Overview
- **Name:** FoodLens AI
- **Summary:** Identify food and get nutrition/allergen info instantly.
- **Version:** 1.0.0
- **Last Updated:** 2026-09-21

## Store Listing Details

### Description
FoodLens AI is a smart, privacy-first food recognition tool that helps you instantly identify dishes right from your browser. 

Whether you're browsing recipes, checking out a restaurant menu online, or reading food blogs, FoodLens AI makes it easy to understand what you're looking at. With a simple right-click or by dragging and dropping an image into the side panel, the extension instantly analyzes the food photo and provides:
- The top predicted dish name.
- Estimated calories per typical serving.
- A list of common recipe ingredients.
- Important allergen flags (e.g., dairy, gluten, nuts).

FoodLens AI features a beautiful, non-intrusive side panel that stays out of your way while you browse. It also includes smart confidence warnings, letting you know if an image is too blurry or ambiguous to identify accurately. 

### Category
- Productivity / Tools

## Permissions & Justifications

### Extension Permissions
- **`sidePanel`**: Required to display the main user interface (the FoodLens analysis panel) alongside the user's active browsing session without disrupting their workflow.
- **`contextMenus`**: Required to add the "Analyze Food with FoodLens" option to the right-click menu, allowing users to select an image directly from any webpage.
- **`storage`**: Required to temporarily store the results of the latest image analysis and the analysis state (loading/success/error) so the side panel can read and display the results properly.
- **`notifications`**: Required to alert the user if an image analysis fails (e.g., if the backend server is unreachable) and the side panel isn't open.

### Host Permissions
- **`<all_urls>`**: Required to fetch the image bytes from the user's selected webpage when they right-click and choose to analyze an image. The extension does not read page text or data, only the specific image URL selected by the user.
- **`http://localhost:5000/*`**: Required to send the image data to the local FoodLens deep learning backend for analysis. *(Note: Update to production domain before final release).*

## Privacy & Data Use

### Data Collection
- **Image Data:** The extension only processes images explicitly selected by the user (via right-click context menu or manual upload). Images are sent securely to the prediction API and are never permanently stored or used for secondary purposes.
- **Analytics/Tracking:** None.
- **Personally Identifiable Information:** None.

## Version History
- **1.0.0 (2026-09-21)**: Initial release. Added side panel UI, drag-and-drop upload, right-click context menu integration, and integration with the FoodLens backend API for Top-3 predictions and nutrition retrieval.

