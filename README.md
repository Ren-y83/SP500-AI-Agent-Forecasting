# S&P 500 AI-Assisted Forecasting — IFTE0007

## Forecast

- **Target:** Official S&P 500 price-index close, 20 November 2026 at 16:00 New York time (21:00 GMT).
- **Binding point forecast:** **7,627.41 index points**.
- **Information cutoff:** 13 November 2026, 12:00 GMT.
- **Last market observation:** 12 November 2026, S&P 500 close of approximately 7,592.40.
- **Chosen model:** Expanding-window ordinary least squares (OLS) regression using 20-trading-day annualised realised volatility (RV20) to predict the forward 8-calendar-day simple return.

## Results

Rolling-origin evaluation across 714 matched origins (2024–2026) gives the following mean absolute percentage errors (MAPE):

| Model | MAPE |
| --- | ---: |
| RV20 OLS | 1.5569% |
| Momentum-5 OLS | 1.5610% |
| Historical mean return | 1.5644% |
| Unchanged price | 1.5965% |

The RV20 model has the lowest pooled MAPE in this comparison; the advantage over the historical-mean benchmark is small and not statistically robust. These are retrospective historical tests, not guaranteed future accuracy.

## Repository structure

- `01_Raw_Data/SP500_daily_raw.csv` — frozen daily historical S&P 500 dataset.
- `03_Models/run_final.py` — main model, historical rolling backtest, forecast and time-order checks.
- `03_Models/run_sensitivity.py` — sensitivity analyses, HAC tests, figures.
- `03_Models/run_extended_sensitivity.py` — additional diagnostics.
- `03_Models/make_workflow_diagram.py` — workflow illustration script.
- `04_Backtesting/` — historical predictions, metrics, robustness results and plots.
- `05_Forecast/` — saved forecast results and fixed forecast records.
- `08_Evidence/` — selected non-conversation reproduction and provenance notes.

## Reproduce offline

Python 3 is required. Install dependencies if needed:

```bash
python -m pip install numpy pandas scipy statsmodels matplotlib
```

From the **repository root**, run:

```bash
python 03_Models/run_final.py
python 03_Models/run_sensitivity.py
python 03_Models/run_extended_sensitivity.py
```

These scripts use the **included CSV only**; they do not fetch current prices. Check `05_Forecast/final_forecast.json` for `rv20_ols.predicted_price` (approximately `7627.408185`, rounded to **7627.41**) and `04_Backtesting/backtest_metrics.csv` for 714 RV20 predictions and approximately 1.5569% MAPE.

**Important:** Running the scripts overwrites some generated output files and updates `run_time_utc`. Preserve the original repository revision when comparing historical outputs. The included `08_Evidence/POST_CUTOFF_FROZEN_DATA_REPRODUCTION_LOG.txt` documents an actual local reproduction on 13 November 2026 at 15:27 UTC.

## Data provenance and timing limitations

The historical data are attributed to Yahoo Finance (`^GSPC`). The final CSV's local filesystem save timestamp was recorded as 13 November 2026 at 12:36:06 GMT, **not** as a verified HTTP retrieval time. The exact network download time was not logged. The frozen data contain no market observations after 12 November 2026, but this does not independently verify historical revision status or the original download time. Final computation and approval took place after the official information cutoff; this is **not** represented as a pre-cutoff run. Permission for post-cutoff computation was reported by the student but written confirmation is not attached.

The workflow was AI-assisted: ChatGPT suggested analyses and commands, while the student manually ran Python and reviewed outputs. No claim of a complete autonomous agent tool-call trace is made. The complete private ChatGPT conversation export is intentionally **not** published in this public repository.

## Notes

This repository is a reproducibility record for coursework, not investment advice. The final target level will be known only after the target close.
