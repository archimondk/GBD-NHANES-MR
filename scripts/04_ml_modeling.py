import warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np; import pandas as pd; import seaborn as sns
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
PROJ = Path(__file__).resolve().parent.parent
FIG = PROJ / "output" / "figures"; TBL = PROJ / "output" / "tables"
FIG.mkdir(parents=True, exist_ok=True); TBL.mkdir(parents=True, exist_ok=True)
sns.set_style("whitegrid")

def load():
    df = pd.read_pickle(PROJ / "data" / "processed" / "nhanes_gdm_merged.pkl")
    sub = df[df["pregnant"].notna()].copy()
    sub = sub[(sub["age"]>=15)&(sub["age"]<=49)].copy()
    sub = sub[sub["gdm_self_report"].notna()|sub["gdm_glucose"].notna()].copy()
    sub = sub[sub["lead_ugdl"].notna()|sub["mercury_ugl"].notna()].copy()
    sub["gdm"] = sub["gdm"].astype(int)
    sub["pregnant_now"] = (sub["pregnant"]==1).astype(int)
    sub["education"] = sub["education"].fillna(3)
    rd = pd.get_dummies(sub["race_group"], prefix="race").astype(int)
    for c in rd.columns: sub[c] = rd[c].values
    feats = ["lead_log","mercury_log","age","bmi","education","pregnant_now"]
    feats.extend(sorted([c for c in rd.columns]))
    complete = sub[feats+["gdm","wt_final"]].dropna().copy()
    g = complete['gdm'].sum(); p = complete['gdm'].mean()*100
    print(f"Sample: {len(complete):,}, GDM: {g:,} ({p:.1f}%)")
    return complete, feats

def logit(df, feats):
    import statsmodels.api as sm
    from statsmodels.genmod.families import Binomial
    y = df["gdm"].values; w = df["wt_final"].values
    Xdf = df[feats].copy()
    Xdf["const"] = 1.0
    # Ensure all float64
    for c in Xdf.columns: Xdf[c] = Xdf[c].astype(np.float64)
    X = Xdf.values; y = y.astype(np.float64); w = w.astype(np.float64)
    res = sm.GLM(y, X, family=Binomial(), freq_weights=w).fit()
    print("\n=== Weighted Logistic ==="); print(res.summary())
    cdf = pd.DataFrame({"Feature":feats+["const"],"Coef":res.params,"SE":res.bse,"P":res.pvalues,"OR":np.exp(res.params),"CI_lo":np.exp(res.params-1.96*res.bse),"CI_hi":np.exp(res.params+1.96*res.bse)})
    cdf.to_csv(TBL/"logistic_results.csv",index=False); print("Saved: logistic_results.csv"); return res

def prep_ml(df, feats):
    X = df[feats].values.astype(np.float64); y = df["gdm"].values
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    s = StandardScaler(); Xt = s.fit_transform(Xt); Xv = s.transform(Xv)
    print(f"Train: {len(Xt):,} ({yt.sum():,} GDM), Test: {len(Xv):,} ({yv.sum():,} GDM)"); return Xt, Xv, yt, yv, s

def run_xgb(Xt, yt, Xv, yv):
    print("\n-- XGBoost --"); best_a=0; best=None
    for p in [{"n":200,"d":4,"lr":0.05},{"n":300,"d":6,"lr":0.05},{"n":500,"d":4,"lr":0.03}]:
        m = xgb.XGBClassifier(n_estimators=p["n"],max_depth=p["d"],learning_rate=p["lr"],subsample=0.8,colsample_bytree=0.8,random_state=42,eval_metric="auc",verbosity=0)
        m.fit(Xt, yt); pr = m.predict_proba(Xv)[:,1]; a = roc_auc_score(yv, pr)
        if a>best_a: best_a=a; best=(m,pr)
    yp = (best[1]>=0.5).astype(int); print(f"Best AUC: {best_a:.4f}"); return best[0], yp, best[1]

def run_rf(Xt, yt, Xv, yv):
    print("\n-- Random Forest --")
    m = RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20, random_state=42, n_jobs=-1)
    m.fit(Xt, yt); pr = m.predict_proba(Xv)[:,1]; yp = (pr>=0.5).astype(int); return m, yp, pr

def eval_m(name, yt, yp, pr):
    tn,fp,fn,tp = confusion_matrix(yt,yp).ravel()
    sens=tp/(tp+fn); spec=tn/(tn+fp); f1=2*tp/(2*tp+fp+fn); a=roc_auc_score(yt,pr)
    print(f"  {name}: AUC={a:.4f}, Sens={sens:.3f}, Spec={spec:.3f}, F1={f1:.3f}")
    return {"Model":name,"AUC":a,"Sens":sens,"Spec":spec,"F1":f1}

def plot_roc(entries, path):
    fig,ax = plt.subplots(figsize=(8,7)); colors = ["#2C3E50","#E74C3C","#3498DB"]
    for (name, m, yt, yp), c in zip(entries, colors):
        fpr,tpr,_ = roc_curve(yt,yp)
        ax.plot(fpr,tpr,lw=2.5,color=c,label=f"{name} (AUC={m['AUC']:.3f})")
    ax.plot([0,1],[0,1],"k--",lw=1,alpha=0.5)
    ax.set_xlabel("1 - Specificity"); ax.set_ylabel("Sensitivity"); ax.set_title("ROC Curves"); ax.legend(loc="lower right")
    plt.tight_layout(); fig.savefig(path,dpi=300,bbox_inches="tight"); plt.close(); print(f"Saved: {path}")

def shap_analysis(model, Xv, features, name):
    print(f"\n-- SHAP: {name} --"); import shap as sh
    e = sh.TreeExplainer(model); sv = e.shap_values(Xv)
    sh.summary_plot(sv, Xv, feature_names=features, plot_type="bar", max_display=10, show=False)
    plt.tight_layout(); plt.savefig(FIG/f"shap_bar_{name.lower()}.png",dpi=300,bbox_inches="tight"); plt.close()
    sh.summary_plot(sv, Xv, feature_names=features, plot_type="dot", max_display=10, show=False)
    plt.tight_layout(); plt.savefig(FIG/f"shap_dot_{name.lower()}.png",dpi=300,bbox_inches="tight"); plt.close(); print("  SHAP saved")

def main():
    print("="*60); print("NHANES GDM - ML"); print("="*60)
    df, feats = load()
    print("\n1. WEIGHTED LOGISTIC"); logit(df, feats)
    print("\n2. ML MODELS"); Xt, Xv, yt, yv, s = prep_ml(df, feats)
    xgb_m, xgb_p, xgb_pr = run_xgb(Xt, yt, Xv, yv)
    rf_m, rf_p, rf_pr = run_rf(Xt, yt, Xv, yv)
    res = [("XGBoost", eval_m("XGBoost", yv, xgb_p, xgb_pr), yv, xgb_pr),("RF", eval_m("RF", yv, rf_p, rf_pr), yv, rf_pr)]
    plot_roc(res, FIG/"fig_roc_curves.png")
    pd.DataFrame([r[1] for r in res]).to_csv(TBL/"model_performance.csv",index=False)
    print("\n3. SHAP"); shap_analysis(xgb_m, Xv, feats, "XGBoost")
    imp = pd.DataFrame({"Feature":feats,"XGBoost":xgb_m.feature_importances_,"RandomForest":rf_m.feature_importances_}).sort_values("XGBoost",ascending=False)
    print(imp.to_string(index=False)); imp.to_csv(TBL/"feature_importance.csv",index=False)
    print("\nComplete!")
if __name__=="__main__": main()
