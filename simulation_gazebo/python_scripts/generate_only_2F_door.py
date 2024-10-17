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
close_door_color = 'Gazebo/Red'
level_gap = 3.2  # 高度差

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def rotate_door(x, y, angle_deg, pivot_x, pivot_y):
    angle_rad = math.radians(int(angle_deg))

    x_translated = x - pivot_x
    y_translated = y - pivot_y
    
    x_rotated = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad)
    y_rotated = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad)
    
    x_final = x_rotated + pivot_x
    y_final = y_rotated + pivot_y
    
    return (x_final, y_final)

def add_door_with_joint(world_element, start_, end_, height, thickness, color, wall_name_set, door_name_set, door_angle, z_offset=0):
    start = list(start_)
    end = list(end_)

    start[0] = start_[0] - transition_osm[0]
    start[1] = start_[1] - transition_osm[1]
    end[0] = end_[0] - transition_osm[0]
    end[1] = end_[1] - transition_osm[1]

    length = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

    if length == 0:
        print('Zero length segment')
        return

    door_rotated = rotate_door(end[0], end[1], door_angle, start[0], start[1])

    pivot_name = f"pivot_{start[0]:.1f}_{start[1]:.1f}_{z_offset}"
    if pivot_name in wall_name_set:
        return
    wall_name_set.add(pivot_name)

    pivot_model = ET.SubElement(world_element, 'model', name=pivot_name)
    pivot_static = ET.SubElement(pivot_model, 'static')
    pivot_static.text = 'true'
    pivot_pose = ET.SubElement(pivot_model, 'pose')
    pivot_pose.text = f"{start[0]} {start[1]} {height / 2 + z_offset} 0 0 0"

    pivot_link = ET.SubElement(pivot_model, 'link', name='pivot_link')
    pivot_visual = ET.SubElement(pivot_link, 'visual', name='pivot_visual')
    pivot_geometry = ET.SubElement(pivot_visual, 'geometry')
    pivot_box = ET.SubElement(pivot_geometry, 'box')
    pivot_size = ET.SubElement(pivot_box, 'size')
    pivot_size.text = f"{thickness} {thickness} {height}"

    door_name = f"door_{start[0]:.1f}_{start[1]:.1f}_{z_offset}"
    if door_name in door_name_set:
        return
    door_name_set.add(door_name)

    door_model = ET.SubElement(world_element, 'model', name=door_name)
    door_static = ET.SubElement(door_model, 'static')
    door_static.text = 'false'
    door_pose = ET.SubElement(door_model, 'pose')
    door_pose.text = f"{(start[0] + door_rotated[0]) / 2} {(start[1] + door_rotated[1]) / 2} {height / 2 + z_offset} 0 0 0"

    door_link = ET.SubElement(door_model, 'link', name='door_link')
    door_gravity = ET.SubElement(door_link, 'gravity')
    door_gravity.text = 'false'
    door_visual = ET.SubElement(door_link, 'visual', name='door_visual')
    door_geometry = ET.SubElement(door_visual, 'geometry')
    door_box = ET.SubElement(door_geometry, 'box')
    door_size = ET.SubElement(door_box, 'size')
    door_size.text = f"{length} {thickness} {height}"

    door_material = ET.SubElement(door_visual, 'material')
    door_script = ET.SubElement(door_material, 'script')
    door_uri = ET.SubElement(door_script, 'uri')
    door_uri.text = "file://media/materials/scripts/gazebo.material"
    door_script_name = ET.SubElement(door_script, 'name')
    door_script_name.text = color

    joint_name = f"joint_{start[0]:.1f}_{start[1]:.1f}_{z_offset}"
    joint = ET.SubElement(world_element, 'joint', name=joint_name, type='revolute')
    parent = ET.SubElement(joint, 'parent')
    parent.text = f"{pivot_model.attrib['name']}::pivot_link"
    child = ET.SubElement(joint, 'child')
    child.text = f"{door_model.attrib['name']}::door_link"
    axis = ET.SubElement(joint, 'axis')
    xyz = ET.SubElement(axis, 'xyz')
    xyz.text = '0 0 1'
    limit = ET.SubElement(axis, 'limit')
    lower = ET.SubElement(limit, 'lower')
    lower.text = '0'
    upper = ET.SubElement(limit, 'upper')
    upper.text = "1.5708"

def generated_by_areas(areas, world_element, level):
    passage_id_set = set()
    wall_name_set = set()
    door_name_set = set()
    z_offset = (level - 1) * level_gap
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
                add_door_with_joint(world_element, door_start, door_rotated, wall_height, wall_thickness, close_door_color, wall_name_set, door_name_set, int(passage_degree), z_offset)
            else:
                add_door_with_joint(world_element, door_start, door_rotated, wall_height, wall_thickness, door_color, wall_name_set, door_name_set, int(passage_degree), z_offset)

if __name__ == '__main__':
    file_name='/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_utm_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'

    areas_tree = ET.parse(file_name)

    areas = map_drawer_jiajie.parse_osm(areas_tree)

    world = ET.Element('sdf', version='1.6')
    world_element = ET.SubElement(world, 'world', name='default')

    generated_by_areas(areas, world_element, level=1)

    generated_by_areas(areas, world_element, level=2)

    pretty_xml = prettify(world)
    with open('osm_fujing_edited_2F_only_door_joint.world', 'w') as world_file:
        world_file.write(pretty_xml)
