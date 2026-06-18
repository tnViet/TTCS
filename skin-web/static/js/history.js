/* history.js — Tra cứu lịch sử bệnh nhân theo SĐT */

async function searchHistory() {
  const phone = document.getElementById('search-phone').value.trim();
  if (!phone) {
    showToast('Vui lòng nhập số điện thoại.', 'error');
    return;
  }

  const btn = document.getElementById('search-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Đang tìm...';

  const container = document.getElementById('history-results');
  container.innerHTML = `
    <div class="spinner-wrap">
      <div class="spinner"></div>
      <div>Đang tra cứu...</div>
    </div>`;

  try {
    const res  = await fetch(`/api/history?phone=${encodeURIComponent(phone)}`);
    const data = await res.json();

    if (!res.ok || data.error) {
      container.innerHTML = `<div class="no-results"><div class="nr-icon">⚠️</div><div>${data.error || 'Lỗi.'}</div></div>`;
      return;
    }

    if (!data.length) {
      container.innerHTML = `
        <div class="no-results">
          <div class="nr-icon">🔍</div>
          <div>Không tìm thấy lịch sử với số điện thoại <strong>${phone}</strong></div>
          <div style="margin-top:.5rem;font-size:.8rem;color:var(--clr-text-dim)">Kiểm tra lại số điện thoại bạn đã dùng khi upload ảnh</div>
        </div>`;
      return;
    }

    renderHistory(data, container);
  } catch (err) {
    container.innerHTML = `<div class="no-results"><div class="nr-icon">⚠️</div><div>Lỗi kết nối máy chủ.</div></div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Tìm kiếm';
  }
}

function renderHistory(records, container) {
  // Header count
  let html = `<div style="margin-bottom:1rem;color:var(--clr-text-muted);font-size:.85rem">
    Tìm thấy <strong style="color:var(--clr-text)">${records.length}</strong> lần phân tích
  </div>`;
  html += `<div class="history-grid">`;

  records.forEach((r, idx) => {
    const hasNote     = r.verified_disease || r.doctor_note;
    const lowConf     = r.low_confidence;
    const modelLabel  = r.model_used === 'densenet121' ? 'DenseNet-121' : 'EfficientNetV2-B0';

    let doctorSection = '';
    if (hasNote) {
      doctorSection = `
        <div class="doctor-note-box">
          <div class="dn-label">💊 Bác sĩ đã xem xét</div>
          ${r.verified_disease_vi ? `<div class="dn-disease">Chẩn đoán: ${r.verified_disease_vi}</div>` : ''}
          ${r.doctor_note        ? `<div class="dn-note">${escHtml(r.doctor_note)}</div>`               : ''}
          ${r.reviewed_at        ? `<div style="font-size:.7rem;color:var(--clr-text-dim);margin-top:.25rem">Xem xét lúc ${r.reviewed_at}</div>` : ''}
        </div>`;
    } else {
      doctorSection = `
        <div class="pending-badge">⏳ Bác sĩ chưa xem xét</div>`;
    }

    html += `
      <div class="history-card" style="animation-delay:${idx*0.05}s">
        <div class="history-card-img" onclick="openLightbox('${r.image_url}')">
          <img src="${r.image_url}" alt="Ảnh da liễu" loading="lazy"
               onerror="this.parentElement.style.background='#1a1f2e';this.style.display='none'">
          ${r.gradcam_url ? `<div class="cam-badge" onclick="event.stopPropagation();openLightbox('${r.gradcam_url}')">Heatmap</div>` : ''}
        </div>
        <div class="history-card-body">
          <div class="hc-date">📅 ${r.created_at}</div>
          <div class="hc-model-badge">${modelLabel}</div>
          <div class="hc-disease">${r.top_disease_vi || r.top_disease}</div>
          <div class="hc-disease-en">${r.top_disease} ${lowConf ? '⚠️' : ''}</div>
          <div class="hc-conf">Độ tin cậy: <span>${r.top_confidence}%</span></div>
          ${doctorSection}
        </div>
      </div>`;
  });

  html += `</div>`;
  container.innerHTML = html;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Enter key on search field
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('search-phone')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') searchHistory();
  });

  // Auto-search if phone in URL params
  const params = new URLSearchParams(window.location.search);
  const phone  = params.get('phone');
  if (phone) {
    document.getElementById('search-phone').value = phone;
    searchHistory();
  }
});
