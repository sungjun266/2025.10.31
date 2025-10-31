import csv
import json
import math
import os
from collections import defaultdict
from datetime import datetime

CSV_PATH = "temp.csv"
OUTPUT_SVG = "efficient_frontier.svg"
DOCS_SVG = "docs/assets/efficient_frontier.svg"
OUTPUT_JSON = "docs/data/analysis_summary.json"
TICKERS = []

# CSV를 읽어 종목별 종가를 수집합니다.
close_prices = defaultdict(list)  # ticker -> (날짜, 종가) 목록
with open(CSV_PATH, "r", newline="") as f:
    reader = csv.reader(f)
    header_price = next(reader)
    header_ticker = next(reader)
    header_misc = next(reader)
    # 종가 열 위치를 확인합니다.
    close_cols = []
    for idx, (ptype, ticker) in enumerate(zip(header_price, header_ticker)):
        if idx == 0:
            continue  # 날짜 열
        if ptype.strip().lower() == "close":
            close_cols.append((idx, ticker.strip()))
            if ticker.strip() not in TICKERS:
                TICKERS.append(ticker.strip())
    for row in reader:
        if not row:
            continue
        date_str = row[0].strip()
        if not date_str:
            continue
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        for col_idx, ticker in close_cols:
            value_str = row[col_idx].strip()
            if not value_str:
                continue
            close_prices[ticker].append((date, float(value_str)))

if not TICKERS:
    raise RuntimeError("No tickers found in CSV header")

# 종목별 일간 수익률을 계산합니다.
daily_returns = {}
for ticker in TICKERS:
    series = sorted(close_prices[ticker], key=lambda item: item[0])
    returns = {}
    for idx in range(1, len(series)):
        prev_date, prev_price = series[idx - 1]
        date, price = series[idx]
        if prev_price == 0:
            continue
        rtn = price / prev_price - 1.0
        returns[date] = rtn
    daily_returns[ticker] = returns

# 모든 종목에 공통으로 존재하는 거래일을 찾습니다.
common_dates = set.intersection(*(set(rtns.keys()) for rtns in daily_returns.values()))
common_dates = sorted(common_dates)
if not common_dates:
    raise RuntimeError("No overlapping return dates across tickers")

# 날짜별 수익률 행렬을 구성합니다.
return_matrix = []
for date in common_dates:
    row = [daily_returns[ticker][date] for ticker in TICKERS]
    return_matrix.append(row)

n = len(TICKERS)
m = len(return_matrix)
means = []
for j in range(n):
    mean = sum(row[j] for row in return_matrix) / m
    means.append(mean)

covariance = [[0.0 for _ in range(n)] for _ in range(n)]
for i in range(n):
    for j in range(n):
        cov = sum((row[i] - means[i]) * (row[j] - means[j]) for row in return_matrix)
        cov /= (m - 1)
        covariance[i][j] = cov

# 포트폴리오 조합을 격자 탐색으로 생성합니다.
step = 0.02
points = []
total_units = int(round(1.0 / step))


def enumerate_weights(num_assets, units_remaining, prefix_units):
    if len(prefix_units) == num_assets - 1:
        last_units = units_remaining
        if last_units < 0:
            return
        weights_units = prefix_units + [last_units]
        weight_vector = [round(unit / total_units, 4) for unit in weights_units]
        points.append(compute_portfolio(weight_vector))
        return

    start_units = 0
    end_units = units_remaining
    for units in range(start_units, end_units + 1):
        enumerate_weights(num_assets, units_remaining - units, prefix_units + [units])


def compute_portfolio(weights):
    port_mean_daily = sum(weights[k] * means[k] for k in range(n))
    port_var_daily = 0.0
    for a in range(n):
        for b in range(n):
            port_var_daily += weights[a] * weights[b] * covariance[a][b]
    if port_var_daily < 0:
        port_var_daily = 0.0
    port_vol_daily = math.sqrt(port_var_daily)
    if port_vol_daily > 0:
        sharpe = (port_mean_daily / port_vol_daily) * math.sqrt(252)
    else:
        sharpe = None
    annual_return = (1.0 + port_mean_daily) ** 252 - 1.0
    annual_vol = port_vol_daily * math.sqrt(252)
    return {
        "weights": weights,
        "annual_return": annual_return,
        "annual_vol": annual_vol,
        "mean_daily": port_mean_daily,
        "vol_daily": port_vol_daily,
        "sharpe": sharpe,
    }


enumerate_weights(n, total_units, [])

# 효율적 프런티어 상의 점들을 추출합니다.
points_sorted = sorted(points, key=lambda item: item["annual_vol"])
frontier = []
max_return_so_far = -float("inf")
for point in points_sorted:
    ret = point["annual_return"]
    if ret > max_return_so_far + 1e-9:
        frontier.append(point)
        max_return_so_far = ret

# 단일 종목 자체의 연율화 지표를 계산합니다.
asset_metrics = []
for idx, ticker in enumerate(TICKERS):
    annual_return = (1.0 + means[idx]) ** 252 - 1.0
    annual_vol = math.sqrt(covariance[idx][idx]) * math.sqrt(252)
    asset_metrics.append({
        "ticker": ticker,
        "annual_return": annual_return,
        "annual_vol": annual_vol,
        "mean_daily": means[idx],
        "vol_daily": math.sqrt(covariance[idx][idx]),
    })

# 대표 포트폴리오를 선택합니다.
gmv = min(points, key=lambda item: item["annual_vol"])
max_return_point = max(points, key=lambda item: item["annual_return"])
finite_sharpe_points = [p for p in points if not math.isnan(p["sharpe"])]
best_sharpe = max(finite_sharpe_points, key=lambda item: item["sharpe"]) if finite_sharpe_points else None

def format_pct(value):
    return f"{value * 100:.2f}%"

# 콘솔 요약을 한국어로 출력합니다.
print("사용된 공통 거래일 수:", m)
if common_dates:
    print("적용 기간:", common_dates[0], "~", common_dates[-1])
print("\n종목별 연율화 지표:")
for metric in asset_metrics:
    print(
        f"  {metric['ticker']}: 수익률={format_pct(metric['annual_return'])}, 변동성={format_pct(metric['annual_vol'])}"
    )

print("\n글로벌 최소분산 포트폴리오:")
print(
    "  비중="
    + ", ".join(
        f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, gmv["weights"])
    )
)
print(
    f"  연간 수익률={format_pct(gmv['annual_return'])}, 연간 변동성={format_pct(gmv['annual_vol'])}"
)

if best_sharpe:
    print("\n최대 샤프 지수 포트폴리오(무위험수익률 0%):")
    print(
        "  비중="
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, best_sharpe["weights"])
        )
    )
    print(
        "  연간 수익률="
        + format_pct(best_sharpe["annual_return"])
        + ", 연간 변동성="
        + format_pct(best_sharpe["annual_vol"])
        + ", 샤프="
        + f"{best_sharpe['sharpe']:.2f}"
    )

print("\n최대 기대수익 포트폴리오:")
print(
    "  비중="
    + ", ".join(
        f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, max_return_point["weights"])
    )
)
print(
    f"  연간 수익률={format_pct(max_return_point['annual_return'])}, 연간 변동성={format_pct(max_return_point['annual_vol'])}"
)

print("\n효율적 프런티어 예시 (처음 5개 조합):")
for point in frontier[:5]:
    print(
        f"  수익률={format_pct(point['annual_return'])}, 변동성={format_pct(point['annual_vol'])}, "
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, point["weights"])
        )
    )

print("\n효율적 프런티어 예시 (마지막 5개 조합):")
for point in frontier[-5:]:
    print(
        f"  수익률={format_pct(point['annual_return'])}, 변동성={format_pct(point['annual_vol'])}, "
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, point["weights"])
        )
    )

# 효율적 프런티어 SVG를 생성합니다.
width, height = 800, 520
padding = 70
plot_width = width - 2 * padding
plot_height = height - 2 * padding

all_returns = [p["annual_return"] for p in points] + [m["annual_return"] for m in asset_metrics]
all_vols = [p["annual_vol"] for p in points] + [m["annual_vol"] for m in asset_metrics]

min_return = min(all_returns)
max_return = max(all_returns)
min_vol = min(all_vols)
max_vol = max(all_vols)

# 시각적 여유를 위해 축 범위를 확장합니다.
return_padding = (max_return - min_return) * 0.1 if max_return > min_return else 0.05
vol_padding = (max_vol - min_vol) * 0.1 if max_vol > min_vol else 0.05
min_return -= return_padding
max_return += return_padding
min_vol -= vol_padding
max_vol += vol_padding

# 최대·최소 값이 동일한 경우를 보정합니다.
if min_return == max_return:
    min_return -= 0.05
    max_return += 0.05
if min_vol == max_vol:
    min_vol -= 0.05
    max_vol += 0.05


def x_coord(vol):
    ratio = (vol - min_vol) / (max_vol - min_vol)
    ratio = min(max(ratio, 0.0), 1.0)
    return padding + ratio * plot_width


def y_coord(ret):
    ratio = (ret - min_return) / (max_return - min_return)
    ratio = min(max(ratio, 0.0), 1.0)
    return height - padding - ratio * plot_height

# 축과 눈금을 그립니다.
x_ticks = 6
y_ticks = 6
svg_lines = [
    f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
    "  <style>"
    "    text { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 12px; }"
    "  </style>",
    "  <rect x='0' y='0' width='{0}' height='{1}' fill='white' />".format(width, height),
    f"  <line x1='{padding}' y1='{height - padding}' x2='{width - padding}' y2='{height - padding}' stroke='black' stroke-width='1' />",
    f"  <line x1='{padding}' y1='{padding}' x2='{padding}' y2='{height - padding}' stroke='black' stroke-width='1' />",
    f"  <text x='{width / 2}' y='{height - 20}' text-anchor='middle'>연율화 변동성</text>",
    f"  <text x='20' y='{height / 2}' text-anchor='middle' transform='rotate(-90 20 {height / 2})'>연율화 수익률</text>",
]

for i in range(x_ticks + 1):
    frac = i / x_ticks
    vol = min_vol + frac * (max_vol - min_vol)
    x = x_coord(vol)
    svg_lines.append(
        f"  <line x1='{x:.2f}' y1='{height - padding}' x2='{x:.2f}' y2='{height - padding + 6}' stroke='black' stroke-width='1' />"
    )
    svg_lines.append(
        f"  <text x='{x:.2f}' y='{height - padding + 20}' text-anchor='middle'>{format_pct(vol)}</text>"
    )

for i in range(y_ticks + 1):
    frac = i / y_ticks
    ret = min_return + frac * (max_return - min_return)
    y = y_coord(ret)
    svg_lines.append(
        f"  <line x1='{padding - 6}' y1='{y:.2f}' x2='{padding}' y2='{y:.2f}' stroke='black' stroke-width='1' />"
    )
    svg_lines.append(
        f"  <text x='{padding - 10}' y='{y + 4:.2f}' text-anchor='end'>{format_pct(ret)}</text>"
    )

# 전체 포트폴리오 조합을 옅은 점으로 표시합니다.
for point in points:
    x = x_coord(point["annual_vol"])
    y = y_coord(point["annual_return"])
    svg_lines.append(
        f"  <circle cx='{x:.2f}' cy='{y:.2f}' r='2' fill='#c7d3e3' opacity='0.6' />"
    )

# 효율적 프런티어를 선으로 연결해 표시합니다.
if len(frontier) >= 2:
    path_commands = []
    for idx, point in enumerate(frontier):
        x = x_coord(point["annual_vol"])
        y = y_coord(point["annual_return"])
        cmd = "M" if idx == 0 else "L"
        path_commands.append(f"{cmd}{x:.2f},{y:.2f}")
    path_data = " ".join(path_commands)
    svg_lines.append(
        f"  <path d='{path_data}' fill='none' stroke='#1f4e79' stroke-width='2' />"
    )

# 최소분산 포트폴리오(GMV)를 강조합니다.
x_gmv = x_coord(gmv["annual_vol"])
y_gmv = y_coord(gmv["annual_return"])
svg_lines.append(
    f"  <circle cx='{x_gmv:.2f}' cy='{y_gmv:.2f}' r='5' fill='#ffb347' stroke='#b36b00' stroke-width='1.5' />"
)
svg_lines.append(
    f"  <text x='{x_gmv + 8:.2f}' y='{y_gmv - 8:.2f}' fill='#b36b00'>GMV</text>"
)

# 개별 종목 위치를 표시합니다.
colors = ["#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
for idx, metric in enumerate(asset_metrics):
    x = x_coord(metric["annual_vol"])
    y = y_coord(metric["annual_return"])
    color = colors[idx % len(colors)]
    svg_lines.append(
        f"  <rect x='{x - 4:.2f}' y='{y - 4:.2f}' width='8' height='8' fill='{color}' stroke='black' stroke-width='1' />"
    )
    svg_lines.append(
        f"  <text x='{x + 8:.2f}' y='{y + 4:.2f}' fill='{color}'>{metric['ticker']}</text>"
    )

svg_lines.append("</svg>")

svg_content = "\n".join(svg_lines)

with open(OUTPUT_SVG, "w", encoding="utf-8") as out_svg:
    out_svg.write(svg_content)

os.makedirs(os.path.dirname(DOCS_SVG), exist_ok=True)
with open(DOCS_SVG, "w", encoding="utf-8") as out_docs_svg:
    out_docs_svg.write(svg_content)

print(f"\nSVG 파일 생성 완료: {OUTPUT_SVG} 및 {DOCS_SVG}")

# 웹페이지에서 활용할 분석 요약 JSON을 생성합니다.
os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)


def sanitize_portfolio(portfolio):
    return {
        "weights": portfolio["weights"],
        "annual_return": portfolio["annual_return"],
        "annual_vol": portfolio["annual_vol"],
        "mean_daily": portfolio["mean_daily"],
        "vol_daily": portfolio["vol_daily"],
        "sharpe": portfolio["sharpe"],
    }


summary_payload = {
    "metadata": {
        "tickers": TICKERS,
        "common_days": m,
        "start_date": common_dates[0].isoformat() if common_dates else None,
        "end_date": common_dates[-1].isoformat() if common_dates else None,
    },
    "assets": asset_metrics,
    "portfolios": {
        "gmv": sanitize_portfolio(gmv),
        "max_return": sanitize_portfolio(max_return_point),
        "max_sharpe": sanitize_portfolio(best_sharpe) if best_sharpe else None,
    },
    "frontier": [sanitize_portfolio(point) for point in frontier],
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as out_json:
    json.dump(summary_payload, out_json, ensure_ascii=False, indent=2)

print(f"JSON 파일 생성 완료: {OUTPUT_JSON}")
