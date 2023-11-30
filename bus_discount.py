import pandas as pd
from math import *
import xml.etree.ElementTree as ET
import os,sys
import json


# data = pd.read_csv(r'')
# logit = sm.MNLogit(data_0['P'], data_0[['waiting_time', 'driving_time', 'cost', 'person_1', 'person_2']])
# result = logit.fit()
# x = [0, 0.20, 0.40, 0.50, 0.60, 0.80, 1.00, 1.20, 1.50, 2.00]


# 公交票价优惠政策 调整交通需求
def bus_discount(former_csv,later_csv,json_file):
    data = pd.read_csv(former_csv)
    df = pd.DataFrame(data)
    with open(json_file, 'r', encoding="utf-8") as f:
        data1 = json.load(f)
    into_discount = float(data1["entryExitFare"])
    in_discount = float(data1["internalFare"])

    p_bus_into = 0.0721 + 0.06 * (1 - into_discount)  # 公交
    p_subway_into = 0.0904 + 0.07 * (1 - into_discount)  # 轨道
    p_car_into = 0.2298 + 0.05 * (into_discount - 1)  # 小汽车
    p_other_into = 0.6077 + 0.08 * (into_discount - 1)  # 慢行

    p_bus_in = 0.0721 + 0.06 * (1 - in_discount)  # 公交
    p_subway_in = 0.0904 + 0.07 * (1 - in_discount)  # 轨道
    p_car_in = 0.2298 + 0.05 * (in_discount - 1)  # 小汽车
    p_other_in = 0.6077 + 0.08 * (in_discount - 1)  # 慢行

    p_bus = min(max(p_bus_into * 0.71 + p_bus_in * 0.29, 0), 1)
    p_subway = min(max(p_subway_into * 0.71 + p_subway_in * 0.29, 0), 1)
    p_car = min(max(p_car_into * 0.71 + p_car_in * 0.29, 0), 1)
    p_other = 1 - p_bus - p_subway - p_car


    with open(r'./output/output_bus_discount/方式结构.csv', 'w', encoding = 'utf-8') as fw:
        fw.write('轨道,公交,小汽车,慢行' + '\n')
        fw.write('{},{},{},{}'.format(p_subway, p_bus, p_car, p_other))

    # 10月12日高峰小时总出行量为 113602 人次/h
    d2 = {"路网指标": {'public_trip': 113602 * (p_bus + p_subway), 'car_trip': 113602 * p_car}}
    d2 = pd.DataFrame(d2)
    d2.to_csv(r'./output/output_bus_discount/路网指标.csv')

    df["ODcount"] = df["ODcount"].apply(lambda x: round(x * (1 + p_car - 0.2298)))
    df.to_csv(later_csv)


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

def bus_discount_od(csv_path,timeslot,od_path):
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

