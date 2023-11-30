from daduan import *
import subprocess
from new_xifa import filtrate
import json

def add_net(formor_path,net_path):
    tree = ET.parse(formor_path)
    tree.write(net_path)

def rename(add_front_id,rou_files_path,rou_files_new_file):
    tree = ET.parse(rou_files_path)
    root = tree.getroot()  # 获取根节点
    nodes = root.findall("vehicle") 
    for node in nodes:
        new_id = add_front_id + node.attrib["id"]
        node.attrib["id"]  = new_id
    tree.write(rou_files_new_file)


def cutline(outputpath = r'./output_refresh',tag = "refresh"):
    # config_scene_root = self.config_root.find('config_scene')
    # if "on" == config_scene_root.find('roadclose_scene').get('cutline_flag'):
    file_former="./cache/osm.net.xml"
    file = outputpath + '/osm.net.xml'
    add_net(file_former,file)
    if tag == "new_built":
        with open("./in/new_built.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    if tag == "refresh":
        with open("./in/refresh.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    if tag == "parking_new":
        with open("./in/parking_new.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    new_built1(file,data,tag)
    # (file,data,net,xmlfile,junction_id,junction_x,junction_y,edge_id,edge_from,edge_to,final_file)
    proc = subprocess.Popen(
        r'netconvert -s ' + outputpath + '/osm.net.xml -o ' + outputpath + '/osm.net.xml --plain.extend-edge-shape --ignore-errors',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=None,
        bufsize=-1,
    )
    proc.wait()
    return "mapCutline result"

def new_built(outputpath = r'./output_refresh',tag = "refresh",timeslot ="7-9"):
    file="./cache/osm.net.xml"
    newfile = outputpath + '/osm.net.xml'
    tazfile="./cache/od.taz.xml"
    tazfile1 = outputpath + r'/od.taz1.xml'
    if tag == "new_built":
        with open("./in/new_built.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    if tag == "refresh":
        with open("./in/refresh.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    if tag == "parking_new":
        with open("./in/parking_new.json", 'r', encoding="utf-8") as f:
            data = json.load(f)
    former_taz=edge2taz(tazfile,file,data)
    # former =
    new_built_taz=added_taz_id(file,tazfile,data,tazfile1,newfile)
    print(former_taz,new_built_taz)
    in_path=r"./cache/GC_ODtaz_motorized.csv"
    timeslot='7-9'
    if (tag == "refresh") or (tag == "new_built"):
        occurance_num=round(data["occurNum"]*2)
        attraction_num =round(data["attractNum"]*2)
    if tag == "parking_new":
        occurance_num=round(data["berthsNumber"]*(12/data["parkingTime"])*0.1*0.5*2) #要改
        attraction_num =round(data["berthsNumber"]*(12/data["parkingTime"])*0.1*0.5*2) #要改
        #需要停车泊位数的数据
    # occurance_num = float(data["occurNum"])
    # attraction_num = float(data["attractNum"])
    # print(occurance_num,attraction_num)
    filtrate(former_taz,new_built_taz,occurance_num,attraction_num,in_path,timeslot,tag)
    # print("ok")
    proc = subprocess.Popen(
        r'od2trips -n ' + outputpath + '/od.taz1.xml --od-amitran-files ' + outputpath + '/' + tag + '_od.xml -o ' + outputpath + '/new.trip.xml --ignore-errors',
        shell=True,
        stdout=None,
        stderr=None,
        bufsize=-1,
    )
    proc.wait()

    proc = subprocess.Popen(
        r'duarouter -n ' + outputpath + '/osm.net.xml -r ' + outputpath + '/new.trip.xml -o ' + outputpath + '/new.rou.xml --ignore-errors --seed 42 --randomize-flows --repair',
        shell=True,
        stdout=None,
        stderr=None,
        bufsize=-1,
    )
    proc.wait()

    add_front_id = "A"
    rou_files_path = outputpath + '/new.rou.xml'
    rou_files_new_path = outputpath + '/new.rou.xml'
    rename(add_front_id,rou_files_path,rou_files_new_path)




# mapRepair.cutline()  #这两行不需要，否则在auto主文件中导入mapRepair包后，会即刻运行这两个函数
# mapRepair.new_built()