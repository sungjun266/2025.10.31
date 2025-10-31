const numberFormat = new Intl.NumberFormat('ko-KR');

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '-';
  }
  return `${(value * 100).toFixed(digits)}%`;
}

function formatSharpe(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '-';
  }
  return value.toFixed(2);
}

function renderWeights(listEl, tickers, weights) {
  listEl.innerHTML = '';
  if (!Array.isArray(weights) || !Array.isArray(tickers)) {
    listEl.innerHTML = '<li>데이터 없음</li>';
    return;
  }
  weights.forEach((weight, idx) => {
    const li = document.createElement('li');
    const ticker = tickers[idx] || `자산 ${idx + 1}`;
    li.textContent = `${ticker} ${formatPercent(weight, 1)}`;
    listEl.appendChild(li);
  });
}

function renderFrontierList(listEl, points, tickers) {
  listEl.innerHTML = '';
  points.forEach((point) => {
    const item = document.createElement('li');
    const weightText = (point.weights || [])
      .map((weight, idx) => `${tickers[idx]} ${formatPercent(weight, 1)}`)
      .join(', ');
    item.innerHTML = `
      <strong>수익률 ${formatPercent(point.annual_return)}, 변동성 ${formatPercent(
      point.annual_vol
    )}</strong>
      <span>${weightText}</span>
    `;
    listEl.appendChild(item);
  });
}

async function loadAnalysis() {
  const statusElements = {
    startDate: document.getElementById('start-date'),
    endDate: document.getElementById('end-date'),
    commonDays: document.getElementById('common-days'),
    tickers: document.getElementById('tickers'),
    assetRows: document.getElementById('asset-rows'),
    gmv: {
      returnEl: document.getElementById('gmv-return'),
      volEl: document.getElementById('gmv-vol'),
      sharpeEl: document.getElementById('gmv-sharpe'),
      weightsEl: document.getElementById('gmv-weights'),
    },
    maxSharpe: {
      returnEl: document.getElementById('sharpe-return'),
      volEl: document.getElementById('sharpe-vol'),
      sharpeEl: document.getElementById('sharpe-value'),
      weightsEl: document.getElementById('sharpe-weights'),
    },
    maxReturn: {
      returnEl: document.getElementById('max-return'),
      volEl: document.getElementById('max-vol'),
      sharpeEl: document.getElementById('max-sharpe'),
      weightsEl: document.getElementById('max-weights'),
    },
    frontierStart: document.getElementById('frontier-start'),
    frontierEnd: document.getElementById('frontier-end'),
  };

  try {
    const response = await fetch('data/analysis_summary.json');
    if (!response.ok) {
      throw new Error(`요약 데이터를 불러오지 못했습니다: ${response.status}`);
    }
    const data = await response.json();

    const tickers = data.metadata?.tickers ?? [];

    statusElements.startDate.textContent = data.metadata?.start_date ?? '-';
    statusElements.endDate.textContent = data.metadata?.end_date ?? '-';
    statusElements.commonDays.textContent = numberFormat.format(
      data.metadata?.common_days ?? 0
    );
    statusElements.tickers.textContent = tickers.join(' · ');

    const assets = Array.isArray(data.assets) ? data.assets : [];
    statusElements.assetRows.innerHTML = '';
    assets.forEach((asset) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <th scope="row">${asset.ticker}</th>
        <td>${formatPercent(asset.annual_return)}</td>
        <td>${formatPercent(asset.annual_vol)}</td>
        <td>${formatPercent(asset.mean_daily)}</td>
        <td>${formatPercent(asset.vol_daily)}</td>
      `;
      statusElements.assetRows.appendChild(row);
    });

    const gmv = data.portfolios?.gmv;
    if (gmv) {
      statusElements.gmv.returnEl.textContent = formatPercent(gmv.annual_return);
      statusElements.gmv.volEl.textContent = formatPercent(gmv.annual_vol);
      statusElements.gmv.sharpeEl.textContent = formatSharpe(gmv.sharpe);
      renderWeights(statusElements.gmv.weightsEl, tickers, gmv.weights);
    }

    const maxSharpe = data.portfolios?.max_sharpe;
    if (maxSharpe) {
      statusElements.maxSharpe.returnEl.textContent = formatPercent(maxSharpe.annual_return);
      statusElements.maxSharpe.volEl.textContent = formatPercent(maxSharpe.annual_vol);
      statusElements.maxSharpe.sharpeEl.textContent = formatSharpe(maxSharpe.sharpe);
      renderWeights(statusElements.maxSharpe.weightsEl, tickers, maxSharpe.weights);
    } else {
      statusElements.maxSharpe.returnEl.textContent = '-';
      statusElements.maxSharpe.volEl.textContent = '-';
      statusElements.maxSharpe.sharpeEl.textContent = '-';
      statusElements.maxSharpe.weightsEl.innerHTML = '<li>데이터 없음</li>';
    }

    const maxReturn = data.portfolios?.max_return;
    if (maxReturn) {
      statusElements.maxReturn.returnEl.textContent = formatPercent(maxReturn.annual_return);
      statusElements.maxReturn.volEl.textContent = formatPercent(maxReturn.annual_vol);
      statusElements.maxReturn.sharpeEl.textContent = formatSharpe(maxReturn.sharpe);
      renderWeights(statusElements.maxReturn.weightsEl, tickers, maxReturn.weights);
    }

    const frontier = Array.isArray(data.frontier) ? data.frontier : [];
    const previewCount = Math.min(5, frontier.length);
    renderFrontierList(statusElements.frontierStart, frontier.slice(0, previewCount), tickers);
    renderFrontierList(
      statusElements.frontierEnd,
      previewCount > 0 ? frontier.slice(-previewCount) : [],
      tickers
    );
  } catch (error) {
    console.error(error);
    statusElements.assetRows.innerHTML =
      '<tr><td colspan="5">요약 데이터를 불러오는 데 실패했습니다.</td></tr>';
    statusElements.frontierStart.innerHTML = '<li>데이터 없음</li>';
    statusElements.frontierEnd.innerHTML = '<li>데이터 없음</li>';
  }
}

document.addEventListener('DOMContentLoaded', loadAnalysis);
