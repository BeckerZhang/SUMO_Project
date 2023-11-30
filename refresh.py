import xml.etree.ElementTree as ET
import pandas as pd
import sumolib
from shapely import wkt
from shapely.geometry import LineString,Point,Polygon
import json
import re
import math
"""
首先筛选现有flow文件中，从A交通小区出发到其影响区内其他交通小区的odpair_amount以走影响区到交通小区A的odpair_amount；
并可将结果保存至csv文件中；
"""
# def read_sumo_net(path):
#     ''' 加载路网'''
#     net = sumolib.net.readNet(path, withInternal=False)  # 'withPedestrianConnections'
#     return net

def readxml(xmlfile):
    '''
    xml：
    root-根
        node-结点
            attribute-属性
            text-文本
            subnode-子节点
    :param xmlfile: 文件名#--绝对路径
    :return: root
    '''
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    return tree,root

def lonlat2taz(tazfile,file,jsonfile):
    with open(jsonfile, 'r', encoding="utf-8") as f:
        data = json.load(f)
    node_list=data["geometry"]
    polygon_edge = Polygon(node_list)
    # print(polygon_edge)
    p1 = wkt.loads(str(polygon_edge))
    point = p1.centroid.wkt
    point_split = point.split(" ")
    # print(point_split)
    lon = point_split[1][1:]
    lat = point_split[2][0:-1]
    # print(lon1)
    net = sumolib.net.readNet(file)
    radius = 200
    x, y = net.convertLonLat2XY(lon, lat)
    # print(x,y)
    edges = net.getNeighboringEdges(x, y, radius)
    # print(edges)
    # pick the closest edge
    if len(edges) > 0:
        distancesAndEdges = sorted(edges, key=lambda x:x[1])
        closestEdge,dist = distancesAndEdges[0]
    # print(str(closestEdge))
    t = re.findall(r'"(.+?)"',str(closestEdge))
    # print(t[0])

    tree,root = readxml(tazfile)
    tazs = root.findall("taz")
    for taz in tazs:
        for tazsink in taz:
            if tazsink.attrib["id"] == t[0]:
                taz_id = taz.attrib["id"]
                return taz_id
# lonlat2taz(r'C:\Users\Backer\Desktop\fresh\od.taz.xml',r'C:\Users\Backer\Desktop\fresh\osm.net.xml',r'C:\Users\Backer\Desktop\fresh\in.json')

def read_csv_file(in_path,timeslot):
        data1 = pd.read_csv(in_path ,sep=',',header='infer')  
        df = pd.DataFrame(data1)
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
            xxx = df2['odtaz_timeslot'][i].split(",")[0]
            xxxx = xxx.split("-")
            # print(xxx)
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

def minus_fresh(former_od,timeslot,changed_taz,later_od):
#  C:\Users\Backer\Desktop\dikuaigengxin_test\former_od.xml
# tree = ET.parse(former_od_path)
    tree = ET.parse(former_od)
    a = ET.Element("demand")
    b = ET.SubElement(a,"timeSlice")
    # print(int(str(timeslot).split("-")[1]))
    # print(int(str(timeslot).split("-")[0]))

    time_gap = (int(str(timeslot).split("-")[1]) - int(str(timeslot).split("-")[0])) * 3600 
    t = 0
    dura = str(time_gap * 1000)
    begin_time = str(t * time_gap * 1000)
    b.attrib = {"duration": dura, "startTime": begin_time}
    amounts = []
    destinations = []
    origins = []
    # c = ET.SubElement(b,"odPair")1
    root = tree.getroot()
    timeslices = root.findall("timeSlice")
    for timeslice in timeslices:
        # print(timeslice.findall("odPair"))
        for i in range(len(timeslice.findall("odPair"))):
            if timeslice.findall("odPair")[i].attrib["destination"] != str(changed_taz):
                if timeslice.findall("odPair")[i].attrib["origin"] != str(changed_taz):
                    amounts.append(timeslice.findall("odPair")[i].attrib["amount"])
                    destinations.append(timeslice.findall("odPair")[i].attrib["destination"])
                    origins.append(timeslice.findall("odPair")[i].attrib["origin"])
            else:
                pass
    for x in range(len(amounts)):
        amount = amounts[x]
        destination = destinations[x]
        origin = origins[x]
        c = ET.SubElement(b,"odPair")
        c.attrib = {"amount": str(amount) ,"destination":destination ,"origin": origin}
    tree1 = ET.ElementTree(a)
    __indent(a, level=0)
    tree1.write(later_od)
# former_od = r"C:\Users\Backer\Desktop\dikuaigengxin_test\former_od.xml"
# timeslot = "7-9"
# changed_taz = 177
# later_od = r"C:\Users\Backer\Desktop\fresh\later_od.xml"
# # minus_fresh()
# minus_fresh(former_od,timeslot,changed_taz,later_od)


def new_fresh(changed_taz,timeslot,in_path,od_path):


    od_pair_name_new = []
    od_pair_name_new1 = []
    od_pair_o = []
    od_pair_d = []
    od_pair_o1 = []
    od_pair_d1 = []
    od_pair_freq_new = []
    od_pair_freq_new1 = []

    result = read_csv_file(in_path,timeslot)
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
        if o == changed_taz:#affected_taz删掉就好
            od_pair_o.append(o)
            od_pair_d.append(d)
            od_pair_freq_new.append(od_num[xxx])
            od_pair_name_new.append(od_pair_name[xxx])
        elif d == changed_taz:
            od_pair_o1.append(o)
            od_pair_d1.append(d)
            od_pair_freq_new1.append(od_num[xxx])
            od_pair_name_new1.append(od_pair_name[xxx])
        else:
            pass

    sum = 0
    for xxxx in od_pair_freq_new:
        sum = sum + xxxx 
    # print(sum)#本taz作为o点的总发生量；

    sum1 = 0 
    for xxxxx in od_pair_freq_new1:
        sum1 = sum1 + xxxxx
    # print(sum1)#本taz作为d点的总吸引量；

    od_pair_freq_new_sing = []
    od_pair_freq_new1_sing = []
    for c in od_pair_freq_new:
        c = c/sum
        od_pair_freq_new_sing.append(c)
    # print(od_pair_freq_new_sing)
    for cc in od_pair_freq_new1:
        cc = cc/sum1
        od_pair_freq_new1_sing.append(cc)


    # 这一步之后，得到了每个odpair之间的一个吸发量的比例，后一步需要对od作为od点的那个demand算出来即可；

    # 之前用地条件下，生成的吸发量
    # compute_former_o = 500
    # compute_former_d = 500

    # # 更换用地性质之后的吸发量
    # compute_present_o = 600
    # compute_present_d = 600

    # 现如今需要进行交通分配的量
    sum_new = sum * 0.3
    sum1_new = sum1 * 0.3

    land_taz_o_pair_num1 = []
    land_taz_d_pair_num1 = [] 
    for t in od_pair_freq_new_sing:
        land_taz_o_pair_num1.append(math.ceil(t*sum_new))
    for tt in od_pair_freq_new1_sing:
        land_taz_d_pair_num1.append(math.ceil(tt*sum1_new))

    od_pair = []
    od_pair_num = []

    for v in od_pair_name_new:
        od_pair.append(v)
    for vv in od_pair_name_new1:
        od_pair.append(vv)

    for b in land_taz_o_pair_num1:
        od_pair_num.append(b)
    for bb in land_taz_d_pair_num1:
        od_pair_num.append(bb)

    # print(od_pair_name_new)
    # print(land_taz_o_pair_num1)
    # print(od_pair_name_new1)
    # print(land_taz_d_pair_num1)

    # land_taz_o_pair = []
    # land_taz_d_pair = []
    # 计算出每个od对的demand，存入分别作为o与d的list中；可以和之前的name一一对应；


    # if os.path.exists("G:\\projects\\xifaliang_test\\new_built_od.xml"):
    #         os.remove("G:\\projects\\xifaliang_test\\new_built_od.xml")


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
    for xx in range(len(od_pair_num)):
        amount = str(od_pair_num[xx])
        d = ET.SubElement(c,"odPair")
        d.attrib = {"amount": str(od_pair_num[xx]) ,"destination":od_pair[xx][0] ,"origin": od_pair[xx][1]}



    tree = ET.ElementTree(a)
    __indent(a, level=0)
    tree.write(od_path)
# changed_taz = "177"
# timeslot = '7-9'
# in_path = r"C:\Users\Backer\Desktop\dikuaigengxin_test\GC_ODtaz_motorized.csv"
# od_path = r"C:\Users\Backer\Desktop\dikuaigengxin_test\od.xml"
# new_fresh(changed_taz,timeslot,in_path,od_path)

def combine_od(later_od,od_path,combine_od_path):
    tree = ET.parse(later_od)
    tree1 = ET.parse(od_path)
    root = tree.getroot()
    root1 = tree1.getroot()
    timeslices1 = root1.findall("timeSlice")
    timeslices = root.findall("timeSlice")
    # for timeslice in timeslices:
    # print(len(timeslices[0]))
    for timeslice1 in timeslices1:
        for i in timeslice1:
            timeslices[0].append(i)
    # print(len(timeslices[0]))
    __indent(root, level=0)
    tree.write(combine_od_path)

# combine_od()

def fresh(jsonfile,timeslot,later_od,od_path,combine_od_path):
    changed_taz = lonlat2taz(r'./cache/od.taz.xml',r'./cache/osm.net.xml',jsonfile)
    minus_fresh(r'./cache/od.xml',timeslot,changed_taz,later_od)
    new_fresh(changed_taz,timeslot,r'./cache/GC_ODtaz_motorized.csv',od_path)
    combine_od(later_od,od_path,combine_od_path)


# fresh(r'./in/refresh.json', "7-9", r'./output_refresh/later_od.xml',\
#                             r'./output_refresh/newod.xml', r'./output_refresh/combine.xml')
# 到这一步为止是把od从之前的小区里面剪掉，后面则是需要从加上新增的吸发量
# 用地更新第一个部分的 输入是交通小区、路网文件、json输入文件和原od文件、输入时段等