/* doctor.js — Dashboard bác sĩ: load cases, filter, save review */

let allCases      = [];
let currentFilter = 'all';

// ── Load all cases on page load ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadCases();
});

async function loadCases() {
  try {
    const res  = await fetch('/doctor/api/cases');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi tải dữ liệu');
    allCases = data;
    updateStats();
    renderCases();
  } catch (err) {
    document.getElementById('cases-list').innerHTML =
      `<div class="no-results"><div class="nr-icon">!</div><div>${err.message}</div></div>`;
  }
}

// ── Stats ─────────────────────────────────────────────────────────────────────
function updateStats() {
  const total    = allCases.length;
  const reviewed = allCases.filter(c => c.verified_disease || c.doctor_note).length;
  const pending  = total - reviewed;
  document.getElementById('stat-total').textContent    = total;
  document.getElementById('stat-pending').textContent  = pending;
  document.getElementById('stat-reviewed').textContent = reviewed;
}

// ── Filter ────────────────────────────────────────────────────────────────────
function setFilter(f) {
  currentFilter = f;
  ['all', 'pending', 'reviewed'].forEach(k => {
    document.getElementById(`filter-${k}`).classList.toggle('active', k === f);
  });
  renderCases();
}

function getFiltered() {
  if (currentFilter === 'pending')  return allCases.filter(c => !c.verified_disease && !c.doctor_note);
  if (currentFilter === 'reviewed') return allCases.filter(c => c.verified_disease || c.doctor_note);
  return allCases;
}

// ── Render cases ──────────────────────────────────────────────────────────────
function renderCases() {
  const list     = document.getElementById('cases-list');
  const filtered = getFiltered();

  if (!filtered.length) {
    list.innerHTML = `<div class="no-results"><div class="nr-icon">-</div><div>Không có ca nào.</div></div>`;
    return;
  }

  list.innerHTML = filtered.map((c, idx) => buildCaseCard(c, idx)).join('');
}

function buildCaseCard(c, idx) {
  const reviewed   = !!(c.verified_disease || c.doctor_note);
  const modelLabel = c.model_used === 'densenet121' ? 'DenseNet-121' : 'EfficientNetV2-B0';

  // Disease dropdown options
  const opts = window.DISEASE_CHOICES.map(d =>
    `<option value="${d.key}" ${c.verified_disease === d.key ? 'selected' : ''}>${d.label}</option>`
  ).join('');

  // Verified chip
  const verifiedChip = c.verified_disease_vi
    ? `<span class="verified-chip">Đã phân loại: ${c.verified_disease_vi}</span>`
    : '';

  // Top 3 short list
  const top3Html = c.top3.map((t, i) =>
    `<span class="case-top3-item">#${i+1} ${t.class_vi} (${t.confidence}%)</span>`
  ).join('');

  // Heatmap button (only if heatmap exists)
  const heatmapBtn = c.gradcam_url
    ? `<button class="btn-heatmap" onclick="event.stopPropagation(); openLightbox('${c.gradcam_url}')" title="Xem Grad-CAM heatmap">Heatmap</button>`
    : '';

  return `
  <div class="case-card ${reviewed ? 'reviewed' : ''}" id="case-${c.id}" style="animation-delay:${idx * 0.04}s">
    <div class="case-card-main">

      <!-- Thumbnail: click = zoom lightbox -->
      <div class="case-thumb" onclick="openLightbox('${c.image_url}')" title="Nhấn để phóng to ảnh">
        <img src="${c.image_url}" alt="Ảnh bệnh nhân" onerror="this.style.opacity=0.2">
        <div class="case-thumb-label">Phóng to</div>
        ${heatmapBtn}
      </div>

      <!-- Info -->
      <div class="case-info">
        <div class="case-patient">${escHtml(c.patient_name)}</div>
        <div class="case-phone">${c.patient_phone}</div>
        <div class="case-ai-row">
          <span class="case-disease-badge">${c.top_disease_vi}</span>
          <span class="case-conf-badge">${c.top_confidence}%</span>
          ${c.low_confidence ? '<span class="case-low-conf">Thấp</span>' : ''}
        </div>
        <div class="case-top3">${top3Html}</div>
        <div class="case-meta">
          ${c.created_at} &nbsp;|&nbsp; ${modelLabel}
          ${c.reviewed_at ? `&nbsp;|&nbsp; Đã xem xét: ${c.reviewed_at}` : ''}
        </div>
        ${verifiedChip}
      </div>

      <!-- Doctor actions -->
      <div class="case-actions">
        <select class="form-control" id="select-${c.id}">
          <option value="">Chọn phân loại bệnh</option>
          ${opts}
        </select>
        <textarea class="form-control" id="note-${c.id}"
                  placeholder="Ghi chú cho bệnh nhân..."
                  rows="3">${c.doctor_note || ''}</textarea>
        <div class="case-save-row">
          <button class="btn btn-success btn-sm" onclick="saveReview(${c.id})">Lưu</button>
          <span class="save-status hidden" id="saved-${c.id}">Da luu</span>
        </div>
      </div>
    </div>
  </div>`;
}

// ── Save review ───────────────────────────────────────────────────────────────
async function saveReview(id) {
  const disease = document.getElementById(`select-${id}`).value;
  const note    = document.getElementById(`note-${id}`).value.trim();

  const btn = document.querySelector(`#case-${id} .btn-success`);
  btn.disabled    = true;
  btn.textContent = '...';

  try {
    const res = await fetch('/doctor/api/review', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        prediction_id:    id,
        verified_disease: disease || null,
        doctor_note:      note    || null,
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Lỗi lưu.');

    // Update local state
    const c = allCases.find(x => x.id === id);
    if (c) {
      c.verified_disease    = disease || null;
      c.verified_disease_vi = disease
        ? (window.DISEASE_CHOICES.find(d => d.key === disease)?.label || '')
        : '';
      c.doctor_note = note || null;
    }

    // Mark card reviewed + flash save indicator
    document.getElementById(`case-${id}`).classList.add('reviewed');
    const savedEl = document.getElementById(`saved-${id}`);
    savedEl.textContent = 'Da luu';
    savedEl.classList.remove('hidden');
    setTimeout(() => savedEl.classList.add('hidden'), 3000);

    updateStats();
    showToast('Da luu ghi chu!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Luu';
  }
}

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
