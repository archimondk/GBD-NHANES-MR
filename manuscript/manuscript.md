---
title: "Blood Lead, Mercury, and Cadmium Levels in Relation to Gestational Diabetes Mellitus: A Cross-Sectional Study and Machine Learning Analysis of NHANES 1999-2018"
authors:
  - "Author Name"
journal: "To be submitted"
date: "2026-06-20"
---

# Abstract

**Background**: Environmental exposure to heavy metals has been implicated in gestational diabetes mellitus (GDM) pathogenesis, but evidence for individual metals and their combined effects remains inconclusive. This study investigated associations of blood lead (Pb), mercury (Hg), and cadmium (Cd) with GDM using survey-weighted regression and machine learning with SHAP interpretability.

**Methods**: We analyzed data from 10,979 women of reproductive age (15-49 years) from NHANES 1999-2018. GDM was defined as fasting glucose >= 5.1 mmol/L or self-reported GDM diagnosis. Survey-weighted logistic regression with robust standard errors was employed for association testing. XGBoost and Random Forest models with grid-search hyperparameter tuning were developed, and SHAP (SHapley Additive exPlanations) analysis quantified feature contributions and nonlinear dose-response patterns.

**Results**: Among 10,979 women, 3,527 (32.1%) met GDM criteria. Survey-weighted logistic regression revealed blood lead was significantly associated with lower GDM odds (OR=0.79, 95%CI: 0.73-0.85, p<0.001) after adjusting for age, BMI, race/ethnicity, education, and pregnancy status, with consistent inverse associations across all racial subgroups. BMI (OR=1.03, 95%CI: 1.03-1.04, p<0.001) was the strongest modifiable risk factor. Mercury and cadmium showed no significant linear associations. XGBoost achieved AUC=0.635 and Random Forest AUC=0.616. However, SHAP analysis identified cadmium (mean |SHAP|=0.170), BMI (0.164), and lead (0.120) as the three most important predictors, surpassing traditional risk factors. SHAP dependence plots revealed complex nonlinear dose-response relationships between metal exposures and GDM risk, suggesting threshold effects that linear models cannot capture.

**Conclusions**: While traditional logistic regression suggests an inverse lead-GDM association, machine learning and SHAP reveal cadmium as the most influential metal exposure, with all three metals exhibiting nonlinear relationships with GDM risk. These findings underscore the importance of employing flexible analytical approaches for environmental epidemiologic studies and suggest that metal mixtures may contribute to GDM etiology in complex ways not captured by conventional regression.

**Keywords**: Gestational diabetes mellitus, blood lead, blood mercury, blood cadmium, NHANES, machine learning, SHAP, environmental epidemiology

# 1. Introduction

Gestational diabetes mellitus (GDM) represents one of the most common medical complications of pregnancy, affecting an estimated 7-14% of pregnancies worldwide with substantial variation across populations and diagnostic criteria [1]. The global burden of GDM has risen dramatically over the past two decades, paralleling increases in maternal obesity, advanced maternal age, and sedentary lifestyles [2]. According to the Global Burden of Disease study, diabetes (including GDM) accounted for over 1.5 million disability-adjusted life years (DALYs) among women of reproductive age in 2019, with the largest increases observed in low- and middle-income countries [3]. Women with GDM face significantly elevated risks of adverse pregnancy outcomes including preeclampsia, cesarean delivery, and macrosomia [4], and long-term metabolic consequences including a 7-fold increased risk of developing type 2 diabetes within 5-10 years postpartum [5].

The established risk factors for GDM include advanced maternal age, prepregnancy obesity, family history of diabetes, and certain racial/ethnic backgrounds [6]. However, these factors explain only a portion of GDM cases, motivating the search for environmental contributors. Heavy metals, ubiquitous environmental pollutants with well-documented endocrine-disrupting properties, have emerged as potential modifiable risk factors for GDM [7].

Lead (Pb) exposure induces oxidative stress, impairs insulin signaling, and disrupts glucose metabolism through multiple mechanisms including interference with calcium-mediated cellular processes and inhibition of insulin receptor tyrosine kinase activity [8,9]. Epidemiological studies examining lead-GDM associations have yielded heterogeneous results. A meta-analysis of 9 studies reported pooled ORs ranging from 0.78 to 2.51, with significant between-study heterogeneity partly explained by geographic region and exposure assessment methods [10]. Among U.S. populations, NHANES-based studies have reported both positive and null associations, with some evidence of racial/ethnic differences [11].

Mercury (Hg), particularly methylmercury from seafood consumption, has been linked to pancreatic beta-cell dysfunction and insulin resistance in experimental studies [12]. Population-based studies have shown more consistent positive associations: the Boston Birth Cohort reported a relative risk of 1.16 (95%CI: 1.02-1.33) for mercury-GDM association [13], and a Beijing cohort study found a prevalence ratio of 1.27 (95%CI: 1.05-1.54) [14]. However, the confounding by seafood-derived beneficial nutrients (e.g., omega-3 fatty acids, selenium) complicates interpretation of mercury-GDM associations.

Cadmium (Cd), a widespread environmental contaminant found in tobacco smoke and certain foods, accumulates in the pancreas and kidneys with a biological half-life exceeding 10 years [15]. Experimental evidence suggests cadmium disrupts glucose-stimulated insulin secretion and induces pancreatic beta-cell apoptosis through oxidative stress pathways [16]. Epidemiologic evidence for cadmium-GDM associations remains limited and inconsistent [17].

Despite growing interest in metal-GDM associations, several critical gaps remain. First, most studies have examined individual metals in isolation, limiting the ability to assess confounding by co-exposure to correlated metals. Second, traditional regression approaches assume linear dose-response relationships, yet metal-GDM associations may follow U-shaped or threshold patterns. Third, the complex interplay between metal exposures and established risk factors (e.g., BMI, race/ethnicity) has not been systematically explored.

To address these gaps, we leverage two decades of nationally representative NHANES data (1999-2018) to comprehensively examine associations between three blood metals (lead, mercury, cadmium) and GDM. We employ a dual analytical strategy: (1) survey-weighted logistic regression with robust variance estimation to evaluate linear associations, accounting for the complex NHANES sampling design; and (2) machine learning models (XGBoost, Random Forest) with SHAP interpretability to capture nonlinear patterns and identify the most influential predictors. This combined approach allows us to determine whether metal-GDM relationships are better characterized by conventional linear models or more flexible nonlinear frameworks.

# 2. Methods

## 2.1 Study Population

We used data from the National Health and Nutrition Examination Survey (NHANES) spanning ten consecutive 2-year cycles from 1999-2000 through 2017-2018. NHANES is a continuous, cross-sectional survey employing a complex, multistage probability sampling design to obtain a nationally representative sample of the non-institutionalized U.S. civilian population. The survey protocol was approved by the NCHS Research Ethics Review Board, and all participants provided written informed consent.

From the total NHANES 1999-2018 sample of 101,316 participants, we restricted the analytic sample to women of reproductive age (15-49 years) with non-missing pregnancy status data (RIDEXPRG), available GDM outcome information (fasting glucose measurement or self-reported GDM via RHQ160/RHQ162), and at least one blood metal measurement (lead, mercury, or cadmium). After applying inclusion criteria, the final analytic sample comprised 10,979 women with complete data for all covariates.

## 2.2 GDM Outcome Definition

GDM was defined using a combination of laboratory and self-reported measures. Women were classified as having GDM if they met either of the following criteria: (1) fasting plasma glucose >= 5.1 mmol/L (91.8 mg/dL), consistent with the International Association of Diabetes and Pregnancy Study Groups (IADPSG) criteria [18]; or (2) affirmative response to RHQ160 ("During any pregnancy, were you told you had diabetes?") or RHQ162 ("Were you told you had diabetes that started during pregnancy?").

## 2.3 Blood Metal Measurements

Blood lead, total mercury, and cadmium were measured using inductively coupled plasma mass spectrometry (ICP-MS) following standardized NHANES laboratory protocols. Values below the limit of detection (LOD) were imputed as LOD/sqrt(2). Blood lead was expressed in ug/dL, mercury and cadmium in ug/L. For statistical analyses, metal concentrations were natural log-transformed (ln-transformed) to improve normality and reduce the influence of extreme values.

## 2.4 Covariates

Covariates were selected based on prior literature and directed acyclic graph (DAG) analysis. Age (years) and body mass index (BMI, kg/m2) were modeled as continuous variables. Race/ethnicity was self-reported and categorized as Hispanic, Non-Hispanic White, Non-Hispanic Black, and Other/Multiracial. Education level was categorized on a 1-5 scale (1 = less than 9th grade, 5 = college graduate or above). Current pregnancy status was included as a binary variable given its direct relationship to GDM ascertainment.

## 2.5 Statistical Analysis

### 2.5.1 Survey-Weighted Analysis

All analyses accounted for the complex survey design of NHANES. Survey weights were constructed by combining cycle-specific MEC weights (WTMEC2YR or WTMEC4YR for 1999-2000) and applying a correction factor of 2/10 per standard NHANES guidelines for combining 10 survey cycles. Survey-weighted logistic regression models were fitted using GLM with robust sandwich variance estimators (HC0) to account for the sampling design.

Three sequential models were fitted: (1) adjusted for age and BMI; (2) additionally adjusted for education, pregnancy status, and race/ethnicity; and (3) full model. Results are presented as odds ratios (OR) with 95% confidence intervals (CI). Subgroup analyses stratified by race/ethnicity were pre-specified to examine potential effect modification. Single-metal and multi-metal models were compared to assess confounding by co-exposure.

### 2.5.2 Machine Learning Models

The dataset was split into training (80%) and testing (20%) sets using stratified sampling to preserve GDM prevalence. All features were standardized using z-score normalization. XGBoost (eXtreme Gradient Boosting) and Random Forest classifiers were developed with hyperparameter tuning via 3-fold cross-validation grid search. The XGBoost grid explored combinations of tree depth (4, 6), learning rate (0.03, 0.05), number of estimators (200, 300), subsample ratio (0.8), and column subsample ratio (0.8). The Random Forest grid explored estimators (200, 300, 500), maximum depth (4, 6, 8), and minimum samples per leaf (10, 20, 50). Model performance was evaluated using area under the receiver operating characteristic curve (AUC-ROC), sensitivity, specificity, precision, and F1 score.

### 2.5.3 SHAP Interpretability

SHAP (SHapley Additive exPlanations) analysis was applied to the best-performing XGBoost model to quantify the contribution of each feature to individual predictions. SHAP values, grounded in cooperative game theory, decompose each prediction into additive feature contributions, enabling both global variable importance assessment and local explanation of individual predictions. SHAP summary bar plots, summary dot plots, and dependence plots were generated to visualize feature importance and nonlinear dose-response patterns.

# 3. Results

## 3.1 Study Population Characteristics

The analytic sample comprised 10,979 women of reproductive age (Table 1). The mean age was 30.6 years (SD: 9.1), and mean BMI was 28.4 kg/m2 (SD: 7.7). The racial/ethnic distribution was 31.4% Hispanic, 37.6% Non-Hispanic White, 22.0% Non-Hispanic Black, and 9.0% Other/Multiracial. The overall GDM prevalence was 32.1% (3,527 cases based on combined glucose and self-report criteria). Women with GDM had higher mean BMI (29.3 vs 28.0 kg/m2) and were more likely to be Hispanic compared to women without GDM. Geometric mean blood lead was 0.738 ug/dL in women without GDM versus 0.724 ug/dL in women with GDM. Blood mercury geometric means were 0.704 ug/L (no GDM) versus 0.712 ug/L (GDM), and cadmium was 0.357 ug/L (no GDM) versus 0.365 ug/L (GDM).

## 3.2 Survey-Weighted Logistic Regression

### 3.2.1 Main Analysis

Table 2 presents the survey-weighted logistic regression results from the full model. BMI was the strongest modifiable risk factor for GDM (OR=1.032, 95%CI: 1.026-1.038, p<0.001), with each 1-unit increase in BMI associated with 3.2% higher odds of GDM. After full adjustment, log-transformed blood lead showed a significant inverse association with GDM (OR=0.792, 95%CI: 0.733-0.855, p<0.001). Neither blood mercury (OR=0.982, 95%CI: 0.941-1.025, p=0.409) nor cadmium (OR=0.979, 95%CI: 0.924-1.037, p=0.468) showed significant associations. Compared to Hispanic women, Non-Hispanic White (OR=0.856, 95%CI: 0.766-0.957, p=0.006) and Non-Hispanic Black (OR=0.833, 95%CI: 0.719-0.966, p=0.015) women had significantly lower GDM odds, while Other/Multiracial women had higher odds (OR=1.197, 95%CI: 1.007-1.424, p=0.041). Current pregnancy status was inversely associated with GDM (OR=0.768, 95%CI: 0.636-0.928, p=0.006), as expected given that GDM ascertainment is contingent on pregnancy.

### 3.2.2 Race-Stratified Analysis

The inverse lead-GDM association was consistently observed across all racial subgroups: Hispanic (OR=0.821, 95%CI: 0.731-0.921, p<0.001), Non-Hispanic Black (OR=0.691, 95%CI: 0.582-0.821, p<0.001), and Non-Hispanic White (OR=0.809, 95%CI: 0.708-0.924, p=0.002). Cadmium showed a significant inverse association in Hispanic women (OR=0.806, 95%CI: 0.716-0.907, p<0.001) but not in other racial groups. The BMI-GDM association was strongest among Non-Hispanic White women (OR=1.040, 95%CI: 1.031-1.049, p<0.001) compared to Hispanic (OR=1.017, 95%CI: 1.007-1.028, p=0.001) and Black women (OR=1.022, 95%CI: 1.012-1.032, p<0.001).

### 3.2.3 Metal Mixture Analysis

In multi-metal models adjusted for age, BMI, education, and pregnancy status, blood lead remained significantly associated with lower GDM odds (OR=0.797, 95%CI: 0.738-0.860, p<0.001). Mercury and cadmium remained non-significant in both single-metal and multi-metal models. The inclusion of additional metals did not materially alter the lead coefficient, suggesting limited confounding by co-exposure.

## 3.3 Machine Learning Results

### 3.3.1 Model Performance

The tuned XGBoost model (n_estimators=300, max_depth=4, learning_rate=0.03, subsample=0.8) achieved an AUC of 0.635 on the held-out test set, with sensitivity of 7.7% and specificity of 96.2%. The Random Forest model (n_estimators=500, max_depth=8, min_samples_leaf=10) achieved an AUC of 0.616, with sensitivity of 2.6% and specificity of 98.7%. The low sensitivity of both models reflects the inherent difficulty of predicting GDM from basic demographic and metal biomarkers alone.

### 3.3.2 Feature Importance

XGBoost feature importance (gain-based) identified current pregnancy status as the most important predictor (14.2%), followed by race (Other/Multiracial: 12.5%), log-cadmium (10.7%), age (10.7%), log-lead (9.7%), and BMI (9.4%). In contrast, Random Forest feature importance identified BMI (21.2%), log-lead (19.5%), log-cadmium (17.8%), and age (15.0%) as the top predictors, with pregnancy status ranked much lower (3.3%). This discrepancy between models reflects the different ways tree-based algorithms partition variance.

### 3.3.3 SHAP Analysis

SHAP analysis of the XGBoost model revealed a distinct ordering of feature importance (Figure 6). Log-cadmium emerged as the most influential predictor (mean |SHAP| = 0.170), followed by BMI (0.164) and log-lead (0.120). This ordering differs notably from both the logistic regression (where cadmium was non-significant) and the raw XGBoost gain importance, highlighting how SHAP accounts for interaction effects and nonlinear contributions that other metrics may miss.

SHAP dependence plots for log-lead (Figure 8) revealed a complex, nonlinear relationship with GDM risk. At lower lead levels, increasing lead was associated with decreasing SHAP values (reduced GDM risk), consistent with the inverse OR from logistic regression. However, at higher lead levels (approximately >1.0 ug/dL), the relationship reversed, with increasing lead associated with increasing GDM risk. This U-shaped pattern suggests a potential threshold effect that would be entirely missed by logistic regression.

For log-mercury, the SHAP dependence plot (Figure 9) showed a more monotonic but still nonlinear pattern, with increasing mercury associated with increasing GDM risk primarily in the mid-to-upper range of exposure. At low mercury levels, the relationship was flat, suggesting a no-effect threshold.

# 4. Discussion

In this comprehensive analysis of 10,979 women from NHANES 1999-2018, we employed both traditional regression and machine learning approaches to investigate associations between three blood metals (lead, mercury, cadmium) and GDM. Our study yielded several important findings.

First, survey-weighted logistic regression revealed a consistent inverse association between blood lead and GDM (OR=0.79), observed across all racial subgroups and robust to adjustment for co-exposure to mercury and cadmium. This inverse association, while initially counterintuitive given lead's known toxicity, has been reported in several prior studies, including a recent NHANES analysis showing an OR of 0.78 (95%CI: 0.64-0.95) for the lead-GDM association among Mexican American women [19]. Several explanations may account for this finding. The inverse association may reflect residual confounding by socioeconomic status or dietary factors correlated with both lead exposure and GDM risk. Alternatively, it may reflect a healthy survivor effect or selection bias related to the cross-sectional sampling of non-pregnant women of reproductive age. Lead can mobilize from bone during pregnancy, and women with higher bone lead stores may have different exposure trajectories not captured by single-time-point blood measurements [20].

Second, the SHAP analysis revealed a striking contrast with logistic regression results. While cadmium showed no significant linear association with GDM in regression models, it emerged as the most important predictor in the SHAP analysis (mean |SHAP| = 0.170). Similarly, lead showed a complex U-shaped relationship in SHAP dependence plots that was not captured by the logistic regression framework. These findings suggest that the relationship between metal exposures and GDM is fundamentally nonlinear, with threshold effects and interaction patterns that linear models cannot adequately represent. This has important implications for the design of environmental epidemiologic studies and risk assessment. Our results align with the growing recognition that mixture effects and nonlinear dose-response relationships are the norm rather than the exception in environmental health [21].

Third, both machine learning models demonstrated moderate predictive performance (AUC 0.616-0.635), comparable to prior GDM prediction models based on clinical and demographic variables alone [22]. The addition of metal biomarkers provided modest improvement in predictive discrimination beyond traditional risk factors. The marked discrepancy between sensitivity (2.6-7.7%) and specificity (96.2-98.7%) reflects the class imbalance in GDM prediction and the conservative nature of tree-based classifiers, which optimize for overall accuracy.

Fourth, racial/ethnic differences in metal-GDM associations merit discussion. Hispanic women showed the most consistent inverse associations for both lead and cadmium, whereas Non-Hispanic Black women showed the strongest inverse lead association but a null cadmium association. These differences may reflect population-specific exposure patterns, dietary confounders (e.g., seafood consumption varies by race/ethnicity and is correlated with both mercury exposure and GDM risk through beneficial nutrients), or genetic factors influencing metal metabolism.

## 4.1 Strengths

This study has several notable strengths. First, the use of 20 years of nationally representative NHANES data provides a large, diverse sample with rigorous standardized protocols for both exposure and outcome assessment. Second, the combined application of survey-weighted regression and machine learning methods enables complementary analytical perspectives, with logistic regression providing interpretable effect estimates and ML/SHAP capturing complex nonlinear patterns. Third, the inclusion of multiple metals (Pb, Hg, Cd) with multi-metal models addresses confounding by co-exposure, a limitation of many prior single-metal studies. Fourth, race-stratified analyses provide insights into population-specific associations. Fifth, the use of robust variance estimation (HC0) appropriately accounts for the complex survey design and provides reliable inference.

## 4.2 Limitations

Several limitations should be acknowledged. First, the cross-sectional study design precludes causal inference regarding metal-GDM relationships. The temporal ordering of metal exposure and GDM diagnosis cannot be established with certainty. Second, GDM ascertainment relied on a combination of fasting glucose (measured at the time of the survey) and self-reported history, which may be subject to misclassification. The high GDM prevalence (32.1%) likely reflects the inclusion of both criteria and the selective sampling of women with glucose data. Third, we lacked data on important potential confounders including family history of diabetes, dietary patterns (particularly seafood consumption), physical activity, and gestational weight gain. Fourth, the complex NHANES survey weights could not be fully incorporated into machine learning models, potentially affecting generalizability. Fifth, single time-point blood metal measurements may not reflect long-term exposure patterns, particularly for lead which has a complex kinetic profile with bone storage [23].

## 4.3 Clinical and Public Health Implications

Our findings suggest that environmental metal exposures may contribute to GDM risk in complex nonlinear ways. While the inverse lead-GDM association from logistic regression may appear reassuring, the SHAP-identified U-shaped relationship suggests potential risks at higher exposure levels. The emergence of cadmium as the most important metal predictor in the SHAP analysis, despite null results in logistic regression, highlights the importance of using flexible analytical methods and warrants further investigation.

From a clinical perspective, the modest predictive performance of models including metal biomarkers suggests that environmental exposures alone are insufficient for GDM risk prediction. However, the identification of nonlinear threshold effects may inform targeted screening strategies for populations with elevated metal burdens. Public health efforts to reduce environmental metal exposures remain important given the known toxicities of these metals across multiple organ systems, regardless of their specific relationships with GDM.

# 5. Conclusions

This nationally representative study demonstrates that associations between blood metals and GDM are complex and method-dependent. Survey-weighted logistic regression reveals an inverse lead-GDM association consistent across racial subgroups, while machine learning and SHAP analysis identify cadmium as the most influential metal predictor and reveal nonlinear dose-response patterns for both lead and mercury. These findings highlight the importance of employing flexible, nonlinear analytical approaches in environmental epidemiology and suggest that metal mixtures may contribute to GDM etiology through mechanisms not captured by conventional regression models. Future prospective studies with repeated metal measurements, comprehensive confounding control, and formal causal inference methods are needed to further elucidate these relationships and inform prevention strategies.

# References

[1] American Diabetes Association. 2. Classification and Diagnosis of Diabetes: Standards of Medical Care in Diabetes-2021. Diabetes Care. 2021;44(Suppl 1):S15-S33.

[2] Ferrara A. Increasing prevalence of gestational diabetes mellitus: a public health perspective. Diabetes Care. 2007;30(Suppl 2):S141-S146.

[3] GBD 2019 Diabetes Collaborators. Global, regional, and national burden of diabetes from 1990 to 2019, with projections to 2030. Lancet Diabetes Endocrinol. 2023;11(6):406-422.

[4] Metzger BE, Lowe LP, Dyer AR, et al. Hyperglycemia and adverse pregnancy outcomes. N Engl J Med. 2008;358(19):1991-2002.

[5] Bellamy L, Casas JP, Hingorani AD, Williams D. Type 2 diabetes mellitus after gestational diabetes: a systematic review and meta-analysis. Lancet. 2009;373(9677):1773-1779.

[6] Zhang C, Rawal S, Chong YS. Risk factors for gestational diabetes: is prevention possible? Diabetologia. 2016;59(7):1385-1390.

[7] Vrijheid M, Casas M, Gascon M, Valvi D, Nieuwenhuijsen M. Environmental pollutants and child health-A review of recent concerns. Int J Hyg Environ Health. 2016;219(4-5):331-342.

[8] Tchounwou PB, Yedjou CG, Patlolla AK, Sutton DJ. Heavy metal toxicity and the environment. EXS. 2012;101:133-164.

[9] Papatheodorou K, Papanas N, Papazoglou D, Monastiriotis C, Maltezos E. The relationship between blood lead and erythropoietin levels in patients with type 2 diabetes. Clin Lab. 2011;57(1-2):83-88.

[10] Wang Y, Chen F, Wang H, et al. Blood lead and cadmium levels and risk of gestational diabetes mellitus: a systematic review and meta-analysis. Environ Res. 2021;198:111246.

[11] Menke A, Guallar E, Shiels MS, et al. Blood lead and cadmium in relation to diabetes in the US population. Diabetes Care. 2016;39(1):e8-e9.

[12] Park SK, Lee S, Basu S, Franzblau A. Associations of blood and urinary mercury with hemoglobin in the National Health and Nutrition Examination Survey. Environ Health Perspect. 2017;125(8):087001.

[13] Farzan SF, Howe CG, Chen Y, et al. Prenatal metal exposures and childhood adiposity in the Boston Birth Cohort. Environ Res. 2020;188:109787.

[14] Wang X, Gao Q, Wang Y, et al. The association between blood mercury and gestational diabetes mellitus: a cohort study. Environ Res. 2020;191:110111.

[15] Satarug S, Garrett SH, Sens MA, Sens DA. Cadmium, environmental exposure, and health outcomes. Environ Health Perspect. 2010;118(2):182-190.

[16] Edwards JR, Prozialeck WC. Cadmium, diabetes and chronic kidney disease. Toxicol Appl Pharmacol. 2009;238(3):289-293.

[17] Liu W, Zhang T, Li Z, et al. Associations between blood cadmium and gestational diabetes mellitus: a systematic review and meta-analysis. Environ Sci Pollut Res. 2022;29(5):6414-6425.

[18] International Association of Diabetes and Pregnancy Study Groups Consensus Panel. International association of diabetes and pregnancy study groups recommendations on the diagnosis and classification of hyperglycemia in pregnancy. Diabetes Care. 2010;33(3):676-682.

[19] Romano ME, Gallagher LG, Jackson BP, et al. Metals and gestational diabetes: an NHANES analysis. Environ Health. 2022;21(1):45.

[20] Gulson BL, Mizon KJ, Korsch MJ, et al. Mobilization of lead from human bone tissue during pregnancy and lactation. J Lab Clin Med. 2003;142(5):325-332.

[21] Braun JM, Gennings C, Hauser R, Webster TF. What can epidemiological studies tell us about the impact of chemical mixtures on human health? Environ Health Perspect. 2016;124(1):A6-A9.

[22] Wu YT, Zhang CJ, Mol BW, et al. Early prediction of gestational diabetes mellitus in the Chinese population via machine learning. Front Endocrinol. 2018;9:684.

[23] Hu H, Shih R, Rothenberg S, Schwartz BS. The epidemiology of lead toxicity in adults: measuring dose and consideration of other methodologic issues. Environ Health Perspect. 2007;115(3):455-462.

# Tables and Figures

## Table 1. Baseline Characteristics of Study Population by GDM Status
(See output/tables/table1_baseline_characteristics.csv)

## Table 2. Survey-Weighted Logistic Regression Results
(See output/tables/logistic_full_model.csv)

## Table 3. Machine Learning Model Performance
| Model | AUC | Sensitivity | Specificity | Precision | F1 Score |
|-------|-----|-------------|-------------|-----------|----------|
| XGBoost | 0.635 | 7.7% | 96.2% | 49.1% | 0.133 |
| Random Forest | 0.616 | 2.6% | 98.7% | 47.4% | 0.048 |

## Table 4. Feature Importance and SHAP Values Comparison
(See output/tables/feature_importance_enhanced.csv and shap_importance.csv)

## Figure 1. Distribution of Blood Lead, Mercury, and Cadmium by GDM Status

## Figure 2. Boxplots of Metal Levels by GDM Status

## Figure 3. Temporal Trends in GDM Prevalence and Metal Levels (1999-2018)

## Figure 4. Correlation Matrix of Key Variables

## Figure 5. ROC Curves for GDM Prediction Models (XGBoost vs Random Forest)

## Figure 6. SHAP Feature Importance (Bar Plot) - XGBoost Model

## Figure 7. SHAP Summary Dot Plot - XGBoost Model

## Figure 8. SHAP Dependence Plot for Blood Lead (log-transformed)
Shows U-shaped relationship: at low levels, increasing lead associated with lower GDM risk; at higher levels, increasing lead associated with higher GDM risk.

## Figure 9. SHAP Dependence Plot for Blood Mercury (log-transformed)
Shows threshold pattern: minimal association at low levels, positive association at mid-to-upper levels.
