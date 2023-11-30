import numpy as np
import pandas as pd
import sumolib

def read_sumo_net(path):
    ''' 加载路网'''
    net = sumolib.net.readNet(path, withInternal=True) # 'withPedestrianConnections'
    return net

def find_nearest_edge(net, stop_df, radius, vType):
    ''' 输入：加载后的路网，轨迹df, 搜索半径
     输出：原有的df加两列，一列是每一行的最近边id 一列是到最近边的距离'''
    
    all_edge_list = []
    all_dist_list = []
    
    # 获取路网坐标范围 （对于超出边界的坐标值：不搜索）
    xmin, ymin, xmax, ymax = net.getBoundary()
    # print('Network coordiantes range:')
    # print(xmin, ymin, xmax, ymax)
    
    # 上一个公交站的经纬度的初始值 默认为0 因为总得有一个初值 但其实0是不能用的
    x0 = 0
    y0 = 0
    # 判断 在数据表中 这一行的站点 是否是这条线路的第一个站点 即staion_sequence =1 
    # 这个主要是用于traj_vector的计算：一般情况下 我们是取上一个站点 到这个站点的向量作为traj_vector
    # 但是对于第一个站点 他没有上一个站点 所以需要专门取一下下一个站点 和这一个站点共同构成一个traj_vector
    is_neighboring_sequence = False # 是否和上一个站点是相邻的 例如上一个sequence = 2 这一个sequence = 3 就是相邻
    # 取出每一行的经纬度 转换为SUMO路网的局部坐标（几千到几千）
    for i in range(stop_df.shape[0]):
        lng = stop_df.loc[i,'longitude']
        lat = stop_df.loc[i,'latitude']
        x, y = net.convertLonLat2XY(lng, lat)
        if i >= 1:
            is_neighboring_sequence = (stop_df.loc[i, 'station_sequence'] - stop_df.loc[i-1,'station_sequence']==1) #判断是否是相连的站点
            if is_neighboring_sequence:
                raw_direction = np.subtract((x,y),(x0,y0))
            else:
                # 如果他的上一行站点并不是和他相邻的站点：即他是在表格中的该条线路的第一个站点 取下一行和他构成方向向量
                x_next, y_next = net.convertLonLat2XY(stop_df.loc[i+1,'longitude'], stop_df.loc[i+1,'latitude'])
                raw_direction = np.subtract((x_next,y_next),(x,y))
        else:
            # 如果他是整个数据表的第一行 直接取不到上一行 显然也并非 neighboring sequence 所以也是取下一行和他构成一个方向向量
            x_next, y_next = net.convertLonLat2XY(stop_df.loc[i+1,'longitude'], stop_df.loc[i+1,'latitude'])
            raw_direction = np.subtract((x_next,y_next),(x,y))
        if xmin <= x <= xmax and ymin <= y <= ymax: # 如果在边界以内
            #　最近边搜索的函数接口
            edges = net.getNeighboringEdges(x, y, radius)
            #print(edges)
            if len(edges) > 0: #如果元素大于0　说明搜索出结果 当然如果大于等于2个元素 则需要排序
                edge_list = [] # 候选edge
                allow_list = [] # 是否允许公交车运行的flag
                dist_list = [] # 点到候选边的距离
                dire_dot_list = [] # 储存（每一个边的方向，路径方向的）点积
                for item in edges:
                    if item[0].getFunction() == "":  # sumolib内函数，具体可见 https://sumo.dlr.de/pydoc/sumolib.html
                        # item[0] 是 edge对象
                        # item[1] 是距离
                        edge = item[0].getID()  # 取出来edge id 要使用get接口 因为他是一个封装的net对象
                        allow = item[0].allows(vType)  # 是否允许bus的运行 只应该取所有允许bus通行的edge
                        dist = item[1]
                        edge_list.append(edge)
                        allow_list.append(allow)
                        dist_list.append(dist)
                        edge_direction = np.subtract(item[0].getShape()[-1], item[0].getShape()[0])
                        # 把这个边向量和原始向量的乘积  存储到 dire_dot_list中
                        dire_dot_list.append(np.dot(raw_direction, edge_direction))
                all_df = pd.DataFrame({'edge':edge_list, 'dist':dist_list, 'direction': dire_dot_list, 'allow': allow_list})
                all_df = all_df.loc[all_df['direction'] > 0] # 仅取所有点积大于0的df 即同向边
                all_df = all_df.loc[all_df['allow'] == True] # 仅取所有运行公交车运行的edge
                # 在所有大于0的点积中 取出最近的那条边
                if all_df.shape[0] == 0:
                    # 如果取同向边的 df 是空值 说明都是逆向边 或者不允许公交车运行 不要他
                    all_edge_list.append('None align direction')
                    all_dist_list.append('None align direction')
                else:
                    # 如果同向边有结果（当然结果可能不止一个 则做一个排序 而且一个元素也可以排序 都这么走下来吧）
                    closestEdge = all_df.loc[all_df['dist'].idxmin(),'edge']
                    min_dist = all_df['dist'].min()
                    all_edge_list.append(str(closestEdge))
                    all_dist_list.append(min_dist)
            else:
                # 如果搜索不到：len(edges)=0 说明 没有搜索到最近的边 返回 None
                all_edge_list.append('None nearest edge')
                all_dist_list.append('None nearest edge')
        else:
            #　如果坐标直接超出边界：没有必要再浪费时间搜索　返回 exceed boundary
            all_edge_list.append('Exceed boundary')
            all_dist_list.append('Exceed boundary')
        
        # 把每一次的 最新的 x y 保存下来 用于下一个的方向计算 x0 y0
        x0 = x
        y0 = y
    # 原有的df 加两列：最近边 最近距离  
    
    return all_edge_list, all_dist_list

def cal_offset(net, df):
    '''
    判断公交站在edge上的距离 即busStops.xml中的 startPos
    
    这边的一个误差就是对于曲向边 用了最终点-最起点的结果 所以他这个位置标定对于直线边比较好 对于折线边和曲线边 相对不是那么的准确'''
    df.reset_index(inplace = True)
    del df['index']
    offset_list = []
    for i in range(df.shape[0]):
        point = [df.loc[i, 'x'], df.loc[i, 'y']]
        line_start = net.getEdge(df.loc[i,'edge']).getShape()[0]
        line_end = net.getEdge(df.loc[i,'edge']).getShape()[-1]
        offset = sumolib.geomhelper.lineOffsetWithMinimumDistanceToPoint(point, line_start, line_end, perpendicular=False)
        offset_list.append(offset)
    return offset_list

def find_candidate_lane(net, df, vType):
    '''
    对于每个edge 找到从外向内的第一个允许公交车通过的车道 作为bus stop lane
    但是实践证明如果不放在最外层车道 ptlines2flows 会产生一系列奇怪的问题
    '''
    lane_list = []
    for i in range(df.shape[0]):
        edge = df.loc[i, 'edge']
        no_lanes = net.getEdge(edge).getLaneNumber() # 获取有几条车道 前面已经挑选出所有允许公交车运行的边了 所以至少有一个lane是允许公交车运行的
        lane = 0 # 从最外侧的车道逐渐向里面递增 直到找到对应的车道
        while (lane < no_lanes) and (not net.getLane('{}_{}'.format(edge, lane)).allows(vType)):
            lane = lane + 1
        # 出了这个循环以后 如果超过了车道数 说明找遍了车道也没有对应的lane
        if lane > no_lanes:
            # print('{} {} has no candidate lane, please check'.format(station_id, station_name))
            lane = 0 # 如果搜遍了也发现不合适的话 还是保留这个站点 只不过lane先放为0
        lane_list.append(lane)
    df['lane'] = lane_list
    return df

                
def merge_stations(df, merge_threshold):
    '''合并相同地方的公交站点
     df2 是合并公共站点的中间文件
    df3 需要根据df2的结果，合并相近的公交站点 其方法是邻近边取中位数'''

    # 先排序再错位相减
    df2 = df.sort_values(by=['edge','offset'], ascending = True)
    df2['diff1'] = np.abs(df2['offset'].diff())
    df2['diff2'] = np.abs(df2['offset'].diff(-1))
    # 筛选在邻域半径以内的 任意 diff1 或者 diff2 在邻域半径以内都行
    df2 = pd.concat([df2.loc[(df2['diff1'] <= merge_threshold)],df2.loc[df2['diff2'] <= (merge_threshold)]], axis=0)
    # 这样合并肯定会有重复的（diff1 diff2 都在邻域半径以内 所以删除掉重复行）
    df2.drop_duplicates(inplace = True)
    
    # 查看一下高德中的原始ID是否匹配
    df2['raw_id'] = df2['station_id'].apply(lambda x: x.split('_')[1]) # 取出来原来station id 的第二个元素（不加线路ID的ID）
    label_list = []
    # (raw_id, edge) 是每个公交站唯一的识别符
    for item in zip(df2['raw_id'].values, df2['edge'].values):
        label_list.append(item)
    df2['label'] = label_list
    label_values = pd.DataFrame(df2['label'].value_counts())
    # 还是有些公交站比较巧 恰好和前后的站点offset 差值小于一个界限 因此只取出现次数大于2次的站点 超过两次出现才需要合并起来
    df2 = df2[df2['label'].isin(label_values[label_values['label']>=2].index)]
    
    # 对于原始记录公交站顺序的表格 更新所有的 ID
    df3 = df.copy()
    df3['raw_id'] = df3['station_id'].apply(lambda x: x.split('_')[1])
    for i in range(df3.shape[0]):
        # 还是以 (raw_id, edge) 作为识别符
        label = (df3.loc[i,'raw_id'], df3.loc[i,'edge'])
        if label in set(df2['label'].values):
            df3.loc[i,'station_id'] = '{}_{}'.format(label[0], label[1]) # 公共站点的命名方式：站点名_edge
            df3.loc[i, 'offset'] = df2[df2['label'] == label]['offset'].median()
    return df3

def find_map_trace(net, traj_df, map_trace_radius):
    ''' GPS运行轨迹的匹配
     存储线路-轨迹的一个字典 键是线路的id号  值是轨迹的列表'''
    line_trace_dict = {}
    
    # 路网坐标范围 
    xmin, ymin, xmax, ymax = net.getBoundary()
    traj_df['x'], traj_df['y'] = net.convertLonLat2XY(traj_df['longitude'].values, traj_df['latitude'].values)
    # 单独删除某一列和某一行是没有意义的 只要超出边界就认为不合理吗？ 其实也可以
    
    # 删除df中越过边界的行 不参与最近边搜索的计算
    # 而且发现 虽然最小的坐标是0 但是其实可能就是几个孤立的案例 绝大部分的x y 比较小的坐标可能已经到达了2000多了
    
    traj_df.drop(index = traj_df.loc[(traj_df['x'] < xmin)].index, inplace = True)
    traj_df.drop(index = traj_df.loc[(traj_df['y'] < ymin)].index, inplace = True)
    traj_df.drop(index = traj_df.loc[(traj_df['x'] > xmax)].index, inplace = True)
    traj_df.drop(index = traj_df.loc[(traj_df['y'] > ymax)].index, inplace = True)
    
    for line_id in set(traj_df['line_id'].values):
        trace = []
        small_df = traj_df.loc[traj_df['line_id']==line_id] # 提取出来对应 bus id的df 
        # 但是由于要写循环 所以把他的index 重新从0开始
        small_df.reset_index(inplace = True)
        # 把这个bus id 对应的每一行的x y 都写进trace 中 让他查找
        for i in range(small_df.shape[0]):
            # 注意：原始的表格中的轨迹就是按照顺序的一行一行
            trace_step = [small_df.loc[i,'x'], small_df.loc[i,'y']] #每一个轨迹点
            trace.append(trace_step)
        edges = sumolib.route.mapTrace(trace, net, map_trace_radius, verbose=False, airDistFactor=2, fillGaps=0, gapPenalty=-1, debug=False)
        # 返回的数据类型示例：是一个元组 他自己带每个 edge 的 id 还有对应的 from to 等信息 本身的路线肯定就是联通的
        '''
        (<edge id="3532" from="1550" to="1551"/>,
          <edge id="4716" from="2275" to="2276"/>),
        '''
        edge_list = []
        if len(edges) > 0:
            for item in edges:
                edge = item.getID() # 取出来edge id
                edge_list.append(edge) # 就是这条公交线路对应的所有的edges的id
        # 否则这条线路就对应了一个空的列表 因为edge list 没有添加任何元素
        #print(line_id, list(set(edge_list)))  
        # print(line_id, 'finished')
        line_trace_dict[line_id] = list(set(edge_list)) # 线路的字典 每个id对应添加一个list 注意在之后引用的时候先判断轨迹列表是否非空
    return line_trace_dict

def generate_raw_ptstops(df_simplified, length):
    ''' 生成busStops.xml 为了使用ptlines2flows 统一放在最外侧 
    统一放在最外侧车道 lane 为 edge_0'''
    s = '''<?xml version="1.0" encoding="UTF-8"?>\n<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n'''    
    for i in range(df_simplified.shape[0]):
        station_id = df_simplified.loc[i, 'station_id'] #这个地方是需要使用id_lng_lat的索引 不用station_id
        station_name = df_simplified.loc[i, 'station_name']
        edge = df_simplified.loc[i, 'edge']
        offset = df_simplified.loc[i, 'offset']
        lane = 0 # lane 只可以放在最外侧 否则报错
        s1 = '    <busStop id="{}" lane="{}_{}" startPos="{}" endPos="{}" name="{}" friendlyPos="1"/>\n'.format(station_id, edge, lane, offset, offset+length, station_name)
        s = s + s1
    s = s + '''</additional>'''
    return s

def generate_ptstops(df_simplified, length):
    ''' 真正寻找合适的车道 而不是把他放在全部最外侧车道：只用于最后的仿真  不能用于ptlines2flows'''
    s = '''<?xml version="1.0" encoding="UTF-8"?>\n<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n'''    
    for i in range(df_simplified.shape[0]):
        station_id = df_simplified.loc[i, 'station_id'] #这个地方是需要使用id_lng_lat的索引 不用station_id
        station_name = df_simplified.loc[i, 'station_name']
        edge = df_simplified.loc[i, 'edge']
        offset = df_simplified.loc[i, 'offset']
        lane = df_simplified.loc[i,'lane']# lane 只可以放在最外侧 否则报错
        s1 = '    <busStop id="{}" lane="{}_{}" startPos="{}" endPos="{}" name="{}" friendlyPos="1"/>\n'.format(station_id, edge, lane, offset, offset+length, station_name)
        s = s + s1
    s = s + '''</additional>'''
    return s

def generate_ptlines(df, duration):
    '''生成busLines.xml（不含轨迹）'''
     # line_name_list 只是用于显示一下所有的站点

    line_name_list = sorted(set(df['line_name'].values))
    # print('exsiting bus lines:{}'.format(line_name_list)) # 显示出来所有存在的 bus id list
    
    s = '''<?xml version="1.0" encoding="UTF-8"?>\n<ptLines xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/ptlines_file.xsd">\n'''
    line_id_list = set(df['line_id'].values) # 这个是实际的索引用的id
    for line_id in line_id_list:
        line_name = df.loc[df['line_id'] == line_id]['line_name'].values[0] # 取第一个的名称即可
        small_df = df.loc[df['line_id'] == line_id, :]
        small_df.reset_index(inplace=True) #方便循环的时候索引index值
        small_df.sort_values(by = 'station_sequence', ascending = True, inplace = True) # 加一道保险 确认这个确实是按照先后顺序走的
        s1 = '    <ptLine id="{}" name="{}" line="{}" type="bus" vClass="bus" completeness="1.00">\n'.format(line_id, line_name, line_id)
        s = s + s1
        for i in range(small_df.shape[0]):
            station_id = small_df.loc[i, 'station_id'] 
            s2 = '        <busStop id="{}" duration="{}"/>\n'.format(station_id, duration)
            s = s + s2
        s = s + '    </ptLine>\n'
    s = s + '''</ptLines>'''
    return s

def generate_ptlines_with_trace(bus_stop_df, line_trace_dict, duration): 
    '''这个是已知要按照 map trace 走下去的写法 但是有点冗余
    核心就是在ptlines里面加上对应的route'''
    
    # line_name_list 只是用于显示一下所有的站点
    line_name_list = sorted(set(bus_stop_df['line_name'].values))
    # print('exsiting bus lines:{}'.format(line_name_list)) # 显示出来所有存在的 bus id list
    
    s = '''<?xml version="1.0" encoding="UTF-8"?>\n<ptLines xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/ptlines_file.xsd">\n'''
    line_id_list = set(bus_stop_df['line_id'].values) # 这个是实际的索引用的id
    for line_id in line_id_list:
        # 开头：引入id & name
        line_name = bus_stop_df.loc[bus_stop_df['line_id'] == line_id]['line_name'].values[0] # 取第一个的名称即可
        s1 = '<ptLine id="{}" name="{}" line="{}" type="bus" vClass="bus" completeness="1.00">\n'.format(line_id, line_name, line_id)
        s = s + s1
        
        if line_id in line_trace_dict.keys(): # 判断在traj_df 中存在有这条线路的ID
            # 引入trace:
            trace = line_trace_dict[line_id]
            if len(trace) > 0:
                s2 = ''
                for edge in trace:
                    s2 = s2 + edge + ' '
                s2 = s2.rstrip()
                s3 = '    <route edges="{}" id="{}"/>\n'.format(s2, line_id)
                s = s +  s3
        # 否则的话：比如 line_id 不在traj_df中 或者 虽然有 但是没匹配成功路径 则不管他 不写入文件
        
        # 准备 每一个bus stop 的 df 生成xml
        small_df = bus_stop_df.loc[bus_stop_df['line_id'] == line_id, :]
        small_df.reset_index(inplace=True) #方便循环的时候索引index值
        small_df.sort_values(by = 'station_sequence', ascending = True, inplace = True) # 加一道保险 确认这个确实是按照先后顺序走的
        for i in range(small_df.shape[0]):
            station_id = small_df.loc[i, 'station_id'] # 这个地方还是要用新的索引格式
            s4 = '      <busStop id="{}" duration="{}"/>\n'.format(station_id, duration)
            s = s + s4
        s = s + '</ptLine>\n'
    s = s + '''</ptLines>'''
    return s

def write_xml(s, path):
    with open(path, 'w+', encoding='utf-8') as f:
        f.write(s)

def mapTrace(net_path, bus_stop_path, outputpath = '../tw_rdc_case/output_background', vType = 'bus', bus_stop_search_radius=10, bus_stop_length=20, stop_duration=20, merge_threshold = 20, **kwargs):
    '''
    net_path: 路网文件路径
    bus_stop_path: 公交站点csv文件路径
    vType: 'bus/metro' 这个主要用于道路属性的搜索 使它放在合适的edge&lane上
    bus_stop_length: 公交站长度(m)
    stop_duration: 停靠时间(s)
    bus_stop_search_radius: 公交站点的邻边搜索半径(m)
    merge_threshold: 合并相邻公交站点的距离 如果输入小于0的数（如-1）则不合并
    **kwargs: 如果要匹配公交轨迹 需要传入一个traj_df 参与匹配 读入轨迹文件的那个路径 当然 一旦传入了traj_path 就认为是要匹配公交路径了
    **{'traj_path': 'all_traj_wgs84.csv', 'map_trace_radius': map_trace_radius}
    '''
    net = read_sumo_net(net_path)
    # df 就是 带有 bus_stop信息的全文件
    df = pd.read_csv(bus_stop_path, encoding = 'utf-8')
    all_edge_list, all_dist_list = find_nearest_edge(net, df, bus_stop_search_radius, vType) # 原有的df 加了两列 edge distance
    df['edge'] = all_edge_list
    df['distance'] = all_dist_list
    # 储存最原始的数据表格 包括每一行的查询信息
    df.to_csv('raw.csv', index=0, encoding = 'utf-8')
    
    # 实在搜索不到 或者超出路网边界的站点 不保留
    df.drop(index = df.loc[df['edge'] == 'None align direction', :].index, inplace = True)
    df.drop(index = df.loc[df['edge'] == 'None nearest edge', :].index, inplace = True)
    df.drop(index = df.loc[df['edge'] == 'Exceed boundary', :].index, inplace = True)
    
    # 转换为局部坐标 计算偏心距（站点该放在edge上哪个位置）
    df['x'], df['y'] = net.convertLonLat2XY(df['longitude'].values, df['latitude'].values)
    offset_list = cal_offset(net, df) # 这个函数中 已经reset_index了 所以drop掉的index不对应的问题也可以解决
    df['offset'] = offset_list

    df = find_candidate_lane(net, df, vType) #多加了一列lane 记录公交站的合适的车道
    
    # 合并站点
    # 这边还要注意的一点是 sumo不可以重复声明一个站点 所以需要做一下去重
    if merge_threshold > 0:
        df = merge_stations(df, merge_threshold)
        df_simplified = df.drop_duplicates(subset='station_id')
        df_simplified.reset_index(inplace = True) # 因为下面要遍历 因此还需要重新reset 一下index值
    
    df.to_csv('../tw_rdc_case/cache/busLines.csv', index=0, encoding = 'utf-8')
    # 生成lane为0的stops.xml 用于ptlines2flows
    s0 = generate_raw_ptstops(df_simplified, bus_stop_length) 
    write_xml(s0, '../tw_rdc_case/cache/busStops_raw.xml')
    # 生成真实lane的stops.xml 用于final simulation
    s1 = generate_ptstops(df_simplified, bus_stop_length)  
    write_xml(s1, outputpath + '/busStops.xml')
    
    # 如果要生成traj_df的文件 走这边
    if 'traj_path' in kwargs.keys(): 
        traj_df = pd.read_csv(kwargs['traj_path'], encoding = 'utf-8')
        line_trace_dict = find_map_trace(net, traj_df, kwargs['map_trace_radius'])
        s2 = generate_ptlines_with_trace(df, line_trace_dict, stop_duration)
    else:
        s2 = generate_ptlines(df, stop_duration) #这个是用原来总的DataFrame 因为要建立 线路-站点的映射关系
    
    write_xml(s2, '../tw_rdc_case/cache/busLines.xml')

# main('F:/merge/merge/bus/s1/osm.net.xml', 'F:/merge/merge/bus/s1/all_stops_wgs84.csv', vType='bus', bus_stop_search_radius=20,
#      bus_stop_length = 20, stop_duration=20, merge_threshold = 40)