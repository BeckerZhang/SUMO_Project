from edge_lane_cal import cal_edge_lane
from prepare4cal_juc import prepare4cal_juc
from juncion_cal import cal_junc
from update_linkcsv import update_linkcsv
from combine_link_lane import combine_lane,combine_link,combine_junc
from edge_lane_cal_5min import cal_edge_lane_5min
from junc_cal_5min import cal_junc_5min
from combine_wkt import combine_wkt
from fcd_output import fcd_extract

def combine_link1(path1=r'./output_refresh', path2=r'./output/output_refresh', tag='refresh'):
    update_linkcsv('./in/' + tag + '.json','./cache/dss_project_link.csv', path2 + '/dss_project_link.csv')
    cal_edge_lane(path1 + '/output.lanedata.xml', path1 + '/osm.net.xml',
                  path2 + '/simulation_veh_lane_' + tag + '.csv',
                  path2 + '/simulation_veh_link_' + tag + '.csv', path2 + '/dss_project_link.csv','./in/' + tag + '.json')
    cal_edge_lane_5min(path1 + '/output.lanedata_5min.xml', path1 + '/osm.net.xml', path2 + '/dss_project_link.csv',tag)
    prepare4cal_juc(path1 + '/osm.net.xml', path2 + '/junction_for_cal.csv',
                    path2 + '/交叉口进口道方位.csv', path2 + '/交叉口出口道方位.csv')
    if (tag == 'parking_new'):
        pass
    else:
        cal_junc(path1 + '/osm.net.xml',
                path2 + '/simulation_veh_lane_' + tag + '.csv',
                path2 + '/交叉口进口道方位.csv', path2 + '/交叉口分组结果.csv',
                path2 + '/交叉口计算结果.csv', path2 + '/交叉口出口道方位.csv',
                path2 + '/junction_result_' + tag + '.csv', './in/' + tag + '.json')
        cal_junc_5min(path1 + '/osm.net.xml',
                path2 + '/交叉口进口道方位.csv', path2 + '/交叉口分组结果.csv',
                path2 + '/交叉口计算结果.csv', path2 + '/交叉口出口道方位.csv',
                './in/' + tag + '.json', tag)
        combine_junc(r'./cache/junction_result_background.csv',
                    path2 + '/junction_result_' + tag + '.csv',
                    path2 + '/fin_simulation_junc_veh.csv', './in/' + tag + '.json',)
    combine_link(r'./output/output_background/simulation_veh_link_background.csv',
                 path2 + '/simulation_veh_link_' + tag + '.csv', './in/' + tag + '.json',
                 path2 + '/new_simulation_link_veh.csv')
    combine_lane(r'./output/output_background/simulation_veh_lane_background.csv',
                 path2 + '/simulation_veh_lane_' + tag + '.csv', './in/' + tag + '.json',
                 path2 + '/new_simulation_lane_veh.csv')
    combine_wkt(path2+'/break_link_wkt.csv',path2+'/dss_project_link.csv',path2+'/new_simulation_link_veh.csv')
    fcd_extract(path1 + '/output.fcd.xml',path1 + '/osm.net.xml',path1 + '/fcd_raw_cars.csv', path2 + '/subway_fcd.csv','./in/' + tag + '.json', path2 + '/simulation_cars_fcd_in_range.csv')
