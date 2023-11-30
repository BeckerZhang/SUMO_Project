'''
本文件是用来判断交叉口各进口道方向；
'''
import xml.etree.ElementTree as ET
from pandas.core.frame import DataFrame
import sumolib
import pandas as pd
import math

def read_junction(readfile1,outputfile2):
    tree = ET.parse(readfile1)
    root = tree.getroot()  # 获取根节点
    junc = root.findall("junction")
    junc_x_final = []
    junc_y_final = []
    junc_id_final = []
    junc_incLanes_final = []
    for i in range(len(junc)):
        j_type_fin= junc[i].attrib["type"]
        j_id_fin = junc[i].attrib["id"]
        if j_id_fin.startswith(":"):
            continue
        else:
            if j_type_fin != "dead_end":
                j_id_fin = junc[i].attrib["id"]
                j_x_fin = junc[i].attrib["x"]
                j_y_fin = junc[i].attrib["y"]
                j_inc_fin = junc[i].attrib["incLanes"]
                junc_x_final.append(j_x_fin)
                junc_y_final.append(j_y_fin)
                junc_id_final.append(j_id_fin)
                junc_incLanes_final.append(j_inc_fin)
            else:
                continue
    # print(len(junc_x_final))
    # junc_final_df = DataFrame({"junc_id":junc_id_final, "junc_x":junc_x_final, "junc_y":junc_y_final})
    # print(junc_final_df)
    net = sumolib.net.readNet(readfile1)
    junc_coord_final = []
    junc_lon_final = []
    junc_lat_final = []
    for i in range(len(junc_id_final)):
        x = junc_x_final[i]
        y = junc_y_final[i]
        lon,lat = net.convertXY2LonLat(float(x), float(y))
        junc_coord_final.append((lon,lat))
        junc_lon_final.append(lon)
        junc_lat_final.append(lat)
    junc_new_zyq_df = DataFrame({"junc_id":junc_id_final, "junc_x":junc_x_final, "junc_y":junc_y_final, "junc_lon":junc_lon_final, "junc_lat":junc_lat_final, "incLanes":junc_incLanes_final})
    junc_new_zyq_df.to_csv(outputfile2)

import math
def azimuthAngle(x1, y1, x2, y2):
  angle = 0.0;
  dx = x2 - x1
  dy = y2 - y1
  if x2 == x1:
    angle = math.pi / 2.0
    if y2 == y1 :
      angle = 0.0
    elif y2 < y1 :
      angle = 3.0 * math.pi / 2.0
  elif x2 > x1 and y2 > y1:
    angle = math.atan(dx / dy)
  elif x2 > x1 and y2 < y1 :
    angle = math.pi / 2 + math.atan(-dy / dx)
  elif x2 < x1 and y2 < y1 :
    angle = math.pi + math.atan(dx / dy)
  elif x2 < x1 and y2 > y1 :
    angle = 3.0 * math.pi / 2.0 + math.atan(dy / -dx)
  return (angle * 180 / math.pi)


def judging_dir(csvfile,netxml,incsv,outcsv):
    data=pd.read_csv(csvfile)
    df=pd.DataFrame(data)
    # Step1 : 筛选出来每个交叉口进口道的id；
    inclanes=df["incLanes"].apply(lambda x:x.split(" "))
    junction = []
    junction_num = []
    for i in range(len(inclanes)):
        edges = []
        edges_num = []
        for j in range(len(inclanes[i])):
            try:
                edgex = inclanes[i][j].split('_')[2]
                edge = inclanes[i][j].split('_')[0] + "_" + inclanes[i][j].split('_')[1]
            except:
                edge = inclanes[i][j].split('_')[0]
            if ":" in edge:
                pass
            else:
                edges.append(edge)
        edges = list(set(edges))
        junction.append(edges)
        junction_num.append(len(edges))

    df["jkd_ID"] = junction
    df=df.drop(['incLanes'], axis=1)
    # print(df)

    # Step2 : 这一步需要得到edgeID与其对应的from_node的xy坐标之间的关系；
    import xml.etree.ElementTree as ET
    edge_list=[]
    edge_from_list=[]
    edge_to_list=[]
    tree=ET.parse(netxml)
    root=tree.getroot()
    junctions=root.findall("junction")
    junction_id_list=[]
    junction_x=[]
    junction_y=[]

    for junction in junctions:
        if ":" not in junction.attrib["id"]:
            junction_id_list.append(junction.attrib["id"])
            junction_x.append(junction.attrib["x"])
            junction_y.append(junction.attrib["y"])
    e ={"junction_id":junction_id_list,"junction_x":junction_x,"junction_y":junction_y}
    junction_list=pd.DataFrame(e)

    edges=root.findall("edge")
    for edge in edges:
        if ":" not in edge.attrib["id"]:
            edge_list.append(edge.attrib["id"])
            edge_from_list.append(edge.attrib["from"])
            edge_to_list.append(edge.attrib["to"])
        else:
            pass

    # 这部分需要提取junction的出口道的edgeID，才可以通过后面的步骤进行判定；
    '''
    现有的大致思路是提取所有from值为junction的交叉口；存入一个list中，把它插入df中；
    '''

    out_edge = []
    for t in range(len(df["junc_id"])):
        out = []
        for tt in range(len(edge_from_list)):
            if df["junc_id"][t] == edge_from_list[tt]:
                out.append(edge_list[tt])
        out_edge.append(out)
    # print(len(out_edge))
    df["ckd_ID"] = out_edge
    # print(df)


    f = {"edge":edge_list,"edge_from_node":edge_from_list,"edge_to_node":edge_to_list}
    to = pd.DataFrame(f)
    # print(junction_list)
    edge_from_node_x=[]
    edge_from_node_y=[]
    edge_to_node_x=[]
    edge_to_node_y=[]

    for x in to["edge_from_node"]:
        for y in range(len(junction_list["junction_id"])):
            if x == junction_list["junction_id"][y]:
                edge_from_node_x.append(junction_list["junction_x"][y])
                edge_from_node_y.append(junction_list["junction_y"][y])
                
    for xx in to["edge_to_node"]:
        for yy in range(len(junction_list["junction_id"])):
            if xx == junction_list["junction_id"][yy]:
                edge_to_node_x.append(junction_list["junction_x"][yy])
                edge_to_node_y.append(junction_list["junction_y"][yy])
    to["edge_from_node_x"] = edge_from_node_x
    to["edge_from_node_y"] = edge_from_node_y
    to["edge_to_node_x"] = edge_to_node_x
    to["edge_to_node_y"] = edge_to_node_y
    # print(len(edge_from_node_x))
    # print(len(edge_from_node_y))
    # print(to)



    # Step3 : 这一步需要将进口道ID用某一个点的坐标来代替；需要得到edgeID与from与to的node的关系；
    direction=[]
    for xxx in range(len(df["jkd_ID"])):
        x1 = df["junc_x"][xxx]
        y1 = df["junc_y"][xxx]
        angel=[]
        for yyy in df["jkd_ID"][xxx]:
            for zz in range(len(to["edge"])):
                if yyy == to["edge"][zz]:
                    x2 = to["edge_from_node_x"][zz]
                    y2 = to["edge_from_node_y"][zz]
                    ang = azimuthAngle(float(x2), float(y2), float(x1), float(y1))
                    if ang >= 0 and ang <= 45:
                        dir = '南'
                    elif ang < 360 and ang >= 315:
                        dir = '南'
                    elif ang > 45 and ang <= 135:
                        dir = '西'
                    elif ang > 135 and ang <= 225:
                        dir = '北'
                    else:
                        dir = '东'
                    angel.append(dir)
        for o in range(len(angel)):
            if angel.count(angel[o])>1:
                angel[o] = angel[o] + str(angel.count(angel[o])-1)
        direction.append(angel)
    # print(direction)
    df["进口，东、南、西、北"] = direction
    # print(df)
    direction1=[]
    for xxx1 in range(len(df["ckd_ID"])):
        x1 = df["junc_x"][xxx1]
        y1 = df["junc_y"][xxx1]
        angel1=[]
        for yyy1 in df["ckd_ID"][xxx1]:
            for zz1 in range(len(to["edge"])):
                if yyy1 == to["edge"][zz1]:
                    x2 = to["edge_to_node_x"][zz1]
                    y2 = to["edge_to_node_y"][zz1]
                    ang = azimuthAngle(float(x2), float(y2), float(x1), float(y1))
                    if ang >= 0 and ang <= 45:
                        dir1 = '南'
                    elif ang < 360 and ang >= 315:
                        dir1 = '南'
                    elif ang > 45 and ang <= 135:
                        dir1 = '西'
                    elif ang > 135 and ang <= 225:
                        dir1 = '北'
                    else:
                        dir1 = '东'
                    angel1.append(dir1)
        for oo in range(len(angel1)):
            if angel1.count(angel1[oo])>1:
                angel1[oo] = angel1[oo] + str(angel1.count(angel1[oo])-1)
        direction1.append(angel1)
    # print(direction)
    df["出口，东、南、西、北"] = direction1
    # df.to_csv("chakan.csv")
    # Step4 : 最后一步就是把df的表格改成（junction/进口道名称/进口道方位的格式）
    juns_in = []
    juns_out = []
    edgs_in = []
    edgs_out = []
    dirs_in =[]
    dirs_out=[]
    for jun in range(len(df["junc_id"])):
        for edg in range(len(df["jkd_ID"][jun])):
            edgs_in.append(df["jkd_ID"][jun][edg])
            # edgs_out.append(df["ckd_ID"][jun][edg])
            juns_in.append(df["junc_id"][jun])
            dirs_in.append(df["进口，东、南、西、北"][jun][edg])
            # dirs_out.append(df["出口，东e、南s、西w、北n"][jun][edg])

            
    for jun1 in range(len(df["junc_id"])):
        for edg1 in range(len(df["ckd_ID"][jun1])):
            # edgs_in.append(df["jkd_ID"][jun][edg])
            edgs_out.append(df["ckd_ID"][jun1][edg1])
            juns_out.append(df["junc_id"][jun1])
            # dirs_in.append(df["进口，东e、南s、西w、北n"][jun][edg])
            dirs_out.append(df["出口，东、南、西、北"][jun1][edg1])
    g = {"交叉口id":juns_in,"jkdmc":edgs_in,"jkd_dir":dirs_in}
    g1 = {"交叉口id":juns_out,"ckdmc":edgs_out,"ckd_dir":dirs_out}
    result_in = pd.DataFrame(g)
    result_in.to_csv(incsv)
    result_out = pd.DataFrame(g1)
    result_out.to_csv(outcsv)


def prepare4cal_juc(netxml,junc_file,incsv,outcsv):
    read_junction(netxml,junc_file)
    judging_dir(junc_file,netxml,incsv,outcsv)

# read_junction(r'E:\output_convert_xy\tiquluwangzuobiao\0528\latest.netnew_0528.xml',"junction_for_cal_new.csv")
# csvfile = "junction_for_cal.csv"
# netxml = 'osm.net.xml'
# incsv = "交叉口进口道方位.csv"
# outcsv = "交叉口出口道方位.csv"
# judging_dir(csvfile,netxml,incsv,outcsv)
# print(result)

# print(len(juns))
# print(len(edgs))
# print(len(dirs))

