/* patient.js — Upload, paste, drag-drop, predict, display results */

let selectedFile  = null;
let originalB64   = null;
let gradcamB64    = null;

// ── Setup paste from clipboard ───────────────────────────────────────────────
document.addEventListener('paste', (e) => {
  const items = (e.clipboardData || window.clipboardData).items;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile();
      if (file) setFile(file);
      break;
    }
  }
});

// ── Drag & Drop ──────────────────────────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.add('drag-over');
}
function handleDragLeave(e) {
  document.getElementById('upload-zone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) setFile(file);
  else showToast('Vui lòng chỉ thả file ảnh.', 'error');
}

// ── File select via input ────────────────────────────────────────────────────
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}

// ── Set file & preview ───────────────────────────────────────────────────────
function setFile(file) {
  if (file.size > 16 * 1024 * 1024) {
    showToast('File quá lớn (tối đa 16 MB).', 'error');
    return;
  }
  selectedFile = file;
  originalB64  = null;
  gradcamB64   = null;

  const reader = new FileReader();
  reader.onload = (ev) => {
    document.getElementById('preview-img').src = ev.target.result;
    document.getElementById('upload-zone').classList.add('hidden');
    document.getElementById('preview-panel').classList.remove('hidden');
    updateAnalyzeBtn();
    // Reset results
    document.getElementById('result-placeholder').classList.remove('hidden');
    document.getElementById('result-content').classList.add('hidden');
    document.getElementById('loading-panel').classList.add('hidden');
  };
  reader.readAsDataURL(file);
}

function resetImage() {
  selectedFile = null;
  document.getElementById('upload-input').value = '';
  document.getElementById('upload-zone').classList.remove('hidden');
  document.getElementById('preview-panel').classList.add('hidden');
  document.getElementById('result-placeholder').classList.remove('hidden');
  document.getElementById('result-content').classList.add('hidden');
  updateAnalyzeBtn();
}

// ── Enable/disable analyze button ────────────────────────────────────────────
function updateAnalyzeBtn() {
  const btn = document.getElementById('analyze-btn');
  btn.disabled = !selectedFile;
}

// ── Start analysis ───────────────────────────────────────────────────────────
async function startAnalysis() {
  const name  = document.getElementById('full-name').value.trim();
  const phone = document.getElementById('phone-number').value.trim();
  const model = document.getElementById('model-select').value;

  if (!name)  { showToast('Vui lòng nhập họ và tên.', 'error'); return; }
  if (!phone) { showToast('Vui lòng nhập số điện thoại.', 'error'); return; }
  if (!selectedFile) { showToast('Chưa chọn ảnh.', 'error'); return; }

  // UI: show loading
  document.getElementById('result-placeholder').classList.add('hidden');
  document.getElementById('result-content').classList.add('hidden');
  document.getElementById('loading-panel').classList.remove('hidden');
  document.getElementById('analyze-btn').disabled = true;
  document.getElementById('btn-icon').textContent = '⏳';
  document.getElementById('btn-text').textContent = 'Đang phân tích...';

  const formData = new FormData();
  formData.append('full_name',    name);
  formData.append('phone_number', phone);
  formData.append('model_choice', model);
  formData.append('file',         selectedFile);

  try {
    const res = await fetch('/predict', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      showToast(data.error || 'Lỗi không xác định.', 'error', 5000);
      resetLoadingUI();
      return;
    }

    displayResults(data);
  } catch (err) {
    showToast('Lỗi kết nối máy chủ.', 'error');
    resetLoadingUI();
  }
}

function resetLoadingUI() {
  document.getElementById('loading-panel').classList.add('hidden');
  document.getElementById('result-placeholder').classList.remove('hidden');
  document.getElementById('analyze-btn').disabled = false;
  document.getElementById('btn-icon').textContent = '🔍';
  document.getElementById('btn-text').textContent = 'Phân tích ảnh';
}

// ── Display results ───────────────────────────────────────────────────────────
function displayResults(data) {
  document.getElementById('loading-panel').classList.add('hidden');
  document.getElementById('result-content').classList.remove('hidden');

  // Store b64 for toggle
  originalB64 = data.original_b64;
  gradcamB64  = data.gradcam_b64;

  // Top 3 list
  const list = document.getElementById('top3-list');
  list.innerHTML = '';
  data.results.forEach((r, i) => {
    const isTop = i === 0;
    const card = document.createElement('div');
    card.className = `diag-card${isTop ? ' top-1' : ''}`;
    card.innerHTML = `
      <div class="diag-rank">#${i+1}</div>
      <div class="diag-icon">${r.icon}</div>
      <div class="diag-info">
        <div class="diag-name-vi">${r.class_vi}</div>
        <div class="diag-name-en">${r.en_label}</div>
        <div class="conf-bar-wrap">
          <div class="conf-bar-bg">
            <div class="conf-bar-fill" style="width:${r.confidence}%"></div>
          </div>
        </div>
      </div>
      <div class="diag-conf">${r.confidence}%</div>
    `;
    list.appendChild(card);
  });

  // Low confidence
  const alert = document.getElementById('low-conf-alert');
  alert.classList.toggle('hidden', !data.low_confidence);

  // Grad-CAM
  showOriginal();  // default: show original
  document.getElementById('gradcam-display').src = originalB64;

  // Re-enable button
  document.getElementById('analyze-btn').disabled = false;
  document.getElementById('btn-icon').textContent = '🔍';
  document.getElementById('btn-text').textContent = 'Phân tích lại';

  showToast('Phân tích hoàn tất!', 'success');
}

// ── Grad-CAM toggle ───────────────────────────────────────────────────────────
function showOriginal() {
  if (originalB64) document.getElementById('gradcam-display').src = originalB64;
  document.getElementById('toggle-original').classList.add('active');
  document.getElementById('toggle-gradcam').classList.remove('active');
}
function showGradcam() {
  if (gradcamB64) document.getElementById('gradcam-display').src = gradcamB64;
  document.getElementById('toggle-gradcam').classList.add('active');
  document.getElementById('toggle-original').classList.remove('active');
}

// Click on image to lightbox
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('gradcam-display')?.addEventListener('click', function() {
    if (this.src) openLightbox(this.src);
  });
  document.getElementById('preview-img')?.addEventListener('click', function() {
    if (this.src) openLightbox(this.src);
  });
});
