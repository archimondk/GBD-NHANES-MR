import warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np; import pandas as pd; import seaborn as sns
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from itertools import combinations

PROJ = Path(__file__).resolve().parent.parent
FIG = PROJ / "output" / "figures"
TBL = PROJ / "output" / "tables"
FIG.mkdir(parents=True, exist_ok=True); TBL.mkdir(parents=True, exist_ok=True)
sns.set_style("whitegrid")
plt.rcParams.update({"figure.max_open_warning": 0, "font.size": 11})

def load_and_filter():
    df = pd.read_pickle(str(PROJ / "data" / "processed" / "nhanes_gdm_merged.pkl"))
    sub = df[df["pregnant"].notna()].copy()
    sub = sub[(sub["age"] >= 15) & (sub["age"] <= 49)].copy()
    sub = sub[sub["gdm_self_report"].notna() | sub["gdm_glucose"].notna()].copy()
    sub = sub[sub["lead_ugdl"].notna() | sub["mercury_ugl"].notna()].copy()
    sub["gdm"] = sub["gdm"].astype(int)
    sub["pregnant_now"] = (sub["pregnant"] == 1).astype(int)
    sub["education"] = sub["education"].fillna(3)
    rd = pd.get_dummies(sub["race_group"], prefix="race").astype(int)
    for c in rd.columns:
        sub[c] = rd[c].values
    for m in ["lead", "mercury", "cadmium"]:
        sub[f"{m}_log"] = np.log(sub[f"{m}_ugdl" if m=="lead" else f"{m}_ugl"].values + 1e-6)
    return sub

def weighted_logit(df, feats, name="Model"):
    print(f"\n=== {name} ===")
    y = df["gdm"].values.astype(np.float64)
    w = df["wt_final"].values.astype(np.float64)
    Xdf = df[feats].copy().astype(np.float64)
    Xdf.insert(0, "const", 1.0)
    w_norm = w / w.sum() * len(w)
    try:
        res = sm.GLM(y, Xdf.values, family=Binomial(), freq_weights=w_norm).fit(cov_type="HC0")
        cdf = pd.DataFrame({"Feature": Xdf.columns, "OR": np.exp(res.params),
            "CI_lo": np.exp(res.params - 1.96 * res.bse),
            "CI_hi": np.exp(res.params + 1.96 * res.bse),
            "P": res.pvalues})
        cdf["Sig"] = cdf["P"].apply(lambda p: "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "ns")
        print(cdf.to_string(index=False))
        return cdf
    except Exception as e:
        print(f"  Failed: {e}"); return None

def main():
    print("="*60)
    print("ENHANCED ANALYSIS")
    print("="*60)
    df = load_and_filter()
    print(f"Sample: {len(df):,}, GDM: {df['gdm'].sum():,} ({df['gdm'].mean()*100:.1f}%)")
    
    core = ["lead_log", "mercury_log", "cadmium_log", "age", "bmi", "education", "pregnant_now"]
    race_cols = sorted([c for c in df.columns if c.startswith("race_")])
    all_feats = core + race_cols
    
    # 1. Main logistic regression (FIXED)
    r = weighted_logit(df, all_feats, "Full Model (Weighted, Robust SE)")
    if r is not None:
        r.to_csv(str(TBL / "logistic_results_fixed.csv"), index=False)
        print(f"  Saved: logistic_results_fixed.csv")
    
    # 2. Subgroup by race
    print("\n=== Subgroup: Race ===")
    for race in df["race_group"].dropna().unique():
        sub = df[df["race_group"] == race]
        if len(sub) >= 100 and sub["gdm"].sum() >= 10:
            r2 = weighted_logit(sub, core, f"Race: {race} (n={len(sub)})")
            if r2 is not None:
                r2.to_csv(str(TBL / f"subgroup_{race.replace(' ','_')}.csv"), index=False)
    
    # 3. Metal mixture (joint model)
    print("\n=== Metal Mixture ===")
    complete = df[core + ["gdm", "wt_final"]].dropna()
    base = ["age", "bmi", "pregnant_now", "education"]
    print(f"Complete cases: {len(complete):,}")
    for m in ["lead_log", "mercury_log", "cadmium_log"]:
        weighted_logit(complete, base + [m], f"Single metal: {m}")
    weighted_logit(complete, base + ["lead_log", "mercury_log", "cadmium_log"], "All metals joint")
    
    # 4. ML with grid search
    print("\n=== ML Models ===")
    ml_df = df[all_feats + ["gdm"]].dropna()
    X = ml_df[all_feats].values.astype(np.float64)
    y = ml_df["gdm"].values
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    Xt = scaler.fit_transform(Xt); Xv = scaler.transform(Xv)
    print(f"Train: {len(Xt):,}, Test: {len(Xv):,}")
    
    xgb_grid = GridSearchCV(
        xgb.XGBClassifier(random_state=42, eval_metric="auc", verbosity=0),
        {"n_estimators":[200,300], "max_depth":[4,6], "learning_rate":[0.03,0.05],
         "subsample":[0.8], "colsample_bytree":[0.8]},
        cv=3, scoring="roc_auc", n_jobs=-1, verbose=0)
    xgb_grid.fit(Xt, yt)
    xgb_best = xgb_grid.best_estimator_
    xgb_pr = xgb_best.predict_proba(Xv)[:, 1]
    
    rf_grid = GridSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1),
        {"n_estimators":[200,300,500], "max_depth":[4,6,8], "min_samples_leaf":[10,20,50]},
        cv=3, scoring="roc_auc", n_jobs=-1, verbose=0)
    rf_grid.fit(Xt, yt)
    rf_best = rf_grid.best_estimator_
    rf_pr = rf_best.predict_proba(Xv)[:, 1]
    
    perf = []
    for name, pr in [("XGBoost", xgb_pr), ("Random Forest", rf_pr)]:
        auc = roc_auc_score(yv, pr)
        yp = (pr >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(yv, yp).ravel()
        sens = tp/(tp+fn) if (tp+fn)>0 else 0
        spec = tn/(tn+fp) if (tn+fp)>0 else 0
        f1 = 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn)>0 else 0
        print(f"  {name}: AUC={auc:.4f}, Sens={sens:.3f}, Spec={spec:.3f}, F1={f1:.3f}")
        perf.append({"Model":name,"AUC":round(auc,4),"Sensitivity":round(sens,3),
                     "Specificity":round(spec,3),"F1":round(f1,3)})
    pd.DataFrame(perf).to_csv(str(TBL / "model_performance_enhanced.csv"), index=False)
    
    # ROC plot
    fig, ax = plt.subplots(figsize=(8,7))
    for name, pr, c, ls in [("XGBoost", xgb_pr, "#2C3E50", "-"),
                             ("Random Forest", rf_pr, "#E74C3C", "--")]:
        fpr, tpr, _ = roc_curve(yv, pr)
        ax.plot(fpr, tpr, ls, lw=2.5, color=c,
                label=f"{name} (AUC={roc_auc_score(yv, pr):.3f})")
    ax.plot([0,1],[0,1],"k--",lw=1,alpha=0.5)
    ax.set_xlabel("1 - Specificity"); ax.set_ylabel("Sensitivity"); ax.legend(loc="lower right")
    plt.tight_layout(); fig.savefig(str(FIG/"fig_roc_enhanced.png"), dpi=300, bbox_inches="tight"); plt.close()
    
    # Feature importance
    imp = pd.DataFrame({"Feature": all_feats,
        "XGBoost": xgb_best.feature_importances_,
        "RandomForest": rf_best.feature_importances_}).sort_values("XGBoost", ascending=False)
    imp.to_csv(str(TBL/"feature_importance_enhanced.csv"), index=False)
    print(f"\nFeature Importance:\n{imp.to_string(index=False)}")
    
    # 5. SHAP
    print("\n=== SHAP ===")
    import shap as sh
    exp = sh.TreeExplainer(xgb_best)
    sv = exp.shap_values(Xv)
    
    sh.summary_plot(sv, Xv, feature_names=all_feats, plot_type="bar", max_display=12, show=False)
    plt.tight_layout(); plt.savefig(str(FIG/"shap_bar_xgboost.png"), dpi=300, bbox_inches="tight"); plt.close()
    
    sh.summary_plot(sv, Xv, feature_names=all_feats, plot_type="dot", max_display=12, show=False)
    plt.tight_layout(); plt.savefig(str(FIG/"shap_dot_xgboost.png"), dpi=300, bbox_inches="tight"); plt.close()
    
    # SHAP dependence plots
    fi = {f:i for i,f in enumerate(all_feats)}
    for metal in ["lead_log", "mercury_log"]:
        if metal in fi:
            sh.dependence_plot(metal, sv, Xv, feature_names=all_feats, show=False, alpha=0.6)
            plt.tight_layout()
            plt.savefig(str(FIG/f"shap_dependence_{metal}.png"), dpi=300, bbox_inches="tight")
            plt.close()
            print(f"  Saved: shap_dependence_{metal}.png")
    
    sh_imp = pd.DataFrame({"Feature": all_feats, "Mean_SHAP": np.abs(sv).mean(0)}).sort_values("Mean_SHAP", ascending=False)
    sh_imp.to_csv(str(TBL/"shap_importance.csv"), index=False)
    print(f"\nSHAP:\n{sh_imp.to_string(index=False)}")
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
