import xml.etree.ElementTree as ET
from pandas.core.frame import DataFrame
import pandas as pd
import json
from collections import Counter

def cal_junc_5min(file1,file3,file4,file5,file6,file8,tag):
    with open(file8, 'r', encoding="utf-8") as f:
        data = json.load(f)
    surrounding_node_id = []
    for i in range(len(data["surroundingNodes"])):
        link_id = data["surroundingNodes"][i]
        surrounding_node_id.append(link_id)
    tree = ET.parse(file1)
    root = tree.getroot()
    connections = root.findall('connection')
    from_edge = []
    to_edge = []
    from_lane_index = []
    to_lane_index = []
    direction = []
    for connection in connections:
        if ":" not in connection.attrib['from'] and ":" not in connection.attrib['to']:
            from_edge.append(connection.attrib['from'])
            to_edge.append(connection.attrib['to'])
            from_lane_index.append(connection.attrib['fromLane'])
            to_lane_index.append(connection.attrib['toLane'])
            direction.append(connection.attrib['dir'])
    from_lane = []
    to_lane = []
    for i in range(len(from_edge)):
        f_l = from_edge[i] +"_"+ from_lane_index[i]
        t_l = to_edge[i] +"_"+ to_lane_index[i]
        from_lane.append(f_l)
        to_lane.append(t_l)
    junc_df = DataFrame({'from_edge':from_edge, 'to_edge':to_edge, 'from_lane':from_lane, 'to_lane':to_lane, 'dir':direction})
    # print(junc_df)

    '''到目前为止还没有交叉口id'''
    data = pd.read_csv(file3)
    df_jin = pd.DataFrame(data)
    jin_id_csv = df_jin["jkdmc"]
    junc_id_csv = df_jin["交叉口id"]
    junc_id = []
    for i in range(len(from_edge)):
        if from_edge[i] in set(jin_id_csv):
            for e in range(len(jin_id_csv)):
                if from_edge[i] == jin_id_csv[e]:
                    junc_id.append(junc_id_csv[e])
                else:
                    continue
        else:
            junc_id.append("0")
    junc_df["交叉口id"] = junc_id
    surrounding_flag = []
    for i in range(len(junc_id)):
        if junc_id[i] in surrounding_node_id:
            for e in range(len(surrounding_node_id)):
                if junc_id[i] == surrounding_node_id[e]:
                    surrounding_flag.append("1")
                else:
                    continue
        else:
            surrounding_flag.append("2")
    # print(len(surrounding_flag))
    junc_df["surrounding_flag"] = surrounding_flag
    junc2_df = junc_df[-junc_df.surrounding_flag.isin(["2"])]
    # print(junc2_df)
    junc3_df = junc2_df.reset_index(drop=True)
    # print(junc3_df)

    for cycle_time in range(1,13):
        #下面需要进口道车道的交通量
        file2 = "./output/output_" + tag + "/simulation_veh_lane_" + tag + "_5min" + "_" + str(cycle_time) +".csv"
        data_vol = pd.read_csv(file2)
        df_vol = pd.DataFrame(data_vol)
        laneID_vol = df_vol["ID"]
        ave_vol = df_vol["flow"]
        lane_timeloss_vol = df_vol["time_loss"]
        v_c_vol = df_vol["voc"]
        vol_all = []
        timeloss_all = []
        v_c_all = []
        # duqudata_above = pd.read_csv(r"F:\suzhougucheng\output_convert_xy\output_huizong\交叉口计算1.csv")
        # df_duqu_above = pd.DataFrame(duqudata_above)
        # from_lane = df_duqu_above["from_lane"]
        for i in range(len(junc3_df["from_lane"])):
            if junc3_df["from_lane"][i] in set(laneID_vol):
                for e in range(len(laneID_vol)):
                    if junc3_df["from_lane"][i] == laneID_vol[e]:
                        vol_all.append(ave_vol[e])
                        timeloss_all.append(lane_timeloss_vol[e])
                        v_c_all.append(v_c_vol[e])
                    else:
                        continue
            else:
                vol_all.append("0")
                timeloss_all.append("0")
                v_c_all.append("0")
        junc3_df["flow"] = vol_all
        junc3_df["delay"] = timeloss_all
        junc3_df["voc"] = v_c_all
        # 匹配simulation_lane中的lane_id_veh，这里面的lane是剔除了自行车道和人行道的
        junc_label = []
        lane_tichu = df_vol["ID"]
        for i in range(len(junc3_df["from_lane"])):
            if junc3_df["from_lane"][i] in set(lane_tichu):
                junc_label.append(1)
            else:
                junc_label.append(2)
        junc3_df["剔除情况"] = junc_label
        junc4_df = junc3_df[-junc3_df.剔除情况.isin([2])]
        # print(junc4_df)
        '''下一步就是如何获取grouped每个group内包含的index'''
        # n_grouped = junc2_df.groupby(['交叉口id','from_lane'])
        #print(n_grouped) #<pandas.core.groupby.generic.DataFrameGroupBy object at 0x0000020C7E7A4C70>
        new_grouped = junc4_df.groupby(['交叉口id','from_lane']).apply(lambda x:x[:]).drop(axis =1,columns=["交叉口id","from_lane"],inplace=False)
        new_grouped = pd.DataFrame(new_grouped)
        #print(new_grouped) #这个是符合我要求的，一个交叉口id，后面是from_lane
        new_grouped.to_csv(file4)
        '''现在判断如果交叉口id相同，且from_lane相同的情况下，to_lane不同，那么我们就看dir的组合情况'''
        data2 = pd.read_csv(file4)
        df = pd.DataFrame(data2)
        #print(df)
        from_lane_num = Counter(df["from_lane"])
        # print(from_lane_num)
        dic_from_lane_num = dict(from_lane_num)
        # print(dic_from_lane_num)
        i = 0
        dir_same = []
        #print(type(dic_from_lane_num["621257569_2"])) #<class 'int'>
        for key,value in dic_from_lane_num.items():
            if value == 1:
                dir_same.append(list(df["dir"])[i])
                i += 1
                continue
            else:
                for n in range(value):
                    dir_l = list(df["dir"])[i:i+value]
                    dir_same.append(dir_l)
                i += value
        #print(len(dir_same))
        #print(dir_same)
        #下一步判断dir_sample中方向的组合情况，然后给定一个交通量
        for i in range(len(dir_same)):
            if len(dir_same[i]) == 1:
                continue
            elif len(dir_same[i]) == 2:
                if ("s" and "l") in dir_same[i]:
                    if df["dir"][i] == "s":
                        df["flow"][i] = 0.3*df["flow"][i]
                        df["delay"][i] = 0.3*df["delay"][i]
                        df["voc"][i] = 0.3 * df["voc"][i]
                    else:
                        df["flow"][i] = 0.7*df["flow"][i]
                        df["delay"][i] = 0.7*df["delay"][i]
                        df["voc"][i] = 0.7 * df["voc"][i]
                elif ("s" and "r") in dir_same[i]:
                    if df["dir"][i] == "s":
                        df["flow"][i] = 0.3*df["flow"][i]
                        df["delay"][i] = 0.3*df["delay"][i]
                        df["voc"][i] = 0.3 * df["voc"][i]
                    else:
                        df["flow"][i] = 0.7*df["flow"][i]
                        df["delay"][i] = 0.7*df["delay"][i]
                        df["voc"][i] = 0.7 * df["voc"][i]
                elif ("s" and "t") in dir_same[i]:
                    if df["dir"][i] == "t":
                        df["flow"][i] = 0.3*df["flow"][i]
                        df["delay"][i] = 0.3*df["delay"][i]
                        df["voc"][i] = 0.3 * df["voc"][i]
                    else:
                        df["flow"][i] = 0.7*df["flow"][i]
                        df["delay"][i] = 0.7*df["delay"][i]
                        df["voc"][i] = 0.7 * df["voc"][i]
                elif ("l" and "t") in dir_same[i]:
                    if df["dir"][i] == "t":
                        df["flow"][i] = 0.3*df["flow"][i]
                        df["delay"][i] = 0.3*df["delay"][i]
                        df["voc"][i] = 0.3 * df["voc"][i]
                    else:
                        df["flow"][i] = 0.7*df["flow"][i]
                        df["delay"][i] = 0.7*df["delay"][i]
                        df["voc"][i] = 0.7 * df["voc"][i]
            else:
                df["flow"][i] = df["flow"][i]/len(dir_same[i])
                df["delay"][i] = df["delay"][i]/len(dir_same[i])
                df["voc"][i] = df["voc"][i]/len(dir_same[i])
        #下面将进口道和出口道相同edge的数值合并
        final_group = df.groupby(['交叉口id','from_edge','to_edge']).sum()
        final_group = final_group.drop(axis =1,columns=["Unnamed: 2","剔除情况","surrounding_flag"],inplace=False)
        final_group = pd.DataFrame(final_group)
        # print(final_group)
        final_group.to_csv(file5) 
        # data = pd.read_csv(r"E:\output+坐标转换\output_huizong\交叉口进口道方位.csv")
        data1 = pd.read_csv(file5)
        # df_jin = pd.DataFrame(data)
        result_df = pd.DataFrame(data1)
        jin_id_csv = df_jin["jkdmc"]
        junc_id_res = result_df["交叉口id"]
        from_edge_res = result_df["from_edge"]
        jin_dir_csv = df_jin["jkd_dir"]
        jin_dir = []
        # junc_id = []
        for i in range(len(from_edge_res)):
            # f_edge = from_edge_res[i].split("_")[0]
            f_edge = str(from_edge_res[i])
            if f_edge in set(jin_id_csv):
                for e in range(len(jin_id_csv)):
                    if f_edge == str(jin_id_csv[e]):
                        jin_dir.append(jin_dir_csv[e])
                        # junc_id.append(junc_id_csv[e])
                    else:
                        continue
            else:
                jin_dir.append("0")
                # junc_id.append("0")
        # print(len(jin_dir))
        #print(jin_dir)
        # junc_df["交叉口id"] = junc_id
        result_df["jkd_dir"] = jin_dir
        data3 = pd.read_csv(file6)
        df_chu = pd.DataFrame(data3)
        chu_id_csv = df_chu["ckdmc"]
        chu_dir_csv = df_chu["ckd_dir"]
        to_edge_res = result_df["to_edge"]
        chu_dir = []
        for i in range(len(to_edge_res)):
            # t_edge = str(to_edge_res[i]).split("_")[0]
            t_edge = str(to_edge_res[i])
            if t_edge in set(chu_id_csv):
                for e in range(len(chu_id_csv)):
                    if t_edge == str(chu_id_csv[e]):
                        chu_dir.append(chu_dir_csv[e])
                    else:
                        continue
            else:
                chu_dir.append("0")

        #print(chu_dir)
        result_df["ckd_dir"] = chu_dir
        #车均延误
        ave_loss = []
        for i in range(len(from_edge_res)):
            if result_df["flow"][i] != 0:
                loss_veh = (result_df["delay"][i])/(result_df["flow"][i])
            else:
                loss_veh = 0
            ave_loss.append(loss_veh)
        result_df["ave_delay"] = ave_loss
        results_df = result_df.drop(axis =1,columns="delay",inplace=False)
        file7 = "./output/output_" + tag + "/junction_result_" + tag + "_5min" + "_" + str(cycle_time) +".csv"
        results_df.to_csv(file7)

# cal_junc_5min(r'osm.net.xml',r'交叉口进口道方位.csv',r'交叉口分组结果.csv',r'交叉口计算结果.csv',r'交叉口出口道方位.csv',r'in.json')