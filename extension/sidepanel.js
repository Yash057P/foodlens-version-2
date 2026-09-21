// UI Elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const previewImg = document.getElementById('preview-img');

const loadingState = document.getElementById('loading-state');
const errorState = document.getElementById('error-state');
const errorMessage = document.getElementById('error-message');
const resultsState = document.getElementById('results-state');

const warningsContainer = document.getElementById('warnings-container');

// Result Elements
const leadName = document.getElementById('lead-name');
const leadProb = document.getElementById('lead-prob');
const nutritionCard = document.getElementById('nutrition-card');
const caloriesVal = document.getElementById('calories-val');
const allergensVal = document.getElementById('allergens-val');
const ingredientsVal = document.getElementById('ingredients-val');
const altPredictions = document.getElementById('alt-predictions');

// Initial load check
chrome.storage.local.get(['foodLensStatus', 'foodLensResult', 'foodLensImage', 'foodLensError'], (data) => {
  if (data.foodLensImage) showPreview(data.foodLensImage);
  handleStatusChange(data);
});

// Listen for updates from background script
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    const data = {};
    for (let [key, { newValue }] of Object.entries(changes)) {
      data[key] = newValue;
    }
    
    if (data.foodLensImage) showPreview(data.foodLensImage);
    
    // Merge existing data to handle partial updates
    chrome.storage.local.get(null, (fullData) => {
      handleStatusChange({ ...fullData, ...data });
    });
  }
});

// Handle Manual Upload
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const url = URL.createObjectURL(file);
  showPreview(url);
  
  await chrome.storage.local.set({ foodLensStatus: 'loading', foodLensResult: null, foodLensError: null });
  
  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch('http://localhost:5000/api/predict', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const result = await response.json();
    await chrome.storage.local.set({ foodLensStatus: 'success', foodLensResult: result });
  } catch (err) {
    await chrome.storage.local.set({ foodLensStatus: 'error', foodLensError: err.message });
  }
});

function showPreview(url) {
  previewImg.src = url;
  previewContainer.classList.remove('hidden');
  uploadZone.classList.add('hidden');
}

function handleStatusChange(data) {
  loadingState.classList.add('hidden');
  errorState.classList.add('hidden');
  resultsState.classList.add('hidden');
  warningsContainer.classList.add('hidden');

  if (data.foodLensStatus === 'loading') {
    loadingState.classList.remove('hidden');
    loadingState.classList.add('flex');
  } else if (data.foodLensStatus === 'error') {
    errorState.classList.remove('hidden');
    errorMessage.textContent = data.foodLensError || 'Unknown error occurred.';
  } else if (data.foodLensStatus === 'success' && data.foodLensResult) {
    renderResults(data.foodLensResult);
  }
}

function renderResults(res) {
  resultsState.classList.remove('hidden');
  
  // Render Lead
  const lead = res.top[0];
  leadName.textContent = lead.name;
  leadProb.textContent = `${(lead.prob * 100).toFixed(1)}%`;

  // Render Warnings
  if (res.warnings && res.warnings.length > 0) {
    warningsContainer.innerHTML = '';
    res.warnings.forEach(w => {
      const isErr = w.level === 'warning';
      const div = document.createElement('div');
      div.className = `p-3 rounded-lg text-sm border ${isErr ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-blue-50 border-blue-200 text-blue-800'}`;
      div.innerHTML = `<p class="font-semibold">${w.type.replace('_', ' ').toUpperCase()}</p><p class="opacity-90">${w.message}</p>`;
      warningsContainer.appendChild(div);
    });
    warningsContainer.classList.remove('hidden');
  }

  // Render Nutrition (only if not suppressed by warnings)
  const hasSevereWarning = res.warnings && res.warnings.some(w => w.level === 'warning');
  if (res.ingredients && !hasSevereWarning && Object.keys(res.ingredients).length > 0) {
    nutritionCard.classList.remove('hidden');
    caloriesVal.textContent = res.ingredients.calories ? `${res.ingredients.calories} kcal` : '--';
    
    // Allergens
    allergensVal.innerHTML = '';
    if (res.ingredients.allergens && res.ingredients.allergens.length > 0) {
      res.ingredients.allergens.forEach(a => {
        const span = document.createElement('span');
        span.className = 'text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-700';
        span.textContent = a;
        allergensVal.appendChild(span);
      });
    } else {
      allergensVal.innerHTML = '<span class="text-xs text-slate-400">None detected</span>';
    }

    // Ingredients
    ingredientsVal.textContent = res.ingredients.ingredients ? res.ingredients.ingredients.join(', ') : 'Unknown';
  } else {
    nutritionCard.classList.add('hidden');
  }

  // Render Alternatives
  altPredictions.innerHTML = '';
  res.top.slice(1).forEach(t => {
    const pPct = (t.prob * 100).toFixed(1);
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between text-sm';
    div.innerHTML = `
      <span class="text-slate-600 font-medium">${t.name}</span>
      <div class="flex items-center w-1/2">
        <div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden mr-2">
          <div class="h-full bg-slate-300 rounded-full" style="width: ${pPct}%"></div>
        </div>
        <span class="text-slate-400 text-xs w-8 text-right">${pPct}%</span>
      </div>
    `;
    altPredictions.appendChild(div);
  });
}

