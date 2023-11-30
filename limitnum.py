import pandas as pd
import xml.etree.ElementTree as ET
import os,sys
import json

# 限行政策 调整交通需求
def xianxing(former_csv,later_csv,json_file):
    data = pd.read_csv(former_csv)
    df = pd.DataFrame(data)
    with open(json_file, 'r', encoding="utf-8") as f:
        data1 = json.load(f)
    policy = data1["limitedTailNumber"]
    if policy == 1:
        df["ODcount"] = df["ODcount"].apply(lambda x: round(x / 2))
        df.to_csv(later_csv)

        # 10月12日高峰小时总出行量为 113602 人次/h
        d2 = {"路网指标": {'小汽车出行量(人次/h)': round(113602 * 0.5)}}
        d2 = pd.DataFrame(d2)
        d2.to_csv(r'./output/output_limit_num/路网指标.csv', encoding='gbk')

    if policy == 2:
        df["ODcount"] = df["ODcount"].apply(lambda x: round((x / 5) *4))
        df.to_csv(later_csv)

        # 10月12日高峰小时总出行量为 113602 人次/h
        d2 = {"路网指标": {'小汽车出行量(人次/h)': round((113602 / 5) *4)}}
        d2 = pd.DataFrame(d2)
        d2.to_csv(r'./output/output_limit_num/路网指标.csv', encoding='gbk')

    if policy == 3:
        df["ODcount"] = df["ODcount"].apply(lambda x: round(x))
        df.to_csv(later_csv)

        # 10月12日高峰小时总出行量为 113602 人次/h
        d2 = {"路网指标": {'小汽车出行量(人次/h)': round(113602)}}
        d2 = pd.DataFrame(d2)
        d2.to_csv(r'./output/output_limit_num/路网指标.csv', encoding='gbk')
    
    


# 写入od.xml文件中
def read_xml(in_path):
    tree = ET.parse(in_path)
    return tree



def read_csv_file(in_path,timeslot):
    data = pd.read_csv(in_path ,sep=',',header='infer')  
    df = pd.DataFrame(data)
    df.sort_values(by="timeslot" , inplace=True, ascending=True)
    df1 = df[df["timeslot"] == timeslot]
    df2 = df1.reset_index(drop=True) 
    o_taz = []
    d_taz = []
    od_num = []
    a = timeslot.split("-")
    time_gap = int(a[1]) - int(a[0])
    for i in range(len(df2["o2d_taz"])):
        # print(type(df2['o2d_taz'][i]))
        xxx = df2['o2d_taz'][i].split("-")
        o_taz.append(xxx[0])
        d_taz.append(xxx[1])
        od_num.append(df2['ODcount'][i])
    return o_taz,d_taz,od_num,time_gap

# 美化xml文件
def __indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            __indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def writing_xml(csv_path,json_file,od_path):
    '''
    将df_od写为输入sumo的交通需求文件

    Parameters
    ----------
    xml_path : TYPE:XML
        DESCRIPTION:写入od.xml文件的数据来源文件
    od_path : TYPE：string
        DESCRIPTION：写入od.xml文件的路径

    Returns
    -------
    None.

    '''
    with open(json_file, 'r', encoding="utf-8") as f:
        data = json.load(f)
    if (data["limitedTime"] == 101) or (data["limitedTime"] == 103) or (data["limitedTime"] == 104): #101早高峰，103白天，104全天
        timeslot = "7-9"
    if data["limitedTime"] == 102: #晚高峰
        timeslot = "17-19"

    if os.path.exists(od_path):
        os.remove(od_path)
    o_taz = read_csv_file(csv_path,timeslot)[0]
    d_taz = read_csv_file(csv_path,timeslot)[1]
    od_num = read_csv_file(csv_path,timeslot)[2]
    time_gap = read_csv_file(csv_path,timeslot)[3]
    time_gap_min = time_gap * 3600
    a = ET.Element("demand")
    c = ET.SubElement(a,"timeSlice")
    dura = str(time_gap_min * 1000)
    t = 0
    begin_time = str(t * time_gap * 1000)
    c.attrib = {"duration": dura, "startTime": begin_time}
    for taz in range(len(o_taz)):
        d = ET.SubElement(c,"odPair")
        d.attrib = {"amount":str(od_num[taz]) ,"destination":str(d_taz[taz]) , "origin":str(o_taz[taz])}
    tree = ET.ElementTree(a)
    # print(tree)
    __indent(a, level=0)
    tree.write(od_path)


# json_file = "xianxing.json"
# timeslot = "7-9"
# od_path = 'od.xml'
# former_csv = "odgc_motorized_count.csv"
# later_csv = "./later/later.csv"
# xianxing(former_csv,later_csv,json_file)
# writing_xml(later_csv,timeslot,od_path)    