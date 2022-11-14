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
        create_floorplan(base_path, program_path, i)

    '''
    Save to file
    TODO add several save modes here!
    '''
    bpy.ops.wm.save_as_mainfile(filepath=program_path + target + ".blend") #"/floorplan"
    
    bpy.ops.export_mesh.stl(filepath=program_path + target + ".stl")

    '''
    Send correct exit code
    '''


def create_floorplan(base_path,program_path, name=0):

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

def Room_Object_List(roomname):
    room_obj = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Objects'].children:
        if check_inter(i,room_obj,xy=True):
             list.append(i.name)
    return list

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
        
def Room_Wall_List(roomname):
    list = []
    for i in bpy.data.objects['TopWalls'].children:
        if check_inter(bpy.data.objects[roomname],i):
             list.append(i.name)
    return list

def get_object(obj_name,typ):
    name = obj_name + '_'+str(typ)
    file_path = directory+'object.blend'
    inner_path = 'Collection'
    object_name = name
    bpy.ops.wm.append(filepath=os.path.join(file_path, inner_path, object_name),
    directory=os.path.join(file_path, inner_path),
    filename=object_name)
    return name
        
    
def PlaceObject(roomname,obj_name,place_box_obj,type,index):
    if isinstance(place_box_obj,str) == True:
        place_box = Bounding_Box(bpy.data.objects[place_box_obj])
        place_box.pop(5)
        place_box.pop(2)
    else:
        place_box = place_box_obj
    xmin,ymin,xmax,ymax = place_box
    x_length = xmax-xmin
    y_length = ymax-ymin
    Center = [(xmin+xmax)/2.0,(ymin+ymax)/2.0]
    name = get_object(obj_name,type)
    if index!=0:
        name = name + '.%03d'%(index)
    obj = bpy.data.objects[name]
    print(name)
    angle,wall_tail,wall_vect,dist = get_orientation(roomname, None, Center )
    xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(obj)
    if abs(angle) == pi/2:
        scale_x = y_length/abs(xmax-xmin)
        scale_y = x_length/abs(ymax-ymin)
    else:
        scale_x = x_length/abs(xmax-xmin)
        scale_y = y_length/abs(ymax-ymin)
    print(scale_x)
    print(scale_y)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.transform.resize(value=(scale_x,scale_y,1),orient_type='GLOBAL')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    ov=bpy.context.copy()
    ov['area']=[a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    bpy.ops.transform.rotate(ov,value=angle, orient_axis='Z',orient_type='GLOBAL')  
    bpy.ops.object.select_all(action='DESELECT')
    x, y ,z = Mesh_center(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.transform.translate(value=(-x+Center[0],-y+Center[1],0), orient_type='GLOBAL')  
    bpy.ops.object.select_all(action='DESELECT')
    obj.parent = bpy.data.objects['OBJS']
    for i in bpy.data.collections[name.split('.')[0]].objects[:]:
        bpy.data.collections['Collection'].objects.link(i)
    del_list = bpy.data.collections[name.split('.')[0]]
    bpy.data.collections.remove(del_list)
    return 

def conv_to_vectors(obj_name):
    b = Mesh_vectors(bpy.data.objects[obj_name])
    b = list(b)
    b.pop(2)
    b = [[i,j] for i,j in zip(b[0],b[1])]
    b.append(b[0])
    vectors = [{'vector':[i-j 
              for i,j in zip(b[k+1],b[k])],'tail':b[k]}
              for k in range(len(b)-1)]
    import numpy as np
    for i in vectors:
        i['mag'] = np.linalg.norm(i['vector'])
    axis_fix = np.array([1,0])
    for i in vectors:
        if i['vector'][1] == 0:
            i['direction'] = np.arccos(np.dot(i['vector'],axis_fix)/i['mag'])
        else:
            i['direction'] = -1*np.sign(i['vector'][1])*np.arccos(np.dot(i['vector'],axis_fix)/i['mag'])
    return vectors

def conv_to_lines(obj_name):
    b = Mesh_vectors(bpy.data.objects[obj_name])
    b = list(b)
    b.pop(2)
    b = [[i,j] for i,j in zip(b[0],b[1])]
    b.append(b[0])
    lines = [[b[i],b[i+1]] for i in range(len(b)-1)]
    return lines

def check_dist(line,point):
    xa, ya = line[0]
    xb, yb = line[1]
    A = ya-yb
    B = -(xa-xb)
    C = xa*yb-xb*ya
    D = (A**2+B**2)**0.5
    if int(D) == 0:
        return 0
    d = abs(A*point[0]+B*point[1]+C)/D
    return d

def Point_in_Room(roomname,point):
    from shapely.geometry import Polygon, Point
    vects = conv_to_vectors(roomname)
    points_x = [i['tail'][0] for i in vects]
    points_y = [i['tail'][1] for i in vects]
    p = Polygon(list(zip(points_x, points_y)))
    if p.buffer(1e-2).contains(Point(point[0],point[1])):
        return True
    else:
        return False

def get_orientation(roomname, object_name, point = None):
    if object_name !=None and (object_name not in Room_Object_List(roomname)):
        print("Please input valid data")
        return None
    lines_room = conv_to_lines(roomname)
    if object_name !=None:
        vec_object = conv_to_vectors(object_name)
    orent_inds = []
    dists = []
    sum = [0,0]
    if point == None:
        for i in vec_object:
            sum = [sum[0] + i['tail'][0], sum[1] + i['tail'][1]]
        mean_point = [i/len(vec_object) for i in sum]
    else:
        mean_point = point
    for i in lines_room:
        print(i)
        d = check_dist(i,mean_point)
        dists.append(d)
    print(dists)
    near_wall = False
    for i in dists:
        if i < 0.1:
            near_wall = True
    if near_wall == True:
        print('Near')
        for l,i in enumerate(dists):
            if i < 0.1:
                orent_inds.append(l)
    else:
        print('Far')
        temp = True
        while temp:
            for l,i in enumerate(dists):
                wall = lines_room[l]
                vect = np.array(wall[1]) - np.array(wall[0])
                dim = np.where(np.array(vect)!=0)[0][0] 
                seg = [wall[1][dim] ,wall[0][dim] ]
                check = min(seg) <= mean_point[dim] <= max(seg)
                if i == min(dists) and check ==True :
                    print(dists)
                    orent_inds.append(l)
                    temp = False
                elif i == min(dists):
                    dists[l] =50000
                    break
    vec_room = conv_to_vectors(roomname)
    orentation = []
    wall_vect = []
    snapping_dist = []
    wall_tail = []
    for i in orent_inds:
        orentation.append(vec_room[i]['direction'])
        wall_vect.append(vec_room[i]['vector'])
        snapping_dist.append(dists[i])
        wall_tail.append(vec_room[i]['tail'])
    print(orentation,snapping_dist,wall_tail,wall_vect)
    '''
    if object_name!=None:
        if len(orent_inds) == 2:
            m =0
            angle = None
            ind = 0
            for k,i in enumerate(vec_object):
                if i['direction'] in orentation:
                    if i['mag']>m:
                        m=i['mag']
                        angle = i['direction']
                        ind = k
                    else:
                        continue
            if angle == None:
                orentation= orentation[0]
                wall_vect = wall_vect[0]
                snapping_dist = snapping_dist[0]
                wall_tail = wall_tail[0]
            else:
                orentation = angle
                wall_vect = wall_vect[ind]
                snapping_dist = snapping_dist[ind]
                wall_tail = wall_tail[ind]
            
        else:
            orentation= orentation[0]
            wall_vect = wall_vect[0]
            snapping_dist = snapping_dist[0]
            wall_tail = wall_tail[0]
    else:
    '''
    orentation= orentation[0]
    wall_vect = wall_vect[0]
    snapping_dist = snapping_dist[0]
    wall_tail = wall_tail[0]
    return orentation,wall_tail, wall_vect, snapping_dist

def create_object_index():
    dic = {
    'Closet':4,
    'ElectricalAppliance':3,
    'SaunaBench':1,
    'Sink':2,
    'Toilet':5,
    'Curtain':3,
    'Bed':4,
    'Table':10,
    'Diningtable':3,
    'Desk':7,
    'Sofa':6,
    'Bookshelf':2,
    'Picture':8,
    'Counter':5,
    'Chair':8,
    'Bathtub':3,
    'Shower':1
    }
    index = {}
    for i in dic:
        for j in range(dic[i]):
            index[i+'_'+str(j+1)] = 0
    return index

def Populate_Room(roomname,index):
    import numpy as np
    import random as rd
    if index == None:
        index = create_object_index()    
    Type_List={
    'Kitchen':{
        'Closet':[1,2],
        'ElectricalAppliance':[1],
        'Sink':[2],
        'Curtain':[1,2,3],
        'Toilet':[1]
        },
    'Bath':{
        'Toilet':[1],
        'Sink':[1],
        'Closet':[1,2],
        'Curtain':[1,2,3]
        },
    'Bedroom':{
        'Closet':[1,2],
        'Curtain':[1,2,3],
        'Toilet':[1]
        },
    'LivingRoom':{
        'Closet':[1,2],
        'Curtain':[1,2,3],
        'Toilet':[1]
        } 
    }
    polygons = Room_Object_List(roomname)
    for i in polygons:
        obj_name = i.split('.')[0]
        if obj_name in Type_List[roomname.split('.')[0]]:
            type = Type_List[roomname.split('.')[0]][obj_name]
        else:
            continue
        rd.shuffle(type)
        type = type[0]
        PlaceObject(roomname,obj_name,i,type,index[obj_name+'_'+str(type)])
        index[obj_name+'_'+str(type)] +=1
    return index

def create_plane(name, loc, width, height):
    bpy.ops.mesh.primitive_plane_add(size=1,
    enter_editmode=False, align='WORLD',
    location=(0, 0, 0), scale=(1, 1, 1))
    bpy.data.objects['Plane'].name = name
    bpy.data.objects[name].scale.x = width
    bpy.data.objects[name].scale.y = height
    obj = bpy.data.objects[name]
    bpy.data.objects[name].parent = bpy.data.objects['Objects']
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.transform.translate(value=(loc[0],loc[1],0), orient_type='GLOBAL')  
    bpy.ops.object.select_all(action='DESELECT')
    return 


def bbox_to_pol(xmin, ymin, xmax, ymax,tol = 0):
    return [[xmin+tol, ymin+tol],
            [xmax-tol,ymin+tol],
            [xmax-tol,ymax-tol],
            [xmin+tol, ymax-tol]]
    
        
def Room_Window_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Window_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
             list.append(i.name)
    return list

def Room_Bot_Window_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Bot_Window_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
             list.append(i.name)
    return list

def Room_Door_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Door_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
             list.append(i.name)
    return list

def create_window_planes(roomname):
    room = bpy.data.objects[roomname] 
    h = 0.2
    x,y,z = Mesh_center(room)
    for i in Room_Window_List(roomname):
        xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(bpy.data.objects[i])
        center_x,center_y,center_z = Mesh_center(bpy.data.objects[i])
        print([center_x,center_y,center_z])
        if xmax-xmin>ymax-ymin:
            w = xmax-xmin
            line1 = [[xmin,ymax],[xmax,ymax]]
            line2 = [[xmin,ymin],[xmax,ymin]]
            d1 = check_dist(line1,[x,y])
            d2 = check_dist(line2,[x,y])
            if d1<d2:
                center_y = ymax
                create_plane('Curtain', [center_x,center_y+h/2],w,h)
            else:
                center_y = ymin
                create_plane('Curtain', [center_x,center_y-h/2],w,h)
        else:
            w = ymax-ymin
            line1 = [[xmax,ymin],[xmax,ymax]]
            line2 = [[xmin,ymin],[xmin,ymax]]
            d1 = check_dist(line1,[x,y])
            d2 = check_dist(line2,[x,y])
            if d1<d2:
                center_x = xmax
                create_plane('Curtain',[center_x+h/2,center_y],h,w)
            else:
                center_x = xmin
                create_plane('Curtain',[center_x-h/2,center_y],h,w)
    return

def select_obj(obj,first_obj=True):
    if first_obj==True:
        obj.select_set(True)
    if obj.children==():
        return 
    for i in obj.children:
        i.select_set(True)
        select_obj(i,first_obj=False)
        
def obj_xy_dims(obj):
    xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(obj)
    t1 = xmax-xmin
    t2 = ymax-ymin
    return [t1,t2]
     
def random_point_snap(roomname,obj_name,type,index):
    import random as r
    from shapely.geometry import Point, Polygon
    if index == None:
        index = create_object_index() 
    ind = index[obj_name+'_'+str(type)]   
    name = get_object(obj_name,type)
    if ind!=0:
        name = name + '.%03d'%(ind)
    obj = bpy.data.objects[name] 
    xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(bpy.data.objects[roomname])
    while True:
        x = r.uniform(xmin,xmax)
        y = r.uniform(ymin,ymax)
        poly = conv_to_vectors(roomname)
        poly = Polygon([i['tail'] for i in poly])
        point = Point(x,y)
        if poly.contains(point)==True:
            break
    print([x,y])
    xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(obj)
    center = [(xmin+xmax)/2,(ymin+ymax)/2] 
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.transform.translate(value=(-center[0]+x,-center[1]+y,0), 
     orient_type='GLOBAL',
     orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
     orient_matrix_type='GLOBAL', 
     constraint_axis=(True, True, True),
     mirror=True, 
     use_proportional_edit=False, 
     proportional_edit_falloff='SMOOTH', 
     proportional_size=1, 
     use_proportional_connected=False, 
     use_proportional_projected=False)
    bpy.ops.object.select_all(action='DESELECT')
    snap_object(roomname,name)
    return index

def Bb_Center_Clearence(name):
    coll = bpy.data.collections[name.split('.')[0]]
    xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box_mult(coll)
    Clear = max([(ymax-ymin)/2,(xmax-xmin)/2])
    cx = (xmin+xmax)/2
    cy = (ymin+ymax)/2
    cz = (zmin+zmax)/2
    return cx,cy,cz,Clear

def random_place(roomname,obj_name,type,index):
    import time as t
    index = random_point_snap(roomname,obj_name,type,index)
    ind = index[obj_name+'_'+str(type)] 
    name = obj_name+'_'+str(type)
    if ind!=0:
        name = name + '.%03d'%(ind)
    start = t.time()
    while True:
        stop = False
        print(stop)
        print(roomname)
        doors = [bpy.data.objects[i] for i in Room_Door_List(roomname)]
        windows = [bpy.data.objects[i] for i in Room_Window_List(roomname)]
        objects = [bpy.data.objects[i.name] for i in bpy.data.objects['OBJS'].children]
        obj = bpy.data.objects[name] 
        x,y,z,clear = Bb_Center_Clearence(name)
        print(doors)
        for i in doors:
            x_d,y_d,z_d = Mesh_center(i)
            clearence = max(obj_xy_dims(i))*2
            print(((x_d-x)**2+(y_d-y)**2)**0.5)
            print(clearence)
            if (((x_d-x)**2+(y_d-y)**2)**0.5-clear)<clearence:
                stop = True
                print("DOOR")
        for i in windows:
            if check_inter(obj,i,xy=True):
                stop = True
                print("WINDOW")
        for i in objects:
            if check_inter(obj,i,xy=True,tol=0.01):
                stop = True
                print("OBJECTS")
        if stop == True:
            remove_collection(name)
            end = t.time()
            if end - start >100:
                return index
            random_point_snap(roomname,obj_name,type,index)
            continue
        else:
            break
    obj = bpy.data.objects[name] 
    obj.parent = bpy.data.objects['OBJS']
    for i in bpy.data.collections[name.split('.')[0]].objects[:]:
        bpy.data.collections['Collection'].objects.link(i)
    del_list = bpy.data.collections[name.split('.')[0]]
    bpy.data.collections.remove(del_list)
    index[obj_name+'_'+str(type)] +=1
    return index
def remove_collection(name):
    del_list = bpy.data.collections[name.split('.')[0]]
    for i in del_list.objects[:]:
        bpy.data.objects.remove(i)
    bpy.data.collections.remove(del_list)
    return

def room_perimeter(roomname):
    from shapely.geometry import Polygon
    poly = conv_to_vectors(roomname)
    poly = Polygon([i['tail'] for i in poly])
    return poly.length

def get_room_objects_quant(roomname):
    dt = {'Bedroom':{'Bed':1,
                       'Desk':1
                       },
            'LivingRoom':{'Sofa':1,
                          'Bookshelf':1
                          },
            'Kitchen':{'Closet':1
                    },
            }
    return dt[roomname.split('.')[0]]

def Bb_peri(obj):
    from math import pi
    l = []
    obj = bpy.data.objects[obj]
    angle = obj.rotation_euler.z
    bpy.ops.object.select_all(action='DESELECT')
    select_obj(obj,first_obj=True)
    selection_names = [obj for obj in bpy.context.selected_objects]
    bpy.ops.object.select_all(action='DESELECT')
    for i in selection_names[:]:
        l.append(Bounding_Box(i))
    l = np.array(l)
    l= list(l[:,:3].min(axis=0))+list(l[:,3:].max(axis=0))
    xmin,ymin,zmin,xmax,ymax,zmax = l
    t1 = xmax-xmin
    t2 = ymax-ymin
    if angle in [0,pi]:
        return t1
    else:
        return t2

def objs_in_room(roomname):
    room_obj = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['OBJS'].children:
        if check_inter(i,room_obj,xy=True):
             list.append(i)
    return list

def Add_random_objs(index):
    if index == None:
        index = create_object_index()
    f = open('Placed_polygons.txt','r')
    names = []
    Cents = []
    rots = []
    for i in f.readlines():
        names.append(i.split(',')[0])
        Cents.append([float(i.split(',')[1]),float(i.split(',')[2])])
        rots.append(float(i.split(',')[3][:-2]))
        
    for i,j in enumerate(names):
        typ = int(j.split('_')[1])
        obj_name = j.split('_')[0]
        ind = index[obj_name+'_'+str(typ)]   
        name = get_object(obj_name,typ)
        if ind!=0:
            name = name + '.%03d'%(ind)
        print(index)
        obj = bpy.data.objects[name] 
        obj.location.x = Cents[i][0]
        obj.location.y = Cents[i][1]
        obj.rotation_euler.z += math.pi*rots[i]/180
        obj = bpy.data.objects[name] 
        obj.parent = bpy.data.objects['OBJS']
        for i in bpy.data.collections[name.split('.')[0]].objects[:]:
            bpy.data.collections['Collection'].objects.link(i)
        del_list = bpy.data.collections[name.split('.')[0]]
        bpy.data.collections.remove(del_list)
        index[obj_name+'_'+str(typ)] +=1
    return index
     
def Room_populate(roomname,index):
    global dict_type
    dict_type = {
    'Closet':4,
    'ElectricalAppliance':3,
    'SaunaBench':1,
    'Sink':2,
    'Toilet':5,
    'Curtain':3,
    'Bed':4,
    'Table':10,
    'Diningtable':3,
    'Desk':7,
    'Sofa':6,
    'Bookshelf':2,
    'Picture':8,
    'Counter':5,
    'Chair':8,
    'Bathtub':3,
    'Shower':1
    }
    import random as r
    if index == None:
        init_object('OBJS')
    create_window_planes(roomname)
    index = Populate_Room(roomname,index)
    return index

''' 
Per_r = room_perimeter(roomname)
    Per = Per_r
    for i in objs_in_room(roomname):
        Per += -Bb_peri(i.name)
    for i in dict:
        type = r.randint(1,dict_type[i])
        if dict[i] ==None and 2*Bb_peri(i+'_'+str(type))<Per:
            index = random_place(roomname,i,type,index)
            '''
            
def set_base_path(base_path):
    global BasePath
    BasePath = base_path
    if not os.path.exists(base_path):
        os.makedirs(base_path + RGBPath)
        os.makedirs(base_path + DepthPath)
        os.makedirs(base_path + EXRDepthPath)


def set_camera_fov(fov):
    global CameraFOV
    CameraFOV = fov


def set_scale(scale):
    global DepthScale
    DepthScale = scale


def set_image_width_and_height(width, height):
    global ImageWidth
    global ImageHeight
    global ox
    global oy
    global K
    global Kinv
    ImageWidth = width
    ImageHeight = height
    ox = ImageWidth/2
    oy = ImageHeight/2
    K = np.array([[fx, 0, ox], [0, fy, oy], [0, 0, 1]], dtype=np.float32)
    Kinv = np.linalg.inv(K)


def set_depth_threshold(threshold):
    global MaxDepth
    MaxDepth = threshold


def set_camera_properties(camera_name="Camera", inv_camera=True):
    camera = bpy.data.cameras[camera_name]
    camera.type = 'PERSP'
    camera.lens_unit = 'FOV'
    camera.angle = CameraFOV
    camera.sensor_fit = 'AUTO'
    camera.sensor_width = 32.0
    # clip start/end in unit defined by Scene Should be meters
    print(camera.clip_start, type(camera.clip_start))
    print(camera.clip_end, type(camera.clip_end))
    camera.clip_start = 0.4  # meters
    camera.clip_end = 10 # meters
    # bpy.data.objects[cameraName].rotation_mode = 'QUATERNION'
    if inv_camera:
        print("InvertCamera is True", inv_camera)
        bpy.data.objects[camera_name].scale = 1, -1, -1


def set_renderer_properties(scene):
    print(scene.render.engine, type(scene.render.engine))
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = ImageWidth
    scene.render.resolution_y = ImageHeight
    scene.render.resolution_percentage = 100


def set_scene_properties(scene_name='Scene'):
    print(bpy.data.scenes[scene_name], type(bpy.data.scenes[scene_name]))
    scene = bpy.data.scenes[scene_name]
    set_renderer_properties(scene)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.system_rotation = 'RADIANS'


def get_key_frame(scene_name='Scene'):
    scene = bpy.data.scenes[scene_name]
    return scene.frame_current


def get_camera(camera_name='Camera'):
    return bpy.data.cameras[camera_name]


def get_camera_as_object(camera_name='Camera'):
    return bpy.data.objects[camera_name]


def get_camera_transformation(camera_name='Camera'):
    camera = get_camera_as_object(camera_name)
    return camera.matrix_world


def get_scene_start_frame(scene='Scene'):
    return bpy.data.scenes[scene].frame_start


def get_scene_end_frame(scene='Scene'):
    return bpy.data.scenes[scene].frame_end


def update_scene(scene='Scene'):
    bpy.data.scenes[scene].update()


def increment_key_frame(scene_name='Scene'):
    scene = bpy.data.scenes[scene_name]
    scene.frame_set(scene.frame_current + 1)


def reset_key_frame(scene_name='Scene'):
    scene = bpy.data.scenes[scene_name]
    scene.frame_set(0)


def build_nodes():
    print("Building Nodes")
    # switch on nodes
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)
    # create input render layer node
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = 185,285
    # create output node
    v = tree.nodes.new('CompositorNodeViewer')
    v.location = 750,80
    v.use_alpha = False
    multiplier = tree.nodes.new('CompositorNodeMapValue')
    multiplier.location = 450, 80
    multiplier.size[0] = 1000
    output_node = tree.nodes.new('CompositorNodeOutputFile')
    output_node.location = 750, 285
    output_node.base_path = BasePath + RGBPath
    output_node.file_slots[0].path = RGBFileNameFormat
    output_node.file_slots[0].use_node_format = True
    output_node.format.color_mode = 'RGBA'
    output_node.format.color_depth = '8'
    output_node.format.file_format = 'PNG'
    outputNodeZbuffer = tree.nodes.new('CompositorNodeOutputFile')
    outputNodeZbuffer.location = 750,185
    outputNodeZbuffer.base_path = BasePath + EXRDepthPath
    outputNodeZbuffer.file_slots[0].path = RGBFileNameFormat
    outputNodeZbuffer.file_slots[0].use_node_format = False
    outputNodeZbuffer.file_slots[0].format.file_format = "OPEN_EXR"
    outputNodeZbuffer.file_slots[0].format.color_mode = 'RGB'
    print(outputNodeZbuffer.format.color_depth)
    outputNodeZbuffer.file_slots[0].format.color_depth = '32'
    # Links
    links.new(rl.outputs[2], multiplier.inputs[0])
    links.new(multiplier.outputs[0], v.inputs[0])  # link Image output to Viewer input
    links.new(rl.outputs[0], output_node.inputs[0])  # link Image output to Viewer input
    links.new(rl.outputs[2], outputNodeZbuffer.inputs[0])

def get_depth_map():
    # get viewer pixels
    pixels = bpy.data.images['Viewer Node'].pixels
    # zMap reports depth in mm from camera
    # copy buffer to numpy array for faster manipulation
    depthMap = np.zeros((ImageHeight, ImageWidth), dtype=np.uint16)
    zBuffer = np.array(pixels[:])
    print(zBuffer.shape)
    for c in range(0, ImageWidth):
        for r in range(0, ImageHeight):
            # Blender stores the image in column major format, numpy uses row major
            index = r * ImageWidth * 4 + c * 4
            red = zBuffer[index]
            green = zBuffer[index + 1]
            blue = zBuffer[index + 2]
            alpha = zBuffer[index + 3]
            if (red != green or green != blue):
                print("Failed", alpha, red, green, blue)
                return;
            depth = red
            if(depth > MaxDepth):
                depth = 0
            # New fix for the warped image
            # Z map reports the length along the ray
            # I am interested in the Z component of the vector that represents the point
            v = np.array([c, r, 1], dtype=np.float32)
            K_cal = get_calibration_matrix_K_from_blender(bpy.data.objects['Camera'].data)
            K_cal = np.array(K_cal)
            Kinv_cal = np.linalg.inv(K_cal)
            n = Kinv_cal.dot(v)
            #n = n / np.linalg.norm(n);
            n = n * depth
            # Dirty fix, Some reason the image is flipped on the x axis 'ImageHeight - 1 - r' to correct
            # depthMap[ImageHeight - 1 - r, c] = np.uint16(depth * DepthScale)
            depthMap[ImageHeight - 1 - r, c] = np.uint16(n[2] * DepthScale)
    return depthMap


def build_translation_and_rotation(x, y, z, rx, ry, rz):
    rotation = mathutils.Vector()
    rotation.x = np.radians(rx)
    rotation.y = np.radians(ry)
    rotation.z = np.radians(rz)
    translation = mathutils.Vector()
    translation.x = x
    translation.y = y
    translation.z = z
    return translation, rotation


def set_camera_location_and_rotation(translation, rotation, camera_name='Camera'):
    camera = bpy.data.objects[camera_name]
    camera.location = translation
    camera.rotation_quaternion = rotation


def save_data(depth_maps, all_translations=None, all_rotations=None, timestamps=None):
    print("Starting Save")
    if not len(depth_maps) == len(all_translations) or not len(depth_maps) == len(all_rotations):
        print('ERROR')
    print("Opening files")
    print(len(all_translations))
    print(len(all_rotations))
    print(len(timestamps))
    if not os.path.isdir(BasePath + DepthPath):
        os.mkdir(BasePath + DepthPath)
    ground_truth = open(BasePath + GroundTruth, 'w')
    depth = open(BasePath + Depth, 'w')
    rgb = open(BasePath + RGB, 'w')
    print("Saving Files")
    if len(depth_maps) == 0:
        for i in range(len(timestamps)):
            depthName = str(timestamps[i]) + '.png'
            depth.write(str(timestamps[i]) + ' ' + DepthPath + depthName + '\n')
            num = str(timestamps[i])
            if timestamps[i] < 1000:
                num = '0'+num
            if timestamps[i] < 100:
                num = '0'+num
            if timestamps[i] < 10:
                num = '0'+num
            rgb.write(str(timestamps[i]) + ' ' + RGBPath + RGBFileNameFormat + num + EXT + '\n')
            ground_truth.write(str(timestamps[i]) + ' ' + "%.4f" % all_translations[i].x + ' ' + "%.4f" % all_translations[i].y + ' ' + "%.4f" % all_translations[i].z + ' ' +
                            "%.4f" % all_rotations[i].x + ' ' + "%.4f" % all_rotations[i].y + ' ' + "%.4f" % all_rotations[i].z + ' ' + "%.4f" % all_rotations[i].w + '\n')
    for i in range(len(depth_maps)):
        # print("Iteration ", i)
        depthName = str(timestamps[i]) + '.png'
        depth.write(str(timestamps[i]) + ' ' + DepthPath + depthName + '\n')
        depthMap = depth_maps[i]
        # plugin broken for some reason
        #io.imsave(BasePath + DepthPath + depthName, skimage.img_as_uint(depthMap), plugin='freeimage')
        io.imsave(BasePath + DepthPath + depthName, skimage.img_as_uint(depthMap))
        num = str(timestamps[i])
        if(timestamps[i] < 1000):
            num = '0'+num
        if(timestamps[i] < 100):
            num = '0'+num
        if(timestamps[i] < 10):
            num = '0'+num
        rgb.write(str(timestamps[i]) + ' ' + RGBPath + RGBFileNameFormat + num + EXT + '\n')
        rotation_quaternion = all_rotations[i]
        ground_truth.write(str(timestamps[i]) + ' ' + "%.4f" % all_translations[i].x + ' ' + "%.4f" % all_translations[i].y + ' ' + "%.4f" % all_translations[i].z + ' ' +
                            "%.4f" % all_rotations[i].x + ' ' + "%.4f" % all_rotations[i].y + ' ' + "%.4f" % all_rotations[i].z + ' ' + "%.4f" % all_rotations[i].w + '\n')
    print("Closing")
    depth.close()
    ground_truth.close()
    rgb.close()
    print("Ending Save")
    
def save_poses(RT,ind):
    import numpy as np
    pose = np.array(RT)
    pose = [list(i) for i in list(pose)]+[[0,0,0,1]]
    with open(BasePath+Name+'pose/pose_%d.txt'%(ind),'wb') as f:
        for line in np.matrix(pose):
            np.savetxt(f, line)
    return

def animation(render=False):
    translation = mathutils.Vector()
    rotation = mathutils.Matrix.Rotation(0, 3, 'X')
    allTranslations = []
    allRotations = []
    #allDepthMaps = []
    timestamps = []
    sceneStart = get_scene_start_frame()
    sceneEnd = get_scene_end_frame()
    print(sceneStart, sceneEnd)
    if not os.path.isdir(directory):
        os.mkdir(BasePath)
    os.mkdir(BasePath +Name[:-1])
    os.mkdir(BasePath +Name+ 'pose')
    for i in range(sceneStart, sceneEnd):
        # UpdateScene()
        # GetRotation and translation
        RT = get_3x4_RT_matrix_from_blender(bpy.data.objects['Camera'])
        print('Index', i, 'test',  bpy.data.scenes['Scene'].frame_current)
        print(RT)
        save_poses(RT,i)
        # Render
        if render:
            bpy.ops.render.render(animation=False)
            #depthMap = get_depth_map()
            # add data to list
            allTranslations.append(mathutils.Vector(translation))
            allRotations.append(rotation.to_quaternion())
            #allDepthMaps.append(depthMap)
            timestamps.append(get_key_frame())
        else:
            allTranslations.append(mathutils.Vector(translation))
            allRotations.append(rotation.to_quaternion())
            timestamps.append(get_key_frame())
        # updateKeyFrame
        increment_key_frame()
        # return allDepthMaps, allTranslations, allRotations, timestamps
        # update Rotation/Translation
    reset_key_frame()
    #return allDepthMaps, allTranslations, allRotations, timestamps
    return allTranslations, allRotations, timestamps

def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if camd.sensor_fit == 'VERTICAL':
        # the sensor height is fixed (sensor fit is horizontal),
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal),
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm
    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v
    u_0 = resolution_x_in_px*scale / 2
    v_0 = resolution_y_in_px*scale / 2
    skew = 0 # only use rectangular pixels
    K = Matrix(
        ((alpha_u, skew,    u_0),
        (0 ,  alpha_v, v_0),
        (0 ,    0,      1)))
    return K

def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))
    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam * location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()
    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam @ location
    # Build the coordinate transform matrix from world to computer vision camera
    # NOTE: Use * instead of @ here for older versions of Blender
    # TODO: detect Blender version
    R_world2cv = R_bcam2cv@R_world2bcam
    T_world2cv = R_bcam2cv@T_world2bcam
    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))
    return RT

def inspect_depth(depth_maps):
    image = depth_maps[0]
    print(image.shape)
    f = open("DepthImage.txt", 'w')
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            f.write(str(image[i][j]) + " ")
        f.write("\n")


def test(directory):
    set_base_path(directory)
    set_camera_fov(57)
    set_scale(1)
    set_image_width_and_height(640, 480)
    set_depth_threshold(10 * 1000) # 10 meters -> converted to mm
    build_nodes()
    set_camera_properties(inv_camera=False)
    print(ImageWidth, ImageHeight)
    set_scene_properties()
    depth_maps, all_translations, all_rotations, timestamps = animation(render=True)
    #save_data(depth_maps, all_translations, all_rotations, timestamps)
    # InspectDepth(depthMaps)
    k = get_calibration_matrix_K_from_blender(bpy.data.objects['Camera'].data)
    print(k)

def Room_to_RGBD(name):
    import bpy
    import numpy as np
    import mathutils
    from mathutils import Matrix
    import os
    import sys
    from skimage import io
    import skimage
    ImageWidth = 640
    ImageHeight = 480
    ox = ImageWidth/2
    oy = ImageHeight/2
    global fx, fy, K, Kinv, CameraFOV ,MaxDepth ,DepthScale ,BlenderFile ,BasePath ,RGBPath ,DepthPath ,EXRDepthPath ,GroundTruth ,RGB ,Depth ,RGBFileNameFormat ,EXT ,render ,test_mode
    fx = 588
    fy = 588
    K = np.array([[fx, 0, ox], [0, fy, oy], [0, 0, 1]], dtype=np.float32)
    Kinv = np.linalg.inv(K)
    #CameraFOV = 0.994838 # 57
    CameraFOV = 1.49484
    MaxDepth = 1500#cmeters ?
    DepthScale = 5
    BlenderFile = ""
    BasePath = './GeneratedImages/'
    global Name
    Name = name+'/'
    RGBPath = Name+'rgb/'
    DepthPath = Name+'depth/'
    EXRDepthPath = Name+'EXRdepth/'
    GroundTruth = Name+'groundtruth.txt'
    RGB = Name+'rgb.txt'
    Depth = Name+'depth.txt'
    RGBFileNameFormat = 'Image_'
    EXT = '.png'            
    render = True
    test_mode = False
    if test_mode:
        test(directory)
        return
    # Check if file exisits
    if not os.path.isdir(directory):
        print("Can't find directory", directory)
        return
    set_base_path(directory)
    set_camera_fov(CameraFOV)
    set_scale(5)
    set_image_width_and_height(640, 480)
    set_depth_threshold(5 * 1000) # 10 meters -> converted to mm
    build_nodes()
    set_camera_properties(inv_camera=False)
    set_scene_properties()
    #rotation = mathutils.Matrix.Rotation(-(3 * np.pi)/4, 3, 'Z')
    #depthMaps, allTranslations, allRotations, timestamps = MoveAroundPoint(pathStart, center, \
     # distance, 100, initRotation=rotation, render=True)
    # rotation = mathutils.Matrix.Rotation(0, 3, 'X')
    # depthMaps, allTranslations, allRotations, timestamps = MoveAlongLine(pathStart, pathEnd, 200,\
    #  initRotation=rotation, render=True)
    #depth_maps, all_translations, all_rotations, timestamps = animation(render=render)
    all_translations, all_rotations, timestamps = animation(render=render)
    print("Ready")
    print("direc ", directory)
    #save_data(depth_maps, all_translations, all_rotations, timestamps)
    K = get_calibration_matrix_K_from_blender(bpy.data.objects['Camera'].data)
    K = np.array(K)
    K = [list(i) for i in list(K)]
    os.mkdir(directory+Name+'Intrinsic')
    with open(directory+Name+'Intrinsic/Camera_Intrinsic.txt','wb') as f:
        for line in np.matrix(K):
            np.savetxt(f, line)
    print('Data Set Generated')
'''
def MakeAnimation(roomname):
    import numpy as np
    poly = conv_to_vectors(roomname)
    poly = np.array([i['tail'] for i in poly])
    mean = poly.mean(axis = 0)
    centered_poly = poly - mean
    centered_poly = centered_poly*0.5
    cam_poly = centered_poly + mean
    Light = bpy.data.objects['Light']
    Light.data.energy = 100
    Light.location = list(np.append(mean,0))
    Light.location.z += 2.5
    ob = bpy.data.objects['Camera']
    f = 1.0
    for i in cam_poly:
        ob = bpy.data.objects['Camera']
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = pi/2
        ob.rotation_euler.z = 0
        ob.location = (i[0],i[1],1.5)
        ob.keyframe_insert(data_path = "location", frame = f, index= -1)
        ob.keyframe_insert("rotation_euler", frame = f)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = pi/2
        ob.rotation_euler.z = 2*pi*7/8
        ob.location = (i[0],i[1],1.5) 
        ob.keyframe_insert(data_path = "location", frame = f+8, index= -1)
        ob.keyframe_insert("rotation_euler", frame = f+8)
        f=f+8+1
    ob = bpy.data.objects['Camera']
    ob.rotation_mode = "XYZ"
    ob.rotation_euler.x = 0
    ob.rotation_euler.z = 0
    ob.location = (mean[0],mean[1],3)
    ob.keyframe_insert(data_path = "location", frame = f, index= -1)
    ob.keyframe_insert("rotation_euler", frame = f)
    f=f+1
    bpy.data.scenes['Scene'].frame_end = int(f+1)
    reset_key_frame()
    return
'''
def MakeAnimation(roomname):
    import numpy as np
    pol = conv_to_vectors(roomname)
    poly = np.array([i['tail'] for i in pol])
    mean = poly.mean(axis = 0)
    centered_poly = poly - mean
    centered_poly = centered_poly*0.5
    cam_poly = centered_poly + mean
    Light = bpy.data.objects['Light']
    Light.data.energy = 100
    Light.location = list(np.append(mean,0))
    Light.location.z += 2.5
    ob = bpy.data.objects['Camera']
    f = 1.0
    for j,i in enumerate(pol):
        if j == 0:
            if i['direction'] in [0,pi]:
                if i['direction'] == 0:
                    i['direction'] = pi
                else:
                    i['direction'] = 0
            st_angle = i['direction']
        k = j + 1
        if j == len(pol)-1:
            k = 0
        switch_angle = -pi/2
        rot = np.array([[np.cos(switch_angle),-np.sin(switch_angle)],[np.sin(switch_angle),np.cos(switch_angle)]])
        check_vec = np.array([unit_vector(i['vector'])]).T
        d = rot@check_vec
        d = list(d.T[0].astype('int8'))
        print(d)
        print(list(unit_vector(pol[k]['vector']).astype('int8')))
        if d != list(unit_vector(pol[k]['vector']).astype('int8')):
            switch_angle = pi/2 
        ob = bpy.data.objects['Camera']
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = pi/2
        ob.rotation_euler.z = st_angle
        ob.location = (cam_poly[j][0],cam_poly[j][1],1.5)
        ob.keyframe_insert(data_path = "location", frame = f, index= -1)
        ob = bpy.data.objects['Camera']
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = pi/2
        ob.rotation_euler.z = st_angle
        ob.location = (cam_poly[k][0],cam_poly[k][1],1.5)
        ob.keyframe_insert(data_path = "location", frame = f+int(i['mag']/1), index= -1)
        ob.keyframe_insert("rotation_euler", frame = f+int(i['mag']/1))
        f=f+int(i['mag']/1)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = pi/2
        ob.rotation_euler.z = st_angle+switch_angle
        ob.location = (cam_poly[k][0],cam_poly[k][1],1.5) 
        ob.keyframe_insert(data_path = "location", frame = f+2, index= -1)
        ob.keyframe_insert("rotation_euler", frame = f+2)
        f=f+2
        st_angle = st_angle+switch_angle
    f=f+1
    ob = bpy.data.objects['Camera']
    ob.rotation_mode = "XYZ"
    ob.rotation_euler.x = 0
    ob.rotation_euler.z = 0
    ob.location = (mean[0],mean[1],3)
    ob.keyframe_insert(data_path = "location", frame = f, index= -1)
    ob.keyframe_insert("rotation_euler", frame = f)
    f=f+1
    bpy.data.scenes['Scene'].frame_end = int(f+1)
    reset_key_frame()
    return

def DelAnimation():
    obj = bpy.data.objects['Camera']
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    ov=bpy.context.copy()
    ov['area']=[a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    bpy.ops.anim.keyframe_clear_v3d(ov)
    bpy.ops.object.select_all(action='DESELECT')

def Create_RGBD(roomname):
    DelAnimation()
    MakeAnimation(roomname)
    Room_to_RGBD(plan+'/'+roomname)
    
def _build_xy_crop_boundary(polygon, z_range=(-100, 100)):
    z_min = z_range[0]
    z_max = z_range[1]

    dim =  polygon.shape[1]
    if dim != 3:
        raise RuntimeError(f"The given polygon should be [nx3] dimention, not [nx{dim}]")

    o3d_boundary = o3d.visualization.SelectionPolygonVolume()
    o3d_boundary.orthogonal_axis = "Z"
    o3d_boundary.bounding_polygon = o3d.utility.Vector3dVector(polygon)
    o3d_boundary.axis_max = z_max
    o3d_boundary.axis_min = z_min

    return o3d_boundary

def RGBD_to_PointCloud(path):
    os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
    from scipy.spatial.transform import Rotation as R
    import cv2
    import open3d as o3d
    import numpy as np
    # Function for Stitching ScanNet 
    main_path = path+'/'
    names = os.listdir(main_path+"rgb")
    paths_color = [main_path+"rgb/Image_%04d.png"%(i)for i in range(len(names))]
    print(paths_color)
    paths_depth = [main_path+"EXRdepth/Image_%04d.exr"%(i) for i in range(len(names))]
    print(paths_depth)
    for i in range(len(paths_depth)):
        if i==0:
            pcd_m = Rot_trans(main_path,paths_depth[i],paths_color[i],i)
            #pcd_m = Rot_trans(paths[i],paths_color[i],Rotations[i],Centers[i],i)
            continue
        
        p1_load = np.asarray(pcd_m.points)
        p1_color = np.asarray(pcd_m.colors)
        pcd_A = Rot_trans(main_path,paths_depth[i],paths_color[i],i)
        #pcd_A = Rot_trans(paths[i],paths_color[i],Rotations[i],Centers[i],i)
        p2_load = np.asarray(pcd_A.points)
        p2_color = np.asarray(pcd_A.colors)
        p3_load = np.concatenate((p1_load,p2_load), axis=0)
        p3_color = np.concatenate((p1_color,p2_color), axis=0)
        pcd_m = o3d.geometry.PointCloud()
        pcd_m.points = o3d.utility.Vector3dVector(p3_load)
        pcd_m.colors = o3d.utility.Vector3dVector(p3_color)
    Pol = np.array([i['tail'] for i in conv_to_vectors(path.split('/')[-1])])
    from shapely.geometry import Polygon
    points_x = [i[0] for i in Pol]
    points_y = [i[1] for i in Pol]
    p = Polygon(list(zip(points_x, points_y))).buffer(0.2)
    Pol = np.array(p.exterior.coords[:])
    Pol = np.concatenate([Pol,np.array([np.zeros(len(Pol))]).T],axis=1)/1000
    new = _build_xy_crop_boundary(Pol, z_range=(-100, 100)).crop_point_cloud(pcd_m)
    o3d.io.write_point_cloud(path+'/'+path.split('/')[-1]+'.ply',new)    
    return pcd_m
        
def Rot_trans(main_path,path_d,path_c,ind):
    os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
    path = main_path[:-1]
    import open3d as o3d
    import cv2
    depth = cv2.imread(path_d,  cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    #depth = cv2.imread(path_d)
    color = cv2.imread(path_c)
    color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
    color_raw = o3d.pybind.geometry.Image(color.astype('int8'))
    depth_raw = o3d.pybind.geometry.Image(depth.astype('float32'))
    rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
        color_raw, depth_raw, convert_rgb_to_intensity=False)
    pose = open(main_path+"pose/pose_%d.txt"%(ind+1), "r")
    pose = pose.readlines()
    pose = [[float(j) for j in i.split(' ')] for i in pose]
    intrinsic_mat = open(main_path+"Intrinsic/Camera_Intrinsic.txt", "r")
    intrinsic_mat = intrinsic_mat.readlines()
    intrinsic_mat = [[float(j) for j in i.split(' ')] for i in intrinsic_mat]
    intrinsic = o3d.camera.PinholeCameraIntrinsic()
    intrinsic.intrinsic_matrix = intrinsic_mat
    cam = o3d.camera.PinholeCameraParameters()
    cam.intrinsic = intrinsic
    T = np.array(pose)
    T[:,3][:3] = T[:,3][:3]/1000.0
    cam.extrinsic = T
    pcd_m = o3d.geometry.PointCloud.create_from_rgbd_image(
        rgbd_image, cam.intrinsic, cam.extrinsic)
    return pcd_m

def Labelled_List(roomname):
    from tqdm import tqdm as tq
    path = directory+plan+'/'+roomname
    pcd = o3d.io.read_point_cloud(path+'/'+path.split('/')[-1]+'.ply') 
    pcd = pcd.scale(1000, center=(0,0,0))
    pcd = pcd.voxel_down_sample(0.01)
    pcd = np.asarray(pcd.points)
    bpy.ops.object.select_all(action='DESELECT')
    objects = objs_in_room(roomname)
    extras = [Room_Window_List(roomname),Room_Door_List(roomname),Room_Wall_List(roomname)]
    for i in extras:
        for j in i:
            objects.append(bpy.data.objects[j])      
    objects.append(bpy.data.objects[roomname])
    for i in extras[0]:
        ind = i.split('Walls')[1]
        select_obj(D.objects['Window'+ind])
        objects = objects + bpy.context.selected_objects[:2]
        bpy.ops.object.select_all(action='DESELECT')
    for i in extras[1]:
        ind = i.split('Walls')[1]
        select_obj(D.objects['Door'+ind])
        objects = objects + bpy.context.selected_objects[:4]
        bpy.ops.object.select_all(action='DESELECT')
    desk_no = [i for i,j in enumerate(objs_in_room(roomname)) if 'Desk' in j.name]
    for i in np.array(objs_in_room(roomname))[desk_no]:
        select_obj(i)
        objects +=[j for j in bpy.context.selected_objects if 'Chair' in j.name]
        bpy.ops.object.select_all(action='DESELECT')
    directions = [[1,1,1],
                  [1,1,-1],
                  [1,-1,1],
                  [-1,1,1],
                  [1,-1,-1],
                  [-1,-1,1],
                  [-1,1,-1],
                  [-1,-1,-1],
                  [1,0,0],
                  [0,1,0],
                  [0,0,1],
                  [-1,0,0],
                  [0,-1,0],
                  [0,0,-1]]
    selected_obj_ind = 0
    pcd_labels = []
    for k in tq.tqdm(pcd):
        o_dists = []
        for i in objects:
            dists = []
            rot = np.linalg.inv(i.matrix_world)
            p = rot[:3,:4]@(np.array([np.append(k,1)]).T)
            p = p.T[0][:3]
            for j in directions:
                dist = i.ray_cast(list(p),j)
                d_point = np.asarray(dist[1])
                if dist[0] == False:
                    d = 1000
                else:
                    d = np.linalg.norm(d_point-p)
                dists.append(d)
            o_d = min(dists)
            o_dists.append(o_d)
        m = min(o_dists)
        selected_obj_ind = np.where(np.array(o_dists)==m)[0][0]
        pcd_labels.append(objects[selected_obj_ind].name)
    return pcd_labels,pcd

def Categorized_Point_Dict(pcd_labels,pcd):
    pcd_labels = np.array(pcd_labels)
    labels = np.unique(pcd_labels)
    dict = {}
    for i in labels:
        pos = np.where(pcd_labels==i)[0]
        dict[i] = pcd[pos]
    return dict

def Room_Bot_Window_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Bot_Window_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
            list.append(i.name)
    return list
    
def roomtexture(roomname):
    path = directory+"materials.json"
    import json
    import random
    bpy.ops.object.select_all(action='DESELECT')
    objects = objs_in_room(roomname)
    extras = [Room_Bot_Window_List(roomname),Room_Window_List(roomname),Room_Door_List(roomname),Room_Wall_List(roomname)]
    roomWalls = []
    roomFloor= [bpy.data.objects[roomname]]
    for i in extras:
        for j in i:
            roomWalls.append(bpy.data.objects[j])
    #print(objects)
    #print(roomWalls)
    #print(roomFloor)
    with open(path, 'r') as mat_json:
        mat_data = json.load(mat_json)
    matIndwall = random.randint(0, int(len(mat_data["wall_materials"]) - 1))
    matIndfloor = random.randint(0, int(len(mat_data["floor_material"]) - 1))
    wallText = mat_data["wall_materials"][matIndwall]
    floorText = mat_data["floor_material"][matIndfloor]
    get_material(wallText)
    get_material(floorText)
    for i in roomWalls:
        if len(i.material_slots) == 0:
            i.data.materials.append(bpy.data.materials[wallText])
        else:
            i.material_slots[0].material =  bpy.data.materials[wallText]
    for i in roomFloor:
        if len(i.material_slots) == 0:
            i.data.materials.append(bpy.data.materials[floorText])
        else:
            i.material_slots[0].material =  bpy.data.materials[floorText]
    
def get_material(matname):
    file_path = directory+"Materials.blend"
    inner_path = 'Material'
    bpy.ops.wm.append(filepath=os.path.join(file_path, inner_path, matname),
    directory=os.path.join(file_path, inner_path),
    filename=matname)
    
def object_joining():
    objs = [i for i in bpy.data.objects['OBJS'].children if not ('Desk' in i.name) or ('Diningtable' in i.name)]
    for i in objs:
        bpy.context.view_layer.objects.active = bpy.data.objects[i.name]
        select_obj(i)
        if len(bpy.context.selected_objects)!=1:
            bpy.ops.object.join()
        bpy.ops.object.select_all(action='DESELECT')
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
    #main(sys.argv)
    bpy.ops.wm.open_mainfile(filepath = sys.argv[5]+'/floorplan.blend')
    dict = {'Bedroom':{'Bed':1,
                       'Desk':1
                       },
            'LivingRoom':{'Sofa':1,
                          'Bookshelf':1,
                          'Closet':1,
                          'Table':1
                          },
            'Kitchen':{'Closet':1
                    },
            }
    global directory, plan
    directory = sys.argv[5]+'/'
    number = [i for i in os.listdir(directory) if '_Plan_'==i[:6] and ".blend" not in i]
    if number == [] :
        plan = '_Plan_0'
    else:
        plan = '_Plan_'+str(len(number))
   
    print(directory+plan)
    os.mkdir(directory+plan)
    
    index = None
    rooms = []
    for i in bpy.data.objects['Rooms'].children:
        t1,t2 = obj_xy_dims(i)
        V = conv_to_vectors(i.name)
        V = [t['vector'] for t in V]
        check_invalid_polygon = False
        for k in V:
            # POINT WALL FILTER
            if k[0]==0 and k[1]==0:
                check_invalid_polygon = True
            # SLANT WALL FILTER
            if int(k[0])!=0 and int(k[1])!=0:
                check_invalid_polygon = True
        if i.name.split('.')[0] in [j for j in dict] and check_invalid_polygon==False:
            index = Room_populate(i.name,index)
            rooms.append(i.name)
    index = Add_random_objs(index)
    
    if rooms==[]:
        print("No usable rooms in Plan")
        text_file = open("config.txt", "w")
        n = text_file.write("No usable rooms in Plan")
        text_file.close()
        exit(0)
        
    count = 0
    prop = bpy.context.preferences.addons['cycles'].preferences
    prop.get_devices()
    prop.compute_device_type = 'CUDA'

    for device in prop.devices:
        if device.type == 'CUDA':
            device.use = True
    bpy.context.scene.cycles.device = 'GPU'

    for scene in bpy.data.scenes:
        scene.cycles.device = 'GPU'
    for i in bpy.data.objects['Rooms'].children:
        roomtexture(i.name)
    
    #bpy.ops.wm.save_as_mainfile(filepath=directory+plan+".blend")
    object_joining() 
    
    select_obj(bpy.data.objects['Objects'])
    bpy.ops.object.delete()
    select_obj(bpy.data.objects['Floor'])
    bpy.ops.object.delete()
    bpy.ops.object.select_all(action='DESELECT')
    
    # CREATING CONFIG FILE FOR ANNOTATIONS
    text_file = open("config.txt", "w")
    n = text_file.write(directory+plan+"_a.blend")
    text_file.close()     
    bpy.ops.wm.save_as_mainfile(filepath=directory+plan+"_a.blend")
    
    for i in rooms:
        Create_RGBD(i)
        RGBD_to_PointCloud(directory+plan+'/'+i)
        
    exit(0)
    