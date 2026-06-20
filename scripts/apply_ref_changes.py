import re
# Read gen_eh_v2.py
with open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8-sig') as f:
    content = f.read()
# Replace Deputy ref with Gregory ref
content = content.replace(
    '3. Deputy NP, Kim SY, Conrey EJ, Bullard KM. Prevalence and changes in preexisting diabetes and gestational diabetes among women who had a live birth - United States, 2012-2016. MMWR Morb Mortal Wkly Rep. 2018;67(43):1201-1207.',
    '3. Gregory ECW, Ely DM. Trends and characteristics in gestational diabetes: United States, 2016-2020. NCHS Vital Statistics Rapid Release. 2022;11. DOI: 10.15620/cdc:118018.'
)
# Update Background text
content = content.replace(
    'GDM prevalence in the United States has risen from 3.7 percent in 2000 to 7.6 percent in 2019',
    'GDM prevalence in the United States rose from 3.7 percent in 2000 to 7.6 percent in 2020'
)
# Add Bobb 2018 and Gibson 2019 before the closing bracket of refs
bobb = "'41. Bobb JF, Claus Henn B, Valeri L, Coull BA. Statistical software for analyzing the health effects of multiple concurrent exposures via Bayesian kernel machine regression. Environ Health. 2018;17(1):67.',"
gibson = "'42. Gibson EA, Goldsmith J, Kioumourtzoglou MA. Complex mixtures, complex analyses: an emphasis on interpretable results. Curr Environ Health Rep. 2019;6(2):53-61.',"
# Find last ref in list (Hu 2007)
old_last = "'40. Hu H, Shih R, Rothenberg S, Schwartz BS. The epidemiology of lead toxicity in adults: measuring dose and consideration of other methodologic issues. Environ Health Perspect. 2007;115(3):455-462.',"
new_last = "'40. Hu H, Shih R, Rothenberg S, Schwartz BS. The epidemiology of lead toxicity in adults: measuring dose and consideration of other methodologic issues. Environ Health Perspect. 2007;115(3):455-462.',\n    " + bobb + "\n    " + gibson
content = content.replace(old_last, new_last)
# Update BKMR/WQS citation in Discussion
content = content.replace(
    'BKMR) and weighted quantile sum (WQS) regression, may provide additional insights beyond those achievable with single-chemical models [38]. However, tree-based machine learning',
    'BKMR) and weighted quantile sum (WQS) regression, may provide additional insights beyond those achievable with single-chemical models [37, 41, 42]. However, tree-based machine learning'
)
# Write back
with open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
# Verify
c2 = open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8').read()
print('Gregory ref:', 'Gregory ECW' in c2)
print('Bobb ref:', 'Bobb JF' in c2)
print('Gibson ref:', 'Gibson EA' in c2)
print('New BKMR citation:', '[37, 41, 42]' in c2)
print('New BG year:', '2020' in c2[c2.find('GDM prevalence'):c2.find('GDM prevalence')+150])
