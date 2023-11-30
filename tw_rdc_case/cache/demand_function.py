import xml.etree.ElementTree as ET
import os,sys
import pandas as pd


def read_xml(in_path):
    tree = ET.parse(in_path)
    return tree



def read_csv_file(in_path,timeslot):
    data1 = pd.read_csv(in_path ,sep=',',header='infer',encoding='utf-8')  
    df = pd.DataFrame(data1)
    # print(data1)
    df.sort_values(by="timeslot" , inplace=True, ascending=True)
    df1 = df[df["timeslot"] == timeslot]
    df2 = df1.reset_index(drop=True) 
    # print(df2)
    o_taz = []
    d_taz = []
    od_num = []
    a = timeslot.split("-")
    time_gap = int(a[1]) - int(a[0])
    for i in range(len(df2["o2d_taz"])):
        xxxx = df2['o2d_taz'][i].split("-")
        o_taz.append(xxxx[1])
        d_taz.append(xxxx[0])
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

def writing_xml(csv_path,timeslot,od_path):
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

    # '''
    # time_gap是关键参数，用于控制OD变化的时间间隔，现在设置的是900秒，即15min
    # '''
    time_gap_min = time_gap * 3600
    # 创建根节点
    a = ET.Element("demand")
    c = ET.SubElement(a,"timeSlice")
    dura = str(time_gap_min * 1000)
    t = 0
    begin_time = str(t * time_gap * 1000)
    c.attrib = {"duration": dura, "startTime": begin_time}
    # d = ET.SubElement(c,"odPair")
    for taz in range(len(o_taz)):
        d = ET.SubElement(c,"odPair")
        d.attrib = {"amount":str(od_num[taz]) ,"destination":str(o_taz[taz]) , "origin":str(d_taz[taz])}
    tree = ET.ElementTree(a)
    # print(tree)
    __indent(a, level=0)
    tree.write(od_path)
writing_xml(r'C:\Users\Yongqi Zhang\Desktop\weight\0720\tw_rdc_case\cache\GC_ODtaz_motorized.csv','7-9',r'C:\Users\Yongqi Zhang\Desktop\weight\0720\tw_rdc_case\cache\od.xml')