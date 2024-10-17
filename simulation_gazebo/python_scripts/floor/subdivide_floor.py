# Last Modified by Jiajie, 用于增加原始floor的顶点和面的密度否则 cut_floor.py是无法正常工作的
import numpy as np
from stl import mesh
from scipy.spatial import Delaunay

def midpoint_subdivision(vertices, faces, iterations=1):
    for _ in range(iterations):
        new_vertices = list(vertices)
        new_faces = []

        # 用于存储边的中点
        midpoint_cache = {}

        def get_midpoint(v1, v2):
            edge = tuple(sorted((v1, v2)))
            if edge in midpoint_cache:
                return midpoint_cache[edge]
            midpoint = (vertices[v1] + vertices[v2]) / 2.0
            new_vertices.append(midpoint)
            midpoint_index = len(new_vertices) - 1
            midpoint_cache[edge] = midpoint_index
            return midpoint_index

        for face in faces:
            v1, v2, v3 = face
            a = get_midpoint(v1, v2)
            b = get_midpoint(v2, v3)
            c = get_midpoint(v3, v1)

            new_faces.extend([[v1, a, c], [v2, b, a], [v3, c, b], [a, b, c]])

        vertices = np.array(new_vertices)
        faces = np.array(new_faces)

    return vertices, faces

# 读取原始地板模型
floor = mesh.Mesh.from_file('/home/johnnylin/fujing_osm/floor_level_2.stl')

# 获取顶点和面
original_vertices = floor.vectors.reshape(-1, 3)
faces = np.arange(len(original_vertices)).reshape(-1, 3)

# 使用多次中点细分进行细分
iterations = 9  # 调整迭代次数以增加细分深度
new_vertices, new_faces = midpoint_subdivision(original_vertices, faces, iterations=iterations)

# 创建新的mesh对象
subdivided_floor = mesh.Mesh(np.zeros(new_faces.shape[0], dtype=mesh.Mesh.dtype))
subdivided_floor.vectors = new_vertices[new_faces]

# 保存细分后的地板模型
subdivided_floor.save('/home/johnnylin/fujing_osm/subdivided_9_floor_level_2.stl')
