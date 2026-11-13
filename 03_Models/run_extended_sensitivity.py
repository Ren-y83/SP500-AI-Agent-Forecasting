"""Supplementary analysis (run AFTER run_final.py). Python 3 + pandas + numpy (+ matplotlib for the PNG).
Outputs in 04_Backtesting/: sensitivity_forecast.csv, horizon_sensitivity.csv, paired_HAC.json,
paired_tests_extra.json, adverse_scenario.csv, model_comparison.png
Labelling rule (same as run_final.py): label = first trading close on/after origin + h calendar days (h=8 for the
target); a training row is used only if its target date <= the forecast origin (no future labels).
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
BT = ROOT / '04_Backtesting'
df = (pd.read_csv(ROOT/'01_Raw_Data/SP500_daily_raw.csv', parse_dates=['date'])
        .sort_values('date').drop_duplicates('date'))
df = df[df.date <= pd.Timestamp('2026-11-12')].reset_index(drop=True)
p = df.Close.to_numpy(float); r = pd.Series(p).pct_change()
dates = df.date.to_numpy('datetime64[ns]'); N = len(df)

def rv(w): return np.sqrt((252/w)*r.pow(2).rolling(w).sum()).to_numpy()
def labels(h):
    tix = np.searchsorted(dates, dates + np.timedelta64(h, 'D')); valid = tix < N
    y = np.full(N, np.nan); y[valid] = p[tix[valid]]/p[valid]-1
    return tix, valid, y
def fit_predict(x, j, h=8, train_years=None, min_n=252):
    tix, valid, y = labels(h)
    m = (np.arange(N) < j) & valid & (tix <= j) & np.isfinite(y) & np.isfinite(x)
    if train_years is not None: m &= dates >= dates[j] - np.timedelta64(int(365.25*train_years), 'D')
    if m.sum() < min_n: return np.nan
    b = np.linalg.lstsq(np.column_stack([np.ones(m.sum()), x[m]]), y[m], rcond=None)[0]
    return float(b[0] + b[1]*x[j])
def hist_mean(j, h=8):
    tix, valid, y = labels(h)
    m = (np.arange(N) < j) & valid & (tix <= j) & np.isfinite(y); return float(y[m].mean())
def nw(d, L=10):
    d = np.asarray(d, float); n = len(d); mu = d.mean(); e = d-mu; s = e@e/n
    for k in range(1, L+1): s += 2*(1-k/(L+1))*(e[k:]@e[:-k])/n
    se = math.sqrt(s/n); t = mu/se; pv = math.erfc(abs(t)/math.sqrt(2))
    return mu, se, t, pv, mu-1.96*se, mu+1.96*se

last = N-1
# 1) sensitivity of the final forecast to the key assumptions (RV window, training window)
rows = []
for w in (10, 20, 60):
    for ty in (None, 5, 3):
        pr = fit_predict(rv(w), last, 8, ty)
        rows.append(dict(rv_window=w, train_window='expanding' if ty is None else f'{ty}y',
                         predicted_return_pct=100*pr, forecast=p[last]*(1+pr)))
pd.DataFrame(rows).to_csv(BT/'sensitivity_forecast.csv', index=False)

# 2) evaluation-horizon diagnostic (7/8/9 calendar days), RV20 model, origins from 2024-01-01
hz = []; x20 = rv(20)
for h in (7, 8, 9):
    tix, valid, y = labels(h); ape = []
    for j in range(N):
        if not valid[j] or dates[j] < np.datetime64('2024-01-01') or not np.isfinite(x20[j]): continue
        pr = fit_predict(x20, j, h)
        if np.isnan(pr): continue
        f = p[j]*(1+pr); a = p[tix[j]]; ape.append(100*abs(f-a)/a)
    hz.append(dict(calendar_days=h, n=len(ape), MAPE_percent=float(np.mean(ape))))
pd.DataFrame(hz).to_csv(BT/'horizon_sensitivity.csv', index=False)

# 3) paired tests on the saved backtest (Newey-West / HAC, 10 lags)
bt = pd.read_csv(BT/'backtest_predictions.csv')
w = bt.pivot(index='origin_date', columns='model', values='APE_percent').dropna()
out = {}
for a, b in (('rv20_ols','unchanged_price'), ('rv20_ols','historical_mean_return'),
             ('historical_mean_return','unchanged_price'), ('rv20_ols','momentum5_ols')):
    mu, se, t, pv, lo, hi = nw(w[a]-w[b])
    out[f'{a}_minus_{b}'] = dict(mean_APE_diff_pp=mu, se=se, t=t, p_value=pv, ci95=[lo, hi], maxlags=10)
mu, se, t, pv, lo, hi = nw(w['rv20_ols']-w['unchanged_price'])
(BT/'paired_HAC.json').write_text(json.dumps(dict(mean_APE_difference_pp=mu, **{'95CI':[lo, hi]}, p_value=pv, maxlags=10), indent=2))
(BT/'paired_tests_extra.json').write_text(json.dumps(out, indent=2))

# 4) adverse scenario and forecast decomposition
base = fit_predict(x20, last); hm = hist_mean(last); sc = []
for shock in (-0.05, -0.03, 0.0, 0.03):
    a = p[last]*(1+shock)
    for name, f in (('rv20_ols', p[last]*(1+base)), ('unchanged_price', p[last]), ('historical_mean_return', p[last]*(1+hm))):
        sc.append(dict(scenario_return_pct=100*shock, model=name, forecast=f, APE_percent=100*abs(f-a)/a))
pd.DataFrame(sc).to_csv(BT/'adverse_scenario.csv', index=False)
dec = dict(base_close=p[last], drift_points=p[last]*hm, rv20_increment_points=p[last]*(base-hm), forecast=p[last]*(1+base),
           rv20_now=float(x20[last]), rv20_median_since_2018=float(np.nanmedian(x20)),
           rv20_percentile_since_2018=float((x20[np.isfinite(x20)] < x20[last]).mean()*100))
(BT/'decomposition.json').write_text(json.dumps(dec, indent=2)); print(json.dumps(dec, indent=2))

# 5) figure
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    m = pd.read_csv(BT/'backtest_metrics.csv'); ym = pd.read_csv(BT/'yearly_metrics.csv')
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].barh(m.model[::-1], m.MAPE_percent[::-1], color=['#9aa5b1','#9aa5b1','#9aa5b1','#1f4e79'][::-1] if False else '#1f4e79')
    ax[0].set_xlim(1.5, 1.62); ax[0].set_xlabel('MAPE % (8-calendar-day horizon, 714 origins, 2024-2026)'); ax[0].set_title('Pooled backtest MAPE')
    for i, v in enumerate(m.MAPE_percent[::-1]): ax[0].text(v+0.001, i, f'{v:.3f}', va='center', fontsize=8)
    pv_ = ym.pivot(index='year', columns='model', values='MAPE_percent')
    pv_.plot.bar(ax=ax[1], rot=0, width=0.8); ax[1].set_ylim(1.3, 1.9); ax[1].set_ylabel('MAPE %'); ax[1].set_title('By year (RV20 lost to others in 2024)')
    ax[1].legend(fontsize=7); plt.tight_layout(); plt.savefig(BT/'model_comparison.png', dpi=160)
except Exception as e: print('figure skipped:', e)
print(pd.DataFrame(rows).round(4).to_string(index=False)); print(pd.DataFrame(hz).round(4).to_string(index=False))
print(json.dumps(out, indent=1)[:900])
