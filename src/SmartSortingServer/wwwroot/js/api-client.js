const API_BASE_URL = window.location.origin;

const PRODUCT_UNIT_PER_SET = {
  chocolate: 10,
  candy: 1
};

function getAccessToken() {
  return localStorage.getItem('accessToken');
}

async function apiRequest(path, options = {}) {
  const token = getAccessToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });

  const data = response.status === 204
    ? null
    : await response.json().catch(() => null);

  if (!response.ok) {
    const error = new Error(data?.message || `API 요청 실패: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return data;
}

function apiGet(path) {
  return apiRequest(path);
}

function apiPost(path, body) {
  return apiRequest(path, {
    method: 'POST',
    body: JSON.stringify(body)
  });
}

function apiPatch(path, body) {
  return apiRequest(path, {
    method: 'PATCH',
    ...(body ? { body: JSON.stringify(body) } : {})
  });
}

function apiPut(path, body) {
  return apiRequest(path, {
    method: 'PUT',
    body: JSON.stringify(body)
  });
}

function setCurrentProductionTargets(targets) {
  window.currentProductionTargets = {
    chocolate: targets?.targetChocolateSetCount,
    candy: targets?.targetCandySetCount
  };
}

function initTargetControls() {
  initSaveResultModal();

  document.querySelectorAll('.stepper-btn').forEach(button => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.target);

      if (!input) {
        return;
      }

      const step = Number(button.dataset.step) || 0;
      const min = Number(input.min) || 1;
      const nextValue = Math.max(min, (Number(input.value) || min) + step);

      input.value = nextValue;
    });
  });

  const targetForm = document.querySelector('.target-form');

  if (targetForm) {
    targetForm.addEventListener('submit', event => {
      event.preventDefault();
      saveProductionTargets();
    });
  }

  const workerSaveButton = document.querySelector('.btn-worker-save');

  if (workerSaveButton) {
    workerSaveButton.addEventListener('click', saveWorkerCount);
  }
}

function initSaveResultModal() {
  const modal = document.getElementById('saveResultModal');
  const closeButton = document.getElementById('closeSaveResultButton');

  closeButton?.addEventListener('click', () => {
    if (modal) {
      modal.hidden = true;
    }
  });

  modal?.addEventListener('click', event => {
    if (event.target === modal) {
      modal.hidden = true;
    }
  });
}

function showSaveResultModal(title, message, includeTiming = false) {
  const modal = document.getElementById('saveResultModal');
  const titleElement = document.getElementById('saveResultModalTitle');
  const messageElement = document.getElementById('saveResultModalMessage');
  const timingElement = document.getElementById('saveResultModalTiming');

  if (!modal || !titleElement || !messageElement || !timingElement) {
    window.alert(message);
    return;
  }

  titleElement.textContent = title;
  messageElement.textContent = message;
  timingElement.textContent = includeTiming
    ? (/다음|익일|예약/.test(message)
      ? '※ 변경사항이 다음 날 생산에 반영됩니다.'
      : '※ 변경사항이 오늘 생산에 반영됩니다.')
    : '';
  modal.hidden = false;
}

async function saveProductionTargets() {
  const chocolateTarget = document.getElementById('chocoTarget');
  const candyTarget = document.getElementById('candyTarget');
  const saveButton = document.querySelector('.target-settings .btn-save');
  if (saveButton?.disabled) return;
  for (const input of [chocolateTarget, candyTarget]) {
    if (!input) return;
    if (!input.reportValidity()) return;
    if (!Number.isSafeInteger(Number(input.value)) || Number(input.value) < 1) {
      window.alert('생산 목표는 1 이상의 정수로 입력해 주세요.');
      input.focus();
      return;
    }
  }
  if (saveButton) saveButton.disabled = true;

  try {
    const targets = await apiPut('/api/production-targets/current', {
      targetChocolateSetCount: Number(chocolateTarget?.value) || 0,
      targetCandySetCount: Number(candyTarget?.value) || 0
    });

    setCurrentProductionTargets(targets);
    updateTargetInputs(targets);
    updateWorkerCountInput(targets);
    await loadDashboardSummary();
    await refreshDashboardCharts();
    showSaveResultModal(
      '저장 완료',
      targets?.message || '생산 목표가 저장되었습니다.',
      true
    );
  } catch (error) {
    console.error('생산 목표 저장 실패:', error);
    showSaveResultModal(
      '저장 실패',
      error.message || '생산 목표 저장에 실패했습니다.'
    );
  } finally {
    if (saveButton) saveButton.disabled = false;
  }
}

async function saveWorkerCount() {
  const workerCountInput = document.getElementById('workerCount');
  const saveButton = document.querySelector('.btn-worker-save');
  const dailyWorkerCount = Number(workerCountInput?.value);

  if (!Number.isInteger(dailyWorkerCount) || dailyWorkerCount < 1) {
    window.alert('작업 인원은 1명 이상으로 입력해 주세요.');
    return;
  }

  if (saveButton) {
    saveButton.disabled = true;
  }

  try {
    const targets = await apiPut('/api/production-targets/worker-count', {
      dailyWorkerCount
    });

    updateWorkerCountInput(targets);
    showSaveResultModal(
      '저장 완료',
      targets?.message || '작업 인원이 저장되었습니다.',
      true
    );
  } catch (error) {
    console.error('작업 인원 저장 실패:', error);
    showSaveResultModal(
      '저장 실패',
      error.message || '작업 인원 저장에 실패했습니다.'
    );
  } finally {
    if (saveButton) {
      saveButton.disabled = false;
    }
  }
}

// 로그인
async function login(loginId, password) {
  const data = await apiPost('/api/auth/login', {
    loginId,
    password
  });

  localStorage.setItem('accessToken', data.token);
  localStorage.setItem('adminName', data.name);

  return data;
}

// 장비상태 최초 로딩
async function loadComponents() {
  const components = await apiGet('/api/system-components');

  components.forEach(component => {
    updateComponentStatus({
      componentCode: component.componentCode,
      status: component.currentStatus
    });
  });
}

// 현재 적용 목표 및 작업 인원 로딩
async function loadProductionTargets() {
  const targets = await apiGet('/api/production-targets/current');

  // 상단 현황 카드는 예약값이 아닌 오늘 적용 중인 목표를 사용한다.
  setCurrentProductionTargets(targets);

  updateTargetInputs(targets);
  updateWorkerCountInput(targets);
}

// 오늘 하루 생산 요약 로딩
async function loadDashboardSummary() {
  const summary = await apiGet('/api/dashboard/summary');

  updateProductionStatus(summary);
}

async function refreshDashboardSummary() {
  const summary = await apiGet('/api/dashboard/summary');

  updateProductionStatus(summary);
}

// 차트 갱신
async function refreshDashboardCharts() {
  const hourly = [...await apiGet('/api/dashboard/hourly-production')]
    .sort((a, b) => Number.parseInt(a.hour, 10) - Number.parseInt(b.hour, 10));
  const ratio = await apiGet('/api/dashboard/classification-ratio');

  updateProductionChart({
    labels: hourly.map(item => `${item.hour}:00`),
    chocolate: hourly.map(item => item.chocolateCount),
    candy: hourly.map(item => item.candyCount),
    goals: window.dashboardProductionGoals || {}
  });

  updateRatioChart({
    chocolate: ratio.chocolateRate ?? ratio.chocolateRatio ?? ratio.chocolate ?? ratio.successRate,
    candy: ratio.candyRate ?? ratio.candyRatio ?? ratio.candy ?? ratio.failedRate
  });
}

// 전체 초기 로딩
async function loadInitialDashboard() {
  try {
    await loadProductionTargets();

    await Promise.all([
      loadComponents(),
      loadDashboardSummary()
    ]);

    await refreshDashboardCharts();

    try {
      await loadRecentAlerts();
    } catch (error) {
      console.error('최근 알람 로딩 실패:', error);
    }

    try {
      await loadRecentProductImages();
    }
    catch (error) {
      console.error('최근 제품 이미지 로딩 실패:', error);
    }
  }
  catch (error) {
    console.error('초기 대시보드 로딩 실패:', error);
  }
}

async function loadRecentProductImages() {
  const detections = await apiGet('/api/dashboard/recent-detections');

  updateRecentProductImages(detections);
}

function getApiImageUrl(path) {
  if (!path) {
    return '';
  }

  if (/^https?:\/\//.test(path)) {
    return path;
  }

  return `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTargetControls);
}
else {
  initTargetControls();
}
async function loadRecentAlerts() {
  const alerts = await apiGet('/api/alerts');

  updateRecentAlerts(alerts);
}
