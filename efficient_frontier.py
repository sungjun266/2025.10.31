import csv
import math
from collections import defaultdict
from datetime import datetime

CSV_PATH = "temp.csv"
OUTPUT_SVG = "efficient_frontier.svg"
TICKERS = []

# Read CSV and capture close prices per ticker
close_prices = defaultdict(list)  # ticker -> list of (date, close)
with open(CSV_PATH, "r", newline="") as f:
    reader = csv.reader(f)
    header_price = next(reader)
    header_ticker = next(reader)
    header_misc = next(reader)
    # Identify close price columns
    close_cols = []
    for idx, (ptype, ticker) in enumerate(zip(header_price, header_ticker)):
        if idx == 0:
            continue  # date column
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

# Compute daily returns per ticker
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

# Determine overlapping dates across all tickers
common_dates = set.intersection(*(set(rtns.keys()) for rtns in daily_returns.values()))
common_dates = sorted(common_dates)
if not common_dates:
    raise RuntimeError("No overlapping return dates across tickers")

# Build matrix of returns per date
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

# Portfolio grid search
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
        sharpe = float("nan")
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

# Efficient frontier extraction
points_sorted = sorted(points, key=lambda item: item["annual_vol"])
frontier = []
max_return_so_far = -float("inf")
for point in points_sorted:
    ret = point["annual_return"]
    if ret > max_return_so_far + 1e-9:
        frontier.append(point)
        max_return_so_far = ret

# Asset-only metrics
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

# Identify global minimum variance portfolio
gmv = min(points, key=lambda item: item["annual_vol"])
max_return_point = max(points, key=lambda item: item["annual_return"])
finite_sharpe_points = [p for p in points if not math.isnan(p["sharpe"])]
best_sharpe = max(finite_sharpe_points, key=lambda item: item["sharpe"]) if finite_sharpe_points else None

def format_pct(value):
    return f"{value * 100:.2f}%"

# Produce text summary for console output
print("Common trading days used:", m)
if common_dates:
    print("Date range:", common_dates[0], "to", common_dates[-1])
print("\nPer-asset annualized metrics:")
for metric in asset_metrics:
    print(
        f"  {metric['ticker']}: return={format_pct(metric['annual_return'])}, vol={format_pct(metric['annual_vol'])}"
    )

print("\nGlobal minimum variance portfolio:")
print(
    "  weights="
    + ", ".join(
        f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, gmv["weights"])
    )
)
print(
    f"  annual return={format_pct(gmv['annual_return'])}, annual vol={format_pct(gmv['annual_vol'])}"
)

if best_sharpe:
    print("\nMaximum Sharpe ratio portfolio (risk-free 0%):")
    print(
        "  weights="
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, best_sharpe["weights"])
        )
    )
    print(
        "  annual return="
        + format_pct(best_sharpe["annual_return"])
        + ", annual vol="
        + format_pct(best_sharpe["annual_vol"])
        + ", Sharpe="
        + f"{best_sharpe['sharpe']:.2f}"
    )

print("\nMaximum return portfolio:")
print(
    "  weights="
    + ", ".join(
        f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, max_return_point["weights"])
    )
)
print(
    f"  annual return={format_pct(max_return_point['annual_return'])}, annual vol={format_pct(max_return_point['annual_vol'])}"
)

print("\nEfficient frontier sample (first 5 points):")
for point in frontier[:5]:
    print(
        f"  return={format_pct(point['annual_return'])}, vol={format_pct(point['annual_vol'])}, "
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, point["weights"])
        )
    )

print("\nEfficient frontier sample (last 5 points):")
for point in frontier[-5:]:
    print(
        f"  return={format_pct(point['annual_return'])}, vol={format_pct(point['annual_vol'])}, "
        + ", ".join(
            f"{ticker} {weight * 100:.1f}%" for ticker, weight in zip(TICKERS, point["weights"])
        )
    )

# Build SVG visualization
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

# Expand ranges slightly for padding
return_padding = (max_return - min_return) * 0.1 if max_return > min_return else 0.05
vol_padding = (max_vol - min_vol) * 0.1 if max_vol > min_vol else 0.05
min_return -= return_padding
max_return += return_padding
min_vol -= vol_padding
max_vol += vol_padding

# Guard for identical values
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

# Axes and tick marks
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
    f"  <text x='{width / 2}' y='{height - 20}' text-anchor='middle'>Annualized Volatility</text>",
    f"  <text x='20' y='{height / 2}' text-anchor='middle' transform='rotate(-90 20 {height / 2})'>Annualized Return</text>",
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

# Plot all portfolios as faint points
for point in points:
    x = x_coord(point["annual_vol"])
    y = y_coord(point["annual_return"])
    svg_lines.append(
        f"  <circle cx='{x:.2f}' cy='{y:.2f}' r='2' fill='#c7d3e3' opacity='0.6' />"
    )

# Plot efficient frontier as connected line
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

# Highlight GMV
x_gmv = x_coord(gmv["annual_vol"])
y_gmv = y_coord(gmv["annual_return"])
svg_lines.append(
    f"  <circle cx='{x_gmv:.2f}' cy='{y_gmv:.2f}' r='5' fill='#ffb347' stroke='#b36b00' stroke-width='1.5' />"
)
svg_lines.append(
    f"  <text x='{x_gmv + 8:.2f}' y='{y_gmv - 8:.2f}' fill='#b36b00'>GMV</text>"
)

# Plot individual assets
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

with open(OUTPUT_SVG, "w", encoding="utf-8") as out_svg:
    out_svg.write("\n".join(svg_lines))

print(f"\nSVG written to {OUTPUT_SVG}")
