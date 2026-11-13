import pandas as pd,numpy as np,json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/'01_Raw_Data/SP500_daily_raw.csv',parse_dates=['date']).sort_values('date').drop_duplicates('date')
df=df[df.date<=pd.Timestamp('2026-11-12')].reset_index(drop=True)
assert df.date.max()==pd.Timestamp('2026-11-12')
assert df.Close.notna().all() and df.date.is_unique
p=df.Close.to_numpy(dtype=float);r=pd.Series(p).pct_change();rv=np.sqrt((252/20)*r.pow(2).rolling(20).sum()).to_numpy();mom=pd.Series(p).pct_change(5).to_numpy()
dates=df.date.to_numpy(dtype='datetime64[ns]');target_dates=dates+np.timedelta64(8,'D');target_ix=np.searchsorted(dates,target_dates);valid=target_ix<len(dates)
y=np.full(len(df),np.nan);y[valid]=p[target_ix[valid]]/p[valid]-1
features={'rv20_ols':rv,'momentum5_ols':mom}
models=['rv20_ols','momentum5_ols','historical_mean_return','unchanged_price']
records=[]
def fit_predict(j,model):
    train=(np.arange(len(df))<j)&valid&(target_ix<=j)&np.isfinite(y)
    if model in features:
        x=features[model];train &=np.isfinite(x); assert train.sum()>=252
        b=np.linalg.lstsq(np.column_stack([np.ones(train.sum()),x[train]]),y[train],rcond=None)[0]
        return float(b[0]+b[1]*x[j]),int(train.sum()),[float(z) for z in b]
    if model=='historical_mean_return':return float(y[train].mean()),int(train.sum()),[]
    return 0.0,int(train.sum()),[]
for j in range(len(df)):
    if not valid[j] or df.date.iloc[j]<pd.Timestamp('2024-01-01') or not np.isfinite(rv[j]):continue
    for m in models:
        try: pred,n,coef=fit_predict(j,m)
        except (AssertionError,ValueError):continue
        predicted=p[j]*(1+pred);actual=p[target_ix[j]]
        records.append(dict(origin_date=str(df.date.iloc[j].date()),target_date=str(df.date.iloc[target_ix[j]].date()),model=m,train_n=n,forecast=predicted,actual=actual,APE_percent=100*abs(predicted-actual)/actual,AE=abs(predicted-actual)))
res=pd.DataFrame(records);res.to_csv(ROOT/'04_Backtesting/backtest_predictions.csv',index=False)
metrics=res.groupby('model').agg(n=('APE_percent','size'),MAPE_percent=('APE_percent','mean'),MAE_points=('AE','mean')).reset_index().sort_values('MAPE_percent');metrics.to_csv(ROOT/'04_Backtesting/backtest_metrics.csv',index=False)
year=res.assign(year=res.origin_date.str[:4]).groupby(['year','model']).agg(n=('APE_percent','size'),MAPE_percent=('APE_percent','mean')).reset_index();year.to_csv(ROOT/'04_Backtesting/yearly_metrics.csv',index=False)
last=len(df)-1
forecast={}
for m in models:
    pred,n,coef=fit_predict(last,m)
    forecast[m]={'training_rows':n,'predicted_return':pred,'predicted_price':float(p[last]*(1+pred)),'coefficients':coef}
forecast['metadata']={'origin_date':str(df.date.iloc[last].date()),'target_date':'2026-11-20','official_information_cutoff':'2026-11-13 12:00 Europe/London','last_market_observation':'2026-11-12 US close','base_close':float(p[last]),'RV20':float(rv[last]),'momentum5':float(mom[last]),'data_rows':len(df),'data_sha256':hashlib.sha256((ROOT/'01_Raw_Data/SP500_daily_raw.csv').read_bytes()).hexdigest(),'run_time_utc':datetime.now(timezone.utc).isoformat(),'note':'Computation and CSV upload after official cutoff. All observations dated through 2026-11-12; exact source snapshot provenance and historical revision status unverified. This is a retrospective calculation, not a pre-cutoff run.'}
(ROOT/'05_Forecast/final_forecast.json').write_text(json.dumps(forecast,indent=2),encoding='utf-8')
print(metrics.to_string(index=False));print(year.to_string(index=False));print(json.dumps(forecast,indent=2));print('leakage: training targets <= origin enforced')
