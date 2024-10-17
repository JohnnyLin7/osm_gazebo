import xml.etree.ElementTree as ET
# from pyproj import Transformer
# from pyproj.transformer import Transformer
from collections import OrderedDict
import xml.dom.minidom as minidom
import re
from utility_map import *
import xmltodict
import json
import random
import copy
file_xml='../OSM/select.osm'
file_xml='../map_draw/topological_more_intersection.osm'
# file_xml='../map_draw/topological_medium_edited.osm'

output_file_path=file_xml[0:-4]+'_edited.osm'
output_file_path='../map_draw/edited_osm/topological_more_intersection.osm'
# 删除所有passage
def del_all_passage(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        # osmAG-tag的本质是键值对 : "key-value"
        if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'passage' for tag in way.findall('tag')):
            root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)


# remove empty way # 删除所有不包含标签 osmAG:type的way元素
def check_remove_way(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        if any(tag.get('k') == 'osmAG:type'  for tag in way.findall('tag')):
            continue
        else:
            root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)

# 删除包含标签 osmAG:parent 和 v值为 structure 的way元素
def remove_parent_and_structure(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        for tag in way.findall('tag'):
            if(tag.attrib['k']=='osmAG:parent'):
                way.remove(tag)
            if(tag.attrib['v']=='structure'):
                root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)

# check for 'half' passage(only one or none room connected to it)
def check_invalid_passage(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        from_=-10000000
        to_=-10000000
        for tag in way.findall('tag'):
            if(tag.attrib['k']=='osmAG:from'):
                from_=tag.attrib['v']
        # for tag in way.findall('tag'):
            if(tag.attrib['k']=='osmAG:to'):
                to_=tag.attrib['v']
        # for tag in way.findall('tag'):
            if(tag.attrib['k']=='osmAG:type' and tag.attrib['v']=='passage'):
                count=0
                for way_ in root.findall('way'):
                    if any(tag.get('v') == 'room' for tag in way_.findall('tag')):
                        for tag in way_.findall('tag'):
                            room_name='__'
                            if(tag.attrib['k']=='name') :
                                room_name=tag.attrib['v']
                            if room_name==from_ or room_name==to_:
                                count+=1
                    
                if(count<=1):
                    print(f'invalid passage found, from_={from_}, to_={to_}')
                    root.remove(way)

    tree.write(output_file,encoding='utf-8', xml_declaration=True)

# 规范化 "way" 元素的 ID， 使它们从 0 开始，并递增，连续编号
def normalize_id(input_file_path,output_file_path):
    tree = ET.parse(input_file_path)
    root = tree.getroot()
    min_id=0
    for way in root.findall('way'):
        # for tag in way.findall('tag'):
        id=way.attrib['id']
        if int(id)<min_id:
            min_id=int(id)
    for way in root.findall('way'):
        # if any(tag.get('v') == 'room' for tag in way.findall('tag')):
        id=way.attrib['id']
        way.set('id',str(int(id)-min_id))
        print(f'way id changed from {id} to {str(int(id)-min_id)}')
    tree.write(output_file_path,encoding='utf-8', xml_declaration=True)

# remove area that doesn't have a passage connected to it   # 删除没有连接到passage的区域
def remove_un_passage_area(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        #  means it is a room, passage doesn't have name tag
        exist=False
        for tag in way.findall('tag'):
            if tag.get('k') == 'name':
                name=tag.get('v')
                for way_ in root.findall('way'):
                    for tag_ in way_.findall('tag'):
                        if(tag_.get('k')=='osmAG:from' or tag_.get('k')=='osmAG:to'):
                            if name==tag_.get('v'):
                                exist=True
                if exist==False:
                    root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)

def remove_same_name_area(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        #  means it is a room, passage doesn't have name tag
        exist=False
        id=way.attrib['id']
        for tag in way.findall('tag'):
            if tag.get('k') == 'name':
                name=tag.get('v')
                for way_ in root.findall('way'):
                    id_=way_.attrib['id']
                    for tag_ in way_.findall('tag'):
                        if(tag_.get('k')=='name' ):
                            if name==tag_.get('v') and id!=id_:
                                exist=True
                if exist==True:
                    root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)




def remove_ref_in_area(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Find all 'nd' elements and remove the 'ref' attribute from each of them
    for way in root.findall('way'):
        # print(way.attrib['id'])
        for nd_element in way.findall("nd"):
        # for attribute in nd_element.attrib.copy():
            # print(nd_element.attrib)
            way.remove(nd_element)

    # Save the modified XML file
    # xml_string = ET.tostring(root, encoding='unicode', method='xml')
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
    
def cleanup_node(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for i,node in enumerate(root.findall('node')):
        # make its use less token
        # del node.attrib['action']
        # del node.attrib['visible']
        del node.attrib['lat']
        del node.attrib['lon']
        
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
  
def areaid2semantic(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        for tag in way.findall('tag'):
            if(tag.attrib['k']=='osmAG:from' or tag.attrib['k']=='osmAG:to' or tag.attrib['k']=='osmAG:parent'):
                id=tag.attrib['v']
                for way in root.findall('way'):
                    if(way.attrib['id']==id):
                        for tag_ in way.findall('tag'):
                            # name_element = tag_.find('name')
                            # Get the 'v' attribute value from the 'tag' element
                            if tag_.attrib['k']=='name':
                                print("setting from or to"+id+" to "+tag_.get('v'))
                                
                                tag.set('v',tag_.get('v'))
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
# del height,indoor,level,action, visible in way
def cleanup_way(input_file,output_file):
    # delete all ref node in way 
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        del way.attrib['action']
        del way.attrib['visible']
        for tag in way.findall('tag'):
            if(tag.attrib['k']=='height' or tag.attrib['k']=='indoor' or tag.attrib['k']=='level'):
                way.remove(tag)
            if tag.attrib['k']=='name' and any(tag.get('v') == 'passage' for tag in way.findall('tag')):
                way.remove(tag)
        for nd in way.findall('nd'):
            way.remove(nd)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
def del_all_parents(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        for tag in way.findall('tag'):
            if(tag.attrib['k']=='parent' or tag.attrib['k']=='osmAG:parent'):
                way.remove(tag)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
def del_all_passages(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for way in root.findall('way'):
        if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'passage' for tag in way.findall('tag')):
            root.remove(way)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
def del_all_node(input_file,output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    for node in root.findall('node'):
        root.remove(node)
    tree.write(output_file,encoding='utf-8', xml_declaration=True)
# def parent2semantic(input_file,output_file):
#     tree=ET.parse(input_file)
#     root=tree.getroot()
#     for way in root.findall('way'):
#         for tag in way.findall('tag'):
#             if(tag.attrib['k']=='parent' ):
def xml2json(xml_file,json_name):
    with open(xml_file, 'r') as file:
        xml_string = file.read()

    # Step 2: Convert XML to a Python dictionary
    dict_data = xmltodict.parse(xml_string)

    # Step 3: Convert the dictionary to a JSON string
    json_data = json.dumps(dict_data, indent=4)

    # Step 4: Write the JSON data to a file (optional)
    with open(json_name, 'w') as json_file:
        json_file.write(json_data)


def transform_json(input_file_path):
    with open(input_file_path, 'r') as file:
        json_data = json.load(file)
    # Extracting the ways from the input JSON
    ways = json_data["osm"]["way"]

    # Separating ways into rooms and passages
    rooms, passages, others = [], [], []
    for way in ways:
        tags = way.get("tag", [])
        name_tag = next((tag for tag in tags if tag["@k"] == "name"), None)
        is_room = any(tag["@v"] == "room" for tag in tags)
        is_passage = any(tag["@v"] == "passage" for tag in tags)

        if name_tag:
            # Creating a new structure for ways with a name
            new_way = {"name": name_tag["@v"], "tag": [{"@k": "id", "@v": way["@id"]}] + [tag for tag in tags if tag["@k"] != "name"]}
            if is_room:
                rooms.append(new_way)
            elif is_passage:
                passages.append(new_way)
            else:
                others.append(new_way)
        else:
            # Keeping the original structure for ways without a name
            others.append(way)

    # Combining the lists with rooms first, then passages, then others
    transformed_ways = rooms + passages + others

    # Returning the transformed JSON
    return {
        "osm": {
            "@version": json_data["osm"].get("@version", ""),
            "@generator": json_data["osm"].get("@generator", ""),
            "way": transformed_ways
        }
    }
def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def add_element_with_indent(parent, tag, attributes={}, indent_level=1, is_last=False):
    """
    Adds a new element to the parent with specified indentation and attributes.
    Also handles newline and indentation for a prettified output.
    """
    # Calculate indent spaces
    indent_space = '  ' * indent_level
    newline_and_indent = '\n' + indent_space
    newline = '\n' if is_last else '\n' + '  ' * (indent_level - 1)
    
    # Add newline and indent before the element
    parent.tail = (parent.tail if parent.tail else '') + newline_and_indent
    new_element = ET.SubElement(parent, tag, attrib=attributes)
    
    # Set tail for the new element for proper formatting
    new_element.tail = newline

def double_passages(input_file, output_file):
    with open(input_file, 'r') as file:
        xml_data = file.read()

    root = ET.fromstring(xml_data)
    xml_str = ET.tostring(root, encoding='unicode')
    highest_id = max([int(way.get('id')) for way in root.findall('way')], default=0)

    # List to accumulate new 'way' elements as strings
    new_way_strings = []

    for way_element in root.findall('way'):
        highest_id += 1
        way_id = str(highest_id)
        
        # Initialize parts of the new 'way' string including opening tag
        new_way_str = f'  <way id="{way_id}">\n'

        # Sort the tags to ensure 'from' comes first, then 'osmAG:type', then 'to'
        tags_dict = {}
        for tag in way_element.findall('tag'):
            tags_dict[tag.get('k')] = tag.get('v')

        # Ensure both 'from' and 'to' tags are present, else skip to the next 'way'
        if 'osmAG:' in tags_dict and 'osmAG:' in tags_dict:
            # Manually construct tag strings with proper formatting
            new_way_str += f'    <tag k="osmAG:from" v="{tags_dict["osmAG:to"]}" />\n'
            if 'osmAG:type' in tags_dict:
                new_way_str += f'    <tag k="osmAG:type" v="{tags_dict["osmAG:type"]}" />\n'
            new_way_str += f'    <tag k="osmAG:to" v="{tags_dict["osmAG:from"]}" />\n'
        else:
            continue  # Skip this 'way' if it doesn't have both 'from' and 'to'

        # Close the 'way' element
        new_way_str += '  </way>'

        # Add the constructed 'way' string to the list
        new_way_strings.append(new_way_str)

    # Construct the final XML string
    final_xml = '<osm>\n' + xml_str[0:-6]+'\n'.join(new_way_strings) + '\n</osm>'
    final_xml =  xml_str[0:-6]+'\n'.join(new_way_strings) + '\n</osm>'

    # Write the final XML to the output file
    with open(output_file, 'w') as file:
        file.write(final_xml)

def generate_new_xml_with_shuffled_roomno(input_file,output_file,prefix):
    with open(input_file, 'r') as file:
        xml_data = file.read()
    root = ET.fromstring(xml_data)
    room_names = set()
    existing_ids = set()
    # Step 1: Identify rooms and count them
    for way in root.findall('way'):
        existing_ids.add(int(way.get('id')))
        for tag in way.findall('tag'):
            if tag.get('k') == 'osmAG:areaType' and tag.get('v') == 'room':
                name_tag = way.find("tag[@k='name']")
                if name_tag is not None:
                    room_names.add(name_tag.get('v'))

    # Step 2: Count the number of unique rooms
    num_rooms = len(room_names)
    print(f"Number of rooms: {num_rooms}")

    # Step 3: Generate a new sequence of room identifiers
    random_num=random.randint(1, 20)
    new_room_ids = [f"{prefix}{str((random_num + i) % 100).zfill(2)}" for i in range(num_rooms)]
    random.shuffle(new_room_ids)  # Randomize the sequence

    # Mapping of old room names to new room identifiers
    room_mapping = dict(zip(room_names, new_room_ids))
    print(room_mapping)
    max_existing_id = max(existing_ids) if existing_ids else 0
    new_way_ids = list(range(max_existing_id + 1, max_existing_id + 1 + len(root.findall('way'))))
    random.shuffle(new_way_ids)  # Ensure IDs are randomized
    # Step 4: Replace old room identifiers with new ones
    for way, new_id in zip(root.findall('way'), new_way_ids):
        way.set('id', str(new_id))  # Update way ID
        for tag in way.findall('tag'):
            if tag.get('k') == 'name' and tag.get('v') in room_mapping:
                # Update room names
                tag.set('v', room_mapping[tag.get('v')])
            elif tag.get('k') in ['osmAG:from', 'osmAG:to'] and tag.get('v') in room_mapping:
                # Update passage references to rooms
                tag.set('v', room_mapping[tag.get('v')])

    # Convert the updated XML back to a string
    updated_xml = ET.tostring(root, encoding='unicode')
    with open(output_file[0:-4]+'_'+prefix+'.osm', 'w') as file:
        file.write(updated_xml)
    return updated_xml
# also delete the room has two door to same other room
def del_certain_area(input_tree,output_file,tobe_deleted):
    output_tree=copy.deepcopy(input_tree)

    root = output_tree.getroot()
    for way in root.findall('way'):
        if tobe_deleted==way.find("tag[@k='name']").get('v'):
            pass
def del_all_leaves(input_tree,output_file,free_pass,no_pass):
    output_tree=copy.deepcopy(input_tree)
    # free_pass is the start or destinate area, a set, use .add to add area
    # tree = ET.parse(input_file)
    root = output_tree.getroot()
    # key=area name, value=set of connected area name
    passage_dict={}
    all_name_set=set()
    for way in root.findall('way'):
        if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'passage' for tag in way.findall('tag')):
            # if way.find("tag[@k='osmAG:from']") in no_pass or way.find("tag[@k='osmAG:to']") in no_pass:
            #     continue
            if way.find("tag[@k='osmAG:from']") is not None and way.find("tag[@k='osmAG:to']") is not None:
                if way.find("tag[@k='osmAG:from']").get('v') !='None' and way.find("tag[@k='osmAG:to']").get('v')!='None':
                    all_name_set.add(way.find("tag[@k='osmAG:from']").get('v'))
                    all_name_set.add(way.find("tag[@k='osmAG:to']").get('v'))
                    empty_set=set()
                    empty_set1=set()
                    passage_dict.get(way.find("tag[@k='osmAG:from']").get('v'), empty_set).add(str(way.find("tag[@k='osmAG:to']").get('v')))
                    if(len(empty_set)==1):
                        passage_dict[way.find("tag[@k='osmAG:from']").get('v')]=empty_set
                    
                    passage_dict.get(way.find("tag[@k='osmAG:to']").get('v'), empty_set1).add(way.find("tag[@k='osmAG:from']").get('v'))
                    if(len(empty_set1)==1):
                        passage_dict[way.find("tag[@k='osmAG:to']").get('v')]=empty_set1
    # delete area with only one passage
    for way in root.findall('way'):
        if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'area' for tag in way.findall('tag')):
            name=way.find("tag[@k='name']").get('v')
            if (len(passage_dict.get(name, empty_set)) <=1 and name not in free_pass) or name in no_pass :
                root.remove(way)
    # remove the passage connected to the removed area    
    for way in root.findall('way'):
        appera_time=0
        if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'passage' for tag in way.findall('tag')):
            # print(way.attrib['id'])
            from_tag = way.find("tag[@k='osmAG:from']").get('v')
            to_tag = way.find("tag[@k='osmAG:to']").get('v')

            for way_ in root.findall('way'):
                if any(tag.get('k') == 'osmAG:type' and tag.get('v') == 'area' for tag in way_.findall('tag')):
                    name=way_.find("tag[@k='name']").get('v')
                    if from_tag==name or to_tag==name:
                        appera_time+=1
            # only one or none of the areas are still in the map
            if appera_time<=1:
                root.remove(way)
    # delete unused node
    used_node_refs = set()
    for way in root.findall('way'):
        for nd in way.findall('nd'):
            ref = nd.get('ref')
            if ref:
                used_node_refs.add(ref)
    for node in root.findall('node'):
        if node.get('id') not in used_node_refs:
            root.remove(node)
    if output_file!=None:
        output_tree.write(output_file,encoding='utf-8', xml_declaration=True)
    return output_tree


if __name__ == '__main__':
    output_file_path_random_no=output_file_path[0:-4]+'randomNo.xml'
    input_file_path = file_xml
    output_file_path =output_file_path
    xml_from_wgs2utm(input_file_path, output_file_path)
    del_all_node(output_file_path, output_file_path)
    cleanup_way(output_file_path, output_file_path)

    double_passages(output_file_path, output_file_path)
    generate_new_xml_with_shuffled_roomno(output_file_path,output_file_path_random_no,'4d-')

    # remove_ref_in_area(input_file_path, output_file_path)
    # cleanup_node(output_file_path, output_file_path)
    # areaid2semantic(output_file_path, output_file_path)


    # input_file_path = '../map_draw/topological_edited.osm'
    # output_file_path=input_file_path[0:-4]+'.json'
    # xml2json(input_file_path,output_file_path)



    # Example usage with the provided JSON structure
    # input_file_path = '../map_draw/topological_edited.json'
    # transformed_json = transform_json(input_file_path)
    # output_file_path=output_file_path[0:-5]+'_transfermed.json'

    # with open(output_file_path, 'w') as file:
    #     json.dump(transformed_json, file, indent=4)
    # print(transformed_json)