const $ = (id) => document.getElementById(id);
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const HISTORY_KEY = 'foodlens.history';
const THEME_KEY = 'foodlens.theme';
const PROFILE_KEY = 'foodlens.profile';

// Always open the workspace at its intended landing position. Browsers often
// restore the previous scroll offset after a Docker rebuild or hard refresh.
if ('scrollRestoration' in window.history) {
  window.history.scrollRestoration = 'manual';
}
window.addEventListener('pageshow', () => window.scrollTo(0, 0));

// DOM Elements
const uploadZone = $('uploadZone');
const fileInput = $('fileInput');
const galleryInput = $('galleryInput');
const previewCard = $('previewCard');
const previewImg = $('previewImg');
const btnScan = $('btnScan');
const btnClear = $('btnClear');
const btnClosePreview = $('btnClosePreview');
const btnAgain = $('btnAgain');
const notice = $('notice');
const results = $('results');
const warningsBox = $('warnings');
const topPredictions = $('topPredictions');
const ingredientsCard = $('ingredientsCard');
const metaRow = $('metaRow');
const ingredientsList = $('ingredientsList');
const confidenceBadge = $('confidenceBadge');
const inferenceMeta = $('inferenceMeta');
const aiInsight = $('aiInsight');
const historyList = $('historyList');
const histCount = $('histCount');
const histEmpty = $('histEmpty');
const btnViva = $('btnViva');
const vivaPanel = $('vivaPanel');
const guardrailResult = $('guardrailResult');
const feedbackForm = $('feedbackForm');
const feedbackClass = $('feedbackClass');
const feedbackStatus = $('feedbackStatus');
const ttaToggle = $('ttaToggle');
const thresholdRange = $('thresholdRange');
const modelToolStatus = $('modelToolStatus');

// Camera elements
const cameraModal = $('cameraModal');
const cameraVideo = $('cameraVideo');
const cameraMsg = $('cameraMsg');
const fallbackInput = $('fallbackInput');
const btnSnap = $('btnSnap');
const btnCamClose = $('btnCamClose');
const btnFlip = $('btnFlip');
const btnCameraFallback = $('btnCameraFallback');

let selectedFile = null;
let stream = null;
let facing = 'environment';
let loading = false;
let history = loadHistory();
let foodProfile = loadFoodProfile();
let lastPrediction = null;

/* ========== THEME ========== */
$('themeToggle').addEventListener('click', toggleTheme);

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') === 'dark';
  const newTheme = cur ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  
  // Toggle icon visibility
  const moonIcon = document.querySelector('.icon-moon');
  const sunIcon = document.querySelector('.icon-sun');
  if (moonIcon && sunIcon) {
    moonIcon.classList.toggle('hidden', !cur);
    sunIcon.classList.toggle('hidden', cur);
  }
  
  try { localStorage.setItem(THEME_KEY, newTheme); } catch (e) {}
}

// Initialize theme icon
function initThemeIcon() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const moonIcon = document.querySelector('.icon-moon');
  const sunIcon = document.querySelector('.icon-sun');
  if (moonIcon && sunIcon) {
    moonIcon.classList.toggle('hidden', isDark);
    sunIcon.classList.toggle('hidden', !isDark);
  }
}
initThemeIcon();

/* ========== VIVA MODE + MODEL STATUS ========== */
if (btnViva && vivaPanel) {
  btnViva.addEventListener('click', () => {
    const opening = vivaPanel.classList.contains('hidden');
    vivaPanel.classList.toggle('hidden', !opening);
    btnViva.setAttribute('aria-expanded', String(opening));
    btnViva.classList.toggle('active', opening);
    if (opening) vivaPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

async function loadModelStatus() {
  try {
    const response = await fetch('/api/model');
    if (!response.ok) throw new Error('Model metadata unavailable');
    const model = await response.json();
    $('vivaReady').textContent = model.ready ? 'Service ready' : 'Warming up';
    $('vivaReady').classList.toggle('ready', Boolean(model.ready));
    $('factParameters').textContent = `${(model.parameters / 1_000_000).toFixed(2)}M`;
    $('factBackend').textContent = String(model.backend).toUpperCase();
    $('factThreshold').textContent = `${Math.round(model.confidence_threshold * 100)}%`;
  } catch (error) {
    $('vivaReady').textContent = 'Status unavailable';
  }
}

loadModelStatus();
thresholdRange.addEventListener('input', () => {
  $('thresholdValue').textContent = `${thresholdRange.value}%`;
});

/* ========== NAVIGATION ========== */
const pages = ['scan', 'history', 'profile', 'evaluation', 'about'];

document.querySelectorAll('.nav-item').forEach((btn) => {
  btn.addEventListener('click', () => { 
    closeDrawer(); 
    navigate(btn.dataset.page); 
  });
});

$('btnBack').addEventListener('click', () => navigate('scan'));
$('btnMenu').addEventListener('click', openDrawer);
$('drawerOverlay').addEventListener('click', closeDrawer);
$('btnDrawerClose').addEventListener('click', closeDrawer);
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

function openDrawer() {
  $('drawer').classList.remove('hidden');
  $('drawerOverlay').classList.remove('hidden');
}

function closeDrawer() {
  $('drawer').classList.add('hidden');
  $('drawerOverlay').classList.add('hidden');
}

function navigate(page) {
  pages.forEach((p) => { 
    const pageEl = $(`page-${p}`);
    if (pageEl) pageEl.classList.toggle('hidden', p !== page);
  });
  
  document.querySelectorAll('.nav-item').forEach((b) => {
    b.classList.toggle('active', b.dataset.page === page);
  });
  
  const titles = { scan: 'Discover', history: 'Tasting history', profile: 'Food profile', evaluation: 'Model evaluation', about: 'About FoodLens' };
  $('topbarTitle').textContent = titles[page];
  $('btnBack').style.visibility = page === 'scan' ? 'hidden' : 'visible';
  
  if (page === 'history') renderHistory();
  if (page === 'profile') renderFoodProfile();
  if (page === 'evaluation') renderEvaluation();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

$('btnBack').style.visibility = 'hidden';

/* ========== UPLOAD ========== */
uploadZone.addEventListener('click', (e) => {
  if (e.target.closest('button')) return;
  fileInput.click();
});

fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
galleryInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
$('btnGallery').addEventListener('click', (e) => { e.stopPropagation(); galleryInput.click(); });
fallbackInput.addEventListener('change', (e) => { 
  closeCamera();
  handleFile(e.target.files[0]); 
});
btnCameraFallback.addEventListener('click', () => fallbackInput.click());

document.querySelectorAll('.demo-sample').forEach((button) => {
  button.addEventListener('click', async () => {
    if (loading) return;
    const src = button.dataset.sampleSrc;
    const label = button.dataset.sampleLabel || 'Food-101 sample';
    button.classList.add('is-loading');
    try {
      const response = await fetch(src);
      if (!response.ok) throw new Error('The demo image could not be loaded.');
      const blob = await response.blob();
      const filename = src.split('/').pop() || 'food101-demo.jpg';
      handleFile(new File([blob], filename, { type: blob.type || 'image/jpeg' }));
      previewImg.alt = `${label} Food-101 demo sample`;
      previewCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
      showNotice(error.message || 'The demo image could not be loaded.', true);
    } finally {
      button.classList.remove('is-loading');
    }
  });
});

uploadZone.ondragover = (e) => { e.preventDefault(); uploadZone.classList.add('over'); };
uploadZone.ondragleave = () => uploadZone.classList.remove('over');
uploadZone.ondrop = (e) => {
  e.preventDefault(); 
  uploadZone.classList.remove('over');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
};

// Close preview button
if (btnClosePreview) {
  btnClosePreview.addEventListener('click', resetScan);
}

function handleFile(file) {
  if (!file) return;
  if (!file.type.startsWith('image/')) { 
    showNotice('Please choose an image file (JPEG, PNG, or WebP).', true); 
    return; 
  }
  if (file.size > MAX_SIZE_BYTES) { 
    showNotice('Image is too large. Maximum size is 10 MB.', true); 
    return; 
  }
  
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  uploadZone.classList.add('hidden');
  previewCard.classList.remove('hidden');
  notice.classList.add('hidden');
  results.classList.add('hidden');
}

/* ========== CAMERA ========== */
$('btnCamera').addEventListener('click', openCamera);
btnCamClose.addEventListener('click', closeCamera);
btnFlip.addEventListener('click', () => {
  facing = facing === 'environment' ? 'user' : 'environment';
  openCamera();
});
btnSnap.addEventListener('click', captureFrame);
window.addEventListener('pagehide', closeCamera);

async function openCamera() {
  cameraMsg.classList.add('hidden');
  btnCameraFallback.classList.add('hidden');
  btnSnap.classList.remove('hidden');
  cameraModal.classList.remove('hidden');
  
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: { ideal: facing }, 
          width: { ideal: 1920 }, 
          height: { ideal: 1080 } 
        },
        audio: false,
      });
      
      cameraVideo.srcObject = stream;
      await cameraVideo.play().catch(() => {});
      cameraModal.classList.remove('hidden');
      return;
    } catch (err) {
      console.warn('Camera access failed:', err);
      const permissionDenied = err && (err.name === 'NotAllowedError' || err.name === 'SecurityError');
      showCameraMsg(permissionDenied
        ? 'Camera permission was denied. Allow camera access in your browser settings, or choose a photo instead.'
        : 'The camera is unavailable on this device or browser. Choose a photo instead.');
    }
  } else {
    showCameraMsg(window.isSecureContext
      ? 'This browser does not provide camera access. Choose a photo instead.'
      : 'Camera access requires HTTPS or localhost. Open the secure site or choose a photo instead.');
  }

  btnSnap.classList.add('hidden');
  btnCameraFallback.classList.remove('hidden');
}

function captureFrame() {
  const v = cameraVideo;
  if (!v || v.readyState < 2 || !v.videoWidth) return;
  
  const canvas = document.createElement('canvas');
  canvas.width = v.videoWidth;
  canvas.height = v.videoHeight;
  const ctx = canvas.getContext('2d');
  
  ctx.save();
  if (facing === 'user') { 
    ctx.translate(canvas.width, 0); 
    ctx.scale(-1, 1); 
  }
  ctx.drawImage(v, 0, 0);
  ctx.restore();
  
  canvas.toBlob((blob) => {
    if (!blob) return;
    const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
    closeCamera();
    handleFile(file);
    // Auto-analyze after capture
    setTimeout(() => analyze(false), 300);
  }, 'image/jpeg', 0.95);
}

function closeCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
  }
  stream = null;
  cameraVideo.srcObject = null;
  cameraModal.classList.add('hidden');
}

function showCameraMsg(msg) { 
  cameraMsg.textContent = msg; 
  cameraMsg.classList.remove('hidden'); 
}

async function readJsonResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const body = await response.text();
  if (contentType.includes('application/json') && body) {
    try {
      return JSON.parse(body);
    } catch (_error) {
      // Continue to an actionable server message below.
    }
  }
  if (!response.ok) {
    if ([502, 503, 504].includes(response.status)) {
      throw new Error('The hosted AI service is restarting or temporarily out of capacity. Wait about a minute and try again.');
    }
    throw new Error(`The server returned an invalid response (HTTP ${response.status}).`);
  }
  throw new Error('The server returned an empty or invalid response. Please try again.');
}

/* ========== ANALYZE ========== */
btnScan.addEventListener('click', () => analyze(false));
btnClear.addEventListener('click', resetScan);
btnAgain.addEventListener('click', resetScan);

async function analyze(silent) {
  if (!selectedFile || loading) return;
  
  loading = true;
  btnScan.disabled = true;
  
  const btnLabel = btnScan.querySelector('.btn-label');
  const btnLoader = btnScan.querySelector('.btn-loader');
  
  if (btnLabel) btnLabel.classList.add('hidden');
  if (btnLoader) btnLoader.classList.remove('hidden');
  
  if (!silent) { 
    results.classList.add('hidden'); 
    notice.classList.add('hidden'); 
  }

  const form = new FormData();
  form.append('image', selectedFile);
  form.append('tta', String(ttaToggle.checked));
  form.append('threshold', String(Number(thresholdRange.value) / 100));
  
  try {
    const res = await fetch('/api/predict', { method: 'POST', body: form });
    const data = await readJsonResponse(res);
    
    if (!res.ok || data.status !== 'ok') {
      throw new Error(data.message || 'Server error occurred');
    }
    
    renderResults(data);
    addToHistory(data);
  } catch (err) {
    showNotice(err.message || 'Failed to analyze image. Please try again.', true);
  } finally {
    loading = false;
    btnScan.disabled = false;
    
    if (btnLabel) btnLabel.classList.remove('hidden');
    if (btnLoader) btnLoader.classList.add('hidden');
  }
}

function renderResults(data) {
  lastPrediction = data;
  results.classList.remove('hidden');
  warningsBox.innerHTML = '';

  const runtime = data.inference || {};
  if (inferenceMeta) {
    inferenceMeta.innerHTML = [
      `<span><b>${escapeHtml(runtime.model || 'EfficientNetB0')}</b> CNN architecture</span>`,
      `<span><b>${Number(runtime.tta_views || 3)}-view TTA</b> probability ensemble</span>`,
      `<span><b>${Number(runtime.latency_ms || 0).toFixed(1)} ms</b> inference time</span>`,
    ].join('');
  }
  
  // Render warnings
  (data.warnings || []).forEach((w) => {
    const div = document.createElement('div');
    div.className = `warn ${w.level}`;
    div.innerHTML = `<strong>${w.level === 'warning' ? 'Check' : 'Note'}</strong> ${escapeHtml(w.message)}`;
    warningsBox.appendChild(div);
  });

  // Render predictions
  topPredictions.innerHTML = '';
  (data.top || []).forEach((p) => {
    const pct = Math.round(p.prob * 100);
    const row = document.createElement('div');
    row.className = 'pred-row';
    row.innerHTML = `
      <span class="pred-rank">${p.rank}</span>
      <div class="pred-bar-wrap">
        <div class="pred-bar r${p.rank}" style="width:0%"></div>
        <span class="pred-label">${escapeHtml(p.name)}</span>
      </div>
      <span class="pred-pct">${pct}%</span>`;
    topPredictions.appendChild(row);
    
    // Animate bar
    requestAnimationFrame(() => { 
      const bar = row.querySelector('.pred-bar');
      if (bar) bar.style.width = pct + '%'; 
    });
  });

  // Update confidence badge
  if (data.top && data.top[0]) {
    const conf = Math.round(data.top[0].prob * 100);
    const gap = data.top[1] ? Math.round((data.top[0].prob - data.top[1].prob) * 100) : conf;
    if (confidenceBadge) {
      confidenceBadge.textContent = `${conf}% confidence`;
      confidenceBadge.style.background = conf >= 70 ? 'var(--success-soft)' : conf >= 50 ? 'var(--warn-soft)' : 'var(--danger-soft)';
      confidenceBadge.style.color = conf >= 70 ? 'var(--success)' : conf >= 50 ? 'var(--warn)' : 'var(--danger)';
    }
    if (aiInsight) {
      const interpretation = conf >= 70
        ? 'The model found a strong visual match.'
        : conf >= 45
          ? 'The model found a possible match, but visual evidence is moderate.'
          : 'The model is uncertain, so treat all matches as suggestions.';
      const entropy = Number(data.uncertainty?.normalized_entropy || 0);
      aiInsight.innerHTML = `<b>Model assessment:</b> ${interpretation} The lead is <strong>${escapeHtml(data.top[0].name)}</strong> at ${conf}%, with a ${gap}-point margin over the next class. Normalized entropy is ${entropy.toFixed(3)} (${escapeHtml(data.uncertainty?.interpretation || 'unknown')} uncertainty).`;
      aiInsight.className = `ai-insight ${conf >= 70 ? 'strong' : conf >= 45 ? 'moderate' : 'uncertain'}`;
    }
  }

  // Render nutrition info
  const info = data.ingredients || {};
  const ings = info.ingredients || [];
  const cals = info.calories || null;
  const allergens = (info.allergens || []).filter((a) => a);
  renderGuardrails(info);
  configureNearbyLink(data.lead_name || data.top?.[0]?.name || 'food');
  resetFeedbackControls();
  
  metaRow.innerHTML = '';
  if (cals) {
    metaRow.innerHTML += `<span class="meta-pill">Estimated: ~${cals} kcal</span>`;
  }
  if (allergens.length) {
    metaRow.innerHTML += `<span class="meta-pill allergens">May contain: ${allergens.map(escapeHtml).join(', ')}</span>`;
  }
  
  ingredientsList.innerHTML = ings.length 
    ? ings.map((i) => `<span class="ing-tag">${escapeHtml(i)}</span>`).join('')
    : '<span style="color: var(--muted); font-size: 0.85rem;">No ingredient data available</span>';
  
  ingredientsCard.classList.remove('hidden');
  
  // Smooth scroll to results
  setTimeout(() => {
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);
}

function showNotice(msg, isError) {
  notice.textContent = msg;
  notice.className = 'notice' + (isError ? ' error' : '');
  notice.classList.remove('hidden');
}

function resetScan() {
  selectedFile = null;
  previewImg.src = '';
  uploadZone.classList.remove('hidden');
  previewCard.classList.add('hidden');
  notice.classList.add('hidden');
  results.classList.add('hidden');
  ingredientsCard.classList.add('hidden');
  
  // Clear predictions
  if (topPredictions) topPredictions.innerHTML = '';
  if (metaRow) metaRow.innerHTML = '';
  if (ingredientsList) ingredientsList.innerHTML = '';
  if (warningsBox) warningsBox.innerHTML = '';
  if (aiInsight) aiInsight.innerHTML = '';
  if (guardrailResult) guardrailResult.classList.add('hidden');
  $('gradcamResult').classList.add('hidden');
  $('ttaComparison').classList.add('hidden');
  modelToolStatus.textContent = '';
}

/* ========== EXPLAINABILITY + MODEL COMPARISON ========== */
$('btnGradcam').addEventListener('click', async () => {
  if (!selectedFile || !lastPrediction?.top?.[0]) return;
  modelToolStatus.textContent = 'Computing Grad-CAM from the EfficientNet feature map...';
  const form = new FormData();
  form.append('image', selectedFile);
  form.append('class', lastPrediction.top[0].class);
  try {
    const response = await fetch('/api/explain', { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Grad-CAM failed.');
    $('gradcamImage').src = data.overlay;
    $('gradcamCaption').textContent = `${data.method} for ${data.class.replaceAll('_', ' ')} using ${data.layer}. Warm colours contributed more strongly to this class score.`;
    $('gradcamResult').classList.remove('hidden');
    modelToolStatus.textContent = 'Grad-CAM generated from the deployed model.';
  } catch (error) {
    modelToolStatus.textContent = error.message;
  }
});

$('btnCompareTta').addEventListener('click', async () => {
  if (!selectedFile) return;
  modelToolStatus.textContent = 'Running single-view and three-view inference...';
  const form = new FormData();
  form.append('image', selectedFile);
  try {
    const response = await fetch('/api/compare-tta', { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'TTA comparison failed.');
    const single = data.single.top[0];
    const ensemble = data.ensemble.top[0];
    $('ttaComparison').innerHTML = `
      <div><span>Single view</span><b>${escapeHtml(single.name)} | ${Math.round(single.prob * 100)}%</b><small>${data.single.latency_ms.toFixed(1)} ms | entropy ${data.single.uncertainty.normalized_entropy.toFixed(3)}</small></div>
      <div><span>3-view TTA</span><b>${escapeHtml(ensemble.name)} | ${Math.round(ensemble.prob * 100)}%</b><small>${data.ensemble.latency_ms.toFixed(1)} ms | entropy ${data.ensemble.uncertainty.normalized_entropy.toFixed(3)}</small></div>`;
    $('ttaComparison').classList.remove('hidden');
    modelToolStatus.textContent = 'Comparison complete. TTA trades extra computation for multi-view averaging.';
  } catch (error) {
    modelToolStatus.textContent = error.message;
  }
});

$('btnDownloadReport').addEventListener('click', () => {
  if (!lastPrediction) return;
  const report = {
    generated_at: new Date().toISOString(),
    image_name: selectedFile?.name || 'camera-capture',
    model: lastPrediction.inference,
    predictions: lastPrediction.top,
    uncertainty: lastPrediction.uncertainty,
    image_quality: lastPrediction.image_quality,
    warnings: lastPrediction.warnings,
    food_details: lastPrediction.ingredients,
    applied_profile: foodProfile,
    disclaimer: 'Educational decision support only. Verify ingredients and allergens directly.',
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `foodlens-report-${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
  modelToolStatus.textContent = 'Prediction report downloaded.';
});

/* ========== PERSONAL FOOD PROFILE ========== */
function loadFoodProfile() {
  try {
    const parsed = JSON.parse(localStorage.getItem(PROFILE_KEY) || '{}');
    return {
      allergies: Array.isArray(parsed.allergies) ? parsed.allergies : [],
      diets: Array.isArray(parsed.diets) ? parsed.diets : [],
      saved: Boolean(parsed.saved),
    };
  } catch (error) {
    return { allergies: [], diets: [], saved: false };
  }
}

function renderFoodProfile() {
  document.querySelectorAll('input[name="allergy"]').forEach((input) => {
    input.checked = foodProfile.allergies.includes(input.value);
  });
  document.querySelectorAll('input[name="diet"]').forEach((input) => {
    input.checked = foodProfile.diets.includes(input.value);
  });
  $('profileStatus').textContent = foodProfile.saved
    ? `${foodProfile.allergies.length} allergy concern(s), ${foodProfile.diets.length} preference(s) saved locally.`
    : 'No profile saved yet.';
}

$('btnSaveProfile').addEventListener('click', () => {
  foodProfile = {
    allergies: [...document.querySelectorAll('input[name="allergy"]:checked')].map((input) => input.value),
    diets: [...document.querySelectorAll('input[name="diet"]:checked')].map((input) => input.value),
    saved: true,
  };
  localStorage.setItem(PROFILE_KEY, JSON.stringify(foodProfile));
  renderFoodProfile();
  $('profileStatus').textContent = 'Food profile saved on this device.';
});

const DIET_TERMS = {
  vegan: ['beef', 'pork', 'chicken', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'egg', 'milk', 'cream', 'cheese', 'butter', 'yogurt', 'honey'],
  vegetarian: ['beef', 'pork', 'chicken', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster'],
  keto: ['bread', 'rice', 'pasta', 'noodle', 'flour', 'sugar', 'potato', 'tortilla', 'pastry', 'crust', 'syrup'],
};

function renderGuardrails(info) {
  if (!guardrailResult) return;
  if (!foodProfile.saved || (!foodProfile.allergies.length && !foodProfile.diets.length)) {
    guardrailResult.className = 'guardrail-result neutral';
    guardrailResult.innerHTML = '<b>No food profile applied.</b> Add allergy concerns or eating preferences for personalized flags. <button type="button" id="openProfile">Set profile</button>';
    guardrailResult.classList.remove('hidden');
    $('openProfile').addEventListener('click', () => navigate('profile'));
    return;
  }
  const allergens = (info.allergens || []).map((item) => String(item).toLowerCase());
  const ingredients = (info.ingredients || []).map((item) => String(item).toLowerCase());
  const allergyHits = foodProfile.allergies.filter((choice) =>
    allergens.some((item) => item.includes(choice) || (choice === 'peanuts' && item === 'nuts'))
  );
  const dietHits = [];
  foodProfile.diets.forEach((diet) => {
    const matches = (DIET_TERMS[diet] || []).filter((term) => ingredients.some((ingredient) => ingredient.includes(term)));
    if (matches.length) dietHits.push(`${diet}: ${[...new Set(matches)].slice(0, 3).join(', ')}`);
  });
  if (allergyHits.length) {
    guardrailResult.className = 'guardrail-result danger';
    guardrailResult.innerHTML = `<b>Possible allergy concern:</b> ${allergyHits.map(escapeHtml).join(', ')}. Do not rely on image recognition for allergen safety; verify directly.`;
  } else if (dietHits.length) {
    guardrailResult.className = 'guardrail-result caution';
    guardrailResult.innerHTML = `<b>Possible profile conflict:</b> ${dietHits.map(escapeHtml).join(', ')}. Recipes vary, so confirm before ordering.`;
  } else {
    guardrailResult.className = 'guardrail-result safe';
    guardrailResult.innerHTML = '<b>No profile conflicts found in the reference entry.</b> This does not prove the dish is safe or compliant; recipes and cross-contact vary.';
  }
  guardrailResult.classList.remove('hidden');
}

/* ========== ACTIVE-LEARNING FEEDBACK ========== */
async function loadFeedbackClasses() {
  try {
    const response = await fetch('/api/classes');
    const data = await response.json();
    const names = Object.values(data.index_to_name || {}).sort();
    feedbackClass.innerHTML = names.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name.replaceAll('_', ' '))}</option>`).join('');
  } catch (error) {
    feedbackStatus.textContent = 'Correction choices could not be loaded.';
  }
}

function resetFeedbackControls() {
  feedbackForm.classList.add('hidden');
  feedbackStatus.textContent = '';
  $('btnFeedbackCorrect').disabled = false;
  $('btnFeedbackWrong').disabled = false;
  $('shareFeedbackImage').checked = false;
}

async function submitFeedback(correctedClass) {
  if (!lastPrediction?.top?.[0]) return;
  const lead = lastPrediction.top[0];
  feedbackStatus.textContent = 'Saving feedback...';
  try {
    const shareImage = $('shareFeedbackImage').checked && selectedFile;
    let requestOptions;
    if (shareImage) {
      const form = new FormData();
      form.append('predicted_class', lead.class);
      form.append('corrected_class', correctedClass);
      form.append('confidence', String(lead.prob));
      form.append('source', 'user');
      form.append('image', selectedFile);
      requestOptions = { method: 'POST', body: form };
    } else {
      requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ predicted_class: lead.class, corrected_class: correctedClass, confidence: lead.prob, source: 'user' }),
      };
    }
    const response = await fetch('/api/feedback', requestOptions);
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Feedback could not be saved.');
    feedbackStatus.textContent = data.message;
    feedbackForm.classList.add('hidden');
    $('btnFeedbackCorrect').disabled = true;
    $('btnFeedbackWrong').disabled = true;
  } catch (error) {
    feedbackStatus.textContent = error.message;
  }
}

$('btnFeedbackCorrect').addEventListener('click', () => submitFeedback(lastPrediction?.top?.[0]?.class));
$('btnFeedbackWrong').addEventListener('click', () => feedbackForm.classList.toggle('hidden'));
$('btnFeedbackSubmit').addEventListener('click', () => submitFeedback(feedbackClass.value));
loadFeedbackClasses();

/* ========== NEARBY DISCOVERY ========== */
function configureNearbyLink(dishName) {
  const query = encodeURIComponent(`best ${dishName} near me`);
  $('findNearby').href = `https://www.google.com/maps/search/?api=1&query=${query}`;
  $('findNearby').setAttribute('aria-label', `Find highly rated ${dishName} nearby on Google Maps`);
}

/* ========== HELD-OUT EVALUATION ========== */
let evaluationLoaded = false;
async function renderEvaluation() {
  if (evaluationLoaded) return;
  try {
    const response = await fetch('/api/evaluation');
    const data = await response.json();
    if (!response.ok) throw new Error('Evaluation evidence unavailable.');
    $('evaluationProvenance').textContent = `${data.provenance} Test images: ${data.test_images.toLocaleString()}.`;
    const metrics = [
      ['Top-1', data.metrics.top1], ['Top-3', data.metrics.top3], ['Top-5', data.metrics.top5], ['Macro F1', data.metrics.macro_f1],
    ];
    $('evaluationMetrics').innerHTML = metrics.map(([label, value]) => `<div><span>${label}</span><b>${(value * 100).toFixed(2)}%</b></div>`).join('');
    $('worstClasses').innerHTML = data.worst_classes.map(([name, value]) => `<div class="evaluation-row"><span>${escapeHtml(name.replaceAll('_', ' '))}</span><b>${(value * 100).toFixed(1)}%</b></div>`).join('');
    $('confusionPairs').innerHTML = data.confusions.map(([truth, predicted, count]) => `<div class="evaluation-row"><span>${escapeHtml(truth.replaceAll('_', ' '))} predicted as ${escapeHtml(predicted.replaceAll('_', ' '))}</span><b>${count}</b></div>`).join('');
    $('ttaTable').querySelector('tbody').innerHTML = data.tta_ablation.map((row) => `<tr><td>${escapeHtml(row.configuration)}</td><td>${row.views}</td><td>${row.latency_ms.toFixed(2)} ms</td><td>${(row.top1 * 100).toFixed(2)}%</td></tr>`).join('');
    const calibration = data.calibration;
    const calibrationHtml = calibration.status === 'fitted'
      ? `<h3>Temperature fitted on ${calibration.fit_samples.toLocaleString()} development images</h3><p>On ${calibration.samples.toLocaleString()} untouched test images, temperature ${calibration.temperature.toFixed(3)} reduced ECE from ${(calibration.ece_before * 100).toFixed(2)}% to ${(calibration.ece_after * 100).toFixed(2)}%, and NLL from ${calibration.nll_before.toFixed(3)} to ${calibration.nll_after.toFixed(3)}.</p>`
      : `<h3>Softmax scores are not calibrated</h3><p>${escapeHtml(calibration.reason)}</p>`;
    $('calibrationCard').innerHTML = `<span class="action-kicker">Calibration status</span>${calibrationHtml}<p><strong>Architecture comparison:</strong> ${escapeHtml(data.architecture_comparison.note)}</p>`;
    evaluationLoaded = true;
  } catch (error) {
    $('evaluationProvenance').textContent = error.message;
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ 
    '&': '&amp;', 
    '<': '&lt;', 
    '>': '&gt;', 
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

/* ========== HISTORY ========== */
function loadHistory() {
  try { 
    const raw = localStorage.getItem(HISTORY_KEY); 
    const p = raw ? JSON.parse(raw) : []; 
    return Array.isArray(p) ? p : []; 
  } catch (e) { 
    return []; 
  }
}

function addToHistory(data) {
  const thumb = previewImg.src;
  history.unshift({
    id: Date.now(),
    food: data.lead_name || 'Unknown',
    conf: data.top && data.top[0] ? Math.round(data.top[0].prob * 100) : 0,
    thumb,
    ts: Date.now(),
  });
  
  // Keep only last 24 items
  history = history.slice(0, 24);
  
  try { 
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); 
  } catch (e) {}
}

function renderHistory() {
  if (!histCount || !histEmpty || !historyList) return;
  
  histCount.textContent = history.length 
    ? `${history.length} scan${history.length > 1 ? 's' : ''}` 
    : 'No scans';
    
  histEmpty.classList.toggle('hidden', history.length > 0);
  
  if (history.length === 0) {
    historyList.innerHTML = '';
    return;
  }
  
  historyList.innerHTML = history.map((h) => `
    <div class="hist-item">
      <img class="hist-thumb" src="${escapeHtml(h.thumb)}" alt="${escapeHtml(h.food)}"/>
      <div class="hist-info">
        <div class="hist-food">${escapeHtml(h.food)}</div>
        <div class="hist-sub">${h.conf}% | ${formatDate(h.ts)}</div>
      </div>
      <button class="hist-del" data-id="${h.id}" aria-label="Delete entry">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>`).join('');
    
  // Add delete handlers
  historyList.querySelectorAll('.hist-del').forEach((b) => {
    b.addEventListener('click', () => {
      const id = Number(b.dataset.id);
      history = history.filter((x) => x.id !== id);
      try { 
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); 
      } catch (e) {}
      renderHistory();
    });
  });
}

function formatDate(ts) {
  const date = new Date(ts);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}

const btnClearHist = $('btnClearHist');
if (btnClearHist) {
  btnClearHist.addEventListener('click', () => { 
    if (history.length === 0) return;
    if (confirm('Are you sure you want to clear all scan history?')) {
      history = []; 
      try { 
        localStorage.setItem(HISTORY_KEY, '[]'); 
      } catch (e) {}
      renderHistory();
    }
  });
}

// Initialize
navigate('scan');
requestAnimationFrame(() => window.scrollTo(0, 0));
