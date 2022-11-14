import bpy
import os
import numpy as np
import json
import sys
import math
import mathutils
from mathutils import Matrix, Vector
from archimesh.door_window_automation import *
import skimage
from skimage import io
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import open3d as o3d
import cv2

'''
Floorplan to Blender

FloorplanToBlender3d
Copyright (C) 2019 Daniel Westberg

This code read data from a file and creates a 3d model of that data.
RUN THIS CODE FROM BLENDER

The new implementation starts blender and executes this script in a new project
so tutorial below can be ignored if you don't want to do this manually in blender.

HOW TO: (old style)

1. Run create script to create data files for your floorplan image.
2. Edit path in this file to generated data files.
3. Start blender
4. Open Blender text editor
5. Open this file "alt+o"
6. Run script

This code is tested on Windows 10, Blender 2.79, in January 2019.
'''

'''
Our helpful functions
'''
    
def read_from_file(file_path):
    '''
    Read from file
    read verts data from file
    @Param file_path, path to file
    @Return data
    '''
    # Now read the file back into a Python list object
    with open(file_path+'.txt', 'r') as f:
        data = json.loads(f.read())
    return data

def init_object(name):
    # Create new blender object and return references to mesh and object
    mymesh = bpy.data.meshes.new(name)
    myobject = bpy.data.objects.new(name, mymesh)
    bpy.context.collection.objects.link(myobject)
    return myobject, mymesh

def average(lst): 
    return sum(lst) / len(lst) 

def get_mesh_center(verts):
    # Calculate center location of a mesh from verts
    x=[]
    y=[]
    z=[]

    for vert in verts:
        x.append(vert[0])
        y.append(vert[1])
        z.append(vert[2])

    return [average(x), average(y), average(z)]

def subtract_center_verts(verts1, verts2):
    # Remove verts1 from all verts in verts2, return result, verts1 & verts2 must have same shape!
    for i in range(0, len(verts2)):
        verts2[i][0] -= verts1[0]
        verts2[i][1] -= verts1[1]
        verts2[i][2] -= verts1[2]
    return verts2

def create_custom_mesh(objname, verts, faces, pos = None, rot = None, mat = None, cen = None):
    '''
    @Param objname, name of new mesh
    @Param pos, object position [x, y, z]
    @Param vertex, corners
    @Param faces, buildorder
    '''
    # Create mesh and object
    myobject, mymesh = init_object(objname)

    # Rearrange verts to put pivot point in center of mesh
    # Find center of verts
    center = get_mesh_center(verts)
    # Subtract center from verts before creation
    proper_verts = subtract_center_verts(center,verts)

    # Generate mesh data
    mymesh.from_pydata(proper_verts, [], faces)
    # Calculate the edges
    mymesh.update(calc_edges=True)

    parent_center = [0,0,0]
    if cen is not None:
        parent_center = [int(cen[0]/2),int(cen[1]/2),int(cen[2])]

    # Move object to input verts location
    myobject.location.x = center[0] - parent_center[0]
    myobject.location.y = center[1] - parent_center[1]
    myobject.location.z = center[2] - parent_center[2]

    # Move to Custom Location
    if pos is not None:
        myobject.location.x += pos[0]
        myobject.location.y += pos[1]
        myobject.location.z += pos[2]

    if rot is not None:
        myobject.rotation_euler = rot

    # add contraint for pivot point
    # pivot = myobject.constraints.new(type='PIVOT')
    
    # add material
    if mat is None: # add random color
        myobject.data.materials.append(create_mat( np.random.randint(0, 40, size=4))) #add the material to the object
    else:
        myobject.data.materials.append(mat) #add the material to the object
    return myobject

def create_mat(rgb_color):
    mat = bpy.data.materials.new(name="MaterialName") #set new material to variable
    mat.diffuse_color = rgb_color #change to random color
    return mat

'''
Main functionallity here!
'''
def main(argv):
    '''
    Create Walls
    All walls are square
    Therefore we split data into two files
    '''

    # Remove starting object cube
    # Select all
    import sys
    print(sys.exec_prefix)
    
    objs = bpy.data.objects
    objs.remove(objs["Cube"], do_unlink=True)

    if(len(argv) > 7): # Note YOU need 8 arguments!
        program_path = argv[5]
        target = argv[6]
    else:
        exit(0)


    '''
    Instantiate
    '''
    for i in range(7,len(argv)):
        base_path = argv[i]
        send_floorplan(base_path, program_path, i)
    '''
    Send correct exit code
    '''
    bpy.ops.wm.save_as_mainfile(filepath=program_path + target + ".blend")


def send_floorplan(base_path,program_path, name=0):

    parent, parent_mesh = init_object("Floorplan"+str(name))
    
    # base_path = base_path.replace('/','\\')

    path_to_wall_faces_file = program_path +"/" + base_path + "wall_faces"
    path_to_wall_verts_file = program_path +"/" + base_path + "wall_verts"

    path_to_top_wall_faces_file = program_path +"/" + base_path + "top_wall_faces"
    path_to_top_wall_verts_file = program_path +"/" + base_path + "top_wall_verts"

    path_to_floor_faces_file = program_path +"/" +base_path + "floor_faces"
    path_to_floor_verts_file = program_path +"/" +base_path + "floor_verts"

    path_to_rooms_faces_file = program_path +"/" + base_path + "rooms_faces"
    path_to_rooms_verts_file = program_path +"/" + base_path + "rooms_verts"
    
    path_to_icon_faces_file = program_path +"/" + base_path + "icons_faces"
    path_to_icon_verts_file = program_path +"/" + base_path + "icons_verts"
    
    path_to_room_name_file = program_path +"/" + base_path + "room_names"
    path_to_icon_name_file = program_path +"/" + base_path + "icon_names"
    
    # path_to_window_faces_file = program_path +"/" + base_path + "windows_faces"
    # path_to_window_verts_file = program_path +"/" + base_path + "windows_verts"
    
# TODO add window, doors here!
#    path_to_windows_faces_file = program_path +"\\" + base_path + "windows_faces"
#    path_to_windows_verts_file = program_path +"\\" + base_path + "windows_verts"

    path_to_transform_file = program_path+"/" + base_path + "transform"

    '''
    Get transform
    '''
    # read from file
    transform = read_from_file(path_to_transform_file)

    rot = transform["rotation"]
    pos = transform["position"]
    
    # Calculate and move floorplan shape to center
    cen = transform["shape"]

    # rotate to fix mirrored floorplan
    parent.rotation_euler = (0, math.pi, 0)

    # Set Cursor start
    bpy.context.scene.cursor.location = (0,0,0)

    '''
    Create Top  Walls
    '''
    # get image top wall data
    verts = read_from_file(path_to_top_wall_verts_file)
    faces = read_from_file(path_to_top_wall_faces_file)

    # Create mesh from data
    boxcount = 0
    wallcount = 0

    # Create parent
    top_wall_parent, top_wall_parent_mesh = init_object("TopWalls")

    for i in range(0, len(verts)):
        roomname = "TopWalls"+str(i)
        obj = create_custom_mesh(
            roomname, verts[i], faces[i], pos=pos, rot=rot, cen=cen, mat=create_mat((0.5, 0.5, 0.5, 1)))
        obj.parent = top_wall_parent

    top_wall_parent.parent = parent
    
    obj = bpy.context.scene.objects["TopWalls"]
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.select_all( action = 'SELECT' )
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.mesh.extrude_context_move(
    TRANSFORM_OT_translate={"value":(-0, -0, 2.5)}
    )
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
    
    path_to_door_verts_file = program_path +"/" + base_path + "doors_verts"
    path_to_door_faces_file = program_path +"/" + base_path + "doors_faces"
    door_verts = read_from_file(path_to_door_verts_file)
    door_faces = read_from_file(path_to_door_faces_file)
    # Create parent
    door_parent, door_parent_mesh = init_object("Door_Walls")
    door_parent.parent = parent
    
    for i in range(0, len(door_verts)):
        roomname = "Door_Walls"+str(i)
        obj = create_custom_mesh(
            roomname, door_verts[i], door_faces[i], pos=[0,0,-1-2.1], rot=rot, cen=cen, mat=create_mat((0.5, 0.5, 0.5, 1)))
        obj.parent = door_parent
    
    obj = bpy.context.scene.objects["Door_Walls"]
    bpy.context.view_layer.objects.active = obj
    
    for i in obj.children:
        i.select_set(True)
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.mesh.extrude_context_move(
    TRANSFORM_OT_translate={"value":(-0, -0, (2.5-2.1))}
    )
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
    
    '''
    '''
    path_to_window_verts_file = program_path +"/" + base_path + "windows_verts"
    path_to_window_faces_file = program_path +"/" + base_path + "windows_faces"
    window_verts = read_from_file(path_to_window_verts_file)
    window_faces = read_from_file(path_to_window_faces_file)
    
    # Create parent
    win_wall_parent, win_wall_parent_mesh = init_object("Window_Walls")
    win_wall_parent.parent = parent
    
    for i in range(0, len(window_verts)):
        roomname = "Window_Walls"+str(i)
        obj = create_custom_mesh(
            roomname, window_verts[i], window_faces[i], pos=[0,0,-1-1.15-1], rot=rot, cen=cen, mat=create_mat((0.5, 0.5, 0.5, 1)))
        obj.parent = win_wall_parent
    
    obj = bpy.context.scene.objects["Window_Walls"]
    bpy.context.view_layer.objects.active = obj
    
    for i in obj.children:
        i.select_set(True)
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.mesh.extrude_context_move(
    TRANSFORM_OT_translate={"value":(-0, -0, (2.5-2.15))}
    )
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
    
    
    window_verts = read_from_file(path_to_window_verts_file)
    window_faces = read_from_file(path_to_window_faces_file)
    
    # Create parent
    bot_win_wall_parent, bot_win_wall_parent_mesh = init_object("Bot_Window_Walls")
    bot_win_wall_parent.parent = parent
    
    for i in range(0, len(window_verts)):
        roomname = "Bot_Window_Walls"+str(i)
        obj = create_custom_mesh(
            roomname, window_verts[i], window_faces[i], pos=[0,0,-1], rot=rot, cen=cen, mat=create_mat((0.5, 0.5, 0.5, 1)))
        obj.parent = bot_win_wall_parent
    
    obj = bpy.context.scene.objects["Bot_Window_Walls"]
    bpy.context.view_layer.objects.active = obj
    
    for i in obj.children:
        i.select_set(True)
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.mesh.extrude_context_move(
    TRANSFORM_OT_translate={"value":(-0, -0, 1.15)}
    )
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
    
    pos[2] = -1
    '''
    Create Floor
    '''
    # get image wall data
    verts = read_from_file(path_to_floor_verts_file)
    faces = read_from_file(path_to_floor_faces_file)

    # Create mesh from data
    cornername="Floor"
    obj = create_custom_mesh(cornername, verts, [faces], pos=pos, mat=create_mat((40,1,1,1)), cen=cen)
    obj.parent = parent

    '''
    Create rooms
    '''
    
    # get image wall data
    verts = read_from_file(path_to_rooms_verts_file)
    faces = read_from_file(path_to_rooms_faces_file)

    # Create parent
    room_parent, room_parent_mesh = init_object("Rooms")
    
    room_names = read_from_file(path_to_room_name_file)
                   
    for i in range(0,len(verts)):
        roomname= room_names[i]
        obj = create_custom_mesh(roomname, verts[i], faces[i], pos=pos, rot=rot, cen=cen)
        obj.parent = room_parent

    room_parent.parent = parent
    
    '''
    Create icons
    '''
    
    # get image wall data
    verts = read_from_file(path_to_icon_verts_file)
    faces = read_from_file(path_to_icon_faces_file)

    # Create parent
    icon_parent, icon_parent_mesh = init_object("Objects")
    
    icon_names = read_from_file(path_to_icon_name_file)
                   
    for i in range(0,len(verts)):
        iconname= icon_names[i]
        obj = create_custom_mesh(iconname, verts[i], faces[i], pos=pos, rot=rot, cen=cen)
        obj.parent = icon_parent

    icon_parent.parent = parent
    
    parent, parent_mesh = init_object("Doors")
    path_to_transform_file = program_path+"/" + base_path + "transform"
    path_to_door_verts_file = program_path +"/" + base_path + "doors_verts"
    door_verts = read_from_file(path_to_door_verts_file)
    #centers_doors = np.array([i - mean_center for i in centers_doors])
    transform = read_from_file(path_to_transform_file)
    cen = transform["shape"]
    parent_center = [int(cen[0]/2),int(cen[1]/2),int(cen[2])]       

    x_y_dist = [[max(np.array(door_verts)[i][:,0])
                -min(np.array(door_verts)[i][:,0]),
                max(np.array(door_verts)[i][:,1])
                -min(np.array(door_verts)[i][:,1])]
                for i in range(len(door_verts))]
            
    m = DoorMake(ObjectProp_door,"D")
    for i,j in enumerate(door_verts):
        m.name = "Door"+str(i)
        m.ObjectProp['frame_width'] = max(x_y_dist[i])
        m.ObjectProp['frame_thick'] = 0.1
        m.execute()
        center = get_mesh_center(j)
        # Subtract center from verts before creation
        proper_verts = subtract_center_verts(center,j)
        move_rot = bpy.context.scene.objects["Door"+str(i)]
        if x_y_dist[i][0]<x_y_dist[i][1]:
            move_rot.rotation_euler = (math.pi,0,math.pi/2)
        else:
            move_rot.rotation_euler = (math.pi,0, 0)
        mean_center = np.mean(np.array(proper_verts), axis = 0)
        move_rot.location = [center[0] - parent_center[0],center[1] - parent_center[1],center[2] - parent_center[2]]
        if x_y_dist[i][0]<x_y_dist[i][1]:
            move_rot.location.x += -0.02
        else:
            move_rot.location.y +=0.02
        move_rot.parent = parent
    myobject = bpy.context.scene.objects["Doors"]
    myobject.rotation_euler = (0, math.pi, 0)
    myobject.location.z = 1
    
    parent, parent_mesh = init_object("Windows")
    path_to_transform_file = program_path+"/" + base_path + "transform"
    path_to_window_verts_file = program_path +"/" + base_path + "windows_verts"
    path_to_window_faces_file = program_path +"/" + base_path + "windows_faces"
    window_verts = read_from_file(path_to_window_verts_file)
    window_faces = read_from_file(path_to_window_faces_file)
    #centers_doors = np.array([i - mean_center for i in centers_doors])
    transform = read_from_file(path_to_transform_file)
    cen = transform["shape"]
    parent_center = [int(cen[0]/2),int(cen[1]/2),int(cen[2])]       

    x_y_dist = [[max(np.array(window_verts)[i][:,0])
                -min(np.array(window_verts)[i][:,0]),
                max(np.array(window_verts)[i][:,1])
                -min(np.array(window_verts)[i][:,1])]
                for i in range(len(window_verts))]
            
    m = WindowMake(ObjectProp_window,"W")
    for i,j in enumerate(window_verts):
        m.name = "Window"+str(i)
        m.ObjectProp['width'] = max(x_y_dist[i])
        m.ObjectProp['depth'] = min(x_y_dist[i])
        m.execute()
        center = get_mesh_center(j)
        # Subtract center from verts before creation
        proper_verts = subtract_center_verts(center,j)
        move_rot = bpy.context.scene.objects["Window"+str(i)]
        if x_y_dist[i][0]<x_y_dist[i][1]:
            move_rot.rotation_euler = (math.pi,0,math.pi/2)
        else:
            move_rot.rotation_euler = (math.pi,0, 0)
        mean_center = np.mean(np.array(proper_verts), axis = 0)
        move_rot.location = [center[0] - parent_center[0],center[1] - parent_center[1],center[2] - parent_center[2]]
        if x_y_dist[i][0]<x_y_dist[i][1]:
            move_rot.location.x += (m.ObjectProp['depth'])/2
        else:
            move_rot.location.y += -(m.ObjectProp['depth'])/2
        move_rot.parent = parent
    myobject = bpy.context.scene.objects["Windows"]
    myobject.rotation_euler = (0, math.pi, 0)
    myobject.location.z = 2.15
    
def Mesh_vectors(obj):
    o = obj
    vcos = [ o.matrix_world @ v.co for v in o.data.vertices ]
    x,y,z  = [ [ v[i] for v in vcos ] for i in range(3) ]
    return x,y,z

def Mesh_center(obj):
    x,y,z = Mesh_vectors(obj)
    findCenter = lambda l: ( max(l) + min(l) ) / 2
    center = [ findCenter(axis) for axis in [x,y,z] ]
    return center

def Bounding_Box(obj):
    x,y,z = Mesh_vectors(obj)
    findBox = lambda x,y,z: [min(x),min(y),min(z),max(x),max(y),max(z)]
    return findBox(x,y,z)

def Bounding_Box_mult(coll):
    l = []
    for i in coll.objects[:]:
        l.append(Bounding_Box(i))
    l = np.array(l)
    l= list(l[:,:3].min(axis=0))+list(l[:,3:].max(axis=0))
    return l

def unit_vector(vector):
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def select_obj(obj,first_obj=True):
    if first_obj==True:
        obj.select_set(True)
    if obj.children==():
        return 
    for i in obj.children:
        i.select_set(True)
        select_obj(i,first_obj=False)
        
def Room_Window_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Window_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
             list.append(i.name)
    return list

def Room_Object_List(roomname):
    room_obj = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Objects'].children:
        if check_inter(i,room_obj,xy=True):
             list.append(i.name)
    return list

def Room_Door_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Door_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
             list.append(i.name)
    return list

def is_inside(inner_box, outer_box,tol = 0):
    for k,i in enumerate(inner_box[:2]):
        if i>=outer_box[:2][k]-tol:
            continue
        else:
            return False
    for k,i in enumerate(inner_box[3:5]):
        if i<=outer_box[3:5][k]+tol:
            continue
        else:
            return False
    return True

def check_inter(obj1,obj2,xy=False,tol=0):
    box1 = Bounding_Box(obj1)
    box2 = Bounding_Box(obj2)
    overlap_1D = lambda b1,b2: b1[1]>=b2[0] and b2[1]>=b1[0]
    if is_inside(box1,box2)==True:
        return True
    elif is_inside(box2,box1)==True :
        return True
    else:
        x1,y1,z1 = [i-tol for i in box1[:3]]
        xm1,ym1,zm1 = [i+tol for i in box1[3:]]
        x2,y2,z2 = [i-tol for i in box2[:3]]
        xm2,ym2,zm2 = [i+tol for i in box2[3:]]
        if xy == False:
            inter = overlap_1D([x1,xm1],[x2,xm2]) and overlap_1D([y1,ym1],[y2,ym2]) and overlap_1D([z1,zm1],[z2,zm2])
        else:
            inter = overlap_1D([x1,xm1],[x2,xm2]) and overlap_1D([y1,ym1],[y2,ym2])
        if inter  == True:
            return True
        else:
            return False

def Bounding_Children_Box(obj):
    bpy.ops.object.select_all(action='DESELECT')
    select_obj(obj)
    l = []
    for i in bpy.context.selected_objects:
        print(i.data)
        if i.data != None and 'CTRL' not in i.name:
            l.append(Bounding_Box(i))
    l = np.array(l)
    l= list(l[:,:3].min(axis=0))+list(l[:,3:].max(axis=0))
    bpy.ops.object.select_all(action='DESELECT')
    return l

'''    
def load_file(file_name, voxel_size=0.02):
    import MinkowskiEngine as ME
    pcd = o3d.io.read_point_cloud(file_name)
    coords = np.array(pcd.points)
    feats = np.array(pcd.colors)
    quantized_coords = np.floor(coords / voxel_size)
    inds = ME.utils.sparse_quantize(quantized_coords, return_index=True)
    return quantized_coords[inds]*0.02, feats[inds], pcd
'''
# Start
if __name__ == "__main__":
    main(sys.argv)
    global directory
    directory = sys.argv[5]+'/'
    os.remove(directory+"rooms.txt")
    os.remove(directory+"rooms_info.txt")
    os.remove(directory+"objects.txt")
    text_file = open(directory+"rooms.txt","w")
    tf_room_info = open(directory+"rooms_info.txt","w")
    for i in bpy.data.objects['Rooms'].children:
        X,Y,Z = Mesh_vectors(i)
        for t in [X,Y,Z]:
            text_file.write(i.name+',')
            for no,j in enumerate(t):
                if no == len(t)-1:
                    n = text_file.write(str(j)+'\n')
                else:
                    text_file.write(str(j)+',')
        tf_room_info.write(i.name+'\n')
        Door_nos = [tf_room_info.write(i.split('s')[1]+',') for i in Room_Door_List(i.name)]
        tf_room_info.write('\n')
        Window_nos = [tf_room_info.write(i.split('s')[1]+',') for i in Room_Window_List(i.name)]
        tf_room_info.write('\n')
        Obj_nos = [tf_room_info.write(i+',') for i in Room_Object_List(i.name)]
        tf_room_info.write('\n')
    tf_room_info.close()  
    text_file.close()
    text_file = open(directory+"objects.txt","w")
    for i in bpy.data.objects['Objects'].children:
        xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(i)
        text_file.write(i.name+',')
        n = text_file.write(str(xmin)+','+str(ymin)+','+str(zmin)+','+str(xmax)+','+str(ymax)+','+str(zmax)+'\n')
    for j in bpy.data.objects['Doors'].children:
        xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Children_Box(j)
        text_file.write(j.name+',')
        n = text_file.write(str(xmin)+','+str(ymin)+','+str(zmin)+','+str(xmax)+','+str(ymax)+','+str(zmax)+'\n')
    for k in bpy.data.objects['Windows'].children:
        xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Children_Box(k)
        text_file.write(k.name+',')
        n = text_file.write(str(xmin)+','+str(ymin)+','+str(zmin)+','+str(xmax)+','+str(ymax)+','+str(zmax)+'\n')
    text_file.close()
    exit(0)
    