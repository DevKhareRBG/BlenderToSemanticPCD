import bpy
import os
import numpy as np
import json
import sys
import math
import mathutils
from shapely.geometry import Polygon, Point
from mathutils import Matrix, Vector
from archimesh.door_window_automation import *
import skimage
from skimage import io
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import open3d as o3d
import cv2
import pickle

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

def get_object(obj_name,type):
    name = obj_name + '_'+str(type)
    file_path = directory+'object.blend'
    inner_path = 'Collection'
    object_name = name
    bpy.ops.wm.append(filepath=os.path.join(file_path, inner_path, object_name),
    directory=os.path.join(file_path, inner_path),
    filename=object_name)
    return name

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
    d = abs(A*point[0]+B*point[1]+C)/D
    return d

def bbox_to_pol(xmin, ymin, xmax, ymax,tol = 0):
    return [[xmin+tol, ymin+tol],
            [xmax-tol,ymin+tol],
            [xmax-tol,ymax-tol],
            [xmin+tol, ymax-tol]]
                        
def inside_room(roomname, coll):
    from shapely.geometry import Polygon, Point
    box = Bounding_Box_mult(coll)
    obj_points = bbox_to_pol(box[0], box[1], box[3], box[4],tol=0.1)
    poly = conv_to_vectors(roomname)
    poly = Polygon([i['tail'] for i in poly])
    for i in obj_points:
        point = Point(i[0],i[1])
        if poly.contains(point)==False:
            return False
    return True
        
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

def Room_Bot_Window_List(roomname):
    obj1 = bpy.data.objects[roomname]
    list = []
    for i in bpy.data.objects['Bot_Window_Walls'].children:
        if check_inter(obj1,i,xy=True,tol=0.001):
            list.append(i.name)
    return list

def select_obj(obj,first_obj=True):
    if first_obj==True:
        obj.select_set(True)
    if obj.children==():
        return 
    for i in obj.children:
        i.select_set(True)
        select_obj(i,first_obj=False)

def objs_in_room(roomname):
    room_obj = bpy.data.objects[roomname]
    lis = []
    for i in bpy.data.objects['OBJS'].children:
        if check_inter(i,room_obj,xy=True):
             lis.append(i)
    lis_new = []
    for i in lis:
        x,y,z = Mesh_center(i)
        if Point_in_Room(roomname,[x,y]):
            lis_new.append(i)
    return lis_new

def Labelled_List(pnts,roomname):
    D = bpy.data
    pcd = pnts
    bpy.ops.object.select_all(action='DESELECT')
    objects = objs_in_room(roomname)
    extras =[Room_Window_List(roomname),Room_Door_List(roomname),Room_Wall_List(roomname),Room_Bot_Window_List(roomname)]
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
    desk_no = [i for i,j in enumerate(objs_in_room(roomname)) if (('Desk' in j.name) or ('Diningtable' in j.name))]
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
    for k in pcd:
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
    return pcd_labels

def Annotate_Using_dd_list(Upsampled,Downsampled,ll):
    batch_size = 1000
    iters = len(Upsampled)/batch_size
    L = len(Downsampled)
    annotated = np.repeat(np.array([Downsampled]),batch_size,axis=0).swapaxes(0,1)
    Labels_up = []

    for i in range(int(np.floor(iters))+1):
        batch = Upsampled[batch_size*i:batch_size*(i+1)]
        batch = np.repeat(np.array([batch]),L,axis=0)
        if i == int(np.floor(iters)):
            annotated = np.repeat(np.array([Downsampled]),len(Upsampled[batch_size*i:batch_size*(i+1)]),axis=0).swapaxes(0,1)
        dists = (batch - annotated)**2
        dists = np.sum(dists,axis=2)
        inds = np.argmin(dists,axis=0)
        Labels_up.append(ll[inds])
    Labels_up = np.hstack(Labels_up)
    return Labels_up

'''
def Box_Annotate(pnts,roomname):
    D = bpy.data
    pcd = o3d.utility.Vector3dVector(pnts) 
    bpy.ops.object.select_all(action='DESELECT')
    objects = []
    extras =[Room_Window_List(roomname),Room_Door_List(roomname),Room_Wall_List(roomname),Room_Bot_Window_List(roomname)]
    for i in extras:
        for j in i:
            objects.append(bpy.data.objects[j])      
    objects.append(bpy.data.objects[roomname])
    for i in objs_in_room(roomname):
        objects.append(i)
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
    pcd_labels = np.zeros(len(pnts)).astype('str')  
    for i in objects:
        xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(i)
        bound = o3d.geometry.AxisAlignedBoundingBox((xmin,ymin,zmin),(xmax,ymax,zmax))
        ind = bound.get_point_indices_within_bounding_box(pcd)
        pcd_labels[ind] = i.name
    for i in objects:
        if 'Wall' not in i.name: 
            xmin,ymin,zmin,xmax,ymax,zmax = Bounding_Box(i)
            if i.name == roomname:
                bound = o3d.geometry.AxisAlignedBoundingBox((xmin,ymin,zmax-0.1),(xmax,ymax,zmax))
            else:
                bound = o3d.geometry.AxisAlignedBoundingBox((xmin,ymin,zmin),(xmax,ymax,zmax))
            ind = bound.get_point_indices_within_bounding_box(pcd)
            if len(np.unique(pcd_labels[ind]))>1:
                new_labels = Labelled_List(np.asarray(pcd)[ind],roomname)
                pcd_labels[ind] = new_labels
    return pcd_labels
'''           

def main(name):
    name = name[0:len(name)-8]
    rooms = [i for i in os.listdir(name+'/')]
    for i in rooms:
        with open(name+'/'+i+'/'+i+'_downsampled.npy', 'rb') as f:
            pnts = np.load(f)
        downsampledpcd = o3d.geometry.PointCloud()
        downsampledpcd.points = o3d.utility.Vector3dVector(pnts)
        downpcd = downsampledpcd.voxel_down_sample(voxel_size=0.05)
        ll = np.array(Labelled_List(np.asarray(downpcd.points),i))
        with open(name+'/'+i+'/'+i+'_labels_norm.npy', 'wb') as f:
            np.save(f, ll)
        ll_up = Annotate_Using_dd_list(pnts,np.asarray(downpcd.points),ll)
        with open(name+'/'+i+'/'+i+'_labels.npy', 'wb') as f:
            np.save(f, ll_up)
    exit(0)
    
if __name__ == "__main__":
    
    prop = bpy.context.preferences.addons['cycles'].preferences
    prop.get_devices()
    prop.compute_device_type = 'CUDA'

    for device in prop.devices:
        if device.type == 'CUDA':
            device.use = True
    bpy.context.scene.cycles.device = 'GPU'

    for scene in bpy.data.scenes:
        scene.cycles.device = 'GPU'
    
    with open('config.txt', 'r') as file:
        name = file.read().replace('\n', '')
    
    bpy.ops.wm.open_mainfile(filepath = name)
    main(name)
   