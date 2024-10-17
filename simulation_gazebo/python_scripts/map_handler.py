# 为了把OSM的纬度和精度转换为UTM坐标（笛卡尔坐标系），存储为新的osm文件

import xml.etree.ElementTree as ET
from collections import OrderedDict

import utility_map
import process_osm

def sort_id(input_file,output_file):
    pass

    
def convert_wgs_2_cartesian(input_file,output_file):
    # Parse the XML file
    tree = ET.parse(input_file)
    # tree = minidom.parse(input_file)
    root = tree.getroot()
    # Iterate through all 'node' elements
    ordered_dict_id = OrderedDict()
    min_node_id=0
    min_east=10000000
    min_north=10000000
    for i,node in enumerate(root.findall('node')):
        # if(min_node_id>int(node.get('id'))):
        #     min_node_id=int(node.get('id'))
        # ordered_dict_id[str(node.get('id'))]=str((i+1))
        # node.set('id',str((i+1)))
        
        east,north=utility_map.lat_lon_to_utm(float(node.get('lat')),float(node.get('lon')))
        if(min_east>east):
            min_east=east
        if(min_north>north):
            min_north=north
        node.set('x',str(round(east,2)))
        node.set('y',str(round(north,2)))
        del node.attrib['lat']
        del node.attrib['lon']

    for node in root.findall('node'):
        # node.set('x',str(round(float(node.get('x'))-min_east,2)))
        # node.set('y',str(round(float(node.get('y'))-min_north,2)))
        node.set('x',str(float(node.get('x'))))
        node.set('y',str(float(node.get('y'))))
        
    # for way in root.findall('way'):
    #     for nd in way.findall('nd'):
    #         nd.set('ref',ordered_dict_id[str(nd.get('ref'))])

   
    tree.write(output_file, "UTF-8",short_empty_elements=True)
if __name__ == '__main__':
    wsg_file_name = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'
    utm_file_name = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/fujing_edited_utm_jiajie_2F_ShanghaiTech_merge_F2_corrected_id2name_outside_structure.osm'
    # shanghaitech_F2_D_sector
    # topological_medium_nicerlooking
    convert_wgs_2_cartesian(wsg_file_name ,utm_file_name)
    # process_osm.areaid2semantic(osm_path_prefix+utm_file_name+'_utm.osm',osm_path_prefix+utm_file_name+'_utm.osm')
    free_set=set()
    no_pass=set()
    free_set.add('E1d-F1-06')
    free_set.add('E1d-F1-08')
    # process_osm.del_all_leaves(osm_path_prefix+utm_file_name+'.osm',osm_path_prefix+utm_file_name+'_noleaf.osm',free_set,no_pass)
