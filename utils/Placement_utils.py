from shapely.geometry import Polygon, box, MultiPolygon, LineString, Point
from sympy import Point as Pnt
from sympy import Polygon as Pol
from sympy import Segment, N
import time
import numpy as np 

global Room_add_list
Room_add_list = {'Bedroom':{'Bed':[1,True],
                           'Desk':[1,True],
                           'Chair':[1,False]
                           },
                'LivingRoom':{'Sofa':[1,True],
                              'Bookshelf':[1,True],
                              'Closet':[1,True],
                              'Table':[1,False]
                              },
                'Kitchen':{'Counter':[1,True],
                        },
                }

class Shapley3Dobj:
    
    def __init__(self,name, roomname, room_pol, obj_bb):
        self.name = name
        self.roomname = roomname 
        self.rotated = 0
        self.room_pol = Polygon([[i,j,k] for i,j,k in zip(room_pol[0],room_pol[1],room_pol[2])])
        self.obj_bb = box(obj_bb[0],obj_bb[1],obj_bb[3],obj_bb[4])
        
    def center(self):
        return self.obj_bb.centroid.xy[0][0],self.obj_bb.centroid.xy[1][0]
    
    def is_inside(self):
        return self.room_pol.contains(self.obj_bb)
    
    def translate(self,x_c,y_c):
        points = np.array(self.obj_bb.exterior.coords.xy)
        points = points+np.array([[x_c,y_c]]).T
        self.obj_bb = Polygon(points.T)
        return self.obj_bb
    
    def rotate(self,theta):
        theta = np.radians(theta)
        x_c,y_c = self.center()
        points = np.array(self.obj_bb.exterior.coords.xy)-np.array([[x_c,y_c]]).T
        rots = int(np.floor(theta/np.pi))
        extra = theta-rots*np.pi
        for i in range(rots):
            rot_mat = np.array([[np.cos(np.pi),np.sign(rots)*-np.sin(np.pi)],[np.sign(rots)*np.sin(np.pi),np.cos(np.pi)]])
            points = rot_mat@points
        rot_mat = np.array([[np.cos(extra),-np.sin(extra)],[np.sin(extra),np.cos(extra)]])
        points = rot_mat@points
        self.obj_bb = Polygon((points+np.array([[x_c,y_c]]).T).T)
        self.rotated += np.degrees(theta)
        return self.obj_bb
    
    def dims(self,room=False):
        if room==True:
            bb_x,bb_y = np.min(np.array(self.room_pol.exterior.coords.xy),axis=1)
            bb_X,bb_Y = np.max(np.array(self.room_pol.exterior.coords.xy),axis=1)
            return [bb_X-bb_x,bb_Y-bb_y]
        else:
            bb_x,bb_y = np.min(np.array(self.obj_bb.exterior.coords.xy),axis=1)
            bb_X,bb_Y = np.max(np.array(self.obj_bb.exterior.coords.xy),axis=1)
            return [bb_X-bb_x,bb_Y-bb_y]
        
    def get_room_lines(self):
        points = np.array(self.room_pol.exterior.coords.xy).T
        points = np.append(points,points[[0],:],axis=0)
        lines = []
        for i in range(len(points)-2):
            lines.append(LineString([Point(*points[i]),Point(*points[i+1])]))
        return lines
    
    def random_point_in_room(self):
        bb_x,bb_y = np.min(np.array(self.room_pol.exterior.coords.xy),axis=1)
        bb_X,bb_Y = np.max(np.array(self.room_pol.exterior.coords.xy),axis=1)
        while True:
            X = bb_x+(bb_X-bb_x)*np.random.rand(1)
            Y = bb_y+(bb_Y-bb_y)*np.random.rand(1)
            if self.room_pol.contains(Point(X,Y)):
                return X,Y
    
    def orient_to_nearest_wall(self):
        int_point, ind, dists = self.ray_trace()
        line_no = np.argmax([i.intersects(Point(*int_point[ind]).buffer(0.00001)) for i in self.get_room_lines()])
        V = np.array(self.get_room_lines()[line_no].coords.xy).T
        orient = np.array([[0,1],[-1,0]])@((V[[1]]-V[[0]])/np.linalg.norm(V[1]-V[0])).T
        orient = orient.T[0]
        ref = np.array([0,-1])
        if np.sign(orient[0])==-1:
            return 360 - np.degrees(np.arccos(np.dot(orient,ref)/(np.linalg.norm(orient) * np.linalg.norm(ref)))),int_point[ind],int_point,dists
        else:
            return np.degrees(np.arccos(np.dot(orient,ref)/(np.linalg.norm(orient) * np.linalg.norm(ref)))),int_point[ind],int_point,dists
    
    def Place_Object(self,room_objects,snap=True):
        import time
        start = time.time()
        while True:
            while True:
                x,y = self.random_point_in_room()
                x_c,y_c = self.center()
                self.translate(x[0]-x_c,y[0]-y_c)
                if time.time()-start>10:
                    return False
                if self.is_inside()==True:
                    break
            if snap == True:
                x_l,y_l = self.dims()
                theta,to_point,_,_ = self.orient_to_nearest_wall()
                self.rotate(theta)
                x_c,y_c = self.center()
                map_snap = {0:[0,-1],90:[1,0],180:[0,1],270:[-1,0]}
                snap_dist = np.array(map_snap[int(np.ceil(theta))])*(y_l/2)
                self.translate(to_point[0]-x_c+snap_dist[0],to_point[1]-y_c+snap_dist[1])
            else:
                theta,to_point,_,_ = self.orient_to_nearest_wall()
                self.rotate(theta)
            check = False
            for i in room_objects:
                if 'Window' not in i.name:
                    if i.obj_bb.intersects(self.obj_bb):
                        check = True
                        break
            for i in room_objects:
                if 'Door' in i.name:
                    h,w = i.dims()
                    clearence = np.max([h,w])
                    h,w = self.dims()
                    clearence += np.max([h,w])/2
                    if np.linalg.norm(np.array(i.center())-np.array(self.center()))<clearence:
                        check = True
                        break
            if time.time()-start>10:
                return False
            if check:
                self.rotate(-theta)
                continue
            else:
                break
        
        return True
                
    def ray_trace(self):
        x,y = self.center()
        points = np.array(self.room_pol.exterior.coords.xy).T
        Sym_pol = Pol(*points)
        bb_x,bb_y = np.min(np.array(self.room_pol.exterior.coords.xy),axis=1)
        bb_X,bb_Y = np.max(np.array(self.room_pol.exterior.coords.xy),axis=1)
        d = np.max([bb_X-bb_x,bb_Y-bb_y])
        rays = [Segment((x,y),(x+d,y)),
                Segment((x,y),(x,y+d)),
                Segment((x,y),(x-d,y)),
                Segment((x,y),(x,y-d))]
        ints = []
        dists = []
        for i,j in enumerate(rays):
            end_point = N(j.intersection(Sym_pol)[0])
            dists.append(np.linalg.norm(np.array([float(end_point.x),float(end_point.y)])-np.array([x,y])))
            ints.append([float(end_point.x),float(end_point.y)])
        closest_ray = np.argmin(dists)
        return ints,closest_ray,dists
            
    def viz(self):
        return MultiPolygon([self.obj_bb,self.room_pol])
    
def read_object_boxes(config):
    Objects = config.program_path+'/'+'object_boundbox.txt'
    n = open(Objects,'r')
    Objects = n.readlines()
    BB = {}
    for i in Objects:
        if 'chair' not in i:
            name = i.split(' ')[0]
            bb = [float(j) for j in i.split(' ')[1:]]
            BB[name]=bb
    return BB
    
def create_room_with_objects(roomname,config):
    room_with_objects = []
    Rooms, BB, Inf = extract_polygons(config)
    Cubi_Pols = [[i,BB[i]] for i in Inf[roomname][2] if i !='']+[['Door'+str(i),BB['Door'+str(i)]] for i in Inf[roomname][0]]+[['Window'+str(i),BB['Window'+str(i)]] for i in Inf[roomname][1]]
    for i in Cubi_Pols:
        room_with_objects.append(Shapley3Dobj(i[0],roomname,Rooms[roomname],i[1]))
    return room_with_objects

def get_objects_for_room(roomname,Room_add_list,config):
    D = read_object_boxes(config)
    all_objects = np.unique([i.split('_')[0] for i in D])
    type_nos = []
    count = 0
    for i in all_objects:
        type_nos.append(0)
        for j in D:
            if i in j:
                type_nos[count]+=1
        count +=1
    roomname = roomname.split('.')[0]
    selected_objs = []
    for i in Room_add_list[roomname]:
        for j in range(Room_add_list[roomname][i][0]):
            selected_objs.append([i+'_'+str(np.random.randint(type_nos[np.where(all_objects==i)[0][0]])+1),Room_add_list[roomname][i][1]])
    return selected_objs          
    
def add_objects_to_room(roomname,config):
    D = read_object_boxes(config)
    Rooms, BB, Inf = extract_polygons(config)
    object_list = create_room_with_objects(roomname,config)
    objects = get_objects_for_room(roomname,Room_add_list,config)
    obj_polygons = [[i[0],D[i[0]],i[1]] for i in objects] 
    add_new = []
    for i in obj_polygons:
        C = Shapley3Dobj(i[0],roomname,Rooms[roomname],i[1])
        check = C.Place_Object(object_list,snap=i[2])
        if check:
            object_list.append(C)
    return object_list
    
def extract_polygons(config):
    Rooms = config.program_path+'/'+'rooms.txt'
    n = open(Rooms,'r')
    Rooms = n.readlines()
    no_rooms = len(Rooms)/3
    XYZ = {}
    for i in range(int(no_rooms)):
        xyz = Rooms[(i)*3:(i+1)*3]
        name = xyz[0].split(',')[0]
        x = [float(i) for i in xyz[0].split(',')[1:]]
        y = [float(i) for i in xyz[1].split(',')[1:]]
        z = [float(i) for i in xyz[2].split(',')[1:]]
        XYZ[name]=[x,y,z]
    Rooms = XYZ
    Objects = config.program_path+'/'+'objects.txt'
    n = open(Objects,'r')
    Objects = n.readlines()
    BB = {}
    for i in Objects:
        name = i.split(',')[0]
        bb = [float(j) for j in i.split(',')[1:]]
        BB[name]=bb
    Room_info = config.program_path+'/'+'rooms_info.txt'
    n = open(Room_info,'r')
    Room_info = n.readlines()
    Inf={}
    for i in range(int(len(Room_info)/4)):
        name,d,w,o = Room_info[(i)*4:(i+1)*4]
        Inf[name[:-1]]=[[int(i) for i in d.split(',')[:-1]],[int(i) for i in w.split(',')[:-1]],o[:-2].split(',')]
    return Rooms, BB, Inf