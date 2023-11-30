import json
import xml.etree.ElementTree as ET
import sumolib
from shapely .geometry import Polygon
from shapely import wkt
import re
import pandas as pd


def readxml(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    return tree,root

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
    radius = 250
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
    return trace_edge


def fcd_extract(file1,file2,file3,file4,jsonfile,output):
    doc = ET.iterparse(file1, ("start", "end"))
    net = sumolib.net.readNet(file2)
    wf = open(file3, "w", encoding = "utf-8")
    wf2 = open(file4, "w", encoding="utf-8")
    wf.write("timestep,carid,cartype,lon,lat,lane,angle,speed\n")
    wf2.write("timestep,carid,cartype,lon,lat,lane,angle,speed\n")
    wf.flush()
    start_flg = False;
    timestep = None
    for event, elem in doc:
        if event == "start":
            if elem.tag == "timestep":
                start_flg = True
                timestep = elem.attrib["time"]
            if elem.tag == "vehicle" and start_flg:
                v_id = elem.attrib["id"]
                v_type = elem.attrib["type"]
                x = elem.attrib["x"]
                y = elem.attrib["y"]
                lane = elem.attrib["lane"]
                angle = elem.attrib["angle"]
                speed = elem.attrib["speed"]
                lon,lat = net.convertXY2LonLat(float(x), float(y))
                if v_type == "pt_subway":
                    wf2.write(f"{timestep},{v_id},{v_type},{lon},{lat},{lane},{angle},{speed}\n")
                    wf2.flush()
                else:
                    wf.write(f"{timestep},{v_id},{v_type},{lon},{lat},{lane},{angle},{speed}\n")
                    wf.flush()
        if event == "end":
            if elem.tag == "timestep":
                start_flg = False
            elem.clear()
    wf.close()
    wf2.close()

    data = pd.read_csv(file3)
    df_data = pd.DataFrame(data)
    chosen_flag = []
    trace_edge = lonlat2taz(file2,jsonfile)
    for i in range(len(df_data["lane"])):
        if str(df_data["lane"][i][:-2]) in list(trace_edge):
            chosen_flag.append("1")
        else:
            chosen_flag.append("2")
    df_data["flag"] = chosen_flag
    # print(df_data)
    # df_data.to_csv("new_test.csv")
    df2_data = df_data[-df_data.flag.isin(["2"])]
    df2_data = df2_data.drop(axis =1,columns=["flag"],inplace=False)
    df2_data.to_csv(output, index=None)

# file1 = "output.fcd.xml"
# file2 = "osm.net.xml"
# file3 = "fcd.csv"
# jsonfile = "in.json"
# output = "fcd_in_range.csv"
# fcd_extract(file1,file2,file3,jsonfile,output)