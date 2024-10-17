# Last modified by Jiajie, 24.7.11
# 用于对一个完整的floor切割去 elevator 和 stairs 的部分 （利用从osm中读到的组成 elevator 和 stairs 的 node 的坐标信息）

import xml.etree.ElementTree as ET
import numpy as np
from stl import mesh
from shapely.geometry import Polygon, Point
import os
import matplotlib.pyplot as plt

# 定义文件路径
xml_file_path = '/home/johnnylin/fujing_osm/src/simulation_gazebo/maps/stairs_elevators.xml'
stl_file_path = '/home/johnnylin/fujing_osm/subdivided_9_floor_level_2.stl'
output_stl_file_path = '/home/johnnylin/fujing_osm/new_9_floor_level_2.stl'

# 解析XML文件
tree = ET.parse(xml_file_path)
root = tree.getroot()

# 创建一个字典来存储楼梯和电梯的坐标
areas = {'stairs': [], 'elevator': []}

# 遍历每一个Way
for way in root.findall('way'):
    usage = way.get('usage')
    coords = []
    for node in way.findall('node'):
        x = float(node.get('x'))
        y = float(node.get('y'))
        coords.append((x, y))
    if usage in areas:
        areas[usage].append(coords)

# 输出解析到的多边形坐标
# print("Parsed areas:", areas)


# 创建楼梯和电梯的多边形
polygons = {'stairs': [], 'elevator': []}
for usage, area_list in areas.items():
    for coords in area_list:
        polygon = Polygon(coords)
        polygons[usage].append(polygon)

# 输出生成的多边形信息
print("Generated polygons:", polygons)

# 读取完整的地板模型
floor = mesh.Mesh.from_file(stl_file_path)

# 将所有三角形面片转换为shapely的多边形
def create_polygon_from_mesh(face):
    return Polygon([(face[0][0], face[0][1]), (face[1][0], face[1][1]), (face[2][0], face[2][1])])

# 可视化多边形
def plot_polygons(polygons, floor_mesh=None):
    for usage, poly_list in polygons.items():
        for poly in poly_list:
            x, y = poly.exterior.xy
            plt.plot(x, y, label=usage)
    if floor_mesh:
        for face in floor_mesh.vectors:
            x = [face[0][0], face[1][0], face[2][0], face[0][0]]
            y = [face[0][1], face[1][1], face[2][1], face[0][1]]
            plt.plot(x, y, color='grey', alpha=0.5)
    plt.legend()
    plt.show()
# 切割地板模型
def cut_area_from_floor(floor_mesh, polygons):
    faces_to_remove = set()
    
    # 遍历每个面
    for i, face in enumerate(floor_mesh.vectors):
        polygon = create_polygon_from_mesh(face)
        
        # 检查是否有任何多边形包含该面
        for area_polygons in polygons.values():
            for poly in area_polygons:
                if poly.intersects(polygon):
                    faces_to_remove.add(i)
                    break

    # 输出要移除的面片信息
    print("Faces to remove:", faces_to_remove)


    # 创建新的mesh，不包含被移除的面
    new_vectors = np.delete(floor_mesh.vectors, list(faces_to_remove), axis=0)
    new_mesh = mesh.Mesh(np.zeros(new_vectors.shape[0], dtype=mesh.Mesh.dtype))
    new_mesh.vectors = new_vectors
    return new_mesh

# plot_polygons(polygons, floor)

# 切割楼梯和电梯的区域
cut_polygons = [poly for poly_list in polygons.values() for poly in poly_list]
modified_floor = cut_area_from_floor(floor, {'cut_areas': cut_polygons})

# 输出修改后的地板模型信息
print("Modified floor vectors:", modified_floor.vectors)

# 保存修改后的地板模型
modified_floor.save(output_stl_file_path)
