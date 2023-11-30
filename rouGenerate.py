from mapTrace import mapTrace
import subprocess
import os, time
import xml.etree.ElementTree as ET
import pandas as pd


def add_net(formor_path,net_path):
    tree = ET.parse(formor_path)
    tree.write(net_path)

def add_csv(formor_path,net_path):
    data = pd.read_csv(formor_path)
    data.to_csv(net_path)

def netconvert_net(formor_path,net_path):
    proc = subprocess.Popen(
            r"netconvert -s " + formor_path + "-o " + net_path + " --plain.extend-edge-shape --ignore-errors",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=None,
            bufsize=-1,
        )
    proc.wait()

def rouGenerate(outputpath = '../tw_rdc_case/output_background', tag = 'background'):

    # print(r'---Start to generate subway.rou.xml---')
    add_net(formor_path = "./cache/subway.rou.xml", net_path = outputpath + '/subway.rou.xml')
    add_net(formor_path="./cache/newsubwayStops.xml", net_path=outputpath + '/newsubwayStops.xml')
    add_csv(formor_path="./cache/交叉口出口道方位.csv", net_path=outputpath + '/交叉口出口道方位.csv')
    add_csv(formor_path="./cache/交叉口进口道方位.csv", net_path=outputpath + '/交叉口进口道方位.csv')
    add_net(formor_path="./cache/meandata.xml", net_path=outputpath + '/meandata.xml')
    add_net(formor_path="./cache/meandata_5min.xml", net_path=outputpath + '/meandata_5min.xml')
    # print(r'---osm.net.xml is prepared for SUMO---')

    if (tag != 'output_new_built') and (tag != 'output_refresh') and (tag != 'output_parking_new'):
        # print(r'---Start to generate osm.net.xml---')
        add_net(formor_path = "./cache/osm.net.xml", net_path = outputpath + '/osm.net.xml')
        # print(r'---osm.net.xml is prepared for SUMO---')

#-------------------------------------------------------------------------------------------------------------#

    if (tag == 'background') or (tag == 'output_new_built') or (tag == 'output_refresh') or (tag == 'output_parking_new'):
        # print(r'---Start to generate busxml for SUMO---')
        busxml = mapTrace(net_path=outputpath + '/osm.net.xml',
                          bus_stop_path='../tw_rdc_case/cache/all_stops_wgs84.csv', \
                          outputpath=outputpath, vType='bus', bus_stop_search_radius=10, bus_stop_length=20,
                          stop_duration=20,
                          merge_threshold=20)
        # print(r'---busxml is prepared---')

        # print(r'---Start to generate bus.rou.xml---')
        proc = subprocess.Popen(
            r'polyconvert --net-file ' + outputpath + '/osm.net.xml --osm-files ./cache/map.osm --type-file ./cache/polytype.xml -o ' + outputpath + '/suzhou.poly.xml')
        proc.wait()
        proc = subprocess.Popen(
            r'python ../ptlines2flows.py -n ' + outputpath + '/osm.net.xml -s ' + outputpath + '/busStops.xml\
                 -l ../tw_rdc_case/cache/busLines.xml -o ' + outputpath + '/bus.rou.xml\
                  -p 600 -b 0 -e 3600 --min-stops 0')
        proc.wait()
        # fixed完的文件需要添加到output的文件中，可以代替osm文件做cfg的net.xml
        # print(r'---bus.rou.xml is prepared for SUMO---')

        # print(r'---Start to generate pedestrian.rou.xml---')
        # 行人生成这个地方，切记将cmd命令写成一行，别分行写；这一步对格式非常敏感，如果分行写，可能引入空格。
        proc = subprocess.Popen(
            r'python ../randomTrips.py -n ' + outputpath + '/osm.net.xml -o ../tw_rdc_case/cache/' + tag + '_pedestrian.trips.xml --fringe-factor 4 --seed 42 -e 3600 -p 5 --vehicle-class pedestrian --persontrips  --additional-files ' + outputpath + '/busStops.xml,' + outputpath + '/newsubwayStops.xml,' + outputpath + '/bus.rou.xml,' + outputpath + '/subway.rou.xml ' + '--trip-attributes "modes=\'public\'"')
        proc.wait()
        proc = subprocess.Popen(
            r'duarouter -n ' + outputpath + '/osm.net.xml -r ../tw_rdc_case/cache/' + tag + '_pedestrian.trips.xml --ignore-errors --begin 0 --end 3600 --no-step-log --additional-files ' + outputpath + '/busStops.xml,' + outputpath + '/newsubwayStops.xml,' + outputpath + '/bus.rou.xml,' + outputpath + '/subway.rou.xml ' + '--no-warnings -o ' + outputpath + '/pedestrian.rou.xml')
        proc.wait()
        # print(r'---pedestrian.rou.xml is prepared for SUMO---')

        # print(r'---Start to generate bike.rou.xml---')
        proc = subprocess.Popen(
            r'python ../randomTrips.py -n ' + outputpath + '/osm.net.xml -o ./cache/' + tag + '_bike.trip.xml --vclass bicycle')
        proc.wait()
        proc = subprocess.Popen(
            r'duarouter -n ' + outputpath + '/osm.net.xml -r ./cache/' + tag + '_bike.trip.xml -o ' + outputpath + '/bike.rou.xml --ignore-errors --seed 42')
        proc.wait()
        # print(r'---bike.rou.xml is prepared for SUMO---')

        if tag == 'output_refresh':
            # print(r'---Start to generate od.rou.xml---')
            proc = subprocess.Popen(
                r'od2trips -n ./cache/od.taz.xml --od-amitran-files ./output_refresh/combine.xml -o ./output_refresh/od.trip.xml --departpos free --ignore-errors')
            proc.wait()
            proc = subprocess.Popen(
                r'duarouter -n ' + outputpath + '/osm.net.xml -r ./output_refresh/od.trip.xml -o ' + outputpath + '/od.rou.xml -w ../tw_rdc_case/cache/weight.add.xml --seed 42 --ignore-errors')
            proc.wait()
            # print(r'---od.rou.xml is prepared for SUMO---')
        else:
            # print(r'---Start to generate od.rou.xml---')
            proc = subprocess.Popen(
                r'od2trips -n ./cache/od.taz.xml --od-amitran-files ./cache/od.xml -o ./cache/od.trip.xml --departpos free')
            proc.wait()
            proc = subprocess.Popen(
                r'duarouter -n ' + outputpath + '/osm.net.xml -r ../tw_rdc_case/cache/od.trip.xml -o ' + outputpath + '/od.rou.xml -w ../tw_rdc_case/cache/weight.add.xml --seed 42 --ignore-errors')
            proc.wait()
            # print(r'---od.rou.xml is prepared for SUMO---')


    if (tag == 'output_limit_num') or (tag == 'bus_discount')\
            or (tag == 'output_transit_flow') or (tag == 'parking_charge'):
        add_net(formor_path='../tw_rdc_case/output_background/bus.rou.xml',\
                net_path=outputpath + '/bus.rou.xml')
        add_net(formor_path='../tw_rdc_case/output_background/pedestrian.rou.xml',\
                net_path=outputpath + '/pedestrian.rou.xml')
        add_net(formor_path='../tw_rdc_case/output_background/busStops.xml',\
                net_path=outputpath + '/busStops.xml')
        add_net(formor_path='../tw_rdc_case/output_background/suzhou.poly.xml',\
                net_path=outputpath + '/suzhou.poly.xml')

        # print(r'---Start to generate od.rou.xml---')
        proc = subprocess.Popen(
            r'od2trips -n ./cache/od.taz.xml --od-amitran-files ' + outputpath + '/od.xml -o ' + outputpath + '/od.trip.xml --ignore-errors')
        proc.wait()
        proc = subprocess.Popen(
            r'duarouter -n ' + outputpath + '/osm.net.xml -r ' + outputpath + '/od.trip.xml -w ../tw_rdc_case/cache/weight.add.xml -o ' + outputpath + '/od.rou.xml --seed 42 --ignore-errors')
        proc.wait()
        # print(r'---od.rou.xml is prepared for SUMO---')

    return "Done"