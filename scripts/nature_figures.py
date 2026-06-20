"""
Nature-quality manuscript figures for GDM-NHANES paper
Backend: Python (matplotlib + seaborn + xgboost + shap)
Palette: Nature-style DEFAULT_COLORS from nature-figure API
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np; import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import shap as sh
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix

# ── Nature-style rcParams ──
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'font.size': 7,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.linewidth': 0.8,
    'legend.frameon': False,
})

# ── Nature-style PALETTE ──
PALETTE = {
    'blue_main':      '#0F4D92',
    'blue_secondary': '#3775BA',
    'green_3': '#8BCF8B',
    'red_strong': '#B64342',
    'teal':   '#42949E',
    'violet': '#9A4D8E',
    'neutral_light': '#CFCECE',
    'neutral_mid':   '#767676',
    'neutral_dark':  '#4D4D4D',
    'neutral_black': '#272727',
    'gold':   '#FFD700',
}
DEFAULT_COLORS = [PALETTE['blue_main'], PALETTE['green_3'], PALETTE['red_strong'],
                  PALETTE['teal'], PALETTE['violet'], PALETTE['neutral_light']]

PROJ = Path('C:/Users/008bu/Documents/GBD-NHANES-MR')
FIG = PROJ / 'output' / 'figures'
TBL = PROJ / 'output' / 'tables'
FIG.mkdir(parents=True, exist_ok=True)

# ── Load & prepare data ──
print('Loading data...')
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
print(f'Data ready: {len(sub):,} rows, {len(all_feats)} features')

# ── Train XGBoost ──
ml_df = sub[all_feats + ['gdm']].dropna()
X = ml_df[all_feats].values.astype(np.float64)
y = ml_df['gdm'].values
Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
scaler = StandardScaler()
Xt = scaler.fit_transform(Xt); Xv = scaler.transform(Xv)

model = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.03,
                          subsample=0.8, colsample_bytree=0.8,
                          random_state=42, eval_metric='auc', verbosity=0)
model.fit(Xt, yt)
y_prob = model.predict_proba(Xv)[:, 1]
auc = roc_auc_score(yv, y_prob)
print(f'XGBoost AUC = {auc:.4f}')

# ── SHAP ──
explainer = sh.TreeExplainer(model)
shap_values = explainer.shap_values(Xv)
print(f'SHAP computed: {shap_values.shape}')

# ════════════════════════════════════════
# Figure 1: ROC Curve (Nature-style)
# ════════════════════════════════════════
print('Plotting ROC curve...')
fig, ax = plt.subplots(figsize=(4.5, 4.0))
fpr, tpr, _ = roc_curve(yv, y_prob)
ax.plot(fpr, tpr, color=PALETTE['blue_main'], linewidth=1.5,
        label=f'XGBoost (AUC={auc:.3f})')
ax.fill_between(fpr, tpr, alpha=0.08, color=PALETTE['blue_main'])
ax.plot([0,1],[0,1], color=PALETTE['neutral_light'], linewidth=0.8, linestyle='--')
ax.set_xlabel('1 - Specificity', fontsize=8)
ax.set_ylabel('Sensitivity', fontsize=8)
ax.legend(fontsize=7, loc='lower right')
ax.set_title('ROC Curve - GDM Prediction', fontsize=9, fontweight='bold')
ax.set_xlim(0,1); ax.set_ylim(0,1)
ax.text(0.98, 0.02, f'n = {len(yv):,}', transform=ax.transAxes,
        ha='right', va='bottom', fontsize=7, color=PALETTE['neutral_mid'])
plt.tight_layout()
fig.savefig(str(FIG / 'fig_roc_nature.png'), dpi=600, bbox_inches='tight')
fig.savefig(str(FIG / 'fig_roc_nature.svg'), bbox_inches='tight')
print('  Saved fig_roc_nature.png/svg')
plt.close()

# ════════════════════════════════════════
# Figure 2: SHAP Summary Bar (Nature-style)
# ════════════════════════════════════════
print('Plotting SHAP bar...')
mean_shap = np.abs(shap_values).mean(0)
idx_sort = np.argsort(mean_shap)
feat_labels = [all_feats[i] for i in idx_sort]
bar_colors = [DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i in range(len(feat_labels))]

fig, ax = plt.subplots(figsize=(4.5, 3.5))
ax.barh(range(len(mean_shap)), mean_shap[idx_sort], color=bar_colors, height=0.7)
ax.set_yticks(range(len(mean_shap)))
ax.set_yticklabels(feat_labels, fontsize=7)
ax.set_xlabel('mean |SHAP value|', fontsize=8)
ax.set_title('SHAP Feature Importance', fontsize=9, fontweight='bold')
ax.set_xlim(0, max(mean_shap) * 1.15)
for i, v in enumerate(mean_shap[idx_sort]):
    ax.text(v + max(mean_shap)*0.01, i, f'{v:.3f}', va='center', fontsize=6, color=PALETTE['neutral_mid'])
plt.tight_layout()
fig.savefig(str(FIG / 'shap_bar_nature.png'), dpi=600, bbox_inches='tight')
fig.savefig(str(FIG / 'shap_bar_nature.svg'), bbox_inches='tight')
print('  Saved shap_bar_nature.png/svg')
plt.close()

# ════════════════════════════════════════
# Figure 3: SHAP Summary Dot (Nature-style)
# ════════════════════════════════════════
print('Plotting SHAP dot...')
fig = plt.figure(figsize=(4.5, 3.5))
sh.summary_plot(shap_values, Xv, feature_names=all_feats, plot_type='dot',
                max_display=10, show=False, plot_size=(4.5, 3.5),
                color_bar_label='Feature value')
ax = plt.gca()
ax.set_xlabel('SHAP value (impact on model output)', fontsize=8)
ax.set_title('SHAP Summary', fontsize=9, fontweight='bold')
plt.tight_layout()
fig.savefig(str(FIG / 'shap_dot_nature.png'), dpi=600, bbox_inches='tight')
fig.savefig(str(FIG / 'shap_dot_nature.svg'), bbox_inches='tight')
print('  Saved shap_dot_nature.png/svg')
plt.close()

# ════════════════════════════════════════
# Figure 4: SHAP Dependence - Lead (Nature-style)
# ════════════════════════════════════════
print('Plotting SHAP dependence lead...')
lead_idx = all_feats.index('lead_log')
fig, ax = plt.subplots(figsize=(4.0, 3.0))
x_vals = Xv[:, lead_idx]
shap_lead = shap_values[:, lead_idx]
ax.scatter(x_vals, shap_lead, s=4, alpha=0.5, color=PALETTE['blue_main'], edgecolors='none')
# Add smoothed trend line
from scipy.ndimage import gaussian_filter1d
sort_idx = np.argsort(x_vals)
xs = x_vals[sort_idx]
ys = gaussian_filter1d(shap_lead[sort_idx], sigma=10)
ax.plot(xs, ys, color=PALETTE['red_strong'], linewidth=1.5)
ax.axhline(y=0, color=PALETTE['neutral_light'], linewidth=0.5, linestyle='-')
# Add reference lines for the approximate turning point
ax.axvline(x=0.5, color=PALETTE['neutral_mid'], linewidth=0.5, linestyle=':', alpha=0.6)
ax.set_xlabel('log(Blood lead)', fontsize=8)
ax.set_ylabel('SHAP value', fontsize=8)
ax.set_title('Lead - SHAP Dependence', fontsize=9, fontweight='bold')
x_min, x_max = ax.get_xlim()
ax.text(x_min + (x_max-x_min)*0.02, ax.get_ylim()[1]*0.9,
        'U-shaped pattern', fontsize=6, color=PALETTE['red_strong'], style='italic')
plt.tight_layout()
fig.savefig(str(FIG / 'shap_dependence_lead_nature.png'), dpi=600, bbox_inches='tight')
fig.savefig(str(FIG / 'shap_dependence_lead_nature.svg'), bbox_inches='tight')
print('  Saved shap_dependence_lead_nature.png/svg')
plt.close()

# ════════════════════════════════════════
# Figure 5: SHAP Dependence - Mercury (Nature-style)
# ════════════════════════════════════════
print('Plotting SHAP dependence mercury...')
hg_idx = all_feats.index('mercury_log')
fig, ax = plt.subplots(figsize=(4.0, 3.0))
x_vals = Xv[:, hg_idx]
shap_hg = shap_values[:, hg_idx]
ax.scatter(x_vals, shap_hg, s=4, alpha=0.5, color=PALETTE['teal'], edgecolors='none')
sort_idx = np.argsort(x_vals)
xs = x_vals[sort_idx]
ys = gaussian_filter1d(shap_hg[sort_idx], sigma=10)
ax.plot(xs, ys, color=PALETTE['red_strong'], linewidth=1.5)
ax.axhline(y=0, color=PALETTE['neutral_light'], linewidth=0.5, linestyle='-')
ax.set_xlabel('log(Blood mercury)', fontsize=8)
ax.set_ylabel('SHAP value', fontsize=8)
ax.set_title('Mercury - SHAP Dependence', fontsize=9, fontweight='bold')
ax.text(ax.get_xlim()[0] + 0.02, ax.get_ylim()[1]*0.9,
        'Threshold pattern', fontsize=6, color=PALETTE['red_strong'], style='italic')
plt.tight_layout()
fig.savefig(str(FIG / 'shap_dependence_mercury_nature.png'), dpi=600, bbox_inches='tight')
fig.savefig(str(FIG / 'shap_dependence_mercury_nature.svg'), bbox_inches='tight')
print('  Saved shap_dependence_mercury_nature.png/svg')
plt.close()

# ── Summary ──
print('\n=== Nature-quality figures generated ===')
for f in sorted(FIG.glob('*nature*')):
    print(f'  {f.name} ({f.stat().st_size/1024:.0f} KB)')
print('Done!')
