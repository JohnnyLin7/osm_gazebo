
# 用于从wgs84的osm转化为的utm的osm，它们生成gazebo的world时，需要在如下地方作修改：
        # # 从wgs84转为utm的osm地图，需要这个转换
        # # Jiajie: degree -> osmAG:degree
        # passage_degree=element_.find("tag[@k='osmAG:degree']").get('v')
        # # Jiajie: passage_type -> osmAG:passage_type
        # passage_type=element_.find("tag[@k='osmAG:passage_type']").get('v')
import xml.etree.ElementTree as ET
from collections import OrderedDict

# import map_handler
import utility_map
import process_osm

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import networkx as nx
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import nearest_points
from shapely.geometry import Point, Polygon
import json
from matplotlib.patches import Polygon as MplPolygon
from shapely.ops import nearest_points
from itertools import islice
from collections import Counter
from numpy.linalg import norm
fig, ax = plt.subplots()

# # Parse the XML
# tree = ET.parse(path_prefix+'topological_medium_nicerlooking_id2name.osm')
# root = tree.getroot()

# # Extract nodes
# nodes = {}
# for node in root.findall('node'):
#     id = node.get('id')
#     x = float(node.get('x'))
#     y = float(node.get('y'))
#     nodes[id] = (x, y)

# Function to create a polygon from node references
def create_polygon(way,nodes):
    polygon = [nodes[nd.get('ref')] for nd in way.findall('nd')]
    return polygon

# Function to calculate the centroid of a polygon
def cal_centroid_poly(polygon):
    x_list = [vertex[0] for vertex in polygon]
    y_list = [vertex[1] for vertex in polygon]
    _len = len(polygon)
    x = sum(x_list) / _len
    y = sum(y_list) / _len
    return (x, y)
def plot_osmAG(root):
    # Extract rooms, passages, names, and IDs
    rooms = []
    passages = []
    annotations = []
    for way in root.findall('way'):
        polygon = create_polygon(way)
        way_id = way.get('id')
        name_tag = way.find("tag[@k='name']")
        name = name_tag.get('v') if name_tag is not None else "Unnamed"
        centroid_point = cal_centroid_poly(polygon)
        if way.find("tag[@k='osmAG:type']").get('v') == 'area':
            rooms.append(polygon)
            annotations.append({'text': name, 'centroid': centroid_point, 'color': 'orange'})
        else:
            passages.append(polygon)
            # Use way ID for passages
            annotations.append({'text': way_id, 'centroid': centroid_point, 'color': 'red'})

    # Plotting
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    for room in rooms:
        polygon = patches.Polygon(room, closed=True, facecolor='none',edgecolor='blue',linewidth=2, alpha=1)
        ax.add_patch(polygon)

    for passage in passages:
        polygon = patches.Polygon(passage, closed=False, edgecolor='red',linewidth=4, alpha=1)
        ax.add_patch(polygon)

    # Annotate names and IDs
    for annotation in annotations:
        ax.text(annotation['centroid'][0], annotation['centroid'][1], annotation['text'], 
                ha='center', va='center', fontsize=18, color=annotation['color'])

    # Adjusting the plot limits
    all_points = [point for sublist in rooms + passages for point in sublist]
    all_x = [point[0] for point in all_points]
    all_y = [point[1] for point in all_points]
    ax.set_xlim(min(all_x), max(all_x))
    ax.set_ylim(min(all_y), max(all_y))

    plt.show()


def create_visibility_graph(polygon_points, passage_points):
    """
    Create a visibility graph for a given polygon and passages.
    polygon_points: List of (x, y) tuples for the polygon vertices.
    passage_points: List of (x, y) tuples for the passages.
    """
    poly = Polygon(polygon_points)
    graph = nx.Graph()
    
    # Add edges for the polygon perimeter
    for i, point in enumerate(polygon_points):
        next_point = polygon_points[(i + 1) % len(polygon_points)]
        graph.add_edge(point, next_point, weight=LineString([point, next_point]).length)
    
    # Check visibility between all pairs of points (vertices and passages)
    all_points = polygon_points + passage_points
    for i, point_a in enumerate(all_points):
        for point_b in all_points[i+1:]:
            line = LineString([point_a, point_b])
            # Only add an edge if the line does not cross the polygon boundary
            if poly.contains(line):
                graph.add_edge(point_a, point_b, weight=line.length)
    
    return graph


def create_hollow_visibility_graph(polygon_points, passage_points, hole_points):
    """
    Create a visibility graph for a given polygon (including holes) and passages.
    polygon_points: List of (x, y) tuples for the polygon vertices (outer boundary).
    passage_points: List of (x, y) tuples for the passages.
    holes: List of lists of (x, y) tuples, where each list represents a hole in the polygon.
    """
    print(f'passage_points= {passage_points[0]},{passage_points[1]}')
    outer_poly = Polygon(polygon_points)
    # shrink the hole to include passage centroid in the graph
    # bigger_hole_points=enlarge_polygon_shapely(hole_points,1.0)
    bigger_hole_points=hole_points

    graph = nx.Graph()
    # smaller_hole_points=enlarge_polygon_shapely(hole_points,0.95)
    polygon_with_hole = Polygon(shell=polygon_points, holes=[hole_points])
    # Add edges for the polygon perimeter
    # for i, point in enumerate(polygon_points):
    #     next_point = polygon_points[(i + 1) % len(polygon_points)]
    #     graph.add_edge(point, next_point, weight=LineString([point, next_point]).length)
    for i, point in enumerate(bigger_hole_points):
        next_point = bigger_hole_points[(i + 1) % len(bigger_hole_points)]
        graph.add_edge(point, next_point, weight=LineString([point, next_point]).length)

    # Check visibility between all pairs of points (vertices and passages)
    all_points = passage_points+bigger_hole_points
    for i, point_a in enumerate(all_points):
        for point_b in all_points[i+1:]:
            line = LineString([point_a, point_b])
            # if point_a in passage_points or point_b in passage_points:
            # Only add an edge if the line does not cross the polygon boundary
            if outer_poly.contains(line) and polygon_with_hole.contains(line):
                graph.add_edge(point_a, point_b, weight=line.length)

    for edge in graph.edges():
        plt.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 'g--')
    plt.plot([passage_points[0][0], passage_points[1][0]], [passage_points[0][1], passage_points[1][1]], 'ro')
    plt.show()
    return graph
def calculate_path_length(path):
    """Calculate the total length of a path defined by a list of (x, y) tuples."""
    total_length = 0
    for i in range(1, len(path)):
        point_a = path[i - 1]
        point_b = path[i]
        segment_length = math.sqrt((point_b[0] - point_a[0]) ** 2 + (point_b[1] - point_a[1]) ** 2)
        total_length += segment_length
    return total_length

# def k_shortest_paths(graph, source, target, k, weight='weight'):
#     paths = list(nx.all_simple_paths(graph, source, target))
#     sorted_paths = sorted(paths, key=lambda path: sum(graph[u][v][weight] for u, v in zip(path[:-1], path[1:])))
#     return sorted_paths[:k]
def find_path(graph, start, end):
    """
    Find the shortest path between start and end points using the A* algorithm.
    """
    path = nx.astar_path(graph, start, end, weight='weight')

    return path

def calculate_centroid(start_point, end_point):
    return ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2)

def enlarge_polygon(vertices, scale_factor):
    # Convert the list of tuples to a numpy array for easier manipulation
    vertices_array = np.array(vertices)
    # Calculate the centroid of the polygon
    centroid = np.mean(vertices_array, axis=0)
    # Move each vertex away from the centroid by the scale factor
    scaled_vertices = centroid + (vertices_array - centroid) * scale_factor
    # Convert the scaled vertices back to a list of tuples
    scaled_polygon = list(map(tuple, scaled_vertices))
    return scaled_polygon
def enlarge_polygon_shapely(vertices, scale_factor):
    # Create a Polygon from the given vertices
    poly = Polygon(vertices)
    
    # Use buffer to enlarge the polygon. The buffer distance can be calculated
    # as ((scale_factor - 1) * average_distance_to_centroid), 
    # but for simplicity, we'll directly use scale_factor as an approximation for demonstration.
    # For precise control, adjust the buffer distance based on your specific requirements.
    enlarged_poly = poly.buffer(scale_factor - 1, resolution=16, join_style=2)
    
    # Return the coordinates of the enlarged polygon
    return list(enlarged_poly.exterior.coords)
def parse_osm(tree):
# input file could be the osm without leaves with UTM coordinate.
    # Parse the XML file
    # tree = minidom.parse(input_file)
    # need to make sure same passage centroid of two areas 需要确保两个区域的通道中心点相同
    root = tree.getroot()
    nodes = {}
    areas={}

    # 循环遍历 XML 树中的每个元素
    for element in root:
        # 如果元素是“节点”，则将 “其ID作为键” 和 “坐标作为值” 添加到字典中
        if element.tag == 'node':
            # Node ID as key, coordinates as values
            nodes[element.attrib['id']] = (float(element.attrib['x']), float(element.attrib['y']))

    for element in root:
        # 如果元素是“way”
        if element.tag == 'way':
            for tag in element.findall('tag'):
                # ignore all university
                if tag.attrib['v'] == 'university' :
                    break

                #  如果标签值是 "area"，则进一步处理该区域
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    area_nodes = []
                    passages={}
                    area={}
                    area['name']=area_name

                    for nd in element.findall('nd'):
                        # Add node references to way
                        area_nodes.append(nodes[nd.attrib['ref']])
                    area['nodes']=area_nodes
                    area['centroid']=cal_centroid_poly(area_nodes)
                    for element_ in root:
                        if element_.tag == 'way':
                            for tag_ in element_.findall('tag'):
                                if tag_.attrib['v'] == 'passage':
                                    osm_from_name=element_.find("tag[@k='osmAG:from']").get('v')
                                    osm_to_name=element_.find("tag[@k='osmAG:to']").get('v')
                                    passage_name=element_.find("tag[@k='name']").get('v')
                                    # 从wgs84转为utm的osm地图，需要这个转换
                                    # Jiajie: degree -> osmAG:degree
                                    passage_degree=element_.find("tag[@k='osmAG:degree']").get('v')
                                    # Jiajie: passage_type -> osmAG:passage_type
                                    passage_type=element_.find("tag[@k='osmAG:passage_type']").get('v')

                                    node_refs=[]
                                    for nd in element_.findall('nd'):
                                        # Add node references to way
                                        node_refs.append(nd.attrib['ref'])
                                    if osm_from_name==area_name or osm_to_name==area_name:
                                        passage_id=element_.attrib['id']
                                        
                                        passages[passage_id]={}
                                        passages[passage_id]['coordinates']=[nodes[node_refs[0]],nodes[node_refs[1]]]
                                        passages[passage_id]['passage_id']=passage_id
                                        passages[passage_id]['name']=passage_name
                                        passages[passage_id]['degree']=passage_degree
                                        passages[passage_id]['passage_type']=passage_type
                                        
                                        centroid=calculate_centroid(nodes[node_refs[0]],nodes[node_refs[1]])
                                        Point_centroid=Point(centroid)
                                        polygon = Polygon(area_nodes)
                                        # due to round or whatever, the centroid is not guarteed to be inside the polygon, therefore shrink the polygon a little bit and calculate the nearset_point in the shrinked polygon as the centroid
                                        passages[passage_id]['centroid']=centroid
                                        if osm_from_name==area_name:
                                            passages[passage_id]['from']=area_name
                                            passages[passage_id]['to']=osm_to_name
                                        else:
                                            passages[passage_id]['from']=area_name
                                            passages[passage_id]['to']=osm_from_name


                    area['passages']=passages
                    areas[area_name]=area


    return areas
def cal_save_astar_paths(input_file, output_file,output_json_file,areas):
# output file is json file with path, maybe also with length

    tree = ET.parse(input_file)
    # tree = minidom.parse(input_file)
    root = tree.getroot()
    plt.figure(figsize=(8, 8))
    plt.axis('equal')
    areas_paths_data = {}
    for element in root:
        if element.tag == 'way':
            for tag in element.findall('tag'):
                if tag.attrib['v'] == 'university' :
                    break
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    if len(areas[area_name]['passages'])>1:
                        areas_paths_data[area_name]=[]
                        print(f'!!!!!!!!!!!!area with more than one passages, area_name= {area_name}')
                        # calculate the path length between all pairs of passages
                        for start_passage_id, start_passage in areas[area_name]['passages'].items():
                            for end_passage_id, end_passage in areas[area_name]['passages'].items():
                                if start_passage_id != end_passage_id:
                                    start_passage_centroid = start_passage['centroid']
                                    end_passage_centroid = end_passage['centroid']
                                    polygon_nodes=areas[area_name]['nodes']

                                    polygon = Polygon(polygon_nodes)
                                    start_Point_centroid=Point(start_passage_centroid)
                                    end_Point_centroid=Point(end_passage_centroid)

                                    polygon_shrink=enlarge_polygon_shapely(polygon,0.95)
                                    polygon_shrink = Polygon(polygon_shrink)
                                    nearest_start_on_boundary = nearest_points(start_Point_centroid, polygon_shrink)[1]
                                    nearest_end_on_boundary = nearest_points(end_Point_centroid, polygon_shrink)[1]
                                            # if not nearest_point_on_boundary.within(polygon):
                                            #     print("still outside.....................")
                                            # centroid_=(nearest_point_on_boundary.x,nearest_point_on_boundary.y)
                                            # passages[passage_id]['centroid']=centroid_
                                    graph = create_visibility_graph(polygon_nodes, [(nearest_start_on_boundary.x,nearest_start_on_boundary.y), (nearest_end_on_boundary.x,nearest_end_on_boundary.y)])
                                    # print(f"passage= {areas[area_name]['passages']}")
                                    visibility_graph = nx.Graph()
                                    visibility_graph = nx.compose(visibility_graph, graph)
                                    polygon_x, polygon_y = zip(*areas[area_name]['nodes'])
                                    
                                    plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                    plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                    # plt.show()
                                    
                                    path = find_path(visibility_graph, (nearest_start_on_boundary.x,nearest_start_on_boundary.y), (nearest_end_on_boundary.x,nearest_end_on_boundary.y))

                                    # try:
                                    #     path = find_path(visibility_graph, Point(nearest_end_on_boundary.x,nearest_end_on_boundary.y), Point(nearest_end_on_boundary.x,nearest_end_on_boundary.y))
                                    # except nx.NodeNotFound as e:
                                    #     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!handling NodeNotFound exception")
                                    #     print(f'start_passaage id={start_passage_id}')
                                    #     print(f'end passage id= {end_passage_id}')
                                    #     plt.cla()
                                    #     plt.axis('equal')
                                    #     plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                    #     plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                    #     plt.show()
                                    path[0]=start_passage_centroid
                                    path[-1]=end_passage_centroid
                                    path_x, path_y = zip(*path)
                                    plt.plot(path_x, path_y, 'g--', label='Path')

                                    path_length = calculate_path_length(path)
                                    areas_paths_data[area_name].append({
                                        "start_passage": start_passage_id,
                                        "end_passage": end_passage_id,
                                        "path": path,
                                        "path_length": path_length
                                    })
                                    print(f'path_length= {path_length}')
                                    ET.SubElement(element, 'tag', {'k': start_passage_id+','+end_passage_id, 'v': str(round(path_length,2))})
                        # plt.show()
    with open(output_json_file, 'w') as f:
        json.dump(areas_paths_data, f, indent=4)
    plt.show()
    tree.write(output_file, "UTF-8",short_empty_elements=True)
def visualize_graph(graph):
    # Positions for all nodes
    pos = {node: (node[0], node[1]) for node in graph.nodes()}
    
    # Draw the nodes
    nx.draw_networkx_nodes(graph, pos, node_size=5, node_color='red')
    
    # Draw the edges
    nx.draw_networkx_edges(graph, pos, width=1, alpha=0.5)
    
    # Optionally, draw node labels
    # nx.draw_networkx_labels(graph, pos)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    edge_labels = {e: round(w, 1) for e, w in edge_labels.items()}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8,bbox=dict(facecolor='none', edgecolor='none', pad=0))
    plt.axis('equal')  # So the graph is not distorted
    plt.show()
def cal_save_astar_outside_paths(input_file, output_file,output_json_file,areas,outside_passage_ids):
    # numerical handle strategy: enlarge or shrink the polygon, make sure the nearest point on the boundary is inside the polygon, use the origin polygon to form the graph
    tree = ET.parse(input_file)
    root = tree.getroot()
    plt.figure(figsize=(8, 8))
    plt.axis('equal')
    areas_paths_data = {}
    for element in root:
        if element.tag == 'way':
            for tag in element.findall('tag'):
                if tag.attrib['v'] == 'university' :
                    break
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    if area_name=='E1-F1':
                        hole_polygon=areas[area_name]['nodes']
                    if area_name=='outside':
                        outer_polygon=areas[area_name]['nodes']
    for element in root:
        if element.tag == 'way':
            for tag in element.findall('tag'):
                if tag.attrib['v'] == 'university' :
                    break
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    if len(areas[area_name]['passages'])>1:
                        areas_paths_data[area_name]=[]
                        print(f'!!!!!!!!!!!!area with more than one passages, area_name= {area_name}')
                        # calculate the path length between all pairs of passages
                        for start_passage_id, start_passage in areas[area_name]['passages'].items():
                            for end_passage_id, end_passage in areas[area_name]['passages'].items():
                                if start_passage_id != end_passage_id and (start_passage_id in outside_passage_ids and end_passage_id in outside_passage_ids):
                                    start_passage_centroid = start_passage['centroid']
                                    end_passage_centroid = end_passage['centroid']
                                    hole_polygon_=Polygon(enlarge_polygon_shapely(hole_polygon,1.05))

                                    nearest_start_on_boundary = nearest_points(Point(start_passage_centroid), hole_polygon_.boundary)[1]
                                    nearest_end_on_boundary = nearest_points(Point(end_passage_centroid), hole_polygon_.boundary)[1]
                                    graph = create_hollow_visibility_graph(outer_polygon, [(nearest_start_on_boundary.x,nearest_start_on_boundary.y), (nearest_end_on_boundary.x,nearest_end_on_boundary.y)],hole_polygon)
                                    # visualize_graph(graph)
                                    visibility_graph = nx.Graph()
                                    visibility_graph = nx.compose(visibility_graph, graph)
                                    polygon_x, polygon_y = zip(*areas[area_name]['nodes'])
                                    
                                    plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                    plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                    # plt.show()
                                    # try:
                                    path = find_path(visibility_graph,(nearest_start_on_boundary.x,nearest_start_on_boundary.y), (nearest_end_on_boundary.x,nearest_end_on_boundary.y))
                                    # make sure the start and end point are the passage centroid, so no make inside one area or outside the area, it is using the same passage centroid
                                    path[0]=start_passage_centroid
                                    path[-1]=end_passage_centroid
                                    # except nx.NodeNotFound as e:
                                    #     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!handling NodeNotFound exception")
                                    #     print(f'start_passaage id={start_passage_id}')
                                    #     print(f'end passage id= {end_passage_id}')
                                    #     plt.cla()
                                    #     plt.axis('equal')
                                    #     plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                    #     plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                    #     plt.show()
                                    path_x, path_y = zip(*path)
                                    plt.plot(path_x, path_y, 'g--', label='Path')
                                    path_length = calculate_path_length(path)
                                    areas_paths_data[area_name].append({
                                        "start_passage": start_passage_id,
                                        "end_passage": end_passage_id,
                                        "path": path,
                                        "path_length": path_length
                                    })
                                    print(f'outside path_length= {path_length}')
                                    ET.SubElement(element, 'tag', {'k': start_passage_id+','+end_passage_id, 'v': str(round(path_length,2))})
                        # plt.show()
    with open(output_json_file, 'w') as f:
        json.dump(areas_paths_data, f, indent=4)
    plt.show()
    # tree.write(output_file, "UTF-8",short_empty_elements=True)
def is_passage_in_areas(passage_id, areas):
    for area in areas.values():
        for passage in area["passages"].values():
            if passage["passage_id"] == passage_id:
                return True
    return False
def is_passage_in_area(passage_id, area,areas):
    for passage in areas[area]["passages"].values():
        if passage["passage_id"] == passage_id:
            return True
    return False
def round_numbers(data):
    if isinstance(data, dict):
        return {key: round_numbers(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [round_numbers(item) for item in data]
    elif isinstance(data, float):
        rounded = round(data, 3)
        # Check if the rounded number is a whole number and convert to int if so
        if rounded.is_integer():
            return int(rounded)
        else:
            return rounded
    else:
        return data
def normalize_angle(angle):
    # Normalize angle to be within the range [0, 360)
    angle = angle % 360

    # Adjust angles to be within [-90, 90]
    if angle > 90 and angle <= 270:
        # If angle is in the second or third quadrant, adjust it
        angle -= 180
    elif angle > 270:
        # If angle is in the fourth quadrant, adjust it back into range
        angle -= 360

    return angle
def plot_polygon_with_label(ax, polygon, label):
    # Convert shapely polygon to matplotlib patch
    mpl_poly = MplPolygon(np.array(polygon.exterior.coords), closed=True, edgecolor='blue', facecolor='white')#lightblue
    # ax.add_patch(mpl_poly)

    # Calculate the oriented minimum bounding box (OMB)
    min_rect = polygon.minimum_rotated_rectangle

    # Get the coordinates of the bounding box
    rect_coords = np.array(min_rect.exterior.coords)

    # Calculate center for text placement
    center = np.mean(rect_coords, axis=0)
    
    # Calculate width and height of the rectangle for scaling text
    edge1 = np.linalg.norm(rect_coords[0] - rect_coords[1])
    edge2 = np.linalg.norm(rect_coords[1] - rect_coords[2])
    width, height = min(edge1, edge2), max(edge1, edge2)
    
    # Adjust text size and orientation
    angle = np.degrees(np.arctan2(*(rect_coords[1] - rect_coords[0])[::-1]))
    angle=normalize_angle(90+angle)
    fontsize = 0.5 * min(width,height)  # Scale font size based on width of rectangle

    # Add text to plot
    ax.text(center[0], center[1], label, ha='center', va='center', fontsize=min(3,fontsize), rotation=angle)
def shorten_line(line, shrink_distance):
    if line.length <= 2 * shrink_distance:
        # If the shrink distance is too long, return None or an empty LineString
        # to indicate the line cannot be shortened by this distance.
        return LineString([])
    # Calculate new start point (a point shrink_distance away from the original start)
    new_start = line.interpolate(shrink_distance)
    # Calculate new end point (a point shrink_distance away from the original end)
    new_end = line.interpolate(line.length - shrink_distance)
    # Create a new LineString from the new start to the new end
    return LineString([new_start, new_end])
def transfer_passage_id_2_area_seq(free_pass,passage_id_path,tree):
    root = tree.getroot()
    area_seq=[]
    area_seq.append(free_pass[0])
    next_area=free_pass[0]
    for passage_id in passage_id_path:
        for element in root:
            if element.tag == 'way':
                for tag in element.findall('tag'):
                    if tag.attrib['v'] == 'passage':
                        if element.attrib['id']==passage_id:
                            if next_area==element.find("tag[@k='osmAG:from']").get('v'):
                                area_seq.append(element.find("tag[@k='osmAG:to']").get('v'))
                                next_area=element.find("tag[@k='osmAG:to']").get('v')
                                break
                            if next_area==element.find("tag[@k='osmAG:to']").get('v'):
                                area_seq.append(element.find("tag[@k='osmAG:from']").get('v'))
                                next_area=element.find("tag[@k='osmAG:from']").get('v')
                                break
    
    return area_seq
def calculate_directed_normal(p1, p2, p3, p4):
    # P1,P2=passage node coordinates, P3,P4=start/end centroid coordinates, the normal should be less than 90 degree with path direction
    # Convert 2D points to 3D by appending a zero z-component
    p1, p2, p3, p4 = np.append(p1, 0), np.append(p2, 0), np.append(p3, 0), np.append(p4, 0)
    # Calculate direction vectors for the lines
    d12 = p2 - p1
    d34 = p4 - p3
    # Calculate a normal to d12 (assuming zero z-component for simplicity)
    normal = np.array([-d12[1], d12[0], 0])
    # Ensure the normal points in a direction making less than 90 degrees with d34
    if np.dot(normal, d34) < 0:
        normal = -normal  # Flip the normal if necessary
    # Normalize the normal vector
    normal_unit = normal / norm(normal)
    # Calculate quaternion
    z_axis = np.array([0, 0, 1])
    axis = np.cross(z_axis, normal_unit)
    if norm(axis) == 0:  # If normal is parallel to the z-axis
        return normal_unit, np.array([1, 0, 0, 0])  # Identity quaternion
    axis_unit = axis / norm(axis)
    cos_theta = np.dot(z_axis, normal_unit)
    theta = np.arccos(cos_theta)
    w = np.cos(theta / 2)
    xyz = axis_unit * np.sin(theta / 2)
    quaternion = [ xyz[0], xyz[1], xyz[2],w]
    # for visual normal
    # normal_unit[0]=0.5*normal_unit[0]+(p1[0]+p2[0])/2
    # normal_unit[1]=0.5*normal_unit[1]+(p1[1]+p2[1])/2
    normal_unit[0]=(p1[0]+p2[0])/2
    normal_unit[1]=(p1[1]+p2[1])/2
    # normal_unit is passage centroid for now, for send move-base goal
    return normal_unit, quaternion

def get_path_normal(shortest_path,passage_id_path,areas):
    path_normal=[]
    passage_lines=[]
    normals=[]
    for i,passage_id_1 in enumerate(passage_id_path):
        for area in areas.values():
            find=False
            for passage in area["passages"].values():
                if passage["passage_id"] == passage_id_1:
                    passage_line = passage["coordinates"]
                    passage_lines.append(passage_line)
                    find=True
                    break
            if find:
                break
    for i,centroid_1 in enumerate(shortest_path):
        if i==len(shortest_path)-1:
            break
        centroid_2 = shortest_path[(i + 1) % len(shortest_path)]
        
        normal_unit, quaternion=calculate_directed_normal(np.array(passage_lines[i][0]),np.array(passage_lines[i][1]),np.array(centroid_1),np.array(centroid_2))
        path_normal.append(quaternion)
        normals.append(normal_unit)

    if len(shortest_path)>2:
        normal_unit, quaternion=calculate_directed_normal(np.array(passage_lines[-1][0]),np.array(passage_lines[-1][1]),np.array(shortest_path[-2]),np.array(shortest_path[-1]))
        path_normal.append(quaternion)
        normals.append(normal_unit)
# normals is passage centroid + normal in place orientation,path_normal is quaternion
    return normals,path_normal

def tranfer_path_2_passage_id(shortest_path,areas_paths):
    point_path=[]
    passage_id_path=[]
    start_passage_id=None
    end_passage_id=None
    for i,seg_path in enumerate(shortest_path):
        if i==len(shortest_path)-1:
            passage_id_path.append(end_passage_id)
            break
        next_point = shortest_path[(i + 1) % len(shortest_path)]
        for area_paths in areas_paths.values():
            for path_ in area_paths:
                if [seg_path[0],seg_path[1]]==path_["path"][0] and [next_point[0],next_point[1]]==path_["path"][-1]:
                    start_passage_id = path_["start_passage"]
                    end_passage_id = path_["end_passage"]
                    point_path+=path_["path"]
                    passage_id_path.append(start_passage_id)
    return passage_id_path,point_path

def k_shortest_paths(G, source, target, k, weight='weight'):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
def get_sandwich_area_between_passageid(passage_id_path,tree,no_pass):
    root = tree.getroot()
    sandwich_area=None
    area_seq=[]
    # area_seq.append(free_pass[0])
    # next_area=free_pass[0]
    for passage_id in passage_id_path:
        for element in root:
            if element.tag == 'way':
                for tag in element.findall('tag'):
                    if tag.attrib['v'] == 'passage':
                        if element.attrib['id']==passage_id:
                            if element.find("tag[@k='osmAG:to']").get('v') in no_pass or element.find("tag[@k='osmAG:from']").get('v') in no_pass:
                                continue
                            area_seq.append(element.find("tag[@k='osmAG:to']").get('v'))
                            area_seq.append(element.find("tag[@k='osmAG:from']").get('v'))
                            # if next_area==element.find("tag[@k='osmAG:from']").get('v'):
                            #     area_seq.append(element.find("tag[@k='osmAG:to']").get('v'))
                            #     next_area=element.find("tag[@k='osmAG:to']").get('v')
                            #     break
                            # if next_area==element.find("tag[@k='osmAG:to']").get('v'):
                            #     area_seq.append(element.find("tag[@k='osmAG:from']").get('v'))
                            #     next_area=element.find("tag[@k='osmAG:from']").get('v')
                            #     break
    item_counts = Counter(area_seq)
    # print(f'area_seq= {area_seq}')
    sandwich_area=[item for item, count in item_counts.items() if count > 1]
    return sandwich_area
def build_graph(cropped_areas,areas_paths,free_pass,no_pass,areas_try_to_Avoid,color,tree,visited_areas,omit_area=None,invalid_search=0):
    # we want to visit as much as areas as possible, so we increase the weight of the edge in visited area
    shortest_graph = nx.Graph()
    start_area_name=free_pass[0]
    end_area_name=free_pass[1]
    # TODO: Find the right(shortest) passage IDs for the start and end areas
    start_area_passage_id = (next(iter(cropped_areas[start_area_name]['passages'].values())),None)[0]['passage_id']
    end_area_passaged_id = (next(iter(cropped_areas[end_area_name]['passages'].values())),None)[0]['passage_id']
    # print(f'start_area_passage_id= {start_area_passage_id}')
    start_area_centroid=None
    end_area_centroid=  None
    for area_paths in areas_paths.values():
        for path in area_paths:
            start_passage = path["start_passage"]
            end_passage = path["end_passage"]
            # If either the start or end passage is in the areas, plot the path
            # build the graph based on the cropped areas, not all areas
            if is_passage_in_areas(start_passage, cropped_areas) and is_passage_in_areas(end_passage, cropped_areas):
                if start_passage==start_area_passage_id:
                    start_area_centroid=path["path"][0]
                if end_passage==end_area_passaged_id:
                    end_area_centroid=path["path"][-1]
                x_coords, y_coords = zip(*path["path"])
                
                sandwich_area=get_sandwich_area_between_passageid([start_passage,end_passage],tree,no_pass)
                if not sandwich_area:
                    continue
                # print(f'sandwich_area= {sandwich_area}')
                # print(f'no_pass= {no_pass}')
                # if sandwich_area in no_pass:
                #     continue
                # print(f"start passage={start_passage},end_passage={end_passage}")
                # print(f'sandwich_area= {sandwich_area}')
                edge_weight=path['path_length']
                if len(sandwich_area)>1:
                    print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!sandwich_area= {sandwich_area}')
                if sandwich_area[0] in areas_try_to_Avoid:
                    edge_weight+=10
                visited_counts = Counter(visited_areas)
                # if sandwich_area[0] in visited_areas and sandwich_area[0]!="outside":
                if sandwich_area[0] in visited_areas:

                    # print("adding weight to the edge")
                    if sandwich_area[0]!="outside":
                        # edge_weight+=(visited_counts[sandwich_area[0]]+invalid_search)*path['path_length']
                        edge_weight+=100
                    else:
                        pass
                        # edge_weight+=(visited_counts[sandwich_area[0]])*path['path_length']/3
                        # edge_weight+=(visited_counts[sandwich_area[0]])*path['path_length']/3

                shortest_graph.add_edge((path["path"][0][0],path["path"][0][1]), (path["path"][-1][0],path["path"][-1][1]),weight=edge_weight)
    return shortest_graph,start_area_centroid,end_area_centroid,x_coords,y_coords

def draw_name_path(cropped_areas,areas_paths,area_name_path):
    centroid_path=[]
    for i,area_name in enumerate(area_name_path):
        if i==len(area_name_path)-1:
            break
        next_area_name=area_name_path[i+1]
        for id,passage in cropped_areas[area_name]['passages'].items():
            if passage['to']==next_area_name:
                centroid_path.append(passage['centroid'])
    passage_id_path_,point_path_=tranfer_path_2_passage_id(centroid_path,areas_paths)
    point_path_x=[point[0] for point in point_path_]
    point_path_y=[point[1] for point in point_path_]

    plt.plot(point_path_x, point_path_y, 'b--', linewidth=0.5)
    for i, point in enumerate(centroid_path):
        if i==len(centroid_path)-1:
            break
        next_point = centroid_path[(i + 1) % len(centroid_path)]
        plt.plot([point[0], next_point[0]], [point[1], next_point[1]], 'r--',linewidth=0.5)
#  areas_paths is the json file
def find_shortest_path(cropped_areas,areas_paths,free_pass,no_pass,areas_try_to_Avoid,color,tree):
    invalid_search=0
    visited_areas=[]
    point_path_x,point_path_y=[],[]
    multi_passageid_path=[]
    color_list=['g','c','m','y','k','#33DFFF' ]

    for i in range(1):
        print(i)
        shortest_graph,start_area_centroid,end_area_centroid,x_coords, y_coords=build_graph(cropped_areas,areas_paths,free_pass,no_pass,areas_try_to_Avoid,color,tree,visited_areas,invalid_search)
        # shortest_path using passage centroid coordinates, from one passage to other without mediate point, on other words staight line
        shortest_path=find_path(shortest_graph, (start_area_centroid[0],start_area_centroid[1]),(end_area_centroid[0],end_area_centroid[1]))
        # point_path_ is the path with mediate points inside all areas
        passage_id_path_,point_path_=tranfer_path_2_passage_id(shortest_path,areas_paths)
        passage_centroid,shortest_path_normal=get_path_normal(shortest_path,passage_id_path_,cropped_areas)
        area_path=transfer_passage_id_2_area_seq(free_pass,passage_id_path_,tree)

        # print(f'area_seq= {transfer_passage_id_2_area_seq(free_pass,passage_id_path_,tree)}')
        if passage_id_path_ in multi_passageid_path:
            print(f"same passage_id_path!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!{invalid_search}")
            invalid_search+=1
            # visualize_graph(shortest_graph)

            continue
        multi_passageid_path.append(passage_id_path_)

        visited_areas+=transfer_passage_id_2_area_seq(free_pass,passage_id_path_,tree)
        # print(f'visited_areas= {visited_areas}')
        # area_path=transfer_passage_id_2_area_seq(free_pass,passage_id_path_,tree)
        # visited_areas+=area_path
        point_path_x.append([point[0] for point in point_path_])
        point_path_y.append([point[1] for point in point_path_])

    # plt.plot(x_coords, y_coords, color_list[i%len(color_list)],linewidth=0.2)
    for  i,(point_x,point_y) in enumerate(zip(point_path_x,point_path_y)):
        plt.plot(point_x, point_y, color_list[i%len(color_list)], linewidth=0.5)
    
    # # visualize_graph(shortest_graph)




    last_area=None

    return shortest_path,area_path,shortest_path_normal
def load_plot_json_paths(input_tree,json_file_path,areas,cropped_areas,free_pass,no_pass,areas_try_to_Avoid,example_free_pass):
    # use free_pass to represent start and destination area
    # plot all areas 
    # only plot relevant passages(start/end/passages in areas with more than two passages)
    # do not plot structure
    # calculate the shortest path between start and end area

    with open(json_file_path, 'r') as f:
        areas_paths = json.load(f)
    # plt.figure(figsize=(8, 8))
    plt.axis('equal')
    root = input_tree.getroot()

    for element in root:
        if element.tag == 'way':
            if element.find("tag[@k='osmAG:areaType']")!=None and element.find("tag[@k='osmAG:areaType']").get('v')=='structure':
                continue
            for tag in element.findall('tag'):
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    try:
                        polygon_x, polygon_y = zip(*cropped_areas[area_name]['nodes'])
                    except KeyError:
                        # print("")
                        continue
                    poly_area = Polygon(cropped_areas[area_name]['nodes'])
                    minx, miny, maxx, maxy = poly_area.bounds
                    bbox_width = maxx - minx
                    bbox_height = maxy - miny
                    font_size = min(bbox_width, bbox_height) * 1.5
                    plt.plot(polygon_x, polygon_y, 'b-',linewidth=0.5)
                    # text_show=area_name.replace("E1", "").replace("-F1", "")
                    text_show=area_name.replace("-F1", "")
                    plot_polygon_with_label(ax, poly_area, area_name)
                    # plt.text(areas[area_name]['centroid'][0], areas[area_name]['centroid'][1], text_show, ha='center', va='center',fontsize=min(4,font_size))
                    if area_name in cropped_areas:
                        if len(cropped_areas[area_name]['passages'])>1 or area_name in free_pass:
                            for passage_id, passage in cropped_areas[area_name]['passages'].items():
                                passage_coordinates = passage['coordinates']
                                passage_coordinates_x, passage_coordinates_y = zip(*passage_coordinates)
                                plt.plot(passage_coordinates_x, passage_coordinates_y, 'r-',linewidth=0.8)
    shortest_centroid_path,shortest_area_path,shortest_path_normal=find_shortest_path(cropped_areas,areas_paths,free_pass,no_pass,areas_try_to_Avoid,'g--',input_tree)
    if len(example_free_pass)>0:
        find_shortest_path(cropped_areas,areas_paths,example_free_pass,'y--',input_tree)

    # plt.legend()
    plt.grid(False)
    plt.axis('off')
    plt.savefig('high_resolution_plot.png', dpi=800)  # Adjust dpi value as needed

    # plt.show()
    return shortest_area_path,shortest_path_normal,shortest_centroid_path
def cal_astar_paths_length(input_file, output_file,areas):
    tree = ET.parse(input_file)
    # tree = minidom.parse(input_file)
    root = tree.getroot()
    plt.figure(figsize=(8, 8))
    plt.axis('equal')
    for element in root:
        if element.tag == 'way':
            
            for tag in element.findall('tag'):
                if tag.attrib['v'] == 'area':
                    area_name=element.find("tag[@k='name']").get('v')
                    if len(areas[area_name]['passages'])>1:
                        print(f'!!!!!!!!!!!!area_name= {area_name}')
                        # calculate the path length between all pairs of passages
                        for start_passage_id, start_passage in areas[area_name]['passages'].items():
                            for end_passage_id, end_passage in areas[area_name]['passages'].items():
                                if start_passage_id != end_passage_id:
                                    start_passage_centroid = start_passage['centroid']
                                    end_passage_centroid = end_passage['centroid']
                                    # polygon_nodes=enlarge_polygon(areas[area_name]['nodes'],1.005)
                                    # polygon_nodes=enlarge_polygon_shapely(areas[area_name]['nodes'],1.05)
                                    polygon_nodes=areas[area_name]['nodes']
                                    graph = create_visibility_graph(polygon_nodes, [start_passage_centroid, end_passage_centroid])
                                    # print(f"passage= {areas[area_name]['passages']}")
                                    visibility_graph = nx.Graph()
                                    visibility_graph = nx.compose(visibility_graph, graph)
                                    polygon_x, polygon_y = zip(*areas[area_name]['nodes'])
                                    
                                    plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                    plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                    # plt.show()
                                    try:
                                        path = find_path(visibility_graph, start_passage_centroid, end_passage_centroid)
                                    except nx.NodeNotFound as e:
                                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!handling exception")
                                        print(f'start_passaage id={start_passage_id}')
                                        print(f'end passage id= {end_passage_id}')
                                        plt.cla()
                                        plt.axis('equal')
                                        plt.plot(polygon_x, polygon_y, 'b-', label='Polygon Boundary')
                                        plt.plot([start_passage_centroid[0], end_passage_centroid[0]], [start_passage_centroid[1], end_passage_centroid[1]], 'ro', label='Passages')
                                        plt.show()
                                    path_x, path_y = zip(*path)

                                    path_length = calculate_path_length(path)
                                    print(f'path_length= {path_length}')
                                    
                                    plt.plot(path_x, path_y, 'g--', label='Path')

                                    # ET.SubElement(element, 'tag', {'k': start_passage_id+','+end_passage_id, 'v': str(round(path_length,2))})
                        # plt.show()

    plt.show()
    tree.write(output_file, "UTF-8",short_empty_elements=True)
def generate_additional_text_4_figure(input_file, output_file,cropped_areas):
    tree = ET.parse(input_file)
    process_osm.del_all_node(input_file,output_file)
    process_osm.cleanup_way(output_file,output_file)  
    # process_osm.del_all_passages(output_file,output_file)  
    process_osm.del_all_parents(output_file,output_file)                      

if __name__ == '__main__':
    path_prefix='../osmAG/real/'
    # file_name='ShanghaiTech_merge_F2_corrected_id2name_noleaf_utm'
    # file_name='ShanghaiTech_merge_F2_corrected_id2name_bak_easy_utm'
    file_name='ShanghaiTech_merge_F2_corrected_id2name_outside_structure_utm'
    json_file_name='ShanghaiTech_merge_F2_corrected_id2name_outside_structure_utm_path_0609'#ShanghaiTech_merge_F2_corrected_id2name_bak_utm_path__

    # outside_passage_ids=['-180525','-180620','-181141','-181144','-180450']#-180450
    outside_passage_ids=['-183600','-183656','-183660','-183661','-183662','-183664','-183665','-184555','-184716','-185177']#-180450

    # map_handler.convert_wgs_2_cartesian(path_prefix+file_name+'.osm',path_prefix+file_name+'_utm.osm')
    # process_osm.areaid2semantic(path_prefix+'shanghaitech_F2_D_sector_id2name.osm',path_prefix+'shanghaitech_F2_D_sector_id2name.osm')
    areas_tree = ET.parse(path_prefix+file_name+'.osm')
    areas=parse_osm(areas_tree)
    # cal_astar_paths_length(path_prefix+file_name+'.osm',path_prefix+file_name+'_length.osm',areas)
    # cal_save_astar_paths(path_prefix+file_name+'.osm',path_prefix+file_name+'_length.osm',path_prefix+file_name+'_path_0609.json',areas)
    # cal_save_astar_outside_paths(path_prefix+file_name+'.osm',path_prefix+file_name+'_length.osm',path_prefix+file_name+'_outside_path_0609.json',areas,outside_passage_ids)

    free_pass=['E1c-F1-COR-02','E1b-F1-08']
    free_pass=['E1d-F1-06','E1b-F1-03']
    draw_path=['E1d-F1-06', 'E1d-F1-COR-01', 'E1-F1-COR-01',  'E1b-F1-COR-01', 'E1b-F1-07']

    example_free_pass=[]
    no_path=['E1-P2','E1b-F1-12','E1-F1-COR-01']
    no_path=[]
    cropped_tree=process_osm.del_all_leaves(areas_tree,path_prefix+file_name+'_feedin.osm',free_pass,no_path)
    cropped_tree=process_osm.del_all_leaves(cropped_tree,path_prefix+file_name+'_feedin.osm',free_pass,no_path)
    cropped_tree=process_osm.del_all_leaves(cropped_tree,path_prefix+file_name+'_feedin.osm',free_pass,no_path)

    cropped_areas = parse_osm(cropped_tree)
    with open(path_prefix+json_file_name+'.json', 'r') as f:
        areas_paths = json.load(f)
    # draw_name_path(cropped_areas,areas_paths,draw_path)
    no_path=[]
    load_plot_json_paths(areas_tree,path_prefix+json_file_name+'.json',areas,cropped_areas,free_pass,no_path,[],example_free_pass)
    # generate_additional_text_4_figure(path_prefix+file_name+'_feedin.osm',path_prefix+file_name+'_text.osm',cropped_areas)
# '''