 # -*- coding: UTF-8 -*- 
import os, sys, time
import subprocess
import json
import xml.etree.ElementTree as ET
from cfgGenerate import cfgGenerate
from rouGenerate import rouGenerate
import mapRepair
from edge_lane_cal import cal_edge_lane
from limitnum import writing_xml, xianxing
import bus_discount
import transit_flow
import parkingdemand_function
import refresh
from overall_statistics import overall_statistics,overall_statistics2,overall_statistics1
from combine_link import combine_link1
from update_odxml import update_odxml

# set SUMO environment
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

def read_xml(ifn):
    tree = ET.parse(ifn)
    return tree

def write_xml(tree, ofn):
    tree.write(ofn, encoding="utf-8")

def get_os_type(info):
    if 'nt' == info:
        info = r'Windows'
    if 'posix' == info:
        info = r'Linux'
    return info

# 获取当前工作目录
def get_cwd():
    _my_cwd_ = os.path.split(os.path.realpath(__file__))[0] + '/tw_rdc_case'

    # print('argv:',len(sys.argv))
    for d in sys.argv:
        # print('argv:', d, os.path.isdir(d), os.path.isfile(d))
        if os.path.isdir(d):
            _my_cwd_ = d

    return _my_cwd_

def check_config(configFile):
    if os.path.isfile(configFile):
        result = r'check config file done.'
    else:
        result = r'check config file is not exist!'
    return result

# 设置运行环境
def set_environment(_os_type_, _my_cwd_):

    # set OS environment
    # print('SUMO_env:',os.environ['SUMO_HOME'])
    # print('sys_path:',sys.path)
    # print('ostype:',_os_type_)
    # print('oscwd:',os.getcwd())
    # print('mycwd:',_my_cwd_)

    os.chdir(_my_cwd_)
    # print('Change current working directory to',os.getcwd())

# 创建相关目录
def make_dir(_my_cwd_):
    dir_list = ['/output', '/output/output_background', '/output/output_new_built','/output/output_parking_new', '/output/output_limit_num',\
                '/output/output_bus_discount', '/output/output_transit_flow', '/output/output_parking_charge', \
                '/output_background', '/output_new_built', '/output_limit_num', '/output_bus_discount',\
                '/output_transit_flow', '/output_parking_charge', '/output_parking_new','/cache', '/output/output_refresh', '/output_refresh']
    for dir in dir_list:
        if not os.path.exists(_my_cwd_ + dir):
            os.makedirs(_my_cwd_ + dir)
            print('make dir', _my_cwd_ + dir)
    return


class AutoSim:

    def __init__(self, _my_cwd_):
        self._os_type_ = get_os_type(os.name)
        set_environment(self._os_type_, _my_cwd_)
        self._my_cwd_ = os.getcwd()

        self.configFile = self._my_cwd_ + '/AutoCfg.xml'
        check_config(self.configFile)

        make_dir(self._my_cwd_)


    def AutoSim(self):

        # 生成.sumocfg配置文件: 包括背景流量的sumocfg、新建项目的sumocfg等
        # print(r'---Start to Generate Config File for SUMO---')
        cfg = cfgGenerate(self.configFile)
        result = cfg.generate()
        # print("cfg Generated:", result)

        config_tree = read_xml(self.configFile)
        with open('in\module.json', 'r', encoding="utf-8") as f:
            jsondata = json.load(f)

        # 背景流量part
        # print(r'开启背景流量生成')

        # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
        # print(r'---Start to Generate Demand File for SUMO---')
        result = rouGenerate(outputpath = '../tw_rdc_case/output_background', tag = 'background')
        # print("rou Generated:", result)

        # 启动仿真(先不启动)
        # print(r'---Launch SUMO---')
        # proc = subprocess.Popen(
        #     r'sumo -c ./output_background/background_sim.sumocfg')
        # proc.wait()
        # print("Finished:", result)

        # # print(r'背景流量生成成功')

        # # print(r'开启数据输出与计算')

        # cal_edge_lane(r'./output_background/output.lanedata.xml',r'./output_background/osm.net.xml',r'./output/output_background/simulation_veh_lane_background.csv',r'./output/output_background/simulation_veh_link_background.csv',r'./cache/dss_project_link.csv')
        # # cal_junc(r'./output_background/osm.net.xml',r'./output/output_background/simulation_veh_lane_background.csv',r'./output_background/交叉口进口道方位.csv',r'./output/output_background/交叉口分组结果.csv',r'./output/output_background/交叉口计算结果.csv',r'./output_background/交叉口出口道方位.csv',r'./output/output_background/junction_result_background.csv')
        # overall_statistics(path1 = r'./output_background', path2 = r'./output/output_background')
        # overall_statistics1(path1 = r'./output_background', path2 = r'./output/output_background')
        # # # print(r'数据输出与计算完成')
 
        
        ## 新建项目part
        if jsondata["new_built"] == 'on':
            # print(r'开启新建项目模块')
            mapRepair.cutline(outputpath = r'./output_new_built',tag="new_built")
            mapRepair.new_built(outputpath = r'./output_new_built',tag="new_built")

            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath = '../tw_rdc_case/output_new_built', tag = 'output_new_built')
            # print("rou Generated:", result)

            # # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_new_built/new_built_sim.sumocfg --fcd-output fcd.xml --step-length 0.5')
            proc.wait()

            
            # print("Finished:", result)

            # print(r'新建项目成功')

            # print(r'开启数据输出与计算')
            combine_link1(path1=r'./output_new_built', path2=r'./output/output_new_built', tag='new_built')
            overall_statistics2(path1 = r'./output_new_built', path2 = r'./output/output_new_built',path3 = 2)

            # print(r'数据输出与计算完成')

            ## 地块更新part
        if jsondata["refresh"] == 'on':
            # print(r'开启地块更新模块')

            refresh.fresh(r'./in/refresh.json', "7-9", r'./output_refresh/later_od.xml',\
                        r'./output_refresh/newod.xml', r'./output_refresh/combine.xml')

            mapRepair.cutline(outputpath = r'./output_refresh')
            mapRepair.new_built(outputpath = r'./output_refresh')

            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath='../tw_rdc_case/output_refresh', tag='output_refresh')
            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_refresh/refresh_sim.sumocfg --fcd-output ./output_refresh/fcd.xml --step-length 0.5')
            proc.wait()
            # proc = subprocess.Popen(
            #     r"sumo -c ./output_refresh/refresh_sim.sumocfg --fcd-output ./output_refresh/fcd.xml --step-length 0.5"
            # )
            # proc.wait()
            # print("Finished:", result)

            # print(r'地块更新成功')

            # print(r'开启数据输出与计算')
            combine_link1(path1=r'./output_refresh', path2=r'./output/output_refresh', tag='refresh')
            overall_statistics2(path1 = r'./output_refresh', path2 = r'./output/output_refresh',path3 = 2)
            # print(r'数据输出与计算完成')


         ## 停车场新建改建part
        if jsondata["parking_new"] == 'on':
            # print(r'开启停车场新建改建模块')
    
            mapRepair.cutline(outputpath = r'./output_parking_new',tag="parking_new")
            mapRepair.new_built(outputpath = r'./output_parking_new',tag="parking_new")

            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath = '../tw_rdc_case/output_parking_new', tag = 'output_parking_new')
            
            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_parking_new/parking_new_sim.sumocfg')
            proc.wait()
            # print("Finished:", result)

            # print(r'停车场新建改建成功')

            # print(r'开启数据输出与计算')
            combine_link1(path1=r'./output_parking_new', path2=r'./output/output_parking_new', tag='parking_new')
            overall_statistics2(path1 = r'./output_parking_new', path2 = r'./output/output_parking_new',path3 = 2)
            
            # print(r'数据输出与计算完成')



        ## 限号政策模块
        if jsondata["limit_num"] == 'on':
            # print(r'开启限号政策模块')

            xianxing("./cache/GC_ODtaz_motorized.csv","./output_limit_num/GC_ODtaz_motorized_changed.csv","./in/limit_num.json")
            writing_xml("./output_limit_num/GC_ODtaz_motorized_changed.csv",'in\limit_num.json',"./output_limit_num/od.xml")

            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath = '../tw_rdc_case/output_limit_num', tag = 'output_limit_num')

            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_limit_num/limit_num_sim.sumocfg')
            proc.wait()
            # print("Finished:", result)

            # print(r'限号政策成功')

            # print(r'开启数据输出与计算')

            cal_edge_lane(r'./output_limit_num/output.lanedata.xml',r'./output_limit_num/osm.net.xml',r'./output/output_limit_num/simulation_veh_lane_limit_num.csv',r'./output/output_limit_num/simulation_veh_link_limit_num.csv',r'./cache/dss_project_link.csv',tag=0)
            overall_statistics(path1=r'./output_limit_num', path2=r'./output/output_limit_num',path3 = 0)

            # print(r'数据输出与计算完成')

        # 公交票价优惠政策part
        if jsondata["bus_discount"] == 'on':
            # print(r'开启公交票价优惠政策part')

            bus_discount.bus_discount("./cache/GC_ODtaz_motorized.csv", "./output_bus_discount/GC_ODtaz_motorized_changed.csv", "./in/bus_discount.json")
            # update_odxml(r"./output_bus_discount/GC_ODtaz_motorized_changed.csv",r"./cache/od.taz.xml",r"./cache/tazshp/gcTaz 2022-02-28.shp",r"./output_bus_discount/GC_ODtaz_motorized_changed.csv")
            bus_discount.bus_discount_od("./output_bus_discount/GC_ODtaz_motorized_changed.csv", "7-9", "./output_bus_discount/od.xml")
            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath = '../tw_rdc_case/output_bus_discount', tag = 'bus_discount')
            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_bus_discount/bus_discount_sim.sumocfg')
            proc.wait()
            # print("Finished:", result)

            # print(r'公交票价优惠政策成功')

            # print(r'开启数据输出与计算')

            cal_edge_lane(r'./output_bus_discount/output.lanedata.xml', r'./output_bus_discount/osm.net.xml', r'./output/output_bus_discount/simulation_veh_lane_bus_discount.csv', r'./output/output_bus_discount/simulation_veh_link_bus_discount.csv',r'./cache/dss_project_link.csv')
            overall_statistics(path1 = r'./output_bus_discount', path2 = r'./output/output_bus_discount')

            # print(r'数据输出与计算完成')

        # 过境限行政策模块
        if jsondata["transit_flow"] == 'on':
            # print(r'开启过境限行政策模块')

            transit_flow.transit_t(transit_file = "./cache/odgc_through_all.csv", json_file = "./in/transit_flow.json",\
                                   filter_csv = "./cache/od_filter_all.csv")
            transit_flow.transit_c(filter_csv = "./cache/od_filter_all.csv", json_file = "./in/transit_flow.json",\
                                   through_file = "./cache/throughc.csv")
            transit_flow.transit_o(moto_file = "./cache/odgc_motorized_all.csv", through_file = "./cache/throughc.csv",\
                                   transit_output = "./output_transit_flow/od_filter_count.csv")
            update_odxml(r'./output_transit_flow/od_filter_count.csv',r'./cache/od.taz.xml',r'./cache/tazshp/gcTaz 2022-02-28.shp',r'./output_transit_flow/od_filter_count.csv')
            transit_flow.time_distr(transit_file = "./cache/odgc_through_all.csv",distr_file="./output_transit_flow/distr.csv")
            transit_flow.writing_xml("./output_transit_flow/od_filter_count.csv", "7-9", "./output_transit_flow/od.xml")

            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath='../tw_rdc_case/output_transit_flow', tag='output_transit_flow')
            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_transit_flow/transit_flow_sim.sumocfg')
            proc.wait()
            # print("Finished:", result)

            # print(r'开启数据输出与计算')
            cal_edge_lane(
                r'./output_transit_flow/output.lanedata.xml',
                r'./output_transit_flow/osm.net.xml',
                r'./output/output_transit_flow/simulation_veh_lane_transit_flow.csv',
                r'./output/output_transit_flow/simulation_veh_link_transit_flow.csv',r'./cache/dss_project_link.csv')

            overall_statistics(path1=r'./output_transit_flow', path2=r'./output/output_transit_flow')

            # print(r'数据输出与计算完成')

        # 停车收费政策part
        if jsondata["parking_charge"] == 'on':
            # print(r'开启停车收费政策part')

            parkingdemand_function.writing_xml("./output_parking_charge/df_upd_count.csv", "7-9",\
                                               "./output_parking_charge/od.xml", "./in/parking_charge.json")
            #需要对od.xml进行修正
            # 生成.rou.xml需求文件：公交、地铁、小汽车、自行车、行人
            # print(r'---Start to Generate Demand File for SUMO---')
            result = rouGenerate(outputpath='../tw_rdc_case/output_parking_charge', tag='parking_charge')
            # print("rou Generated:", result)

            # 启动仿真
            # print(r'---Launch SUMO---')
            proc = subprocess.Popen(
                r'sumo -c ./output_parking_charge/parking_charge_sim.sumocfg')
            proc.wait()
            # print("Finished:", result)

            # print(r'停车收费政策成功')

            # print(r'开启数据输出与计算')

            cal_edge_lane(r'./output_parking_charge/output.lanedata.xml', r'./output_parking_charge/osm.net.xml',
                          r'./output/output_parking_charge/simulation_veh_lane_parking.csv',
                          r'./output/output_parking_charge/simulation_veh_link_parking.csv',r'./cache/dss_project_link.csv')

            overall_statistics(path1=r'./output_parking_charge', path2=r'./output/output_parking_charge')

            # print(r'数据输出与计算完成')

#
#
if __name__ == '__main__':
    # print(r'---AutoSim for SUMO---')

    start_time = time.time()

    _my_cwd_ = get_cwd()
    make_dir(_my_cwd_)
    AS = AutoSim(_my_cwd_)
    AS.AutoSim()

    end_time = time.time()

    # print('Time Cost:{time}'.format(time=end_time - start_time))