chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'analyze-food',
    title: 'Analyze Food with FoodLens',
    contexts: ['image']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyze-food') {
    analyzeImage(info.srcUrl, tab);
  }
});

async function analyzeImage(imageUrl, tab) {
  try {
    // Open the side panel for the user immediately to show loading state
    await chrome.sidePanel.open({ windowId: tab.windowId });
    await chrome.storage.local.set({ foodLensStatus: 'loading', foodLensResult: null, foodLensImage: imageUrl });

    // Fetch the image as a Blob
    const response = await fetch(imageUrl);
    const blob = await response.blob();

    // Prepare form data for the Flask API
    const formData = new FormData();
    formData.append('image', blob, 'image.jpg');

    // Call the local FoodLens Flask API
    const apiResponse = await fetch('http://localhost:5000/api/predict', {
      method: 'POST',
      body: formData
    });

    if (!apiResponse.ok) {
      throw new Error(`API error: ${apiResponse.statusText}`);
    }

    const result = await apiResponse.json();
    
    // Save to storage (the side panel listens to this)
    await chrome.storage.local.set({ foodLensStatus: 'success', foodLensResult: result });
    
  } catch (err) {
    console.error('FoodLens Analysis Failed:', err);
    await chrome.storage.local.set({ foodLensStatus: 'error', foodLensError: err.message });
    
    // Notification fallback
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCI+PGNpcmNsZSBjeD0iMjQiIGN5PSIyNCIgcj0iMjQiIGZpbGw9IiNGRjAwMDAiLz48L3N2Zz4=', // red circle
      title: 'FoodLens Error',
      message: 'Failed to analyze image. Is the Flask server running on port 5000?'
    });
  }
}
