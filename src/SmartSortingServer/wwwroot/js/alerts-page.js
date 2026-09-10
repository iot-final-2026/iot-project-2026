(function () {
  const state = { page: 1, pageSize: 10, status: '', search: '', totalPages: 1, selectedAlertId: null, processing: false, searchTimer: null };
  let pendingRecoveryId = null;
  let recoveryTrigger = null;
  const componentView = { IR_SENSOR: ['적외선 센서', 'radio'], CAMERA: ['카메라', 'camera'], SERVO_MOTOR: ['서보모터', 'settings'], CONVEYOR: ['컨베이어', 'move-horizontal'], WORKER_DISPLAY: ['작업자 LCD', 'monitor'], LCD: ['LCD', 'monitor'], ARDUINO: ['Arduino', 'cpu'] };
  const $ = id => document.getElementById(id);
  const checked = alert => alert?.checkStatus === 'CHECKED';
  const recovered = alert => alert?.recoveryStatus === 'RECOVERED';
  function formatDate(value, seconds = false) { if (value == null || value === '' || value === 0) return '-'; const date = new Date(value); if (Number.isNaN(date.getTime()) || date.getFullYear() <= 1970) return '-'; const pad = value => String(value).padStart(2, '0'); const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`; const time = `${pad(date.getHours())}:${pad(date.getMinutes())}${seconds ? `:${pad(date.getSeconds())}` : ''}`; return `${day} ${time}`; }
  function statusView(alert) { if (alert.alertType === 'INFO') return ['INFO', 'info']; if (recovered(alert)) return ['복구완료', 'success']; if (alert.alertType === 'ERROR') return ['ERROR', 'fail']; if (alert.alertType === 'WARNING') return ['WARNING', 'warning']; return ['INFO', 'info']; }
  function priorityClass(priority) { return priority === 'HIGH' ? 'fail' : priority === 'MEDIUM' ? 'warning' : 'info'; }
  function getComponent(alert) { if (alert?.alertType === 'INFO' && !alert.componentCode) return { name: '시스템', icon: 'info' }; const view = componentView[alert.componentCode]; return { name: alert.componentCode ? (view?.[0] || alert.componentCode) : '-', icon: view?.[1] || 'circle-alert' }; }
  function setText(id, value) { if ($(id)) $(id).textContent = value; }
  function setStatus(id, value, className) { if ($(id)) { $(id).textContent = value || '-'; $(id).className = `status-pill ${className}`; } }
  function renderCounts(summary) { setText('todayAlertCount', summary?.todayCount ?? 0); setText('uncheckedAlertCount', summary?.uncheckedCount ?? 0); setText('unrecoveredAlertCount', summary?.notRecoveredCount ?? 0); }
  function renderDetail(alert) {
    setStatus('alertDetailPriority', alert?.priority || '-', priorityClass(alert?.priority));
    setText('alertDetailMessage', alert?.alertMessage || '목록에서 알림을 선택해 주세요.');
    if ($('alertDetailMessage')) $('alertDetailMessage').className = `alert-detail-message${alert?.alertType === 'ERROR' ? ' critical' : ''}`;
    setText('alertDetailId', alert?.alertId ?? '-'); setText('alertDetailComponent', alert ? getComponent(alert).name : '-'); setStatus('alertDetailCheck', alert ? (checked(alert) ? '확인완료' : '미확인') : '-', alert ? (checked(alert) ? 'success' : 'warning') : 'info'); setStatus('alertDetailRecovery', alert ? (recovered(alert) ? '복구완료' : '미복구') : '-', alert ? (recovered(alert) ? 'success' : 'fail') : 'info'); setText('alertDetailCreatedAt', alert ? formatDate(alert.createdAt, true) : '-'); setText('alertDetailCheckedAt', alert && checked(alert) ? formatDate(alert.checkedAt ?? alert.checkAt, true) : '-'); setText('alertDetailRecoveredAt', alert && recovered(alert) ? formatDate(alert.recoveredAt ?? alert.recoveryAt, true) : '-');
    const info = alert?.alertType === 'INFO';
    $('alertDetailCheckRow').hidden = info;
    $('alertDetailRecoveryRow').hidden = info;
    $('alertDetailCheckedAtRow').hidden = info;
    $('alertDetailRecoveredAtRow').hidden = info;
    document.querySelector('.detail-actions').hidden = info;
    const checkButton = $('checkAlertButton');
    const recoverButton = $('recoverAlertButton');
    checkButton.disabled = !alert || state.processing || checked(alert);
    recoverButton.disabled = !alert || state.processing || recovered(alert);
    checkButton.textContent = checked(alert) ? '확인완료' : '확인 처리';
    recoverButton.textContent = recovered(alert) ? '복구완료' : '복구 처리';
    checkButton.className = `modal-button ${checked(alert) ? 'success' : 'secondary'}`;
    recoverButton.className = `modal-button ${recovered(alert) ? 'success' : 'danger'}`;
  }
  function createActionButton(alert, action) { const button = document.createElement('button'); const done = action === 'check' ? checked(alert) : recovered(alert); button.type = 'button'; button.className = `table-action${done ? ' success' : action === 'recover' ? ' primary' : ''}`; button.textContent = done ? (action === 'check' ? '확인완료' : '복구완료') : (action === 'check' ? '확인' : '복구'); button.disabled = state.processing || done; button.addEventListener('click', event => { event.stopPropagation(); selectAlert(alert.alertId); processAlert(action, alert.alertId); }); return button; }
  function createRow(alert) { const row = document.createElement('div'); const [label, style] = statusView(alert); const component = getComponent(alert); row.className = `alert-row${String(alert.alertId) === String(state.selectedAlertId) ? ' selected' : ''}`; row.dataset.alertId = alert.alertId; row.tabIndex = 0; row.setAttribute('role', 'button'); const status = document.createElement('span'); const pill = document.createElement('span'); pill.className = `status-pill ${style}`; pill.textContent = label; status.append(pill); const device = document.createElement('span'); device.className = 'component-cell'; const icon = document.createElement('i'); icon.dataset.lucide = component.icon; device.append(icon, document.createTextNode(component.name)); const message = document.createElement('span'); message.className = 'alert-message-cell'; message.textContent = alert.alertMessage || '-'; const time = document.createElement('span'); time.className = 'time-cell'; time.textContent = formatDate(alert.createdAt); const actions = document.createElement('span'); actions.className = 'action-cell'; if (alert.alertType !== 'INFO') actions.append(createActionButton(alert, 'check'), createActionButton(alert, 'recover')); row.append(status, device, message, time, actions); row.addEventListener('click', () => selectAlert(alert.alertId)); row.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectAlert(alert.alertId); } }); return row; }
  function renderRows(items) { const table = $('alertTable'); table.querySelectorAll('.alert-row:not(.alert-row-head)').forEach(row => row.remove()); if (!items.length) { const empty = document.createElement('div'); empty.className = 'alert-row alert-empty'; empty.textContent = '조건에 맞는 알림이 없습니다.'; table.append(empty); renderDetail(null); return; } items.forEach(alert => table.append(createRow(alert))); lucide.createIcons(); }
  function renderPagination(data) { state.totalPages = Math.max(1, Number(data.totalPages) || 1); state.page = Number(data.page) || state.page; setText('alertResultCount', `${Number(data.totalCount) || 0}건`); setText('alertPageInfo', `${state.page} / ${state.totalPages}`); $('alertPrevPage').disabled = state.page <= 1; $('alertNextPage').disabled = state.page >= state.totalPages; }
  async function loadSummary() { try { renderCounts(await apiGet('/api/alerts/summary')); } catch (error) { if (error.status === 401) redirectLogin(); } }
  async function loadAlerts(preferredId = state.selectedAlertId) { const params = new URLSearchParams({ page: state.page, pageSize: state.pageSize }); if (state.status) params.set('status', state.status); if (state.search) params.set('search', state.search); showTableMessage('알림 내역을 불러오는 중입니다.'); try { const data = await apiGet(`/api/alerts?${params}`); const items = Array.isArray(data?.items) ? data.items : []; state.selectedAlertId = items.some(item => String(item.alertId) === String(preferredId)) ? preferredId : items[0]?.alertId ?? null; renderRows(items); renderPagination(data || {}); await loadSummary(); if (state.selectedAlertId != null) await loadDetail(state.selectedAlertId); else renderDetail(null); } catch (error) { if (error.status === 401) return redirectLogin(); showTableMessage(error.message || '알림 내역을 불러오지 못했습니다.'); } }
  async function loadDetail(id) { try { renderDetail(await apiGet(`/api/alerts/${encodeURIComponent(id)}`)); } catch (error) { if (error.status === 401) redirectLogin(); else console.error('알림 상세 조회 실패:', error); } }
  function selectAlert(id) { state.selectedAlertId = id; document.querySelectorAll('.alert-row[data-alert-id]').forEach(row => row.classList.toggle('selected', String(row.dataset.alertId) === String(id))); loadDetail(id); }
  function closeRecoveryModal() {
    $('recoverModal').hidden = true;
    pendingRecoveryId = null;
    if (recoveryTrigger?.isConnected) recoveryTrigger.focus();
    recoveryTrigger = null;
  }
  function bindRecoveryModal() {
    const modal = $('recoverModal');
    const cancelButton = $('cancelRecoverButton');
    const confirmButton = $('confirmRecoverButton');
    cancelButton.addEventListener('click', closeRecoveryModal);
    modal.addEventListener('click', event => { if (event.target === modal) closeRecoveryModal(); });
    modal.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); closeRecoveryModal(); }
      if (event.key === 'Tab') {
        event.preventDefault();
        (document.activeElement === cancelButton ? confirmButton : cancelButton).focus();
      }
    });
    confirmButton.addEventListener('click', () => {
      const id = pendingRecoveryId;
      closeRecoveryModal();
      if (id != null) processAlert('recover', id, true);
    });
  }
  async function processAlert(action, id, confirmed = false) {
    if (state.processing) return;
    if (action === 'recover' && !confirmed) {
      if (pendingRecoveryId != null) return;
      pendingRecoveryId = id;
      recoveryTrigger = document.activeElement;
      $('recoverModal').hidden = false;
      $('cancelRecoverButton').focus();
      return;
    }
    state.processing = true;
    renderDetail(null);
    try { await apiPatch(`/api/alerts/${id}/${action}`); await loadAlerts(id); }
    catch (error) { if (error.status === 401) redirectLogin(); else window.alert(error.message || '알림 처리에 실패했습니다.'); }
    finally { state.processing = false; if (state.selectedAlertId != null) loadDetail(state.selectedAlertId); }
  }
  function showTableMessage(message) { const table = $('alertTable'); table.querySelectorAll('.alert-row:not(.alert-row-head)').forEach(row => row.remove()); const row = document.createElement('div'); row.className = 'alert-row alert-empty'; row.textContent = message; table.append(row); }
  function redirectLogin() { localStorage.removeItem('accessToken'); localStorage.removeItem('adminName'); window.location.href = 'login.html'; }
  function bindControls() { document.querySelectorAll('[data-alert-filter]').forEach(button => button.addEventListener('click', () => { state.status = button.dataset.alertFilter === 'ALL' ? '' : button.dataset.alertFilter; state.page = 1; document.querySelectorAll('[data-alert-filter]').forEach(item => item.classList.toggle('active', item === button)); loadAlerts(); })); $('alertSearch').addEventListener('input', event => { state.search = event.target.value.trim(); state.page = 1; clearTimeout(state.searchTimer); state.searchTimer = setTimeout(() => loadAlerts(), 300); }); $('alertPrevPage').addEventListener('click', () => { if (state.page > 1) { state.page -= 1; loadAlerts(); } }); $('alertNextPage').addEventListener('click', () => { if (state.page < state.totalPages) { state.page += 1; loadAlerts(); } }); $('checkAlertButton').addEventListener('click', () => { if (state.selectedAlertId != null) processAlert('check', state.selectedAlertId); }); $('recoverAlertButton').addEventListener('click', () => { if (state.selectedAlertId != null) processAlert('recover', state.selectedAlertId); }); }
  window.handleAlertsPageMqttAlert = function (alert) { if (alert?.alertId) loadAlerts(alert.alertId); };
  function init() { bindControls(); bindRecoveryModal(); loadAlerts(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}());
