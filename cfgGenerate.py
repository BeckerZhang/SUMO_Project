import xml.etree.ElementTree as ET


def read_xml(in_path):
    tree = ET.parse(in_path)
    return tree


def write_xml(tree, out_path):
    tree.write(out_path, encoding="utf-8")


class cfgGenerate:
    def __init__(self, configFile):
        self.configFile = configFile

    def generate(self):
        # 载入用户配置文件
        config_tree = read_xml(self.configFile)
        # 读取用户配置信息(仿真时间、步长、随机种子)
        config_sumo = config_tree.getroot().find('config_sumo')
        begin_time = int(config_sumo.find('time').get('begin'))
        end_time = int(config_sumo.find('time').get('end'))
        step_length = float(config_sumo.find('time').get('step-length'))
        random_seed = int(config_sumo.find('random_number').get('seed'))
        # 读取sumocfg模板文件地址
        sumocfg_tamplate_file = config_sumo.find('sumocfg_template_path').get('value')


        ## 生成用于背景流量的配置文件
        sumocfg_sim_file = './output_background/background_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('background_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('background_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成用于新建项目的配置文件
        sumocfg_sim_file = './output_new_built/new_built_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('new_built_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('new_built_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成用于限号政策的配置文件
        sumocfg_sim_file = './output_limit_num/limit_num_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('limit_num_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('limit_num_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成用于公交票价政策场景的配置文件
        sumocfg_sim_file = './output_bus_discount/bus_discount_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('bus_discount_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('bus_discount_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成用于过境政策的配置文件
        sumocfg_sim_file = './output_transit_flow/transit_flow_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('transit_flow_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('transit_flow_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成用于停车收费政策场景的配置文件
        sumocfg_sim_file = './output_parking_charge/parking_charge_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('parking_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('parking_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)

        ## 生成用地块更新的配置文件
        sumocfg_sim_file = './output_refresh/refresh_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('refresh_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('refresh_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        ## 生成停车场新建改建的配置文件
        sumocfg_sim_file = './output_parking_new/parking_new_sim.sumocfg'

        tree = read_xml(sumocfg_tamplate_file)
        root = tree.getroot()

        time_node = root.find('time')
        bgTime_Tag = time_node.findall("begin")
        bgTime_Tag[0].set("value", str(begin_time))

        edTime_Tag = time_node.findall("end")
        edTime_Tag[0].set("value", str(end_time))

        stTime_Tag = time_node.findall("step-length")
        stTime_Tag[0].set("value", str(step_length))

        random_number_node = root.find('random_number')
        seed_Tag = random_number_node.findall("seed")
        seed_Tag[0].set("value", str(random_seed))

        input_node = root.find('input')
        route_files_Tag = input_node.findall("route-files")
        route_files_Tag[0].set("value", config_sumo.find('parking_new_route-files').get('value'))
        additional_files_Tag = input_node.findall("additional-files")
        additional_files_Tag[0].set("value", config_sumo.find('parking_new_additional-files').get('value'))

        write_xml(tree, sumocfg_sim_file)


        return "Done"
