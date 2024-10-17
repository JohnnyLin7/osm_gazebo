# Last Modified by Jiajie, Failed to generate correct door and its joint urdf, to let them rotate in gazebo.
import xml.etree.ElementTree as ET
from xml.dom import minidom
import math
import json
import map_drawer

# 加载配置文件
with open('/home/johnnylin/fujing_osm/src/simulation_gazebo/config/config.json', 'r') as config_file:
    config = json.load(config_file)
transition_osm = (config['osm_utm_transform']['x'], config['osm_utm_transform']['y'])

# 将XML元素转化为格式化的字符串
def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def add_material(robot, name, rgba):
    material = ET.SubElement(robot, 'material', name=name)
    color = ET.SubElement(material, 'color')
    color.set('rgba', rgba)

def rotate_door(x, y, angle_deg, pivot_x, pivot_y):
    angle_rad = math.radians(int(angle_deg))
    x_translated = x - pivot_x
    y_translated = y - pivot_y
    x_rotated = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad)
    y_rotated = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad)
    x_final = x_rotated + pivot_x
    y_final = y_rotated + pivot_y
    return (x_final, y_final)

def generate_doors_urdf(areas):
    robot = ET.Element('robot', name='doors')
    door_name_set = set()

    # 添加根节点
    base_link = ET.SubElement(robot, 'link', name='base_link')

    # 添加材料定义
    add_material(robot, 'Green', '0 1 0 1')
    add_material(robot, 'Red', '1 0 0 1')

    for area_name, area_data in areas.items():
        for passages_data in area_data['passages'].items():
            passage_data = passages_data[1]
            passage_id = passage_data['passage_id']
            passage_type = passage_data['passage_type']
            passage_name = passage_data['name']
            passage_degree = passage_data['degree']
            coordinates = passage_data['coordinates']
            start = coordinates[0]
            end = coordinates[1 % len(coordinates)]

            center_x = (start[0] + end[0]) / 2 - transition_osm[0]
            center_y = (start[1] + end[1]) / 2 - transition_osm[1]
            name = f"door_{center_x:.1f}_{center_y:.1f}"
            pivot_name = f"pivot_{name}"

            if name in door_name_set:
                continue
            door_name_set.add(name)

            door_start = [start[0] - transition_osm[0], start[1] - transition_osm[1]]
            door_rotated = rotate_door(end[0] - transition_osm[0], end[1] - transition_osm[1], passage_degree, door_start[0], door_start[1])
            length = math.sqrt((door_rotated[0] - door_start[0])**2 + (door_rotated[1] - door_start[1])**2)
            angle = math.atan2(door_rotated[1] - door_start[1], door_rotated[0] - door_start[0])
            center_z = 1.5  # Assume door height is 3m

            pivot_x, pivot_y = door_start[0], door_start[1]  # 使用门的起始点作为铰链位置
            # Create URDF elements for the door pivot and door
            pivot_link = ET.SubElement(robot, 'link', name=pivot_name)
            pivot_origin = ET.SubElement(pivot_link, 'origin', xyz=f"{pivot_x} {pivot_y} {center_z}", rpy="0 0 0")

            link = ET.SubElement(robot, 'link', name=name)
            visual = ET.SubElement(link, 'visual')
            visual_origin = ET.SubElement(visual, 'origin', xyz="0 0 1.5", rpy="0 0 0")
            geometry = ET.SubElement(visual, 'geometry')
            box = ET.SubElement(geometry, 'box', size=f"{length} 0.1 3")

            material = ET.SubElement(visual, 'material', name='Red' if passage_degree == '0' else 'Green')
            script = ET.SubElement(material, 'script')
            uri = ET.SubElement(script, 'uri')
            uri.text = "file://media/materials/scripts/gazebo.material"
            script_name = ET.SubElement(script, 'name')
            script_name.text = 'Gazebo/Green' if passage_degree != '0' else 'Gazebo/Red'

            collision = ET.SubElement(link, 'collision')
            collision_origin = ET.SubElement(collision, 'origin', xyz="0 0 1.5", rpy="0 0 0")
            collision_geometry = ET.SubElement(collision, 'geometry')
            collision_box = ET.SubElement(collision_geometry, 'box', size=f"{length} 0.1 3")

            # Create joint for the pivot link with base_link as parent
            pivot_joint = ET.SubElement(robot, 'joint', name=f"{pivot_name}_joint", type='fixed')
            parent = ET.SubElement(pivot_joint, 'parent', link='base_link')
            child = ET.SubElement(pivot_joint, 'child', link=pivot_name)
            origin = ET.SubElement(pivot_joint, 'origin', xyz=f"{pivot_x} {pivot_y} {center_z}", rpy="0 0 0")

            # Create joint for the door link with pivot_link as parent
            door_joint = ET.SubElement(robot, 'joint', name=f"{name}_joint", type='revolute')
            parent = ET.SubElement(door_joint, 'parent', link=pivot_name)
            child = ET.SubElement(door_joint, 'child', link=name)
            origin = ET.SubElement(door_joint, 'origin', xyz="0 0 0", rpy="0 0 0")
            axis = ET.SubElement(door_joint, 'axis', xyz="0 0 1")
            limit = ET.SubElement(door_joint, 'limit', lower="-1.5708", upper="1.5708", effort="10", velocity="1")

    return robot

if __name__ == '__main__':
    file_name = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/ShanghaiTech_merge_F2_corrected_id2name_outside_structure_utm.osm'
    areas_tree = ET.parse(file_name)
    areas = map_drawer.parse_osm(areas_tree)

    robot = generate_doors_urdf(areas)

    pretty_xml = prettify(robot)
    with open('doors.urdf', 'w') as urdf_file:
        urdf_file.write(pretty_xml)
