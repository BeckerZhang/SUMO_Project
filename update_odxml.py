import geopandas as gpd
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib as plt
from math import radians, cos, sin, asin, sqrt
from shapely.geometry import Point
from collections import Counter

def geodistance(lng1,lat1,lng2,lat2):
    #lng1,lat1,lng2,lat2 = (120.12802999999997,30.28708,115.86572000000001,28.7427)
    lng1, lat1, lng2, lat2 = map(radians, [float(lng1), float(lat1), float(lng2), float(lat2)]) # 经纬度转换成弧度
    dlon=lng2-lng1
    dlat=lat2-lat1
    a=sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    distance=2*asin(sqrt(a))*6371*1000 # 地球平均半径，6371km
    distance=round(distance,3)
    return distance

def seconde_min(lt,t):
    d={}         #设定一个空字典
    for i, v in enumerate(lt):#利用函数enumerate列出lt的每个元素下标i和元素v
        d[v]=i   #把v作为字典的键，v对应的值是i
    lt.sort()    #运用sort函数对lt元素排
    y=lt[t]      #此时lt中第二小的下标是1，求出对应的元素就是字典对应的键
    return d[y]


def update_odxml(former_csv,od_taz,od_shp,later_csv):

    data = pd.read_csv(former_csv)
    # print(data)
    tree = ET.parse(od_taz)
    root = tree.getroot()
    tazs = root.findall("taz")
    taz_exsist = []
    for i in tazs:
        taz_exsist.append(i.attrib["id"])
    # print(taz_exsist)

    df = pd.DataFrame(data)
    # print(df)
    taz_list = []
    for i in range(len(df["o2d_taz"])):
        od = df["o2d_taz"][i].split("-")
        taz_list.append(od[0])
        taz_list.append(od[1])
    taz_set = list(set(taz_list))
    df_tmp = df["o2d_taz"].str.split("-",expand=True)
    # print(df_tmp)
    df= pd.concat([df, df_tmp], axis=1)
    df.rename(columns={0:'o_taz',1:'d_taz'},inplace=True)
    # print(df)
    df_o = df["o_taz"].apply(lambda x: 1 if x in taz_exsist else 0)
    df_d = df["d_taz"].apply(lambda x: 1 if x in taz_exsist else 0)
    df["df_o"] = df_o
    df["df_d"] = df_d
    # print(df)

    data1 = gpd.read_file(od_shp)
    df1 = pd.DataFrame(data1)
    taz = list(df1["TAZID"].apply(lambda x : str(x)))
    point = df1["geometry"].apply(lambda x : x.centroid)
    point = point.apply(lambda x : str(x).split("(")[1])
    point = point.apply(lambda x : x.split(")")[0])
    point = point.apply(lambda x : x.split(" ")[0] + "," + x.split(" ")[1])

    df1["point"] = point
    df1_tmp = df1["point"].str.split(",",expand=True)
    df1= pd.concat([df1, df1_tmp], axis=1)
    df1.rename(columns={0:'x',1:'y'},inplace=True)
    df2 = df1[["TAZID","x","y"]]
    df2["x"] = df2["x"].apply(lambda x : float(x))
    df2["y"] = df2["y"].apply(lambda x : float(x))
    # print(type(df2["y"][0]))

    # print(df2)
    count = 1
    t = 1
    while count > 0:

        c = []
        for j in range(len(df)):
            if df["df_o"][j] == 0:
                a = df["o_taz"][j] 
                dist=[]
                x_list = []
                y_list =[]
                for x in range(len(df2)):
                    if a == str(df2["TAZID"][x]):
                        xx = float(df2["x"][x])
                        y = float(df2["y"][x])
                        x_list.append(xx)
                        y_list.append(y)

                for yy in range(len(df2)):
                    dis = geodistance(x_list[0],y_list[0],float(df2["x"][yy]),float(df2["y"][yy]))
                    dist.append(dis)
                # print(dist)
                # print(seconde_min(dist))    
                o_present = df2["TAZID"][seconde_min(dist,t)]
                c.append(o_present)
            
            elif df["df_o"][j] == 1:
                c.append(df["o_taz"][j])
        # print(len(c))
        # print(len(df))
        d = []
        for jj in range(len(df)):
            if df["df_d"][jj] == 0:
                a1 = df["d_taz"][jj] 
                dist1=[]
                x_list1 = []
                y_list1 =[]
                for x1 in range(len(df2)):
                    if a1 == str(df2["TAZID"][x1]):
                        xx1 = float(df2["x"][x1])
                        y1 = float(df2["y"][x1])
                        x_list1.append(xx1)
                        y_list1.append(y1)
                for yy1 in range(len(df2)):
                    dis1 = geodistance(x_list1[0],y_list1[0],float(df2["x"][yy1]),float(df2["y"][yy1]))
                    dist1.append(dis1)
                # print(dist)
                # print(seconde_min(dist))    
                d_present = df2["TAZID"][seconde_min(dist1,t)]
                d.append(d_present)
            
            elif df["df_d"][jj] == 1:
                d.append(df["d_taz"][jj])

        # print(len(d))
        # print(len(df))
        p_list=[]
        for z in range(len(d)):
            if c[z] == d[z]:
                try:
                    p = str(c[z]) + "-" + str(d[z+1])
                    p_list.append(p)
                except:
                    p = str(c[z]) + "-" + str(d[z-1])
                    p_list.append(p)
            else:
                p = str(c[z]) + "-" + str(d[z])
                p_list.append(p)
        # print(p_list)
        df["o2d_taz"] = p_list
        del df['df_o']
        del df['df_d']
        del df['o_taz']
        del df['d_taz']

        df_tmp = df["o2d_taz"].str.split("-",expand=True)
        df= pd.concat([df, df_tmp], axis=1)
        df.rename(columns={0:'o_taz',1:'d_taz'},inplace=True)
        # print(df)
        df_o = df["o_taz"].apply(lambda x: 1 if x in taz_exsist else 0)
        df_d = df["d_taz"].apply(lambda x: 1 if x in taz_exsist else 0)
        df["df_o"] = df_o
        df["df_d"] = df_d
        #设置value的显示长度为200，默认为50
        pd.set_option('max_colwidth',200)
        #显示所有列，把行显示设置成最大
        pd.set_option('display.max_columns', None)
        #显示所有行，把列显示设置成最大
        pd.set_option('display.max_rows', None)
        x = Counter(df_o)[0]
        y = Counter(df_d)[0]
        count = x + y
        # print(x)
        # print(y)
        # print(count)
        t =+5

    df.to_csv(later_csv)

# former_csv = r'tw_rdc_case\cache\GC_ODtaz_motorized.csv'
# od_taz = r'tw_rdc_case\cache\od.taz.xml'
# od_shp = r'tw_rdc_case\cache\tazshp\gcTaz 2022-02-28.shp'
# later_csv = r'tw_rdc_case\cache\GC_ODtaz_motorized1.csv'
# update_odxml(former_csv,od_taz,od_shp,later_csv)