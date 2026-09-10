(function () {
  const state = { page: 1, pageSize: 15, productType: '', status: '', search: '', totalPages: 1, selectedId: null, requestId: 0 };
  const $ = id => document.getElementById(id);

  function typeLabel(type) { return type === 'CHOCOLATE' ? '초콜릿' : type === 'CANDY' ? '사탕' : '분류 실패'; }
  function confidence(value) { return value == null ? '확인 필요' : `신뢰도 ${(Number(value) * 100).toFixed(1)}%`; }
  function dateTime(value, withSeconds = false) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const parts = [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')];
    const time = [String(date.getHours()).padStart(2, '0'), String(date.getMinutes()).padStart(2, '0')];
    if (withSeconds) time.push(String(date.getSeconds()).padStart(2, '0'));
    return withSeconds ? `${parts.join('-')} ${time.join(':')}` : time.join(':');
  }
  function statusPill(status) {
    const failed = status === 'FAILED';
    return `<span class="status-pill ${failed ? 'fail' : 'success'}">${status || '-'}</span>`;
  }
  function imageMarkup(path, alt, detail = false) {
    const imageUrl = typeof getApiImageUrl === 'function' ? getApiImageUrl(path) : path;
    if (typeof imageUrl === 'string' && /^https?:\/\//i.test(imageUrl)) {
      return `<img src="${imageUrl.replace(/"/g, '&quot;')}" alt="${alt}" onerror="this.replaceWith(Object.assign(document.createElement('div'), {className:'image-placeholder', textContent:'이미지 준비 중'}))">`;
    }
    return `<div class="image-placeholder${detail ? ' detail-placeholder' : ''}">이미지 준비 중</div>`;
  }
  function renderCards(items) {
    const gallery = $('productGallery');
    gallery.innerHTML = items.map(item => {
      const failed = item.classificationStatus === 'FAILED';
      const selected = item.productDetectionId === state.selectedId ? ' selected' : '';
      return `<button type="button" class="detection-card${selected}" data-id="${item.productDetectionId}">
        <div class="detection-thumb">${imageMarkup(item.imagePath, `${typeLabel(item.productTypeCode)} 감지 이미지`)}<span class="detection-badge ${failed ? 'fail' : item.productTypeCode === 'CANDY' ? 'candy' : 'chocolate'}">${typeLabel(item.productTypeCode)}</span></div>
        <div class="detection-card-body"><div class="detection-meta"><span>${confidence(item.confidence)}</span><span>${dateTime(item.detectedAt)}</span></div><div class="detection-status ${failed ? 'fail' : 'success'}">${item.productDetectionId} · ${item.classificationStatus || '-'}</div></div>
      </button>`;
    }).join('');
    gallery.querySelectorAll('[data-id]').forEach(card => card.addEventListener('click', () => loadDetail(Number(card.dataset.id))));
    $('productEmptyState').hidden = items.length > 0;
  }
  function renderPagination(data) {
    state.totalPages = Math.max(1, Number(data.totalPages) || 1);
    $('productResultCount').textContent = `${Number(data.totalCount) || 0}건`;
    $('productPageInfo').textContent = `${data.page || state.page} / ${state.totalPages}`;
    $('productPrevPage').disabled = state.page <= 1;
    $('productNextPage').disabled = state.page >= state.totalPages;
  }
  async function loadList() {
    const requestId = ++state.requestId;
    $('productGallery').setAttribute('aria-busy', 'true');
    const params = new URLSearchParams({ page: state.page, pageSize: state.pageSize });
    if (state.productType) params.set('productType', state.productType);
    if (state.status) params.set('status', state.status);
    if (state.search) params.set('search', state.search);
    try {
      const data = await apiGet(`/api/product-detections?${params}`);
      if (requestId !== state.requestId) return;
      renderCards(Array.isArray(data?.items) ? data.items : []);
      renderPagination(data || {});
      const first = data?.items?.[0];
      if (first) { state.selectedId = first.productDetectionId; renderCards(data.items); await loadDetail(first.productDetectionId); }
      else clearDetail();
    } catch (error) {
      if (error.status === 401) { localStorage.removeItem('accessToken'); localStorage.removeItem('adminName'); window.location.href = 'login.html'; return; }
      $('productGallery').innerHTML = `<div class="product-error">${error.message || '목록을 불러오지 못했습니다.'}</div>`;
      $('productEmptyState').hidden = true;
    } finally { $('productGallery').removeAttribute('aria-busy'); }
  }
  function clearDetail() { ['detailDetectionId','detailProductType','detailConfidence','detailDetectedAt','detailSessionId'].forEach(id => $(id).textContent = '-'); $('detailClassificationStatus').textContent = '-'; $('detailStatus').textContent = '-'; $('detailStatus').className = 'status-pill info'; $('detailImagePlaceholder').className = 'image-placeholder'; $('detailImagePlaceholder').innerHTML = '이미지 준비 중'; }
  async function loadDetail(id) {
    state.selectedId = id;
    document.querySelectorAll('.detection-card').forEach(card => card.classList.toggle('selected', Number(card.dataset.id) === id));
    try {
      const item = await apiGet(`/api/product-detections/${encodeURIComponent(id)}`);
      $('detailDetectionId').textContent = item.productDetectionId;
      $('detailProductType').textContent = typeLabel(item.productTypeCode);
      $('detailConfidence').textContent = confidence(item.confidence).replace(/^신뢰도 /, '');
      $('detailDetectedAt').textContent = dateTime(item.detectedAt, true);
      $('detailSessionId').textContent = item.sessionId;
      $('detailClassificationStatus').innerHTML = statusPill(item.classificationStatus);
      $('detailStatus').textContent = item.classificationStatus || '-';
      $('detailStatus').className = `status-pill ${item.classificationStatus === 'FAILED' ? 'fail' : 'success'}`;
      $('detailImagePlaceholder').className = 'detail-image-content';
      $('detailImagePlaceholder').innerHTML = imageMarkup(item.imagePath, '선택한 감지 이미지', true);
    } catch (error) {
      if (error.status === 401) { localStorage.removeItem('accessToken'); localStorage.removeItem('adminName'); window.location.href = 'login.html'; return; }
      console.error('제품 감지 상세 조회 실패:', error);
    }
  }
  document.querySelectorAll('.segmented-control .segment').forEach((button, index) => button.addEventListener('click', () => {
    document.querySelectorAll('.segmented-control .segment').forEach(item => item.classList.remove('active')); button.classList.add('active');
    state.page = 1; state.productType = index === 1 ? 'CHOCOLATE' : index === 2 ? 'CANDY' : ''; state.status = index === 3 ? 'FAILED' : ''; loadList();
  }));
  $('productSearch').addEventListener('input', event => { const value = event.target.value.trim(); if (value && !/^\d+$/.test(value)) { event.target.value = value.replace(/\D/g, ''); } state.search = event.target.value.trim(); state.page = 1; loadList(); });
  $('productPrevPage').addEventListener('click', () => { if (state.page > 1) { state.page -= 1; loadList(); } });
  $('productNextPage').addEventListener('click', () => { if (state.page < state.totalPages) { state.page += 1; loadList(); } });
  loadList();
}());
