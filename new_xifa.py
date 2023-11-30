import xml.etree.ElementTree as ET
import pandas as pd
import csv
import time
import pandas as pd
import os,sys
import numpy as np

"""
首先筛选现有flow文件中，从A交通小区出发到其影响区内其他交通小区的odpair_amount以走影响区到交通小区A的odpair_amount；
并可将结果保存至csv文件中；
"""
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


def filtrate(former_taz,new_built_taz,occurance_num,attraction_num,in_path,timeslot,tag):
    od_pair_name_new = []
    od_pair_name_new1 = []
    od_pair_o = []
    od_pair_d = []
    od_pair_o1 = []
    od_pair_d1 = []
    od_pair_freq_new = []
    od_pair_freq_new1 = []
    
    result = read_csv_file(in_path,timeslot)
    # print(result)
    o_taz = result[0]
    d_taz = result[1]
    od_num = result[2]
    time_gap = result[3]
    od_pair_name = []
    for xxx in range(0,len(o_taz)):
        o = o_taz[xxx]
        d = d_taz[xxx]
        od_name = [o,d]
        od_pair_name.append(od_name)
        if o == former_taz:#affected_taz删掉就好
            od_pair_o.append(o)
            od_pair_d.append(d)
            od_pair_freq_new.append(od_num[xxx])
            od_pair_name_new.append(od_pair_name[xxx])
        elif d == former_taz:
            od_pair_o1.append(o)
            od_pair_d1.append(d)
            od_pair_freq_new1.append(od_num[xxx])
            od_pair_name_new1.append(od_pair_name[xxx])
        else:
            pass
    """
    将计算得到的新建项目区域与其影响区之间的交通量分配比例按新建项目吸发量完成分配;
    """
    # occurance_num = 400
    # attraction_num = 500
    sum_occur = 0
    sum_occur1 = 0
    for y in range(0,len(od_pair_d)):
        sum_occur = sum_occur + int(od_pair_freq_new[y])

    for yy in range(len(od_pair_freq_new)):
        yy_new = float(od_pair_freq_new[yy] / sum_occur)
        od_pair_freq_new[yy] = yy_new

    for yyy in range(len(od_pair_freq_new)):
        yyy_new = float(od_pair_freq_new[yyy] * occurance_num)
        od_pair_freq_new[yyy] = yyy_new

    for z in range(0,len(od_pair_d1)):
        sum_occur1 = sum_occur1 + int(od_pair_freq_new1[z])

    for zz in range(len(od_pair_freq_new1)):
        zz_new = float(od_pair_freq_new1[zz] / sum_occur1)
        od_pair_freq_new1[zz] = zz_new

    for zzz in range(len(od_pair_freq_new1)):
        zzz_new = float(od_pair_freq_new1[zzz] * attraction_num)
        od_pair_freq_new1[zzz] = zzz_new

    """
    此处可以将得到的数据存入result.csv文件中,当然也可以不存;
    """
    # dataframe = pd.DataFrame({'od_pair_name':od_pair_name_new,'o':od_pair_o,'d':od_pair_d,'od_pair_freq':od_pair_freq_new})
    # dataframe.to_csv("G:\\projects\\xifaliang_test\\result.csv",sep=',')

    """
    将计算出来的各交通小区之间的新增吸发量分配到od对之间；
    """
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


    if os.path.exists(r"new_built_od.xml"):
        os.remove(r"new_built_od.xml")

    od_pair = od_pair_name_new
    od_pair1 = od_pair_name_new1


    od_amount = od_pair_freq_new
    od_amount1 = od_pair_freq_new1

    od_new_amount = []
    od_new_amount1 = []

    for nn in od_amount:
        od_new_amount.append(round(nn))
        
    for nnn in od_amount1:
        od_new_amount1.append(round(nnn))
    # print(od_new_amount)
    '''
    time_gap是关键参数，用于控制OD变化的时间间隔，现在设置的是900秒，即15min
    '''
    time_gap = (int(str(timeslot).split("-")[1]) - int(str(timeslot).split("-")[0])) * 3600 
    # 创建根节点
    a = ET.Element("demand")
    # 创建子节点，并添加属性
    c = ET.SubElement(a,"timeSlice")
    dura = str(time_gap * 1000)
    t = 0
    begin_time = str(t * time_gap * 1000)
    c.attrib = {"duration": dura, "startTime": begin_time}
    for xx in range(len(od_pair)):
        amount = od_new_amount[xx]
        list1111 = od_pair[xx][0]
        list111 = od_pair[xx][1]
        d = ET.SubElement(c,"odPair")
        d.attrib = {"amount": str(amount) ,"destination":new_built_taz ,"origin": list111}
    for xxxxx in range(len(od_amount1)):
        amount1 = od_new_amount1[xxxxx]
        o1 = od_pair1[xxxxx][0]
        d1 = od_pair1[xxxxx][1]
        d = ET.SubElement(c,"odPair")
        d.attrib = {"amount": str(amount1) ,"destination":o1 ,"origin": new_built_taz}


    tree = ET.ElementTree(a)
    __indent(a, level=0)
    # tree.write(r"new_built_od.xml")
    tree.write("./output_" + tag + "/" + tag + "_od.xml")


# former_taz = "taz_86"
# new_built_taz = "taz_89"
# filtrate(former_taz,new_built_taz,400,500)