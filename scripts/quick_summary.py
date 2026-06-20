import warnings,warnings,sys
warnings.filterwarnings('ignore')
import pandas as pd
df = pd.read_pickle('data/processed/nhanes_gdm_merged.pkl')
sub = df[df['pregnant'].notna() & (df['age'] >= 15) & (df['age'] <= 49)].copy()
sub = sub[sub['gdm_self_report'].notna() | sub['gdm_glucose'].notna()].copy()
sub = sub[sub['lead_ugdl'].notna() | sub['mercury_ugl'].notna()].copy()
print(f'Analytic sample: {len(sub):,}')
print(f'GDM rate: {sub["gdm"].mean()*100:.2f}%')
print(f'GDM cases: {sub["gdm"].sum():,}')
print(f'Mean age: {sub["age"].mean():.1f}')
print(f'Mean lead: {sub["lead_ugdl"].mean():.3f}')
print(f'Mean mercury: {sub["mercury_ugl"].mean():.3f}')
print(f'Mean BMI: {sub["bmi"].mean():.1f}')
print()
for race in sub['race_group'].dropna().unique():
    rsub = sub[sub['race_group'] == race]
    print(f'{race}: n={len(rsub):,}, GDM={rsub["gdm"].mean()*100:.1f}%')
