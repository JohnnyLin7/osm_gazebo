import xml.etree.ElementTree as ET
from xml.dom import minidom
import math
import os
import process_osm
import map_drawer_jiajie
import map_handler
import json

with open('/home/johnnylin/fujing_osm/src/simulation_gazebo/config/config.json', 'r') as config_file:
    config = json.load(config_file)
transition_osm = (config['osm_utm_transform']['x'], config['osm_utm_transform']['y'])    

wall_height = 3
wall_thickness = 0.1
door_color = 'Gazebo/Green'
wall_color = 'Gazebo/White'
close_door_color = 'Gazebo/Red'
level_gap =3.2  # 高度差

# 将XML元素转化为格式化的字符串
def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# 计算各面墙的中心、长度和角度，并在gazebo世界中添加相应的墙壁模型
def add_wall_segment(world_element, start_, end_, height, thickness, color, wall_name_set, wall, z_offset=0):
    start = list(start_)
    end = list(end_)

    # 对起点和终点坐标平移转换，使用从配置文件中读取的"transition_osm"参数
    start[0] = start_[0] - transition_osm[0]
    start[1] = start_[1] - transition_osm[1]
    end[0] = end_[0] - transition_osm[0]
    end[1] = end_[1] - transition_osm[1]
    
    # 计算墙段的长度，使用欧几里德距离公式
    length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)

    # 检查墙段长度是否为零
    if length == 0:
        print('Zero length segment')
        return  # Avoid division by zero in case of zero-length segment
    
    # 计算墙段的中心、长度和角度，使用反正切函数计算角度
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    center_x = (start[0] + end[0]) / 2
    center_y = (start[1] + end[1]) / 2
    center_z = height / 2 + z_offset

    # 生成墙段的模型名称，并检查是否已经存在，避免重复添加
    name = f"wall_{center_x:.1f}_{center_y:.1f}_{z_offset}"
    if wall and name in wall_name_set:
        return
    wall_name_set.add(name)
    
    # 生成一个新的 model 元素，并设置其名称、静态属性、位置、链接、视觉和材质属性
    model = ET.SubElement(world_element, 'model', name=name)
    static = ET.SubElement(model, 'static')
    static.text = 'true'
    pose = ET.SubElement(model, 'pose')
    pose.text = f"{center_x} {center_y} {center_z} 0 0 {angle}"

    link = ET.SubElement(model, 'link', name='link')
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry = ET.SubElement(visual, 'geometry')
    box = ET.SubElement(geometry, 'box')
    size = ET.SubElement(box, 'size')
    size.text = f"{length} {thickness} {height}"

    material = ET.SubElement(visual, 'material')
    script = ET.SubElement(material, 'script')
    uri = ET.SubElement(script, 'uri')
    uri.text = "file://media/materials/scripts/gazebo.material"
    name = ET.SubElement(script, 'name')
    name.text = color

# 旋转门函数：根据给定的坐标、角度和旋转中心，返回旋转后的坐标
def rotate_door(x, y, angle_deg, pivot_x, pivot_y):
    angle_rad = math.radians(int(angle_deg))

    x_translated = x - pivot_x
    y_translated = y - pivot_y
    
    x_rotated = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad)
    y_rotated = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad)
    
    x_final = x_rotated + pivot_x
    y_final = y_rotated + pivot_y
    
    return (x_final, y_final)

def generated_by_areas(areas, world_element, level):
    passage_id_set = set()
    wall_name_set = set()
    door_name_set = set()
    z_offset = (level - 1) * level_gap
    min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')

    # add doors to world
    for area_name, area_data in areas.items():
        for passages_data in area_data['passages'].items():
            passage_data = passages_data[1]
            passage_id = passage_data['passage_id']
            passage_type = passage_data['passage_type']
            passage_name = passage_data['name']
            passage_degree = passage_data['degree']
            coordinates = passage_data['coordinates']
            centroid = passage_data['centroid']
            
            start = coordinates[0]
            end = coordinates[(1) % len(coordinates)]
            center_x = (start[0] + end[0]) / 2 - transition_osm[0]
            center_y = (start[1] + end[1]) / 2 - transition_osm[1]
            name = f"wall_{center_x:.1f}_{center_y:.1f}_{z_offset}"

            if name in door_name_set:
                continue
            wall_name_set.add(name)

            door_start = start
            door_end = end
            door_rotated = rotate_door(door_end[0], door_end[1], passage_degree, door_start[0], door_start[1])

            if passage_type == 'automatic':
                continue

            if passage_degree == '0':
                add_wall_segment(world_element, door_start, door_rotated, wall_height, wall_thickness, close_door_color, wall_name_set, False, z_offset)
            else:
                add_wall_segment(world_element, door_start, door_rotated, wall_height, wall_thickness, door_color, wall_name_set, False, z_offset)
            door_name_set.add(name)

    # add rooms to world
    for area_name, area_data in areas.items():
        nodes = area_data['nodes']
        for i in range(len(nodes) - 1):
            start = nodes[i]
            end = nodes[(i + 1) % len(nodes)]
            add_wall_segment(world_element, start, end, wall_height, wall_thickness, wall_color, wall_name_set, True, z_offset)


if __name__ == '__main__':
    file_name='/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_utm_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'

    # areas_tree 对象，利用 ElementTree 从 .osm文件加载并解析，作为XML文件的整个结构树
    areas_tree = ET.parse(file_name)

    # 调用 map_drawer 自定义模块的 parse_osm 函数，生成一个包含区域信息的字典 "areas"
    areas=map_drawer_jiajie.parse_osm(areas_tree)

    # Create a basic world template
    world = ET.Element('sdf', version='1.6')
    world_element = ET.SubElement(world, 'world', name='default')

    # 生成第一层
    generated_by_areas(areas, world_element, level=1)

    # 生成第二层
    generated_by_areas(areas, world_element, level=2)

    # Generate the world file content in a pretty format
    pretty_xml = prettify(world)
    # Write the pretty XML to file
    with open('osm_fujing_edited_2F_no_door.world', 'w') as world_file:
        world_file.write(pretty_xml)