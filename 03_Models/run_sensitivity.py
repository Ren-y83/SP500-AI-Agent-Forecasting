from pathlib import Path
import json, hashlib, sys, platform, importlib.metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
import statsmodels.api as sm
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'04_Backtesting';F=ROOT/'05_Forecast';E=ROOT/'08_Evidence'
D=pd.read_csv(ROOT/'01_Raw_Data/SP500_daily_raw.csv',parse_dates=['date']).sort_values('date').reset_index(drop=True)
D=D[D.date<=pd.Timestamp('2026-11-12')].reset_index(drop=True)
R=pd.read_csv(B/'backtest_predictions.csv')
P=R.pivot(index='origin_date',columns='model',values='APE_percent').dropna()
def hac(a,b):
    z=(P[a]-P[b]).to_numpy()
    m=sm.OLS(z,np.ones((len(z),1))).fit(cov_type='HAC',cov_kwds={'maxlags':10})
    return {'comparison':a+' minus '+b,'n':len(z),'mean_APE_difference_pp':float(m.params[0]),'95CI':[float(v) for v in m.conf_int()[0]],'t_stat':float(m.tvalues[0]),'p_value':float(m.pvalues[0]),'maxlags':10}
res={'rv20_vs_unchanged':hac('rv20_ols','unchanged_price'),'rv20_vs_historical_mean':hac('rv20_ols','historical_mean_return'),'rv20_vs_momentum5':hac('rv20_ols','momentum5_ols')}
(B/'paired_HAC.json').write_text(json.dumps(res,indent=2))
# Key modelling assumption sensitivity: RV window lengths 10, 20, 30; keep 8-day horizon and same test origins.
p=D.Close.to_numpy(float);dates=D.date.to_numpy(dtype='datetime64[ns]');ret=pd.Series(p).pct_change();idx=np.searchsorted(dates,dates+np.timedelta64(8,'D'));valid=idx<len(p)
y=np.full(len(p),np.nan);y[valid]=p[idx[valid]]/p[valid]-1
out=[];origin_set=None
for w in [10,20,30]:
    x=np.sqrt((252/w)*ret.pow(2).rolling(w).sum()).to_numpy()
    predictions={};abs_errors={}
    for j in range(len(p)):
        if D.date.iloc[j]<pd.Timestamp('2024-01-01') or not valid[j] or not np.isfinite(x[j]):continue
        train=(np.arange(len(p))<j)&valid&(idx<=j)&np.isfinite(y)&np.isfinite(x)
        if train.sum()<252:continue
        beta=np.linalg.lstsq(np.column_stack([np.ones(train.sum()),x[train]]),y[train],rcond=None)[0]
        pred=p[j]*(1+beta[0]+beta[1]*x[j]);predictions[str(D.date.iloc[j].date())]=100*abs(pred-p[idx[j]])/p[idx[j]];abs_errors[str(D.date.iloc[j].date())]=abs(pred-p[idx[j]])
    out.append({'RV_window_sessions':w,'n':len(predictions),'MAPE_percent':float(np.mean(list(predictions.values()))),'MAE_points':float(np.mean(list(abs_errors.values()))),'final_RV':float(x[-1]),'final_predicted_price':float(p[-1]*(1+np.linalg.lstsq(np.column_stack([np.ones(((np.arange(len(p))<len(p)-1)&valid&(idx<=len(p)-1)&np.isfinite(y)&np.isfinite(x)).sum()),x[(np.arange(len(p))<len(p)-1)&valid&(idx<=len(p)-1)&np.isfinite(y)&np.isfinite(x)]]),y[(np.arange(len(p))<len(p)-1)&valid&(idx<=len(p)-1)&np.isfinite(y)&np.isfinite(x)],rcond=None)[0]@np.array([1,x[-1]])))})
pd.DataFrame(out).to_csv(B/'rv_window_sensitivity.csv',index=False)
R=pd.read_csv(B/'backtest_predictions.csv');R[R.model=='rv20_ols'].nlargest(5,'APE_percent').to_csv(B/'worst_5_RV20_predictions.csv',index=False)
# Keep original horizon sensitivity for audit only, clearly secondary.
metrics=pd.read_csv(B/'backtest_metrics.csv');fig,ax=plt.subplots(figsize=(8.4,4.6))
ax.barh(metrics.model,metrics.MAPE_percent,color=['#166088','#3a7ca5','#81b1ce','#bdcbd4']);ax.invert_yaxis();ax.set_xlabel('Mean absolute percentage error (%)');ax.set_title('Matched 8-calendar-day rolling backtest (n=714 each)')
for i,v in enumerate(metrics.MAPE_percent):ax.text(v+.004,i,f'{v:.4f}%',va='center',fontsize=9)
ax.set_xlim(0,max(metrics.MAPE_percent)*1.16);fig.tight_layout();fig.savefig(B/'model_comparison.png',dpi=190);plt.close(fig)
f=json.loads((F/'final_forecast.json').read_text());base=f['metadata']['base_close'];pred=f['rv20_ols']['predicted_price']
sc=[]
for move in [-.03,-.05]:
 actual=base*(1+move)
 sc.append({'assumed_market_move_percent':move*100,'scenario_actual_index':actual,'rv20_APE_percent':100*abs(pred-actual)/actual,'unchanged_APE_percent':100*abs(base-actual)/actual})
pd.DataFrame(sc).to_csv(B/'adverse_scenario.csv',index=False)
co=f['rv20_ols']['coefficients'];drift=base*co[0];vol_contribution=base*co[1]*f['metadata']['RV20']
# Drift decomposition depends on definition: intercept is negative, not +21.8. Historical mean baseline +21.84.
decomp={'OLS_intercept_points':drift,'RV20_slope_contribution_points':vol_contribution,'total_model_change_points':pred-base,'historical_mean_return_baseline_points':f['historical_mean_return']['predicted_price']-base,'increment_vs_historical_mean_points':pred-f['historical_mean_return']['predicted_price']}
(F/'forecast_decomposition.json').write_text(json.dumps(decomp,indent=2))
versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','matplotlib','reportlab','python-pptx']}
(E/'software_versions.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'packages':versions},indent=2))
(E/'analysis_audit.json').write_text(json.dumps({'data_sha256':hashlib.sha256((ROOT/'01_Raw_Data/SP500_daily_raw.csv').read_bytes()).hexdigest(),'predictions_count':len(R),'paired_origins':len(P),'comparison':res,'model_formula':'RV20=sqrt((252/window)*sum(daily_simple_return**2))','target_rule':'first trading date on/after origin+8 calendar days','training_rule':'training_origin<test_origin and training_target_date<=test_origin','provenance':'CSV provided after official information cutoff; original retrieval time unknown'},indent=2))
print(json.dumps({'HAC':res,'window_sensitivity':out,'adverse':sc,'decomposition':decomp},indent=2))
