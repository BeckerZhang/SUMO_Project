
import pandas as pd
import re
data = pd.read_csv(r"C:\Users\Yongqi Zhang\Desktop\weight\0720\tw_rdc_case\cache\GC_ODtaz_motorized.csv",encoding="ansi")
df = pd.DataFrame(data)
# timeslot = df["timeslot"]
try:
    df["timeslot"] = df["timeslot"].apply(lambda x: re.sub('[\u4e00-\u9fa5]','-',x))
    df["o2d_taz"] = df["o2d_taz"].apply(lambda x: re.sub('[\u4e00-\u9fa5]','-',x))
    # df["timeslot"] = df["timeslot"].apply(lambda x: x[0:-1])
except:
    pass

timeslot = []
for i in df["timeslot"]:
    if i.count("-") == 2:
        i = i[0:-1]
        timeslot.append(i)
        # print(i)
    else:
        timeslot.append(i)
        
o2d_taz = []
for i in df["o2d_taz"]:
    if i.count("-") == 2:
        i = i[0:-1]
        o2d_taz.append(i)

    else:
        o2d_taz.append(i)
        
df["timeslot"] = timeslot
df["o2d_taz"] = o2d_taz
print(df)
df.to_csv(r"C:\Users\Yongqi Zhang\Desktop\weight\0720\tw_rdc_case\cache\GC_ODtaz_motorized1.csv",encoding="utf-8")