let productionChart = null;
let ratioChart = null;

const defaultProductionData = {
  labels: [
    '00:00', '02:00', '04:00', '06:00', '08:00', '10:00',
    '12:00', '14:00', '16:00', '18:00', '20:00', '22:00', '24:00'
  ],
  chocolate: Array(13).fill(0),
  candy: Array(13).fill(0),
  goals: {}
};
let productionView = 'hourly';
let latestProductionData = defaultProductionData;

function buildProductionDatasets(data) {
  const cumulative = productionView === 'cumulative';
  const datasets = [];
  for (const [key, label, color, background] of [
    ['chocolate', '초콜릿', '#2563eb', 'rgba(37,99,235,0.1)'],
    ['candy', '사탕', '#22c55e', 'rgba(34,197,94,0.1)']
  ]) {
    let total = 0;
    const values = data[key].map(value => {
      const count = Number(value) || 0;
      total += count;
      return cumulative ? total : count;
    });
    datasets.push({ label, data: values, borderColor: color, backgroundColor: background,
      fill: true, pointRadius: 2, borderWidth: 2,
      tension: cumulative ? 0 : 0.35,
      cubicInterpolationMode: cumulative ? 'default' : 'monotone' });
  }
  if (cumulative) {
    for (const [key, label, color] of [
      ['chocolate', '초콜릿 목표', '#2563eb'], ['candy', '사탕 목표', '#22c55e']
    ]) {
      const goal = data.goals?.[key];
      if (goal == null || !Number.isFinite(Number(goal)) || Number(goal) <= 0) continue;
      datasets.push({ label, data: Array(data.labels.length).fill(Number(goal)),
        borderColor: color, borderDash: key === 'chocolate' ? [6, 4] : [2, 4],
        borderWidth: 1.5, pointRadius: 0, fill: false });
    }
  }
  return datasets;
}

function setProductionView(view) {
  if (!['hourly', 'cumulative'].includes(view)) return;
  productionView = view;
  const title = document.getElementById('productionChartTitle');
  if (title) title.textContent = view === 'hourly' ? '시간대별 생산량(오늘)' : '누적 생산량(오늘)';
  document.querySelectorAll('[data-production-view]').forEach(button => {
    const active = button.dataset.productionView === view;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  updateProductionChart(latestProductionData);
}

const defaultRatioData = {
  chocolate: 0,
  candy: 0
};

function initDashboardCharts() {
  initProductionChart(defaultProductionData);
  initRatioChart(defaultRatioData);
  document.querySelectorAll('[data-production-view]').forEach(button => {
    button.addEventListener('click', () => setProductionView(button.dataset.productionView));
  });
}

// 생산량 차트
function initProductionChart(data) {
  latestProductionData = data;
  const productionCtx = document.getElementById('productionChart');

  if (!productionCtx) {
    return;
  }

  productionChart = new Chart(productionCtx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: buildProductionDatasets(data)
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            color: '#43515a',
            font: { size: 11, weight: '600' }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#7a858b', font: { size: 10 } }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: '생산량 (개)' },
          ticks: { precision: 0, color: '#7a858b', font: { size: 10 } },
          grid: { color: 'rgba(23,33,38,0.08)' }
        }
      }
    }
  });
}

//생산량 차트 갱신
function updateProductionChart(data) {
  latestProductionData = data;
  if (!productionChart) {
    initProductionChart(data);
    return;
  }

  productionChart.data.labels = data.labels;
  productionChart.data.datasets = buildProductionDatasets(data);

  productionChart.update();
}

// 비율 차트(도넛)
function initRatioChart(data) {
  const ratioCtx = document.getElementById('ratioChart');

  if (!ratioCtx) {
    return;
  }

  ratioChart = new Chart(ratioCtx, {
    type: 'doughnut',
    data: {
      labels: ['초콜릿', '사탕'],
      datasets: [
        {
          data: getRatioChartValues(data),
          backgroundColor: getRatioChartColors(data),
          borderColor: '#ffffff',
          borderWidth: 4,
          hoverOffset: 2,
          cutout: '68%'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// 비율 차트 갱신
function updateRatioChart(data) {
  if (!ratioChart) {
    initRatioChart(data);
  }

  ratioChart.data.datasets[0].data = [
    ...getRatioChartValues(data)
  ];
  ratioChart.data.datasets[0].backgroundColor = getRatioChartColors(data);

  ratioChart.update();
  updateRatioLegend(data);
}

function updateRatioLegend(data) {
  const chocolateElement = document.getElementById('ratio-chocolate-legend');
  const candyElement = document.getElementById('ratio-candy-legend');

  if (chocolateElement) {
    chocolateElement.textContent = `초콜릿 ${formatRatioValue(data.chocolate)}%`;
  }

  if (candyElement) {
    candyElement.textContent = `사탕 ${formatRatioValue(data.candy)}%`;
  }
}

function formatRatioValue(value) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return 0;
  }

  return Math.round(numberValue);
}

function getRatioChartValues(data) {
  const chocolate = Number(data.chocolate) || 0;
  const candy = Number(data.candy) || 0;

  if (chocolate + candy <= 0) {
    return [1, 0];
  }

  return [chocolate, candy];
}

function getRatioChartColors(data) {
  const chocolate = Number(data.chocolate) || 0;
  const candy = Number(data.candy) || 0;

  if (chocolate + candy <= 0) {
    return ['#d5dbe0', 'rgba(0, 0, 0, 0)'];
  }

  return ['#2563eb', '#22c55e'];
}
