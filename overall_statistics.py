import xml.etree.ElementTree as ET
import csv
import json
import os
import pandas as pd

def overall_statistics(path1 = r'./output_bus_discount', path2 = r'./output/output_bus_discount', path3=1):

    xml_file = open(path1 + '/output.statistic.xml',encoding='gbk')
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data_veh = root.findall("vehicles")
    data_trip = root.findall("vehicleTripStatistics")
    f = open(path2 + "/overall_statistics.csv", 'w', encoding = 'utf-8', newline= '')
    csv_writer = csv.writer(f)
    csv_writer.writerow(["car_trip", "speed", "congestion_mileage_ratio", "delay_time"])
    if path3 == 1:
        for i in range(len(data_veh)):
            vehs = float(data_veh[i].attrib["inserted"]) * 2
            speed = data_trip[i].attrib["speed"]
            delay = data_trip[i].attrib["timeLoss"]
            duration = data_trip[i].attrib["duration"]
            ratio = float(delay) / float(duration)
            csv_writer.writerow([vehs, speed, ratio, delay])
    if path3 == 0:
        with open('in\limit_num.json', 'r', encoding="utf-8") as f:
            data = json.load(f)
            time = data["limitedTime"]
            if time == 103: #白天
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 0.6 * 2
                    speed = float(data_trip[i].attrib["speed"]) * 1.2
                    delay = float(data_trip[i].attrib["timeLoss"]) * 0.9
                    duration = float(data_trip[i].attrib["duration"]) * 0.91
                    ratio = float(delay) / float(duration)
                    csv_writer.writerow([vehs, speed, ratio, delay])
            if time == 104: #全天
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 0.4 * 2
                    speed = float(data_trip[i].attrib["speed"]) * 1.4
                    delay = float(data_trip[i].attrib["timeLoss"]) * 0.8 
                    duration = float(data_trip[i].attrib["duration"]) * 0.82
                    ratio = float(delay) / float(duration)
                    csv_writer.writerow([vehs, speed, ratio, delay])
            else:
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 2
                    speed = data_trip[i].attrib["speed"]
                    delay = data_trip[i].attrib["timeLoss"]
                    duration = data_trip[i].attrib["duration"]
                    ratio = float(delay) / float(duration)
                    csv_writer.writerow([vehs, speed, ratio, delay])
    f.close()

    try:
        data_road = pd.read_csv(path2 + '/路网指标.csv')
        data_overall = pd.read_csv(path2 + '/overall_statistics.csv')
        if data_road.iloc[-1, 0] == 'car_trip':
                    for i in range(len(data_road)-1):
                        data_overall[data_road.iloc[i, 0]] = data_road.iloc[i, 1]
                    data_overall['car_trip'] = data_road.iloc[-1, 1]
        else:
            for i in range(len(data_road)):
                data_overall[data_road.iloc[i, 0]] = data_road.iloc[i, 1]
        data_overall.to_csv(path2 + "/overall_statistics.csv", index = False)
        os.remove(path2 + '/路网指标.csv')
    except:
        pass



def overall_statistics1(path1 = r'./output_bus_discount', path2 = r'./output/output_bus_discount', path3=1):

    xml_file = open(path1 + '/output.statistic.xml',encoding='gbk')
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data_veh = root.findall("vehicles")
    data_trip = root.findall("vehicleTripStatistics")
    f = open(path2 + "/overall_statistics1.csv", 'w', encoding = 'utf-8', newline= '')
    csv_writer = csv.writer(f)
    csv_writer.writerow(["vehicleKm","speed"])
    if path3 == 1:
        for i in range(len(data_veh)):
            vehs = float(data_veh[i].attrib["inserted"]) * 2
            speed = data_trip[i].attrib["speed"]
            delay = data_trip[i].attrib["timeLoss"]
            duration = data_trip[i].attrib["duration"]
            ratio = float(delay) / float(duration)
            routeLength = data_trip[i].attrib["routeLength"]
            vehicleKm = float(routeLength) * float(vehs)/ 1000
            csv_writer.writerow([vehicleKm, speed])
    if path3 == 0:
        with open('in\limit_num.json', 'r', encoding="utf-8") as f:
            data = json.load(f)
            time = data["limitedTime"]
            if time == 103: #白天
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 0.6 * 2
                    speed = float(data_trip[i].attrib["speed"]) * 1.2
                    delay = float(data_trip[i].attrib["timeLoss"]) * 0.9
                    duration = float(data_trip[i].attrib["duration"]) * 0.91
                    ratio = float(delay) / float(duration)
                    routeLength = data_trip[i].attrib["routeLength"]
                    vehicleKm = float(routeLength) * float(vehs)/ 1000
                    csv_writer.writerow([vehicleKm, speed])
            if time == 104: #全天
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 0.4 * 2
                    speed = float(data_trip[i].attrib["speed"]) * 1.4
                    delay = float(data_trip[i].attrib["timeLoss"]) * 0.8 
                    duration = float(data_trip[i].attrib["duration"]) * 0.82
                    ratio = float(delay) / float(duration)
                    routeLength = data_trip[i].attrib["routeLength"]
                    vehicleKm = float(routeLength) * float(vehs)/ 1000
                    csv_writer.writerow([vehicleKm, speed])
            else:
                for i in range(len(data_veh)):
                    vehs = float(data_veh[i].attrib["inserted"]) * 2
                    speed = data_trip[i].attrib["speed"]
                    delay = data_trip[i].attrib["timeLoss"]
                    duration = data_trip[i].attrib["duration"]
                    ratio = float(delay) / float(duration)
                    routeLength = data_trip[i].attrib["routeLength"]
                    vehicleKm = float(routeLength) * float(vehs)/ 1000
                    csv_writer.writerow([vehicleKm, speed])

def overall_statistics2(path1 = r'./output_bus_discount', path2 = r'./output/output_bus_discount', path3=2):
    xml_file = open(path1 + '/output.statistic.xml',encoding='gbk')
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data_veh = root.findall("vehicles")
    data_trip = root.findall("vehicleTripStatistics")
    f = open(path2 + "/overall_statistics.csv", 'w', encoding = 'utf-8', newline= '')
    csv_writer = csv.writer(f)
    csv_writer.writerow(["vehicleKm","vehicleKmChange","speed","speedChange"])
    if path3 == 2:
        file = pd.read_csv(r"./output/output_background/overall_statistics1.csv")
        df = pd.DataFrame(file)
        vehicleKm_now = float(df["vehicleKm"].loc[0])
        speed_now = float(df["speed"].loc[0])
        for i in range(len(data_veh)):
            vehs = float(data_veh[i].attrib["inserted"]) * 2
            speed = float(data_trip[i].attrib["speed"])
            delay = data_trip[i].attrib["timeLoss"]
            duration = data_trip[i].attrib["duration"]
            ratio = float(delay) / float(duration)
            routeLength = data_trip[i].attrib["routeLength"]
            vehicleKm = float(routeLength) * float(vehs) / 1000 #单位km
            vehicleKmChange = (vehicleKm_now - vehicleKm) / (vehicleKm) 
            speedChange = (speed_now - speed) / (speed)
            # print(speed,speed_now)
            csv_writer.writerow([vehicleKm,vehicleKmChange,speed,speedChange])

    f.close()
    try:
        data_road = pd.read_csv(path2 + '/路网指标.csv')
        data_overall = pd.read_csv(path2 + '/overall_statistics.csv')
        if data_road.iloc[-1, 0] == 'car_trip':
                    for i in range(len(data_road)-1):
                        data_overall[data_road.iloc[i, 0]] = data_road.iloc[i, 1]
                    data_overall['car_trip'] = data_road.iloc[-1, 1]
        else:
            for i in range(len(data_road)):
                data_overall[data_road.iloc[i, 0]] = data_road.iloc[i, 1]
        data_overall.to_csv(path2 + "/overall_statistics.csv", index = False)
        os.remove(path2 + '/路网指标.csv')
    except:
        pass