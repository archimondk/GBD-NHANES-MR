import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np; import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial

PROJ = Path('C:/Users/008bu/Documents/GBD-NHANES-MR')
TBL = PROJ / 'output' / 'tables'

df = pd.read_pickle(str(PROJ / 'data' / 'processed' / 'nhanes_gdm_merged.pkl'))
sub = df[df['pregnant'].notna()].copy()
sub = sub[(sub['age'] >= 15) & (sub['age'] <= 49)].copy()
sub = sub[sub['gdm_self_report'].notna() | sub['gdm_glucose'].notna()].copy()
sub = sub[sub['lead_ugdl'].notna() | sub['mercury_ugl'].notna()].copy()
sub['gdm'] = sub['gdm'].astype(int)
sub['pregnant_now'] = (sub['pregnant'] == 1).astype(int)
sub['education'] = sub['education'].fillna(3)

rd = pd.get_dummies(sub['race_group'], prefix='race', drop_first=True).astype(int)
for c in rd.columns: sub[c] = rd[c].values
for m in ['lead','mercury','cadmium']:
    col = m+'_ugdl' if m=='lead' else m+'_ugl'
    sub[m+'_log'] = np.log(sub[col].values + 1e-6)

n = len(sub); g = sub['gdm'].sum()
print(f'Sample: {n:,}, GDM: {g:,} ({g/n*100:.1f}%)')

core = ['lead_log','mercury_log','cadmium_log','age','bmi','education','pregnant_now']
race_cols = [c for c in rd.columns]
all_feats = core + race_cols
print(f'Race dummies: {race_cols}')

def run_wlogit(df, feats, name):
    data = df[feats + ['gdm','wt_final']].dropna()
    y = data['gdm'].values.astype(np.float64)
    w = data['wt_final'].values.astype(np.float64)
    Xdf = data[feats].copy().astype(np.float64)
    Xdf.insert(0, 'const', 1.0)
    w_norm = w / w.sum() * len(w)
    res = sm.GLM(y, Xdf.values, family=Binomial(), freq_weights=w_norm).fit(cov_type='HC0')
    cdf = pd.DataFrame({
        'Feature': Xdf.columns,
        'OR': np.exp(res.params),
        'CI_lo': np.exp(res.params - 1.96 * res.bse),
        'CI_hi': np.exp(res.params + 1.96 * res.bse),
        'P': res.pvalues
    })
    cdf['Sig'] = cdf['P'].apply(lambda p: '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns')
    cdf.to_csv(str(TBL / (name + '.csv')), index=False)
    print(f'\n{name}:')
    print(cdf.to_string(index=False))
    return cdf

# 1. Full model
r1 = run_wlogit(sub, all_feats, 'logistic_full_model')

# 2. Core model
r2 = run_wlogit(sub, core, 'logistic_core_model')

# 3. Subgroup by race
print('\n=== Subgroup: Race ===')
race_list = sorted(sub['race_group'].dropna().unique())
for race in race_list:
    sub_r = sub[sub['race_group'] == race].copy()
    tag = race.replace(' ', '_')
    if len(sub_r) >= 200 and sub_r['gdm'].sum() >= 20:
        run_wlogit(sub_r, core, 'subgroup_' + tag)

# 4. Metal mixture
print('\n=== Metal Mixture ===')
complete = sub[core + ['gdm','wt_final']].dropna()
base = ['age','bmi','pregnant_now','education']
for m in ['lead_log','mercury_log','cadmium_log']:
    run_wlogit(complete, base + [m], 'single_metal_' + m)
run_wlogit(complete, base + ['lead_log','mercury_log','cadmium_log'], 'all_metals_joint')

print('\nDone!')
