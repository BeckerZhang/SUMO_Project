import xml.etree.ElementTree as ET
from pandas.core.frame import DataFrame
from collections import Counter
import json
import pandas as pd
import sumolib
from shapely.geometry import Polygon
from shapely import wkt
import re

def lonlat2taz(file,jsonfile):
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
    radius = 1500
    x, y = net.convertLonLat2XY(lon, lat)
    # print(x,y)
    edges = net.getNeighboringEdges(x, y, radius)
    # print(edges)
    # pick the closest edge
    trace_edge = []
    if len(edges) > 0:
        distancesAndEdges = sorted(edges, key=lambda x:x[1])
        for i in range(len(distancesAndEdges)):
            closestEdge,dist = distancesAndEdges[i]
            trace = re.findall(r'"(.+?)"',str(closestEdge))[0]
            trace_edge.append(trace)
    # print(str(closestEdge))
    # print(trace_edge)
    # print(len(trace_edge))
    return trace_edge


def cal_edge_lane(file1,file2, file3, file4, file5, jsonfile = './in/background.json', tag = 1):
    tree = ET.parse(file1)
    root = tree.getroot()  # 获取根节点
    nodes = root.findall("interval")
    edge_id = []
    edges_id = []  # edge有重复的情况，它的数量应该跟lane_id的数量一样
    lane_id = []
    departed = []
    arrived = []
    entered = []
    left = []
    laneChangedFrom = []
    laneChangedTo = []
    occupancy = []
    speed = []
    waiting_time = []
    time_loss = []
    lane_density = []
    if tag == 1:
        for node in nodes:
            for edge in node:
                e_id = edge.attrib['id']
                edge_id.append(e_id)
                for lane in edge:
                    try:
                        edges_id.append(e_id)
                        l_id = lane.attrib["id"]
                        l_dep = float(lane.attrib["departed"]) * 2 
                        l_arrived = float(lane.attrib["arrived"]) * 2
                        l_entered = float(lane.attrib["entered"]) * 2
                        l_left = float(lane.attrib["left"]) * 2
                        l_laneChangedFrom = float(lane.attrib["laneChangedFrom"]) * 2 
                        l_laneChangedTo = float(lane.attrib["laneChangedTo"]) * 2
                        lane_id.append(l_id)
                        departed.append(l_dep)
                        arrived.append(l_arrived)
                        entered.append(l_entered)
                        left.append(l_left)
                        laneChangedFrom.append(l_laneChangedFrom)
                        laneChangedTo.append(l_laneChangedTo)
                        l_occupancy = lane.attrib["occupancy"]
                        l_speed = lane.attrib["speed"]
                        l_wait = lane.attrib["waitingTime"]
                        l_loss = lane.attrib["timeLoss"]
                        l_lane_density = lane.attrib["laneDensity"]
                        occupancy.append(l_occupancy)
                        speed.append(l_speed)
                        waiting_time.append(l_wait)
                        time_loss.append(l_loss)
                        lane_density.append(l_lane_density)
                    except KeyError:
                        occupancy.append("0")
                        speed.append("0")
                        waiting_time.append("0")
                        time_loss.append("0")
                        lane_density.append("0")
        simulation_all_lane_df = DataFrame({"ID": lane_id, "arrived": arrived, "departed": departed, "entered": entered, "left": left, "lane_changed_from": laneChangedFrom, "lane_changed_to": laneChangedTo, "occupancy": occupancy, "speed": speed, "waiting_time": waiting_time, "time_loss": time_loss})
        # print(simulation_all_lane_df)
    if tag == 0:
        with open('in\limit_num.json', 'r', encoding="utf-8") as f:
            data = json.load(f)
            time = data["limitedTime"]
            if time == 103: #白天
                for node in nodes:
                    for edge in node:
                        e_id = edge.attrib['id']
                        edge_id.append(e_id)
                        for lane in edge:
                            try:
                                edges_id.append(e_id)
                                l_id = lane.attrib["id"]
                                l_dep = round(float(lane.attrib["departed"])*0.6 *2) 
                                l_arrived = round(float(lane.attrib["arrived"])*0.6*2)
                                l_entered = round(float(lane.attrib["entered"])*0.6*2)
                                l_left = round(float(lane.attrib["left"])*0.6*2)
                                l_laneChangedFrom = round(float(lane.attrib["laneChangedFrom"])*0.6*2)
                                l_laneChangedTo = round(float(lane.attrib["laneChangedTo"])*0.6*2)
                                lane_id.append(l_id)
                                departed.append(l_dep)
                                arrived.append(l_arrived)
                                entered.append(l_entered)
                                left.append(l_left)
                                laneChangedFrom.append(l_laneChangedFrom)
                                laneChangedTo.append(l_laneChangedTo)
                                l_occupancy = float(lane.attrib["occupancy"])*0.6
                                l_speed = float(lane.attrib["speed"])*1.2
                                l_wait = float(lane.attrib["waitingTime"])*0.9
                                l_loss = float(lane.attrib["timeLoss"])*0.9
                                l_lane_density = float(lane.attrib["laneDensity"])*0.6
                                occupancy.append(l_occupancy)
                                speed.append(l_speed)
                                waiting_time.append(l_wait)
                                time_loss.append(l_loss)
                                lane_density.append(l_lane_density)
                            except KeyError:
                                occupancy.append("0")
                                speed.append("0")
                                waiting_time.append("0")
                                time_loss.append("0")
                                lane_density.append("0")
                simulation_all_lane_df = DataFrame({"ID": lane_id, "arrived": arrived, "departed": departed, "entered": entered, "left": left, "lane_changed_from": laneChangedFrom, "lane_changed_to": laneChangedTo, "occupancy": occupancy, "speed": speed, "waiting_time": waiting_time, "time_loss": time_loss})
            if time == 104: #全天
                for node in nodes:
                    for edge in node:
                        e_id = edge.attrib['id']
                        edge_id.append(e_id)
                        for lane in edge:
                            try:
                                edges_id.append(e_id)
                                l_id = lane.attrib["id"]
                                l_dep = round(float(lane.attrib["departed"])*0.4*2)
                                l_arrived = round(float(lane.attrib["arrived"])*0.4*2)
                                l_entered = round(float(lane.attrib["entered"])*0.4*2)
                                l_left = round(float(lane.attrib["left"])*0.4*2)
                                l_laneChangedFrom = round(float(lane.attrib["laneChangedFrom"])*0.4*2)
                                l_laneChangedTo = round(float(lane.attrib["laneChangedTo"])*0.4*2)
                                lane_id.append(l_id)
                                departed.append(l_dep)
                                arrived.append(l_arrived)
                                entered.append(l_entered)
                                left.append(l_left)
                                laneChangedFrom.append(l_laneChangedFrom)
                                laneChangedTo.append(l_laneChangedTo)
                                l_occupancy = float(lane.attrib["occupancy"])*0.4
                                l_speed = float(lane.attrib["speed"])*1.4
                                l_wait = float(lane.attrib["waitingTime"])*0.8
                                l_loss = float(lane.attrib["timeLoss"])*0.8
                                l_lane_density = float(lane.attrib["laneDensity"])*0.4
                                occupancy.append(l_occupancy)
                                speed.append(l_speed)
                                waiting_time.append(l_wait)
                                time_loss.append(l_loss)
                                lane_density.append(l_lane_density)
                            except KeyError:
                                occupancy.append("0")
                                speed.append("0")
                                waiting_time.append("0")
                                time_loss.append("0")
                                lane_density.append("0")
                simulation_all_lane_df = DataFrame({"ID": lane_id, "arrived": arrived, "departed": departed, "entered": entered, "left": left, "lane_changed_from": laneChangedFrom, "lane_changed_to": laneChangedTo, "occupancy": occupancy, "speed": speed, "waiting_time": waiting_time, "time_loss": time_loss})
            else:
                for node in nodes:
                    for edge in node:
                        e_id = edge.attrib['id']
                        edge_id.append(e_id)
                        for lane in edge:
                            try:
                                edges_id.append(e_id)
                                l_id = lane.attrib["id"]
                                l_dep = lane.attrib["departed"]*2
                                l_arrived = lane.attrib["arrived"]*2
                                l_entered = lane.attrib["entered"]*2
                                l_left = lane.attrib["left"]*2
                                l_laneChangedFrom = lane.attrib["laneChangedFrom"]*2
                                l_laneChangedTo = lane.attrib["laneChangedTo"]*2
                                lane_id.append(l_id)
                                departed.append(l_dep)
                                arrived.append(l_arrived)
                                entered.append(l_entered)
                                left.append(l_left)
                                laneChangedFrom.append(l_laneChangedFrom)
                                laneChangedTo.append(l_laneChangedTo)
                                l_occupancy = lane.attrib["occupancy"]
                                l_speed = lane.attrib["speed"]
                                l_wait = lane.attrib["waitingTime"]
                                l_loss = lane.attrib["timeLoss"]
                                l_lane_density = lane.attrib["laneDensity"]
                                occupancy.append(l_occupancy)
                                speed.append(l_speed)
                                waiting_time.append(l_wait)
                                time_loss.append(l_loss)
                                lane_density.append(l_lane_density)
                            except KeyError:
                                occupancy.append("0")
                                speed.append("0")
                                waiting_time.append("0")
                                time_loss.append("0")
                                lane_density.append("0")
            simulation_all_lane_df = DataFrame({"ID": lane_id, "arrived": arrived, "departed": departed, "entered": entered, "left": left, "lane_changed_from": laneChangedFrom, "lane_changed_to": laneChangedTo, "occupancy": occupancy, "speed": speed, "waiting_time": waiting_time, "time_loss": time_loss})
    
    tree = ET.parse(file2)
    root = tree.getroot()
    edges = root.findall("edge")
    lane_allow = []
    lanes_id = []
    for e in range(len(edges)):
        for l in range(len(edges[e])):
            # print(edges[e][l])
            l_id = edges[e][l].get("id")
            # lanes_id.append(l_id)
            # print(l_id)
            if str(l_id).startswith(":"):
                continue
            elif l_id == None:
                continue
            else:
                if edges[e][l].get("allow"):
                    l_allow = edges[e][l].get("allow")
                    lane_allow.append(l_allow)
                    lanes_id.append(l_id)
                else:
                    l_allow = 1
                    # 用1表示是因为有的lane写了disallow，有的没有这个字段，如-gneE10_2/3/4，而人行道和自行车道一定有allow，所以把这些都归类于1
                    lane_allow.append(l_allow)
                    lanes_id.append(l_id)
    # print(len(lanes_id))
    # print(len(lane_allow))
    edges_id_veh = []  # 剔除自行车道和人行道后，edge有重复的情况，它的数量应该跟lane_id_veh的数量一样
    lane_id_veh = []
    departed_veh = []
    arrived_veh = []
    entered_veh = []
    left_veh = []
    laneChangedFrom_veh = []
    laneChangedTo_veh = []
    occupancy_veh = []
    speed_veh = []
    waiting_time_veh = []
    time_loss_veh = []
    lane_density_veh = []
    for i in range(len(lane_allow)):
        if lane_allow[i] == 1:
            edges_id_veh.append(edges_id[i])
            lane_id_veh.append(lane_id[i])
            departed_veh.append(departed[i])
            arrived_veh.append(arrived[i])
            entered_veh.append(entered[i])
            left_veh.append(left[i])
            laneChangedFrom_veh.append(laneChangedFrom[i])
            laneChangedTo_veh.append(laneChangedTo[i])
            occupancy_veh.append(occupancy[i])
            speed_veh.append(speed[i])
            waiting_time_veh.append(waiting_time[i])
            time_loss_veh.append(time_loss[i])
            lane_density_veh.append(lane_density[i])
    edges_net = pd.read_csv(file5,encoding='utf-8')
    df_edges_net = pd.DataFrame(edges_net)
    # print(df_edges_net)
    edges_net_id = []
    for i in range(len(df_edges_net["edge_id"])):
        if str(df_edges_net["edge_id"][i]).startswith("'"):
            id = df_edges_net["edge_id"][i][1:][:-1]
            edges_net_id.append(id)
        else:
            id = df_edges_net["edge_id"][i][:-1]
            edges_net_id.append(id)
    # print(len(edges_net_id))
    lanes_edges_type = []
    for i in range(len(edges_id_veh)):
        for e in range(len(edges_net_id)):
            if edges_id_veh[i] == edges_net_id[e]:
                lanes_edges_type.append(df_edges_net["道路等级"][e])
            else:
                continue
    # print(len(lanes_edges_type))
    # print(len(edges_id_veh))
    capacity = []
    # print(lanes_edges_type)
    for i in range(len(edges_id_veh)):
        if lanes_edges_type[i] == "主干路":
            capacity.append(2000)
        elif lanes_edges_type[i] == "次干路":
            capacity.append(1600)
        elif lanes_edges_type[i] == "支路":
            capacity.append(1000)
        else:
            capacity.append(600)
    # print(len(capacity))
    # print(capacity)
    '''还要计算一个交通量，Q = speed*3.6*density'''
    ave_traffic_volume = []
    for i in range(len(lane_id_veh)):
        q = round(float(speed_veh[i]) * 3.6 * float(lane_density_veh[i]) * 2)
        ave_traffic_volume.append(q)
    # print(ave_traffic_volume)
    vol_to_cap = []
    for i in range(len(lane_id_veh)):
        v_c = (ave_traffic_volume[i]) / (capacity[i])
        vol_to_cap.append(v_c)
    # print(len(vol_to_cap))
    # print(vol_to_cap)
    ser_level = []
    for i in range(len(lane_id_veh)):
        if vol_to_cap[i] <= 0.35:
            ser_level.append("一级")
        elif 0.35 < vol_to_cap[i] <= 0.55:
            ser_level.append("二级")
        elif 0.55 < vol_to_cap[i] <= 0.75:
            ser_level.append("三级")
        elif 0.75 < vol_to_cap[i] <= 0.90:
            ser_level.append("四级")
        elif 0.90 < vol_to_cap[i] <= 1.00:
            ser_level.append("五级")
        else:
            ser_level.append("六级")
    # print(len(ser_level))
    # print(ser_level)
    for i in range(len(lane_id_veh)):
        if ave_traffic_volume[i] == 0:
            waiting_time_veh[i] = 0
            time_loss_veh[i] = 0
        else:
            waiting_time_veh[i] = float(waiting_time_veh[i]) / float(ave_traffic_volume[i])
            time_loss_veh[i] = float(time_loss_veh[i]) / float(ave_traffic_volume[i])
    '''这里可以output出lane能够提供的指标了'''
    '''这里是剔除自行车道和人行道的lane数据'''
    simulation_veh_lane_df = DataFrame({"ID": lane_id_veh, "flow": ave_traffic_volume, "voc": vol_to_cap,"service_level": ser_level, "arrived": arrived_veh, "departed": departed_veh, "entered": entered_veh, "left": left_veh,"lane_changed_from": laneChangedFrom_veh, "lane_changed_to": laneChangedTo_veh, "occupancy": occupancy_veh, "speed": speed_veh, "waiting_time": waiting_time_veh, "time_loss": time_loss_veh})
    # print(simulation_veh_lane_df)
    simulation_veh_lane_df.to_csv(file3)
    edge_nums = Counter(edges_id_veh)
    # print(type(edge_nums)) #<class 'collections.Counter'>
    dic_e_nums = dict(edge_nums)
    # print(edge_nums)
    # print(dic_e_nums)
    lane_numbers_veh = []
    for key, value in dic_e_nums.items():
        lane_numbers_veh.append(value)
    '''先将相同edge_id下的各指标求和'''
    edges_veh_tag = []
    for i in range(len(edges_id_veh)):
        try:
            if edges_id_veh[i] == edges_id_veh[i + 1]:
                departed_veh[i + 1] = int(departed_veh[i + 1]) + int(departed_veh[i])
                arrived_veh[i + 1] = str(int(arrived_veh[i + 1]) + int(arrived_veh[i]))
                entered_veh[i + 1] = int(entered_veh[i + 1]) + int(entered_veh[i])
                left_veh[i + 1] = int(left_veh[i + 1]) + int(left_veh[i])
                laneChangedFrom_veh[i + 1] = int(laneChangedFrom_veh[i + 1]) + int(laneChangedFrom_veh[i])
                laneChangedTo_veh[i + 1] = int(laneChangedTo_veh[i + 1]) + int(laneChangedTo_veh[i])
                occupancy_veh[i + 1] = float(occupancy_veh[i + 1]) + float(occupancy_veh[i])
                speed_veh[i + 1] = float(speed_veh[i + 1]) + float(speed_veh[i])
                waiting_time_veh[i + 1] = float(waiting_time_veh[i + 1]) + float(waiting_time_veh[i])
                time_loss_veh[i + 1] = float(time_loss_veh[i + 1]) + float(time_loss_veh[i])
                lane_density_veh[i + 1] = float(lane_density_veh[i + 1]) + float(lane_density_veh[i])
                ave_traffic_volume[i + 1] = float(ave_traffic_volume[i + 1]) + float(ave_traffic_volume[i])
                capacity[i + 1] = float(capacity[i + 1]) + float(capacity[i])
                vol_to_cap[i + 1] = float(vol_to_cap[i + 1]) + float(vol_to_cap[i])
                edges_veh_tag.append("1")
            else:
                edges_veh_tag.append("2")
        except IndexError:
            edges_veh_tag.append("2")
    # print(len(edges_veh_tag))
    for i in range(len(edges_veh_tag)):
        if edges_veh_tag[i] == "2":
            a = int(dic_e_nums[edges_id_veh[i]])
            occupancy_veh[i] = float(occupancy_veh[i]) / a
            speed_veh[i] = float(speed_veh[i]) / a
            lane_density_veh[i] = float(lane_density_veh[i]) / a
            vol_to_cap[i] = float(vol_to_cap[i]) / a
        else:
            continue
    # print(len(occupancy_veh))
    edges_id_veh_fin = []
    lane_id_veh_fin = []
    departed_veh_fin = []
    arrived_veh_fin = []
    entered_veh_fin = []
    left_veh_fin = []
    laneChangedFrom_veh_fin = []
    laneChangedTo_veh_fin = []
    occupancy_veh_fin = []
    speed_veh_fin = []
    waiting_time_veh_fin = []
    time_loss_veh_fin = []
    lane_density_veh_fin = []
    ave_traffic_volume_fin = []
    capacity_fin = []
    vol_to_cap_fin = []
    for i in range(len(edges_veh_tag)):
        if edges_veh_tag[i] == "2":
            edges_id_veh_fin.append(edges_id_veh[i])
            lane_id_veh_fin.append(lane_id_veh[i])
            departed_veh_fin.append(departed_veh[i])
            arrived_veh_fin.append(arrived_veh[i])
            entered_veh_fin.append(entered_veh[i])
            left_veh_fin.append(left_veh[i])
            laneChangedFrom_veh_fin.append(laneChangedFrom_veh[i])
            laneChangedTo_veh_fin.append(laneChangedTo_veh[i])
            occupancy_veh_fin.append(occupancy_veh[i])
            speed_veh_fin.append(speed_veh[i])
            waiting_time_veh_fin.append(waiting_time_veh[i])
            time_loss_veh_fin.append(time_loss_veh[i])
            lane_density_veh_fin.append(lane_density_veh[i])
            ave_traffic_volume_fin.append(ave_traffic_volume[i])
            capacity_fin.append(capacity[i])
            vol_to_cap_fin.append(vol_to_cap[i])
        else:
            continue
    # 服务水平
    ser_level_edge = []
    for i in range(len(edges_id_veh_fin)):
        if vol_to_cap_fin[i] <= 0.35:
            ser_level_edge.append("一级")
        elif 0.35 < vol_to_cap_fin[i] <= 0.55:
            ser_level_edge.append("二级")
        elif 0.55 < vol_to_cap_fin[i] <= 0.75:
            ser_level_edge.append("三级")
        elif 0.75 < vol_to_cap_fin[i] <= 0.90:
            ser_level_edge.append("四级")
        elif 0.90 < vol_to_cap_fin[i] <= 1.00:
            ser_level_edge.append("五级")
        else:
            ser_level_edge.append("六级")
    # print(len(ser_level_edge))
    # print(ser_level_edge)
    if jsonfile == './in/background.json':
        simulation_veh_link_df = DataFrame({"ID": edges_id_veh_fin, "flow": ave_traffic_volume_fin, "voc": vol_to_cap_fin, "service_level": ser_level_edge, "arrived": arrived_veh_fin, "departed": departed_veh_fin, "entered": entered_veh_fin, "left": left_veh_fin, "lane_changed_from": laneChangedFrom_veh_fin, "lane_changed_to": laneChangedTo_veh_fin, "occupancy": occupancy_veh_fin, "speed": speed_veh_fin, "waiting_time": waiting_time_veh_fin, "time_loss": time_loss_veh_fin})
        # print(simulation_veh_link_df)
        simulation_veh_link_df.to_csv(file4)
    else:
        trace_edge = lonlat2taz(file2,jsonfile)
        is_range = []
        for i in range(len(edges_id_veh_fin)):
            if str(edges_id_veh_fin[i]) in list(trace_edge):
                is_range.append(1)
            else:
                is_range.append(0)
        '''这里可以output出dege能够包含的指标了'''
        simulation_veh_link_df = DataFrame({"ID": edges_id_veh_fin, "flow": ave_traffic_volume_fin, "voc": vol_to_cap_fin, "service_level": ser_level_edge, "arrived": arrived_veh_fin, "departed": departed_veh_fin, "entered": entered_veh_fin, "left": left_veh_fin, "lane_changed_from": laneChangedFrom_veh_fin, "lane_changed_to": laneChangedTo_veh_fin, "occupancy": occupancy_veh_fin, "speed": speed_veh_fin, "waiting_time": waiting_time_veh_fin, "time_loss": time_loss_veh_fin, "is_range":is_range})
        # print(simulation_veh_link_df)
        simulation_veh_link_df.to_csv(file4)

# file1 = r'output.lanedata.xml'
# file2 = r'osm.net.xml'
# file3 = r'simulation_veh_lane_background.csv'
# file4 = r'simulation_veh_link_background.csv'
# file5 = r'C:\Users\Yongqi Zhang\Desktop\weight\0720\tw_rdc_case\cache\dss_project_link.csv'
# file6 = r'C:\Users\Yongqi Zhang\Desktop\suzhou\output_background\output.lanedata.xml'
# file7 = r'C:\Users\Yongqi Zhang\Desktop\suzhou\output_background\osm.net.xml'
# file8 = r'C:\Users\Yongqi Zhang\Desktop\suzhou\output_background\simulation_veh_lane_new.csv'
# file9 = r'C:\Users\Yongqi Zhang\Desktop\suzhou\output_background\simulation_veh_link_new.csv'
# # cal_edge_lane(file1,file2,file3,file4,file5)
# cal_edge_lane(file6,file7,file8,file9,file5)