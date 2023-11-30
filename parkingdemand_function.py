import xml.etree.ElementTree as ET
import os,sys
import json
import pandas as pd
import math
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from update_odxml import update_odxml

def count_change(json_file):
    '''
    停车收费政策调整输入
    '''

    # 输入调整后一类区域/二类区域收费金额
    with open(json_file, 'r', encoding="utf-8") as f:
        data1 = json.load(f)
    areaTrack1 = data1["areaTrack1"]
    chargeMethod1 = data1["chargeMethod1"]
    chargeMethod2 = data1["chargeMethod2"]
    chargePertime1 = data1["chargePertime1"]
    chargePertime2 = data1["chargePertime2"]
    chargeInOneHour1 = data1["chargeInOneHour1"]
    chargeOutOneHour1 = data1["chargeOutOneHour1"]
    chargeOneDay1 = data1["chargeOneDay1"]
    chargeInOneHour2 = data1["chargeInOneHour2"]
    chargeOutOneHour2 = data1["chargeOutOneHour2"]
    chargeOneDay2 = data1["chargeOneDay2"]

    '''
    输入完成
    '''


    df = pd.read_csv(r'./cache/odgc_motorized_all.csv')
    df_baseTaz = pd.read_excel(r'./cache/OD2Taz-upd.xlsx')

    df['park_flag'] = df['staytime_d'].apply(lambda x: 1 if x >= 15 else 0)
    df.loc[df['park_flag'] == 0, 'pcost'] = 0

    polygon = Polygon(areaTrack1)
    df_baseTaz['area_flag'] = df_baseTaz.apply(lambda x: polygon.contains(Point(x['lon'], x['lat'])), axis=1)

    # 筛选一类区域/二类区域数据
    base1_unique = df_baseTaz[df_baseTaz['area_flag'] == 1]['geohash'].unique()
    base2_unique = df_baseTaz[df_baseTaz['area_flag'] == 0]['geohash'].unique()
    df_1 = df[df['geohash_d'].isin(base1_unique)]
    df_2 = df[df['geohash_d'].isin(base2_unique)]

    # 计时或计次收费方式计算默认收费标准下停车成本，用于MNL模型标定

    # 一类区域
    if chargeMethod1 == 1:  # 计时收费
        df_1.loc[(df_1['park_flag'] == 1) & (df_1['staytime_d'] <= 60), 'pcost'] = 6
        df_1.loc[(df_1['park_flag'] == 1) & (df_1['staytime_d'] > 60), 'pcost'] = 6 + \
                                                                                  np.ceil((df_1.loc[
                                                                                               (df_1['park_flag'] == 1) & (
                                                                                                           df_1[
                                                                                                               'staytime_d'] > 60), 'staytime_d'] - 60) / 30) * 4
        df_1['pcost'] = df_1['pcost'].apply(lambda x: x if x <= 40 else 40)
    elif chargeMethod1 == 2:  # 计次收费
        df_1.loc[df_1['park_flag'] == 1, 'pcost'] = 8
    else:
        # print('Charge mode error!')
        pass

    # 二类区域
    if chargeMethod2 == 1:  # 计时收费
        df_2.loc[(df_2['park_flag'] == 1) & (df_2['staytime_d'] <= 60), 'pcost'] = 6
        df_2.loc[(df_2['park_flag'] == 1) & (df_2['staytime_d'] > 60), 'pcost'] = 6 + \
                                                                                  np.ceil((df_2.loc[
                                                                                               (df_2['park_flag'] == 1) & (
                                                                                                           df_2[
                                                                                                               'staytime_d'] > 60), 'staytime_d'] - 60) / 30) * 3
        df_2['pcost'] = df_2['pcost'].apply(lambda x: x if x <= 30 else 30)
    elif chargeMethod2 == 2:  # 计次收费
        df_2.loc[df_2['park_flag'] == 1, 'pcost'] = 6
    else:
        print('Charge mode error!')


    # 基于现有数据标定MNL模型
    # 分两类区域计算出行成本（出行时长、燃油成本、停车成本）
    # 分两类区域基于当前小汽车出行比例计算MNL模型其他出行方式常数项
    def calibration(triptime, pcar, pfunit1, pfunit2):
        # 当前一类区域小汽车出行成本
        v_car1 = (1 + 8.66) * triptime + pfunit1
        # 当前二类区域小汽车出行成本
        v_car2 = (1 + 8.66) * triptime + pfunit2
        c_other1 = math.exp(-1 * v_car1) / pcar - math.exp(-1 * v_car1)
        c_other2 = math.exp(-1 * v_car2) / pcar - math.exp(-1 * v_car2)
        return c_other1, c_other2


    pfunit1 = df_1[df_1['park_flag'] == 1]['pcost'].mean()
    pfunit2 = df_2[df_2['park_flag'] == 1]['pcost'].mean()
    triptime = df['trip_time'].mean() / 60
    pcar = len(df) / 1421308
    # MNL模型标定
    c_other1, c_other2 = calibration(triptime, pcar, pfunit1, pfunit2)


    # 政策指标变化后小汽车出行比例
    def func(unit_new1, unit_new2):
        v_car1_new = (1 + 8.66) * (df['trip_time'].mean() / 60) + unit_new1
        v_car2_new = (1 + 8.66) * (df['trip_time'].mean() / 60) + unit_new2
        p1_new = math.exp(-1 * v_car1_new) / (math.exp(-1 * v_car1_new) + c_other1)
        p2_new = math.exp(-1 * v_car2_new) / (math.exp(-1 * v_car2_new) + c_other2)
        return p1_new, p2_new


    # 计算停车收费政策指标变化后新的停车成本

    # 一类区域
    if chargeMethod1 == 1:  # 计时收费
        df_1.loc[df_1['park_flag'] == 0, 'pcost_new'] = 0
        df_1.loc[(df_1['park_flag'] == 1) & (df_1['staytime_d'] <= 60), 'pcost_new'] = chargeInOneHour1
        df_1.loc[(df_1['park_flag'] == 1) & (df_1['staytime_d'] > 60), 'pcost_new'] = chargeInOneHour1 + \
                                                                                      np.ceil((df_1.loc[(df_1[
                                                                                                             'park_flag'] == 1) & (
                                                                                                                    df_1[
                                                                                                                        'staytime_d'] > 60), 'staytime_d'] - 60) / 30) * chargeOutOneHour1
        df_1['pcost_new'] = df_1['pcost_new'].apply(lambda x: x if x <= chargeOneDay1 else chargeOneDay1)
    elif chargeMethod1 == 2:  # 计次收费
        df_1.loc[df_1['park_flag'] == 0, 'pcost_new'] = 0
        df_1.loc[df_1['park_flag'] == 1, 'pcost_new'] = chargePertime1
    else:
        # print('Charge mode error!')
        pass

    # 二类区域
    if chargeMethod2 == 1:  # 计时收费
        df_2.loc[df_2['park_flag'] == 0, 'pcost_new'] = 0
        df_2.loc[(df_2['park_flag'] == 1) & (df_2['staytime_d'] <= 60), 'pcost_new'] = chargeInOneHour2
        df_2.loc[(df_2['park_flag'] == 1) & (df_2['staytime_d'] > 60), 'pcost_new'] = chargeInOneHour2 + \
                                                                                      np.ceil((df_2.loc[(df_2[
                                                                                                             'park_flag'] == 1) & (
                                                                                                                    df_2[
                                                                                                                        'staytime_d'] > 60), 'staytime_d'] - 60) / 30) * chargeOutOneHour2
        df_2['pcost_new'] = df_2['pcost_new'].apply(lambda x: x if x <= chargeOneDay2 else chargeOneDay2)
    elif chargeMethod2 == 2:  # 计次收费
        df_2.loc[df_2['park_flag'] == 0, 'pcost_new'] = 0
        df_2.loc[df_2['park_flag'] == 1, 'pcost_new'] = chargePertime2
    else:
        # print('Charge mode error!')
        pass

    # 调整后一类区域及二类区域停车收费成本均值
    unit_new1 = df_1[df_1['park_flag'] == 1]['pcost_new'].mean()
    unit_new2 = df_2[df_2['park_flag'] == 1]['pcost_new'].mean()

    p1_new, p2_new = func(unit_new1, unit_new2)

    # 一类区域计算停车收费指标变化后新的小汽车出行成本
    df_1['trip_cost_new'] = (1 + 8.66) * (df_1['trip_time'] / 60) + df_1['pcost_new']
    # 二类区域计算停车收费指标变化后新的小汽车出行成本
    df_2['trip_cost_new'] = (1 + 8.66) * (df_2['trip_time'] / 60) + df_2['pcost_new']

    #更新数据
    deltacount1 = int(abs(p1_new - pcar) * len(df_1))
    deltacount2 = int(abs(p2_new - pcar) * len(df_2))

    # 一类区域
    if unit_new1 > pfunit1:
        redindex1 = df_1.sort_values(by='trip_cost_new', ascending=False).head(deltacount1).index.tolist()
        df_upd = df[~df.index.isin(redindex1)]
    elif unit_new1 < pfunit1:
        addindex1 = df_1.sort_values(by='trip_cost_new').head(deltacount1).index.tolist()
        df_upd = df.append(df[df.index.isin(addindex1)], ignore_index=True)
    else:
        df_upd = df

    # 二类区域
    if unit_new2 > pfunit2:
        redindex2 = df_2.sort_values(by='trip_cost_new', ascending=False).head(deltacount2).index.tolist()
        df_upd = df_upd[~df_upd.index.isin(redindex2)]
    elif unit_new2 < pfunit2:
        addindex2 = df_2.sort_values(by='trip_cost_new').head(deltacount2).index.tolist()
        df_upd = df_upd.append(df[df.index.isin(addindex2)], ignore_index=True)
    else:
        df_upd = df_upd

    # 集计
    df_upd_count = df_upd.groupby(['odtaz_timeslot'])['u_id'].count().rename('ODcount').reset_index()
    df_upd_count[['o2d_taz', 'timeslot']] = df_upd_count['odtaz_timeslot'].str.split(',', expand=True)
    df_upd_count = df_upd_count[['odtaz_timeslot', 'o2d_taz', 'timeslot', 'ODcount']]

    df_upd_count.to_csv(r'./cache/df_upd_count.csv', index=None,encoding='gbk')

    update_odxml(r'./cache/df_upd_count.csv',r'./cache/od.taz.xml',r'./cache/tazshp/gcTaz 2022-02-28.shp',r'./output_parking_charge/df_upd_count.csv')
    # 不同停车收费指标下的区域小汽车出行总量
    df_carcount = pd.DataFrame([['计次：8元/次', '计次：6元/次', 252648],
                                ['计次：7元/次', '计次：5元/次', 301252],
                                ['计次：9元/次', '计次：7元/次', 226352],
                                ['计时：一小时内收费6元，超一小时收费4.5元/半小时，1天封顶50元', '计时：一小时内收费6元，超一小时收费3.5元/半小时，1天封顶40元', 217717]],
                               columns=['一类区域停车收费标准', '二类区域停车收费标准', '区域小汽车出行总量（全天）'])
    df_carcount = df_carcount.append([{'一类区域停车收费标准': '计时：' + '一小时内收费' + str(chargeInOneHour1) + '元，' + '超一小时收费' + str(
        chargeOutOneHour1) + '元/半小时，' + '1天封顶' + str(chargeOneDay1) + '元' \
        if chargeMethod1 == 1 \
        else '计次：' + str(chargePertime1) + '元/次' \
        if chargeMethod1 == 2 \
        else 'Error',
                                       '二类区域停车收费标准': '计时：' + '一小时内收费' + str(chargeInOneHour2) + '元，' + '超一小时收费' + str(
                                           chargeOutOneHour2) + '元/半小时，' + '1天封顶' + str(chargeOneDay2) + '元' \
                                           if chargeMethod2 == 1 \
                                           else '计次：' + str(chargePertime2) + '元/次' \
                                           if chargeMethod2 == 2 \
                                           else 'Error',
                                       '区域小汽车出行总量（全天）': len(df_upd)}], ignore_index=True)
    df_carcount.to_csv(r'./output/output_parking_charge/area_carcount.csv')


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

def writing_xml(csv_path,timeslot,od_path,json_file):
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

    count_change(json_file)


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
        d.attrib = {"amount":str(od_num[taz]) ,"destination":str(d_taz[taz]) , "origin":str(o_taz[taz])}
    tree = ET.ElementTree(a)
    # print(tree)
    __indent(a, level=0)
    tree.write(od_path)

# writing_xml(r'df_upd_count.csv','7-9',r'od.xml',"./in/parking.json")