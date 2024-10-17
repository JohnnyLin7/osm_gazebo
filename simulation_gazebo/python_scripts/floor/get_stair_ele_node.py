# Last Modified by Jiajie， 24.7.11
    # 读取osm，找出所有的 area 中 osmAG:area_usage == stairs && elevator 的area的node的坐标
    # 转换到gazebo世界坐标系下的坐标
    # 输出为一个xml文件： stairs_elevators.xml  

import xml.etree.ElementTree as ET
import json
from xml.dom import minidom

# 配置文件路径，包含坐标转换参数
config_path = '/home/johnnylin/fujing_osm/src/simulation_gazebo/config/config.json'

# 读取配置文件以获取坐标转换参数
with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    transition_osm = (config['osm_utm_transform']['x'], config['osm_utm_transform']['y'])

def transform_coordinates(x, y):
    """Apply the transformation to the coordinates."""
    return x - transition_osm[0], y - transition_osm[1]

def save_to_xml(areas, output_file):
    """Save extracted areas and nodes to an XML file in a pretty format."""
    root = ET.Element('OSMAreas')
    for way_id, info in areas.items():
        way_elem = ET.SubElement(root, 'way', id=way_id, usage=info['usage'])
        for node in info['nodes']:
            ET.SubElement(way_elem, 'node', x=str(node[0]), y=str(node[1]))

    # 使用 ElementTree 生成 XML 结构
    tree = ET.ElementTree(root)
    
    # 使用 minidom 转换 ElementTree 的输出为美化后的字符串
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")  # 指定缩进为四个空格

    # 写入文件
    with open(output_file, 'w') as output:
        output.write(pretty_xml)

def extract_coordinates(input_file):
    """Extract and transform coordinates from specified 'way' elements, preserving their structure."""
    tree = ET.parse(input_file)
    root = tree.getroot()
    node_coordinates = {}  # Dictionary to hold node ID and transformed coordinates

    # First, collect all node coordinates
    for node in root.findall('node'):
        node_id = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        # Apply transformation
        transformed_x, transformed_y = transform_coordinates(x, y)
        node_coordinates[node_id] = (transformed_x, transformed_y)
        # print("find nodes:", "node id:", node_id, "x:", transformed_x, "y:", transformed_y)

    # Now, process the ways
    results = {}
    for way in root.findall('way'):
            area_usage_tag = way.find("tag[@k='osmAG:area_usage'][@v='stairs']") 
            if area_usage_tag is not None:
                print("find stairs!")
                way_id = way.get('id')  # Get the ID of the way
                area_nodes = []
                for nd in way.findall('nd'):
                    node_id = nd.get('ref')
                    if node_id in node_coordinates:
                        area_nodes.append(node_coordinates[node_id])
                results[way_id] = {
                    'usage': area_usage_tag.get('v'),
                    'nodes': area_nodes
                }
            area_usage_tag = way.find("tag[@k='osmAG:area_usage'][@v='elevator']") 
            if area_usage_tag is not None:
                print("find elevator!")
                way_id = way.get('id')  # Get the ID of the way
                area_nodes = []
                for nd in way.findall('nd'):
                    node_id = nd.get('ref')
                    if node_id in node_coordinates:
                        area_nodes.append(node_coordinates[node_id])
                results[way_id] = {
                    'usage': area_usage_tag.get('v'),
                    'nodes': area_nodes
                }
    return results

if __name__ == '__main__':
    input_osm_file = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_utm_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'  # 替换为你的 OSM 文件路径
    output_xml_file = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/stairs_elevators.xml'  # Replace with desired output XML file path
    areas = extract_coordinates(input_osm_file)
    save_to_xml(areas, output_xml_file)
