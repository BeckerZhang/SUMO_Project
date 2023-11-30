# -*- coding: utf-8 -*-
"""
Created on Wed May 25 19:10:28 2022

@author: DELL
"""
# -- coding: utf-8 --**
import os
import json
import pandas as pd
import xml.etree.ElementTree as ET


def transit_t(transit_file,json_file,filter_csv):
    with open(json_file, 'r', encoding="utf-8") as f: 
        data1 = json.load(f)
        threshold = data1["transitThreshold"] 

    df0 = pd.read_csv(transit_file) #过境od
    df0['stime_min'] = df0['stime_o'].apply(lambda x:int(float(x[:2]))*60 + int(float(x[3:])))
    df0['etime_min'] = df0['etime_d'].apply(lambda x:int(float(x[:2]))*60 + int(float(x[3:])))
    df0['stay_time_min'] = df0['etime_min'] - df0['stime_min']
    df2 = df0[df0['stay_time_min'] < int(threshold)] # 筛选出判定的过境od
    # print(len(df0))
    # print(len(df2))
    df2.to_csv(filter_csv,index = False)
    

def transit_c(filter_csv,json_file,through_file):
    with open(json_file, 'r', encoding="utf-8") as f: 
        data1 = json.load(f)
        charge = data1["transitCharge"]
        # print(charge)
    df = pd.read_csv(filter_csv)
    
    l = len(df)
    if charge == 5: 
        n = round(l/2)
        df2 = df.iloc[0:n,:]
        df2.to_csv(through_file,index = False)
    elif charge == 10:  
        n = round((l / 5) *4)
        df2 = df.iloc[0:n,:]
        df2.to_csv(through_file,index = False)
    elif charge == 15: 
        n = round((l/10)*9)
        df2 = df.iloc[0:n,:]
        df2.to_csv(through_file,index = False)
    else: 
        n = round((l/100)*99)
        df2 = df.iloc[0:n,:]
        df2.to_csv(through_file,index = False)
    
      
def transit_o(moto_file,through_file,transit_output):     
    # 筛选去除限行的过境车流
    df1 = pd.read_csv(moto_file)
    df2 = pd.read_csv(through_file)
    # print(len(df1))
    # print(len(df2))
 
    df1['tag'] = df1.iloc[:,0].isin(df2.iloc[:,0])
    od_through = df1[df1['tag'].apply(lambda x: x == False)] 
    # print(len(od_through))
    # 数据集计
    od_through_count = od_through.groupby(['odtaz_timeslot'])['u_id'].count().rename('ODcount').reset_index()
    od_through_count[['o2d_taz','timeslot']] = od_through_count['odtaz_timeslot'].str.split(',',expand = True)
    df = od_through_count[['odtaz_timeslot','o2d_taz','timeslot','ODcount']]    
    df.to_csv(transit_output,index = False)

# 统计过境车流时间分布
def time_distr(transit_file,distr_file):
    df0 = pd.read_csv(transit_file) #过境od
    df0['stime_min'] = df0['stime_o'].apply(lambda x:int(float(x[:2]))*60 + int(float(x[3:])))
    df0['etime_min'] = df0['etime_d'].apply(lambda x:int(float(x[:2]))*60 + int(float(x[3:])))
    df0['stay_time_min'] = df0['etime_min'] - df0['stime_min']
    df1 = df0[['stay_time_min']]
    df1['staytime_slot'] = df0['stay_time_min'].apply(lambda x: '0-5' if x < 5\
                                                             else '5-10' if x < 10\
                                                                 else '10-15' if x < 15\
                                                                    else '15-20' if x < 20\
                                                                        else '20-25' if x < 25\
                                                                            else '25-30' if x < 30\
                                                                                else '30-35' if x < 35\
                                                                                    else '35-60' if x < 60\
                                                                                        else '>60')
    
    df2 = pd.DataFrame({'count':df1.groupby('staytime_slot').count()['stay_time_min']})
    df2.index.name = 'staytime_slot'
    # print(df2)
    df2.to_csv(distr_file)


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
# if __name__ == "__main__":
#     root_path = r'D:\xiangmu\szgc\through_extract_upd0618'
    
# auto部分修改示例
# input # 
    # json_file = os.path.join(root_path,"./transit_flow.json")    
    # transit_file = os.path.join(root_path,"./odgc_through_all.csv")
    # moto_file = os.path.join(root_path,"./odgc_motorized_all.csv")
# output
    # filter_csv = os.path.join(root_path,"./od_filter_t.csv")
    # through_file = os.path.join(root_path,"./od_filter_c.csv")
    # transit_output = os.path.join(root_path,"./od_filter_o.csv")     
    # distr_file = os.path.join(root_path,"./time_distri.csv")
    
    # transit_t(transit_file,json_file,filter_csv)
    # transit_c(filter_csv,json_file,through_file)
    # transit_o(moto_file,through_file,transit_output)
    # time_distr(transit_file,distr_file)
    
    # writing_xml("./output_transit_flow/od_filter_count.csv", "7-9", "./output_transit_flow/od.xml")

    