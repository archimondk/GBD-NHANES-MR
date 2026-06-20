import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np; import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler

PROJ = Path('C:/Users/008bu/Documents/GBD-NHANES-MR')
FIG = PROJ / 'output' / 'figures'
TBL = PROJ / 'output' / 'tables'
sns.set_style('whitegrid')
plt.rcParams.update({'figure.max_open_warning': 0, 'font.size': 11})

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

core = ['lead_log','mercury_log','cadmium_log','age','bmi','education','pregnant_now']
race_cols = [c for c in rd.columns]
all_feats = core + race_cols

ml_df = sub[all_feats + ['gdm']].dropna()
print(f'ML sample: {len(ml_df):,}, GDM: {ml_df.gdm.sum():,}')

X = ml_df[all_feats].values.astype(np.float64)
y = ml_df['gdm'].values
Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler()
Xt = scaler.fit_transform(Xt); Xv = scaler.transform(Xv)
print(f'Train: {len(Xt):,}, Test: {len(Xv):,}')

# XGBoost with grid search
xg = GridSearchCV(xgb.XGBClassifier(random_state=42, eval_metric='auc', verbosity=0),
    {'n_estimators':[200,300], 'max_depth':[4,6], 'learning_rate':[0.03,0.05],
     'subsample':[0.8], 'colsample_bytree':[0.8]},
    cv=3, scoring='roc_auc', n_jobs=-1, verbose=0)
xg.fit(Xt, yt)
xgb_best = xg.best_estimator_
print(f'XGBoost params: {xg.best_params_}')

# Random Forest
rg = GridSearchCV(RandomForestClassifier(random_state=42, n_jobs=-1),
    {'n_estimators':[200,300,500], 'max_depth':[4,6,8], 'min_samples_leaf':[10,20,50]},
    cv=3, scoring='roc_auc', n_jobs=-1, verbose=0)
rg.fit(Xt, yt)
rf_best = rg.best_estimator_
print(f'RF params: {rg.best_params_}')

# Evaluate
results = []
for name, model, pr_func in [('XGBoost', xgb_best, lambda m: m.predict_proba(Xv)[:,1]),
                               ('Random Forest', rf_best, lambda m: m.predict_proba(Xv)[:,1])]:
    pr = pr_func(model)
    auc = roc_auc_score(yv, pr)
    yp = (pr >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(yv, yp).ravel()
    sens = tp/(tp+fn) if (tp+fn)>0 else 0
    spec = tn/(tn+fp) if (tn+fp)>0 else 0
    prec = tp/(tp+fp) if (tp+fp)>0 else 0
    f1 = 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn)>0 else 0
    print(f'{name}: AUC={auc:.4f}, Sens={sens:.3f}, Spec={spec:.3f}, Prec={prec:.3f}, F1={f1:.3f}')
    results.append({'Model':name,'AUC':round(auc,4),'Sensitivity':round(sens,3),
                    'Specificity':round(spec,3),'Precision':round(prec,3),'F1':round(f1,3)})
pd.DataFrame(results).to_csv(str(TBL/'model_performance_enhanced.csv'), index=False)

# ROC plot
fig, ax = plt.subplots(figsize=(8,7))
for name, pr_func in [('XGBoost', lambda: xgb_best.predict_proba(Xv)[:,1]),
                       ('Random Forest', lambda: rf_best.predict_proba(Xv)[:,1])]:
    pr = pr_func()
    fpr, tpr, _ = roc_curve(yv, pr)
    c = '#2C3E50' if name=='XGBoost' else '#E74C3C'
    ls = '-' if name=='XGBoost' else '--'
    ax.plot(fpr, tpr, ls, lw=2.5, color=c, label=f'{name} (AUC={roc_auc_score(yv, pr):.3f})')
ax.plot([0,1],[0,1],'k--',lw=1,alpha=0.5)
ax.set_xlabel('1 - Specificity'); ax.set_ylabel('Sensitivity'); ax.legend(loc='lower right')
ax.set_title('ROC Curves for GDM Prediction')
plt.tight_layout(); fig.savefig(str(FIG/'fig_roc_enhanced.png'), dpi=300, bbox_inches='tight'); plt.close()
print('Saved: fig_roc_enhanced.png')

# Feature importance
imp = pd.DataFrame({'Feature': all_feats,
    'XGBoost_Gain': xgb_best.feature_importances_,
    'RandomForest': rf_best.feature_importances_}).sort_values('XGBoost_Gain', ascending=False)
imp.to_csv(str(TBL/'feature_importance_enhanced.csv'), index=False)
print(f'\nFeature Importance:\n{imp.to_string(index=False)}')

# SHAP
print('\n=== SHAP Analysis ===')
import shap as sh
exp = sh.TreeExplainer(xgb_best)
sv = exp.shap_values(Xv)

sh.summary_plot(sv, Xv, feature_names=all_feats, plot_type='bar', max_display=12, show=False)
plt.tight_layout(); plt.savefig(str(FIG/'shap_bar_xgboost.png'), dpi=300, bbox_inches='tight'); plt.close()

sh.summary_plot(sv, Xv, feature_names=all_feats, plot_type='dot', max_display=12, show=False)
plt.tight_layout(); plt.savefig(str(FIG/'shap_dot_xgboost.png'), dpi=300, bbox_inches='tight'); plt.close()

fi = {f:i for i,f in enumerate(all_feats)}
for metal in ['lead_log','mercury_log']:
    if metal in fi:
        sh.dependence_plot(metal, sv, Xv, feature_names=all_feats, show=False, alpha=0.6)
        plt.tight_layout()
        plt.savefig(str(FIG/f'shap_dependence_{metal}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f'Saved: shap_dependence_{metal}.png')

sh_imp = pd.DataFrame({'Feature': all_feats, 'Mean_SHAP': np.abs(sv).mean(0)}).sort_values('Mean_SHAP', ascending=False)
sh_imp.to_csv(str(TBL/'shap_importance.csv'), index=False)
print(f'\nSHAP:\n{sh_imp.to_string(index=False)}')
print('\nML Analysis Complete!')
