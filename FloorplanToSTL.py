from utils.FloorplanToBlenderLib import execution
from subprocess import check_output
import os
import open3d as o3d
import numpy as np
import time
import config 
import utils.Placement_utils as pl

def createFloorPlan(image_path = config.image_path, target_path = config.target_path, SR_Check=True):
    import config 
    if SR_Check == True:
        SR= [config.SR_scale,config.SR_method]
    else:
        SR = None
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    blender_script_path = config.blender_script_path
    CubiCasa = config.CubiCasa
    
    
    data_paths = [execution.simple_single(image_path,CubiCasa=CubiCasa,SR=SR)]
  
    check_output([blender_install_path,
     "-noaudio", # this is a dockerfile ubuntu hax fix
     "--background",
     "--python",
     blender_script_path,
     program_path, # Send this as parameter to script
     target_path
     ] +  data_paths)
 
    print("Created File at "+target_path)

def createFloorPlan_svg(image_path = config.image_path, target_path = config.target_path,svg_path =""):
    import config 
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    blender_script_path = program_path+'/floorplan_to_PointClouds_in_blender.py'
    
    data_paths = [execution.SVG_polygons(image_path, svg_path)]
  
    check_output([blender_install_path,
     "-noaudio", # this is a dockerfile ubuntu hax fix
     "--background",
     "--python",
     blender_script_path,
     program_path, # Send this as parameter to script
     target_path
     ] +  data_paths)
    
    print("Created File at "+target_path)
    
def Placement_Info_from_plan(image_path = config.image_path, target_path = config.target_path, svg_path =""):
    import config 
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    blender_script_path = program_path+'/Placement_Info.py'

    data_paths = [execution.SVG_polygons(image_path, svg_path)]
  
    check_output([blender_install_path,
     "-noaudio", # this is a dockerfile ubuntu hax fix
     "--background",
     "--python",
     blender_script_path,
     program_path, # Send this as parameter to script
     target_path
     ] +  data_paths)
    
    R,_,_ = pl.extract_polygons(config)
    D = []
    for i in R:
        rooms = [i for i in pl.Room_add_list]
        if i.split('.')[0] in rooms:
            D += pl.add_objects_to_room(i,config)

    t = open("Placed_polygons.txt",'w')
    for i in D:
        if '_' in i.name:
            t.write(i.name+',')
            t.write(str(i.center())[1:-1]+',')
            t.write(str(i.rotated%360)+'\n')
    t.close()
    print("Generated_Placement_Info")
    return data_paths
    

def load_file(file_name, voxel_size=0.02):
    import MinkowskiEngine as ME
    pcd = o3d.io.read_point_cloud(file_name)
    coords = np.array(pcd.points)*1000
    feats = np.array(pcd.colors)
    quantized_coords = np.floor(coords / voxel_size)
    inds = ME.utils.sparse_quantize(quantized_coords, return_index=True)
    return quantized_coords[inds]*0.02, feats[inds], pcd

def annotate(target_path = config.target_path, calc_an = True):
    import config 
    import time
    start = time.time()
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    #blender_script_path_pc = program_path+'/annotate.py'
    blender_script_path_pc = program_path+'/annotate-Blocky.py'
    with open(program_path+'/config.txt', 'r') as file:
        name = file.read().replace('\n', '')
    if name == "No usable rooms in Plan":
        return "No usable rooms in Plan"
    name = name[0:len(name)-8]
    rooms = [i for i in os.listdir(name+'/')]
    print(blender_script_path_pc)
    for i in rooms:
        filename = name+'/'+i+'/'+i+'.ply'
        pnts,cls,pcd = load_file(filename)
        with open(name+'/'+i+'/'+i+'_downsampled.npy', 'wb') as f:
            np.save(f, pnts)
        with open(name+'/'+i+'/'+i+'_downsampled(cls).npy', 'wb') as f:
            np.save(f, cls)
    if calc_an==True:
        check_output([blender_install_path,
         "-noaudio", # this is a dockerfile ubuntu hax fix
         "--background",
         "--python",
          # Send this as parameter to script
         blender_script_path_pc])
    
    os.remove(name+"_a.blend")
    print("Created Anotations")
    end = time.time()
    return end-start
    

    
def createFloorPlanPointCloud_svg(image_path = config.image_path, target_path = config.target_path,svg_path ="",calc_an = True):
    import config 
    # Place Random Objects
    data_paths = Placement_Info_from_plan(image_path = config.image_path, target_path = config.target_path, svg_path =svg_path)
    
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    blender_script_path_pc = program_path+'/floorplan_to_PointClouds_in_blender.py'

    #data_paths = [execution.SVG_polygons(image_path, svg_path)]
  
    check_output([blender_install_path,
     "-noaudio", # this is a dockerfile ubuntu hax fix
     "--background",
     "--python",
     blender_script_path_pc,
     program_path, # Send this as parameter to script
     target_path
     ] +  data_paths)
    
    anotation_time = annotate(target_path = config.target_path, calc_an=calc_an)
    
    
    print("Created File at "+target_path)
    print("Total_time_annotations: "+str(anotation_time)+' secs')
    
def createRender(image_path = config.image_path, target_path = config.target_path,svg_path =""):
    import config 
    
    program_path = config.program_path
    blender_install_path = config.blender_install_path
    blender_script_path_pc = program_path+'/Render.py'

    data_paths = [execution.SVG_polygons(image_path, svg_path)]
  
    check_output([blender_install_path,
     "-noaudio", # this is a dockerfile ubuntu hax fix
     "--background",
     "--python",
     blender_script_path_pc,
     program_path, # Send this as parameter to script
     target_path
     ] +  data_paths)
    
    return
    
  
