from pyproj import Transformer
from pyproj.transformer import Transformer
from collections import OrderedDict
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import networkx as nx
# 将纬度和经度转换为UTM坐标
def lat_lon_to_utm(latitude, longitude):
    #ACCORDING TO https://developers.arcgis.com/javascript/3/jshelp/pcs.htm WGS84 TO UTM 51N(SHANGHAI) is 32651
    transformer = Transformer.from_crs("epsg:4326", "epsg:32651")
    utm_easting, utm_northing = transformer.transform(latitude, longitude)

    return utm_easting, utm_northing

# 将节点从WGS84坐标转换为UTM坐标： 删除节点的action和visible属性，更新节点ID和坐标，删除longitude和latitude属性
def xml_from_wgs2utm(input_file, output_file):
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
        # make its use less token
        del node.attrib['action']
        del node.attrib['visible']
        if(min_node_id>int(node.get('id'))):
            min_node_id=int(node.get('id'))
        ordered_dict_id[str(node.get('id'))]=str((i+1))
        node.set('id',str((i+1)))
        
        east,north=lat_lon_to_utm(float(node.get('lat')),float(node.get('lon')))
        if(min_east>east):
            min_east=east
        if(min_north>north):
            min_north=north
        node.set('x',str(round(east,2)))
        node.set('y',str(round(north,2)))
        del node.attrib['lat']
        del node.attrib['lon']

    for node in root.findall('node'):
        node.set('x',str(round(float(node.get('x'))-min_east,2)))
        node.set('y',str(round(float(node.get('y'))-min_north,2)))
        
    for way in root.findall('way'):
        for nd in way.findall('nd'):
            nd.set('ref',ordered_dict_id[str(nd.get('ref'))])
            
    # Convert the XML tree to a string and remove spaces before opening angle brackets
    xml_string = ET.tostring(root, encoding='unicode', method='xml')
   
    tree.write(output_file, "UTF-8",short_empty_elements=True)

# 从OSM文件中提取节点坐标并绘制散点图
def plot_nodes(file_name:str):
    # Parse the OSM file
    tree = ET.parse(file_name)  # Replace 'your_osm_file.osm' with your actual file path
    root = tree.getroot()

    x_coords = []
    y_coords = []

    # Extract node coordinates
    for node in root.findall('node'):
        x = float(node.get('x'))
        y = float(node.get('y'))
        x_coords.append(x)
        y_coords.append(y)

    # Plot the coordinates
    plt.figure(figsize=(8, 6))
    plt.scatter(x_coords, y_coords, color='blue', s=10)
    plt.title('Node Coordinates Plot')
    plt.xlabel('X Coordinates')
    plt.ylabel('Y Coordinates')
    plt.axis('equal')  # Set equal aspect ratio
    plt.grid(True)
    plt.show()

# tranfer a osm( only have area and passage) to area and area_connected_by_passage, and delete all passages
# 将OSM文件中的Area通过通道连接起来，并删除通道
def osm2area_connected_by_passage(input_file, output_file):
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    G = nx.Graph()
    # build graph
    for way in root.findall('way'):
        way_tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')}
        print(f'way_tags= {way_tags}')
        if way_tags.get('osmAG:type') == 'passage':
            G.add_edge(way_tags['osmAG:from'], way_tags['osmAG:to'])
    # find all connected area in  all areas
    for way in root.findall('way'):
        way_tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')}
        if way_tags.get('osmAG:type') == 'area':
            area_name=way_tags['name']
            connected_areas = G.neighbors(area_name)
            for connected_area in connected_areas:
                ET.SubElement(way, 'tag', {'k': area_name+'_directly_connected_area', 'v': connected_area})
        #  remove all passages
        else:
            root.remove(way)
    xml_string = ET.tostring(root, encoding='unicode', method='xml')
    tree.write(output_file, "UTF-8",short_empty_elements=True)
if __name__ == '__main__':
    # plot_nodes('../map_draw/edited_osm_area_compare/topological_easy.osm')
    osm2area_connected_by_passage('../osmAG/real/ShanghaiTech_merge_F2_corrected_id2name_bak_utm_text.osm',\
                                  '../osmAG/real/ShanghaiTech_merge_F2_corrected_id2name_bak_utm_text_no_passages.osm')
