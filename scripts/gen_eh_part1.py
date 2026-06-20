import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np; import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

PROJ = Path('C:/Users/008bu/Documents/GBD-NHANES-MR')
TBL = PROJ / 'output' / 'tables'
FIG = PROJ / 'output' / 'figures'
OUT = PROJ / 'manuscript'
doc = Document()

style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(12)
pf = style.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
pf.space_after = Pt(0)

for level in [1, 2, 3]:
    hs = doc.styles[f'Heading {level}']
    hs.font.name = 'Times New Roman'
    hs.font.color.rgb = RGBColor(0, 0, 0)
    hs.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    hs.paragraph_format.space_before = Pt(6)
    hs.paragraph_format.space_after = Pt(6)

section = doc.sections[0]
section._sectPr.append(parse_xml(f'<w:lnNumType {nsdecls("w")} w:countBy="1" w:start="1"/>'))
print('Init done')
