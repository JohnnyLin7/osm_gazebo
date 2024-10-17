import xml.etree.ElementTree as ET
from xml.dom import minidom
import math
import os
import json
import map_drawer_jiajie

# 加载配置文件
with open('/home/johnnylin/fujing_osm/src/simulation_gazebo/config/config.json', 'r') as config_file:
    config = json.load(config_file)
transition_osm = (config['osm_utm_transform']['x'], config['osm_utm_transform']['y'])

# 一些参数
wall_height = 3
wall_thickness = 0.1
wall_color = 'Gazebo/White'
level_gap = 3.2  # 高度差

# 将XML元素转化为格式化的字符串
def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# 旋转门函数
def rotate_door(x, y, angle_deg, pivot_x, pivot_y):
    angle_rad = math.radians(int(angle_deg))

    x_translated = x - pivot_x
    y_translated = y - pivot_y
    
    x_rotated = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad)
    y_rotated = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad)
    
    x_final = x_rotated + pivot_x
    y_final = y_rotated + pivot_y
    
    return (x_final, y_final)

# 添加墙段
def add_wall_segment(world_element, start_, end_, height, thickness, color, wall_name_set, z_offset=0):
    start = list(start_)
    end = list(end_)

    # 转换坐标
    start[0] = start_[0] - transition_osm[0]
    start[1] = start_[1] - transition_osm[1]
    end[0] = end_[0] - transition_osm[0]
    end[1] = end_[1] - transition_osm[1]
    
    length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)

    if length == 0:
        print('Zero length segment')
        return
    
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    center_x = (start[0] + end[0]) / 2
    center_y = (start[1] + end[1]) / 2
    center_z = height / 2 + z_offset

    name = f"wall_{center_x:.1f}_{center_y:.1f}_{z_offset}"
    if name in wall_name_set:
        return
    wall_name_set.add(name)
    
    model = ET.SubElement(world_element, 'model', name=f'{name}_link')
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

# 生成世界文件中的区域
def generated_by_areas(areas, world_element, level):
    wall_name_set = set()
    z_offset = (level - 1) * level_gap

    # 添加门的名称到 wall_name_set 中，以确保不会重复添加与门重叠的墙壁
    for area_name, area_data in areas.items():
        for passages_data in area_data['passages'].items():
            passage_data = passages_data[1]
            coordinates = passage_data['coordinates']
            start = coordinates[0]
            end = coordinates[1 % len(coordinates)]
            center_x = (start[0] + end[0]) / 2 - transition_osm[0]
            center_y = (start[1] + end[1]) / 2 - transition_osm[1]
            name = f"wall_{center_x:.1f}_{center_y:.1f}_{z_offset}"
            wall_name_set.add(name)
    
    # 添加房间墙壁
    for area_name, area_data in areas.items():
        nodes = area_data['nodes']
        for i in range(len(nodes) - 1):
            start = nodes[i]
            end = nodes[(i + 1) % len(nodes)]
            add_wall_segment(world_element, start, end, wall_height, wall_thickness, wall_color, wall_name_set, z_offset)

if __name__ == '__main__':
    file_name = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_utm_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'
    areas_tree = ET.parse(file_name)
    areas = map_drawer_jiajie.parse_osm(areas_tree)

    world = ET.Element('sdf', version='1.6')
    world_element = ET.SubElement(world, 'world', name='default')

    # 生成第一层
    generated_by_areas(areas, world_element, level=1)

    # 生成第二层
    generated_by_areas(areas, world_element, level=2)

    pretty_xml = prettify(world)
    with open('osm_fujing_edited_2F_no_door.world', 'w') as world_file:
        world_file.write(pretty_xml)
