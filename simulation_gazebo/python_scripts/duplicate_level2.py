# Last Modified by Jiajie 24.7.04 
# copy all the ways of level 1 to level 2

# for osmAG:type == area, change its:
    # name
    # osmAG:parent
    # room_number

# for osmAG:areatype == passage, change its:
    # name
    # osmAG:from
    # osmAG:to
import xml.etree.ElementTree as ET
def generate_unique_id(existing_ids):
    new_id = max(existing_ids) + 1
    while new_id in existing_ids:
        new_id += 1
    return new_id

def update_room_info(tag):
    if tag.attrib['k'] == 'name':
        tag.set('v', tag.attrib['v'].replace("F1", "F2"))
    elif tag.attrib['k'] == 'osmAG:parent':
        tag.set('v', tag.attrib['v'].replace("F1", "F2"))
    elif tag.attrib['k'] == 'osmAG:room_number':
        tag.set('v', tag.attrib['v'].replace("-1", "-2"))

def update_passage_info(tag):
    if tag.attrib['k'] == 'name':
        tag.set('v', tag.attrib['v'].replace("F1", "F2"))
    elif tag.attrib['k'] == 'osmAG:from':
        tag.set('v', tag.attrib['v'].replace("F1", "F2"))
    elif tag.attrib['k'] == 'osmAG:to':
        tag.set('v', tag.attrib['v'].replace("F1", "F2"))

def duplicate_level_1_to_level_2(input_file, output_file):
    # 解析 XML 文件
    tree = ET.parse(input_file)
    root = tree.getroot()

    # 获取所有现有的ID
    existing_ids = {int(way.attrib['id']) for way in root.findall('way')}

    # 创建一个列表以存储新的元素
    new_elements = []

    # 遍历所有 'way' 元素，查找 'level' 标签为 1 的元素
    for way in root.findall('way'):
        level_1_found = False
        for tag in way.findall('tag'):
            if tag.attrib.get('k') == 'level' and tag.attrib.get('v') == '1':
                level_1_found = True
                break
        
        if level_1_found:
            # 创建一个副本
            new_way = ET.Element(way.tag)
            
            # 生成新的唯一ID
            new_id = generate_unique_id(existing_ids)
            existing_ids.add(new_id)
            new_way.set('id', str(new_id))
            new_way.set('action', 'modify')
            new_way.set('visible', 'true')
            
            for child in way:
                new_child = ET.Element(child.tag, child.attrib)
                if child.tag == 'tag' and child.attrib.get('k') == 'level':
                    new_child.set('v', '2')
                elif child.tag == 'tag' and way.find("./tag[@k='osmAG:type'][@v='area']") is not None:
                    update_room_info(new_child)
                elif child.tag == 'tag' and way.find("./tag[@k='osmAG:type'][@v='passage']") is not None:
                    update_passage_info(new_child)
                new_way.append(new_child)
            
            new_elements.append(new_way)

    # 将新元素添加到根元素
    for new_elem in new_elements:
        root.append(new_elem)

    # 将修改后的 XML 树写入输出文件
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    input_file = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/ShanghaiTech_merge_F2_corrected_id2name_outside_structure_new.osm'  # 替换为你的输入文件路径
    output_file = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/Jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'  # 替换为你的输出文件路径

    duplicate_level_1_to_level_2(input_file, output_file)
