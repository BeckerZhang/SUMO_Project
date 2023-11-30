import pandas as pd
import json
import re
import numpy as np

def update_linkcsv(jsonfile,former_linkcsv,output):
    with open(jsonfile, 'r', encoding='utf-8') as f:
        jsondata = json.load(f)
    data = pd.read_csv(former_linkcsv,encoding='utf-8')
    edge_id = []
    for i in range(len(jsondata["passageWays"])):
        edge = jsondata["passageWays"][i]["linkId"]
        if "'" in edge:
            pass
        else:
            edge = "'" + edge + "'"
        edge_id.append(edge)
    # print(len(data))

    df_pro = pd.DataFrame()
    for i in range(len(data)):
        if data["edge_id"][i] in edge_id:
            data_temp = pd.DataFrame(np.repeat(pd.DataFrame(data.iloc[i]).T.values,2,axis=0))
            data_temp.columns = pd.DataFrame(data.iloc[i]).T.columns
            df_pro = pd.concat([df_pro,data_temp])      
    x_list = []
    for i in range(len(df_pro)):
        if (i % 2) == 0:
            link_id = "'" + re.sub("'", "", str(df_pro.iloc[i,0]) + "_1") + "'"
            x_list.append(link_id)
        else:
            link_id1 = "'" + re.sub("'", "", str(df_pro.iloc[i,0]) + "_2") +"'"
            x_list.append(link_id1)
    df_pro["edge_id"]=x_list
    df = pd.DataFrame(data)
    for j in edge_id:
        index = df[df["edge_id"] == j].index.tolist()[0]
        df = df.drop([index],axis=0)
    # df1 = df.drop(df[df[0].str.contains(str(j),na=False)])
    # print(len(df))
    df3 = pd.concat([df,df_pro])
    # print(len(df3))
    df3.to_csv(output,encoding='utf-8')
