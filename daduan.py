'''
sumo netxml文件道路打断
需要安装 shapely,scipy
2021/4/1

sumo路网介绍 url=https://blog.csdn.net/weixin_42963375/article/details/112389777

xml url：https://docs.python.org/3/library/xml.etree.elementtree.html
xpath url=https://www.w3school.com.cn/xpath/xpath_syntax.asp

shapely url：https://www.osgeo.cn/shapely/manual.html#geometric-objects

起点的junction ：x="-21.07" y="54.43" 终点的junction：x="63.84" y="53.19"    lane的起点：-21.14,49.63，lane的终点：63.77,48.39
lane1和junction 起点的差值：delta=23.0499  终点：delta=23.0449
length="22.62"	 手动：x="1.55" y="54.10"   机动：x="1.48" y="49.30"   差值：delta=23.0499

四个点以上使用scipy进行三次插值，插值精度为0.01或x间隔为0.001

能否导入sumo-gui.exe的关键点：
    各元素的顺序需要对应
    断开的lane，不能添加在internal edge中不能添加lane，同时对应的junction 的intLanes也不能含有不进行连接的lane
'''
import xml.etree.ElementTree as ET
import time
from shapely import wkt
from shapely.geometry import LineString,Point,Polygon
import json
import os
from scipy.interpolate import interp1d
from math import fabs,sqrt
import pandas as pd
import math
import sys
import json
import sumolib
import re
from pandas.core.frame import DataFrame

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


_JUNCTION_JSON_ = {'id': '', 'type': 'priority', 'x': '', 'y': '', 'incLanes': '', 'intLanes': '', 'keepClear': '', 'name': 'cut junction', 'fringe': '', 'shape': ''}
_CONNECTION_JSON_ = {'from': '', 'to': '', 'fromLane': '', 'toLane': '', 'dir': 's', 'state': 'M'}
_LANE_JSON_ = {'id': '', 'index': '', 'speed': '', 'length': '', 'shape': ''}
_INTERNAL_EDGE_JSON_ = {'id': '', 'function': 'internal'}

import sumolib
#---xml文件读取，操作---
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
def read_sumo_net(path):
    ''' 加载路网'''
    net = sumolib.net.readNet(path, withInternal=False)  # 'withPedestrianConnections'
    return net
#--输入坐标点，计算几何长度--
def CalculateLength(coodinate):
    line=LineString(coodinate)
    return line.length

def getLength(coodinate):
    length=0
    for i,(x,y) in enumerate(coodinate):
        if i==0:
            px=x;py=y
        else:
            length+=sqrt((x-px)**2+(y-py)**2)
            px=x;py=y
    return length

#--获取edge的shape属性，并返回数值型，获取包含多个车道的shape
def getShape(edge):
    '''
    :param edge: edge节点
    :return: [edge_shape:[(x,y)],lane1:[(x,y),(x,y)..],lane2:[(x,y)(x,y)...]...]
    '''
    shapes=[]
    if None != edge.get('shape'):
        shapes.append(edge.get('shape'))
        lanes = edge.findall('lane')
        shapes.extend([lane.get('shape') for lane in lanes])
    else:
        lanes = edge.findall('lane')
        shapes.extend([lane.get('shape') for lane in lanes])

    if len(shapes)<1:
        raise ("--the shape of the edge having the attribute you find is None --")
    #--分割字符串--
    coodinates=[]
    for i,shape in enumerate(shapes):
        x_y=list(shape.split(" "))
        coodinate = []
        for each in x_y:
            data = each.split(',')
            coodinate.append((float(data[0]), float(data[1])))
        coodinates.append(coodinate.copy())
    return coodinates.copy()

def getPolyCenter(coodainate):
    poly=Polygon(coodainate)
    center=poly.centroid
    return center.x,center.y

def get_coordXY(coordinate):
    x_list=[]
    y_list=[]
    for (x,y) in coordinate:
        x_list.append(x)
        y_list.append(y)
    return x_list,y_list

#--线打断--3段式--
def break_in_line(coordinate,from_dis,to_dis,nomalize):
    '''
    :param coordinate: 坐标列表，【（x，y），（）】
    :param from_dis: 距离起始段（from）的距离 或 占此线段的比值，超出范围返回None
    :param to_dis: 距离结束段（to）的距离 或 占此线段的比值，超出范围返回None,from 与 to 之和超过总长或1时，同样返回None
    :param nomalize: 决定取距离 或 占比  0 或 1
    :return: 返回打断后的三段线段的坐标列表（3个列表）[from:[(x,y),(x,y)..],cut:[(x,y),(x,y)..],to:[(x,y),(x,y)..]]
    '''
    #--10段--插值--
    line=LineString(coordinate)
    total_length=line.length
    #--判断起始距离范围--
    nomal=None
    if nomalize==0:
        nomal=False
        if  (from_dis<0 or from_dis>total_length):
            return None
        if to_dis<0 or to_dis+from_dis>=total_length:
            return None
    else:
        nomal=True
        if from_dis<0 or from_dis>1:
            return None
        if to_dis<0 or to_dis+from_dis>=1:
            return None
        # to_dis=to_dis/(1-from_dis)
        from_dis=total_length*from_dis
        to_dis=total_length*to_dis
    # print("起始距离：%f，终点距离：%f，总长：%f"%(from_dis,to_dis,total_length))
    #-------切割------
    line_from=[]
    line_rest=[]
    line_cut=[]
    line_to=[]
    #--第一段--
    import matplotlib.pyplot as plt

    distance=0
    x,y=get_coordXY(coordinate)
    # print("x,y",list(zip(x,y)))
    for i,p in enumerate(coordinate):
        pd=line.project(Point(p))#--距离起始点的距离
        if pd==from_dis:
            line_from=coordinate[:i+1]
            line_rest=coordinate[i:]
            break
        if pd>from_dis:
            #--三次插值--
            distance=from_dis-distance
            interval_line=LineString([coordinate[i-1],coordinate[i]])
            cp=interval_line.interpolate(distance)
            line_from=coordinate[:i] + [(cp.x,cp.y)]
            line_rest=[(cp.x,cp.y)] + coordinate[i:]
            break
        #--记录上一个点的距离
        distance = pd
    #--第二段、第三段--
    distance=0
    # print("剩下的line shape：",line_rest)
    line_rest.reverse()#--反序
    x,y=get_coordXY(line_rest)
    line=LineString(line_rest)
    for i,p in enumerate(line_rest):
        pd=line.project(Point(p))#--距离起始点的距离
        if pd==to_dis:
            line_to=line_rest[:i+1]
            line_cut=line_rest[i:]
            break
        if pd>to_dis:
            #--三次插值--
            distance=to_dis-distance
            interval_line=LineString([line_rest[i-1],line_rest[i]])
            cp=interval_line.interpolate(distance)
            line_to=line_rest[:i] + [(cp.x, cp.y)]
            line_cut=[(cp.x, cp.y)] + line_rest[i:]
            break
        distance = pd
    #--结果再次反序--
    line_cut.reverse()
    line_to.reverse()
    # print("the result of cut:",line_from.copy(),line_cut.copy(),line_to.copy())
    return line_from.copy(),line_cut.copy(),line_to.copy()
#--线打断--2段式--
def break_in_line2(coordinate,from_dis,nomalize):
    '''
    :param coordinate: 坐标列表，【（x，y），（）】
    :param from_dis: 距离起始段（from）的距离 或 占此线段的比值，超出范围返回None
    :param to_dis: 距离结束段（to）的距离 或 占此线段的比值，超出范围返回None,from 与 to 之和超过总长或1时，同样返回None
    :param nomalize: 决定取距离 或 占比  0 或 1
    :return: 返回打断后的三段线段的坐标列表（3个列表）[from:[(x,y),(x,y)..],cut:[(x,y),(x,y)..],to:[(x,y),(x,y)..]]
    '''
    #--10段--插值--
    line=LineString(coordinate)
    total_length=line.length
    #--判断起始距离范围--
    nomal=None
    if nomalize==0:
        nomal=False
        if  (from_dis<0 or from_dis>total_length):
            return None
    else:
        nomal=True
        if from_dis<0 or from_dis>1:
            return None
        # to_dis=to_dis/(1-from_dis)
        from_dis=total_length*from_dis
    # print("起始距离：%f，总长：%f"%(from_dis,total_length))
    #-------切割------
    line_from=[]
    line_rest=[]
    line_cut=[]
    line_to=[]
    #--第一段--
    import matplotlib.pyplot as plt

    distance=0
    x,y=get_coordXY(coordinate)
    # print("x,y",list(zip(x,y)))
    for i,p in enumerate(coordinate):
        pd=line.project(Point(p))#--距离起始点的距离
        if pd==from_dis:
            line_from=coordinate[:i+1]
            line_rest=coordinate[i:]
            break
        if pd>from_dis:
            distance=from_dis-distance
            interval_line=LineString([coordinate[i-1],coordinate[i]])
            cp=interval_line.interpolate(distance)
            line_from=coordinate[:i] + [(cp.x,cp.y)]
            line_rest=[(cp.x,cp.y)] + coordinate[i:]
            break
        #--记录上一个点的距离
        distance = pd
    # line_rest.reverse()#--反序
    return line_from.copy(),line_rest.copy()

#--插值--
def interpolate(coodinate,distance,normalize):
    line=LineString(coodinate)
    px=line.interpolate(distance,normalized=normalize)
    return px.x,px.y


#--获取线性方向上指定距离的点--
def getLinar_dis_poi(coodinate,distance):
    line=LineString(coodinate)
    pos=line.interpolate(distance)
    return pos

#--单个坐标列表转一行string
def coodinate_listToString(coodinate):
    '''
    :param coodinate: [(x,y),(x,y)...]
    :return:
    '''
    String=""
    length=len(coodinate)
    for i,(x,y) in enumerate(coodinate):
        String+="%.2f,%.2f"%(x,y)
        if i<length-1:
            String+=" "
    return String

#--创建junction子节点--
def create_junction(root,junction_id,junc_center,junction_poly):
    '''
    #--junction取最左点
    :param root:
    :param junction_id:
    junc_center:2*(x,y)
    :param junction_poly: 2*[(x,y),(x,y)..]
    :return:
    '''
    junc_dic= _JUNCTION_JSON_
    #--处理junction的shape
    junc_shape=[coodinate_listToString(data) for data in junction_poly]

    node=root.findall('junction/..')[0]
    #--
    for i,id in enumerate(junction_id):
        attrib=junc_dic.copy()
        x,y=junc_center[i]
        # print("junction%s坐标：%f,%f"%(id,x,y))
        attrib['id']=id
        attrib['x']="%.2f"%x
        attrib['y']="%.2f"%y
        attrib['shape']=junc_shape[i]
        if None!=node:
            ET.SubElement(node,'junction',attrib)
        else:
            ET.SubElement(root, 'junction', attrib)
    return root

#--根据分割后的三段创建edges，修补junction属性,修改connection属性--
def create_edges(root,edge,ids,coodinates,junction_id):
    edge_attrib=edge.attrib#--edge属性
    lanes=edge.findall('lane')
    node=root#--edge父节点
    lanes_attrib=[each.attrib for each in lanes]#--lane属性列表
    lanes_num=len(lanes)
    has_shape=1 if 'shape' in edge_attrib.keys() else 0#--edge是否有shape属性
    #--创建edge--
    edge_shape=None
    if has_shape:
        edge_shape=coodinates.pop(0)
    for i,id in enumerate(ids):
        #--edge修改length，id，shape，from，to属性
        edge_dic=edge_attrib.copy()
        edge_dic['id']=id
        if has_shape:
            string=coodinate_listToString(edge_shape[i])
            edge_dic['shape']=string
            length = CalculateLength(edge_shape[i])
            edge_dic['length'] = str(length)
        if i==0:
            edge_dic['to']=junction_id[0]
        if i==1:
            edge_dic['from']=junction_id[0]
            edge_dic['to']=junction_id[1]
        if i==2:
            edge_dic['from']=junction_id[1]
        edge_ele = ET.Element('edge', edge_dic)
        incLanes = ""#--junction的incLanes属性
        for j,lane in enumerate(coodinates):
            #--lane修改id，length，shape，
            string=coodinate_listToString(lane[i])#--单条lane的第i段，共三段
            lane_dic=lanes_attrib[j].copy()#--第j条lane的属性
            lane_dic['shape']=string
            lane_dic['length']=str(CalculateLength(lane[i]))
            lane_dic['id']=id+"_%s"%lane_dic['index']
            #--junction--
            incLanes+=id+"_%s "%lane_dic['index']
            ET.SubElement(edge_ele,'lane',lane_dic)
        #--修改incLanes属性
        for junc_node in root.findall(".//junction[@id='%s']"%edge_dic['to']):
            # data=junc_node.get('incLanes')
            junc_node.set('incLanes',incLanes[:len(incLanes)-1])
        if node!=None:
            node.append(edge_ele)
        else:
            root.append(edge_ele)
    # --修补connection属性,在原edge两端的connection--
    ID=edge_attrib['id']
    flag=None
    from_id=edge_attrib['from'];to_id=edge_attrib['to']
    connect_nodes = root.findall(".//connection[@to='%s']" % edge_attrib['id'])#--to为原edge
    for con_node in connect_nodes:#--所有connection
        #--找连接边--
        con_from = con_node.get('from')
        for connect in root.findall(".//edge[@id='%s']"%con_from):#--所有连接边
            if 'from' in connect.keys():#--连接边不为internal
                con_junc_to=connect.get('to')
                if con_junc_to==to_id:#--连接边的开始结点为此边的结束点,则连接方式为接入edge的尾部
                    con_node.set('to',ids[-1])
                    #--internal的connection
                    for internal_con in root.findall(".//connection[@to='%s'" % edge_attrib['id']):
                        if 'via' not in internal_con.keys():
                            internal_con.set('to',ids[-1])

                elif con_junc_to==from_id:
                    con_node.set('to',ids[0])#--接入头部
                    for internal_con in root.findall(".//connection[@to='%s']" % edge_attrib['id']):
                        if 'via' not in internal_con.keys():
                            internal_con.set('to', ids[0])

    connect_nodes = root.findall(".//connection[@from='%s']" % edge_attrib['id'])
    for con_node in connect_nodes:
        #--找连接边--
        con_from = con_node.get('to')
        for connect in root.findall(".//edge[@id='%s']" % con_from):  # --所有连接边
            if 'from' in connect.keys():  # --连接边不为internal
                con_junc_from=connect.get('from')
                if con_junc_from==to_id:#--连接边的开始结点为此边的结束点,则连接方式从edge的尾部接出
                    con_node.set('from',ids[-1])
                    # --internal的connection
                elif con_junc_from==from_id:#--从头部接出
                    con_node.set('from',ids[0])#--接入头部
    return root
def create_edges2(root,edge,ids,coodinates,junction_id):
    edge_attrib=edge.attrib#--edge属性
    lanes=edge.findall('lane')
    node=root#--edge父节点
    lanes_attrib=[each.attrib for each in lanes]#--lane属性列表
    lanes_num=len(lanes)
    has_shape=1 if 'shape' in edge_attrib.keys() else 0#--edge是否有shape属性
    #--创建edge--
    edge_shape=None
    if has_shape:
        edge_shape=coodinates.pop(0)
    # print(ids)
    for i,id in enumerate(ids):
        #--edge修改length，id，shape，from，to属性
        edge_dic=edge_attrib.copy()
        edge_dic['id']=id
        if has_shape:
            string=coodinate_listToString(edge_shape[i])
            edge_dic['shape']=string
            # print(edge_shape[i])
            length = CalculateLength(edge_shape[i])
            edge_dic['length'] = str(length)
        if i==0:
            edge_dic['to']=junction_id[0]
        if i==1:
            edge_dic['from']=junction_id[0]
        edge_ele = ET.Element('edge', edge_dic)
        incLanes = ""#--junction的incLanes属性
        for j,lane in enumerate(coodinates):
            #--lane修改id，length，shape，
            string=coodinate_listToString(lane[i])#--单条lane的第i段，共三段
            lane_dic=lanes_attrib[j].copy()#--第j条lane的属性
            lane_dic['shape']=string
            # print(lane[i])
            lane_dic['length']=str(CalculateLength(lane[i]))
            lane_dic['id']=id+"_%s"%lane_dic['index']
            #--junction--
            incLanes+=id+"_%s "%lane_dic['index']
            ET.SubElement(edge_ele,'lane',lane_dic)
        #--修改incLanes属性
        for junc_node in root.findall(".//junction[@id='%s']"%edge_dic['to']):
            # data=junc_node.get('incLanes')
            junc_node.set('incLanes',incLanes[:len(incLanes)-1])
        if node!=None:
            node.append(edge_ele)
        else:
            root.append(edge_ele)
    # --修补connection属性,在原edge两端的connection--
    ID=edge_attrib['id']
    flag=None
    from_id=edge_attrib['from'];to_id=edge_attrib['to']
    connect_nodes = root.findall(".//connection[@to='%s']" % edge_attrib['id'])#--to为原edge
    for con_node in connect_nodes:#--所有connection
        #--找连接边--
        con_from = con_node.get('from')
        for connect in root.findall(".//edge[@id='%s']"%con_from):#--所有连接边
            if 'from' in connect.keys():#--连接边不为internal
                con_junc_to=connect.get('to')
                if con_junc_to==to_id:#--连接边的开始结点为此边的结束点,则连接方式为接入edge的尾部
                    con_node.set('to',ids[-1])
                    #--internal的connection
                    for internal_con in root.findall(".//connection[@to='%s'" % edge_attrib['id']):
                        if 'via' not in internal_con.keys():
                            internal_con.set('to',ids[-1])

                elif con_junc_to==from_id:
                    con_node.set('to',ids[0])#--接入头部
                    for internal_con in root.findall(".//connection[@to='%s']" % edge_attrib['id']):
                        if 'via' not in internal_con.keys():
                            internal_con.set('to', ids[0])

    connect_nodes = root.findall(".//connection[@from='%s']" % edge_attrib['id'])
    for con_node in connect_nodes:
        #--找连接边--
        con_from = con_node.get('to')
        for connect in root.findall(".//edge[@id='%s']" % con_from):  # --所有连接边
            if 'from' in connect.keys():  # --连接边不为internal
                con_junc_from=connect.get('from')
                if con_junc_from==to_id:#--连接边的开始结点为此边的结束点,则连接方式从edge的尾部接出
                    con_node.set('from',ids[-1])
                    # --internal的connection       
                elif con_junc_from==from_id:#--从头部接出
                    con_node.set('from',ids[0])#--接入头部
                    
    return root

#--根据shape创建internal edge，同时创建connection，修补junction属性--
def create_internal_Edge(root,edges_id,junction_id,lanes_num,coodinates,lane_indexs):
    '''
    :param root:
    :param edges_id:
    :param junction_id:
    :param lanes_num:
    :param coodinates: internal_coodinate n*2 ,n为车道数
    :return:
    '''

    internal_dic=_INTERNAL_EDGE_JSON_
    connect_dic=_CONNECTION_JSON_
    lane_dic=_LANE_JSON_
    #--开始创建internal
    internal_id=[]
    #--request_num
    # index=0
    for i,id in enumerate(junction_id):
        edge=root.find('edge[@id="%s"]'%edges_id[i])
        #--
        connect_num = 0
        inter_dic=internal_dic.copy()
        inter_dic['id']=":%s_0"%id
        internal_id.append(inter_dic)
        inter_ele=ET.Element('edge',inter_dic)
        intLanes=""
        #--Lane的index
        indexLane=0
        for j in range(lanes_num):#--车道--
            #---需要封锁的lane不创建connection--
            if j not in lane_indexs:
                lane = edge.find("lane[@index='%d']"%j)
                speed=None
                try:
                    speed=lane.get('speed')
                except:
                    pass
                lane_diction=lane_dic.copy()
                length=CalculateLength(coodinates[j][i])
                lane_diction['length']=str(0.1)#---internal 最小长度为0.1
                string=coodinate_listToString(coodinates[j][i])
                lane_diction['shape']=string
                lane_diction['index']=str(indexLane)
                lane_diction['id']=inter_dic['id']+"_%d"%indexLane
                lane_diction['speed']=str(speed)


                # print("--车道：%d创建connection--"%j)
                connect_num+=1
                # print("断开的lane_index为",lane_indexs)
                #--edge之间的connection
                con_dic=connect_dic.copy()
                con_dic['from']=edges_id[i]
                con_dic['to']=edges_id[i+1]
                con_dic['fromLane']=str(j)
                con_dic['toLane']=str(j)
                con_dic['via']=lane_diction['id']
                ET.SubElement(root,'connection',con_dic)
                #--edge与internal之间的连接--
                con_dic = connect_dic.copy()
                con_dic['from']=inter_dic['id']
                con_dic['to'] =edges_id[i+1]
                con_dic['fromLane'] = str(indexLane)
                con_dic['toLane'] = str(j)
                ET.SubElement(root, 'connection', con_dic)
                #--不在封锁列表内，则补全intLanes，创建internal-lane
                intLanes += lane_diction['id'] + " "
                ET.SubElement(inter_ele,'lane',lane_diction)
                indexLane+=1
        #--补全junction的intLanes属性
        req_dic={}
        for node in root.findall('.//junction[@id="%s"]'%id):
            node.set("intLanes",intLanes[:len(intLanes)-1])
            resp="0"*connect_num
            for i in range(connect_num):
                req_dic['index']="%d"%(connect_num-i-1)
                req_dic['response']=resp
                req_dic['foes']=resp
                req_dic['cont']="0"
                ET.SubElement(node,'request',req_dic)
        root.append(inter_ele)
    return root



#--打断xml线，修正属性--
def breakAndModify(root,edge,from_dis,to_dis,nomalize,lane_indexs):
    '''
    :param root: xml树的根节点
    :param edge: 需要打断的edge结点
    :param coodinates_cut: 打断后的3段坐标数据，包含多个车道的打断结果
    --[lane1:[from:[(x,y),(x,y),...],cut:[(x,y),(x,y),...],to:[(x,y),(x,y),...]],lane2[from:[],cut:[],to:[]],lane3[[],[],[]],...]
    :return: 返回根节点
    '''
    #--提取属性--
    root.remove(edge)
    id=edge.get('id')
    from_id=edge.get('from')
    to_id=edge.get('to')#--原edge的to id
    new_id=[id+'_1',id+"cut",id+"_2"]#--新edge的id
    junction_id=[id+"_cut_junc1",id+"_cut_junc2"]#--需要添加的junction id
    attrib=edge.attrib#---所有属性
    lanes_node=edge.findall('lane')
    lane_num=len(lanes_node)#--车道数
    #--获取坐标--
    shape=getShape(edge)
    coodinates_cut=[]
    for data in shape:
        # print("切断前：",data)
        cut=list(break_in_line(data,from_dis,to_dis,nomalize))
        coodinates_cut.append(cut.copy())
        cut.clear()
    #--坐标处理，生成内连接线--
    lanes_coodinate=[];internal_coodinates=[]#--新lane坐标和internal线坐标
    junc_center=[]#--junction坐标
    for i,lane in enumerate(coodinates_cut):#--每个车道--
        x,y=0,0
        lane_coodinate=[];interedge_coodinate=[]#--记录一个车道--
        edge_section=[]#--单个部分--
        poly=[]
        for j,section in enumerate(lane):#--一个部分--
            #--
            poly.append(section[-1])
            if j==0:#--第一段--

                #--new--
                edge_section.append(section[-1])#-单个internal车道的shape
                lane_coodinate.append(section.copy())
            elif j==1:#--第二段头尾都进行处理，裁出 internal edge
                # poly.append(section[0])
                edge_section.append(section[0])
                interedge_coodinate.append(list(edge_section.copy()))
                edge_section.clear()
                edge_section.append(section[-1])#--第二段internal的头
                lane_coodinate.append(section.copy())
            else:
                # poly.append(section[0])
                # --internal edge 部分第二段尾
                edge_section.append(section[0])
                interedge_coodinate.append(list(edge_section.copy()))
                edge_section.clear()
                #--lane第三段--
                lane_coodinate.append(section.copy())
        if len(junc_center)<1:
            junc_center.extend(poly.copy())
        poly.clear()
        lanes_coodinate.append(lane_coodinate.copy())#--添加单挑车道
        lane_coodinate.clear()
        internal_coodinates.append(interedge_coodinate.copy())#--添加单条internal的lane
        interedge_coodinate.clear()
    #---junction坐标处理--，偏移计算--
    junc_from=root.find('junction[@id="%s"]'%from_id)
    # junc_to=root.find('junction[@id="%s"]'%to_id)
    delta=0#--偏移量
    direction_x=0;direction_y=0#--偏移方向
    k=0#--斜率
    lane_x,lane_y=shape[0][0]
    junc_from_pos=[float(junc_from.get('x')),float(junc_from.get('y'))]
    direction_x=junc_from_pos[0]-lane_x
    direction_y=junc_from_pos[1]-lane_y
    # junc_to_pos=[junc_to.get('x'),junc_to.get('y')]
    true_juncPos=[]#--偏移后的位置
    #--junction位置计算
    for i,data in enumerate(junc_center):#--3个
        # print("data:",data)
        x,y=data
        if i<2:
            x+=direction_x
            y+=direction_y
            true_juncPos.append([x,y])
    junction_poly=[]
    junc_poly=junc_from.get('shape')
    points=list(junc_poly.split(' '))
    if len(points)>=2:
        x,y=points[0].split(',')
        x1,y1=points[1].split(',')
        direction_x=float(x)-float(x1)
        direction_y=float(y)-float(y1)
        for x0,y0 in junc_center:
            poly=[]
            poly.append((x0,y0))
            x0+=direction_x
            y0+=direction_y
            poly.append((x0,y0))
            junction_poly.append(poly.copy())


    #--edge处理--lanes_coodinate n*3 列表，internal_coodinate n*2 列表，true_juncPos 2*(x,y) junction_poly 2*[(x,y),(x,y)..]
    #--创建junction--
    root=create_junction(root,junction_id,true_juncPos,junction_poly)
    #--创建新的edges结点，并修补junction属性
    root=create_edges(root,edge,new_id,lanes_coodinate,junction_id)
    #--创建internal edge--,补全connection
    # print("junction_id:",junction_id)
    root=create_internal_Edge(root,new_id,junction_id,lane_num,internal_coodinates,lane_indexs)
    return root
#--打断xml线，修正属性--
def breakAndModify2(root,edge,from_dis,nomalize,lane_indexs):
    '''
    :param root: xml树的根节点
    :param edge: 需要打断的edge结点
    :param coodinates_cut: 打断后的3段坐标数据，包含多个车道的打断结果
    --[lane1:[from:[(x,y),(x,y),...],cut:[(x,y),(x,y),...],to:[(x,y),(x,y),...]],lane2[from:[],cut:[],to:[]],lane3[[],[],[]],...]
    :return: 返回根节点
    '''
    #--提取属性--
    root.remove(edge)
    id=edge.get('id')
    from_id=edge.get('from')
    to_id=edge.get('to')#--原edge的to id
    new_id=[id+'_1',id+"_2"]#--新edge的id
    junction_id=[id+"_cut_junc1"]#--需要添加的junction id
    attrib=edge.attrib#---所有属性
    lanes_node=edge.findall('lane')
    lane_num=len(lanes_node)#--车道数
    print(id,from_dis)
    #--获取坐标--
    shape=getShape(edge)
    print(shape)
    coodinates_cut=[]
    for data in shape:
        print("切断前：",data)
        cut=list(break_in_line2(data,from_dis,nomalize))
        coodinates_cut.append(cut.copy())
        cut.clear()
    #--坐标处理，生成内连接线--
    lanes_coodinate=[];internal_coodinates=[]#--新lane坐标和internal线坐标
    junc_center=[]#--junction坐标
    for i,lane in enumerate(coodinates_cut):#--每个车道--
        x,y=0,0
        lane_coodinate=[];interedge_coodinate=[]#--记录一个车道--
        edge_section=[]#--单个部分--
        poly=[]
        for j,section in enumerate(lane):#--一个部分--
            #--
            poly.append(section[-1])
            if j==0:#--第一段--
                edge_section.append(section[-1])#-单个internal车道的shape
                lane_coodinate.append(section.copy())
            else:
                # edge_section.append(section[0])
                # interedge_coodinate.append(list(edge_section.copy()))
                # edge_section.clear()
                # lane_coodinate.append(section.copy())
                edge_section.append(section[0])
                interedge_coodinate.append(list(edge_section.copy()))
                edge_section.clear()
                edge_section.append(section[-1])  # --第二段internal的头
                lane_coodinate.append(section.copy())
        if len(junc_center)<1:
            junc_center.extend(poly.copy())
        poly.clear()
        lanes_coodinate.append(lane_coodinate.copy())#--添加单挑车道
        lane_coodinate.clear()
        internal_coodinates.append(interedge_coodinate.copy())#--添加单条internal的lane
        interedge_coodinate.clear()
    #---junction坐标处理--，偏移计算--
    junc_from=root.find('junction[@id="%s"]'%from_id)
    # junc_to=root.find('junction[@id="%s"]'%to_id)
    delta=0#--偏移量
    direction_x=0;direction_y=0#--偏移方向
    k=0#--斜率
    lane_x,lane_y=shape[0][0]
    junc_from_pos=[float(junc_from.get('x')),float(junc_from.get('y'))]
    direction_x=junc_from_pos[0]-lane_x
    direction_y=junc_from_pos[1]-lane_y
    # junc_to_pos=[junc_to.get('x'),junc_to.get('y')]
    true_juncPos=[]#--偏移后的位置
    #--junction位置计算
    for i,data in enumerate(junc_center):#--3个
        # print("data:",data)
        x,y=data
        if i<2:
            x+=direction_x
            y+=direction_y
            true_juncPos.append([x,y])
    junction_poly=[]
    junc_poly=junc_from.get('shape')
    points=list(junc_poly.split(' '))
    if len(points)>=2:
        x,y=points[0].split(',')
        x1,y1=points[1].split(',')
        direction_x=float(x)-float(x1)
        direction_y=float(y)-float(y1)
        for x0,y0 in junc_center:
            poly=[]
            poly.append((x0,y0))
            x0+=direction_x
            y0+=direction_y
            poly.append((x0,y0))
            junction_poly.append(poly.copy())



    #--edge处理--lanes_coodinate n*3 列表，internal_coodinate n*2 列表，true_juncPos 2*(x,y) junction_poly 2*[(x,y),(x,y)..]
    #--创建junction--
    root=create_junction(root,junction_id,true_juncPos,junction_poly)
    #--创建新的edges结点，并修补junction属性
    root=create_edges2(root,edge,new_id,lanes_coodinate,junction_id)
    #--创建internal edge--,补全connection
    # print("junction_id:",junction_id)
    root=create_internal_Edge(root,new_id,junction_id,lane_num,internal_coodinates,lane_indexs)
    return root
def beautifulTree(root):
    # type_tag=root.findall(".//type")
    edge_node = root.findall('.//edge')
    junction_tag = root.findall('.//junction')
    connect_tag = root.findall('.//connection')
    roundabout_tag=root.findall(".//roundabout")
    #--删除原始文件--
    for each in root.findall('.//edge'):
        root.remove(each)
    for each in root.findall('.//junction'):
        root.remove(each)
    for each in root.findall('.//connection'):
        root.remove(each)
    for each in root.findall(".//roundabout"):
        root.remove(each)
    # --重新插入--
    for data in edge_node:
        root.append(data)
    for data in junction_tag:
        root.append(data)
    for data in connect_tag:
        root.append(data)
    for data  in roundabout_tag:
        root.append(data)
    tree = ET.ElementTree(root)
    return tree


def prettyXml(element, indent, newline, level=0):  # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行
    if element:  # 判断element是否有子元素
        if element.text == None or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # else:  # 此处两行如果把注释去掉，Element的text也会另起一行
        # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
    temp = list(element)  # 将elemnt转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        prettyXml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作

def cut_edge(file,edge_value,from_dis, to_dis, nomal,str_index):#str_index为车道数的index
    try:
        tree, root = readxml(file)
    except:
        raise("检查文件是否存在...")
    try:
        test_edge = root.findall('.//edge[@%s="%s"]'%("id",edge_value))[0]
    except:
        raise ("找不到%s='%s'的边！！"%("id",edge_value))
    lane_num = len(test_edge.findall('lane'))
    lane_index = []
    if str_index[0] == '':
        lane_index = []
    else:
        for data in str_index:
            if int(data) >= lane_num:
                raise ("Error:索引错误！！")
            lane_index.append(int(data))
    root = breakAndModify(root, test_edge, float(from_dis), float(to_dis), int(nomal), lane_index)
    new_tree = beautifulTree(root)
    prettyXml(root, '\t', '\n')  # 执行美化方法
    # if not os.path.exists(r'./result'):
    #     os.makedirs(r'./result')
    # output = os.path.join('result', file.split('\\')[-1].split('.')[0] + '_cut.net.xml')
    # output = os.path.join(r'./result', (file.split('\\')[-1].split('.')[0]).split('_')[0] + '_cut.net.xml')
    output = os.path.join(r'./output_new_built/osm.net.xml')
    new_tree.write(output, encoding='utf-8')
def cut_edges(file,edge_value,from_dis,nomal,str_index,tag):
    try:
        tree, root = readxml(file)
    except:
        raise("检查文件是否存在...")
    try:
        # print(root.findall('.//edge[@%s="%s"]'%("id",edge_value)))
        test_edge = root.findall('.//edge[@%s="%s"]'%("id",edge_value))[0]
    except:
        # print("error")
        raise("找不到%s='%s'的边！！"%("id",edge_value))
    lane_num = len(test_edge.findall('lane'))
    lane_index = []
    if str_index[0] == '':
        lane_index = []
    else:
        for data in str_index:
            if int(data) >= lane_num:
                raise ("Error:索引错误！！")
            lane_index.append(int(data))
    root = breakAndModify2(root, test_edge, float(from_dis), int(nomal), lane_index)
    new_tree = beautifulTree(root)
    
    prettyXml(root, '\t', '\n')  # 执行美化方法
    # if not os.path.exists(r'./result'):
    #     os.makedirs(r'./result')
    # output = os.path.join('result', file.split('\\')[-1].split('.')[0] + '_cut.net.xml')
    # output = os.path.join(r'./result',(file.split('\\')[-1].split('.')[0]).split('_')[0] + '_cut.net.xml')
    output = os.path.join('./output_'+ tag +'/osm.net.xml')
    new_tree.write(output, encoding='utf-8')
distanceThres=250
def get_edge_type(path):
    tree = ET.parse(path)
    root = tree.getroot()
    edgetype={}
    for edges in root.iter('edge'):
        if "id" in edges.attrib and "type" in edges.attrib:
            ty = str(edges.get("type"))
            if ty.split("_")[-1]=="link":#匝道1
                edgetype[str(edges.get("id"))]=1
            else:
                edgetype[str(edges.get("id"))] = 0
    return edgetype
def calDis(point1, point2):
    dis = math.sqrt((point1[0]-point2[0])**2+(point1[1]-point2[1])**2)
    return dis
def findNearestPoint(point, pointList):
    minDis = float('inf')
    minIndex = 0
    for i in range(len(pointList)):
        dis = calDis(point, pointList[i])
        if dis < minDis:
            minIndex = i
            minDis = dis

    return minIndex
def getAtan2(y, x):
    return math.atan2(y, x);
def vehDirection(endpoint, startpoint):
    x1 = endpoint[1]
    y1 = endpoint[0]
    x2 = startpoint[1]
    y2 = startpoint[0]

    radians = getAtan2((y1 - y2), (x1 - x2))

    compassReading = radians * (180 / math.pi)

    coordNames = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"];
    coordIndex = round(compassReading / 45);
    if (coordIndex < 0):
        coordIndex = coordIndex + 8
    return coordNames[coordIndex]
    # coordNames = ["N", "E",  "S",  "W", "N"];
    # coordIndex = round(compassReading / 90);
    # if (coordIndex < 0):
    #     coordIndex = coordIndex + 4
    # return coordNames[coordIndex]
def get_close_lane_position_noidName(net,data,lon,lat,direction,check_link,edgetype,i):
    data1 = pd.read_csv(r"./cache/dss_project_link.csv")
    non_driveway_id = []
    for ii in range(len(data1)):
        if data1["judgment"][ii] == "driveway":
            pass
        else:
            edge_id = str(data1["edge_id"][ii]).split("'")[1]
            non_driveway_id.append(edge_id)
    x = net.convertLonLat2XY(lon, lat)[0]
    y = net.convertLonLat2XY(lon, lat)[1]
    pointxy = (x, y)
    NeighboringEdge_list = net.getNeighboringEdges(x, y, distanceThres)
    NeighboringEdges_list = []
    for n in NeighboringEdge_list:
        xx = list(n)[0]
        xxx = str(xx).split('"')[1]
        if xxx in non_driveway_id:
            pass
        else:
            NeighboringEdges_list.append(n)
    if len(NeighboringEdges_list) == 0:
        pass
        # print("There is no neighboring edge for point (%s,%s)" % (lon, lat))
    else:
        # print("There are %s nerghboring edges for point (%s,%s)" %(str(len(NeighboringEdges_list)),lon,lat))
        NeighboringEdge = ""
        mindis = float("inf")
        # print(mindis)
        if direction == True:
            edgedire = data["passageWays"][i]["direction"]
            if check_link == True and data["passageWays"][i]["type"] != "":
                linktype = data["passageWays"][i]["type"]
            else:
                linktype = None
            for ne in NeighboringEdges_list:
                print(ne)
                try: 
                    etype = edgetype[str(ne[0].getID())]
                except:
                    pass
                shapeList = ne[0].getShape()
                matchpointIndex = findNearestPoint(pointxy, shapeList)
                if matchpointIndex == (len(shapeList) - 1):
                    dir = vehDirection(
                        net.convertXY2LonLat(shapeList[matchpointIndex][0], shapeList[matchpointIndex][1]),
                        net.convertXY2LonLat(shapeList[matchpointIndex - 1][0],
                                             shapeList[matchpointIndex - 1][1]))

                else:
                    dir = vehDirection(
                        net.convertXY2LonLat(shapeList[matchpointIndex + 1][0],
                                             shapeList[matchpointIndex + 1][1]),
                        net.convertXY2LonLat(shapeList[matchpointIndex][0], shapeList[matchpointIndex][1]))
                # eid = str(ne[0].getID())
                # print("Edge ID is:%s,type is:%s, direction is :%s" % (eid, str(edgetype[eid]),dir))
                if linktype == None:
                    if ne[1] < mindis and dir == edgedire:
                        mindis = ne[1]
                        NeighboringEdge = ne
                else:
                    if ne[1] < mindis and dir == edgedire and linktype == etype:
                        # print(linktype)
                        mindis = ne[1]
                        NeighboringEdge = ne

        else:
            if check_link == True and data["passageWays"][i]["direction"] != "":
                linktype = data["passageWays"][i]["direction"]
            else:
                linktype = None

            for ne in NeighboringEdges_list:
                etype = edgetype[str(ne[0].getID())]
                if linktype == None:
                    if ne[1] < mindis:
                        mindis = ne[1]
                        NeighboringEdge = ne
                else:
                    if ne[1] < mindis and linktype == etype:
                        mindis = ne[1]
                        NeighboringEdge = ne
        if NeighboringEdge != "":
            # print("neibourEgdeis for %s,%s, is: %s" % (lon, lat, str(NeighboringEdge[0].getID())))
            # print(NeighboringEdge)
            index, pos, dis = NeighboringEdge[0].getClosestLanePosDist((x, y))
            edge_len = NeighboringEdge[0].getLength()
            if pos >= edge_len and edge_len > 10:
                pos = edge_len - 10
            elif pos >= edge_len and edge_len <= 10:
                pos = edge_len * 0.8
            else:
                pass
            edge = []
            edge.append(NeighboringEdge[0].getID())
            edge.append(pos)
            return edge
        else:
            # print("There is no suitable neighboring edge for point (%s,%s)" % (lon, lat))
            return 0
# 下面部分是用于新建路网所用，在前面的对应函数下进行了一定修改；
def coodinate_listToString1(coodinate):
    '''
    :param coodinate: [(x,y),(x,y)...]
    :return:
    '''
    String=""
    length=len(coodinate)
    for i,(x,y) in enumerate(coodinate):
        String+="%.2f,%.2f"%(x,y)
        if i<length-1:
            String+=" "
    return String

def create_junction1(root,junction_id,junc_center,junction_poly):
    '''
    #--junction取最左点
    :param root:
    :param junction_id:
    junc_center:2*(x,y)
    :param junction_poly: 2*[(x,y),(x,y)..]
    :return:
    '''
    junc_dic=_JUNCTION_JSON_
    #--处理junction的shape
    junc_shape=[coodinate_listToString1(data) for data in junction_poly]

    node=root.findall('junction/..')[0]
    #--
    for i,id in enumerate(junction_id):
        # print(i,id)
        attrib=junc_dic.copy()
        x=junc_center[i]
        y=junc_center[i+1]
        
        # print("junction%s坐标：%f,%f"%(id,x,y))
        attrib['id']=id
        attrib['x']="%.2f"%x
        attrib['y']="%.2f"%y
        attrib['shape']=junc_shape[i]
        if None!=node:
            ET.SubElement(node,'junction',attrib)
        else:
            ET.SubElement(root, 'junction', attrib)
    return root

def built_node_edge(xmlfile,junction_id,junction_x,junction_y,edge_id,edge_from,edge_to,final_file):
    tree,root = readxml(xmlfile)
    # tree,root = readxml(r"F:\projects\DADUAN\result\osm_cut.net.xml")
    create_junction1(root,junction_id,(junction_x,junction_y),[[]])
    # print(root)
    junctions = root.findall(".//junction")
    edges = root.findall(".//edge")
    n = 0
    incLanes = ""#--junction的incLanes属性
    for edge in edges:
        try:
            # n = 0
            # edge.attrib["from"]
            for junction in junctions:
                # n = 0
                if junction.attrib["id"] == edge.attrib["from"] or junction.attrib["id"] == edge.attrib["to"]:
                    if junction.attrib["type"] == "dead_end" and edge.attrib["priority"]=='-1' and 'shape' not in edge.attrib.keys() and n == 0:
                        n = n + 1
                        newedge_dic = edge.attrib.copy()
                        newedge_dic["id"] = edge_id#id
                        newedge_dic["from"] = edge_from
                        newedge_dic["to"] = edge_to
        except:
            pass
    # 添加edge的lane属性；
    lane_dic = {'id':edge_id +"_%s"%0,'index':'0','speed':"13.89",'length':" ",'width':"3.20",'shape':" "}#%lane_dic['index']
    incLanes += edge_id+"_%s"%lane_dic['index']
    edge_ele = ET.Element('edge', newedge_dic)
    ET.SubElement(edge_ele,'lane',lane_dic)
    #--修改incLanes属性
    for junc_node in root.findall(".//junction[@id='%s']"%newedge_dic['to']):
        # data=junc_node.get('incLanes')
        junc_node.attrib["incLanes"] = str(junc_node.attrib["incLanes"]) + " " + str(incLanes)#.set('incLanes',incLanes[:len(incLanes)-1])
    # 这一步是将edge连接的junction指标补全；下一步是需要完成connection的指标，这部分只需要将点和link加上可以交给netconvert自己生成
    # 开始Connection的撰写
    root.append(edge_ele)
    new_tree = beautifulTree(root)
    prettyXml(root, '\t', '\n')
    new_tree.write(final_file, encoding='utf-8')


def new_link_wkt(file1,file2,file3):
    with open(file1, 'r', encoding="utf-8") as f:
        data = json.load(f)
    break_link_id = []
    for i in range(len(data["passageWays"])):
        link_id_1 = data["passageWays"][i]["linkId"]
        link_id = re.sub("'", "", link_id_1)
        break_link_id.append(link_id)
    # print(len(break_link_id))
    # print(break_link_id)
    new_link_id = []
    for i in range(len(break_link_id)):
        new_1 = break_link_id[i] + "_1"
        new_2 = break_link_id[i] + "_2"
        new_link_id.append(new_1)
        new_link_id.append(new_2)
    # print(new_link_id)

    net = sumolib.net.readNet(file2)
    nodes = net.getEdges()
    edge_id = [] #这里面edge没有重复
    node_from = []
    node_to = []
    for n in range(len(nodes)):
        str1 = str(nodes[n])
        # str1形如<edge id="gneE9" from="4462260503" to="cluster_gneJ28_gneJ29"/>
        t =re.findall(r'"(.+?)"',str1) #re.findall(r'正则表达式'，'要匹配的文本')
        # r'\"(.*)\"'的意图是匹配被双引号包含的文本，但是在正则表达式中*操作符是贪婪的，因此匹配操作会查找最长的可能匹配
        # print(t)
        edge_id.append(t[0])
        node_from.append(t[1])
        node_to.append(t[2])

    xy_from_lon = []
    xy_from_lat = []
    xy_from = []
    for e in range(len(node_from)):
        node_from_xy = net.getNode(node_from[e]).getCoord()
        lon,lat = net.convertXY2LonLat(node_from_xy[0],node_from_xy[1])
        xy_from_lon.append(lon)
        xy_from_lat.append(lat)
        xy_from.append((lon,lat))
    xy_to_lon = []
    xy_to_lat = []
    xy_to = []
    for ee in range(len(node_to)):
        node_to_xy = net.getNode(node_to[ee]).getCoord()
        # x = node1_xy[0]
        lon1,lat1 = net.convertXY2LonLat(node_to_xy[0],node_to_xy[1])
        xy_to_lon.append(lon1)
        xy_to_lat.append(lat1)
        xy_to.append((lon1,lat1))

    lane_id = []
    lane_shape = []
    Edge_id = [] #这个是与lane对应的edge_id，这个里面有重复
    Node_from = []
    Node_to = []
    Node_from_xy = []
    Node_to_xy = []
    for e in range(len(edge_id)):
        # node_from_xy = net.getNode(node_from[e]).getCoord()
        lane = net.getEdge(edge_id[e]).getLanes()
        for i in range(len(lane)):
            l_id = lane[i].getID()
            l_xy = lane[i].getShape()
            lane_id.append(l_id)
            lane_shape.append(l_xy)
            Edge_id.append(edge_id[e])
            Node_from.append(node_from[e])
            Node_to.append(node_to[e])
            Node_from_xy.append(xy_from[e])
            Node_to_xy.append(xy_to[e])
            # print(l_xy)
    # print(len(Edge_id))
    # print(len(lane_id))
    lane_shape_xy = []
    for i in range(len(lane_id)):
        l_xy = []
        for n in range(len(lane_shape[i])):
            lon1,lat1 = net.convertXY2LonLat(lane_shape[i][n][0],lane_shape[i][n][1])
            a = str(lon1) + " " + str(lat1)
            l_xy.append(a)
        # print(l_xy)
        lane_shape_xy.append(l_xy)
    lane_df = DataFrame({"edge_id":Edge_id, "lane_id":lane_id, "edge_node_from":Node_from,"edge_node_to":Node_to, "node_from_xy":Node_from_xy, "node_to_xy":Node_to_xy,"lane_xy":lane_shape_xy})
    # print(type(lane_shape[0][0]))
    # print(lane_shape[0][0][0])
    # print(lane_df)
    lane_flag = []
    for i in range(len(lane_id)):
        l_end = lane_id[i][-2:]
        if l_end == "_0":
            lane_flag.append(1)
        else:
            lane_flag.append(2)
    # print(len(lane_flag))
    lane_df["剔除情况"] = lane_flag
    lane2_df = lane_df[-lane_df.剔除情况.isin([2])]
    break_flag = []
    for i in range(len(edge_id)):
        if edge_id[i] in new_link_id:
            for n in range(len(new_link_id)):
                if edge_id[i] == new_link_id[n]:
                    break_flag.append("1")
        else:
            break_flag.append("2")
    net_df = DataFrame({"edge_id":edge_id, "wkt":lane2_df["lane_xy"], "flag":break_flag})
    #print(net_df)
    net2_df = net_df[-net_df.flag.isin(["2"])]
    #print(net2_df)
    # print(net2_df["wkt"])
    a = net2_df["wkt"].apply(lambda x :"MULTILINESTRING(("+ re.sub("[']",'',str(x)[1:-1])+ "))")
    net3_df = DataFrame({"edge_id":net2_df["edge_id"], "wkt":a})
    # prinft(net3_df)
    net3_df.to_csv(file3,index = False)


def IorO(data,edge1,i):
    # print(points.iloc[3] == 'I')
    if data["passageWays"][i]["type"] == 1:
        edge_from = edge1[0]+"_cut_junc1"
        edge_to = data["projectId"]
    if data["passageWays"][i]["type"] == 2:
        edge_from = data["projectId"]
        edge_to = edge1[0]+"_cut_junc1"
    # else:
    #     print("Errors occured")
    # print(edge_from)
    # print(edge_to)  
    return edge_from,edge_to

def edge2taz(tazfile,file,data):
    # start_point=data.iloc[0]
    node_list=[]
    node_id_list =[]
    for i in range(len(data["passageWays"])):
        lon = data["passageWays"][i]["point"][0]
        lat = data["passageWays"][i]["point"][1]
        node_id = data["passageWays"][i]["linkId"]
        node_id_list.append(node_id)
        node = (lon,lat)
        node_list.append(node)
    a = len(node_list)
    tree,root = readxml(tazfile)
    tazs = root.findall("taz")
    taz_list = []
    if a == 1:
        for taz in tazs:
            for tazsink in taz:
                if tazsink.attrib["id"] == node_id_list[0]:
                    taz_id1 = taz.attrib["id"]
                    taz_list.append(taz_id1)
                    return taz_list[0]
    elif a == 2:
        lon_mid = (node_list[0][0] + node_list[1][0]) /2
        lat_mid = (node_list[0][1] + node_list[1][1]) /2
        net = read_sumo_net(file)
        edgetype=get_edge_type(file)
            #现默认掉check_link
        edge1=get_close_lane_position_noidName(net,data,lon_mid,lat_mid,True,False,edgetype,i)
        for taz in tazs:
            for tazsink in taz:
                if tazsink.attrib["id"] == edge1[0]:
                    taz_id1 = taz.attrib["id"]
                    taz_list.append(taz_id1)
                    return taz_list[0]
    else:
        polygon_edge = Polygon(node_list)
        # print(polygon_edge)
        p1 = wkt.loads(str(polygon_edge))
        point = p1.centroid.wkt
        point_split = point.split(" ")
        # print(point_split)
        # lon1 = point_split[1][1:]
        # lat1 = point_split[2][0:-1]
        # print(lon1)
        lon1 = data["center"][0]
        lat1 = data["center"][1]
        net = read_sumo_net(file)
        edgetype=get_edge_type(file)
        #现默认掉check_link
        edge1=get_close_lane_position_noidName(net,data,lon1,lat1,True,False,edgetype,i)
        # print(edge1)
        for taz in tazs:
            for tazsink in taz:
                if tazsink.attrib["id"] == edge1[0]:
                    taz_id1 = taz.attrib["id"]
                    # print(taz_id1)
                    taz_list.append(taz_id1)
                    return taz_list[0]
    
    # return taz_id1       


def added_taz_id(file,tazfile,data,tazfile1,newfile):
    edge_id_source = []
    edge_id_sink = []
    for i in range(len(data["passageWays"])):
    # points=data1.iloc[0]
    # edge_id=points.iloc[4]
        lon = data["passageWays"][i]["point"][0]
        lat = data["passageWays"][i]["point"][1]
        net = read_sumo_net(file)
        edgetype=get_edge_type(file)
        edge1=get_close_lane_position_noidName(net,data,lon,lat,True,False,edgetype,i)
        new_built_node = edge1[0]+"_cut_junc1"
        tree,root = readxml(newfile)

        edges = root.findall("edge")
        door_type=data["passageWays"][i]["type"]
        if door_type == 3: #3———作为进出口；
            for edge in edges:
                try:
                    if edge.attrib["from"] == new_built_node:
                        edge_id_source.append(edge.attrib["id"])
                        # edge_id_source=edge.attrib["id"]
                    if edge.attrib["to"] == new_built_node:
                        edge_id_sink.append(edge.attrib["id"])
                        # edge_id_sink=edge.attrib["id"]

                except:
                    pass
        if door_type == 2: #2————作为出口；
            for edge in edges:
                try:
                    if edge.attrib["from"] == new_built_node:
                        edge_id_source.append(edge.attrib["id"])
                        # edge_id_source=edge.attrib["id"]
                    # if edge.attrib["to"] == new_built_node:
                        # edge_id_sink.append(edge.attrib["id"])
                        # edge_id_sink=edge.attrib["id"]

                except:
                    pass

        if door_type == 1: #1————作为进口；
            for edge in edges:
                try:
                    # if edge.attrib["from"] == new_built_node:
                        # edge_id_source.append(edge.attrib["id"])
                        # edge_id_source=edge.attrib["id"]
                    if edge.attrib["to"] == new_built_node:
                        edge_id_sink.append(edge.attrib["id"])
                        # edge_id_sink=edge.attrib["id"]

                except:
                    pass
    # print(edge_id_source)
    # print(edge_id_sink)

    tree,root = readxml(tazfile)
    tazs = root.findall("taz")
    # n = len(tazs)
    for taz in tazs:
        new_built_taz = str(int(taz.attrib["id"])+1)
    # print
    # for taz in tazs:
    taz_dic = {"id":new_built_taz}
    taz_ele = ET.Element("taz",taz_dic)
    for source in edge_id_source:
        tazSource_dic = {"id":source,"weight":str(100)}
        ET.SubElement(taz_ele,'tazSource',tazSource_dic)
    for sink in edge_id_sink:
        tazSink_dic = {"id":sink,"weight":str(100)}
        ET.SubElement(taz_ele,'tazSink',tazSink_dic)
    root.append(taz_ele)
    new_tree = beautifulTree(root)
    prettyXml(root, '\t', '\n')
    new_tree.write(tazfile1, encoding='utf-8')

    return new_built_taz 



# 到这里为止
        
# if __name__ == '__main__':
def new_built1(file,data,tag):#这边需要把函数的输入给列出来；

    net = read_sumo_net(file)
    edgetype=get_edge_type(file)
    for i in range(len(data["passageWays"])):
    # file="osm.net.xml"
    # data=pd.read_excel("fix1.xlsx")
    # 目前的输入两个点：id，lon，lat，dir，check_link
    # 需要打断的id，起终点，方向，是否在主路还是匝道0是主路，1是匝道
    # start_point=data.iloc[0]
    # 这边是cut的一遍流程，这一部分是可以重复完成的；
        lon = data["passageWays"][i]["point"][0]
        lat = data["passageWays"][i]["point"][1]
        edge_id = data["passageWays"][i]["linkId"]
        #现默认掉check_link
        edge1=get_close_lane_position_noidName(net,data,lon,lat,True,False,edgetype,i)
        # print(edge1,edge1[0])
        cut_edges(file, edge_id, edge1[1], 0, [''],tag)
        # print(i)

    file1 = './in/' + tag + '.json'
    file2 = r"./output_" + tag + "/osm.net.xml"
    file3 = r"./output/output_" + tag + "/break_link_wkt.csv"
    new_link_wkt(file1,file2,file3)    