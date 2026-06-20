import re
with open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8') as f:
    content = f.read()

# 1. Background year update
content = content.replace('GDM prevalence has risen from 3.7% in 2000 to 7.6% in 2019, with certain racial/e\nthnic groups ', 'GDM prevalence has risen from 3.7% in 2000 to 7.6% in 2020, with certain racial/ethnic groups ')

# 2. Add new refs after Hu ref [41]
import os
bobb = os.linesep + '    ' + "'42. Bobb JF, Claus Henn B, Valeri L, Coull BA. Statistical software for analyzing the health effects of multiple concurrent exposures via Bayesian kernel machine regression. Environ Health. 2018;17(1):67.',"
gibson = os.linesep + '    ' + "'43. Gibson EA, Goldsmith J, Kioumourtzoglou MA. Complex mixtures, complex analyses: an emphasis on interpretable results. Curr Environ Health Rep. 2019;6(2):53-61.',"
hu_text = "'41. Hu H, Shih R, Rothenberg S, Schwartz BS. The epidemiology of lead toxicity in adults: measuring dose and consideration of other methodologic issues. Environ Health Perspect. 2007;115(3):455-462.',"
content = content.replace(hu_text, hu_text + bobb + gibson)

# 3. BKMR citation update  
content = content.replace('[38]. However, tree-based machine learning', '[37, 42, 43]. However, tree-based machine learning')

with open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
for label, needle in [('Gregory ref', 'Gregory ECW'), ('Bobb ref', 'Bobb JF'), ('Gibson ref', 'Gibson EA'), ('BKMR cite', '[37, 42, 43]'), ('Year 2020', '2020, with certain racial/ethnic')]:
    print(f'{label}: {needle in content}')
