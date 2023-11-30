import pandas as pd
import json

def combine_link(file1,file2,jsonfile,savefile):
    data_qian_link = pd.read_csv(file1)
    data_hou_link = pd.read_csv(file2)
    df_qian_link = pd.DataFrame(data_qian_link)
    df_hou_link = pd.DataFrame(data_hou_link)
    with open(jsonfile, 'r', encoding="utf-8") as f:
        data = json.load(f)
    break_link_id = []
    for i in range(len(data["passageWays"])):
        link_id = data["passageWays"][i]["linkId"]
        if link_id.startswith("'"):
            link_id = link_id.split("'")[1]
            break_link_id.append(link_id)
        else:
            break_link_id.append(link_id)        
    new_link_id = []
    for i in range(len(break_link_id)):
        new_1 = break_link_id[i] + "_1"
        new_2 = break_link_id[i] + "_2"
        new_link_id.append(new_1)
        new_link_id.append(new_2)

    background_vol = []
    background_cap = []
    background_ser_level = []
    for i in range(len(df_hou_link["ID"])):
        if str(df_hou_link["ID"][i]) in list(df_qian_link["ID"]):
            for e in range(len(df_qian_link["flow"])):
                if str(df_hou_link["ID"][i]) == str(df_qian_link["ID"][e]):
                    background_vol.append(df_qian_link["flow"][e])
                    background_cap.append(df_qian_link["voc"][e])
                    background_ser_level.append(df_qian_link["service_level"][e])
        else:
            background_vol.append("新增")
            background_cap.append("新增")
            background_ser_level.append("新增")

    check = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check.append(background_vol[i])

    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            yuan = df_hou_link["ID"][i].split("_")[0]
            # print(df_hou_link["ID"][i]) #-462717450#1_1   -462717450#1_2
            for e in range(len(df_qian_link["ID"])):
                if str(df_qian_link["ID"][e]) == yuan:
                    background_vol[i] = df_qian_link["flow"][e]
                    background_cap[i] = df_qian_link["voc"][e]
                    background_ser_level[i] = df_qian_link["service_level"][e]
                else:
                    continue

    check_new = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check_new.append(df_hou_link["ID"][i])

    change_vol = []
    change_cap = []
    for i in range(len(background_cap)):
        bian_vol = float(df_hou_link["flow"][i]) - float(background_vol[i])
        bian_cap = float(df_hou_link["voc"][i]) - float(background_cap[i])
        change_vol.append(bian_vol)
        change_cap.append(bian_cap)

    df_hou_link["flow_raw"] = background_vol
    df_hou_link["voc_raw"] = background_cap
    df_hou_link["service_level_raw"] = background_ser_level
    df_hou_link["flow_change"] = change_vol
    df_hou_link["voc_change"] = change_cap
    df_hou_link.to_csv(savefile)

    

def combine_lane(file1,file2,jsonfile,savefile):
    data_qian_lane= pd.read_csv(file1)
    data_hou_lane = pd.read_csv(file2)
    df_qian_lane = pd.DataFrame(data_qian_lane)
    df_hou_lane = pd.DataFrame(data_hou_lane)
    with open(jsonfile, 'r', encoding="utf-8") as f:
        data = json.load(f)
    break_link_id = []
    for i in range(len(data["passageWays"])):
        link_id = data["passageWays"][i]["linkId"]
        if link_id.startswith("'"):
            link_id = link_id.split("'")[1]
            break_link_id.append(link_id)
        else:
            break_link_id.append(link_id)   
    new_link_id = []
    for i in range(len(break_link_id)):
        new_1 = break_link_id[i] + "_1"
        new_2 = break_link_id[i] + "_2"
        new_link_id.append(new_1)
        new_link_id.append(new_2)

    background_vol = []
    background_cap = []
    background_ser_level = []
    for i in range(len(df_hou_lane["ID"])):
        if str(df_hou_lane["ID"][i]) in list(df_qian_lane["ID"]):
            for e in range(len(df_qian_lane["flow"])):
                if str(df_hou_lane["ID"][i]) == str(df_qian_lane["ID"][e]):
                    background_vol.append(df_qian_lane["flow"][e])
                    background_cap.append(df_qian_lane["voc"][e])
                    background_ser_level.append(df_qian_lane["service_level"][e])
        else:
            background_vol.append("新增")
            background_cap.append("新增")
            background_ser_level.append("新增")

    check = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check.append(background_vol[i])

    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            yuan = df_hou_lane["ID"][i][:-4] + df_hou_lane["ID"][i][-2:]
            # print(df_hou_link["ID"][i]) #-462717450#1_1   -462717450#1_2
            for e in range(len(df_qian_lane["ID"])):
                if str(df_qian_lane["ID"][e]) == yuan:
                    background_vol[i] = df_qian_lane["flow"][e]
                    background_cap[i] = df_qian_lane["voc"][e]
                    background_ser_level[i] = df_qian_lane["service_level"][e]
                else:
                    continue

    check_new = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check_new.append(df_hou_lane["ID"][i])

    change_vol = []
    change_cap = []
    for i in range(len(background_cap)):
        bian_vol = float(df_hou_lane["flow"][i]) - float(background_vol[i])
        bian_cap = float(df_hou_lane["voc"][i]) - float(background_cap[i])
        change_vol.append(bian_vol)
        change_cap.append(bian_cap)

    df_hou_lane["flow_raw"] = background_vol
    df_hou_lane["voc_raw"] = background_cap
    df_hou_lane["service_level_raw"] = background_ser_level
    df_hou_lane["flow_change"] = change_vol
    df_hou_lane["voc_change"] = change_cap
    df_hou_lane.to_csv(savefile)


def combine_junc(background_csv,new_csv,output,jsonfile):
    data_qian_junc = pd.read_csv(background_csv)
    data_hou_junc = pd.read_csv(new_csv)
    df_qian_junc = pd.DataFrame(data_qian_junc)
    df_hou_junc = pd.DataFrame(data_hou_junc)
    with open(jsonfile, 'r', encoding="utf-8") as f:
        data = json.load(f)
    break_link_id = []
    for i in range(len(data["passageWays"])):
        link_id = data["passageWays"][i]["linkId"]
        if link_id.startswith("'"):
            link_id = link_id.split("'")[1]
            break_link_id.append(link_id)
        else:
            break_link_id.append(link_id)   
    new_link_id = []
    for i in range(len(break_link_id)):
        new_1 = break_link_id[i] + "_1"
        new_2 = break_link_id[i] + "_2"
        new_link_id.append(new_1)
        new_link_id.append(new_2)
    background_vol = []
    background_cap = []
    background_timeloss = []
    for i in range(len(df_hou_junc["交叉口id"])):
        background_vol.append("新增")
        background_cap.append("新增")
        background_timeloss.append("新增")

    for i in range(len(df_hou_junc["交叉口id"])):
        if str(df_hou_junc["交叉口id"][i]) in list(df_qian_junc["交叉口id"]):
            for e in range(len(df_qian_junc["flow"])):
                if str(df_hou_junc["交叉口id"][i]) == str(df_qian_junc["交叉口id"][e]) and str(df_hou_junc["from_edge"][i]) == str(df_qian_junc["from_edge"][e]) and str(df_hou_junc["to_edge"][i]) == str(df_qian_junc["to_edge"][e]):
                    background_vol[i] = df_qian_junc["flow"][e]
                    background_cap[i] = df_qian_junc["voc"][e]
                    background_timeloss[i] = df_qian_junc["ave_delay"][e]
        else:
            continue
    check = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check.append(i)
    #然后找新增是from_edge还是to_edge的
    for i in range(len(df_hou_junc["交叉口id"])):
        if background_vol[i] == "新增":
            yuan_from = df_hou_junc["from_edge"][i].split("_")[0]
            yuan_to = df_hou_junc["to_edge"][i].split("_")[0]
            if str(df_hou_junc["from_edge"][i]) in new_link_id:
                for e in range(len(df_qian_junc["交叉口id"])):
                    if str(df_hou_junc["交叉口id"][i]) == str(df_qian_junc["交叉口id"][e]) and str(yuan_from) == str(df_qian_junc["from_edge"][e]) and str(yuan_to) == str(df_qian_junc["to_edge"][e]):
                        background_vol[i] = df_qian_junc["flow"][e]
                        background_cap[i] = df_qian_junc["voc"][e]
                        background_timeloss[i] = df_qian_junc["ave_delay"][e]
                    else:
                        continue
            elif str(df_hou_junc["to_edge"][i]) in new_link_id:
                for e in range(len(df_qian_junc["交叉口id"])):
                    if str(df_hou_junc["交叉口id"][i]) == str(df_qian_junc["交叉口id"][e]) and str(yuan_from) == str(df_qian_junc["from_edge"][e]) and str(yuan_to) == str(df_qian_junc["to_edge"][e]):
                        background_vol[i] = df_qian_junc["flow"][e]
                        background_cap[i] = df_qian_junc["voc"][e]
                        background_timeloss[i] = df_qian_junc["ave_delay"][e]
                    else:
                        continue
            else:
                continue
        else:
            continue
    check_new = []
    for i in range(len(background_vol)):
        if background_vol[i] == "新增":
            check_new.append(i)
    df_hou_junc["flow_raw"] = background_vol
    df_hou_junc["voc_raw"] = background_cap
    df_hou_junc["ave_delay_raw"] = background_timeloss
    df_hou_junc2 = df_hou_junc[-df_hou_junc.flow_raw.isin(["新增"])]
    df_hou_junc2.to_csv(output)
# file1 = r'simulation_veh_link_background.csv'
# file2 = r'simulation_veh_link_new_built.csv'
# file1 = r'simulation_veh_lane_background.csv'
# file2 = r'simulation_veh_lane_new_built.csv'
# jsonfile = r"in.json"
# savefile = r"new_simulation_lane_veh.csv"
# combine_link(file1,file2,jsonfile,savefile)
# combine_lane(file1,file2,jsonfile,savefile)
#combine_junc('tw_rdc_case/output/output_background/junction_result_background.csv','tw_rdc_case/output/output_new_built/junction_result_new_built.csv','tw_rdc_case/output/output_new_built/fin_simulation_junc_veh.csv','tw_rdc_case/in/new_built.json')
# combine_junc('junction_result_background.csv','junction_result_new_built.csv','fin_simulation_junc_veh.csv','in.json')