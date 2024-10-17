# Last Modified by Jiajie, 24.7.11
# 用于将floor.stl移动到局部坐标系下，好在world中以原来的floor的pose以匹配之，并简化其几何结构
import vtk
def transform_and_compress_stl(input_stl, output_stl, reduction=0.5):
    # Read the input STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_stl)
    reader.Update()
    
    # Get the mesh data
    mesh = reader.GetOutput()
    
    # Compute the center of mass
    center_of_mass = vtk.vtkCenterOfMass()
    center_of_mass.SetInputData(mesh)
    center_of_mass.Update()
    center = center_of_mass.GetCenter()
    
    # Create a transform to move the mesh to the origin
    transform = vtk.vtkTransform()
    transform.Translate(-center[0], -center[1], -center[2])
    
    # Apply the transformation
    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputData(mesh)
    transform_filter.SetTransform(transform)
    transform_filter.Update()
    
    # Decimate (simplify) the mesh
    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(transform_filter.GetOutput())
    decimate.SetTargetReduction(reduction)  # Set the target reduction (0.5 means 50% reduction)
    decimate.PreserveTopologyOn()
    decimate.Update()
    
    # Write the transformed and simplified mesh to a new STL file
    writer = vtk.vtkSTLWriter()
    writer.SetFileName(output_stl)
    writer.SetInputData(decimate.GetOutput())
    writer.SetFileTypeToBinary()  # Ensure binary format
    writer.Write()
    
    print(f"Transformed and compressed STL saved to {output_stl}")

# Example usage
input_stl = "/home/johnnylin/fujing_osm/new_9_floor_level_2.stl"
output_stl = "/home/johnnylin/fujing_osm/src/simulation_gazebo/meshes/new_9_floor_level_2_centered_compressed.stl"
transform_and_compress_stl(input_stl, output_stl, reduction=0.5)
