
function updateText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
}

function updateProgress(id, progress) {
  const element = document.getElementById(id);

  if (element) {
    const width = Math.max(0, Math.min(Number(progress) || 0, 100));
    element.style.width = `${width}%`;
  }
}

function updateCard(prefix, current, target, progress, valueUnit, targetUnit = valueUnit) {
  const currentText = formatNumber(current);
  const targetText = formatNumber(target);
  const progressText = formatProgress(progress);

  updateText(`${prefix}-value`, currentText);
  updateText(`${prefix}-target`, `목표 ${targetText}${targetUnit}`);
  updateText(`${prefix}-rate`, progressText);
  updateProgress(`${prefix}-progress`, progress);
}

function updateProductionStatus(data) {
  const { chocolate, candy } = normalizeProductionStatus(data);

  window.dashboardProductionGoals = {
    chocolate: chocolate.targetCount,
    candy: candy.targetCount
  };

  updateCard(
    'chocolate-count',
    chocolate.currentCount,
    chocolate.targetCount,
    chocolate.progress,
    '개'
  );

  updateCard(
    'candy-count',
    candy.currentCount,
    candy.targetCount,
    candy.progress,
    '개'
  );

  updateCard(
    'chocolate-set',
    chocolate.setCount,
    chocolate.targetSetCount,
    chocolate.progress,
    '세트'
  );

  updateCard(
    'candy-set',
    candy.setCount,
    candy.targetSetCount,
    candy.progress,
    '세트'
  );
}

function normalizeProductionStatus(data) {
  const chocolateUnitPerSet = Number(data.chocolate?.unitPerSet) || 10;
  const candyUnitPerSet = Number(data.candy?.unitPerSet) || 1;
  const currentTargets = window.currentProductionTargets || {};

  const chocolateCurrentCount = getNumber(
    data.chocolate?.currentCount,
    data.chocolateCount
  );
  const candyCurrentCount = getNumber(
    data.candy?.currentCount,
    data.candyCount
  );

  const chocolateTargetCount = getNumber(
    Number(currentTargets.chocolate) * chocolateUnitPerSet,
    data.chocolate?.targetCount,
    Number(data.targetChocolateSetCount) * chocolateUnitPerSet
  );
  const candyTargetCount = getNumber(
    Number(currentTargets.candy) * candyUnitPerSet,
    data.candy?.targetCount,
    Number(data.targetCandySetCount) * candyUnitPerSet,
    data.targetCandyCount
  );
  const chocolateTargetSetCount = getNumber(
    currentTargets.chocolate,
    data.chocolate?.targetSetCount,
    data.targetChocolateSetCount,
    Math.ceil(chocolateTargetCount / chocolateUnitPerSet)
  );
  const candyTargetSetCount = getNumber(
    currentTargets.candy,
    data.candy?.targetSetCount,
    data.targetCandySetCount,
    Math.ceil(candyTargetCount / candyUnitPerSet)
  );
  const chocolateSetCount = getNumber(
    data.chocolate?.setCount,
    data.chocolateSetCount,
    Math.floor(chocolateCurrentCount / chocolateUnitPerSet)
  );
  const candySetCount = getNumber(
    data.candy?.setCount,
    data.candySetCount,
    Math.floor(candyCurrentCount / candyUnitPerSet)
  );

  return {
    chocolate: {
      currentCount: chocolateCurrentCount,
      targetCount: chocolateTargetCount,
      targetSetCount: chocolateTargetSetCount,
      unitPerSet: chocolateUnitPerSet,
      setCount: chocolateSetCount,
      progress: getProgress(
        data.chocolate?.progress ?? data.chocolateProgress,
        chocolateSetCount,
        chocolateTargetSetCount
      )
    },
    candy: {
      currentCount: candyCurrentCount,
      targetCount: candyTargetCount,
      targetSetCount: candyTargetSetCount,
      unitPerSet: candyUnitPerSet,
      setCount: candySetCount,
      progress: getProgress(
        data.candy?.progress ?? data.candyProgress,
        candySetCount,
        candyTargetSetCount
      )
    }
  };
}

function updateTargetInputs(data) {
  const chocolateTarget = document.getElementById('chocoTarget');
  const candyTarget = document.getElementById('candyTarget');

  if (chocolateTarget) {
    chocolateTarget.value = getNumber(
      data.nextTargetChocolateSetCount,
      data.targetChocolateSetCount,
      chocolateTarget.value
    );
  }

  if (candyTarget) {
    candyTarget.value = getNumber(
      data.nextTargetCandySetCount,
      data.targetCandySetCount,
      candyTarget.value
    );
  }
}

function updateWorkerCountInput(data) {
  const workerCount = document.getElementById('workerCount');

  if (workerCount) {
    workerCount.value = getNumber(
      data.nextDailyWorkerCount,
      data.dailyWorkerCount,
      workerCount.value
    );
  }
}

function getNumber(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === '') {
      continue;
    }

    const numberValue = Number(value);

    if (Number.isFinite(numberValue)) {
      return numberValue;
    }
  }

  return 0;
}

function getProgress(progress, current, target) {
  const progressValue = Number(progress);

  if (Number.isFinite(progressValue)) {
    return progressValue;
  }

  if (target <= 0) {
    return 0;
  }

  return Math.round((current / target) * 100);
}

function formatNumber(value) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return '--';
  }

  return numberValue.toLocaleString();
}

function formatProgress(value) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return '--%';
  }

  return `${Math.round(numberValue)}%`;
}

function updateComponentStatus(data) {
  const item = document.querySelector(
    `[data-component-code="${data.componentCode}"]`
  );

  if (!item) {
    return;
  }

  const statusMap = {
    NORMAL: {
      text: '정상',
      className: 'status-ok'
    },
    WARNING: {
      text: '경고',
      className: 'status-warn'
    },
    ERROR: {
      text: '오류',
      className: 'status-error'
    },
    OFFLINE: {
      text: '오프라인',
      className: 'status-offline'
    }
  };

  const componentStatus = data.status ?? data.currentStatus;
  const status = statusMap[componentStatus] ?? statusMap.OFFLINE;
  const statusText = item.querySelector('.equipment-status');

  item.classList.remove(
    'status-ok',
    'status-warn',
    'status-error',
    'status-offline'
  );

  item.classList.add(status.className);

  if (statusText) {
    statusText.textContent = status.text;
  }
}
function updateRecentAlerts(response) {
  const list = document.getElementById('recent-alert-list');

  if (!list) {
    return;
  }

  list.innerHTML = '';

  const alerts = Array.isArray(response)
    ? response
    : (
        response?.data ??
        response?.items ??
        response?.content ??
        []
      );

  const recentAlerts = [...alerts]
    .sort((a, b) => {
      return new Date(b.createdAt) - new Date(a.createdAt);
    })
    .slice(0, 5);

  // prependAlert가 맨 앞에 추가하므로 역순으로 전달한다.
  recentAlerts
    .reverse()
    .forEach(alert => prependAlert(alert));
}
function prependAlert(data) {
  const list = document.getElementById('recent-alert-list');
  if (!list) {
    return;
  }
  // QoS 1 중복 메시지 방지
  if (
    data.alertId != null &&
    list.querySelector(`[data-alert-id="${data.alertId}"]`)
  ) {
    return;
  }
  const alertConfig = {
    INFO: {
      className: 'info',
      icon: 'info'
    },
    WARNING: {
      className: 'warning',
      icon: 'triangle-alert'
    },
    ERROR: {
      className: 'critical',
      icon: 'triangle-alert'
    }
  };
  const config = alertConfig[data.alertType] ?? alertConfig.INFO;
  const item = document.createElement('li');
  item.className = `alert-item ${config.className}`;
  if (data.alertId != null) {
    item.dataset.alertId = data.alertId;
  }
  const icon = document.createElement('i');
  icon.className = 'alert-icon';
  icon.dataset.lucide = config.icon;
  const message = document.createElement('span');
  message.className = 'alert-text';
  message.textContent = data.alertMessage;
  const time = document.createElement('span');
  time.className = 'alert-time';
  time.textContent = formatAlertTime(data.createdAt);
  item.append(icon, message, time);
  list.prepend(item);
  // 최근 알림 5개만 표시
  while (list.children.length > 5) {
    list.lastElementChild.remove();
  }
  // 새로 추가한 Lucide 아이콘 렌더링
  lucide.createIcons();
}
function formatAlertTime(createdAt) {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) {
    return '--:--';
  }
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}


// 제품 분류 이미지 - 핵심 렌더링 함수
function updateRecentProductImages(items) {
  const list = document.getElementById('recent-product-list');

  if (!list) {
    return;
  }

  list.innerHTML = '';

  const productItems = normalizeRecentProductItems(items);

  if (productItems.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'product-empty';
    empty.textContent = '최근 감지 이미지가 없습니다.';
    list.append(empty);
    return;
  }

  productItems.slice(0, 5).forEach(item => {
    list.append(createRecentProductItem(item));
  });
}
function prependRecentProductDetection(detection) {
  const list = document.getElementById('recent-product-list');

  if (!list) {
    return;
  }

  const detectionId =
    detection.detectionId ??
    detection.productDetectionId;

  if (
    detectionId != null &&
    list.querySelector(`[data-detection-id="${detectionId}"]`)
  ) {
    return;
  }

  const empty = list.querySelector('.product-empty');

  if (empty) {
    empty.remove();
  }

  const item = createRecentProductItem(detection);

  if (detectionId != null) {
    item.dataset.detectionId = detectionId;
  }

  list.prepend(item);

  while (list.children.length > 5) {
    list.lastElementChild.remove();
  }
}

function normalizeRecentProductItems(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (!response || typeof response !== 'object') {
    return [];
  }

  return (
    response.data ??
    response.items ??
    response.content ??
    response.detections ??
    response.recentDetections ??
    response.recentProductDetections ??
    []
  );
}

// 카드 생성
function createRecentProductItem(item) {
  const product = getProductView(item);
  const detectedAt = item.detectedAt ?? item.detectedTime ?? item.createdAt;
  const wrapper = document.createElement('div');
  wrapper.className = 'product-item';

  wrapper.innerHTML = `
    <div class="product-thumb">
      <img src="${product.imageUrl}" alt="${product.label}">
      <span class="badge ${product.className} product-badge">${product.label}</span>
    </div>
    <div class="product-meta">
      <div class="product-meta-row">
        <span class="product-meta-label">신뢰도</span>
        <span class="product-confidence">${product.confidenceText}</span>
      </div>
      <div class="product-meta-row">
        <span class="product-meta-label">시간</span>
        <span class="product-time">${formatDetectionTime(detectedAt)}</span>
      </div>
    </div>
  `;
  const detectionId =
  item.detectionId ??
  item.productDetectionId;

  if (detectionId != null) {
    wrapper.dataset.detectionId = detectionId;
  }

  return wrapper;
}
// 제품 분류 실패 
function getProductView(item) {
  const status = item.classificationStatus ?? item.status ?? item.detectionStatus;
  const productCode =
  item.productTypeCode ??
  item.productCode ??
  item.productType ??
  item.classifiedProductCode;
  const imagePath = item.imageUrl ?? item.imagePath ?? item.photoUrl ?? item.photoPath ?? item.fileUrl;
  const confidence = item.confidence ?? item.confidenceScore ?? item.score;
  const isFailed = status === 'FAILED';

  if (isFailed) {
    return {
      label: '분류 실패',
      className: 'fail',
      imageUrl: getRecentProductImageUrl(imagePath, 'fail'),
      confidenceText: '-'
    };
  }

  const isCandy = productCode === 'CANDY';

  return {
    label: isCandy ? '사탕' : '초콜릿',
    className: isCandy ? 'candy' : 'chocolate',
    imageUrl: getRecentProductImageUrl(imagePath, isCandy ? 'candy' : 'chocolate'),
    confidenceText: formatConfidence(confidence)
  };
}

function getRecentProductImageUrl(path, type) {
  if (path && typeof getApiImageUrl === 'function') {
    return getApiImageUrl(path);
  }

  if (path) {
    return path;
  }

  if (type === 'fail') {
    return 'assets/images/fail-image1.png';
  }

  if (type === 'candy') {
    return 'assets/images/dataset/image_00017.jpg';
  }

  return 'assets/images/choco/image_00000.jpg';
}

// 시간 신뢰도 포맷
function formatConfidence(value) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return '-';
  }

  const percentValue = numberValue <= 1 ? numberValue * 100 : numberValue;

  return `${percentValue.toFixed(1)}%`;
}

function formatDetectionTime(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return '--:--';
  }

  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}

