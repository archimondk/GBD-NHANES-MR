content = open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8-sig').read()

# Fix 1: bg_p7 was defined but bg_p6 was used instead
old = "add_para(bg_p6, sp_after=6)\npb()\n\nbg_p8 = ('To address these gaps"
new = "add_para(bg_p7, sp_after=6)\npb()\n\nbg_p8 = ('To address these gaps"
content = content.replace(old, new)

# Fix 2: Remove duplicate ref 28 (same as ref 13)
content = content.replace(
    "'28. Romano ME, Gallagher LG, Jackson BP, Baker E, Karagas MR. Metals and gestational diabetes: an NHANES analysis. Environ Health. 2022;21(1):45.',\n    ",
    "'28. Rotter I, Kosik-Bogacka DI, Dolegowska B, Skonieczna-Zydecka K, Karasiewicz B, et al. Relationship between blood lead and metabolic syndrome. Biol Trace Elem Res. 2018;186(2):368-378.',\n    "
)

open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', 'w', encoding='utf-8').write(content)
print('Fixed!')
compile(content, 'gen_eh_v2.py', 'exec')
print('Syntax valid!')
