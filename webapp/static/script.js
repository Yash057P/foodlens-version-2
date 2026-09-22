const $ = (id) => document.getElementById(id);
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const HISTORY_KEY = 'foodlens.history';
const THEME_KEY = 'foodlens.theme';

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
const historyList = $('historyList');
const histCount = $('histCount');
const histEmpty = $('histEmpty');

// Camera elements
const cameraModal = $('cameraModal');
const cameraVideo = $('cameraVideo');
const cameraMsg = $('cameraMsg');
const fallbackInput = $('fallbackInput');
const btnSnap = $('btnSnap');
const btnCamClose = $('btnCamClose');
const btnFlip = $('btnFlip');

let selectedFile = null;
let stream = null;
let facing = 'environment';
let loading = false;
let history = loadHistory();

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

/* ========== NAVIGATION ========== */
const pages = ['scan', 'history', 'about'];

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
  
  const titles = { scan: 'Scan a meal', history: 'History', about: 'About' };
  $('topbarTitle').textContent = titles[page];
  $('btnBack').style.visibility = page === 'scan' ? 'hidden' : 'visible';
  
  if (page === 'history') renderHistory();
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
  cameraModal.classList.add('hidden'); 
  handleFile(e.target.files[0]); 
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
      showCameraMsg('Camera unavailable — please select from gallery instead.');
    }
  }
  
  // Fallback to file input
  setTimeout(() => fallbackInput.click(), 500);
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
  
  try {
    const res = await fetch('/api/predict', { method: 'POST', body: form });
    const data = await res.json();
    
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
  results.classList.remove('hidden');
  warningsBox.innerHTML = '';
  
  // Render warnings
  (data.warnings || []).forEach((w) => {
    const div = document.createElement('div');
    div.className = `warn ${w.level}`;
    div.innerHTML = `<strong>${w.level === 'warning' ? '⚠️' : 'ℹ️'}</strong> ${escapeHtml(w.message)}`;
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
    if (confidenceBadge) {
      confidenceBadge.textContent = `${conf}% confidence`;
      confidenceBadge.style.background = conf >= 70 ? 'var(--success-soft)' : conf >= 50 ? 'var(--warn-soft)' : 'var(--danger-soft)';
      confidenceBadge.style.color = conf >= 70 ? 'var(--success)' : conf >= 50 ? 'var(--warn)' : 'var(--danger)';
    }
  }

  // Render nutrition info
  const info = data.ingredients || {};
  const ings = info.ingredients || [];
  const cals = info.calories || null;
  const allergens = (info.allergens || []).filter((a) => a);
  
  metaRow.innerHTML = '';
  if (cals) {
    metaRow.innerHTML += `<span class="meta-pill">🔥 ~${cals} kcal</span>`;
  }
  if (allergens.length) {
    metaRow.innerHTML += `<span class="meta-pill allergens">⚠️ ${allergens.join(', ')}</span>`;
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
        <div class="hist-sub">${h.conf}% · ${formatDate(h.ts)}</div>
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
