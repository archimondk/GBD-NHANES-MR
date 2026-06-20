old = "GDM_NHANES_Manuscript_EH.docx"
new = "GDM_NHANES_Manuscript_EH_v2.docx"
content = open("C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py").read()
content = content.replace(old, new)
open("C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py","w").write(content)
print("Fixed")
