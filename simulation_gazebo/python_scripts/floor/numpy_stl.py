# ChatGPT 写的 利用 numpy_stl库的示例代码， by fujing

import numpy as np
from stl import mesh

def create_circle(center, radius, num_points):
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    return np.array([
        (center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle), 0) for angle in angles
    ])

def main():
    # Define the size of the plate and the number of holes
    plate_size = (100, 100)
    num_holes = 3
    hole_radius = 10
    hole_points = 20

    # Create a mesh object
    total_faces = 2 + num_holes * (hole_points - 2)
    main_mesh = mesh.Mesh(np.zeros(total_faces, dtype=mesh.Mesh.dtype))

    # Create main surface
    main_mesh.vectors[0] = np.array([[0, 0, 0], [plate_size[0], 0, 0], [plate_size[0], plate_size[1], 0]])
    main_mesh.vectors[1] = np.array([[0, 0, 0], [plate_size[0], plate_size[1], 0], [0, plate_size[1], 0]])

    # Add holes
    face_index = 2
    for i in range(num_holes):
        center = (np.random.rand() * (plate_size[0] - 2 * hole_radius) + hole_radius,
                  np.random.rand() * (plate_size[1] - 2 * hole_radius) + hole_radius)
        circle_points = create_circle(center, hole_radius, hole_points)

        # Triangulate the hole
        for j in range(1, hole_points - 1):
            main_mesh.vectors[face_index] = np.array([circle_points[0], circle_points[j], circle_points[j + 1]])
            face_index += 1

    # Save to file
    main_mesh.save('surface_with_holes.stl')

if __name__ == '__main__':
    main()
