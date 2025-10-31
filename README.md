# Stock Price Dataset Overview

This repository contains `temp.csv`, a daily price history for three large-cap equities: Samsung Electronics (005930.KS), Apple (AAPL), and NVIDIA (NVDA). The file stores Open, High, Low, Close, and Volume columns for each ticker.

## Coverage

| Ticker | First Trading Day | Most Recent Trading Day | Trading Days |
| --- | --- | --- | ---: |
| 005930.KS | 2023-10-16 | 2025-10-10 | 482 |
| AAPL | 2023-10-16 | 2025-10-10 | 499 |
| NVDA | 2023-10-16 | 2025-10-10 | 499 |

Note: 005930.KS observes fewer sessions because the Korean exchange has different holiday and weekend schedules than the U.S. markets.

## Price Performance

- **005930.KS**: Close moved from 64,781.67 on 2023-10-16 to 94,400.00 on 2025-10-10 (+45.72% change).
- **AAPL**: Close moved from 176.99 on 2023-10-16 to 245.27 on 2025-10-10 (+38.58% change).
- **NVDA**: Close moved from 46.07 on 2023-10-16 to 183.16 on 2025-10-10 (+297.59% change).

## Daily Summary Statistics

### 005930.KS

| Metric | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| Open | 66,509.00 | 68,872.64 | 49,263.38 | 94,000.00 |
| High | 67,202.08 | 69,490.01 | 50,784.92 | 94,500.00 |
| Low | 65,822.65 | 68,408.07 | 48,968.97 | 92,700.00 |
| Close | 66,471.53 | 68,812.25 | 48,968.97 | 94,400.00 |
| Volume | 19,481,204.69 | 17,577,060.00 | 2,957,915.00 | 57,691,266.00 |

### AAPL

| Metric | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| Open | 209.29 | 210.92 | 164.17 | 257.99 |
| High | 211.47 | 213.70 | 165.21 | 259.24 |
| Low | 207.33 | 209.35 | 162.91 | 256.72 |
| Close | 209.52 | 212.02 | 163.82 | 258.10 |
| Volume | 56,558,297.39 | 50,036,300.00 | 23,234,700.00 | 318,679,900.00 |

### NVDA

| Metric | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| Open | 115.59 | 120.32 | 40.43 | 193.51 |
| High | 117.54 | 122.40 | 40.85 | 195.62 |
| Low | 113.41 | 117.41 | 39.21 | 191.06 |
| Close | 115.60 | 120.67 | 40.30 | 192.57 |
| Volume | 325,122,504.81 | 289,680,000.00 | 105,157,000.00 | 1,142,269,000.00 |

## Cross-Ticker Relationships

Daily arithmetic return correlations (based on overlapping sessions):

| Pair | Correlation | Overlapping Days |
| --- | ---: | ---: |
| 005930.KS vs AAPL | 0.112 | 464 |
| 005930.KS vs NVDA | 0.086 | 464 |
| AAPL vs NVDA | 0.374 | 498 |

Apple and NVIDIA show the strongest positive co-movement in daily returns, while Samsung Electronics exhibits only a mild relationship with the U.S.-listed stocks.

## Efficient Frontier Analysis

Using the 464 overlapping trading sessions between 2023-10-17 and 2025-10-10, we computed close-to-close arithmetic returns and enumerated long-only portfolios in 2 percentage-point weight increments to approximate the efficient frontier. Portfolios were annualized assuming 252 trading days per year.

### Annualized Standalone Performance

| Portfolio | Annualized Return | Annualized Volatility |
| --- | ---: | ---: |
| 005930.KS | 26.49% | 30.88% |
| AAPL | 24.23% | 28.24% |
| NVDA | 149.18% | 49.45% |

NVIDIA delivered the strongest growth but at the highest risk, while Apple offered the lowest standalone volatility among the three names.

### Efficient Frontier Highlights

| Portfolio | Annualized Return | Annualized Volatility | 005930.KS | AAPL | NVDA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lowest-volatility point | 24.23% | 28.24% | 0% | 100% | 0% |
| Diversified mix | 26.93% | 21.92% | 42% | 56% | 2% |
| Global minimum variance | 30.57% | 21.84% | 44% | 50% | 6% |

The diversified combinations significantly reduced volatility versus single-stock holdings while keeping expected returns in the mid-20% to low-30% range.

![Efficient frontier for Samsung Electronics, Apple, and NVIDIA](efficient_frontier.svg)

## Column Layout

The CSV file uses a three-row header where the first column holds the trade date. Subsequent columns repeat the pattern below for each ticker:

| Column Group | Description |
| --- | --- |
| Open | Opening auction price for the session |
| High | Session high price |
| Low | Session low price |
| Close | Official closing price |
| Volume | Exchange-reported share volume |
