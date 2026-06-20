content = open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', encoding='utf-8').read()
# Add email line after corresponding author
old = "China', size=11, align=WD_ALIGN_PARAGRAPH.CENTER, sp_after=6)"
new = "China', size=11, align=WD_ALIGN_PARAGRAPH.CENTER, sp_after=6)" + "\nadd_para('E-mail: 496729402@qq.com', size=11, align=WD_ALIGN_PARAGRAPH.CENTER, sp_after=6)"
content = content.replace(old, new)
open('C:/Users/008bu/Documents/GBD-NHANES-MR/scripts/gen_eh_v2.py', 'w', encoding='utf-8').write(content)
for check in ['496729402', 'Zhang Han', 'Zhang Yujing', 'Mo Zhenhan', 'Xiong Mei', 'Chengdu First People']:
    print(f'{check}: {check in content}')
