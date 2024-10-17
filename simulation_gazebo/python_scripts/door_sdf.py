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

# 生成门的SDF
def generate_doors_sdf(areas):
    sdf = ET.Element('sdf', version='1.6')
    world = ET.SubElement(sdf, 'world', name='default')
    door_name_set = set()

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

            # Create SDF elements for the door and its pivot
            model = ET.SubElement(world, 'model', name=name)
            static = ET.SubElement(model, 'static')
            static.text = 'false'
            pose = ET.SubElement(model, 'pose')
            pose.text = f"{pivot_x} {pivot_y} {center_z} 0 0 {angle}"

            link_pivot = ET.SubElement(model, 'link', name=pivot_name)
            collision_pivot = ET.SubElement(link_pivot, 'collision', name='collision')
            geometry_pivot = ET.SubElement(collision_pivot, 'geometry')
            box_pivot = ET.SubElement(geometry_pivot, 'box')
            size_pivot = ET.SubElement(box_pivot, 'size')
            size_pivot.text = "0.1 0.1 0.1"
            visual_pivot = ET.SubElement(link_pivot, 'visual', name='visual')
            geometry_visual_pivot = ET.SubElement(visual_pivot, 'geometry')
            box_visual_pivot = ET.SubElement(geometry_visual_pivot, 'box')
            size_visual_pivot = ET.SubElement(box_visual_pivot, 'size')
            size_visual_pivot.text = "0.1 0.1 0.1"

            link_door = ET.SubElement(model, 'link', name=name)
            visual_door = ET.SubElement(link_door, 'visual', name='visual')
            pose_door_visual = ET.SubElement(visual_door, 'pose')
            pose_door_visual.text = "0 0 1.5 0 0 0"
            geometry_door = ET.SubElement(visual_door, 'geometry')
            box_door = ET.SubElement(geometry_door, 'box')
            size_door = ET.SubElement(box_door, 'size')
            size_door.text = f"{length} 0.1 3"
            material = ET.SubElement(visual_door, 'material')
            script = ET.SubElement(material, 'script')
            uri = ET.SubElement(script, 'uri')
            uri.text = "file://media/materials/scripts/gazebo.material"
            script_name = ET.SubElement(script, 'name')
            script_name.text = 'Gazebo/Green' if passage_degree != '0' else 'Gazebo/Red'

            collision_door = ET.SubElement(link_door, 'collision', name='collision')
            pose_door_collision = ET.SubElement(collision_door, 'pose')
            pose_door_collision.text = "0 0 1.5 0 0 0"
            collision_geometry_door = ET.SubElement(collision_door, 'geometry')
            collision_box_door = ET.SubElement(collision_geometry_door, 'box')
            collision_size_door = ET.SubElement(collision_box_door, 'size')
            collision_size_door.text = f"{length} 0.1 3"

            # Create joint for the door
            joint = ET.SubElement(model, 'joint', name=f"{name}_joint", type='revolute')
            parent = ET.SubElement(joint, 'parent')
            parent.text = pivot_name
            child = ET.SubElement(joint, 'child')
            child.text = name
            axis = ET.SubElement(joint, 'axis')
            xyz = ET.SubElement(axis, 'xyz')
            xyz.text = "0 0 1"
            limit = ET.SubElement(axis, 'limit')
            lower = ET.SubElement(limit, 'lower')
            lower.text = "-1.5708"
            upper = ET.SubElement(limit, 'upper')
            upper.text = "1.5708"
            effort = ET.SubElement(limit, 'effort')
            effort.text = "10"
            velocity = ET.SubElement(limit, 'velocity')
            velocity.text = "1"

            # Add plugin to control the door joint
            plugin = ET.SubElement(model, 'plugin', name=f"init_joint_control_{name}", filename="libJointControlPlugin.so")
            controller = ET.SubElement(plugin, 'controller', type="position")
            joint_name = ET.SubElement(controller, 'joint')
            joint_name.text = f"{name}_joint"
            target = ET.SubElement(controller, 'target')
            target.text = "1.0"
            pid_gains = ET.SubElement(controller, 'pid_gains')
            pid_gains.text = "1 0.1 0.01"

    return sdf

if __name__ == '__main__':
    file_name = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/ShanghaiTech_merge_F2_corrected_id2name_outside_structure_utm.osm'
    areas_tree = ET.parse(file_name)
    areas = map_drawer.parse_osm(areas_tree)

    sdf = generate_doors_sdf(areas)

    pretty_xml = prettify(sdf)
    with open('doors.sdf', 'w') as sdf_file:
        sdf_file.write(pretty_xml)
