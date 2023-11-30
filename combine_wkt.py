from pandas.core.frame import DataFrame
import pandas as pd
def combine_wkt(file1,file2,file3):
    data_wkt = pd.read_csv(file1)
    new_built_wkt_df = pd.DataFrame(data_wkt)
    data_link = pd.read_csv(file2)
    new_link_df = pd.DataFrame(data_link)
    link_name = []
    wkt = []
    for i in range(len(new_built_wkt_df["edge_id"])):
        if str("'" + new_built_wkt_df["edge_id"][i] + "'") in list(new_link_df["edge_id"]):
            for j in range(len(new_link_df["edge_id"])):
                a = str(new_link_df["edge_id"][j].split("'")[-2])
                if str(new_built_wkt_df["edge_id"][i]) == a:
                    link_name.append(new_built_wkt_df["edge_id"][i].split("_")[0])
                    wkt.append(new_built_wkt_df["wkt"][i])
                else:
                    continue
        else:
            continue
    # print(len(link_name))
    # print(link_name)
    data_simulation = pd.read_csv(file3)
    simula_df = pd.DataFrame(data_simulation)
    simula_link_name = []
    simula_wkt = []
    for i in range(len(simula_df["ID"])):
        if str(simula_df["ID"][i]) in list(new_built_wkt_df["edge_id"]):
            for j in range(len(new_built_wkt_df["edge_id"])):
                if str(simula_df["ID"][i]) == str(new_built_wkt_df["edge_id"][j]):
                    simula_link_name.append(link_name[j])
                    simula_wkt.append(wkt[j])
                else:
                    continue
        else:
            simula_link_name.append(1)
            simula_wkt.append(1)
    # print(len(simula_link_name))
    simula_df["link_name"] = simula_link_name
    simula_df["wkt"] = simula_wkt
    # print(simula_df)
    simula_df.to_csv(file3,index=False)

# combine_wkt('./tw_rdc_case/output/output_new_built/break_link_wkt.csv', './tw_rdc_case/output/output_new_built/dss_project_link.csv', './tw_rdc_case/output/output_new_built/new_simulation_link_veh.csv', './tw_rdc_case/output/output_new_built/new_simulation_link_veh.csv')