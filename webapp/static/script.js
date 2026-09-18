const $ = (id) => document.getElementById(id);
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const HISTORY_KEY = 'foodlens2.history';
const THEME_KEY = 'foodlens.theme';

const uploadZone = $('uploadZone');
const fileInput = $('fileInput');
const galleryInput = $('galleryInput');
const previewCard = $('previewCard');
const previewImg = $('previewImg');
const btnScan = $('btnScan');
const btnClear = $('btnClear');
const btnAgain = $('btnAgain');
const notice = $('notice');
const results = $('results');
const warningsBox = $('warnings');
const topPredictions = $('topPredictions');
const ingredientsCard = $('ingredientsCard');
const metaRow = $('metaRow');
const ingredientsList = $('ingredientsList');
const historyList = $('historyList');
const histCount = $('histCount');
const histEmpty = $('histEmpty');

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

/* ---------- theme ---------- */
$('themeToggle').addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', cur ? 'light' : 'dark');
  $('themeToggle').textContent = cur ? '🌙' : '☀️';
  try { localStorage.setItem(THEME_KEY, cur ? 'light' : 'dark'); } catch (e) {}
});
if (document.documentElement.getAttribute('data-theme') === 'dark') $('themeToggle').textContent = '☀️';

/* ---------- navigation ---------- */
const pages = ['scan', 'history', 'about'];
document.querySelectorAll('.nav-item').forEach((btn) => {
  btn.addEventListener('click', () => { closeDrawer(); navigate(btn.dataset.page); });
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
  pages.forEach((p) => { $(`page-${p}`).classList.toggle('hidden', p !== page); });
  document.querySelectorAll('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.page === page));
  const titles = { scan: 'Scan a meal', history: 'History', about: 'About' };
  $('topbarTitle').textContent = titles[page];
  $('btnBack').style.visibility = page === 'scan' ? 'hidden' : 'visible';
  if (page === 'history') renderHistory();
  window.scrollTo(0, 0);
}
$('btnBack').style.visibility = 'hidden';

/* ---------- upload ---------- */
uploadZone.addEventListener('click', (e) => {
  if (e.target.closest('button')) return;
  fileInput.click();
});
fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
galleryInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
$('btnGallery').addEventListener('click', () => galleryInput.click());
fallbackInput.addEventListener('change', (e) => { cameraModal.classList.add('hidden'); handleFile(e.target.files[0]); });

uploadZone.ondragover = (e) => { e.preventDefault(); uploadZone.classList.add('over'); };
uploadZone.ondragleave = () => uploadZone.classList.remove('over');
uploadZone.ondrop = (e) => {
  e.preventDefault(); uploadZone.classList.remove('over');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
};

function handleFile(file) {
  if (!file) return;
  if (!file.type.startsWith('image/')) { showNotice('Please choose an image file.', true); return; }
  if (file.size > MAX_SIZE_BYTES) { showNotice('Image is too large (max 10 MB).', true); return; }
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  uploadZone.classList.add('hidden');
  previewCard.classList.remove('hidden');
  notice.classList.add('hidden');
  results.classList.add('hidden');
}

/* ---------- camera ---------- */
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
        video: { facingMode: { ideal: facing }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      cameraVideo.srcObject = stream;
      await cameraVideo.play().catch(() => {});
      cameraModal.classList.remove('hidden');
      return;
    } catch (err) {
      showCameraMsg('Camera blocked or unavailable — pick from gallery instead.');
    }
  }
  fallbackInput.click();
}

function captureFrame() {
  const v = cameraVideo;
  if (!v || v.readyState < 2 || !v.videoWidth) return;
  const canvas = document.createElement('canvas');
  canvas.width = v.videoWidth;
  canvas.height = v.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.save();
  if (facing === 'user') { ctx.translate(canvas.width, 0); ctx.scale(-1, 1); }
  ctx.drawImage(v, 0, 0);
  ctx.restore();
  canvas.toBlob((blob) => {
    if (!blob) return;
    const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
    closeCamera();
    handleFile(file);
    analyze(true);
  }, 'image/jpeg', 0.92);
}

function closeCamera() {
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
  cameraVideo.srcObject = null;
  cameraModal.classList.add('hidden');
}
function showCameraMsg(msg) { cameraMsg.textContent = msg; cameraMsg.classList.remove('hidden'); }

/* ---------- analyze ---------- */
btnScan.addEventListener('click', () => analyze(false));
btnClear.addEventListener('click', resetScan);
btnAgain.addEventListener('click', resetScan);

async function analyze(silent) {
  if (!selectedFile || loading) return;
  loading = true;
  btnScan.disabled = true;
  btnScan.querySelector('.btn-label').classList.add('hidden');
  btnScan.querySelector('.btn-loader').classList.remove('hidden');
  if (!silent) { results.classList.add('hidden'); notice.classList.add('hidden'); }

  const form = new FormData();
  form.append('image', selectedFile);
  try {
    const res = await fetch('/api/predict', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok || data.status !== 'ok') throw new Error(data.message || 'Server error');
    renderResults(data);
    addToHistory(data);
  } catch (err) {
    if (!silent) showNotice(err.message || 'Failed to analyse. Try again.', true);
    else showNotice(err.message || 'Failed to analyse. Try again.', true);
  } finally {
    loading = false;
    btnScan.disabled = false;
    btnScan.querySelector('.btn-label').classList.remove('hidden');
    btnScan.querySelector('.btn-loader').classList.add('hidden');
  }
}

function renderResults(data) {
  results.classList.remove('hidden');
  warningsBox.innerHTML = '';
  (data.warnings || []).forEach((w) => {
    const div = document.createElement('div');
    div.className = `warn ${w.level}`;
    div.textContent = w.message;
    warningsBox.appendChild(div);
  });

  topPredictions.innerHTML = '';
  (data.top || []).forEach((p) => {
    const pct = Math.round(p.prob * 100);
    const row = document.createElement('div');
    row.className = 'pred-row';
    row.innerHTML = `
      <span class="pred-rank">#${p.rank}</span>
      <div class="pred-bar-wrap">
        <div class="pred-bar r${p.rank}" style="width:0%"></div>
        <span class="pred-label">${escapeHtml(p.name)}</span>
      </div>
      <span class="pred-pct">${pct}%</span>`;
    topPredictions.appendChild(row);
    requestAnimationFrame(() => { row.querySelector('.pred-bar').style.width = pct + '%'; });
  });

  const info = data.ingredients || {};
  const ings = info.ingredients || [];
  const cals = info.calories || null;
  const allergens = (info.allergens || []).filter((a) => a);
  metaRow.innerHTML = '';
  if (cals) metaRow.innerHTML += `<span class="meta-pill">~${cals} kcal</span>`;
  if (allergens.length) metaRow.innerHTML += `<span class="meta-pill allergens">⚠ ${allergens.join(', ')}</span>`;
  ingredientsList.innerHTML = ings.map((i) => `<span class="ing-tag">${escapeHtml(i)}</span>`).join('');
  ingredientsCard.classList.remove('hidden');
  results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

/* ---------- history ---------- */
function loadHistory() {
  try { const raw = localStorage.getItem(HISTORY_KEY); const p = raw ? JSON.parse(raw) : []; return Array.isArray(p) ? p : []; } catch (e) { return []; }
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
  history = history.slice(0, 24);
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); } catch (e) {}
}
function renderHistory() {
  histCount.textContent = history.length ? `${history.length} scan${history.length > 1 ? 's' : ''}` : '';
  histEmpty.classList.toggle('hidden', history.length > 0);
  historyList.innerHTML = history.map((h) => `
    <div class="hist-item">
      <img class="hist-thumb" src="${h.thumb}" alt=""/>
      <div class="hist-info">
        <div class="hist-food">${escapeHtml(h.food)}</div>
        <div class="hist-sub">${h.conf}% · ${new Date(h.ts).toLocaleString()}</div>
      </div>
      <button class="hist-del" data-id="${h.id}" aria-label="Delete">✕</button>
    </div>`).join('');
  historyList.querySelectorAll('.hist-del').forEach((b) => {
    b.addEventListener('click', () => {
      history = history.filter((x) => x.id !== Number(b.dataset.id));
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); } catch (e) {}
      renderHistory();
    });
  });
}
$('btnClearHist').addEventListener('click', () => { history = []; try { localStorage.setItem(HISTORY_KEY, '[]'); } catch (e) {} renderHistory(); });

navigate('scan');