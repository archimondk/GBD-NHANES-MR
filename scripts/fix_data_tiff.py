content = open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8').read()

new_text = "The NHANES data used in this study are publicly available from the CDC National Center for Health Statistics. Data for the 1999-2000 through 2017-2018 cycles are accessible via XPT file download from the NHANES website (wwwn.cdc.gov/nchs/nhanes/). All analysis scripts and supporting data are available from the corresponding author upon reasonable request."

content = content.replace("The NHANES data used in this study are publicly available from the CDC website. All analytical code and processed data are available from the corresponding author upon reasonable request.", new_text)

# Also export TIFF figures
import numpy as np
from PIL import Image
from pathlib import Path
FIG = Path('C:/Users/008bu/Documents/GBD-NHANES-MR/output/figures')
for fname in ['fig_roc_nature', 'shap_bar_nature', 'shap_dot_nature',
              'shap_dependence_lead_nature', 'shap_dependence_mercury_nature']:
    src = FIG / (fname + '.png')
    dst = FIG / (fname + '.tiff')
    if src.exists():
        img = Image.open(str(src))
        img.save(str(dst), dpi=(600, 600))
        print('TIFF: ' + fname)

open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', 'w', encoding='utf-8').write(content)
print('Data availability updated')
