# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Author: Antonio Vazquez (antonioya)
#
# ----------------------------------------------------------
# noinspection PyUnresolvedReferences
import bpy
import math
# noinspection PyUnresolvedReferences
from archimesh.achm_tools import *


class DoorMake:
    
    def __init__(self,ObjectProp,name):
        self.ObjectProp = ObjectProp
        self.name = name
        
    def execute(self):
        if bpy.context.mode == "OBJECT":
            self.create_object()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}


    # ------------------------------------------------------------------------------
    #
    # Create main object. The other objects will be children of this.
    #
    # ------------------------------------------------------------------------------
    # noinspection PyUnusedLocal
    def create_object(self):
        # deselect all objects
        for o in bpy.data.objects:
            o.select_set(False)

        # we create main object and mesh
        mainmesh = bpy.data.meshes.new("DoorFrane")
        mainobject = bpy.data.objects.new("DoorFrame", mainmesh)
        mainobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(mainobject)
        # we shape the main object and create other objects as children
        self.shape_mesh(mainobject, mainmesh)
        self.shape_children(mainobject)

        # we select, and activate, main object
        mainobject.select_set(True)
        bpy.context.view_layer.objects.active = mainobject


    # ------------------------------------------------------------------------------
    #
    # Update main mesh and children objects
    #
    # ------------------------------------------------------------------------------
    # noinspection PyUnusedLocal
    def update_object(self):
        # When we update, the active object is the main object
        o = bpy.context.active_object
        oldmesh = o.data
        oldname = o.data.name
        # Now we deselect that object to not delete it.
        o.select_set(False)
        # and we create a new mesh
        tmp_mesh = bpy.data.meshes.new("temp")
        # deselect all objects
        for obj in bpy.data.objects:
            obj.select_set(False)

        # ---------------------------------
        #  Clear Parent objects (autohole)
        # ---------------------------------
        myparent = o.parent
        if myparent is not None:
            ploc = myparent.location
            o.parent = None
            o.location = ploc
            # remove_children(parent)
            for child in myparent.children:
                # noinspection PyBroadException
                try:
                    # clear child data
                    child.hide_viewport = False  # must be visible to avoid bug
                    child.hide_render = False  # must be visible to avoid bug
                    old = child.data
                    child.select_set(True)
                    bpy.ops.object.delete()
                    bpy.data.meshes.remove(old)
                except:
                    dummy = -1

            myparent.select_set(True)
            bpy.ops.object.delete()

        # -----------------------
        # remove all children
        # -----------------------
        # first granchild
        for child in o.children:
            remove_children(child)
        # now children of main object
        remove_children(o)

        # Finally we create all that again (except main object),
        self.shape_mesh(o, tmp_mesh, True)
        o.data = tmp_mesh
        self.shape_children(o, True)
        # Remove data (mesh of active object),
        bpy.data.meshes.remove(oldmesh)
        tmp_mesh.name = oldname
        # and select, and activate, the main object
        o.select_set(True)
        bpy.context.view_layer.objects.active = o


    # ------------------------------------------------------------------------------
    # Generate all objects
    # For main, it only shapes mesh and creates modifiers (the modifier, only the first time).
    # And, for the others, it creates object and mesh.
    # ------------------------------------------------------------------------------
    # noinspection PyUnusedLocal
    def shape_mesh(self,mainobject, tmp_mesh, update=False):
        mp = self.ObjectProp
        print(mp['frame_height'])
        # Create only mesh, because the object is created before
        self.create_doorframe(mp, tmp_mesh)

        remove_doubles(mainobject)
        set_normals(mainobject)

        # saves OpenGL data
        #mp['glpoint_a'] = (-mp['frame_width'] / 2, 0, 0)
        #mp['glpoint_b'] = (-mp['frame_width'] / 2, 0, mp['frame_height'])
        #mp['glpoint_c'] = (mp['frame_width'] / 2, 0, mp['frame_height'])
        #mp['glpoint_d']= (-mp['frame_width'] / 2 + mp['frame_size'], 0, mp['frame_height']- mp['frame_size'] - 0.01)
        #mp['glpoint_e'] = (mp['frame_width'] / 2 - mp['frame_size'], 0, mp['frame_height'] - mp['frame_size']- 0.01)

        # Lock
        mainobject.lock_location = (True, True, True)
        mainobject.lock_rotation = (True, True, True)

        return

    # ------------------------------------------------------------------------------
    # Generate all Children
    #
    # ------------------------------------------------------------------------------
    # noinspection PyUnusedLocal


    def shape_children(self,mainobject, update=False):
        mp = self.ObjectProp

        if mp['openside'] != "3":
            self.make_one_door(mp, mainobject, mp['frame_width'], mp['openside'])
        else:
            w = mp['frame_width']
            widthl = (w * mp.factor)
            widthr = w - widthl

            # left door
            mydoor = self.make_one_door(mp, mainobject, widthl + mp['frame_size'], "2")
            mydoor.location.x = -mp['frame_width'] / 2 + mp['frame_size']
            # right door (pending width)
            mydoor = self.make_one_door(mp, mainobject, widthr + mp['frame_size'], "1")
            mydoor.location.x = mp['frame_width'] / 2 - mp['frame_size']

        if mp['crt_mat'] and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            mat = create_diffuse_material("Door_material", False, 0.8, 0.8, 0.8)
            set_material(mainobject, mat)

        # -------------------------
        # Create empty and parent
        # -------------------------
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        myempty = bpy.data.objects[bpy.context.active_object.name]
        myempty.location = mainobject.location

        myempty.name = self.name
        parentobject(myempty, mainobject)
        mainobject["archimesh.hole_enable"] = True
        # Rotate Empty
        myempty.rotation_euler.z = math.radians(mp['r'])
        # Create control box to open wall holes
        gap = 0.002
        myctrl = create_control_box("CTRL_Hole",
                                    mp['frame_width'], mp['frame_thick'] * 3, mp['frame_height'])
        # Add custom property to detect Controller
        myctrl["archimesh.ctrl_hole"] = True

        set_normals(myctrl)
        myctrl.parent = myempty
        myctrl.location.x = 0
        myctrl.location.y = -((mp['frame_thick'] * 3) / 2)
        myctrl.location.z = -gap
        myctrl.display_type = 'BOUNDS'
        myctrl.hide_viewport = False
        myctrl.hide_render = True
        if bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            myctrl.cycles_visibility.camera = False
            myctrl.cycles_visibility.diffuse = False
            myctrl.cycles_visibility.glossy = False
            myctrl.cycles_visibility.transmission = False
            myctrl.cycles_visibility.scatter = False
            myctrl.cycles_visibility.shadow = False

        # Create control box for baseboard
        myctrlbase = create_control_box("CTRL_Baseboard",
                                        mp['frame_width'], 0.40, 0.40,
                                        False)
        # Add custom property to detect Controller
        myctrlbase["archimesh.ctrl_base"] = True

        set_normals(myctrlbase)
        myctrlbase.parent = myempty
        myctrlbase.location.x = 0
        myctrlbase.location.y = -0.15 - (mp['frame_thick'] / 3)
        myctrlbase.location.z = -0.10
        myctrlbase.display_type = 'BOUNDS'
        myctrlbase.hide_viewport = False
        myctrlbase.hide_render = True
        if bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            myctrlbase.cycles_visibility.camera = False
            myctrlbase.cycles_visibility.diffuse = False
            myctrlbase.cycles_visibility.glossy = False
            myctrlbase.cycles_visibility.transmission = False
            myctrlbase.cycles_visibility.scatter = False
            myctrlbase.cycles_visibility.shadow = False

            mat = create_transparent_material("hidden_material", False)
            set_material(myctrl, mat)
            set_material(myctrlbase, mat)

        # deactivate others
        for o in bpy.data.objects:
            if o.select_get() is True and o.name != mainobject.name:
                o.select_set(False)


    # ------------------------------------------------------------------
    # Define property group class to create or modify
    # ------------------------------------------------------------------

    def create_doorframe(self,mp, mymesh):
        tf = mp['frame_thick'] / 3
        sf = mp['frame_size']
        wf = (mp['frame_width'] / 2) - sf
        hf = mp['frame_height'] - sf
        gap = 0.02
        deep = mp['frame_thick'] * 0.50

        verts = [(-wf - sf, -tf, 0),
                 (-wf - sf, tf * 2, 0),
                 (-wf, tf * 2, 0),
                 (-wf - sf, -tf, hf + sf),
                 (-wf - sf, tf * 2, hf + sf),
                 (wf + sf, tf * 2, hf + sf),
                 (wf + sf, -tf, hf + sf),
                 (wf, -tf, hf),
                 (-wf, tf * 2, hf),
                 (wf, -tf, 0),
                 (wf + sf, -tf, 0),
                 (wf + sf, tf * 2, 0),
                 (wf, -tf + deep, hf),
                 (-wf, -tf + deep, hf),
                 (-wf, -tf + deep, 0),
                 (-wf + gap, -tf + deep, hf),
                 (-wf + gap, -tf + deep, 0),
                 (-wf + gap, tf * 2, hf),
                 (-wf + gap, tf * 2, 0),
                 (wf, -tf + deep, 0),
                 (-wf, -tf, hf),
                 (-wf, -tf, 0),
                 (wf, tf * 2, hf),
                 (wf, tf * 2, 0),
                 (wf - gap, tf * 2, 0),
                 (wf - gap, -tf + deep, 0),
                 (wf - gap, tf * 2, hf),
                 (wf - gap, -tf + deep, hf - gap),
                 (wf - gap, -tf + deep, hf),
                 (-wf + gap, tf * 2, hf - gap),
                 (-wf + gap, -tf + deep, hf - gap),
                 (wf - gap, tf * 2, hf - gap)]

        faces = [(3, 4, 1, 0), (7, 12, 19, 9), (4, 3, 6, 5), (10, 11, 5, 6), (13, 20, 21, 14), (17, 15, 16, 18),
                 (11, 23, 22, 5),
                 (20, 13, 12, 7), (20, 3, 0, 21), (9, 10, 6, 7), (13, 14, 16, 15), (4, 8, 2, 1), (29, 30, 27, 31),
                 (7, 6, 3, 20),
                 (8, 4, 5, 22), (14, 2, 18, 16), (17, 18, 2, 8), (28, 25, 19, 12), (28, 26, 24, 25), (25, 24, 23, 19),
                 (22, 23, 24, 26),
                 (29, 31, 26, 17), (15, 28, 27, 30), (8, 22, 26)]

        mymesh.from_pydata(verts, [], faces)
        mymesh.update(calc_edges=True)

        return


    # ------------------------------------------------------------------------------
    # Make one door
    #
    # ------------------------------------------------------------------------------
    def make_one_door(self,mp,myframe, width, openside):
        mydoor = self.create_door_data( mp, myframe, width, openside)
        handle1 = None
        handle2 = None
        if mp['handle'] != "0":
            handle1 = self.create_handle( mp, mydoor, "Front", width, openside)
            handle1.select_set(True)
            bpy.context.view_layer.objects.active = handle1
            set_smooth(handle1)
            set_modifier_subsurf(handle1)
            handle2 = self.create_handle(mp,  mydoor, "Back", width, openside)
            set_smooth(handle2)
            set_modifier_subsurf(handle2)
        # Create materials
        if mp['crt_mat'] and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            # Door material
            mat = create_diffuse_material("Door_material", False, 0.8, 0.8, 0.8)
            set_material(mydoor, mat)
            # Handle material
            if mp['handle'] != "0":
                mat = create_glossy_material("Handle_material", False, 0.733, 0.779, 0.8)
                set_material(handle1, mat)
                set_material(handle2, mat)
            if mp['model'] == "5" or mp['model'] == "6":
                mat = create_glass_material("DoorGlass_material", False)
                mydoor.data.materials.append(mat)
                if mp['model'] == "5":
                    select_faces(mydoor, 20, True)
                    select_faces(mydoor, 41, False)
                if mp['model'] == "6":
                    select_faces(mydoor, 37, True)
                    select_faces(mydoor, 76, False)
                set_material_faces(mydoor, 1)

        set_normals(mydoor)

        return mydoor


    # ------------------------------------------------------------------------------
    # Create Door
    # All custom values are passed using self container (self.myvariable)
    # ------------------------------------------------------------------------------
    def create_door_data(self,mp, myframe, width, openside):
        # Retry mesh data
        if mp['model'] == "1":
            mydata = self.door_model_01( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'], openside)
        elif mp['model'] == "2":
            mydata = self.door_model_02( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'], openside)
        elif mp['model'] == "3":
            mydata = self.door_model_03( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'], openside)
        elif mp['model'] == "4":
            mydata = self.door_model_04( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'], openside)
        elif mp['model'] == "5":
            mydata = self.door_model_04( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'],
                                   openside)  # uses the same mesh
        elif mp['model'] == "6":
            mydata = self.door_model_02( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'],
                                   openside)  # uses the same mesh
        else:
            mydata = self.door_model_01( mp['frame_size'], width,  mp['frame_height'], mp['frame_thick'], openside)  # default model

        # move data
        verts = mydata[0]
        faces = mydata[1]
        wf = mydata[2]
        deep = mydata[3]
        side = mydata[4]

        mymesh = bpy.data.meshes.new("DoorM")
        myobject = bpy.data.objects.new("DoorM", mymesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mymesh.from_pydata(verts, [], faces)
        mymesh.update(calc_edges=True)

        # Translate to doorframe and parent
        myobject.parent = myframe
        myobject.lock_rotation = (True, True, False)
        myobject.lock_location = (True, True, True)

        myobject.location.x = ((wf / 2) * side)
        myobject.location.y = -(deep * 0.65)
        myobject.location.z =  mp['frame_height'] / 2

        return myobject


    # ------------------------------------------------------------------------------
    # Create Handles
    # All custom values are passed using self container (self.myvariable)
    # ------------------------------------------------------------------------------
    def create_handle( self,mp, mydoor, pos, frame_width, openside):
        # Retry mesh data
        if mp['handle'] == "1":
            mydata = self.handle_model_01()
        elif mp['handle'] == "2":
            mydata = self.handle_model_02()
        elif mp['handle'] == "3":
            mydata = self.handle_model_03()
        elif mp['handle'] == "4":
            mydata = self.handle_model_04()
        else:
            mydata = self.handle_model_01()  # default model

        # move data
        verts = mydata[0]
        faces = mydata[1]

        gap = 0.002
        sf =  mp['frame_size']
        wf = frame_width - (sf * 2) - (gap * 2)
        deep = (mp['frame_thick'] * 0.50) - (gap * 3)
        # Open to right or left
        if openside == "1":
            side = -1
        else:
            side = 1

        mymesh = bpy.data.meshes.new("Handle_" + pos)
        myobject = bpy.data.objects.new("Handle_" + pos, mymesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mymesh.from_pydata(verts, [], faces)
        mymesh.update(calc_edges=True)
        # Rotate if pos is front
        xrot = 0.0
        yrot = 0.0
        if mp['handle'] == "1":
            if openside != "1":
                yrot = math.pi
        else:
            yrot = 0.0

        if pos == "Front":
            xrot = math.pi

        myobject.rotation_euler = (xrot, yrot, 0.0)  # radians PI=180

        # Translate to door and parent (depend of model of door)
        if mp['model'] == "1":
            myobject.location.x = (wf * side) + (0.072 * side * -1)
            if pos == "Front":
                myobject.location.y = deep - 0.005
            else:
                myobject.location.y = 0.005

        if mp['model'] == "2" or mp['model'] == "6":
            myobject.location.x = (wf * side) + (0.060 * side * -1)
            if pos == "Front":
                myobject.location.y = deep - 0.011
            else:
                myobject.location.y = 0.00665

        if mp['model'] == "3":
            myobject.location.x = (wf * side) + (0.060 * side * -1)
            if pos == "Front":
                myobject.location.y = deep - 0.011
            else:
                myobject.location.y = 0.00665

        if mp['model'] == "4" or mp['model'] == "5":
            myobject.location.x = (wf * side) + (0.060 * side * -1)
            if pos == "Front":
                myobject.location.y = deep - 0.011
            else:
                myobject.location.y = 0.00665

        myobject.location.z = 0
        myobject.parent = mydoor
        myobject.lock_rotation = (True, False, True)

        return myobject


    # ----------------------------------------------
    # Door model 01
    # ----------------------------------------------
    def door_model_01(self,frame_size, frame_width, frame_height, frame_thick, openside):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        gap = 0.002
        sf = frame_size
        wf = frame_width - (sf * 2) - (gap * 2)
        hf = (frame_height / 2) - (gap * 2)
        deep = (frame_thick * 0.50) - (gap * 3)
        # Open to right or left
        if openside == "1":
            side = 1
            minx = wf * -1
            maxx = 0.0
        else:
            side = -1
            minx = 0.0
            maxx = wf

        miny = 0.0  # locked
        maxy = deep
        minz = -hf
        maxz = hf - sf - gap

        # Vertex
        myvertex = [(minx, miny, minz),
                    (minx, maxy, minz),
                    (maxx, maxy, minz),
                    (maxx, miny, minz),
                    (minx, miny, maxz),
                    (minx, maxy, maxz),
                    (maxx, maxy, maxz),
                    (maxx, miny, maxz)]

        # Faces
        myfaces = [(4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3), (0, 1, 2, 3),
                   (7, 6, 5, 4)]

        return myvertex, myfaces, wf, deep, side


    # ----------------------------------------------
    # Door model 02
    # ----------------------------------------------
    def door_model_02(self,frame_size, frame_width, frame_height, frame_thick, openside):
        gap = 0.002
        sf = frame_size
        wf = frame_width - (sf * 2) - (gap * 2)
        hf = (frame_height / 2) - (gap * 2)
        deep = (frame_thick * 0.50)

        # ------------------------------------
        # Mesh data
        # ------------------------------------
        # Open to right or left
        if openside == "1":
            side = 1
            minx = wf * -1
            maxx = 0.0
        else:
            side = -1
            minx = 0.0
            maxx = wf

        maxy = deep
        minz = -hf
        maxz = hf - sf - gap

        # Vertex
        myvertex = [(minx, -1.57160684466362e-08, minz + 2.384185791015625e-06),
                    (maxx, -1.5599653124809265e-08, minz),
                    (minx, -1.5599653124809265e-08, maxz),
                    (minx, -1.5599653124809265e-08, maxz - 0.12999999523162842),
                    (minx, -1.57160684466362e-08, minz + 0.2500007152557373),
                    (maxx, -1.5599653124809265e-08, minz + 0.25000011920928955),
                    (maxx, -1.5599653124809265e-08, maxz),
                    (maxx, -1.5599653124809265e-08, maxz - 0.12999999523162842),
                    (maxx - 0.11609852313995361, -1.5599653124809265e-08, maxz),
                    (maxx - 0.12357193231582642, -1.5599653124809265e-08, minz),
                    (maxx - 0.11658430099487305, -1.5599653124809265e-08, maxz - 0.12999999523162842),
                    (maxx - 0.12263774871826172, -1.5599653124809265e-08, minz + 0.25000011920928955),
                    (minx, -1.57160684466362e-08, minz + 0.8700000941753387),
                    (maxx, -1.5599653124809265e-08, minz + 0.8700000941753387),
                    (maxx - 0.12076938152313232, -1.5599653124809265e-08, minz + 0.7500001192092896),
                    (minx + 0.11735659837722778, -1.57160684466362e-08, minz + 0.25000011920928955),
                    (minx + 0.12341010570526123, -1.5599653124809265e-08, maxz - 0.12999999523162842),
                    (minx + 0.11642247438430786, -1.57160684466362e-08, minz),
                    (minx + 0.11967337131500244, -1.57160684466362e-08, minz + 0.8700000941753387),
                    (minx, -1.57160684466362e-08, minz + 0.7500001192092896),
                    (maxx - 0.12032097578048706, -1.5599653124809265e-08, minz + 0.8700000941753387),
                    (minx + 0.12389582395553589, -1.5599653124809265e-08, maxz),
                    (maxx, -1.5599653124809265e-08, minz + 0.7500001192092896),
                    (minx + 0.11922496557235718, -1.57160684466362e-08, minz + 0.7500001192092896),
                    (minx + 0.11922496557235718, -0.010000014677643776, minz + 0.7500001192092896),
                    (minx + 0.12341010570526123, -0.010000014677643776, maxz - 0.12999999523162842),
                    (maxx - 0.12032097578048706, -0.010000014677643776, minz + 0.8700000941753387),
                    (minx + 0.11735659837722778, -0.010000014677643776, minz + 0.25000011920928955),
                    (maxx - 0.11658430099487305, -0.010000014677643776, maxz - 0.12999999523162842),
                    (maxx - 0.12263774871826172, -0.010000014677643776, minz + 0.25000011920928955),
                    (minx + 0.11967337131500244, -0.010000014677643776, minz + 0.8700000941753387),
                    (maxx - 0.12076938152313232, -0.010000014677643776, minz + 0.7500001192092896),
                    (minx + 0.13388586044311523, -0.010000014677643776, minz + 0.7375001013278961),
                    (minx + 0.1321108341217041, -0.010000014677643776, minz + 0.2625001072883606),
                    (maxx - 0.1372986137866974, -0.010000014677643776, minz + 0.2625001072883606),
                    (maxx - 0.13552364706993103, -0.010000014677643776, minz + 0.7375001013278961),
                    (minx + 0.13802427053451538, -0.010000014677643776, maxz - 0.14747536182403564),
                    (maxx - 0.13493508100509644, -0.010000014677643776, minz + 0.8866067305207253),
                    (maxx - 0.13138526678085327, -0.010000014677643776, maxz - 0.14747536182403564),
                    (minx + 0.13447439670562744, -0.010000014677643776, minz + 0.8866067305207253),
                    (minx + 0.13388586044311523, -0.008776669390499592, minz + 0.7375001013278961),
                    (minx + 0.1321108341217041, -0.008776669390499592, minz + 0.2625001072883606),
                    (maxx - 0.1372986137866974, -0.008776669390499592, minz + 0.2625001072883606),
                    (maxx - 0.13552364706993103, -0.008776669390499592, minz + 0.7375001013278961),
                    (minx + 0.13802427053451538, -0.008776669390499592, maxz - 0.14747536182403564),
                    (maxx - 0.13493508100509644, -0.008776669390499592, minz + 0.8866067305207253),
                    (maxx - 0.13138526678085327, -0.008776669390499592, maxz - 0.14747536182403564),
                    (minx + 0.13447439670562744, -0.008776669390499592, minz + 0.8866067305207253),
                    (minx, maxy - 0.009999999776482582, minz + 2.384185791015625e-06),
                    (maxx, maxy - 0.009999999776482582, minz),
                    (minx, maxy - 0.009999999776482582, maxz),
                    (minx, maxy - 0.009999999776482582, maxz - 0.12999999523162842),
                    (minx, maxy - 0.009999999776482582, minz + 0.2500007152557373),
                    (maxx, maxy - 0.009999999776482582, minz + 0.25000011920928955),
                    (maxx, maxy - 0.009999999776482582, maxz),
                    (maxx, maxy - 0.009999999776482582, maxz - 0.12999999523162842),
                    (maxx - 0.11609852313995361, maxy - 0.009999999776482582, maxz),
                    (maxx - 0.12357193231582642, maxy - 0.009999999776482582, minz),
                    (maxx - 0.11658430099487305, maxy - 0.009999999776482582, maxz - 0.12999999523162842),
                    (maxx - 0.12263774871826172, maxy - 0.009999999776482582, minz + 0.25000011920928955),
                    (minx, maxy - 0.009999999776482582, minz + 0.8700000941753387),
                    (maxx, maxy - 0.009999999776482582, minz + 0.8700000941753387),
                    (maxx - 0.12076938152313232, maxy - 0.009999999776482582, minz + 0.7500001192092896),
                    (minx + 0.11735659837722778, maxy - 0.009999999776482582, minz + 0.25000011920928955),
                    (minx + 0.12341010570526123, maxy - 0.009999999776482582, maxz - 0.12999999523162842),
                    (minx + 0.11642247438430786, maxy - 0.009999999776482582, minz),
                    (minx + 0.11967337131500244, maxy - 0.009999999776482582, minz + 0.8700000941753387),
                    (minx, maxy - 0.009999999776482582, minz + 0.7500001192092896),
                    (maxx - 0.12032097578048706, maxy - 0.009999999776482582, minz + 0.8700000941753387),
                    (minx + 0.12389582395553589, maxy - 0.009999999776482582, maxz),
                    (maxx, maxy - 0.009999999776482582, minz + 0.7500001192092896),
                    (minx + 0.11922496557235718, maxy - 0.009999999776482582, minz + 0.7500001192092896),
                    (minx + 0.11922496557235718, maxy, minz + 0.7500001192092896),
                    (minx + 0.12341010570526123, maxy, maxz - 0.12999999523162842),
                    (maxx - 0.12032097578048706, maxy, minz + 0.8700000941753387),
                    (minx + 0.11735659837722778, maxy, minz + 0.25000011920928955),
                    (maxx - 0.11658430099487305, maxy, maxz - 0.12999999523162842),
                    (maxx - 0.12263774871826172, maxy, minz + 0.25000011920928955),
                    (minx + 0.11967337131500244, maxy, minz + 0.8700000941753387),
                    (maxx - 0.12076938152313232, maxy, minz + 0.7500001192092896),
                    (minx + 0.13388586044311523, maxy, minz + 0.7375001013278961),
                    (minx + 0.1321108341217041, maxy, minz + 0.2625001072883606),
                    (maxx - 0.1372986137866974, maxy, minz + 0.2625001072883606),
                    (maxx - 0.13552364706993103, maxy, minz + 0.7375001013278961),
                    (minx + 0.13802427053451538, maxy, maxz - 0.14747536182403564),
                    (maxx - 0.13493508100509644, maxy, minz + 0.8866067305207253),
                    (maxx - 0.13138526678085327, maxy, maxz - 0.14747536182403564),
                    (minx + 0.13447439670562744, maxy, minz + 0.8866067305207253),
                    (minx + 0.13388586044311523, maxy - 0.0012233443558216095, minz + 0.7375001013278961),
                    (minx + 0.1321108341217041, maxy - 0.0012233443558216095, minz + 0.2625001072883606),
                    (maxx - 0.1372986137866974, maxy - 0.0012233443558216095, minz + 0.2625001072883606),
                    (maxx - 0.13552364706993103, maxy - 0.0012233443558216095, minz + 0.7375001013278961),
                    (minx + 0.13802427053451538, maxy - 0.0012233443558216095, maxz - 0.14747536182403564),
                    (maxx - 0.13493508100509644, maxy - 0.0012233443558216095, minz + 0.8866067305207253),
                    (maxx - 0.13138526678085327, maxy - 0.0012233443558216095, maxz - 0.14747536182403564),
                    (minx + 0.13447439670562744, maxy - 0.0012233443558216095, minz + 0.8866067305207253)]

        # Faces
        myfaces = [(15, 4, 0, 17), (21, 2, 3, 16), (23, 19, 4, 15), (6, 8, 10, 7), (8, 21, 16, 10),
                   (16, 3, 12, 18), (11, 15, 17, 9), (20, 18, 23, 14), (18, 12, 19, 23), (5, 11, 9, 1),
                   (22, 14, 11, 5), (7, 10, 20, 13), (13, 20, 14, 22), (20, 10, 28, 26), (10, 16, 25, 28),
                   (16, 18, 30, 25), (18, 20, 26, 30), (15, 11, 29, 27), (14, 23, 24, 31), (23, 15, 27, 24),
                   (11, 14, 31, 29), (31, 24, 32, 35), (24, 27, 33, 32), (27, 29, 34, 33), (29, 31, 35, 34),
                   (26, 28, 38, 37), (30, 26, 37, 39), (28, 25, 36, 38), (25, 30, 39, 36), (33, 34, 42, 41),
                   (36, 39, 47, 44), (34, 35, 43, 42), (37, 38, 46, 45), (32, 33, 41, 40), (38, 36, 44, 46),
                   (35, 32, 40, 43), (39, 37, 45, 47), (18, 20, 10, 16), (14, 23, 15, 11), (63, 52, 48, 65),
                   (69, 50, 51, 64), (71, 67, 52, 63), (54, 56, 58, 55), (56, 69, 64, 58), (64, 51, 60, 66),
                   (59, 63, 65, 57), (68, 66, 71, 62), (66, 60, 67, 71), (53, 59, 57, 49), (70, 62, 59, 53),
                   (55, 58, 68, 61), (61, 68, 62, 70), (68, 58, 76, 74), (58, 64, 73, 76), (64, 66, 78, 73),
                   (66, 68, 74, 78), (63, 59, 77, 75), (62, 71, 72, 79), (71, 63, 75, 72), (59, 62, 79, 77),
                   (79, 72, 80, 83), (72, 75, 81, 80), (75, 77, 82, 81), (77, 79, 83, 82), (74, 76, 86, 85),
                   (78, 74, 85, 87), (76, 73, 84, 86), (73, 78, 87, 84), (81, 82, 90, 89), (84, 87, 95, 92),
                   (82, 83, 91, 90), (85, 86, 94, 93), (80, 81, 89, 88), (86, 84, 92, 94), (83, 80, 88, 91),
                   (87, 85, 93, 95), (66, 68, 58, 64), (62, 71, 63, 59), (50, 2, 21, 69), (8, 56, 69, 21),
                   (6, 54, 56, 8), (54, 6, 7, 55), (55, 7, 13, 61), (61, 13, 22, 70), (5, 53, 70, 22),
                   (1, 49, 53, 5), (49, 1, 9, 57), (57, 9, 17, 65), (0, 48, 65, 17), (48, 0, 4, 52),
                   (52, 4, 19, 67), (12, 60, 67, 19), (3, 51, 60, 12), (2, 50, 51, 3)]

        return myvertex, myfaces, wf, deep, side


    # ----------------------------------------------
    # Door model 03
    # ----------------------------------------------
    def door_model_03(self,frame_size, frame_width, frame_height, frame_thick, openside):
        gap = 0.002
        sf = frame_size
        wf = frame_width - (sf * 2) - (gap * 2)
        hf = (frame_height / 2) - (gap * 2)
        deep = (frame_thick * 0.50)

        # ------------------------------------
        # Mesh data
        # ------------------------------------
        # Open to right or left
        if openside == "1":
            side = 1
            minx = wf * -1
            maxx = 0.0
        else:
            side = -1
            minx = 0.0
            maxx = wf

        miny = 0.0  # Locked

        maxy = deep
        minz = -hf
        maxz = hf - sf - gap

        # Vertex
        myvertex = [(minx, -1.5599653124809265e-08, maxz),
                    (maxx, -1.5599653124809265e-08, maxz),
                    (minx, maxy, maxz),
                    (maxx, maxy, maxz),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, maxz),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, maxz),
                    (minx + 0.10429966449737549, maxy, maxz),
                    (minx, -1.5628756955266e-08, maxz - 0.5012519359588623),
                    (maxx, -1.5599653124809265e-08, maxz - 0.5012525320053101),
                    (minx, maxy, maxz - 0.5012519359588623),
                    (maxx, maxy, maxz - 0.5012525320053101),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, maxz - 0.501252293586731),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, maxz - 0.5012521147727966),
                    (minx + 0.10429966449737549, maxy, maxz - 0.5012521147727966),
                    (maxx - 0.10429960489273071, maxy, maxz - 0.501252293586731),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, maxz),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, maxz),
                    (minx + 0.11909735202789307, maxy, maxz),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, maxz - 0.5012521743774414),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, maxz - 0.5012522339820862),
                    (minx, -1.5629622041046787e-08, maxz - 0.516154021024704),
                    (maxx, -1.5599653124809265e-08, maxz - 0.5161546468734741),
                    (minx, maxy, maxz - 0.516154021024704),
                    (maxx, maxy, maxz - 0.5161546468734741),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, maxz - 0.516154408454895),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, maxz - 0.5161541998386383),
                    (maxx - 0.10429960489273071, maxy, maxz - 0.516154408454895),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, maxz - 0.5161543190479279),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, maxz - 0.5161542594432831),
                    (minx + 0.11909735202789307, maxy, maxz - 0.5161542594432831),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, maxz),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, maxz),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, maxz - 0.501252293586731),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, maxz - 0.5012521147727966),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, maxz),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, maxz),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, maxz - 0.5012521743774414),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, maxz - 0.5012522339820862),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, maxz - 0.516154408454895),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, maxz - 0.5161541998386383),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, maxz - 0.5161543190479279),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, maxz - 0.5161542594432831),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, maxz - 0.992994874715805),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, maxz - 0.9929947257041931),
                    (minx + 0.11909735202789307, maxy, maxz - 0.9929947257041931),
                    (maxx - 0.11909738183021545, maxy, maxz - 0.992994874715805),
                    (minx, -1.565730833874568e-08, maxz - 0.9929942488670349),
                    (maxx, -1.5599653124809265e-08, maxz - 0.9929954260587692),
                    (minx, maxy, maxz - 0.9929942488670349),
                    (maxx, maxy, maxz - 0.9929954260587692),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, maxz - 0.9929950088262558),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, maxz - 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy, maxz - 0.9929950088262558),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, maxz - 0.9929950088262558),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, maxz - 0.9929945915937424),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, maxz - 0.992994874715805),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, maxz - 0.9929947257041931),
                    (maxx - 0.11909729242324829, maxy - 0.0004077646881341934, maxz - 0.992994874715805),
                    (maxx - 0.10429960489273071, maxy - 0.0004077646881341934, maxz - 0.9929950088262558),
                    (maxx - 0.10429960489273071, maxy, maxz),
                    (maxx - 0.11909729242324829, maxy, maxz),
                    (maxx - 0.11909738183021545, maxy, maxz - 0.5012522339820862),
                    (minx + 0.11909735202789307, maxy, maxz - 0.5012521743774414),
                    (minx + 0.10429966449737549, maxy, maxz - 0.5161541998386383),
                    (maxx - 0.11909738183021545, maxy, maxz - 0.5161543190479279),
                    (minx + 0.10429966449737549, maxy, maxz - 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, maxz),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, maxz),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, maxz - 0.5012521147727966),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, maxz - 0.501252293586731),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, maxz),
                    (maxx - 0.11909729242324829, maxy - 0.008999999612569809, maxz),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, maxz - 0.5012522339820862),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, maxz - 0.5012521743774414),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, maxz - 0.5161541998386383),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, maxz - 0.516154408454895),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, maxz - 0.5161542594432831),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, maxz - 0.5161543190479279),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, maxz - 0.9929947257041931),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, maxz - 0.992994874715805),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, maxz - 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, maxz - 0.9929950088262558),
                    (minx, -1.5599653124809265e-08, minz),
                    (maxx, -1.5599653124809265e-08, minz),
                    (minx, maxy, minz),
                    (maxx, maxy, minz),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, minz),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, minz),
                    (minx + 0.10429966449737549, maxy, minz),
                    (minx, -1.5628756955266e-08, minz + 0.5012519359588623),
                    (minx, -1.5657860785722733e-08, minz + 1.0025038719177246),
                    (maxx, -1.5599653124809265e-08, minz + 0.5012525320053101),
                    (maxx, -1.5599653124809265e-08, minz + 1.0025050640106201),
                    (minx, maxy, minz + 0.5012519359588623),
                    (minx, maxy, minz + 1.0025038719177246),
                    (maxx, maxy, minz + 0.5012525320053101),
                    (maxx, maxy, minz + 1.0025050640106201),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, minz + 0.501252293586731),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, minz + 1.0025046467781067),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, minz + 0.5012521147727966),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, minz + 1.0025042295455933),
                    (minx + 0.10429966449737549, maxy, minz + 0.5012521147727966),
                    (minx + 0.10429966449737549, maxy, minz + 1.0025042295455933),
                    (maxx - 0.10429960489273071, maxy, minz + 0.501252293586731),
                    (maxx - 0.10429960489273071, maxy, minz + 1.0025046467781067),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, minz),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, minz),
                    (minx + 0.11909735202789307, maxy, minz),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, minz + 0.5012521743774414),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, minz + 0.5012522339820862),
                    (minx + 0.11909735202789307, maxy, minz + 1.0025043686230788),
                    (minx, -1.5629622041046787e-08, minz + 0.516154021024704),
                    (maxx, -1.5599653124809265e-08, minz + 0.5161546468734741),
                    (minx, maxy, minz + 0.516154021024704),
                    (maxx, maxy, minz + 0.5161546468734741),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, minz + 0.516154408454895),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, minz + 0.5161541998386383),
                    (maxx - 0.10429960489273071, maxy, minz + 0.516154408454895),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, minz + 0.5161543190479279),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, minz + 0.5161542594432831),
                    (minx + 0.11909735202789307, maxy, minz + 0.5161542594432831),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, minz),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, minz),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, minz + 0.501252293586731),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, minz + 1.0025046467781067),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, minz + 0.5012521147727966),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, minz + 1.0025042295455933),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, minz),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, minz),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, minz + 0.5012521743774414),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, minz + 0.5012522339820862),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, minz + 0.516154408454895),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, minz + 0.5161541998386383),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, minz + 0.5161543190479279),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, minz + 0.5161542594432831),
                    (maxx - 0.11909729242324829, -1.5832483768463135e-08, minz + 0.992994874715805),
                    (minx + 0.11909735202789307, -1.5832483768463135e-08, minz + 0.9929947257041931),
                    (minx + 0.11909735202789307, maxy, minz + 0.9929947257041931),
                    (maxx - 0.11909738183021545, maxy, minz + 0.992994874715805),
                    (minx, -1.565730833874568e-08, minz + 0.9929942488670349),
                    (maxx, -1.5599653124809265e-08, minz + 0.9929954260587692),
                    (minx, maxy, minz + 0.9929942488670349),
                    (maxx, maxy, minz + 0.9929954260587692),
                    (maxx - 0.10429960489273071, -1.5832483768463135e-08, minz + 0.9929950088262558),
                    (minx + 0.10429966449737549, -1.5832483768463135e-08, minz + 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy, minz + 0.9929950088262558),
                    (maxx - 0.10429960489273071, miny + 0.009999999776482582, minz + 0.9929950088262558),
                    (minx + 0.10429966449737549, miny + 0.009999999776482582, minz + 0.9929945915937424),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, minz + 1.0025043686231356),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, minz + 1.0025045077006212),
                    (maxx - 0.10429960489273071, maxy - 0.0004077646881341934, minz + 1.0025046467781067),
                    (maxx - 0.11909729242324829, maxy - 0.0004077646881341934, minz + 1.0025045077006212),
                    (maxx - 0.11909729242324829, miny + 0.009999999776482582, minz + 0.992994874715805),
                    (minx + 0.11909735202789307, miny + 0.009999999776482582, minz + 0.9929947257041931),
                    (maxx - 0.11909729242324829, maxy - 0.0004077646881341934, minz + 0.992994874715805),
                    (maxx - 0.10429960489273071, maxy - 0.0004077646881341934, minz + 0.9929950088262558),
                    (maxx - 0.10429960489273071, maxy, minz),
                    (maxx - 0.11909729242324829, maxy, minz),
                    (maxx - 0.11909738183021545, maxy, minz + 0.5012522339820862),
                    (minx + 0.11909735202789307, maxy, minz + 0.5012521743774414),
                    (maxx - 0.11909738183021545, maxy, minz + 1.0025045077005643),
                    (minx + 0.10429966449737549, maxy, minz + 0.5161541998386383),
                    (maxx - 0.11909738183021545, maxy, minz + 0.5161543190479279),
                    (minx + 0.10429966449737549, maxy, minz + 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, minz),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, minz),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, minz + 0.5012521147727966),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, minz + 1.0025042295455933),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, minz + 0.501252293586731),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, minz + 1.0025046467781067),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, minz),
                    (maxx - 0.11909729242324829, maxy - 0.008999999612569809, minz),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, minz + 0.5012522339820862),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, minz + 0.5012521743774414),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, minz + 1.0025045077005643),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, minz + 1.0025043686230788),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, minz + 0.5161541998386383),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, minz + 0.516154408454895),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, minz + 0.5161542594432831),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, minz + 0.5161543190479279),
                    (minx + 0.11909735202789307, maxy - 0.008999999612569809, minz + 0.9929947257041931),
                    (maxx - 0.11909738183021545, maxy - 0.008999999612569809, minz + 0.992994874715805),
                    (minx + 0.10429966449737549, maxy - 0.008999999612569809, minz + 0.9929945915937424),
                    (maxx - 0.10429960489273071, maxy - 0.008999999612569809, minz + 0.9929950088262558)]

        # Faces
        myfaces = [(2, 0, 5, 6), (3, 1, 8, 10), (49, 47, 92, 96), (0, 2, 9, 7), (46, 48, 94, 90),
                   (5, 0, 7, 12), (51, 46, 90, 100), (52, 49, 96, 104), (1, 4, 11, 8), (47, 50, 98, 92),
                   (12, 25, 39, 33), (2, 6, 13, 9), (5, 12, 33, 31), (16, 15, 18, 19), (18, 15, 34, 36),
                   (10, 8, 21, 23), (7, 9, 22, 20), (12, 7, 20, 25), (14, 10, 23, 26), (8, 11, 24, 21),
                   (51, 100, 126, 54), (24, 11, 32, 38), (16, 19, 37, 35), (34, 31, 33, 36), (30, 35, 37, 32),
                   (36, 33, 39, 41), (32, 37, 40, 38), (37, 36, 41, 40), (19, 18, 36, 37), (28, 27, 40, 41),
                   (20, 22, 48, 46), (11, 4, 30, 32), (23, 21, 47, 49), (50, 24, 38, 53), (25, 20, 46, 51),
                   (26, 23, 49, 52), (21, 24, 50, 47), (27, 28, 43, 42), (25, 51, 54, 39), (98, 50, 53, 124),
                   (55, 56, 148, 149), (126, 148, 56, 54), (42, 43, 56, 55), (124, 53, 55, 149), (61, 60, 71, 72),
                   (35, 30, 66, 71), (31, 34, 70, 67), (71, 66, 69, 72), (79, 81, 169, 174), (67, 70, 73, 68),
                   (80, 78, 175, 167), (78, 79, 174, 175), (72, 69, 75, 77), (68, 73, 76, 74), (73, 72, 77, 76),
                   (77, 75, 81, 79), (74, 76, 78, 80), (62, 61, 72, 73), (65, 63, 74, 80), (59, 4, 1, 3),
                   (59, 3, 10, 14), (48, 65, 102, 94), (17, 15, 16, 60), (17, 60, 61, 62), (9, 13, 63, 22),
                   (43, 28, 41, 56), (27, 42, 55, 40), (22, 63, 65, 48), (29, 64, 45, 44), (41, 39, 54, 56),
                   (38, 40, 55, 53), (29, 44, 78, 76), (63, 13, 68, 74), (17, 62, 73, 70), (52, 104, 169, 81),
                   (64, 29, 76, 77), (13, 6, 67, 68), (59, 14, 69, 66), (44, 45, 79, 78), (45, 64, 77, 79),
                   (14, 26, 75, 69), (26, 52, 81, 75), (102, 65, 80, 167), (84, 88, 87, 82), (85, 95, 91, 83),
                   (142, 96, 92, 140), (82, 89, 93, 84), (139, 90, 94, 141), (87, 99, 89, 82), (144, 100, 90, 139),
                   (145, 104, 96, 142), (83, 91, 97, 86), (140, 92, 98, 143), (99, 125, 132, 116), (84, 93, 101, 88),
                   (87, 122, 125, 99), (106, 109, 108, 105), (108, 129, 127, 105), (95, 114, 112, 91), (89, 111, 113, 93),
                   (99, 116, 111, 89), (103, 117, 114, 95), (91, 112, 115, 97), (144, 147, 126, 100), (115, 131, 123, 97),
                   (106, 128, 130, 109), (127, 129, 125, 122), (121, 123, 130, 128), (129, 134, 132, 125),
                   (123, 131, 133, 130),
                   (130, 133, 134, 129), (109, 130, 129, 108), (119, 134, 133, 118), (111, 139, 141, 113),
                   (97, 123, 121, 86),
                   (114, 142, 140, 112), (143, 146, 131, 115), (116, 144, 139, 111), (117, 145, 142, 114),
                   (112, 140, 143, 115),
                   (118, 135, 136, 119), (116, 132, 147, 144), (98, 124, 146, 143), (152, 149, 148, 153),
                   (126, 147, 153, 148),
                   (135, 152, 153, 136), (124, 149, 152, 146), (158, 172, 171, 157), (128, 171, 164, 121),
                   (122, 165, 170, 127),
                   (171, 172, 168, 164), (181, 174, 169, 183), (165, 166, 173, 170), (182, 167, 175, 180),
                   (180, 175, 174, 181),
                   (172, 179, 177, 168), (166, 176, 178, 173), (173, 178, 179, 172), (179, 181, 183, 177),
                   (176, 182, 180, 178),
                   (159, 173, 172, 158), (163, 182, 176, 161), (156, 85, 83, 86), (156, 103, 95, 85), (141, 94, 102, 163),
                   (107, 157, 106, 105), (107, 159, 158, 157), (93, 113, 161, 101), (136, 153, 134, 119),
                   (118, 133, 152, 135),
                   (113, 141, 163, 161), (120, 137, 138, 162), (134, 153, 147, 132), (131, 146, 152, 133),
                   (120, 178, 180, 137),
                   (161, 176, 166, 101), (107, 170, 173, 159), (145, 183, 169, 104), (162, 179, 178, 120),
                   (101, 166, 165, 88),
                   (160, 174, 175, 110), (156, 164, 168, 103), (137, 180, 181, 138), (138, 181, 179, 162),
                   (103, 168, 177, 117),
                   (117, 177, 183, 145), (102, 167, 182, 163)]

        return myvertex, myfaces, wf, deep, side


    # ----------------------------------------------
    # Door model 04
    # ----------------------------------------------
    def door_model_04(self,frame_size, frame_width, frame_height, frame_thick, openside):
        gap = 0.002
        sf = frame_size
        wf = frame_width - (sf * 2) - (gap * 2)
        hf = (frame_height / 2) - (gap * 2)
        deep = (frame_thick * 0.50)

        # ------------------------------------
        # Mesh data
        # ------------------------------------
        # Open to right or left
        if openside == "1":
            side = 1
            minx = wf * -1
            maxx = 0.0
        else:
            side = -1
            minx = 0.0
            maxx = wf

        miny = 0.0  # Locked

        maxy = deep
        minz = -hf
        maxz = hf - sf - gap

        # Vertex
        myvertex = [(minx, miny + 0.009999997913837433, minz + 2.384185791015625e-06),
                    (maxx, miny + 0.009999997913837433, minz),
                    (minx, miny + 0.009999997913837433, maxz),
                    (minx, miny + 0.009999997913837433, maxz - 0.12999999523162842),
                    (minx, miny + 0.009999997913837433, minz + 0.25000083446502686),
                    (maxx, miny + 0.009999997913837433, minz + 0.2500002384185791),
                    (maxx, miny + 0.009999997913837433, maxz),
                    (maxx, miny + 0.009999997913837433, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, miny + 0.009999997913837433, maxz),
                    (maxx - 0.11968576908111572, miny + 0.009999997913837433, minz),
                    (maxx - 0.11968576908111572, miny + 0.009999997913837433, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, miny + 0.009999997913837433, minz + 0.2500002384185791),
                    (minx + 0.12030857801437378, miny + 0.009999997913837433, minz + 0.2500002384185791),
                    (minx + 0.12030857801437378, miny + 0.009999997913837433, maxz - 0.12999999523162842),
                    (minx + 0.12030857801437378, miny + 0.009999997913837433, minz),
                    (minx + 0.12030857801437378, miny + 0.009999997913837433, maxz),
                    (minx + 0.12030857801437378, -0.009999997913837433, maxz - 0.12999999523162842),
                    (minx + 0.12030857801437378, -0.009999997913837433, minz + 0.2500002384185791),
                    (maxx - 0.11968576908111572, -0.009999997913837433, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, -0.009999997913837433, minz + 0.2500002384185791),
                    (maxx - 0.13532748818397522, -0.008776653558015823, minz + 0.2625002861022949),
                    (maxx - 0.13532748818397522, -0.009388323873281479, maxz - 0.14747536182403564),
                    (minx + 0.13506758213043213, -0.009388323873281479, minz + 0.2625002861022949),
                    (minx + 0.13506758213043213, -0.009388323873281479, maxz - 0.14747536182403564),
                    (maxx - 0.13532748818397522, -0.0003883242607116699, minz + 0.2625002861022949),
                    (maxx - 0.13532748818397522, -0.0003883242607116699, maxz - 0.14747536182403564),
                    (minx + 0.13506758213043213, -0.0003883242607116699, minz + 0.2625002861022949),
                    (minx + 0.13506758213043213, -0.0003883242607116699, maxz - 0.14747536182403564),
                    (minx, maxy - 0.010000001639127731, minz + 2.384185791015625e-06),
                    (maxx, maxy - 0.010000001639127731, minz),
                    (minx, maxy - 0.010000001639127731, maxz),
                    (minx, maxy - 0.010000001639127731, maxz - 0.12999999523162842),
                    (minx, maxy - 0.010000001639127731, minz + 0.25000083446502686),
                    (maxx, maxy - 0.010000001639127731, minz + 0.2500002384185791),
                    (maxx, maxy - 0.010000001639127731, maxz),
                    (maxx, maxy - 0.010000001639127731, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, maxy - 0.010000001639127731, maxz),
                    (maxx - 0.11968576908111572, maxy - 0.010000001639127731, minz),
                    (maxx - 0.11968576908111572, maxy - 0.010000001639127731, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, maxy - 0.010000001639127731, minz + 0.2500002384185791),
                    (minx + 0.12030857801437378, maxy - 0.010000001639127731, minz + 0.2500002384185791),
                    (minx + 0.12030857801437378, maxy - 0.010000001639127731, maxz - 0.12999999523162842),
                    (minx + 0.12030857801437378, maxy - 0.010000001639127731, minz),
                    (minx + 0.12030857801437378, maxy - 0.010000001639127731, maxz),
                    (minx + 0.12030857801437378, maxy, maxz - 0.12999999523162842),
                    (minx + 0.12030857801437378, maxy, minz + 0.2500002384185791),
                    (maxx - 0.11968576908111572, maxy, maxz - 0.12999999523162842),
                    (maxx - 0.11968576908111572, maxy, minz + 0.2500002384185791),
                    (maxx - 0.1353275179862976, maxy - 0.001223348081111908, minz + 0.2625002861022949),
                    (maxx - 0.1353275179862976, maxy - 0.0006116703152656555, maxz - 0.14747536182403564),
                    (minx + 0.13506758213043213, maxy - 0.0006116703152656555, minz + 0.2625002861022949),
                    (minx + 0.13506758213043213, maxy - 0.0006116703152656555, maxz - 0.14747536182403564),
                    (maxx - 0.1353275179862976, maxy - 0.010223347693681717, minz + 0.2625002861022949),
                    (maxx - 0.1353275179862976, maxy - 0.009611673653125763, maxz - 0.14747536182403564),
                    (minx + 0.13506758213043213, maxy - 0.009611673653125763, minz + 0.2625002861022949),
                    (minx + 0.13506758213043213, maxy - 0.009611673653125763, maxz - 0.14747536182403564)]

        # Faces
        myfaces = [(12, 4, 0, 14), (15, 2, 3, 13), (6, 8, 10, 7), (8, 15, 13, 10), (11, 12, 14, 9),
                   (5, 11, 9, 1), (10, 13, 16, 18), (12, 11, 19, 17), (3, 4, 12, 13), (5, 7, 10, 11),
                   (20, 22, 17, 19), (18, 21, 20, 19), (17, 22, 23, 16), (17, 16, 13, 12), (11, 10, 18, 19),
                   (21, 18, 16, 23), (22, 26, 27, 23), (21, 23, 27, 25), (21, 25, 24, 20), (20, 24, 26, 22),
                   (24, 25, 27, 26), (40, 42, 28, 32), (43, 41, 31, 30), (34, 35, 38, 36), (36, 38, 41, 43),
                   (39, 37, 42, 40), (33, 29, 37, 39), (38, 46, 44, 41), (40, 45, 47, 39), (31, 41, 40, 32),
                   (33, 39, 38, 35), (48, 47, 45, 50), (46, 47, 48, 49), (45, 44, 51, 50), (45, 40, 41, 44),
                   (39, 47, 46, 38), (49, 51, 44, 46), (50, 51, 55, 54), (49, 53, 55, 51), (49, 48, 52, 53),
                   (48, 50, 54, 52), (52, 54, 55, 53), (34, 36, 8, 6), (36, 43, 15, 8), (2, 15, 43, 30),
                   (6, 7, 35, 34), (7, 5, 33, 35), (29, 33, 5, 1), (1, 9, 37, 29), (9, 14, 42, 37),
                   (28, 42, 14, 0), (32, 4, 3, 31), (30, 31, 3, 2), (32, 28, 0, 4)]
        return myvertex, myfaces, wf, deep, side


    # ----------------------------------------------
    # Handle model 01
    # ----------------------------------------------
    def handle_model_01(self):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.04349547624588013
        maxx = 0.13793155550956726
        miny = -0.07251644879579544
        maxy = 0
        minz = -0.04352371022105217
        maxz = 0.04349301755428314

        # Vertex
        myvertex = [(minx + 0.013302795588970184, maxy - 0.002780601382255554, minz + 0.010707870125770569),
                    (minx + 0.0009496212005615234, maxy - 0.002942140679806471, minz + 0.030204588547348976),
                    (minx, maxy - 0.003071820829063654, maxz - 0.033750676549971104),
                    (minx + 0.010708402842283249, maxy - 0.0031348932534456253, maxz - 0.013303784653544426),
                    (minx + 0.03020550962537527, maxy - 0.003114458406344056, maxz - 0.0009501762688159943),
                    (minx + 0.053267089650034904, maxy - 0.003015991533175111, maxz - 0.0),
                    (minx + 0.07371381670236588, maxy - 0.0028658765368163586, maxz - 0.010707847774028778),
                    (minx + 0.08606699481606483, maxy - 0.0027043374720960855, maxz - 0.030204561538994312),
                    (minx + 0.08701662346720695, maxy - 0.0025746573228389025, minz + 0.03375071194022894),
                    (minx + 0.0763082429766655, maxy - 0.002511584199965, minz + 0.013303810730576515),
                    (minx + 0.05681113991886377, maxy - 0.0025320190470665693, minz + 0.0009501948952674866),
                    (minx + 0.03374955803155899, maxy - 0.0026304861530661583, minz),
                    (minx + 0.014472760260105133, maxy - 0.019589224830269814, minz + 0.011804874986410141),
                    (minx + 0.002567145973443985, maxy - 0.019744910299777985, minz + 0.030595174990594387),
                    (minx + 0.001651916652917862, maxy - 0.019869891926646233, maxz - 0.034195657819509506),
                    (minx + 0.011972300708293915, maxy - 0.019930677488446236, maxz - 0.014489583671092987),
                    (minx + 0.03076297417283058, maxy - 0.019910985603928566, maxz - 0.0025835558772087097),
                    (minx + 0.0529889902099967, maxy - 0.019816085696220398, maxz - 0.0016677752137184143),
                    (minx + 0.07269490510225296, maxy - 0.01967141032218933, maxz - 0.011987630277872086),
                    (minx + 0.0846005342900753, maxy - 0.01951572299003601, maxz - 0.030777926556766033),
                    (minx + 0.08551576733589172, maxy - 0.019390743225812912, minz + 0.03401290811598301),
                    (minx + 0.07519540190696716, maxy - 0.01932995393872261, minz + 0.014306826516985893),
                    (minx + 0.056404732167720795, maxy - 0.01934964768588543, minz + 0.002400781959295273),
                    (minx + 0.03417872078716755, maxy - 0.019444547593593597, minz + 0.001484982669353485),
                    (minx + 0.043508310547622386, maxy - 0.0028232389595359564, maxz - 0.043508357635801076),
                    (minx + 0.029034355655312538, maxy - 0.019612153992056847, minz + 0.027617475017905235),
                    (minx + 0.023084014654159546, maxy - 0.01968996599316597, minz + 0.03700872650370002),
                    (minx + 0.022626593708992004, maxy - 0.01975242979824543, maxz - 0.03889966616407037),
                    (minx + 0.027784643694758415, maxy - 0.019782811403274536, maxz - 0.029050718992948532),
                    (minx + 0.03717608004808426, maxy - 0.019772969186306, maxz - 0.023100173100829124),
                    (minx + 0.048284475691616535, maxy - 0.019725536927580833, maxz - 0.022642474621534348),
                    (minx + 0.058133346028625965, maxy - 0.019653232768177986, maxz - 0.02780025824904442),
                    (minx + 0.06408369168639183, maxy - 0.019575420767068863, maxz - 0.0371915097348392),
                    (minx + 0.06454112380743027, maxy - 0.019512956961989403, minz + 0.03871688432991505),
                    (minx + 0.059383073821663857, maxy - 0.019482573494315147, minz + 0.02886793203651905),
                    (minx + 0.04999163839966059, maxy - 0.019492419436573982, minz + 0.022917380556464195),
                    (minx + 0.038883245550096035, maxy - 0.0195398461073637, minz + 0.022459672763943672),
                    (minx + 0.029087782837450504, maxy - 0.03150090575218201, minz + 0.027552824467420578),
                    (minx + 0.023137442767620087, maxy - 0.03157871589064598, minz + 0.036944076884537935),
                    (minx + 0.022680018097162247, maxy - 0.03164118155837059, maxz - 0.03896431624889374),
                    (minx + 0.027838071808218956, maxy - 0.031671565026044846, maxz - 0.029115368612110615),
                    (minx + 0.0372295081615448, maxy - 0.03166172280907631, maxz - 0.023164819926023483),
                    (minx + 0.04833790427073836, maxy - 0.03161429241299629, maxz - 0.022707123309373856),
                    (minx + 0.05818677507340908, maxy - 0.03154198080301285, maxz - 0.027864910662174225),
                    (minx + 0.06413711979985237, maxy - 0.031464170664548874, maxz - 0.037256159354001284),
                    (minx + 0.06459455192089081, maxy - 0.03140170872211456, minz + 0.038652234710752964),
                    (minx + 0.059436503797769547, maxy - 0.03137132152915001, minz + 0.028803281486034393),
                    (minx + 0.05004506651312113, maxy - 0.031381167471408844, minz + 0.022852730005979538),
                    (minx + 0.038936673663556576, maxy - 0.03142859786748886, minz + 0.022395022213459015),
                    (minx + 0.029038896784186363, maxy - 0.020622700452804565, minz + 0.027611978352069855),
                    (minx + 0.02308855764567852, maxy - 0.02070051059126854, minz + 0.0370032312348485),
                    (minx + 0.02263113297522068, maxy - 0.020762978121638298, maxz - 0.038905161898583174),
                    (minx + 0.02778918668627739, maxy - 0.020793357864022255, maxz - 0.029056214727461338),
                    (minx + 0.037180622573941946, maxy - 0.02078351564705372, maxz - 0.023105667904019356),
                    (minx + 0.04828901821747422, maxy - 0.020736083388328552, maxz - 0.02264796942472458),
                    (minx + 0.05813788715749979, maxy - 0.020663777366280556, maxz - 0.0278057549148798),
                    (minx + 0.0640882346779108, maxy - 0.020585965365171432, maxz - 0.03719700500369072),
                    (minx + 0.06454566307365894, maxy - 0.020523501560091972, minz + 0.0387113899923861),
                    (minx + 0.05938761495053768, maxy - 0.020493119955062866, minz + 0.028862436302006245),
                    (minx + 0.04999618045985699, maxy - 0.020502964034676552, minz + 0.022911883890628815),
                    (minx + 0.03888778714463115, maxy - 0.02055039070546627, minz + 0.02245417609810829),
                    (minx + 0.03133368864655495, maxy - 0.031504075974226, minz + 0.02999168261885643),
                    (minx + 0.02630186453461647, maxy - 0.03156987577676773, minz + 0.03793327230960131),
                    (minx + 0.025915050879120827, maxy - 0.03162270039319992, maxz - 0.039689837489277124),
                    (minx + 0.0302768861874938, maxy - 0.031648389995098114, maxz - 0.03136120364069939),
                    (minx + 0.03821863234043121, maxy - 0.03164006769657135, maxz - 0.026329202577471733),
                    (minx + 0.04761230247095227, maxy - 0.03159996122121811, maxz - 0.025942156091332436),
                    (minx + 0.05594087019562721, maxy - 0.03153881058096886, maxz - 0.030303767882287502),
                    (minx + 0.06097269989550114, maxy - 0.03147301450371742, maxz - 0.038245356641709805),
                    (minx + 0.06135952286422253, maxy - 0.03142019361257553, minz + 0.039377753622829914),
                    (minx + 0.05699768662452698, maxy - 0.03139450028538704, minz + 0.03104911558330059),
                    (minx + 0.049055942334234715, maxy - 0.0314028225839138, minz + 0.02601710893213749),
                    (minx + 0.03966227453202009, maxy - 0.031442929059267044, minz + 0.025630054995417595),
                    (minx + 0.024973656982183456, maxy - 0.009611732326447964, minz + 0.037668352015316486),
                    (minx + 0.030362362042069435, maxy - 0.009541265666484833, minz + 0.029163507744669914),
                    (minx + 0.02455940842628479, maxy - 0.009668299928307533, maxz - 0.03928851708769798),
                    (minx + 0.029230606742203236, maxy - 0.009695813991129398, maxz - 0.030369175598025322),
                    (minx + 0.03773562144488096, maxy - 0.009686900302767754, maxz - 0.02498028054833412),
                    (minx + 0.04779553506523371, maxy - 0.009643946774303913, maxz - 0.02456578239798546),
                    (minx + 0.056714802980422974, maxy - 0.009578464552760124, maxz - 0.02923674415796995),
                    (minx + 0.0621035173535347, maxy - 0.009507997892796993, maxz - 0.037741586565971375),
                    (minx + 0.06251777522265911, maxy - 0.009451429359614849, minz + 0.03921528346836567),
                    (minx + 0.05784657597541809, maxy - 0.009423915296792984, minz + 0.03029593825340271),
                    (minx + 0.0493415636010468, maxy - 0.009432828985154629, minz + 0.02490703947842121),
                    (minx + 0.039281651843339205, maxy - 0.009475781582295895, minz + 0.02449253387749195),
                    (minx + 0.03144440520554781, maxy - 0.02431209199130535, minz + 0.030186276882886887),
                    (minx + 0.02647113800048828, maxy - 0.0243771281093359, minz + 0.038035438396036625),
                    (minx + 0.026088828220963478, maxy - 0.024429334327578545, maxz - 0.03969699679873884),
                    (minx + 0.030399901792407036, maxy - 0.02445472590625286, maxz - 0.031465294770896435),
                    (minx + 0.0382492202334106, maxy - 0.024446498602628708, maxz - 0.026491858065128326),
                    (minx + 0.04753356333822012, maxy - 0.024406857788562775, maxz - 0.02610931731760502),
                    (minx + 0.05576520040631294, maxy - 0.024346424266695976, maxz - 0.03042016737163067),
                    (minx + 0.060738470405340195, maxy - 0.024281391873955727, maxz - 0.03826932841911912),
                    (minx + 0.06112079136073589, maxy - 0.024229183793067932, minz + 0.03946310793980956),
                    (minx + 0.056809717789292336, maxy - 0.024203790351748466, minz + 0.03123140148818493),
                    (minx + 0.04896040167659521, maxy - 0.02421201765537262, minz + 0.026257958263158798),
                    (minx + 0.03967605973593891, maxy - 0.024251656606793404, minz + 0.025875410065054893),
                    (minx + 0.03160235192626715, miny + 0.013056624680757523, minz + 0.02999513689428568),
                    (minx + 0.02662908472120762, miny + 0.012991588562726974, minz + 0.03784429794177413),
                    (minx + 0.026246773079037666, miny + 0.012939386069774628, maxz - 0.039888136787340045),
                    (minx + 0.030557849444448948, miny + 0.012913990765810013, maxz - 0.03165643382817507),
                    (minx + 0.03840716602280736, miny + 0.012922219932079315, maxz - 0.02668299712240696),
                    (minx + 0.04769151005893946, miny + 0.012961860746145248, maxz - 0.02630045637488365),
                    (minx + 0.05592314712703228, miny + 0.013022292405366898, maxz - 0.030611306428909302),
                    (minx + 0.06089641526341438, miny + 0.013087328523397446, maxz - 0.038460468873381615),
                    (minx + 0.06127873808145523, miny + 0.013139534741640091, minz + 0.03927196795120835),
                    (minx + 0.05696766451001167, miny + 0.013164930045604706, minz + 0.031040262430906296),
                    (minx + 0.04911834839731455, miny + 0.013156700879335403, minz + 0.026066819205880165),
                    (minx + 0.0398340062238276, miny + 0.013117063790559769, minz + 0.02568427100777626),
                    (minx + 0.03166038449853659, miny + 0.00014262646436691284, minz + 0.029924907721579075),
                    (minx + 0.026687119156122208, miny + 7.76052474975586e-05, minz + 0.0377740697003901),
                    (minx + 0.026304809376597404, miny + 2.5391578674316406e-05, maxz - 0.039958365727216005),
                    (minx + 0.030615881085395813, miny, maxz - 0.031726663932204247),
                    (minx + 0.0384651985950768, miny + 8.217990398406982e-06, maxz - 0.026753226295113564),
                    (minx + 0.0477495426312089, miny + 4.7869980335235596e-05, maxz - 0.026370685547590256),
                    (minx + 0.05598117969930172, miny + 0.00010830163955688477, maxz - 0.03068153653293848),
                    (minx + 0.06095444969832897, miny + 0.00017333775758743286, maxz - 0.038530697114765644),
                    (minx + 0.06133677065372467, miny + 0.0002255365252494812, minz + 0.039201739244163036),
                    (minx + 0.05702569708228111, miny + 0.00025093555450439453, minz + 0.030970032326877117),
                    (minx + 0.04917638096958399, miny + 0.00024271011352539062, minz + 0.02599659003317356),
                    (minx + 0.039892038563266397, miny + 0.00020306557416915894, minz + 0.025614041835069656),
                    (maxx - 0.012196376919746399, miny + 0.0031514912843704224, minz + 0.03689247788861394),
                    (maxx - 0.011049121618270874, miny + 0.0037728995084762573, minz + 0.04000293998979032),
                    (maxx - 0.010531991720199585, miny + 0.004111833870410919, maxz - 0.041690999176353216),
                    (maxx - 0.010783538222312927, miny + 0.0040774866938591, maxz - 0.035582118667662144),
                    (maxx - 0.011736378073692322, miny + 0.003679051995277405, maxz - 0.030324016697704792),
                    (maxx - 0.013135172426700592, miny + 0.003023289144039154, maxz - 0.027325598523020744),
                    (maxx - 0.013745412230491638, miny + 0.010863490402698517, minz + 0.03701266320422292),
                    (maxx - 0.012598156929016113, miny + 0.011484891176223755, minz + 0.0401231253053993),
                    (maxx - 0.012081027030944824, miny + 0.011823825538158417, maxz - 0.041570812463760376),
                    (maxx - 0.01233258843421936, miny + 0.011789467185735703, maxz - 0.035461933352053165),
                    (maxx - 0.013285413384437561, miny + 0.011391039937734604, maxz - 0.030203829519450665),
                    (maxx - 0.014684207737445831, miny + 0.010735277086496353, maxz - 0.027205411344766617),
                    (maxx - 0.000991135835647583, maxy - 0.01982143148779869, minz + 0.03712343191727996),
                    (maxx - 0.0034268200397491455, maxy - 0.018987802788615227, minz + 0.03702782467007637),
                    (maxx - 0.00027070939540863037, maxy - 0.018310068175196648, minz + 0.040221322793513536),
                    (maxx, maxy - 0.017457325011491776, maxz - 0.04147987486794591),
                    (maxx - 0.00025157630443573, maxy - 0.01749167963862419, maxz - 0.03537099435925484),
                    (maxx - 0.000957980751991272, maxy - 0.018403928726911545, maxz - 0.030105633661150932),
                    (maxx - 0.001929953694343567, maxy - 0.019949644804000854, maxz - 0.02709464356303215),
                    (maxx - 0.0043656229972839355, maxy - 0.01911601796746254, maxz - 0.027190251275897026),
                    (maxx - 0.002706393599510193, maxy - 0.01747644878923893, minz + 0.04012571508064866),
                    (maxx - 0.0024356693029403687, maxy - 0.01662370003759861, maxz - 0.04157548164948821),
                    (maxx - 0.0026872456073760986, maxy - 0.016658056527376175, maxz - 0.03546660114079714),
                    (maxx - 0.0033936500549316406, maxy - 0.017570307478308678, maxz - 0.030201241374015808),
                    (minx + 0.04382078559137881, miny + 0.00012543797492980957, minz + 0.04313003408606164)]

        # Faces
        myfaces = [(24, 0, 1), (24, 1, 2), (24, 2, 3), (24, 3, 4), (24, 4, 5),
                   (24, 5, 6), (24, 6, 7), (24, 7, 8), (24, 8, 9), (24, 9, 10),
                   (24, 10, 11), (11, 0, 24), (0, 12, 13, 1), (1, 13, 14, 2), (2, 14, 15, 3),
                   (3, 15, 16, 4), (4, 16, 17, 5), (5, 17, 18, 6), (6, 18, 19, 7), (7, 19, 20, 8),
                   (8, 20, 21, 9), (9, 21, 22, 10), (10, 22, 23, 11), (12, 0, 11, 23), (13, 12, 25, 26),
                   (14, 13, 26, 27), (15, 14, 27, 28), (16, 15, 28, 29), (17, 16, 29, 30), (18, 17, 30, 31),
                   (19, 18, 31, 32), (20, 19, 32, 33), (21, 20, 33, 34), (22, 21, 34, 35), (23, 22, 35, 36),
                   (12, 23, 36, 25), (25, 49, 50, 26), (49, 37, 38, 50), (26, 50, 51, 27), (50, 38, 39, 51),
                   (27, 51, 52, 28), (51, 39, 40, 52), (28, 52, 53, 29), (52, 40, 41, 53), (29, 53, 54, 30),
                   (53, 41, 42, 54), (30, 54, 55, 31), (54, 42, 43, 55), (31, 55, 56, 32), (55, 43, 44, 56),
                   (32, 56, 57, 33), (56, 44, 45, 57), (33, 57, 58, 34), (57, 45, 46, 58), (34, 58, 59, 35),
                   (58, 46, 47, 59), (35, 59, 60, 36), (59, 47, 48, 60), (36, 60, 49, 25), (60, 48, 37, 49),
                   (38, 37, 61, 62), (39, 38, 62, 63), (40, 39, 63, 64), (41, 40, 64, 65), (42, 41, 65, 66),
                   (43, 42, 66, 67), (44, 43, 67, 68), (45, 44, 68, 69), (46, 45, 69, 70), (47, 46, 70, 71),
                   (48, 47, 71, 72), (37, 48, 72, 61), (62, 61, 74, 73), (63, 62, 73, 75), (64, 63, 75, 76),
                   (65, 64, 76, 77), (66, 65, 77, 78), (67, 66, 78, 79), (68, 67, 79, 80), (69, 68, 80, 81),
                   (70, 69, 81, 82), (71, 70, 82, 83), (72, 71, 83, 84), (61, 72, 84, 74), (86, 85, 97, 98),
                   (87, 86, 98, 99), (88, 87, 99, 100), (89, 88, 100, 101), (90, 89, 101, 102), (91, 90, 102, 103),
                   (92, 91, 103, 104), (93, 92, 104, 105), (94, 93, 105, 106), (95, 94, 106, 107), (96, 95, 107, 108),
                   (97, 85, 96, 108), (98, 97, 109, 110), (99, 98, 110, 111), (100, 99, 111, 112), (101, 100, 112, 113),
                   (102, 101, 113, 114), (108, 107, 119, 120), (108, 120, 109, 97), (119, 107, 127, 121),
                   (118, 119, 121, 122),
                   (117, 118, 122, 123), (116, 117, 123, 124), (115, 116, 124, 125), (114, 115, 125, 126),
                   (102, 114, 126, 132),
                   (107, 106, 128, 127), (106, 105, 129, 128), (105, 104, 130, 129), (104, 103, 131, 130),
                   (103, 102, 132, 131),
                   (121, 127, 134, 133), (122, 121, 133, 135), (123, 122, 135, 136), (124, 123, 136, 137),
                   (125, 124, 137, 138),
                   (126, 125, 138, 139), (132, 126, 139, 140), (127, 128, 141, 134), (128, 129, 142, 141),
                   (129, 130, 143, 142),
                   (130, 131, 144, 143), (131, 132, 140, 144), (138, 144, 140, 139), (137, 143, 144, 138),
                   (136, 142, 143, 137),
                   (135, 141, 142, 136), (133, 134, 141, 135), (110, 109, 145), (111, 110, 145), (112, 111, 145),
                   (113, 112, 145), (114, 113, 145), (115, 114, 145), (116, 115, 145), (117, 116, 145),
                   (118, 117, 145), (119, 118, 145), (120, 119, 145), (109, 120, 145)]

        return myvertex, myfaces


    # ----------------------------------------------
    # Handle model 02
    # ----------------------------------------------
    def handle_model_02(self):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.04349547624588013
        maxx = 0.04352114722132683
        miny = -0.08959200233221054
        maxy = 0
        minz = -0.04352371022105217
        maxz = 0.04349301755428314

        # Vertex
        myvertex = [(minx + 0.013302795588970184, maxy - 0.002780601382255554, minz + 0.010707870125770569),
                    (minx + 0.0009496212005615234, maxy - 0.002942140679806471, minz + 0.030204588547348976),
                    (minx, maxy - 0.003071820829063654, maxz - 0.033750676549971104),
                    (minx + 0.010708402842283249, maxy - 0.0031348932534456253, maxz - 0.013303784653544426),
                    (minx + 0.03020550962537527, maxy - 0.003114458406344056, maxz - 0.0009501762688159943),
                    (maxx - 0.03374953381717205, maxy - 0.003015991533175111, maxz),
                    (maxx - 0.01330280676484108, maxy - 0.0028658765368163586, maxz - 0.010707847774028778),
                    (maxx - 0.0009496286511421204, maxy - 0.0027043374720960855, maxz - 0.030204561538994312),
                    (maxx, maxy - 0.0025746573228389025, minz + 0.03375071194022894),
                    (maxx - 0.010708380490541458, maxy - 0.002511584199965, minz + 0.013303810730576515),
                    (maxx - 0.03020548354834318, maxy - 0.0025320190470665693, minz + 0.0009501948952674866),
                    (minx + 0.03374955803155899, maxy - 0.0026304861530661583, minz),
                    (minx + 0.014472760260105133, maxy - 0.019589224830269814, minz + 0.011804874986410141),
                    (minx + 0.002567145973443985, maxy - 0.019744910299777985, minz + 0.030595174990594387),
                    (minx + 0.001651916652917862, maxy - 0.019869891926646233, maxz - 0.034195657819509506),
                    (minx + 0.011972300708293915, maxy - 0.019930677488446236, maxz - 0.014489583671092987),
                    (minx + 0.03076297417283058, maxy - 0.019910985603928566, maxz - 0.0025835558772087097),
                    (maxx - 0.034027633257210255, maxy - 0.019816085696220398, maxz - 0.0016677752137184143),
                    (maxx - 0.014321718364953995, maxy - 0.01967141032218933, maxz - 0.011987630277872086),
                    (maxx - 0.002416089177131653, maxy - 0.01951572299003601, maxz - 0.030777926556766033),
                    (maxx - 0.0015008561313152313, maxy - 0.019390743225812912, minz + 0.03401290811598301),
                    (maxx - 0.011821221560239792, maxy - 0.01932995393872261, minz + 0.014306826516985893),
                    (maxx - 0.03061189129948616, maxy - 0.01934964768588543, minz + 0.002400781959295273),
                    (minx + 0.03417872078716755, maxy - 0.019444547593593597, minz + 0.001484982669353485),
                    (minx + 0.043508310547622386, maxy - 0.005668943747878075, maxz - 0.043508357635801076),
                    (minx + 0.029034355655312538, maxy - 0.019612153992056847, minz + 0.027617475017905235),
                    (minx + 0.023084014654159546, maxy - 0.01968996599316597, minz + 0.03700872650370002),
                    (minx + 0.022626593708992004, maxy - 0.01975242979824543, maxz - 0.03889966616407037),
                    (minx + 0.027784643694758415, maxy - 0.019782811403274536, maxz - 0.029050718992948532),
                    (minx + 0.03717608004808426, maxy - 0.019772969186306, maxz - 0.023100173100829124),
                    (maxx - 0.03873214777559042, maxy - 0.019725536927580833, maxz - 0.022642474621534348),
                    (maxx - 0.02888327743858099, maxy - 0.019653232768177986, maxz - 0.02780025824904442),
                    (maxx - 0.022932931780815125, maxy - 0.019575420767068863, maxz - 0.0371915097348392),
                    (maxx - 0.022475499659776688, maxy - 0.019512956961989403, minz + 0.03871688432991505),
                    (maxx - 0.0276335496455431, maxy - 0.019482573494315147, minz + 0.02886793203651905),
                    (maxx - 0.03702498506754637, maxy - 0.019492419436573982, minz + 0.022917380556464195),
                    (minx + 0.038883245550096035, maxy - 0.0195398461073637, minz + 0.022459672763943672),
                    (minx + 0.029087782837450504, maxy - 0.03150090575218201, minz + 0.027552824467420578),
                    (minx + 0.023137442767620087, maxy - 0.03157871589064598, minz + 0.036944076884537935),
                    (minx + 0.022680018097162247, maxy - 0.03164118155837059, maxz - 0.03896431624889374),
                    (minx + 0.027838071808218956, maxy - 0.031671565026044846, maxz - 0.029115368612110615),
                    (minx + 0.0372295081615448, maxy - 0.03166172280907631, maxz - 0.023164819926023483),
                    (maxx - 0.03867871919646859, maxy - 0.03161429241299629, maxz - 0.022707123309373856),
                    (maxx - 0.028829848393797874, maxy - 0.03154198080301285, maxz - 0.027864910662174225),
                    (maxx - 0.022879503667354584, maxy - 0.031464170664548874, maxz - 0.037256159354001284),
                    (maxx - 0.022422071546316147, maxy - 0.03140170872211456, minz + 0.038652234710752964),
                    (maxx - 0.02758011966943741, maxy - 0.03137132152915001, minz + 0.028803281486034393),
                    (maxx - 0.03697155695408583, maxy - 0.031381167471408844, minz + 0.022852730005979538),
                    (minx + 0.038936673663556576, maxy - 0.03142859786748886, minz + 0.022395022213459015),
                    (minx + 0.029038896784186363, maxy - 0.020622700452804565, minz + 0.027611978352069855),
                    (minx + 0.02308855764567852, maxy - 0.02070051059126854, minz + 0.0370032312348485),
                    (minx + 0.02263113297522068, maxy - 0.020762978121638298, maxz - 0.038905161898583174),
                    (minx + 0.02778918668627739, maxy - 0.020793357864022255, maxz - 0.029056214727461338),
                    (minx + 0.037180622573941946, maxy - 0.02078351564705372, maxz - 0.023105667904019356),
                    (maxx - 0.03872760524973273, maxy - 0.020736083388328552, maxz - 0.02264796942472458),
                    (maxx - 0.028878736309707165, maxy - 0.020663777366280556, maxz - 0.0278057549148798),
                    (maxx - 0.02292838878929615, maxy - 0.020585965365171432, maxz - 0.03719700500369072),
                    (maxx - 0.022470960393548012, maxy - 0.020523501560091972, minz + 0.0387113899923861),
                    (maxx - 0.027629008516669273, maxy - 0.020493119955062866, minz + 0.028862436302006245),
                    (maxx - 0.03702044300734997, maxy - 0.020502964034676552, minz + 0.022911883890628815),
                    (minx + 0.03888778714463115, maxy - 0.02055039070546627, minz + 0.02245417609810829),
                    (minx + 0.03503026906400919, maxy - 0.0326739065349102, minz + 0.03399384953081608),
                    (minx + 0.03150810860097408, maxy - 0.032719966024160385, minz + 0.03955277753993869),
                    (minx + 0.03123734798282385, maxy - 0.03275693953037262, maxz - 0.04088863683864474),
                    (minx + 0.034290531650185585, maxy - 0.032774921506643295, maxz - 0.035058788023889065),
                    (minx + 0.039849569322541356, maxy - 0.0327690951526165, maxz - 0.03153650462627411),
                    (maxx - 0.04059170465916395, maxy - 0.03274102136492729, maxz - 0.03126558102667332),
                    (maxx - 0.03476190101355314, maxy - 0.032698217779397964, maxz - 0.03431860730051994),
                    (maxx - 0.031239738687872887, maxy - 0.03265216201543808, maxz - 0.039877534145489335),
                    (maxx - 0.03096897155046463, maxy - 0.032615188509225845, minz + 0.040563880698755383),
                    (maxx - 0.03402215428650379, maxy - 0.03259720280766487, minz + 0.03473402839154005),
                    (maxx - 0.03958118986338377, maxy - 0.032603029161691666, minz + 0.03121174033731222),
                    (minx + 0.04086008481681347, maxy - 0.032631102949380875, minz + 0.030940811149775982),
                    (minx + 0.026877090334892273, maxy - 0.04475956782698631, minz + 0.02504805289208889),
                    (minx + 0.020004114136099815, miny + 0.044742558151483536, minz + 0.03589546587318182),
                    (minx + 0.019475765526294708, miny + 0.044670410454273224, maxz - 0.03829052206128836),
                    (minx + 0.025433603674173355, miny + 0.04463531821966171, maxz - 0.0269144456833601),
                    (minx + 0.03628123179078102, miny + 0.04464668035507202, maxz - 0.020041238516569138),
                    (maxx - 0.0379045819863677, miny + 0.0447014644742012, maxz - 0.01951257325708866),
                    (maxx - 0.02652859501540661, miny + 0.044784992933273315, maxz - 0.02547009475529194),
                    (maxx - 0.01965562254190445, maxy - 0.04471714794635773, maxz - 0.036317508202046156),
                    (maxx - 0.019127257168293, maxy - 0.04464499279856682, minz + 0.03786848206073046),
                    (maxx - 0.02508508786559105, maxy - 0.04460989683866501, minz + 0.026492400094866753),
                    (maxx - 0.03593271458521485, maxy - 0.044621266424655914, minz + 0.019619181752204895),
                    (minx + 0.03825310105457902, maxy - 0.044676050543785095, minz + 0.01909050904214382),
                    (minx + 0.01721818558871746, miny + 0.00031135231256484985, minz + 0.01437518559396267),
                    (minx + 0.006362196058034897, miny + 0.00016936659812927246, minz + 0.03150887507945299),
                    (minx + 0.005527656525373459, miny + 5.542486906051636e-05, maxz - 0.03524145483970642),
                    (minx + 0.014938175678253174, miny, maxz - 0.017272725701332092),
                    (minx + 0.032072206027805805, miny + 1.7955899238586426e-05, maxz - 0.006416358053684235),
                    (maxx - 0.03467791061848402, miny + 0.00010447949171066284, maxz - 0.0055813267827034),
                    (maxx - 0.016709323972463608, miny + 0.00023641437292099, maxz - 0.01499134860932827),
                    (maxx - 0.005853328853845596, miny + 0.00037835538387298584, maxz - 0.032125042751431465),
                    (maxx - 0.0050187669694423676, miny + 0.0004923418164253235, minz + 0.03462529182434082),
                    (maxx - 0.014429278671741486, miny + 0.0005477666854858398, minz + 0.016656557098031044),
                    (maxx - 0.03156330715864897, miny + 0.0005298107862472534, minz + 0.005800176411867142),
                    (minx + 0.03518681041896343, miny + 0.000443287193775177, minz + 0.0049651265144348145),
                    (minx + 0.02942624967545271, miny + 0.0012636110186576843, minz + 0.027632080018520355),
                    (minx + 0.023563016206026077, miny + 0.0011869296431541443, minz + 0.03688584640622139),
                    (minx + 0.023112289607524872, miny + 0.0011253878474235535, maxz - 0.039185164496302605),
                    (minx + 0.028194833546876907, miny + 0.0010954588651657104, maxz - 0.029480399563908577),
                    (minx + 0.037448784336447716, miny + 0.0011051595211029053, maxz - 0.023616963997483253),
                    (maxx - 0.038622063118964434, miny + 0.0011518821120262146, maxz - 0.023165971040725708),
                    (maxx - 0.028917375952005386, miny + 0.001223146915435791, maxz - 0.02824824769049883),
                    (maxx - 0.02305414155125618, miny + 0.0012998059391975403, maxz - 0.0375020164065063),
                    (maxx - 0.02260340191423893, miny + 0.0013613700866699219, minz + 0.03856899822130799),
                    (maxx - 0.027685942128300667, miny + 0.001391299068927765, minz + 0.028864230029284954),
                    (maxx - 0.0369398919865489, miny + 0.001381605863571167, minz + 0.023000789806246758),
                    (minx + 0.03913095686584711, miny + 0.0013348758220672607, minz + 0.022549785673618317),
                    (minx + 0.03738117218017578, miny + 0.0037613436579704285, minz + 0.03627043403685093),
                    (minx + 0.03477128129452467, miny + 0.0037272050976753235, minz + 0.04038954642601311),
                    (minx + 0.034570650197565556, miny + 0.0036998093128204346, maxz - 0.041754934238269925),
                    (minx + 0.03683303436264396, miny + 0.0036864876747131348, maxz - 0.03743506921455264),
                    (minx + 0.040952228708192706, miny + 0.0036908015608787537, maxz - 0.03482509031891823),
                    (maxx - 0.0411921211052686, miny + 0.003711603581905365, maxz - 0.03462434001266956),
                    (maxx - 0.03687229100614786, miny + 0.0037433207035064697, maxz - 0.03688660357147455),
                    (maxx - 0.034262401051819324, miny + 0.003777444362640381, maxz - 0.04100571759045124),
                    (maxx - 0.03406176343560219, miny + 0.0038048475980758667, minz + 0.0411387647036463),
                    (maxx - 0.036324144806712866, miny + 0.0038181766867637634, minz + 0.03681889921426773),
                    (maxx - 0.04044333938509226, miny + 0.0038138628005981445, minz + 0.03420891519635916),
                    (minx + 0.04170101135969162, miny + 0.003793060779571533, minz + 0.034008161164820194),
                    (maxx - 0.043253868410829455, miny + 0.00480072945356369, minz + 0.04320027763606049),
                    (minx + 0.03971285093575716, maxy - 0.041327137500047684, maxz - 0.031046375632286072),
                    (maxx - 0.03359287604689598, maxy - 0.04114784672856331, minz + 0.03433086443692446),
                    (minx + 0.03072980046272278, maxy - 0.04131445661187172, maxz - 0.040801193099468946),
                    (minx + 0.031012218445539474, maxy - 0.04127589240670204, minz + 0.03935709968209267),
                    (minx + 0.04076687735505402, maxy - 0.04118320718407631, minz + 0.030374319292604923),
                    (minx + 0.034451283514499664, maxy - 0.03338594362139702, minz + 0.033365121111273766),
                    (minx + 0.030692334286868572, maxy - 0.03343509882688522, minz + 0.039297766517847776),
                    (minx + 0.03040337096899748, maxy - 0.03347455710172653, maxz - 0.040701600490137935),
                    (minx + 0.03366181440651417, maxy - 0.03349374979734421, maxz - 0.03447982110083103),
                    (minx + 0.03959457715973258, maxy - 0.033487528562545776, maxz - 0.03072074055671692),
                    (maxx - 0.040404647355899215, maxy - 0.033457569777965546, maxz - 0.030431604012846947),
                    (maxx - 0.03418291546404362, maxy - 0.03341188654303551, maxz - 0.03368987888097763),
                    (maxx - 0.030423964373767376, maxy - 0.0333627350628376, maxz - 0.03962252289056778),
                    (maxx - 0.030134993605315685, maxy - 0.03332327678799629, minz + 0.04037684458307922),
                    (maxx - 0.033393437042832375, maxy - 0.03330408036708832, minz + 0.03415506146848202),
                    (maxx - 0.03932619746774435, maxy - 0.03331030160188675, minz + 0.030395975336432457),
                    (minx + 0.040673027746379375, maxy - 0.03334026038646698, minz + 0.030106833204627037),
                    (minx + 0.030282274819910526, maxy - 0.005427400581538677, maxz - 0.0011750981211662292),
                    (minx + 0.013463903218507767, maxy - 0.005095209460705519, minz + 0.0108589306473732),
                    (minx + 0.010882444679737091, maxy - 0.005447734147310257, maxz - 0.013467073440551758),
                    (minx + 0.0011723600327968597, maxy - 0.005255943164229393, minz + 0.030258373357355595),
                    (minx + 0.0002274736762046814, maxy - 0.005384976044297218, maxz - 0.033811951987445354),
                    (maxx - 0.0134431142359972, maxy - 0.005180059932172298, maxz - 0.010884080082178116),
                    (maxx - 0.033787828870117664, maxy - 0.005329424981027842, maxz - 0.00022966042160987854),
                    (maxx - 0.0302614476531744, maxy - 0.004847868345677853, minz + 0.0011499449610710144),
                    (maxx - 0.00020667165517807007, maxy - 0.004890293348580599, minz + 0.03378681745380163),
                    (maxx - 0.0011515654623508453, maxy - 0.0050193266943097115, maxz - 0.03028351627290249),
                    (minx + 0.033808655105531216, maxy - 0.004945843946188688, minz + 0.0002044886350631714),
                    (maxx - 0.010861624032258987, maxy - 0.004827534779906273, minz + 0.013441929593682289),
                    (minx + 0.03468604106456041, maxy - 0.04122784733772278, minz + 0.033558815717697144),
                    (minx + 0.033914451487362385, maxy - 0.041333213448524475, maxz - 0.03472032118588686),
                    (maxx - 0.04044530005194247, maxy - 0.04129785671830177, maxz - 0.03076378908008337),
                    (maxx - 0.034364476799964905, maxy - 0.04125320911407471, maxz - 0.03394827153533697),
                    (maxx - 0.03069065511226654, maxy - 0.04120517522096634, maxz - 0.03974655526690185),
                    (maxx - 0.030408228747546673, maxy - 0.04116660729050636, minz + 0.04041173937730491),
                    (maxx - 0.03939127502962947, maxy - 0.0411539226770401, minz + 0.030656912364065647),
                    (minx + 0.03147818427532911, maxy - 0.033236272633075714, minz + 0.03954096930101514),
                    (minx + 0.031206720508635044, maxy - 0.03327333927154541, maxz - 0.04088335996493697),
                    (minx + 0.034267837181687355, maxy - 0.033291369676589966, maxz - 0.03503836318850517),
                    (minx + 0.03984131896868348, maxy - 0.03328552842140198, maxz - 0.03150692768394947),
                    (maxx - 0.040582869900390506, maxy - 0.0332573801279068, maxz - 0.03123530000448227),
                    (maxx - 0.03473791852593422, maxy - 0.033214468508958817, maxz - 0.03429625928401947),
                    (maxx - 0.031206604093313217, maxy - 0.03316829353570938, maxz - 0.03986963024362922),
                    (maxx - 0.030935133807361126, maxy - 0.03313122317194939, minz + 0.040554699720814824),
                    (maxx - 0.03399624954909086, maxy - 0.03311318904161453, minz + 0.03470969945192337),
                    (maxx - 0.03956972947344184, maxy - 0.03311903029680252, minz + 0.031178259290754795),
                    (minx + 0.04085446032695472, maxy - 0.0331471785902977, minz + 0.030906626023352146),
                    (minx + 0.035009496845304966, maxy - 0.03319009393453598, minz + 0.03396759741008282)]

        # Faces
        myfaces = [(24, 0, 1), (24, 1, 2), (24, 2, 3), (24, 3, 4), (24, 4, 5),
                   (24, 5, 6), (24, 6, 7), (24, 7, 8), (24, 8, 9), (24, 9, 10),
                   (24, 10, 11), (11, 0, 24), (140, 12, 13, 142), (142, 13, 14, 143), (143, 14, 15, 141),
                   (141, 15, 16, 139), (139, 16, 17, 145), (145, 17, 18, 144), (144, 18, 19, 148), (148, 19, 20, 147),
                   (147, 20, 21, 150), (150, 21, 22, 146), (146, 22, 23, 149), (140, 0, 11, 149), (13, 12, 25, 26),
                   (14, 13, 26, 27), (15, 14, 27, 28), (16, 15, 28, 29), (17, 16, 29, 30), (18, 17, 30, 31),
                   (19, 18, 31, 32), (20, 19, 32, 33), (21, 20, 33, 34), (22, 21, 34, 35), (23, 22, 35, 36),
                   (12, 23, 36, 25), (25, 49, 50, 26), (49, 37, 38, 50), (26, 50, 51, 27), (50, 38, 39, 51),
                   (27, 51, 52, 28), (51, 39, 40, 52), (28, 52, 53, 29), (52, 40, 41, 53), (29, 53, 54, 30),
                   (53, 41, 42, 54), (30, 54, 55, 31), (54, 42, 43, 55), (31, 55, 56, 32), (55, 43, 44, 56),
                   (32, 56, 57, 33), (56, 44, 45, 57), (33, 57, 58, 34), (57, 45, 46, 58), (34, 58, 59, 35),
                   (58, 46, 47, 59), (35, 59, 60, 36), (59, 47, 48, 60), (36, 60, 49, 25), (60, 48, 37, 49),
                   (38, 37, 61, 62), (39, 38, 62, 63), (40, 39, 63, 64), (41, 40, 64, 65), (42, 41, 65, 66),
                   (43, 42, 66, 67), (44, 43, 67, 68), (45, 44, 68, 69), (46, 45, 69, 70), (47, 46, 70, 71),
                   (48, 47, 71, 72), (37, 48, 72, 61), (124, 125, 74, 75), (74, 73, 85, 86), (79, 78, 90, 91),
                   (80, 79, 91, 92), (77, 76, 88, 89), (82, 81, 93, 94), (76, 75, 87, 88), (81, 80, 92, 93),
                   (73, 84, 96, 85), (84, 83, 95, 96), (83, 82, 94, 95), (78, 77, 89, 90), (75, 74, 86, 87),
                   (90, 89, 101, 102), (86, 85, 97, 98), (93, 92, 104, 105), (96, 95, 107, 108), (85, 96, 108, 97),
                   (89, 88, 100, 101), (91, 90, 102, 103), (88, 87, 99, 100), (92, 91, 103, 104), (95, 94, 106, 107),
                   (94, 93, 105, 106), (87, 86, 98, 99), (105, 104, 116, 117), (108, 107, 119, 120), (97, 108, 120, 109),
                   (101, 100, 112, 113), (103, 102, 114, 115), (100, 99, 111, 112), (104, 103, 115, 116),
                   (107, 106, 118, 119),
                   (106, 105, 117, 118), (99, 98, 110, 111), (102, 101, 113, 114), (98, 97, 109, 110), (120, 119, 121),
                   (109, 120, 121), (113, 112, 121), (115, 114, 121), (112, 111, 121), (116, 115, 121),
                   (119, 118, 121), (118, 117, 121), (111, 110, 121), (114, 113, 121), (110, 109, 121),
                   (117, 116, 121), (169, 158, 62, 61), (158, 159, 63, 62), (159, 160, 64, 63), (160, 161, 65, 64),
                   (161, 162, 66, 65), (162, 163, 67, 66), (163, 164, 68, 67), (164, 165, 69, 68), (165, 166, 70, 69),
                   (166, 167, 71, 70), (167, 168, 72, 71), (168, 169, 61, 72), (72, 138, 127, 61), (63, 129, 130, 64),
                   (67, 133, 134, 68), (64, 130, 131, 65), (61, 127, 128, 62), (69, 135, 136, 70), (66, 132, 133, 67),
                   (65, 131, 132, 66), (71, 137, 138, 72), (70, 136, 137, 71), (62, 128, 129, 63), (68, 134, 135, 69),
                   (0, 140, 142, 1), (1, 142, 143, 2), (2, 143, 141, 3), (3, 141, 139, 4), (4, 139, 145, 5),
                   (5, 145, 144, 6), (6, 144, 148, 7), (7, 148, 147, 8), (8, 147, 150, 9), (9, 150, 146, 10),
                   (10, 146, 149, 11), (12, 140, 149, 23), (153, 154, 163, 162), (154, 155, 164, 163), (155, 156, 165, 164),
                   (125, 151, 73, 74), (152, 124, 75, 76), (122, 152, 76, 77), (153, 122, 77, 78), (154, 153, 78, 79),
                   (155, 154, 79, 80), (156, 155, 80, 81), (123, 156, 81, 82), (157, 123, 82, 83), (126, 157, 83, 84),
                   (73, 151, 126, 84), (151, 125, 158, 169), (125, 124, 159, 158), (124, 152, 160, 159),
                   (152, 122, 161, 160),
                   (122, 153, 162, 161), (156, 123, 166, 165), (123, 157, 167, 166), (157, 126, 168, 167),
                   (126, 151, 169, 168)]

        return myvertex, myfaces


    # ----------------------------------------------
    # Handle model 03
    # ----------------------------------------------
    def handle_model_03(self):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.04349547624588013
        maxx = 0.04352114722132683
        miny = -0.09871400892734528
        maxy = 0
        minz = -0.04352371022105217
        maxz = 0.04349301755428314

        # Vertex
        myvertex = [(minx + 0.013302795588970184, maxy - 0.002780601382255554, minz + 0.010707870125770569),
                    (minx + 0.0009496212005615234, maxy - 0.002942140679806471, minz + 0.030204588547348976),
                    (minx, maxy - 0.003071820829063654, maxz - 0.033750676549971104),
                    (minx + 0.010708402842283249, maxy - 0.0031348932534456253, maxz - 0.013303784653544426),
                    (minx + 0.03020550962537527, maxy - 0.003114458406344056, maxz - 0.0009501762688159943),
                    (maxx - 0.03374953381717205, maxy - 0.003015991533175111, maxz),
                    (maxx - 0.01330280676484108, maxy - 0.0028658765368163586, maxz - 0.010707847774028778),
                    (maxx - 0.0009496286511421204, maxy - 0.0027043374720960855, maxz - 0.030204561538994312),
                    (maxx, maxy - 0.0025746573228389025, minz + 0.03375071194022894),
                    (maxx - 0.010708380490541458, maxy - 0.002511584199965, minz + 0.013303810730576515),
                    (maxx - 0.03020548354834318, maxy - 0.0025320190470665693, minz + 0.0009501948952674866),
                    (minx + 0.03374955803155899, maxy - 0.0026304861530661583, minz),
                    (minx + 0.014472760260105133, maxy - 0.019589224830269814, minz + 0.011804874986410141),
                    (minx + 0.002567145973443985, maxy - 0.019744910299777985, minz + 0.030595174990594387),
                    (minx + 0.001651916652917862, maxy - 0.019869891926646233, maxz - 0.034195657819509506),
                    (minx + 0.011972300708293915, maxy - 0.019930677488446236, maxz - 0.014489583671092987),
                    (minx + 0.03076297417283058, maxy - 0.019910985603928566, maxz - 0.0025835558772087097),
                    (maxx - 0.034027633257210255, maxy - 0.019816085696220398, maxz - 0.0016677752137184143),
                    (maxx - 0.014321718364953995, maxy - 0.01967141032218933, maxz - 0.011987630277872086),
                    (maxx - 0.002416089177131653, maxy - 0.01951572299003601, maxz - 0.030777926556766033),
                    (maxx - 0.0015008561313152313, maxy - 0.019390743225812912, minz + 0.03401290811598301),
                    (maxx - 0.011821221560239792, maxy - 0.01932995393872261, minz + 0.014306826516985893),
                    (maxx - 0.03061189129948616, maxy - 0.01934964768588543, minz + 0.002400781959295273),
                    (minx + 0.03417872078716755, maxy - 0.019444547593593597, minz + 0.001484982669353485),
                    (minx + 0.043508310547622386, maxy - 0.005668943747878075, maxz - 0.043508357635801076),
                    (minx + 0.029034355655312538, maxy - 0.019612153992056847, minz + 0.027617475017905235),
                    (minx + 0.023084014654159546, maxy - 0.01968996599316597, minz + 0.03700872650370002),
                    (minx + 0.022626593708992004, maxy - 0.01975242979824543, maxz - 0.03889966616407037),
                    (minx + 0.027784643694758415, maxy - 0.019782811403274536, maxz - 0.029050718992948532),
                    (minx + 0.03717608004808426, maxy - 0.019772969186306, maxz - 0.023100173100829124),
                    (maxx - 0.03873214777559042, maxy - 0.019725536927580833, maxz - 0.022642474621534348),
                    (maxx - 0.02888327743858099, maxy - 0.019653232768177986, maxz - 0.02780025824904442),
                    (maxx - 0.022932931780815125, maxy - 0.019575420767068863, maxz - 0.0371915097348392),
                    (maxx - 0.022475499659776688, maxy - 0.019512956961989403, minz + 0.03871688432991505),
                    (maxx - 0.0276335496455431, maxy - 0.019482573494315147, minz + 0.02886793203651905),
                    (maxx - 0.03702498506754637, maxy - 0.019492419436573982, minz + 0.022917380556464195),
                    (minx + 0.038883245550096035, maxy - 0.0195398461073637, minz + 0.022459672763943672),
                    (minx + 0.029087782837450504, maxy - 0.03150090575218201, minz + 0.027552824467420578),
                    (minx + 0.023137442767620087, maxy - 0.03157871589064598, minz + 0.036944076884537935),
                    (minx + 0.022680018097162247, maxy - 0.03164118155837059, maxz - 0.03896431624889374),
                    (minx + 0.027838071808218956, maxy - 0.031671565026044846, maxz - 0.029115368612110615),
                    (minx + 0.0372295081615448, maxy - 0.03166172280907631, maxz - 0.023164819926023483),
                    (maxx - 0.03867871919646859, maxy - 0.03161429241299629, maxz - 0.022707123309373856),
                    (maxx - 0.028829848393797874, maxy - 0.03154198080301285, maxz - 0.027864910662174225),
                    (maxx - 0.022879503667354584, maxy - 0.031464170664548874, maxz - 0.037256159354001284),
                    (maxx - 0.022422071546316147, maxy - 0.03140170872211456, minz + 0.038652234710752964),
                    (maxx - 0.02758011966943741, maxy - 0.03137132152915001, minz + 0.028803281486034393),
                    (maxx - 0.03697155695408583, maxy - 0.031381167471408844, minz + 0.022852730005979538),
                    (minx + 0.038936673663556576, maxy - 0.03142859786748886, minz + 0.022395022213459015),
                    (minx + 0.029038896784186363, maxy - 0.020622700452804565, minz + 0.027611978352069855),
                    (minx + 0.02308855764567852, maxy - 0.02070051059126854, minz + 0.0370032312348485),
                    (minx + 0.02263113297522068, maxy - 0.020762978121638298, maxz - 0.038905161898583174),
                    (minx + 0.02778918668627739, maxy - 0.020793357864022255, maxz - 0.029056214727461338),
                    (minx + 0.037180622573941946, maxy - 0.02078351564705372, maxz - 0.023105667904019356),
                    (maxx - 0.03872760524973273, maxy - 0.020736083388328552, maxz - 0.02264796942472458),
                    (maxx - 0.028878736309707165, maxy - 0.020663777366280556, maxz - 0.0278057549148798),
                    (maxx - 0.02292838878929615, maxy - 0.020585965365171432, maxz - 0.03719700500369072),
                    (maxx - 0.022470960393548012, maxy - 0.020523501560091972, minz + 0.0387113899923861),
                    (maxx - 0.027629008516669273, maxy - 0.020493119955062866, minz + 0.028862436302006245),
                    (maxx - 0.03702044300734997, maxy - 0.020502964034676552, minz + 0.022911883890628815),
                    (minx + 0.03888778714463115, maxy - 0.02055039070546627, minz + 0.02245417609810829),
                    (minx + 0.03503026906400919, maxy - 0.0326739065349102, minz + 0.03399384953081608),
                    (minx + 0.03150810860097408, maxy - 0.032719966024160385, minz + 0.03955277753993869),
                    (minx + 0.03123734798282385, maxy - 0.03275693953037262, maxz - 0.04088863683864474),
                    (minx + 0.034290531650185585, maxy - 0.032774921506643295, maxz - 0.035058788023889065),
                    (minx + 0.039849569322541356, maxy - 0.0327690951526165, maxz - 0.03153650462627411),
                    (maxx - 0.04059170465916395, maxy - 0.03274102136492729, maxz - 0.03126558102667332),
                    (maxx - 0.03476190101355314, maxy - 0.032698217779397964, maxz - 0.03431860730051994),
                    (maxx - 0.031239738687872887, maxy - 0.03265216201543808, maxz - 0.039877534145489335),
                    (maxx - 0.03096897155046463, maxy - 0.032615188509225845, minz + 0.040563880698755383),
                    (maxx - 0.03402215428650379, maxy - 0.03259720280766487, minz + 0.03473402839154005),
                    (maxx - 0.03958118986338377, maxy - 0.032603029161691666, minz + 0.03121174033731222),
                    (minx + 0.04086008481681347, maxy - 0.032631102949380875, minz + 0.030940811149775982),
                    (minx + 0.026877090334892273, maxy - 0.04475956782698631, minz + 0.02504805289208889),
                    (minx + 0.020004114136099815, maxy - 0.044849444180727005, minz + 0.03589546587318182),
                    (minx + 0.019475765526294708, maxy - 0.04492159187793732, maxz - 0.03829052206128836),
                    (minx + 0.025433603674173355, maxy - 0.04495668411254883, maxz - 0.0269144456833601),
                    (minx + 0.03628123179078102, maxy - 0.04494532197713852, maxz - 0.020041238516569138),
                    (maxx - 0.0379045819863677, maxy - 0.04489053785800934, maxz - 0.01951257325708866),
                    (maxx - 0.02652859501540661, maxy - 0.044807009398937225, maxz - 0.02547009475529194),
                    (maxx - 0.01965562254190445, maxy - 0.04471714794635773, maxz - 0.036317508202046156),
                    (maxx - 0.019127257168293, maxy - 0.04464499279856682, minz + 0.03786848206073046),
                    (maxx - 0.02508508786559105, maxy - 0.04460989683866501, minz + 0.026492400094866753),
                    (maxx - 0.03593271458521485, maxy - 0.044621266424655914, minz + 0.019619181752204895),
                    (minx + 0.03825310105457902, maxy - 0.044676050543785095, minz + 0.01909050904214382),
                    (minx + 0.021551070734858513, miny + 0.00942724198102951, minz + 0.01908031851053238),
                    (minx + 0.01246710866689682, miny + 0.009308435022830963, minz + 0.03341726865619421),
                    (minx + 0.011768791824579239, miny + 0.009213089942932129, maxz - 0.03664115583524108),
                    (minx + 0.019643226638436317, miny + 0.009166710078716278, maxz - 0.0216054730117321),
                    (minx + 0.033980460837483406, miny + 0.009181737899780273, maxz - 0.012521196156740189),
                    (maxx - 0.036077769473195076, miny + 0.009254135191440582, maxz - 0.011822465807199478),
                    (maxx - 0.021042203530669212, miny + 0.0093645378947258, maxz - 0.019696485251188278),
                    (maxx - 0.011958237737417221, miny + 0.009483307600021362, maxz - 0.03403343725949526),
                    (maxx - 0.011259902268648148, miny + 0.009578689932823181, minz + 0.03602499142289162),
                    (maxx - 0.01913433149456978, miny + 0.009625062346458435, minz + 0.020989302545785904),
                    (maxx - 0.03347156383097172, miny + 0.009610041975975037, minz + 0.011905014514923096),
                    (minx + 0.03658666601404548, miny + 0.00953763723373413, minz + 0.011206269264221191),
                    (minx + 0.02942624967545271, miny + 0.001430809497833252, minz + 0.027632080018520355),
                    (minx + 0.023563016206026077, miny + 0.001354128122329712, minz + 0.03688584640622139),
                    (minx + 0.023112289607524872, miny + 0.001292586326599121, maxz - 0.039185164496302605),
                    (minx + 0.028194833546876907, miny + 0.001262657344341278, maxz - 0.029480399563908577),
                    (minx + 0.037448784336447716, miny + 0.001272358000278473, maxz - 0.023616963997483253),
                    (maxx - 0.038622063118964434, miny + 0.0013190805912017822, maxz - 0.023165971040725708),
                    (maxx - 0.028917375952005386, miny + 0.0013903453946113586, maxz - 0.02824824769049883),
                    (maxx - 0.02305414155125618, miny + 0.001467004418373108, maxz - 0.0375020164065063),
                    (maxx - 0.02260340191423893, miny + 0.0015285685658454895, minz + 0.03856899822130799),
                    (maxx - 0.027685942128300667, miny + 0.0015584975481033325, minz + 0.028864230029284954),
                    (maxx - 0.0369398919865489, miny + 0.0015488043427467346, minz + 0.023000789806246758),
                    (minx + 0.03913095686584711, miny + 0.0015020743012428284, minz + 0.022549785673618317),
                    (minx + 0.03738117218017578, miny + 0.001003175973892212, minz + 0.03627043403685093),
                    (minx + 0.03477128129452467, miny + 0.0009690374135971069, minz + 0.04038954642601311),
                    (minx + 0.034570650197565556, miny + 0.000941641628742218, maxz - 0.041754934238269925),
                    (minx + 0.03683303436264396, miny + 0.0009283199906349182, maxz - 0.03743506921455264),
                    (minx + 0.040952228708192706, miny + 0.0009326338768005371, maxz - 0.03482509031891823),
                    (maxx - 0.0411921211052686, miny + 0.0009534358978271484, maxz - 0.03462434001266956),
                    (maxx - 0.03687229100614786, miny + 0.0009851530194282532, maxz - 0.03688660357147455),
                    (maxx - 0.034262401051819324, miny + 0.0010192766785621643, maxz - 0.04100571759045124),
                    (maxx - 0.03406176343560219, miny + 0.0010466799139976501, minz + 0.0411387647036463),
                    (maxx - 0.036324144806712866, miny + 0.0010600090026855469, minz + 0.03681889921426773),
                    (maxx - 0.04044333938509226, miny + 0.001055695116519928, minz + 0.03420891519635916),
                    (minx + 0.04170101135969162, miny + 0.0010348930954933167, minz + 0.034008161164820194),
                    (maxx - 0.043253868410829455, miny, minz + 0.04320027763606049),
                    (minx + 0.03971285093575716, maxy - 0.041327137500047684, maxz - 0.031046375632286072),
                    (maxx - 0.03359287604689598, maxy - 0.04114784672856331, minz + 0.03433086443692446),
                    (minx + 0.03072980046272278, maxy - 0.04131445661187172, maxz - 0.040801193099468946),
                    (minx + 0.031012218445539474, maxy - 0.04127589240670204, minz + 0.03935709968209267),
                    (minx + 0.04076687735505402, maxy - 0.04118320718407631, minz + 0.030374319292604923),
                    (minx + 0.034451283514499664, maxy - 0.03338594362139702, minz + 0.033365121111273766),
                    (minx + 0.030692334286868572, maxy - 0.03343509882688522, minz + 0.039297766517847776),
                    (minx + 0.03040337096899748, maxy - 0.03347455710172653, maxz - 0.040701600490137935),
                    (minx + 0.03366181440651417, maxy - 0.03349374979734421, maxz - 0.03447982110083103),
                    (minx + 0.03959457715973258, maxy - 0.033487528562545776, maxz - 0.03072074055671692),
                    (maxx - 0.040404647355899215, maxy - 0.033457569777965546, maxz - 0.030431604012846947),
                    (maxx - 0.03418291546404362, maxy - 0.03341188654303551, maxz - 0.03368987888097763),
                    (maxx - 0.030423964373767376, maxy - 0.0333627350628376, maxz - 0.03962252289056778),
                    (maxx - 0.030134993605315685, maxy - 0.03332327678799629, minz + 0.04037684458307922),
                    (maxx - 0.033393437042832375, maxy - 0.03330408036708832, minz + 0.03415506146848202),
                    (maxx - 0.03932619746774435, maxy - 0.03331030160188675, minz + 0.030395975336432457),
                    (minx + 0.040673027746379375, maxy - 0.03334026038646698, minz + 0.030106833204627037),
                    (minx + 0.030282274819910526, maxy - 0.005427400581538677, maxz - 0.0011750981211662292),
                    (minx + 0.013463903218507767, maxy - 0.005095209460705519, minz + 0.0108589306473732),
                    (minx + 0.010882444679737091, maxy - 0.005447734147310257, maxz - 0.013467073440551758),
                    (minx + 0.0011723600327968597, maxy - 0.005255943164229393, minz + 0.030258373357355595),
                    (minx + 0.0002274736762046814, maxy - 0.005384976044297218, maxz - 0.033811951987445354),
                    (maxx - 0.0134431142359972, maxy - 0.005180059932172298, maxz - 0.010884080082178116),
                    (maxx - 0.033787828870117664, maxy - 0.005329424981027842, maxz - 0.00022966042160987854),
                    (maxx - 0.0302614476531744, maxy - 0.004847868345677853, minz + 0.0011499449610710144),
                    (maxx - 0.00020667165517807007, maxy - 0.004890293348580599, minz + 0.03378681745380163),
                    (maxx - 0.0011515654623508453, maxy - 0.0050193266943097115, maxz - 0.03028351627290249),
                    (minx + 0.033808655105531216, maxy - 0.004945843946188688, minz + 0.0002044886350631714),
                    (maxx - 0.010861624032258987, maxy - 0.004827534779906273, minz + 0.013441929593682289),
                    (minx + 0.03468604106456041, maxy - 0.04122784733772278, minz + 0.033558815717697144),
                    (minx + 0.033914451487362385, maxy - 0.041333213448524475, maxz - 0.03472032118588686),
                    (maxx - 0.04044530005194247, maxy - 0.04129785671830177, maxz - 0.03076378908008337),
                    (maxx - 0.034364476799964905, maxy - 0.04125320911407471, maxz - 0.03394827153533697),
                    (maxx - 0.03069065511226654, maxy - 0.04120517522096634, maxz - 0.03974655526690185),
                    (maxx - 0.030408228747546673, maxy - 0.04116660729050636, minz + 0.04041173937730491),
                    (maxx - 0.03939127502962947, maxy - 0.0411539226770401, minz + 0.030656912364065647),
                    (minx + 0.03147818427532911, maxy - 0.033236272633075714, minz + 0.03954096930101514),
                    (minx + 0.031206720508635044, maxy - 0.03327333927154541, maxz - 0.04088335996493697),
                    (minx + 0.034267837181687355, maxy - 0.033291369676589966, maxz - 0.03503836318850517),
                    (minx + 0.03984131896868348, maxy - 0.03328552842140198, maxz - 0.03150692768394947),
                    (maxx - 0.040582869900390506, maxy - 0.0332573801279068, maxz - 0.03123530000448227),
                    (maxx - 0.03473791852593422, maxy - 0.033214468508958817, maxz - 0.03429625928401947),
                    (maxx - 0.031206604093313217, maxy - 0.03316829353570938, maxz - 0.03986963024362922),
                    (maxx - 0.030935133807361126, maxy - 0.03313122317194939, minz + 0.040554699720814824),
                    (maxx - 0.03399624954909086, maxy - 0.03311318904161453, minz + 0.03470969945192337),
                    (maxx - 0.03956972947344184, maxy - 0.03311903029680252, minz + 0.031178259290754795),
                    (minx + 0.04085446032695472, maxy - 0.0331471785902977, minz + 0.030906626023352146),
                    (minx + 0.035009496845304966, maxy - 0.03319009393453598, minz + 0.03396759741008282),
                    (minx + 0.019410474225878716, miny + 0.020503833889961243, minz + 0.016801605001091957),
                    (minx + 0.009459223598241806, miny + 0.020373672246932983, minz + 0.032507372088730335),
                    (maxx - 0.03541257046163082, miny + 0.02031419426202774, maxz - 0.008743710815906525),
                    (maxx - 0.0189414881169796, miny + 0.02043512463569641, maxz - 0.017369499430060387),
                    (maxx - 0.008990231901407242, miny + 0.02056524157524109, maxz - 0.03307527117431164),
                    (minx + 0.017320478335022926, miny + 0.02021842449903488, maxz - 0.01946074701845646),
                    (minx + 0.03302655927836895, miny + 0.02023487538099289, maxz - 0.009509153664112091),
                    (maxx - 0.008225221186876297, miny + 0.02066972106695175, minz + 0.0353640653192997),
                    (maxx - 0.016851460561156273, miny + 0.020720526576042175, minz + 0.018892847001552582),
                    (minx + 0.008694231510162354, miny + 0.020269230008125305, maxz - 0.03593196161091328),
                    (minx + 0.035881591495126486, miny + 0.020624756813049316, minz + 0.008175786584615707),
                    (maxx - 0.032557537779212, miny + 0.020704075694084167, minz + 0.008941244333982468),
                    (minx + 0.008214566856622696, miny + 0.023270338773727417, minz + 0.03213237784802914),
                    (maxx - 0.018073920160531998, miny + 0.023333996534347534, maxz - 0.016406163573265076),
                    (maxx - 0.007764074951410294, miny + 0.023468807339668274, maxz - 0.03267789073288441),
                    (minx + 0.03263115230947733, miny + 0.023126527667045593, maxz - 0.008262567222118378),
                    (maxx - 0.015908580273389816, miny + 0.023629695177078247, minz + 0.018027253448963165),
                    (minx + 0.01852441392838955, miny + 0.023405179381370544, minz + 0.015860654413700104),
                    (maxx - 0.03513853810727596, miny + 0.023208707571029663, maxz - 0.007469546049833298),
                    (minx + 0.016359103843569756, miny + 0.02310948073863983, maxz - 0.018572768196463585),
                    (maxx - 0.006971497088670731, miny + 0.023577049374580383, minz + 0.0350920120254159),
                    (minx + 0.007422015070915222, miny + 0.023162126541137695, maxz - 0.03563752118498087),
                    (minx + 0.035589066334068775, miny + 0.023530468344688416, minz + 0.00692400336265564),
                    (maxx - 0.032180625945329666, miny + 0.023612648248672485, minz + 0.0077170394361019135),
                    (minx + 0.021761823445558548, miny + 0.020728543400764465, minz + 0.019355909898877144),
                    (minx + 0.012772375717759132, miny + 0.020610973238945007, minz + 0.03354368917644024),
                    (maxx - 0.03617278253659606, miny + 0.020557239651679993, maxz - 0.012130718678236008),
                    (maxx - 0.021293656900525093, miny + 0.020666487514972687, maxz - 0.019922811537981033),
                    (maxx - 0.012304211035370827, miny + 0.02078402042388916, maxz - 0.03411059454083443),
                    (minx + 0.019873831421136856, miny + 0.020470723509788513, maxz - 0.021811936050653458),
                    (minx + 0.034061891958117485, miny + 0.020485587418079376, maxz - 0.01282217912375927),
                    (maxx - 0.011613138020038605, miny + 0.020878411829471588, minz + 0.0361242787912488),
                    (maxx - 0.019405635073781013, miny + 0.02092430740594864, minz + 0.02124503068625927),
                    (minx + 0.012081325054168701, miny + 0.020516619086265564, maxz - 0.03669118043035269),
                    (minx + 0.03664098121225834, miny + 0.02083779126405716, minz + 0.01156378909945488),
                    (maxx - 0.03359369467943907, miny + 0.020909443497657776, minz + 0.012255258858203888),
                    (minx + 0.01420576497912407, miny + 0.023059040307998657, minz + 0.03400459885597229),
                    (maxx - 0.022325390949845314, miny + 0.023111969232559204, maxz - 0.021023839712142944),
                    (maxx - 0.013754449784755707, miny + 0.02322402596473694, maxz - 0.034551107324659824),
                    (minx + 0.034504144452512264, miny + 0.022939488291740417, maxz - 0.014253776520490646),
                    (maxx - 0.020525267347693443, miny + 0.023357778787612915, minz + 0.02227850630879402),
                    (minx + 0.022776709869503975, miny + 0.023171141743659973, minz + 0.020477334037423134),
                    (maxx - 0.036511816550046206, miny + 0.023007795214653015, maxz - 0.013594510033726692),
                    (minx + 0.020976610481739044, miny + 0.02292531728744507, maxz - 0.02282501384615898),
                    (maxx - 0.013095550239086151, miny + 0.02331402897834778, minz + 0.03646504878997803),
                    (minx + 0.013546885922551155, miny + 0.0229690819978714, maxz - 0.037011553067713976),
                    (minx + 0.03696316387504339, miny + 0.023275285959243774, minz + 0.013047976419329643),
                    (maxx - 0.03405279852449894, miny + 0.023343607783317566, minz + 0.013707255944609642)]

        # Faces
        myfaces = [(24, 0, 1), (24, 1, 2), (24, 2, 3), (24, 3, 4), (24, 4, 5),
                   (24, 5, 6), (24, 6, 7), (24, 7, 8), (24, 8, 9), (24, 9, 10),
                   (24, 10, 11), (11, 0, 24), (140, 12, 13, 142), (142, 13, 14, 143), (143, 14, 15, 141),
                   (141, 15, 16, 139), (139, 16, 17, 145), (145, 17, 18, 144), (144, 18, 19, 148), (148, 19, 20, 147),
                   (147, 20, 21, 150), (150, 21, 22, 146), (146, 22, 23, 149), (140, 0, 11, 149), (13, 12, 25, 26),
                   (14, 13, 26, 27), (15, 14, 27, 28), (16, 15, 28, 29), (17, 16, 29, 30), (18, 17, 30, 31),
                   (19, 18, 31, 32), (20, 19, 32, 33), (21, 20, 33, 34), (22, 21, 34, 35), (23, 22, 35, 36),
                   (12, 23, 36, 25), (25, 49, 50, 26), (49, 37, 38, 50), (26, 50, 51, 27), (50, 38, 39, 51),
                   (27, 51, 52, 28), (51, 39, 40, 52), (28, 52, 53, 29), (52, 40, 41, 53), (29, 53, 54, 30),
                   (53, 41, 42, 54), (30, 54, 55, 31), (54, 42, 43, 55), (31, 55, 56, 32), (55, 43, 44, 56),
                   (32, 56, 57, 33), (56, 44, 45, 57), (33, 57, 58, 34), (57, 45, 46, 58), (34, 58, 59, 35),
                   (58, 46, 47, 59), (35, 59, 60, 36), (59, 47, 48, 60), (36, 60, 49, 25), (60, 48, 37, 49),
                   (38, 37, 61, 62), (39, 38, 62, 63), (40, 39, 63, 64), (41, 40, 64, 65), (42, 41, 65, 66),
                   (43, 42, 66, 67), (44, 43, 67, 68), (45, 44, 68, 69), (46, 45, 69, 70), (47, 46, 70, 71),
                   (48, 47, 71, 72), (37, 48, 72, 61), (124, 125, 74, 75), (171, 170, 85, 86), (173, 172, 90, 91),
                   (174, 173, 91, 92), (176, 175, 88, 89), (178, 177, 93, 94), (175, 179, 87, 88), (177, 174, 92, 93),
                   (170, 180, 96, 85), (180, 181, 95, 96), (181, 178, 94, 95), (172, 176, 89, 90), (179, 171, 86, 87),
                   (90, 89, 101, 102), (86, 85, 97, 98), (93, 92, 104, 105), (96, 95, 107, 108), (85, 96, 108, 97),
                   (89, 88, 100, 101), (91, 90, 102, 103), (88, 87, 99, 100), (92, 91, 103, 104), (95, 94, 106, 107),
                   (94, 93, 105, 106), (87, 86, 98, 99), (105, 104, 116, 117), (108, 107, 119, 120), (97, 108, 120, 109),
                   (101, 100, 112, 113), (103, 102, 114, 115), (100, 99, 111, 112), (104, 103, 115, 116),
                   (107, 106, 118, 119),
                   (106, 105, 117, 118), (99, 98, 110, 111), (102, 101, 113, 114), (98, 97, 109, 110), (120, 119, 121),
                   (109, 120, 121), (113, 112, 121), (115, 114, 121), (112, 111, 121), (116, 115, 121),
                   (119, 118, 121), (118, 117, 121), (111, 110, 121), (114, 113, 121), (110, 109, 121),
                   (117, 116, 121), (169, 158, 62, 61), (158, 159, 63, 62), (159, 160, 64, 63), (160, 161, 65, 64),
                   (161, 162, 66, 65), (162, 163, 67, 66), (163, 164, 68, 67), (164, 165, 69, 68), (165, 166, 70, 69),
                   (166, 167, 71, 70), (167, 168, 72, 71), (168, 169, 61, 72), (72, 138, 127, 61), (63, 129, 130, 64),
                   (67, 133, 134, 68), (64, 130, 131, 65), (61, 127, 128, 62), (69, 135, 136, 70), (66, 132, 133, 67),
                   (65, 131, 132, 66), (71, 137, 138, 72), (70, 136, 137, 71), (62, 128, 129, 63), (68, 134, 135, 69),
                   (0, 140, 142, 1), (1, 142, 143, 2), (2, 143, 141, 3), (3, 141, 139, 4), (4, 139, 145, 5),
                   (5, 145, 144, 6), (6, 144, 148, 7), (7, 148, 147, 8), (8, 147, 150, 9), (9, 150, 146, 10),
                   (10, 146, 149, 11), (12, 140, 149, 23), (153, 154, 163, 162), (154, 155, 164, 163), (155, 156, 165, 164),
                   (125, 151, 73, 74), (152, 124, 75, 76), (122, 152, 76, 77), (153, 122, 77, 78), (154, 153, 78, 79),
                   (155, 154, 79, 80), (156, 155, 80, 81), (123, 156, 81, 82), (157, 123, 82, 83), (126, 157, 83, 84),
                   (73, 151, 126, 84), (151, 125, 158, 169), (125, 124, 159, 158), (124, 152, 160, 159),
                   (152, 122, 161, 160),
                   (122, 153, 162, 161), (156, 123, 166, 165), (123, 157, 167, 166), (157, 126, 168, 167),
                   (126, 151, 169, 168),
                   (185, 189, 213, 209), (192, 193, 217, 216), (172, 173, 197, 196), (174, 177, 201, 198),
                   (171, 179, 203, 195),
                   (184, 183, 207, 208), (187, 192, 216, 211), (170, 171, 195, 194), (179, 175, 199, 203),
                   (176, 172, 196, 200),
                   (183, 188, 212, 207), (190, 184, 208, 214), (74, 73, 187, 182), (79, 78, 188, 183), (80, 79, 183, 184),
                   (77, 76, 189, 185), (82, 81, 190, 186), (76, 75, 191, 189), (81, 80, 184, 190), (73, 84, 192, 187),
                   (84, 83, 193, 192), (83, 82, 186, 193), (78, 77, 185, 188), (75, 74, 182, 191), (206, 211, 194, 195),
                   (207, 212, 196, 197), (208, 207, 197, 198), (209, 213, 199, 200), (210, 214, 201, 202),
                   (213, 215, 203, 199),
                   (214, 208, 198, 201), (211, 216, 204, 194), (216, 217, 205, 204), (217, 210, 202, 205),
                   (212, 209, 200, 196),
                   (215, 206, 195, 203), (180, 170, 194, 204), (173, 174, 198, 197), (193, 186, 210, 217),
                   (186, 190, 214, 210),
                   (181, 180, 204, 205), (175, 176, 200, 199), (188, 185, 209, 212), (189, 191, 215, 213),
                   (182, 187, 211, 206),
                   (178, 181, 205, 202), (177, 178, 202, 201), (191, 182, 206, 215)]

        return myvertex, myfaces


    # ----------------------------------------------
    # Handle model 04
    # ----------------------------------------------
    def handle_model_04(self):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.04349547624588013
        maxx = 0.04352114722132683
        miny = -0.07034946978092194
        maxy = 0
        minz = -0.12514087557792664
        maxz = 0.12514087557792664

        # Vertex
        myvertex = [(minx + 0.013302795588970184, maxy - 0.002780601382255554, minz + 0.010707870125770569),
                    (minx + 0.0009496212005615234, maxy - 0.002942140679806471, minz + 0.030204586684703827),
                    (minx, maxy - 0.003071820829063654, minz + 0.053266048431396484),
                    (minx + 0.010708402842283249, maxy - 0.0031348932534456253, minz + 0.07371294498443604),
                    (minx + 0.03020550962537527, maxy - 0.003114458406344056, minz + 0.08606655150651932),
                    (maxx - 0.03374953381717205, maxy - 0.003015991533175111, minz + 0.08701672777533531),
                    (maxx - 0.01330280676484108, maxy - 0.0028658765368163586, minz + 0.07630888000130653),
                    (maxx - 0.0009496286511421204, maxy - 0.0027043374720960855, minz + 0.056812167167663574),
                    (maxx, maxy - 0.0025746573228389025, minz + 0.033750712871551514),
                    (maxx - 0.010708380490541458, maxy - 0.002511584199965, minz + 0.013303808867931366),
                    (maxx - 0.03020548354834318, maxy - 0.0025320190470665693, minz + 0.0009501948952674866),
                    (minx + 0.03374955803155899, maxy - 0.0026304861530661583, minz),
                    (minx + 0.014472760260105133, maxy - 0.019589224830269814, minz + 0.01180487871170044),
                    (minx + 0.002567145973443985, maxy - 0.019744910299777985, minz + 0.03059517592191696),
                    (minx + 0.001651916652917862, maxy - 0.019869891926646233, minz + 0.052821069955825806),
                    (minx + 0.011972300708293915, maxy - 0.019930677488446236, minz + 0.07252714410424232),
                    (minx + 0.03076297417283058, maxy - 0.019910985603928566, minz + 0.0844331718981266),
                    (maxx - 0.034027633257210255, maxy - 0.019816085696220398, minz + 0.0853489525616169),
                    (maxx - 0.014321718364953995, maxy - 0.01967141032218933, minz + 0.07502909749746323),
                    (maxx - 0.002416089177131653, maxy - 0.01951572299003601, minz + 0.056238800287246704),
                    (maxx - 0.0015008561313152313, maxy - 0.019390743225812912, minz + 0.03401290625333786),
                    (maxx - 0.011821221560239792, maxy - 0.01932995393872261, minz + 0.014306828379631042),
                    (maxx - 0.03061189129948616, maxy - 0.01934964768588543, minz + 0.0024007856845855713),
                    (minx + 0.03417872078716755, maxy - 0.019444547593593597, minz + 0.001484982669353485),
                    (minx + 0.043508310547622386, maxy - 0.005668943747878075, minz + 0.043508365750312805),
                    (minx + 0.029034355655312538, maxy - 0.019612153992056847, minz + 0.027617476880550385),
                    (minx + 0.023084014654159546, maxy - 0.01968996599316597, minz + 0.037008725106716156),
                    (minx + 0.022626593708992004, maxy - 0.01975242979824543, minz + 0.048117056488990784),
                    (minx + 0.027784643694758415, maxy - 0.019782811403274536, minz + 0.05796600878238678),
                    (minx + 0.03717608004808426, maxy - 0.019772969186306, minz + 0.06391655653715134),
                    (maxx - 0.03873214777559042, maxy - 0.019725536927580833, minz + 0.06437425315380096),
                    (maxx - 0.02888327743858099, maxy - 0.019653232768177986, minz + 0.059216469526290894),
                    (maxx - 0.022932931780815125, maxy - 0.019575420767068863, minz + 0.04982522130012512),
                    (maxx - 0.022475499659776688, maxy - 0.019512956961989403, minz + 0.0387168824672699),
                    (maxx - 0.0276335496455431, maxy - 0.019482573494315147, minz + 0.0288679301738739),
                    (maxx - 0.03702498506754637, maxy - 0.019492419436573982, minz + 0.022917382419109344),
                    (minx + 0.038883245550096035, maxy - 0.0195398461073637, minz + 0.022459670901298523),
                    (minx + 0.029087782837450504, maxy - 0.03150090575218201, minz + 0.027552828192710876),
                    (minx + 0.023137442767620087, maxy - 0.03157871589064598, minz + 0.03694407641887665),
                    (minx + 0.022680018097162247, maxy - 0.03164118155837059, minz + 0.04805241525173187),
                    (minx + 0.027838071808218956, maxy - 0.031671565026044846, minz + 0.05790136009454727),
                    (minx + 0.0372295081615448, maxy - 0.03166172280907631, minz + 0.06385190784931183),
                    (maxx - 0.03867871919646859, maxy - 0.03161429241299629, minz + 0.06430960446596146),
                    (maxx - 0.028829848393797874, maxy - 0.03154198080301285, minz + 0.05915181338787079),
                    (maxx - 0.022879503667354584, maxy - 0.031464170664548874, minz + 0.04976056516170502),
                    (maxx - 0.022422071546316147, maxy - 0.03140170872211456, minz + 0.03865223377943039),
                    (maxx - 0.02758011966943741, maxy - 0.03137132152915001, minz + 0.028803281486034393),
                    (maxx - 0.03697155695408583, maxy - 0.031381167471408844, minz + 0.022852733731269836),
                    (minx + 0.038936673663556576, maxy - 0.03142859786748886, minz + 0.022395022213459015),
                    (minx + 0.029038896784186363, maxy - 0.020622700452804565, minz + 0.027611978352069855),
                    (minx + 0.02308855764567852, maxy - 0.02070051059126854, minz + 0.03700323402881622),
                    (minx + 0.02263113297522068, maxy - 0.020762978121638298, minz + 0.04811156541109085),
                    (minx + 0.02778918668627739, maxy - 0.020793357864022255, minz + 0.05796051025390625),
                    (minx + 0.037180622573941946, maxy - 0.02078351564705372, minz + 0.0639110580086708),
                    (maxx - 0.03872760524973273, maxy - 0.020736083388328552, minz + 0.06436875835061073),
                    (maxx - 0.028878736309707165, maxy - 0.020663777366280556, minz + 0.059210970997810364),
                    (maxx - 0.02292838878929615, maxy - 0.020585965365171432, minz + 0.04981972277164459),
                    (maxx - 0.022470960393548012, maxy - 0.020523501560091972, minz + 0.038711391389369965),
                    (maxx - 0.027629008516669273, maxy - 0.020493119955062866, minz + 0.02886243909597397),
                    (maxx - 0.03702044300734997, maxy - 0.020502964034676552, minz + 0.022911883890628815),
                    (minx + 0.03888778714463115, maxy - 0.02055039070546627, minz + 0.022454172372817993),
                    (minx + 0.03503026906400919, maxy - 0.0326739065349102, minz + 0.03399384766817093),
                    (minx + 0.03150810860097408, maxy - 0.032719966024160385, minz + 0.039552778005599976),
                    (minx + 0.03123734798282385, maxy - 0.03275693953037262, minz + 0.04612809419631958),
                    (minx + 0.034290531650185585, maxy - 0.032774921506643295, minz + 0.051957935094833374),
                    (minx + 0.039849569322541356, maxy - 0.0327690951526165, minz + 0.0554802268743515),
                    (maxx - 0.04059170465916395, maxy - 0.03274102136492729, minz + 0.055751144886016846),
                    (maxx - 0.03476190101355314, maxy - 0.032698217779397964, minz + 0.05269812047481537),
                    (maxx - 0.031239738687872887, maxy - 0.03265216201543808, minz + 0.04713919758796692),
                    (maxx - 0.03096897155046463, maxy - 0.032615188509225845, minz + 0.040563881397247314),
                    (maxx - 0.03402215428650379, maxy - 0.03259720280766487, minz + 0.03473402559757233),
                    (maxx - 0.03958118986338377, maxy - 0.032603029161691666, minz + 0.031211741268634796),
                    (minx + 0.04086008481681347, maxy - 0.032631102949380875, minz + 0.030940808355808258),
                    (minx + 0.03971285093575716, miny + 0.029022332280874252, minz + 0.05597035586833954),
                    (maxx - 0.03359287604689598, miny + 0.029201623052358627, minz + 0.034330859780311584),
                    (minx + 0.03072980046272278, miny + 0.029035013169050217, minz + 0.04621553421020508),
                    (minx + 0.031012218445539474, miny + 0.029073577374219894, minz + 0.03935709595680237),
                    (minx + 0.04076687735505402, miny + 0.029166262596845627, minz + 0.03037431836128235),
                    (minx + 0.034451283514499664, maxy - 0.03338594362139702, minz + 0.033365122973918915),
                    (minx + 0.030692334286868572, maxy - 0.03343509882688522, minz + 0.039297766983509064),
                    (minx + 0.03040337096899748, maxy - 0.03347455710172653, minz + 0.04631512612104416),
                    (minx + 0.03366181440651417, maxy - 0.03349374979734421, minz + 0.05253690481185913),
                    (minx + 0.03959457715973258, maxy - 0.033487528562545776, minz + 0.05629599094390869),
                    (maxx - 0.040404647355899215, maxy - 0.033457569777965546, minz + 0.056585125625133514),
                    (maxx - 0.03418291546404362, maxy - 0.03341188654303551, minz + 0.05332684516906738),
                    (maxx - 0.030423964373767376, maxy - 0.0333627350628376, minz + 0.047394201159477234),
                    (maxx - 0.030134993605315685, maxy - 0.03332327678799629, minz + 0.04037684202194214),
                    (maxx - 0.033393437042832375, maxy - 0.03330408036708832, minz + 0.03415506333112717),
                    (maxx - 0.03932619746774435, maxy - 0.03331030160188675, minz + 0.030395977199077606),
                    (minx + 0.040673027746379375, maxy - 0.03334026038646698, minz + 0.030106835067272186),
                    (minx + 0.030282274819910526, maxy - 0.005427400581538677, minz + 0.08584162965416908),
                    (minx + 0.013463903218507767, maxy - 0.005095209460705519, minz + 0.0108589306473732),
                    (minx + 0.010882444679737091, maxy - 0.005447734147310257, minz + 0.07354965433478355),
                    (minx + 0.0011723600327968597, maxy - 0.005255943164229393, minz + 0.03025837242603302),
                    (minx + 0.0002274736762046814, maxy - 0.005384976044297218, minz + 0.05320477485656738),
                    (maxx - 0.0134431142359972, maxy - 0.005180059932172298, minz + 0.0761326476931572),
                    (maxx - 0.033787828870117664, maxy - 0.005329424981027842, minz + 0.08678706735372543),
                    (maxx - 0.0302614476531744, maxy - 0.004847868345677853, minz + 0.0011499449610710144),
                    (maxx - 0.00020667165517807007, maxy - 0.004890293348580599, minz + 0.03378681838512421),
                    (maxx - 0.0011515654623508453, maxy - 0.0050193266943097115, minz + 0.05673321336507797),
                    (minx + 0.033808655105531216, maxy - 0.004945843946188688, minz + 0.0002044886350631714),
                    (maxx - 0.010861624032258987, maxy - 0.004827534779906273, minz + 0.01344192773103714),
                    (minx + 0.03468604106456041, miny + 0.029121622443199158, minz + 0.033558815717697144),
                    (minx + 0.033914451487362385, miny + 0.02901625633239746, minz + 0.05229640752077103),
                    (maxx - 0.04044530005194247, miny + 0.029051613062620163, minz + 0.056252941489219666),
                    (maxx - 0.034364476799964905, miny + 0.02909626066684723, minz + 0.053068459033966064),
                    (maxx - 0.03069065511226654, miny + 0.029144294559955597, minz + 0.04727017134428024),
                    (maxx - 0.030408228747546673, miny + 0.029182862490415573, minz + 0.04041174054145813),
                    (maxx - 0.03939127502962947, miny + 0.029195547103881836, minz + 0.030656911432743073),
                    (minx + 0.03147818427532911, maxy - 0.033236272633075714, minz + 0.03954096883535385),
                    (minx + 0.031206720508635044, maxy - 0.03327333927154541, minz + 0.0461333692073822),
                    (minx + 0.034267837181687355, maxy - 0.033291369676589966, minz + 0.05197836458683014),
                    (minx + 0.03984131896868348, maxy - 0.03328552842140198, minz + 0.05550979822874069),
                    (maxx - 0.040582869900390506, maxy - 0.0332573801279068, minz + 0.055781424045562744),
                    (maxx - 0.03473791852593422, maxy - 0.033214468508958817, minz + 0.05272047221660614),
                    (maxx - 0.031206604093313217, maxy - 0.03316829353570938, minz + 0.04714709520339966),
                    (maxx - 0.030935133807361126, maxy - 0.03313122317194939, minz + 0.040554702281951904),
                    (maxx - 0.03399624954909086, maxy - 0.03311318904161453, minz + 0.03470969945192337),
                    (maxx - 0.03956972947344184, maxy - 0.03311903029680252, minz + 0.03117825835943222),
                    (minx + 0.04085446032695472, maxy - 0.0331471785902977, minz + 0.03090662509202957),
                    (minx + 0.035009496845304966, maxy - 0.03319009393453598, minz + 0.033967599272727966),
                    (maxx - 0.03939127502962947, miny + 0.0002205297350883484, minz + 0.0343027338385582),
                    (maxx - 0.030408228747546673, miny + 0.007109262049198151, minz + 0.04120940715074539),
                    (maxx - 0.03069065511226654, miny + 0.011931635439395905, minz + 0.046086326241493225),
                    (maxx - 0.034364476799964905, miny + 0.01599767804145813, minz + 0.050220295786857605),
                    (maxx - 0.04044530005194247, miny + 0.01821787655353546, minz + 0.05250363051891327),
                    (minx + 0.033914451487362385, miny + 0.015395186841487885, minz + 0.04973094165325165),
                    (minx + 0.03468604106456041, miny + 0.0022202134132385254, minz + 0.03640696406364441),
                    (minx + 0.04076687735505402, miny, minz + 0.03412361443042755),
                    (minx + 0.031012218445539474, miny + 0.006286241114139557, minz + 0.040540941059589386),
                    (minx + 0.03072980046272278, miny + 0.011108621954917908, minz + 0.04541786015033722),
                    (maxx - 0.03359287604689598, miny + 0.002822697162628174, minz + 0.036896318197250366),
                    (minx + 0.03971285093575716, miny + 0.01799735426902771, minz + 0.05232451856136322),
                    (minx + 0.0343002462759614, miny + 0.015705399215221405, maxz - 0.10733164101839066),
                    (minx + 0.030871009454131126, miny + 0.011495128273963928, maxz - 0.10745517536997795),
                    (minx + 0.030871009454131126, miny + 0.006645478308200836, maxz - 0.1074824407696724),
                    (minx + 0.0343002462759614, miny + 0.0024559199810028076, maxz - 0.10740615427494049),
                    (minx + 0.04023986402899027, miny + 4.902482032775879e-05, maxz - 0.10724674165248871),
                    (maxx - 0.03991828765720129, miny + 6.973743438720703e-05, maxz - 0.10704692453145981),
                    (maxx - 0.03397867642343044, miny + 0.0025124847888946533, maxz - 0.10686022788286209),
                    (maxx - 0.030549442395567894, miny + 0.00672275573015213, maxz - 0.1067366972565651),
                    (maxx - 0.030549442395567894, miny + 0.011572405695915222, maxz - 0.10670943185687065),
                    (maxx - 0.03397867642343044, miny + 0.015761971473693848, maxz - 0.10678572952747345),
                    (maxx - 0.03991828765720129, miny + 0.0181688591837883, maxz - 0.10694513842463493),
                    (minx + 0.04023986402899027, miny + 0.018148154020309448, maxz - 0.10714496672153473),
                    (minx + 0.013302795588970184, maxy - 0.002780601382255554, maxz - 0.010707870125770569),
                    (minx + 0.0009496212005615234, maxy - 0.002942140679806471, maxz - 0.030204586684703827),
                    (minx, maxy - 0.003071820829063654, maxz - 0.053266048431396484),
                    (minx + 0.010708402842283249, maxy - 0.0031348932534456253, maxz - 0.07371294498443604),
                    (minx + 0.03020550962537527, maxy - 0.003114458406344056, maxz - 0.08606655150651932),
                    (maxx - 0.03374953381717205, maxy - 0.003015991533175111, maxz - 0.08701672777533531),
                    (maxx - 0.01330280676484108, maxy - 0.0028658765368163586, maxz - 0.07630888000130653),
                    (maxx - 0.0009496286511421204, maxy - 0.0027043374720960855, maxz - 0.056812167167663574),
                    (maxx, maxy - 0.0025746573228389025, maxz - 0.033750712871551514),
                    (maxx - 0.010708380490541458, maxy - 0.002511584199965, maxz - 0.013303808867931366),
                    (maxx - 0.03020548354834318, maxy - 0.0025320190470665693, maxz - 0.0009501948952674866),
                    (minx + 0.03374955803155899, maxy - 0.0026304861530661583, maxz),
                    (minx + 0.014472760260105133, maxy - 0.019589224830269814, maxz - 0.01180487871170044),
                    (minx + 0.002567145973443985, maxy - 0.019744910299777985, maxz - 0.03059517592191696),
                    (minx + 0.001651916652917862, maxy - 0.019869891926646233, maxz - 0.052821069955825806),
                    (minx + 0.011972300708293915, maxy - 0.019930677488446236, maxz - 0.07252714410424232),
                    (minx + 0.03076297417283058, maxy - 0.019910985603928566, maxz - 0.0844331718981266),
                    (maxx - 0.034027633257210255, maxy - 0.019816085696220398, maxz - 0.0853489525616169),
                    (maxx - 0.014321718364953995, maxy - 0.01967141032218933, maxz - 0.07502909749746323),
                    (maxx - 0.002416089177131653, maxy - 0.01951572299003601, maxz - 0.056238800287246704),
                    (maxx - 0.0015008561313152313, maxy - 0.019390743225812912, maxz - 0.03401290625333786),
                    (maxx - 0.011821221560239792, maxy - 0.01932995393872261, maxz - 0.014306828379631042),
                    (maxx - 0.03061189129948616, maxy - 0.01934964768588543, maxz - 0.0024007856845855713),
                    (minx + 0.03417872078716755, maxy - 0.019444547593593597, maxz - 0.001484982669353485),
                    (minx + 0.043508310547622386, maxy - 0.005668943747878075, maxz - 0.043508365750312805),
                    (minx + 0.029034355655312538, maxy - 0.019612153992056847, maxz - 0.027617476880550385),
                    (minx + 0.023084014654159546, maxy - 0.01968996599316597, maxz - 0.037008725106716156),
                    (minx + 0.022626593708992004, maxy - 0.01975242979824543, maxz - 0.048117056488990784),
                    (minx + 0.027784643694758415, maxy - 0.019782811403274536, maxz - 0.05796600878238678),
                    (minx + 0.03717608004808426, maxy - 0.019772969186306, maxz - 0.06391655653715134),
                    (maxx - 0.03873214777559042, maxy - 0.019725536927580833, maxz - 0.06437425315380096),
                    (maxx - 0.02888327743858099, maxy - 0.019653232768177986, maxz - 0.059216469526290894),
                    (maxx - 0.022932931780815125, maxy - 0.019575420767068863, maxz - 0.04982522130012512),
                    (maxx - 0.022475499659776688, maxy - 0.019512956961989403, maxz - 0.0387168824672699),
                    (maxx - 0.0276335496455431, maxy - 0.019482573494315147, maxz - 0.0288679301738739),
                    (maxx - 0.03702498506754637, maxy - 0.019492419436573982, maxz - 0.022917382419109344),
                    (minx + 0.038883245550096035, maxy - 0.0195398461073637, maxz - 0.022459670901298523),
                    (minx + 0.029087782837450504, maxy - 0.03150090575218201, maxz - 0.027552828192710876),
                    (minx + 0.023137442767620087, maxy - 0.03157871589064598, maxz - 0.03694407641887665),
                    (minx + 0.022680018097162247, maxy - 0.03164118155837059, maxz - 0.04805241525173187),
                    (minx + 0.027838071808218956, maxy - 0.031671565026044846, maxz - 0.05790136009454727),
                    (minx + 0.0372295081615448, maxy - 0.03166172280907631, maxz - 0.06385190784931183),
                    (maxx - 0.03867871919646859, maxy - 0.03161429241299629, maxz - 0.06430960446596146),
                    (maxx - 0.028829848393797874, maxy - 0.03154198080301285, maxz - 0.05915181338787079),
                    (maxx - 0.022879503667354584, maxy - 0.031464170664548874, maxz - 0.04976056516170502),
                    (maxx - 0.022422071546316147, maxy - 0.03140170872211456, maxz - 0.03865223377943039),
                    (maxx - 0.02758011966943741, maxy - 0.03137132152915001, maxz - 0.028803281486034393),
                    (maxx - 0.03697155695408583, maxy - 0.031381167471408844, maxz - 0.022852733731269836),
                    (minx + 0.038936673663556576, maxy - 0.03142859786748886, maxz - 0.022395022213459015),
                    (minx + 0.029038896784186363, maxy - 0.020622700452804565, maxz - 0.027611978352069855),
                    (minx + 0.02308855764567852, maxy - 0.02070051059126854, maxz - 0.03700323402881622),
                    (minx + 0.02263113297522068, maxy - 0.020762978121638298, maxz - 0.04811156541109085),
                    (minx + 0.02778918668627739, maxy - 0.020793357864022255, maxz - 0.05796051025390625),
                    (minx + 0.037180622573941946, maxy - 0.02078351564705372, maxz - 0.0639110580086708),
                    (maxx - 0.03872760524973273, maxy - 0.020736083388328552, maxz - 0.06436875835061073),
                    (maxx - 0.028878736309707165, maxy - 0.020663777366280556, maxz - 0.059210970997810364),
                    (maxx - 0.02292838878929615, maxy - 0.020585965365171432, maxz - 0.04981972277164459),
                    (maxx - 0.022470960393548012, maxy - 0.020523501560091972, maxz - 0.038711391389369965),
                    (maxx - 0.027629008516669273, maxy - 0.020493119955062866, maxz - 0.02886243909597397),
                    (maxx - 0.03702044300734997, maxy - 0.020502964034676552, maxz - 0.022911883890628815),
                    (minx + 0.03888778714463115, maxy - 0.02055039070546627, maxz - 0.022454172372817993),
                    (minx + 0.03503026906400919, maxy - 0.0326739065349102, maxz - 0.03399384766817093),
                    (minx + 0.03150810860097408, maxy - 0.032719966024160385, maxz - 0.039552778005599976),
                    (minx + 0.03123734798282385, maxy - 0.03275693953037262, maxz - 0.04612809419631958),
                    (minx + 0.034290531650185585, maxy - 0.032774921506643295, maxz - 0.051957935094833374),
                    (minx + 0.039849569322541356, maxy - 0.0327690951526165, maxz - 0.0554802268743515),
                    (maxx - 0.04059170465916395, maxy - 0.03274102136492729, maxz - 0.055751144886016846),
                    (maxx - 0.03476190101355314, maxy - 0.032698217779397964, maxz - 0.05269812047481537),
                    (maxx - 0.031239738687872887, maxy - 0.03265216201543808, maxz - 0.04713919758796692),
                    (maxx - 0.03096897155046463, maxy - 0.032615188509225845, maxz - 0.040563881397247314),
                    (maxx - 0.03402215428650379, maxy - 0.03259720280766487, maxz - 0.03473402559757233),
                    (maxx - 0.03958118986338377, maxy - 0.032603029161691666, maxz - 0.031211741268634796),
                    (minx + 0.04086008481681347, maxy - 0.032631102949380875, maxz - 0.030940808355808258),
                    (minx + 0.03971285093575716, miny + 0.029022332280874252, maxz - 0.05597035586833954),
                    (maxx - 0.03359287604689598, miny + 0.029201623052358627, maxz - 0.034330859780311584),
                    (minx + 0.03072980046272278, miny + 0.029035013169050217, maxz - 0.04621553421020508),
                    (minx + 0.031012218445539474, miny + 0.029073577374219894, maxz - 0.03935709595680237),
                    (minx + 0.04076687735505402, miny + 0.029166262596845627, maxz - 0.03037431836128235),
                    (minx + 0.034451283514499664, maxy - 0.03338594362139702, maxz - 0.033365122973918915),
                    (minx + 0.030692334286868572, maxy - 0.03343509882688522, maxz - 0.039297766983509064),
                    (minx + 0.03040337096899748, maxy - 0.03347455710172653, maxz - 0.04631512612104416),
                    (minx + 0.03366181440651417, maxy - 0.03349374979734421, maxz - 0.05253690481185913),
                    (minx + 0.03959457715973258, maxy - 0.033487528562545776, maxz - 0.05629599094390869),
                    (maxx - 0.040404647355899215, maxy - 0.033457569777965546, maxz - 0.056585125625133514),
                    (maxx - 0.03418291546404362, maxy - 0.03341188654303551, maxz - 0.05332684516906738),
                    (maxx - 0.030423964373767376, maxy - 0.0333627350628376, maxz - 0.047394201159477234),
                    (maxx - 0.030134993605315685, maxy - 0.03332327678799629, maxz - 0.04037684202194214),
                    (maxx - 0.033393437042832375, maxy - 0.03330408036708832, maxz - 0.03415506333112717),
                    (maxx - 0.03932619746774435, maxy - 0.03331030160188675, maxz - 0.030395977199077606),
                    (minx + 0.040673027746379375, maxy - 0.03334026038646698, maxz - 0.030106835067272186),
                    (minx + 0.030282274819910526, maxy - 0.005427400581538677, maxz - 0.08584162965416908),
                    (minx + 0.013463903218507767, maxy - 0.005095209460705519, maxz - 0.0108589306473732),
                    (minx + 0.010882444679737091, maxy - 0.005447734147310257, maxz - 0.07354965433478355),
                    (minx + 0.0011723600327968597, maxy - 0.005255943164229393, maxz - 0.03025837242603302),
                    (minx + 0.0002274736762046814, maxy - 0.005384976044297218, maxz - 0.05320477485656738),
                    (maxx - 0.0134431142359972, maxy - 0.005180059932172298, maxz - 0.0761326476931572),
                    (maxx - 0.033787828870117664, maxy - 0.005329424981027842, maxz - 0.08678706735372543),
                    (maxx - 0.0302614476531744, maxy - 0.004847868345677853, maxz - 0.0011499449610710144),
                    (maxx - 0.00020667165517807007, maxy - 0.004890293348580599, maxz - 0.03378681838512421),
                    (maxx - 0.0011515654623508453, maxy - 0.0050193266943097115, maxz - 0.05673321336507797),
                    (minx + 0.033808655105531216, maxy - 0.004945843946188688, maxz - 0.0002044886350631714),
                    (maxx - 0.010861624032258987, maxy - 0.004827534779906273, maxz - 0.01344192773103714),
                    (minx + 0.03468604106456041, miny + 0.029121622443199158, maxz - 0.033558815717697144),
                    (minx + 0.033914451487362385, miny + 0.02901625633239746, maxz - 0.05229640752077103),
                    (maxx - 0.04044530005194247, miny + 0.029051613062620163, maxz - 0.056252941489219666),
                    (maxx - 0.034364476799964905, miny + 0.02909626066684723, maxz - 0.053068459033966064),
                    (maxx - 0.03069065511226654, miny + 0.029144294559955597, maxz - 0.04727017134428024),
                    (maxx - 0.030408228747546673, miny + 0.029182862490415573, maxz - 0.04041174054145813),
                    (maxx - 0.03939127502962947, miny + 0.029195547103881836, maxz - 0.030656911432743073),
                    (minx + 0.03147818427532911, maxy - 0.033236272633075714, maxz - 0.03954096883535385),
                    (minx + 0.031206720508635044, maxy - 0.03327333927154541, maxz - 0.0461333692073822),
                    (minx + 0.034267837181687355, maxy - 0.033291369676589966, maxz - 0.05197836458683014),
                    (minx + 0.03984131896868348, maxy - 0.03328552842140198, maxz - 0.05550979822874069),
                    (maxx - 0.040582869900390506, maxy - 0.0332573801279068, maxz - 0.055781424045562744),
                    (maxx - 0.03473791852593422, maxy - 0.033214468508958817, maxz - 0.05272047221660614),
                    (maxx - 0.031206604093313217, maxy - 0.03316829353570938, maxz - 0.04714709520339966),
                    (maxx - 0.030935133807361126, maxy - 0.03313122317194939, maxz - 0.040554702281951904),
                    (maxx - 0.03399624954909086, maxy - 0.03311318904161453, maxz - 0.03470969945192337),
                    (maxx - 0.03956972947344184, maxy - 0.03311903029680252, maxz - 0.03117825835943222),
                    (minx + 0.04085446032695472, maxy - 0.0331471785902977, maxz - 0.03090662509202957),
                    (minx + 0.035009496845304966, maxy - 0.03319009393453598, maxz - 0.033967599272727966),
                    (maxx - 0.03939127502962947, miny + 0.0002205297350883484, maxz - 0.0343027338385582),
                    (maxx - 0.030408228747546673, miny + 0.007109262049198151, maxz - 0.04120940715074539),
                    (maxx - 0.03069065511226654, miny + 0.011931635439395905, maxz - 0.046086326241493225),
                    (maxx - 0.034364476799964905, miny + 0.01599767804145813, maxz - 0.050220295786857605),
                    (maxx - 0.04044530005194247, miny + 0.01821787655353546, maxz - 0.05250363051891327),
                    (minx + 0.033914451487362385, miny + 0.015395186841487885, maxz - 0.04973094165325165),
                    (minx + 0.03468604106456041, miny + 0.0022202134132385254, maxz - 0.03640696406364441),
                    (minx + 0.04076687735505402, miny, maxz - 0.03412361443042755),
                    (minx + 0.031012218445539474, miny + 0.006286241114139557, maxz - 0.040540941059589386),
                    (minx + 0.03072980046272278, miny + 0.011108621954917908, maxz - 0.04541786015033722),
                    (maxx - 0.03359287604689598, miny + 0.002822697162628174, maxz - 0.036896318197250366),
                    (minx + 0.03971285093575716, miny + 0.01799735426902771, maxz - 0.05232451856136322),
                    (minx + 0.0343002462759614, miny + 0.015705399215221405, minz + 0.10733164101839066),
                    (minx + 0.030871009454131126, miny + 0.011495128273963928, minz + 0.10745517536997795),
                    (minx + 0.030871009454131126, miny + 0.006645478308200836, minz + 0.1074824407696724),
                    (minx + 0.0343002462759614, miny + 0.0024559199810028076, minz + 0.10740615427494049),
                    (minx + 0.04023986402899027, miny + 4.902482032775879e-05, minz + 0.10724674165248871),
                    (maxx - 0.03991828765720129, miny + 6.973743438720703e-05, minz + 0.10704692453145981),
                    (maxx - 0.03397867642343044, miny + 0.0025124847888946533, minz + 0.10686022788286209),
                    (maxx - 0.030549442395567894, miny + 0.00672275573015213, minz + 0.1067366972565651),
                    (maxx - 0.030549442395567894, miny + 0.011572405695915222, minz + 0.10670943185687065),
                    (maxx - 0.03397867642343044, miny + 0.015761971473693848, minz + 0.10678572952747345),
                    (maxx - 0.03991828765720129, miny + 0.0181688591837883, minz + 0.10694513842463493),
                    (minx + 0.04023986402899027, miny + 0.018148154020309448, minz + 0.10714496672153473)]

        # Faces
        myfaces = [(24, 0, 1), (24, 1, 2), (24, 2, 3), (24, 3, 4), (24, 4, 5),
                   (24, 5, 6), (24, 6, 7), (24, 7, 8), (24, 8, 9), (24, 9, 10),
                   (24, 10, 11), (11, 0, 24), (91, 12, 13, 93), (93, 13, 14, 94), (94, 14, 15, 92),
                   (92, 15, 16, 90), (90, 16, 17, 96), (96, 17, 18, 95), (95, 18, 19, 99), (99, 19, 20, 98),
                   (98, 20, 21, 101), (101, 21, 22, 97), (97, 22, 23, 100), (91, 0, 11, 100), (13, 12, 25, 26),
                   (14, 13, 26, 27), (15, 14, 27, 28), (16, 15, 28, 29), (17, 16, 29, 30), (18, 17, 30, 31),
                   (19, 18, 31, 32), (20, 19, 32, 33), (21, 20, 33, 34), (22, 21, 34, 35), (23, 22, 35, 36),
                   (12, 23, 36, 25), (25, 49, 50, 26), (49, 37, 38, 50), (26, 50, 51, 27), (50, 38, 39, 51),
                   (27, 51, 52, 28), (51, 39, 40, 52), (28, 52, 53, 29), (52, 40, 41, 53), (29, 53, 54, 30),
                   (53, 41, 42, 54), (30, 54, 55, 31), (54, 42, 43, 55), (31, 55, 56, 32), (55, 43, 44, 56),
                   (32, 56, 57, 33), (56, 44, 45, 57), (33, 57, 58, 34), (57, 45, 46, 58), (34, 58, 59, 35),
                   (58, 46, 47, 59), (35, 59, 60, 36), (59, 47, 48, 60), (36, 60, 49, 25), (60, 48, 37, 49),
                   (38, 37, 61, 62), (39, 38, 62, 63), (40, 39, 63, 64), (41, 40, 64, 65), (42, 41, 65, 66),
                   (43, 42, 66, 67), (44, 43, 67, 68), (45, 44, 68, 69), (46, 45, 69, 70), (47, 46, 70, 71),
                   (48, 47, 71, 72), (37, 48, 72, 61), (120, 109, 62, 61), (109, 110, 63, 62), (110, 111, 64, 63),
                   (111, 112, 65, 64), (112, 113, 66, 65), (113, 114, 67, 66), (114, 115, 68, 67), (115, 116, 69, 68),
                   (116, 117, 70, 69), (117, 118, 71, 70), (118, 119, 72, 71), (119, 120, 61, 72), (72, 89, 78, 61),
                   (63, 80, 81, 64), (67, 84, 85, 68), (64, 81, 82, 65), (61, 78, 79, 62), (69, 86, 87, 70),
                   (66, 83, 84, 67), (65, 82, 83, 66), (71, 88, 89, 72), (70, 87, 88, 71), (62, 79, 80, 63),
                   (68, 85, 86, 69), (0, 91, 93, 1), (1, 93, 94, 2), (2, 94, 92, 3), (3, 92, 90, 4),
                   (4, 90, 96, 5), (5, 96, 95, 6), (6, 95, 99, 7), (7, 99, 98, 8), (8, 98, 101, 9),
                   (9, 101, 97, 10), (10, 97, 100, 11), (12, 91, 100, 23), (104, 105, 114, 113), (105, 106, 115, 114),
                   (106, 107, 116, 115), (102, 76, 109, 120), (76, 75, 110, 109), (75, 103, 111, 110), (103, 73, 112, 111),
                   (73, 104, 113, 112), (107, 74, 117, 116), (74, 108, 118, 117), (108, 77, 119, 118), (77, 102, 120, 119),
                   (74, 107, 122, 131), (107, 106, 123, 122), (104, 73, 132, 125), (106, 105, 124, 123), (75, 76, 129, 130),
                   (73, 103, 126, 132), (105, 104, 125, 124), (102, 77, 128, 127), (103, 75, 130, 126), (77, 108, 121, 128),
                   (76, 102, 127, 129), (108, 74, 131, 121), (126, 130, 134, 133), (130, 129, 135, 134),
                   (129, 127, 136, 135),
                   (127, 128, 137, 136), (128, 121, 138, 137), (121, 131, 139, 138), (131, 122, 140, 139),
                   (122, 123, 141, 140),
                   (123, 124, 142, 141), (124, 125, 143, 142), (125, 132, 144, 143), (132, 126, 133, 144),
                   (169, 146, 145),
                   (169, 147, 146), (169, 148, 147), (169, 149, 148), (169, 150, 149), (169, 151, 150),
                   (169, 152, 151), (169, 153, 152), (169, 154, 153), (169, 155, 154), (169, 156, 155),
                   (156, 169, 145), (236, 238, 158, 157), (238, 239, 159, 158), (239, 237, 160, 159), (237, 235, 161, 160),
                   (235, 241, 162, 161), (241, 240, 163, 162), (240, 244, 164, 163), (244, 243, 165, 164),
                   (243, 246, 166, 165),
                   (246, 242, 167, 166), (242, 245, 168, 167), (236, 245, 156, 145), (158, 171, 170, 157),
                   (159, 172, 171, 158),
                   (160, 173, 172, 159), (161, 174, 173, 160), (162, 175, 174, 161), (163, 176, 175, 162),
                   (164, 177, 176, 163),
                   (165, 178, 177, 164), (166, 179, 178, 165), (167, 180, 179, 166), (168, 181, 180, 167),
                   (157, 170, 181, 168),
                   (170, 171, 195, 194), (194, 195, 183, 182), (171, 172, 196, 195), (195, 196, 184, 183),
                   (172, 173, 197, 196),
                   (196, 197, 185, 184), (173, 174, 198, 197), (197, 198, 186, 185), (174, 175, 199, 198),
                   (198, 199, 187, 186),
                   (175, 176, 200, 199), (199, 200, 188, 187), (176, 177, 201, 200), (200, 201, 189, 188),
                   (177, 178, 202, 201),
                   (201, 202, 190, 189), (178, 179, 203, 202), (202, 203, 191, 190), (179, 180, 204, 203),
                   (203, 204, 192, 191),
                   (180, 181, 205, 204), (204, 205, 193, 192), (181, 170, 194, 205), (205, 194, 182, 193),
                   (183, 207, 206, 182),
                   (184, 208, 207, 183), (185, 209, 208, 184), (186, 210, 209, 185), (187, 211, 210, 186),
                   (188, 212, 211, 187),
                   (189, 213, 212, 188), (190, 214, 213, 189), (191, 215, 214, 190), (192, 216, 215, 191),
                   (193, 217, 216, 192),
                   (182, 206, 217, 193), (265, 206, 207, 254), (254, 207, 208, 255), (255, 208, 209, 256),
                   (256, 209, 210, 257),
                   (257, 210, 211, 258), (258, 211, 212, 259), (259, 212, 213, 260), (260, 213, 214, 261),
                   (261, 214, 215, 262),
                   (262, 215, 216, 263), (263, 216, 217, 264), (264, 217, 206, 265), (217, 206, 223, 234),
                   (208, 209, 226, 225),
                   (212, 213, 230, 229), (209, 210, 227, 226), (206, 207, 224, 223), (214, 215, 232, 231),
                   (211, 212, 229, 228),
                   (210, 211, 228, 227), (216, 217, 234, 233), (215, 216, 233, 232), (207, 208, 225, 224),
                   (213, 214, 231, 230),
                   (145, 146, 238, 236), (146, 147, 239, 238), (147, 148, 237, 239), (148, 149, 235, 237),
                   (149, 150, 241, 235),
                   (150, 151, 240, 241), (151, 152, 244, 240), (152, 153, 243, 244), (153, 154, 246, 243),
                   (154, 155, 242, 246),
                   (155, 156, 245, 242), (157, 168, 245, 236), (249, 258, 259, 250), (250, 259, 260, 251),
                   (251, 260, 261, 252),
                   (247, 265, 254, 221), (221, 254, 255, 220), (220, 255, 256, 248), (248, 256, 257, 218),
                   (218, 257, 258, 249),
                   (252, 261, 262, 219), (219, 262, 263, 253), (253, 263, 264, 222), (222, 264, 265, 247),
                   (219, 276, 267, 252),
                   (252, 267, 268, 251), (249, 270, 277, 218), (251, 268, 269, 250), (220, 275, 274, 221),
                   (218, 277, 271, 248),
                   (250, 269, 270, 249), (247, 272, 273, 222), (248, 271, 275, 220), (222, 273, 266, 253),
                   (221, 274, 272, 247),
                   (253, 266, 276, 219), (271, 278, 279, 275), (275, 279, 280, 274), (274, 280, 281, 272),
                   (272, 281, 282, 273),
                   (273, 282, 283, 266), (266, 283, 284, 276), (276, 284, 285, 267), (267, 285, 286, 268),
                   (268, 286, 287, 269),
                   (269, 287, 288, 270), (270, 288, 289, 277), (277, 289, 278, 271)]

        return myvertex, myfaces


# WINDOWS -----------------------

from math import pi, radians


class WindowMake:
    
    def __init__(self, ObjectProp, name):
        self.ObjectProp = ObjectProp 
        self.name = name
    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    def execute(self):
        if bpy.context.mode == "OBJECT":
            self.create_object()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archimesh: Option only valid in Object mode")
            return {'CANCELLED'}


# ------------------------------------------------------------------------------
#
# Create main object. The other objects will be children of this.
#
# ------------------------------------------------------------------------------
# noinspection PyUnusedLocal
    def create_object(self):
        # deselect all objects
        for o in bpy.data.objects:
            o.select_set(False)

        # we create main object and mesh
        mainmesh = bpy.data.meshes.new("WindowFrane")
        mainobject = bpy.data.objects.new("WindowFrame", mainmesh)
        mainobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(mainobject)
        mainobject.WindowObjectGenerator.add()

        # we shape the main object and create other objects as children
        self.shape_mesh_and_create_children(mainobject, mainmesh)

        # we select, and activate, main object
        mainobject.select_set(True)
        bpy.context.view_layer.objects.active = mainobject


# ------------------------------------------------------------------------------
#
# Update main mesh and children objects
#
# ------------------------------------------------------------------------------
# noinspection PyUnusedLocal
    def update_object(self):
        # When we update, the active object is the main object
        o = bpy.context.active_object
        oldmesh = o.data
        oldname = o.data.name
        # Now we deselect that object to not delete it.
        o.select_set(False)
        # and we create a new mesh
        tmp_mesh = bpy.data.meshes.new("temp")
        # deselect all objects
        for obj in bpy.data.objects:
            obj.select_set(False)

        # ---------------------------------
        #  Clear Parent objects (autohole)
        # ---------------------------------
        myparent = o.parent
        ploc = myparent.location
        if myparent is not None:
            o.parent = None
            o.location = ploc
            # remove_children(parent)
            for child in myparent.children:
                # noinspection PyBroadException
                try:
                    # clear child data
                    child.hide_viewport = False  # must be visible to avoid bug
                    child.hide_render = False  # must be visible to avoid bug
                    old = child.data
                    child.select_set(True)
                    bpy.ops.object.delete()
                    bpy.data.meshes.remove(old)
                except:
                    dummy = -1

            myparent.select_set(True)
            bpy.ops.object.delete()

        # -----------------------
        # remove all children
        # -----------------------
        # first granchild
        for child in o.children:
            remove_children(child)
        # now children of main object
        remove_children(o)

        # Finally we create all that again (except main object),
        self.shape_mesh_and_create_children(o, tmp_mesh, True)
        o.data = tmp_mesh
        # Remove data (mesh of active object),
        bpy.data.meshes.remove(oldmesh)
        tmp_mesh.name = oldname
        # and select, and activate, the main object
        o.select_set(True)
        bpy.context.view_layer.objects.active = o


    # ------------------------------------------------------------------------------
    # Generate all objects
    # For main, it only shapes mesh and creates modifiers (the modifier, only the first time).
    # And, for the others, it creates object and mesh.
    # ------------------------------------------------------------------------------
    # noinspection PyUnusedLocal
    def shape_mesh_and_create_children(self,mainobject, tmp_mesh, update=False):
        mp = self.ObjectProp
        # Create only mesh, because the object is created before
        if mp['opentype'] == "1":
            self.generate_rail_window(mainobject, mp, tmp_mesh)
        else:
            self.generate_leaf_window(mainobject, mp, tmp_mesh)

        remove_doubles(mainobject)
        set_normals(mainobject)

        # saves OpenGL data
        if mp['blind'] is True:
            plus = mp['blind_height']
        else:
            plus = 0


        # Lock
        mainobject.lock_location = (True, True, True)
        mainobject.lock_rotation = (True, True, True)

        # -------------------------
        # Create empty and parent
        # -------------------------
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        myempty = bpy.data.objects[bpy.context.active_object.name]
        myempty.location = mainobject.location

        myempty.name = self.name
        parentobject(myempty, mainobject)
        mainobject["archimesh.hole_enable"] = True
        # Rotate Empty
        myempty.rotation_euler.z = radians(mp['r'])
        # Create control box to open wall holes
        gap = 0.002
        y = 0
        z = 0
        if mp['blind'] is True:
            y = mp['blind_rail']
        if mp['blind'] is True and mp['blind_box'] is True:
            z = mp['blind_height']

        myctrl = create_control_box("CTRL_Hole",
                                    mp['width'] - gap,
                                    mp['depth'] * 3,  # + y,
                                    mp['height'] + z - gap)
        # Add custom property to detect Controller
        myctrl["archimesh.ctrl_hole"] = True

        set_normals(myctrl)
        myctrl.parent = myempty
        myctrl.location.x = 0
        myctrl.location.y = -mp['depth'] * 3 / 2
        myctrl.location.z = 0
        myctrl.display_type = 'BOUNDS'
        myctrl.hide_viewport = False
        myctrl.hide_render = True
        if bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            myctrl.cycles_visibility.camera = False
            myctrl.cycles_visibility.diffuse = False
            myctrl.cycles_visibility.glossy = False
            myctrl.cycles_visibility.transmission = False
            myctrl.cycles_visibility.scatter = False
            myctrl.cycles_visibility.shadow = False

            mat = create_transparent_material("hidden_material", False)
            set_material(myctrl, mat)

        # deactivate others
        for o in bpy.data.objects:
            if o.select_get() is True and o.name != mainobject.name:
                o.select_set(False)

        return


# ------------------------------------------------------------------
# Define property group class to create or modify
# ------------------------------------------------------------------

    def generate_rail_window(self,myframe, mp, mymesh):
        myloc = bpy.context.scene.cursor.location

        alummat = None
        if mp['crt_mat'] and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            alummat = create_diffuse_material("Window_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)

        # Frame
        win_size, p1, p2 = self.create_rail_window_frame(myframe, mymesh,
                                                    mp['width'], mp['depth'], mp['height'],
                                                    mp['frame'],
                                                    mp['crt_mat'], alummat, mp['external'],
                                                    mp['blind'] and mp['blind_box'],
                                                    mp['blind_height'],
                                                    mp['blind_back'],
                                            mp['blind_rail'])

        remove_doubles(myframe)
        set_normals(myframe)

        # Window L
        width = (mp['width'] / 2) + 0.01
        mywin_l = self.create_rail_window_leaf("Window.L", "L",
                                        width, win_size, mp['height'] - 0.05,
                                        mp['wf'],
                                        myloc.x, myloc.y, myloc.z,
                                        mp['crt_mat'], alummat, mp['handle'])

        remove_doubles(mywin_l)
        set_normals(mywin_l)

        mywin_l.parent = myframe
        mywin_l.location.x = (-mp['width'] / 2) + 0.01
        mywin_l.location.y = p1 - 0.001
        mywin_l.location.z = 0.025
        # Window R
        mywin_r = self.create_rail_window_leaf("Window.R", "R",
                                        width, win_size, mp['height'] - 0.05,
                                        mp['wf'],
                                        myloc.x, myloc.y, myloc.z,
                                        mp['crt_mat'], alummat, mp['handle'])

        remove_doubles(mywin_r)
        set_normals(mywin_r)

        mywin_r.parent = myframe
        mywin_r.location.x = (mp['width'] / 2) - 0.01
        mywin_r.location.y = p2 - 0.001
        mywin_r.location.z = 0.025
        # Sill
        if mp['sill']:
            mysill = self.create_sill("Windows_Sill", mp['width'],
                                mp['depth'] + mp['sill_back'] + mp['sill_front'],
                                mp['sill_thickness'], mp['crt_mat'])
            mysill.parent = myframe
            mysill.location.x = 0
            mysill.location.y = -mp['depth'] - mp['sill_back']
            mysill.location.z = 0

        # Blind
        if mp['blind']:
            myblindrail = self.create_blind_rail("Blind_rails", mp['width'], mp['height'],
                                            myloc.x, myloc.y, myloc.z,
                                            mp['crt_mat'], alummatmp['blind_rail'])
            set_normals(myblindrail)

            myblindrail.parent = myframe
            myblindrail.location.x = 0
            myblindrail.location.y = 0
            myblindrail.location.z = 0
            # Lock
            myblindrail.lock_location = (True, True, True)
            myblindrail.lock_rotation = (True, True, True)

            myblind = self.create_blind("Blind", mp['width'] - 0.006, mp['height'],
                                myloc.x, myloc.y, myloc.z,
                                mp['crt_mat'], mp['blind_ratio'])
            set_normals(myblind)

            myblind.parent = myframe
            myblind.location.x = 0
            myblind.location.y = mp['blind_rail'] - 0.014
            myblind.location.z = mp['height'] - 0.098
            # Lock
            myblind.lock_location = (True, True, True)
            myblind.lock_rotation = (True, True, True)


    # ------------------------------------------------------------------------------
    # Generate leaf windows
    # ------------------------------------------------------------------------------
    def generate_leaf_window(self,myframe, mp, mymesh):
        myloc = bpy.context.scene.cursor.location

        alummat = None
        if mp['crt_mat'] and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            alummat = create_diffuse_material("Window_material", False, 0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.15)

        # Frame
        win_size = self.create_leaf_window_frame(myframe, mymesh,
                                            mp['width'], mp['depth'], mp['height'],
                                            mp['frame'], mp['frame_L'], mp['leafratio'],
                                            mp['crt_mat'], alummat, mp['external'],
                                            mp['blind'] and mp['blind_box'], mp['blind_height'], mp['blind_back'],
                                            mp['blind_rail'])

        remove_doubles(myframe)
        set_normals(myframe)

        stepsize = 0.01
        # -----------------------------
        # Window L
        # -----------------------------
        if mp['opentype'] == "2" or mp['opentype'] == "4":
            handle = mp['handle']
            if mp['opentype'] == "2":
                width = ((mp['width'] - (mp['frame_L'] * 2) + stepsize) / 2) + 0.004
                handle = False  # two windows only one handle
            else:
                width = mp['width'] - (mp['frame_L'] * 2) + stepsize + 0.008

            mywin_l =self. create_leaf_window_leaf("Window.L", "L",
                                            width, win_size, mp['height'] - (mp['frame_L'] * 2) + (stepsize * 2) - 0.004,
                                            mp['wf'],
                                            myloc.x, myloc.y, myloc.z,
                                            mp['crt_mat'], alummat, handle)

            remove_doubles(mywin_l)
            set_normals(mywin_l)

            mywin_l.parent = myframe
            mywin_l.location.x = -mp['width'] / 2 + mp['frame_L'] - stepsize + 0.001
            mywin_l.location.y = -mp['depth']
            mywin_l.location.z = mp['frame_L'] - (stepsize / 2) - 0.003
        # -----------------------------
        # Window R
        # -----------------------------
        if mp['opentype'] == "2" or mp['opentype'] == "3":
            if mp['opentype'] == "2":
                width = ((mp['width'] - (mp['frame_L'] * 2) + stepsize) / 2) + 0.003
            else:
                width = mp['width'] - (mp['frame_L'] * 2) + stepsize + 0.008

            mywin_r =self. create_leaf_window_leaf("Window.R", "R",
                                            width, win_size, mp['height'] - (mp['frame_L'] * 2) + (stepsize * 2) - 0.004,
                                            mp['wf'],
                                            myloc.x, myloc.y, myloc.z,
                                            mp['crt_mat'], alummat, mp['handle'])

            remove_doubles(mywin_r)
            set_normals(mywin_r)

            mywin_r.parent = myframe
            mywin_r.location.x = mp['width'] / 2 - mp['frame_L'] + stepsize - 0.001
            mywin_r.location.y = -mp['depth']
            mywin_r.location.z = mp['frame_L'] - (stepsize / 2) - 0.003

        # Sill
        if mp['sill']:
            mysill = self.create_sill("Windows_Sill", mp['width'],
                                mp['depth'] + mp['sill_back'] + mp['sill_front'],
                                mp['sill_thickness'], mp['crt_mat'])
            mysill.parent = myframe
            mysill.location.x = 0
            mysill.location.y = -mp['depth'] - mp['sill_back']
            mysill.location.z = 0

        # Blind
        if mp['blind']:
            myblindrail = self.create_blind_rail("Blind_rails", mp['width'], mp['height'],
                                            myloc.x, myloc.y, myloc.z,
                                            mp['crt_mat'], alummat,mp['blind_rail'])
            myblindrail.parent = myframe
            myblindrail.location.x = 0
            myblindrail.location.y = 0
            myblindrail.location.z = 0
            # Lock
            myblindrail.lock_location = (True, True, True)
            myblindrail.lock_rotation = (True, True, True)

            myblind = self.create_blind("Blind", mp['width'] - 0.006, mp['height'],
                                myloc.x, myloc.y, myloc.z,
                                mp['crt_mat'], mp['blind_ratio'])
            myblind.parent = myframe
            myblind.location.x = 0
            myblind.location.y = mp['blind_rail'] - 0.014
            myblind.location.z = mp['height'] - 0.098

            # Lock
            myblind.lock_location = (True, True, True)
            myblind.lock_rotation = (True, True, True)

        # deactivate others
        for o in bpy.data.objects:
            if o.select_get() is True:
                o.select_set(False)

        myframe.select_set(True)
        bpy.context.view_layer.objects.active = myframe

        return myframe


    # ------------------------------------------------------------------------------
    # Create windows frame
    #
    # sX: Size in X axis
    # sY: Size in Y axis
    # sZ: Size in Z axis
    # frame: size of external frame
    # mat: Flag for creating materials
    # matdata: Aluminum material
    # external: create external frame flag
    # blind: blind flag
    # blind_height: height of blind box
    # blind_back: front extension
    # blind_rail: distance of the rail
    # ------------------------------------------------------------------------------
    def create_rail_window_frame(self,mywindow, mymesh, sx, sy, sz, frame, mat, matdata, external,
                                blind, blind_height, blind_back, blind_rail):
        myvertex = []
        myfaces = []
        v = 0
        # ===========================================================================
        # Horizontal pieces
        # ===========================================================================
        m = 0.02  # gap in front
        gap = 0.001  # gap between leafs
        rail = 0.007  # rail width
        thick = 0.002  # aluminum thickness
        w = (sy - m - gap - thick - thick - thick) / 2  # width of each leaf
        p = (w - rail) / 2  # space of each side
        side = 0.02  # vertical
        for z in (0, sz):
            for x in (-sx / 2, sx / 2):
                myvertex.extend([(x, 0, z), (x, 0, z + side),
                                (x, -m - p, z + side),
                                (x, -m - p, z + (side * 2)),  # rail 1
                                (x, -m - p - rail, z + (side * 2)),
                                (x, -m - p - rail, z + side),
                                (x, -m - p - rail - thick - p - gap - p, z + side),
                                (x, -m - p - rail - thick - p - gap - p, z + (side * 2)),  # rail 2
                                (x, -m - p - rail - thick - p - gap - p - rail, z + (side * 2)),
                                (x, -m - p - rail - thick - p - gap - p - rail, z + side),
                                (x, -m - p - rail - thick - p - gap - p - rail - p - thick, z + side)])
            # Faces
            myfaces.extend([(v + 12, v + 1, v + 0, v + 11), (v + 13, v + 2, v + 1, v + 12), (v + 14, v + 3, v + 2, v + 13),
                            (v + 15, v + 4, v + 3, v + 14), (v + 16, v + 5, v + 4, v + 15), (v + 17, v + 6, v + 5, v + 16),
                            (v + 18, v + 7, v + 6, v + 17), (v + 19, v + 8, v + 7, v + 18), (v + 20, v + 9, v + 8, v + 19),
                            (v + 20, v + 21, v + 10, v + 9)])

            side *= -1  # reveser direction
            v = len(myvertex)
        # ===========================================================================
        # Vertical pieces
        # ===========================================================================
        y = 0
        sideb = 0.03
        sides = 0.02
        thickb = 0.002  # aluminum thickness
        win_size = p + rail + p
        p1 = y - m - thick
        p2 = y - m - thick - gap - p - rail - p - thick

        # Left
        for x in (-sx / 2, sx / 2):
            for z in (0, sz):
                myvertex.extend([(x, y, z),
                                (x + thickb, y, z),
                                (x + thickb, y - m, z),
                                (x + thickb + sides, y - m, z),
                                (x + thickb + sides, y - m - thick, z),
                                (x + thickb, y - m - thick, z),
                                (x + thickb, y - m - thick - gap - p - rail - p, z),
                                (x + thickb + sides, y - m - thick - gap - p - rail - p, z),
                                (x + thickb + sides, y - m - thick - gap - p - rail - p - thick, z),
                                (x + thickb, y - m - thick - gap - p - rail - p - thick, z),
                                (x + thickb, y - m - thick - gap - p - rail - p - thick - p - rail - p, z),
                                (x + thickb + sideb, y - m - thick - gap - p - rail - p - thick - p - rail - p, z),
                                (x + thickb + sideb, y - m - thick - gap - p - rail - p - thick - p - rail - p - thick, z),
                                (x, y - m - thick - gap - p - rail - p - thick - p - rail - p - thick, z)])
            # Faces
            myfaces.extend([(v + 13, v + 27, v + 14, v + 0), (v + 13, v + 12, v + 26, v + 27),
                            (v + 11, v + 10, v + 24, v + 25),
                            (v + 6, v + 5, v + 19, v + 20), (v + 10, v + 9, v + 23, v + 24),
                            (v + 25, v + 24, v + 27, v + 26), (v + 24, v + 23, v + 15, v + 16),
                            (v + 22, v + 21, v + 20, v + 23),
                            (v + 17, v + 16, v + 19, v + 18), (v + 9, v + 8, v + 22, v + 23),
                            (v + 7, v + 6, v + 20, v + 21), (v + 3, v + 2, v + 16, v + 17),
                            (v + 5, v + 4, v + 18, v + 19),
                            (v + 4, v + 3, v + 17, v + 18), (v + 7, v + 8, v + 9, v + 6),
                            (v + 3, v + 4, v + 5, v + 2), (v + 11, v + 12, v + 13, v + 10),
                            (v + 6, v + 5, v + 9, v + 10),
                            (v + 1, v + 0, v + 14, v + 15),
                            (v + 19, v + 16, v + 15, v + 14, v + 27, v + 24, v + 23, v + 20),
                            (v + 8, v + 7, v + 21, v + 22), (v + 12, v + 11, v + 25, v + 26),
                            (v + 2, v + 1, v + 15, v + 16),
                            (v + 5, v + 6, v + 9, v + 10, v + 13, v + 0, v + 1, v + 2)])

            v = len(myvertex)
            # reverse
            thickb *= -1
            sideb *= -1
            sides *= -1
        # ===========================================================================
        # Front covers
        # ===========================================================================
        x = sx - 0.005 - (sideb * 2)  # sideB + small gap
        y = y - m - thick - gap - p - rail - p - thick - p - rail - p
        z = sideb
        # Bottom
        myvertex.extend([(-x / 2, y - thick, 0.0),
                        (-x / 2, y, 0.0),
                        (x / 2, y, 0.0),
                        (x / 2, y - thick, 0.0),
                        (-x / 2, y - thick, z),
                        (-x / 2, y, z),
                        (x / 2, y, z),
                        (x / 2, y - thick, z)])

        myfaces.extend([(v + 0, v + 1, v + 2, v + 3), (v + 0, v + 1, v + 5, v + 4), (v + 1, v + 2, v + 6, v + 5),
                        (v + 2, v + 6, v + 7, v + 3), (v + 5, v + 6, v + 7, v + 4), (v + 0, v + 4, v + 7, v + 3)])
        v = len(myvertex)
        # Top
        myvertex.extend([(-x / 2, y - thick, sz - sideb),
                        (-x / 2, y, sz - sideb),
                        (x / 2, y, sz - sideb),
                        (x / 2, y - thick, sz - sideb),
                        (-x / 2, y - thick, sz - sideb + z),
                        (-x / 2, y, sz - sideb + z),
                        (x / 2, y, sz - sideb + z),
                        (x / 2, y - thick, sz - sideb + z)])

        myfaces.extend([(v + 0, v + 1, v + 2, v + 3), (v + 0, v + 1, v + 5, v + 4), (v + 1, v + 2, v + 6, v + 5),
                        (v + 2, v + 6, v + 7, v + 3), (v + 5, v + 6, v + 7, v + 4), (v + 0, v + 4, v + 7, v + 3)])
        v = len(myvertex)
        # ===========================================================================
        # External front covers
        # ===========================================================================
        if external:
            x = sx
            gap = -0.001
            sidem = frame
            box = 0
            if blind:
                box = blind_height

            myvertex.extend([((-x / 2) - sidem, y - thick, sz + sidem + box),
                            ((x / 2) + sidem, y - thick, sz + sidem + box),
                            ((-x / 2) - sidem, y - thick, -sidem),
                            ((x / 2) + sidem, y - thick, -sidem),
                            ((-x / 2) - gap, y - thick, sz + gap + box),
                            ((x / 2) + gap, y - thick, sz + gap + box),
                            ((-x / 2) - gap, y - thick, -gap),
                            ((x / 2) + gap, y - thick, -gap)])
            myvertex.extend([((-x / 2) - sidem, y - thick * 2, sz + sidem + box),
                            ((x / 2) + sidem, y - thick * 2, sz + sidem + box),
                            ((-x / 2) - sidem, y - thick * 2, -sidem),
                            ((x / 2) + sidem, y - thick * 2, -sidem),
                            ((-x / 2) - gap, y - thick * 2, sz + gap + box),
                            ((x / 2) + gap, y - thick * 2, sz + gap + box),
                            ((-x / 2) - gap, y - thick * 2, -gap),
                            ((x / 2) + gap, y - thick * 2, -gap)])

            myfaces.extend([(v + 3, v + 1, v + 9, v + 11), (v + 9, v + 8, v + 0, v + 1),
                            (v + 1, v + 5, v + 4, v + 0),
                            (v + 3, v + 7, v + 5, v + 1),
                            (v + 7, v + 3, v + 2, v + 6),
                            (v + 0, v + 4, v + 6, v + 2),
                            (v + 9, v + 13, v + 12, v + 8), (v + 11, v + 15, v + 13, v + 9),
                            (v + 15, v + 11, v + 10, v + 14),
                            (v + 8, v + 12, v + 14, v + 10),
                            (v + 11, v + 3, v + 2, v + 10),
                            (v + 2, v + 10, v + 8, v + 0), (v + 14, v + 12, v + 4, v + 6),
                            (v + 7, v + 6, v + 14, v + 15),
                            (v + 5, v + 13, v + 12, v + 4),
                            (v + 15, v + 7, v + 5, v + 13)])

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            set_material(mywindow, matdata)
        # --------------
        # Blind Box
        # --------------
        if blind:
            mybox = self.create_blind_box("Blind_box", sx, sy + blind_back + blind_rail, blind_height)
            set_normals(mybox)

            mybox.parent = mywindow
            mybox.location.x = 0
            mybox.location.y = -blind_back - sy
            mybox.location.z = sz
            if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
                set_material(mybox, matdata)
            # Lock
            mybox.lock_location = (True, True, True)
            mybox.lock_rotation = (True, True, True)

        return win_size, p1, p2


    # ------------------------------------------------------------------------------
    # Create leafs windows frame
    #
    # sX: Size in X axis
    # sY: Size in Y axis
    # sZ: Size in Z axis
    # frame: size of external frame
    # frame_L: size of main frame
    # leafratio: ratio of leaf depth
    # mat: Flag for creating materials
    # matdata: Aluminum material
    # external: create external frame flag
    # blind: blind flag
    # blind_height: height of blind box
    # blind_back: front extension
    # blind_rail: distance of the rail
    # ------------------------------------------------------------------------------
    def create_leaf_window_frame(self,mywindow, mymesh, sx, sy, sz, frame, frame_l, leafratio, mat, matdata, external,
                                blind, blind_height, blind_back, blind_rail):
        myvertex = []
        myfaces = []
        # ===========================================================================
        # Main frame_L
        # ===========================================================================
        x = sx / 2
        z = sz
        y = sy * leafratio
        gap = 0.01
        size = sy - y - 0.001  # thickness of the leaf

        myvertex.extend([(-x, 0, 0),
                        (-x, 0, z),
                        (x, 0, z),
                        (x, 0, 0),
                        (-x + frame_l, 0, frame_l),
                        (-x + frame_l, 0, z - frame_l),
                        (x - frame_l, 0, z - frame_l),
                        (x - frame_l, 0, frame_l),
                        (-x + frame_l, -y, frame_l),
                        (-x + frame_l, -y, z - frame_l),
                        (x - frame_l, -y, z - frame_l),
                        (x - frame_l, -y, frame_l),
                        (-x + frame_l - gap, -y, frame_l - gap),
                        (-x + frame_l - gap, -y, z - frame_l + gap),
                        (x - frame_l + gap, -y, z - frame_l + gap),
                        (x - frame_l + gap, -y, frame_l - gap),
                        (-x + frame_l - gap, -sy, frame_l - gap),
                        (-x + frame_l - gap, -sy, z - frame_l + gap),
                        (x - frame_l + gap, -sy, z - frame_l + gap),
                        (x - frame_l + gap, -sy, frame_l - gap),
                        (-x, -sy, 0),
                        (-x, -sy, z),
                        (x, -sy, z),
                        (x, -sy, 0)])
        # Faces
        myfaces.extend([(1, 5, 4, 0), (21, 1, 0, 20), (17, 21, 20, 16), (16, 12, 13, 17), (12, 8, 9, 13),
                        (5, 9, 8, 4), (3, 7, 6, 2), (23, 3, 2, 22), (19, 23, 22, 18), (15, 19, 18, 14),
                        (11, 15, 14, 10), (6, 7, 11, 10), (0, 3, 23, 20), (21, 22, 2, 1), (17, 13, 14, 18),
                        (21, 17, 18, 22), (13, 9, 10, 14), (8, 11, 7, 4), (8, 12, 15, 11), (4, 7, 3, 0),
                        (12, 16, 19, 15), (16, 20, 23, 19), (9, 5, 6, 10), (1, 2, 6, 5)])

        v = len(myvertex)
        # ===========================================================================
        # External front covers
        # ===========================================================================
        if external:
            thick = 0.002  # aluminum thickness
            x = sx
            gap = -0.001
            sidem = frame
            box = 0
            if blind:
                box = blind_height

            myvertex.extend([((-x / 2) - sidem, -sy, sz + sidem + box),
                            ((x / 2) + sidem, -sy, sz + sidem + box),
                            ((-x / 2) - sidem, -sy, -sidem),
                            ((x / 2) + sidem, -sy, -sidem),
                            ((-x / 2) - gap, -sy, sz + gap + box),
                            ((x / 2) + gap, -sy, sz + gap + box),
                            ((-x / 2) - gap, -sy, -gap),
                            ((x / 2) + gap, -sy, -gap)])
            myvertex.extend([((-x / 2) - sidem, -sy - thick, sz + sidem + box),
                            ((x / 2) + sidem, -sy - thick, sz + sidem + box),
                            ((-x / 2) - sidem, -sy - thick, -sidem),
                            ((x / 2) + sidem, -sy - thick, -sidem),
                            ((-x / 2) - gap, -sy - thick, sz + gap + box),
                            ((x / 2) + gap, -sy - thick, sz + gap + box),
                            ((-x / 2) - gap, -sy - thick, -gap),
                            ((x / 2) + gap, -sy - thick, -gap)])

            myfaces.extend([(v + 3, v + 1, v + 9, v + 11), (v + 9, v + 8, v + 0, v + 1), (v + 1, v + 5, v + 4, v + 0),
                            (v + 3, v + 7, v + 5, v + 1), (v + 7, v + 3, v + 2, v + 6),
                            (v + 0, v + 4, v + 6, v + 2), (v + 9, v + 13, v + 12, v + 8), (v + 11, v + 15, v + 13, v + 9),
                            (v + 15, v + 11, v + 10, v + 14), (v + 8, v + 12, v + 14, v + 10),
                            (v + 11, v + 3, v + 2, v + 10), (v + 2, v + 10, v + 8, v + 0), (v + 14, v + 12, v + 4, v + 6),
                            (v + 7, v + 6, v + 14, v + 15), (v + 5, v + 13, v + 12, v + 4),
                            (v + 15, v + 7, v + 5, v + 13)])

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            set_material(mywindow, matdata)

        # --------------
        # Blind Box
        # --------------
        if blind:
            mybox = self.create_blind_box("Blind_box", sx, sy + blind_back + blind_rail, blind_height)
            set_normals(mybox)

            mybox.parent = mywindow
            mybox.location.x = 0
            mybox.location.y = -blind_back - sy
            mybox.location.z = sz
            if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
                set_material(mybox, matdata)
            # Lock
            mybox.lock_location = (True, True, True)
            mybox.lock_rotation = (True, True, True)

        return size


    # ------------------------------------------------------------------------------
    # Create rail windows leaf
    #
    # objName: Name for the new object
    # hand: Left or Right
    # sX: Size in X axis
    # sY: Size in Y axis
    # sZ: Size in Z axis
    # f: size of the frame_L
    # pX: position X axis
    # pY: position Y axis
    # pZ: position Z axis
    # mat: Flag for creating materials
    # matdata: default material
    # handle: create handle flag
    # ------------------------------------------------------------------------------
    def create_rail_window_leaf(self,objname, hand, sx, sy, sz, f, px, py, pz, mat, matdata, handle):
        myvertex = []
        myfaces = []
        v = 0
        # ===========================================================================
        # Horizontal pieces
        # ===========================================================================
        rail = 0.010  # rail width
        t = sy - 0.002
        p = ((t - rail) / 2) - 0.002
        side = 0.02  # vertical rail

        x = sx
        z = sz
        fz = f
        if hand == "R":
            x *= -1
            f *= -1
        # ------------------------
        # frame
        # ------------------------
        myvertex.extend([(0, 0, 0),
                        (0, 0, z),
                        (x, 0, z),
                        (x, 0, 0),
                        (f, 0, fz),
                        (f, 0, z - fz),
                        (x - f, 0, z - fz),
                        (x - f, 0, fz),
                        (f, -t / 2, fz),
                        (f, -t / 2, z - fz),
                        (x - f, -t / 2, z - fz),
                        (x - f, -t / 2, fz),
                        (f, -t, fz),
                        (f, -t, z - fz),
                        (x - f, -t, z - fz),
                        (x - f, -t, fz),
                        (0, -t, 0),
                        (0, -t, z),
                        (x, -t, z),
                        (x, -t, 0)])
        # ------------------------
        # Side rails
        # ------------------------
        for z in (0, sz):
            myvertex.extend([(0, -p, z),
                            (x, -p, z),
                            (0, -p, z + side),
                            (x, -p, z + side),
                            (0, -p - rail, z + side),
                            (x, -p - rail, z + side),
                            (0, -p - rail, z),
                            (x, -p - rail, z)])
            side *= -1  # reverse

        # Faces
        myfaces.extend([(v + 10, v + 6, v + 7, v + 11), (v + 9, v + 8, v + 4, v + 5),
                        (v + 13, v + 12, v + 8, v + 9), (v + 14, v + 10, v + 11, v + 15),
                        (v + 6, v + 10, v + 9, v + 5),
                        (v + 9, v + 10, v + 14, v + 13), (v + 11, v + 7, v + 4, v + 8), (v + 12, v + 15, v + 11, v + 8),
                        (v + 3, v + 7, v + 6, v + 2),
                        (v + 5, v + 4, v + 0, v + 1),
                        (v + 4, v + 7, v + 3, v + 0), (v + 5, v + 1, v + 2, v + 6), (v + 17, v + 16, v + 12, v + 13),
                        (v + 15, v + 19, v + 18, v + 14),
                        (v + 15, v + 12, v + 16, v + 19),
                        (v + 14, v + 18, v + 17, v + 13), (v + 29, v + 2, v + 1, v + 28),
                        (v + 35, v + 34, v + 17, v + 18), (v + 35, v + 33, v + 32, v + 34),
                        (v + 31, v + 29, v + 28, v + 30),
                        (v + 33, v + 31, v + 30, v + 32), (v + 25, v + 24, v + 22, v + 23),
                        (v + 19, v + 16, v + 26, v + 27),
                        (v + 3, v + 21, v + 20, v + 0), (v + 25, v + 27, v + 26, v + 24),
                        (v + 23, v + 22, v + 20, v + 21), (v + 3, v + 2, v + 29, v + 21),
                        (v + 19, v + 27, v + 35, v + 18),
                        (v + 31, v + 33, v + 25, v + 23), (v + 32, v + 30, v + 22, v + 24),
                        (v + 16, v + 17, v + 34, v + 26), (v + 0, v + 20, v + 28, v + 1)])
        # Glass
        myfaces.extend([(v + 10, v + 9, v + 8, v + 11)])

        v = len(myvertex)

        # Faces (last glass)
        # ------------------------
        # Plastic parts
        # ------------------------
        ps = -0.004
        gap = -0.0002
        space = 0.005

        if hand == "R":
            ps *= -1
            gap *= -1
        for z in (0, sz):
            for x in (0, sx):

                if hand == "R":
                    x *= -1
                myvertex.extend([(x + gap, -p, z),
                                (x + ps, -p, z),
                                (x + gap, -p, z + side),
                                (x + ps, -p, z + side),
                                (x + gap, -p - rail, z + side),
                                (x + ps, -p - rail, z + side),
                                (x + gap, -p - rail, z),
                                (x + ps, -p - rail, z),
                                (x + gap, -p + rail - space, z),
                                (x + gap, -p - rail - space, z),
                                (x + gap, -p + rail - space, z + (side * 1.5)),
                                (x + gap, -p - rail - space, z + (side * 1.5)),
                                (x + ps, -p + rail - space, z),
                                (x + ps, -p - rail - space, z),
                                (x + ps, -p + rail - space, z + (side * 1.5)),
                                (x + ps, -p - rail - space, z + (side * 1.5))])
                myfaces.extend([(v + 12, v + 8, v + 10, v + 14), (v + 6, v + 7, v + 5, v + 4), (v + 1, v + 0, v + 2, v + 3),
                                (v + 5, v + 3, v + 2, v + 4), (v + 8, v + 12, v + 1, v + 0),
                                (v + 7, v + 6, v + 9, v + 13), (v + 13, v + 9, v + 11, v + 15),
                                (v + 14, v + 10, v + 11, v + 15),
                                (v + 10, v + 8, v + 0, v + 2, v + 4, v + 6, v + 9, v + 11),
                                (v + 12, v + 14, v + 15, v + 13, v + 7, v + 5, v + 3, v + 1)])

                v = len(myvertex)
                ps *= -1
                gap *= -1

            side *= -1  # reverse vertical

        mymesh = bpy.data.meshes.new(objname)
        mywindow = bpy.data.objects.new(objname, mymesh)

        mywindow.location[0] = px
        mywindow.location[1] = py
        mywindow.location[2] = pz
        bpy.context.collection.objects.link(mywindow)

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        set_normals(mywindow)

        # Lock transformation
        mywindow.lock_location = (False, True, True)  # only X axis
        mywindow.lock_rotation = (True, True, True)

        # Handle
        if handle:
            myhandle = self.create_rail_handle("Handle", mat)
            myhandle.parent = mywindow
            if hand == "R":
                myhandle.location.x = -0.035
            else:
                myhandle.location.x = +0.035

            myhandle.location.y = -sy + 0.001
            if sz / 2 <= 1:
                myhandle.location.z = sz / 2
            else:
                myhandle.location.z = 1

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            set_material(mywindow, matdata)
            # Glass
            glass = create_glass_material("Glass_material", False)
            mywindow.data.materials.append(glass)
            select_faces(mywindow, 32, True)
            set_material_faces(mywindow, 1)

        return mywindow


    # ------------------------------------------------------------------------------
    # Create leaf windows leaf
    #
    # objName: Name for the new object
    # hand: Left or Right
    # sX: Size in X axis
    # sY: Size in Y axis
    # sZ: Size in Z axis
    # f: size of the frame_L
    # pX: position X axis
    # pY: position Y axis
    # pZ: position Z axis
    # mat: Flag for creating materials
    # matdata: default material
    # handle: include handle
    # ------------------------------------------------------------------------------
    def create_leaf_window_leaf(self,objname, hand, sx, sy, sz, f, px, py, pz, mat, matdata, handle):
        myvertex = []
        myfaces = []
        x = sx
        z = sz
        fz = f
        t = sy
        if hand == "R":
            x *= -1
            f *= -1
        # ------------------------
        # frame
        # ------------------------
        myvertex.extend([(0, 0, 0),
                        (0, 0, z),
                        (x, 0, z),
                        (x, 0, 0),
                        (f, 0, fz),
                        (f, 0, z - fz),
                        (x - f, 0, z - fz),
                        (x - f, 0, fz),
                        (f, t / 2, fz),
                        (f, t / 2, z - fz),
                        (x - f, t / 2, z - fz),
                        (x - f, t / 2, fz),
                        (f, t, fz),
                        (f, t, z - fz),
                        (x - f, t, z - fz),
                        (x - f, t, fz),
                        (0, t, 0),
                        (0, t, z),
                        (x, t, z),
                        (x, t, 0)])
        # Faces
        myfaces.extend([(13, 14, 10, 9), (10, 6, 5, 9), (11, 7, 4, 8), (12, 15, 11, 8), (13, 9, 8, 12),
                        (9, 5, 4, 8), (10, 14, 15, 11), (6, 10, 11, 7), (19, 3, 2, 18), (17, 1, 0, 16),
                        (2, 1, 17, 18), (19, 16, 0, 3), (13, 17, 18, 14), (15, 14, 18, 19), (13, 12, 16, 17),
                        (12, 16, 19, 15), (6, 7, 3, 2), (4, 5, 1, 0), (5, 6, 2, 1), (4, 7, 3, 0),
                        (10, 9, 8, 11)])

        mymesh = bpy.data.meshes.new(objname)
        mywindow = bpy.data.objects.new(objname, mymesh)

        mywindow.location[0] = px
        mywindow.location[1] = py
        mywindow.location[2] = pz
        bpy.context.collection.objects.link(mywindow)

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        set_normals(mywindow)

        # Lock transformation
        mywindow.lock_location = (True, True, True)
        mywindow.lock_rotation = (True, True, False)

        if handle:
            myhandle = self.create_leaf_handle("Handle", mat)
            if hand == "L":
                myhandle.rotation_euler = (0, pi, 0)

            myhandle.parent = mywindow
            if hand == "R":
                myhandle.location.x = -sx + 0.025
            else:
                myhandle.location.x = sx - 0.025

            myhandle.location.y = 0
            if sz / 2 <= 1:
                myhandle.location.z = sz / 2
            else:
                myhandle.location.z = 1

            set_smooth(myhandle)
            set_modifier_subsurf(myhandle)

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            set_material(mywindow, matdata)
            # Glass
            glass = create_glass_material("Glass_material", False)
            mywindow.data.materials.append(glass)
            select_faces(mywindow, 20, True)
            set_material_faces(mywindow, 1)
        return mywindow


    # ------------------------------------------------------------
    # Generate Leaf handle
    #
    # objName: Object name
    # mat: create materials
    # ------------------------------------------------------------
    def create_leaf_handle(self,objname, mat):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.018522918224334717
        maxx = 0.10613098740577698
        miny = -0.04866280406713486
        maxy = 0.0002815350890159607
        minz = -0.06269633769989014
        maxz = 0.06289216876029968

        # Vertex
        myvertex = [(minx + 0.00752672553062439, maxy - 0.0176689475774765, minz + 0.0503292977809906),
                    (minx + 0.002989441156387329, maxy - 0.017728276550769806, minz + 0.057490378618240356),
                    (minx + 0.002640664577484131, maxy - 0.01777590811252594, maxz - 0.05962774157524109),
                    (minx + 0.006573766469955444, maxy - 0.017799079418182373, maxz - 0.05211767554283142),
                    (minx + 0.013735026121139526, maxy - 0.01779157668352127, maxz - 0.04758024215698242),
                    (minx + 0.0222054123878479, maxy - 0.017755411565303802, maxz - 0.04723122715950012),
                    (minx + 0.02971544861793518, maxy - 0.01770026981830597, maxz - 0.0511641800403595),
                    (minx + 0.03425273299217224, maxy - 0.017640933394432068, maxz - 0.058325231075286865),
                    (minx + 0.03460153937339783, maxy - 0.01759330928325653, minz + 0.05879288911819458),
                    (minx + 0.03066837787628174, maxy - 0.017570137977600098, minz + 0.051282793283462524),
                    (minx + 0.02350717782974243, maxy - 0.017577648162841797, minz + 0.046745359897613525),
                    (minx + 0.01503676176071167, maxy - 0.017613813281059265, minz + 0.046396344900131226),
                    (minx + 0.007489442825317383, maxy - 0.009374044835567474, minz + 0.05037441849708557),
                    (minx + 0.00295218825340271, maxy - 0.009433373808860779, minz + 0.05753546953201294),
                    (minx + 0.0026033520698547363, maxy - 0.009481005370616913, maxz - 0.05958262085914612),
                    (minx + 0.006536513566970825, maxy - 0.009206198155879974, maxz - 0.05207255482673645),
                    (minx + 0.013697713613510132, maxy - 0.009206198155879974, maxz - 0.04753512144088745),
                    (minx + 0.029678165912628174, maxy - 0.009206198155879974, maxz - 0.051119059324264526),
                    (minx + 0.034215450286865234, maxy - 0.009206198155879974, maxz - 0.05828014016151428),
                    (minx + 0.03456425666809082, maxy - 0.009298399090766907, minz + 0.05883798003196716),
                    (minx + 0.03063112497329712, maxy - 0.00927523523569107, minz + 0.051327913999557495),
                    (minx + 0.023469924926757812, maxy - 0.009282737970352173, minz + 0.046790480613708496),
                    (minx + 0.014999479055404663, maxy - 0.009318903088569641, minz + 0.046441465616226196),
                    (minx + 0.009239286184310913, maxy - 0.017671361565589905, minz + 0.052188992500305176),
                    (minx + 0.00540238618850708, maxy - 0.017721541225910187, minz + 0.058244675397872925),
                    (minx + 0.005107402801513672, maxy - 0.017761819064617157, maxz - 0.06018096208572388),
                    (minx + 0.00843346118927002, maxy - 0.01778140664100647, maxz - 0.05383017659187317),
                    (minx + 0.014489203691482544, maxy - 0.017775066196918488, maxz - 0.049993157386779785),
                    (minx + 0.021652132272720337, maxy - 0.017744481563568115, maxz - 0.04969802498817444),
                    (minx + 0.028002887964248657, maxy - 0.01769784837961197, maxz - 0.053023844957351685),
                    (minx + 0.03183978796005249, maxy - 0.01764768362045288, maxz - 0.059079527854919434),
                    (minx + 0.03213474154472351, maxy - 0.01760740578174591, minz + 0.05934610962867737),
                    (minx + 0.02880874276161194, maxy - 0.017587818205356598, minz + 0.05299532413482666),
                    (minx + 0.02275294065475464, maxy - 0.01759415864944458, minz + 0.04915827512741089),
                    (minx + 0.015590071678161621, maxy - 0.017624743282794952, minz + 0.04886317253112793),
                    (minx + 0.004389584064483643, maxy - 0.0009383484721183777, minz + 0.05804264545440674),
                    (minx + 0.00849863886833191, maxy - 0.0009383484721183777, minz + 0.0515575110912323),
                    (minx + 0.00407370924949646, maxy - 0.0009383484721183777, maxz - 0.05987495183944702),
                    (minx + 0.007635623216629028, maxy - 0.0009383484721183777, maxz - 0.053073734045028687),
                    (minx + 0.014120936393737793, maxy - 0.0009383484721183777, maxz - 0.04896456003189087),
                    (minx + 0.021791845560073853, maxy - 0.0009383484721183777, maxz - 0.04864847660064697),
                    (minx + 0.0285930335521698, maxy - 0.0009383484721183777, maxz - 0.052210211753845215),
                    (minx + 0.03270205855369568, maxy - 0.0009383484721183777, maxz - 0.05869537591934204),
                    (minx + 0.03301793336868286, maxy - 0.0009383484721183777, minz + 0.05922222137451172),
                    (minx + 0.02945604920387268, maxy - 0.0009383484721183777, minz + 0.052421003580093384),
                    (minx + 0.022970736026763916, maxy - 0.0009383484721183777, minz + 0.048311829566955566),
                    (minx + 0.015299826860427856, maxy - 0.0009383484721183777, minz + 0.04799577593803406),
                    (minx + 0.009323716163635254, maxy - 0.012187294661998749, minz + 0.05233737826347351),
                    (minx + 0.0055314600467681885, maxy - 0.01223689317703247, minz + 0.05832257866859436),
                    (minx + 0.005239963531494141, maxy - 0.012276701629161835, maxz - 0.06018644571304321),
                    (minx + 0.008527249097824097, maxy - 0.012296058237552643, maxz - 0.05390956997871399),
                    (minx + 0.01451253890991211, maxy - 0.012289784848690033, maxz - 0.05011719465255737),
                    (minx + 0.02159211039543152, maxy - 0.012259557843208313, maxz - 0.04982548952102661),
                    (minx + 0.027868926525115967, maxy - 0.012213476002216339, maxz - 0.05311262607574463),
                    (minx + 0.03166118264198303, maxy - 0.012163884937763214, maxz - 0.05909779667854309),
                    (minx + 0.03195270895957947, maxy - 0.01212407648563385, minz + 0.059411197900772095),
                    (minx + 0.028665393590927124, maxy - 0.012104712426662445, minz + 0.05313432216644287),
                    (minx + 0.02268010377883911, maxy - 0.012110985815525055, minz + 0.049341946840286255),
                    (minx + 0.01560056209564209, maxy - 0.012141212821006775, minz + 0.04905024170875549),
                    (minx + 0.009444117546081543, miny + 0.009956002235412598, minz + 0.05219161510467529),
                    (minx + 0.005651921033859253, miny + 0.00990641862154007, minz + 0.05817681550979614),
                    (minx + 0.005360394716262817, miny + 0.009866602718830109, maxz - 0.06033217906951904),
                    (minx + 0.008647710084915161, miny + 0.009847238659858704, maxz - 0.05405530333518982),
                    (minx + 0.014632970094680786, miny + 0.009853512048721313, maxz - 0.0502629280090332),
                    (minx + 0.021712541580200195, miny + 0.00988374650478363, maxz - 0.04997122287750244),
                    (minx + 0.02798938751220703, miny + 0.009929820895195007, maxz - 0.05325835943222046),
                    (minx + 0.03178161382675171, miny + 0.00997941941022873, maxz - 0.05924355983734131),
                    (minx + 0.032073140144348145, miny + 0.010019220411777496, minz + 0.05926543474197388),
                    (minx + 0.02878585457801819, miny + 0.010038584470748901, minz + 0.05298855900764465),
                    (minx + 0.022800534963607788, miny + 0.010032311081886292, minz + 0.04919618368148804),
                    (minx + 0.015720993280410767, miny + 0.010002091526985168, minz + 0.04890450835227966),
                    (minx + 0.009488403797149658, miny + 0.0001087486743927002, minz + 0.05213809013366699),
                    (minx + 0.0056961774826049805, miny + 5.917251110076904e-05, minz + 0.058123260736465454),
                    (minx + 0.005404621362686157, miny + 1.9356608390808105e-05, maxz - 0.06038573384284973),
                    (minx + 0.008691936731338501, miny, maxz - 0.05410885810852051),
                    (minx + 0.014677256345748901, miny + 6.258487701416016e-06, maxz - 0.05031648278236389),
                    (minx + 0.021756768226623535, miny + 3.650784492492676e-05, maxz - 0.05002477765083313),
                    (minx + 0.02803361415863037, miny + 8.258223533630371e-05, maxz - 0.05331191420555115),
                    (minx + 0.031825870275497437, miny + 0.00013218075037002563, maxz - 0.05929708480834961),
                    (minx + 0.03211739659309387, miny + 0.00017196685075759888, minz + 0.059211909770965576),
                    (minx + 0.028830111026763916, miny + 0.00019133836030960083, minz + 0.052935004234313965),
                    (minx + 0.022844791412353516, miny + 0.0001850724220275879, minz + 0.04914262890815735),
                    (minx + 0.015765219926834106, miny + 0.00015483051538467407, minz + 0.04885092377662659),
                    (maxx - 0.010264694690704346, miny + 0.0024030879139900208, minz + 0.0574510395526886),
                    (maxx - 0.009389877319335938, miny + 0.0028769299387931824, minz + 0.05982285737991333),
                    (maxx - 0.00899556279182434, miny + 0.003135383129119873, maxz - 0.06170690059661865),
                    (maxx - 0.00918734073638916, miny + 0.003109179437160492, maxz - 0.0570487380027771),
                    (maxx - 0.009913921356201172, miny + 0.002805367112159729, maxz - 0.0530393123626709),
                    (maxx - 0.010980546474456787, miny + 0.002305328845977783, maxz - 0.0507529079914093),
                    (maxx - 0.011445850133895874, miny + 0.008283689618110657, minz + 0.05754268169403076),
                    (maxx - 0.010571062564849854, miny + 0.008757516741752625, minz + 0.059914469718933105),
                    (maxx - 0.01017671823501587, miny + 0.009015955030918121, maxz - 0.06161528825759888),
                    (maxx - 0.010368555784225464, miny + 0.008989766240119934, maxz - 0.056957095861434937),
                    (maxx - 0.011095106601715088, miny + 0.008685953915119171, maxz - 0.05294764041900635),
                    (maxx - 0.012161701917648315, miny + 0.008185915648937225, maxz - 0.050661295652389526),
                    (maxx - 0.0007557570934295654, miny + 0.019280850887298584, minz + 0.05762714147567749),
                    (maxx - 0.0026130378246307373, miny + 0.019916504621505737, minz + 0.05755424499511719),
                    (maxx - 0.00020641088485717773, miny + 0.020433299243450165, minz + 0.059989362955093384),
                    (maxx, miny + 0.021083541214466095, maxz - 0.06154590845108032),
                    (maxx - 0.00019183754920959473, miny + 0.021057337522506714, maxz - 0.05688774585723877),
                    (maxx - 0.0007305145263671875, miny + 0.020361721515655518, maxz - 0.05287277698516846),
                    (maxx - 0.0014716684818267822, miny + 0.019183076918125153, maxz - 0.05057680606842041),
                    (maxx - 0.0033288896083831787, miny + 0.0198187455534935, maxz - 0.0506497323513031),
                    (maxx - 0.0020636916160583496, miny + 0.021068952977657318, minz + 0.05991646647453308),
                    (maxx - 0.0018572509288787842, miny + 0.021719202399253845, maxz - 0.061618804931640625),
                    (maxx - 0.002049088478088379, miny + 0.021692998707294464, maxz - 0.05696064233779907),
                    (maxx - 0.002587735652923584, miny + 0.020997390151023865, maxz - 0.05294567346572876),
                    (minx + 0.018761008977890015, miny + 9.564310312271118e-05, minz + 0.062207311391830444),
                    (minx + 0.0222054123878479, maxy - 0.009206198155879974, maxz - 0.04723122715950012),
                    (minx, maxy - 0.009349517524242401, minz),
                    (minx, maxy, minz),
                    (minx + 0.03702586889266968, maxy, minz),
                    (minx + 0.03702586889266968, maxy - 0.009349517524242401, minz),
                    (minx, maxy - 0.009349517524242401, maxz),
                    (minx, maxy, maxz),
                    (minx + 0.03702586889266968, maxy, maxz),
                    (minx + 0.03702586889266968, maxy - 0.009349517524242401, maxz),
                    (minx, maxy - 0.009349517524242401, minz + 0.0038556158542633057),
                    (minx, maxy - 0.009349517524242401, maxz - 0.0038556158542633057),
                    (minx, maxy, maxz - 0.0038556158542633057),
                    (minx, maxy, minz + 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy, maxz - 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy, minz + 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy - 0.009349517524242401, maxz - 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy - 0.009349517524242401, minz + 0.0038556158542633057),
                    (minx, maxy, maxz),
                    (minx, maxy, minz),
                    (minx + 0.03702586889266968, maxy, maxz),
                    (minx + 0.03702586889266968, maxy, minz),
                    (minx, maxy, maxz - 0.0038556158542633057),
                    (minx, maxy, minz + 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy, maxz - 0.0038556158542633057),
                    (minx + 0.03702586889266968, maxy, minz + 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy, maxz),
                    (minx + 0.03234601020812988, maxy, maxz),
                    (minx + 0.03234601020812988, maxy, minz),
                    (minx + 0.00467991828918457, maxy, minz),
                    (minx + 0.03234601020812988, maxy - 0.009349517524242401, maxz),
                    (minx + 0.00467991828918457, maxy - 0.009349517524242401, maxz),
                    (minx + 0.00467991828918457, maxy - 0.009349517524242401, minz),
                    (minx + 0.03234601020812988, maxy - 0.009349517524242401, minz),
                    (minx + 0.03234601020812988, maxy, maxz - 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy, maxz - 0.0038556158542633057),
                    (minx + 0.03234601020812988, maxy, minz + 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy, minz + 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy - 0.009349517524242401, maxz - 0.0038556158542633057),
                    (minx + 0.03234601020812988, maxy - 0.009349517524242401, maxz - 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy - 0.009349517524242401, minz + 0.0038556158542633057),
                    (minx + 0.03234601020812988, maxy - 0.009349517524242401, minz + 0.0038556158542633057),
                    (minx + 0.00467991828918457, maxy, minz),
                    (minx + 0.03234601020812988, maxy, minz),
                    (minx + 0.03234601020812988, maxy, maxz),
                    (minx + 0.00467991828918457, maxy, maxz),
                    (minx + 0.01765689253807068, maxy - 0.008991599082946777, maxz - 0.00847548246383667),
                    (minx + 0.014916181564331055, maxy - 0.008991599082946777, maxz - 0.00961071252822876),
                    (minx + 0.013780921697616577, maxy - 0.008991606533527374, maxz - 0.012351423501968384),
                    (minx + 0.014916181564331055, maxy - 0.008991606533527374, maxz - 0.015092134475708008),
                    (minx + 0.01765689253807068, maxy - 0.008991606533527374, maxz - 0.016227364540100098),
                    (minx + 0.02039763331413269, maxy - 0.008991606533527374, maxz - 0.015092134475708008),
                    (minx + 0.021532833576202393, maxy - 0.008991606533527374, maxz - 0.012351423501968384),
                    (minx + 0.02039763331413269, maxy - 0.008991599082946777, maxz - 0.00961071252822876),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, maxz - 0.00847548246383667),
                    (minx + 0.014916181564331055, maxy - 0.0095299631357193, maxz - 0.00961071252822876),
                    (minx + 0.013780921697616577, maxy - 0.0095299631357193, maxz - 0.012351423501968384),
                    (minx + 0.014916181564331055, maxy - 0.0095299631357193, maxz - 0.015092134475708008),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, maxz - 0.016227364540100098),
                    (minx + 0.02039763331413269, maxy - 0.0095299631357193, maxz - 0.015092134475708008),
                    (minx + 0.021532833576202393, maxy - 0.0095299631357193, maxz - 0.012351423501968384),
                    (minx + 0.02039763331413269, maxy - 0.0095299631357193, maxz - 0.00961071252822876),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, maxz - 0.009734481573104858),
                    (minx + 0.0158064067363739, maxy - 0.0095299631357193, maxz - 0.010500967502593994),
                    (minx + 0.015039980411529541, maxy - 0.0095299631357193, maxz - 0.012351423501968384),
                    (minx + 0.0158064067363739, maxy - 0.0095299631357193, maxz - 0.014201879501342773),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, maxz - 0.014968395233154297),
                    (minx + 0.01950731873512268, maxy - 0.0095299631357193, maxz - 0.014201879501342773),
                    (minx + 0.020273834466934204, maxy - 0.0095299631357193, maxz - 0.012351423501968384),
                    (minx + 0.01950731873512268, maxy - 0.0095299631357193, maxz - 0.010500967502593994),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.009734481573104858),
                    (minx + 0.0158064067363739, maxy - 0.009312078356742859, maxz - 0.010500967502593994),
                    (minx + 0.015039980411529541, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.0158064067363739, maxy - 0.009312078356742859, maxz - 0.014201879501342773),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.014968395233154297),
                    (minx + 0.01950731873512268, maxy - 0.009312078356742859, maxz - 0.014201879501342773),
                    (minx + 0.020273834466934204, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.01950731873512268, maxy - 0.009312078356742859, maxz - 0.010500967502593994),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.01099047064781189),
                    (minx + 0.01669454574584961, maxy - 0.009312078356742859, maxz - 0.011389046907424927),
                    (minx + 0.016295909881591797, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.01669454574584961, maxy - 0.009312078356742859, maxz - 0.013313770294189453),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.013712406158447266),
                    (minx + 0.01861920952796936, maxy - 0.009312078356742859, maxz - 0.013313770294189453),
                    (minx + 0.019017815589904785, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.01861920952796936, maxy - 0.009312078356742859, maxz - 0.011389046907424927),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.011496275663375854),
                    (minx + 0.01705223321914673, maxy - 0.009312078356742859, maxz - 0.011746734380722046),
                    (minx + 0.01680171489715576, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.01705223321914673, maxy - 0.009312078356742859, maxz - 0.012956112623214722),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, maxz - 0.013206571340560913),
                    (minx + 0.018261581659317017, maxy - 0.009312078356742859, maxz - 0.012956112623214722),
                    (minx + 0.018512040376663208, maxy - 0.009312078356742859, maxz - 0.012351423501968384),
                    (minx + 0.018261581659317017, maxy - 0.009312078356742859, maxz - 0.011746734380722046),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.009734481573104858),
                    (minx + 0.0158064067363739, maxy - 0.009564712643623352, maxz - 0.010500967502593994),
                    (minx + 0.015039980411529541, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.0158064067363739, maxy - 0.009564712643623352, maxz - 0.014201879501342773),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.014968395233154297),
                    (minx + 0.01950731873512268, maxy - 0.009564712643623352, maxz - 0.014201879501342773),
                    (minx + 0.020273834466934204, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.01950731873512268, maxy - 0.009564712643623352, maxz - 0.010500967502593994),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.01099047064781189),
                    (minx + 0.01669454574584961, maxy - 0.009564712643623352, maxz - 0.011389046907424927),
                    (minx + 0.016295909881591797, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.01669454574584961, maxy - 0.009564712643623352, maxz - 0.013313770294189453),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.013712406158447266),
                    (minx + 0.01861920952796936, maxy - 0.009564712643623352, maxz - 0.013313770294189453),
                    (minx + 0.019017815589904785, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.01861920952796936, maxy - 0.009564712643623352, maxz - 0.011389046907424927),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.011496275663375854),
                    (minx + 0.01705223321914673, maxy - 0.009564712643623352, maxz - 0.011746734380722046),
                    (minx + 0.01680171489715576, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.01705223321914673, maxy - 0.009564712643623352, maxz - 0.012956112623214722),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, maxz - 0.013206571340560913),
                    (minx + 0.018261581659317017, maxy - 0.009564712643623352, maxz - 0.012956112623214722),
                    (minx + 0.018512040376663208, maxy - 0.009564712643623352, maxz - 0.012351423501968384),
                    (minx + 0.018261581659317017, maxy - 0.009564712643623352, maxz - 0.011746734380722046),
                    (minx + 0.01765689253807068, maxy - 0.008991599082946777, minz + 0.017180711030960083),
                    (minx + 0.014916181564331055, maxy - 0.008991599082946777, minz + 0.016045480966567993),
                    (minx + 0.013780921697616577, maxy - 0.008991606533527374, minz + 0.01330476999282837),
                    (minx + 0.014916181564331055, maxy - 0.008991606533527374, minz + 0.010564059019088745),
                    (minx + 0.01765689253807068, maxy - 0.008991606533527374, minz + 0.009428799152374268),
                    (minx + 0.02039763331413269, maxy - 0.008991606533527374, minz + 0.010564059019088745),
                    (minx + 0.021532833576202393, maxy - 0.008991606533527374, minz + 0.01330476999282837),
                    (minx + 0.02039763331413269, maxy - 0.008991599082946777, minz + 0.016045480966567993),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, minz + 0.017180711030960083),
                    (minx + 0.014916181564331055, maxy - 0.0095299631357193, minz + 0.016045480966567993),
                    (minx + 0.013780921697616577, maxy - 0.0095299631357193, minz + 0.01330476999282837),
                    (minx + 0.014916181564331055, maxy - 0.0095299631357193, minz + 0.010564059019088745),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, minz + 0.009428799152374268),
                    (minx + 0.02039763331413269, maxy - 0.0095299631357193, minz + 0.010564059019088745),
                    (minx + 0.021532833576202393, maxy - 0.0095299631357193, minz + 0.01330476999282837),
                    (minx + 0.02039763331413269, maxy - 0.0095299631357193, minz + 0.016045480966567993),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, minz + 0.015921711921691895),
                    (minx + 0.0158064067363739, maxy - 0.0095299631357193, minz + 0.015155225992202759),
                    (minx + 0.015039980411529541, maxy - 0.0095299631357193, minz + 0.01330476999282837),
                    (minx + 0.0158064067363739, maxy - 0.0095299631357193, minz + 0.01145431399345398),
                    (minx + 0.01765689253807068, maxy - 0.0095299631357193, minz + 0.010687828063964844),
                    (minx + 0.01950731873512268, maxy - 0.0095299631357193, minz + 0.01145431399345398),
                    (minx + 0.020273834466934204, maxy - 0.0095299631357193, minz + 0.01330476999282837),
                    (minx + 0.01950731873512268, maxy - 0.0095299631357193, minz + 0.015155225992202759),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.015921711921691895),
                    (minx + 0.0158064067363739, maxy - 0.009312078356742859, minz + 0.015155225992202759),
                    (minx + 0.015039980411529541, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.0158064067363739, maxy - 0.009312078356742859, minz + 0.01145431399345398),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.010687828063964844),
                    (minx + 0.01950731873512268, maxy - 0.009312078356742859, minz + 0.01145431399345398),
                    (minx + 0.020273834466934204, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.01950731873512268, maxy - 0.009312078356742859, minz + 0.015155225992202759),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.014665752649307251),
                    (minx + 0.01669454574584961, maxy - 0.009312078356742859, minz + 0.014267116785049438),
                    (minx + 0.016295909881591797, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.01669454574584961, maxy - 0.009312078356742859, minz + 0.012342393398284912),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.011943817138671875),
                    (minx + 0.01861920952796936, maxy - 0.009312078356742859, minz + 0.012342393398284912),
                    (minx + 0.019017815589904785, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.01861920952796936, maxy - 0.009312078356742859, minz + 0.014267116785049438),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.014159917831420898),
                    (minx + 0.01705223321914673, maxy - 0.009312078356742859, minz + 0.01390942931175232),
                    (minx + 0.01680171489715576, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.01705223321914673, maxy - 0.009312078356742859, minz + 0.012700080871582031),
                    (minx + 0.01765689253807068, maxy - 0.009312078356742859, minz + 0.012449592351913452),
                    (minx + 0.018261581659317017, maxy - 0.009312078356742859, minz + 0.012700080871582031),
                    (minx + 0.018512040376663208, maxy - 0.009312078356742859, minz + 0.01330476999282837),
                    (minx + 0.018261581659317017, maxy - 0.009312078356742859, minz + 0.01390942931175232),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.015921711921691895),
                    (minx + 0.0158064067363739, maxy - 0.009564712643623352, minz + 0.015155225992202759),
                    (minx + 0.015039980411529541, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.0158064067363739, maxy - 0.009564712643623352, minz + 0.01145431399345398),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.010687828063964844),
                    (minx + 0.01950731873512268, maxy - 0.009564712643623352, minz + 0.01145431399345398),
                    (minx + 0.020273834466934204, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.01950731873512268, maxy - 0.009564712643623352, minz + 0.015155225992202759),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.014665752649307251),
                    (minx + 0.01669454574584961, maxy - 0.009564712643623352, minz + 0.014267116785049438),
                    (minx + 0.016295909881591797, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.01669454574584961, maxy - 0.009564712643623352, minz + 0.012342393398284912),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.011943817138671875),
                    (minx + 0.01861920952796936, maxy - 0.009564712643623352, minz + 0.012342393398284912),
                    (minx + 0.019017815589904785, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.01861920952796936, maxy - 0.009564712643623352, minz + 0.014267116785049438),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.014159917831420898),
                    (minx + 0.01705223321914673, maxy - 0.009564712643623352, minz + 0.01390942931175232),
                    (minx + 0.01680171489715576, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.01705223321914673, maxy - 0.009564712643623352, minz + 0.012700080871582031),
                    (minx + 0.01765689253807068, maxy - 0.009564712643623352, minz + 0.012449592351913452),
                    (minx + 0.018261581659317017, maxy - 0.009564712643623352, minz + 0.012700080871582031),
                    (minx + 0.018512040376663208, maxy - 0.009564712643623352, minz + 0.01330476999282837),
                    (minx + 0.018261581659317017, maxy - 0.009564712643623352, minz + 0.01390942931175232)]

        # Faces
        myfaces = [(12, 0, 1, 13), (13, 1, 2, 14), (14, 2, 3, 15), (15, 3, 4, 16), (17, 6, 7, 18),
                (18, 7, 8, 19), (19, 8, 9, 20), (20, 9, 10, 21), (21, 10, 11, 22), (22, 11, 0, 12),
                (1, 0, 23, 24), (2, 1, 24, 25), (3, 2, 25, 26), (4, 3, 26, 27), (5, 4, 27, 28),
                (6, 5, 28, 29), (7, 6, 29, 30), (8, 7, 30, 31), (9, 8, 31, 32), (10, 9, 32, 33),
                (11, 10, 33, 34), (0, 11, 34, 23), (24, 23, 36, 35), (25, 24, 35, 37), (26, 25, 37, 38),
                (27, 26, 38, 39), (28, 27, 39, 40), (29, 28, 40, 41), (30, 29, 41, 42), (31, 30, 42, 43),
                (32, 31, 43, 44), (33, 32, 44, 45), (34, 33, 45, 46), (23, 34, 46, 36), (48, 47, 59, 60),
                (49, 48, 60, 61), (50, 49, 61, 62), (51, 50, 62, 63), (52, 51, 63, 64), (53, 52, 64, 65),
                (54, 53, 65, 66), (55, 54, 66, 67), (56, 55, 67, 68), (57, 56, 68, 69), (58, 57, 69, 70),
                (59, 47, 58, 70), (60, 59, 71, 72), (61, 60, 72, 73), (62, 61, 73, 74), (63, 62, 74, 75),
                (64, 63, 75, 76), (70, 69, 81, 82), (70, 82, 71, 59), (81, 69, 89, 83), (80, 81, 83, 84),
                (79, 80, 84, 85), (78, 79, 85, 86), (77, 78, 86, 87), (76, 77, 87, 88), (64, 76, 88, 94),
                (69, 68, 90, 89), (68, 67, 91, 90), (67, 66, 92, 91), (66, 65, 93, 92), (65, 64, 94, 93),
                (83, 89, 96, 95), (84, 83, 95, 97), (85, 84, 97, 98), (86, 85, 98, 99), (87, 86, 99, 100),
                (88, 87, 100, 101), (94, 88, 101, 102), (89, 90, 103, 96), (90, 91, 104, 103), (91, 92, 105, 104),
                (92, 93, 106, 105), (93, 94, 102, 106), (100, 106, 102, 101), (99, 105, 106, 100), (98, 104, 105, 99),
                (97, 103, 104, 98), (95, 96, 103, 97), (72, 71, 107), (73, 72, 107), (74, 73, 107),
                (75, 74, 107), (76, 75, 107), (77, 76, 107), (78, 77, 107), (79, 78, 107),
                (80, 79, 107), (81, 80, 107), (82, 81, 107), (71, 82, 107), (17, 108, 5, 6),
                (5, 108, 16, 4), (130, 120, 110, 126), (143, 122, 111, 135), (132, 124, 112, 128), (147, 117, 109, 139),
                (150, 135, 111, 128), (152, 133, 114, 125), (125, 114, 119, 129),
                (129, 119, 120, 130), (134, 115, 121, 141),
                (141, 121, 122, 143), (127, 116, 123, 131), (131, 123, 124, 132),
                (138, 113, 118, 145), (145, 118, 117, 147),
                (117, 130, 126, 109), (122, 132, 128, 111), (140, 150, 128, 112),
                (138, 152, 125, 113), (113, 125, 129, 118),
                (118, 129, 130, 117), (115, 127, 131, 121), (121, 131, 132, 122),
                (120, 144, 136, 110), (144, 143, 135, 136),
                (124, 148, 140, 112), (148, 147, 139, 140), (126, 110, 136, 149),
                (149, 136, 135, 150), (127, 115, 134, 151),
                (151, 134, 133, 152), (114, 133, 142, 119), (133, 134, 141, 142),
                (119, 142, 144, 120), (142, 141, 143, 144),
                (116, 137, 146, 123), (137, 138, 145, 146), (123, 146, 148, 124),
                (146, 145, 147, 148), (109, 126, 149, 139),
                (139, 149, 150, 140), (116, 127, 151, 137), (137, 151, 152, 138),
                (153, 160, 168, 161), (160, 159, 167, 168),
                (159, 158, 166, 167), (158, 157, 165, 166), (157, 156, 164, 165),
                (156, 155, 163, 164), (155, 154, 162, 163),
                (154, 153, 161, 162), (161, 168, 176, 169), (168, 167, 175, 176),
                (167, 166, 174, 175), (166, 165, 173, 174),
                (165, 164, 172, 173), (164, 163, 171, 172), (163, 162, 170, 171),
                (162, 161, 169, 170), (169, 176, 184, 177),
                (176, 175, 183, 184), (175, 174, 182, 183), (174, 173, 181, 182),
                (173, 172, 180, 181), (172, 171, 179, 180),
                (171, 170, 178, 179), (170, 169, 177, 178), (197, 189, 213, 221),
                (184, 183, 191, 192), (196, 197, 221, 220),
                (182, 181, 189, 190), (185, 177, 201, 209), (180, 179, 187, 188),
                (195, 187, 211, 219), (178, 177, 185, 186),
                (198, 199, 223, 222), (192, 191, 199, 200), (191, 183, 207, 215),
                (190, 189, 197, 198), (200, 193, 217, 224),
                (188, 187, 195, 196), (189, 181, 205, 213), (186, 185, 193, 194),
                (194, 193, 200, 199, 198, 197, 196, 195),
                (201, 208, 216, 209),
                (207, 206, 214, 215), (205, 204, 212, 213), (203, 202, 210, 211),
                (209, 216, 224, 217), (215, 214, 222, 223),
                (213, 212, 220, 221), (211, 210, 218, 219), (194, 195, 219, 218),
                (199, 191, 215, 223), (178, 186, 210, 202),
                (193, 185, 209, 217), (177, 184, 208, 201), (180, 188, 212, 204),
                (183, 182, 206, 207), (182, 190, 214, 206),
                (186, 194, 218, 210), (181, 180, 204, 205), (184, 192, 216, 208),
                (188, 196, 220, 212), (179, 178, 202, 203),
                (190, 198, 222, 214), (192, 200, 224, 216), (187, 179, 203, 211),
                (225, 232, 240, 233), (232, 231, 239, 240),
                (231, 230, 238, 239), (230, 229, 237, 238), (229, 228, 236, 237),
                (228, 227, 235, 236), (227, 226, 234, 235),
                (226, 225, 233, 234), (233, 240, 248, 241), (240, 239, 247, 248),
                (239, 238, 246, 247), (238, 237, 245, 246),
                (237, 236, 244, 245), (236, 235, 243, 244), (235, 234, 242, 243),
                (234, 233, 241, 242), (241, 248, 256, 249),
                (248, 247, 255, 256), (247, 246, 254, 255), (246, 245, 253, 254),
                (245, 244, 252, 253), (244, 243, 251, 252),
                (243, 242, 250, 251), (242, 241, 249, 250), (269, 261, 285, 293),
                (256, 255, 263, 264), (268, 269, 293, 292),
                (254, 253, 261, 262), (257, 249, 273, 281), (252, 251, 259, 260),
                (267, 259, 283, 291), (250, 249, 257, 258),
                (270, 271, 295, 294), (264, 263, 271, 272), (263, 255, 279, 287),
                (262, 261, 269, 270), (272, 265, 289, 296),
                (260, 259, 267, 268), (261, 253, 277, 285), (258, 257, 265, 266),
                (266, 265, 272, 271, 270, 269, 268, 267),
                (273, 280, 288, 281),
                (279, 278, 286, 287), (277, 276, 284, 285), (275, 274, 282, 283),
                (281, 288, 296, 289), (287, 286, 294, 295),
                (285, 284, 292, 293), (283, 282, 290, 291), (266, 267, 291, 290),
                (271, 263, 287, 295), (250, 258, 282, 274),
                (265, 257, 281, 289), (249, 256, 280, 273), (252, 260, 284, 276),
                (255, 254, 278, 279), (254, 262, 286, 278),
                (258, 266, 290, 282), (253, 252, 276, 277), (256, 264, 288, 280),
                (260, 268, 292, 284), (251, 250, 274, 275),
                (262, 270, 294, 286), (264, 272, 296, 288), (259, 251, 275, 283)]

        mesh = bpy.data.meshes.new(objname)
        myobject = bpy.data.objects.new(objname, mesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mesh.from_pydata(myvertex, [], myfaces)
        mesh.update(calc_edges=True)

        # Create materials
        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            alumat = create_glossy_material("Handle_material", False, 0.733, 0.779, 0.8)
            set_material(myobject, alumat)

        return myobject


    # ------------------------------------------------------------
    # Generate rail handle
    #
    # objName: Object name
    # mat: create materials
    # ------------------------------------------------------------
    def create_rail_handle(self,objname, mat):
        # ------------------------------------
        # Mesh data
        # ------------------------------------
        minx = -0.007970962673425674
        maxx = 0.007971039041876793
        miny = -0.0038057267665863037
        maxy = 6.780028343200684e-07
        minz = -0.07533407211303711
        maxz = 0.05025443434715271

        # Vertex
        myvertex = [(minx, miny + 0.0009473562240600586, minz),
                    (minx, maxy, minz),
                    (maxx, maxy, minz),
                    (maxx, miny + 0.0009473562240600586, minz),
                    (minx, miny + 0.0009473562240600586, maxz),
                    (minx, maxy, maxz),
                    (maxx, maxy, maxz),
                    (maxx, miny + 0.0009473562240600586, maxz),
                    (minx, miny + 0.0009473562240600586, minz + 0.0038556158542633057),
                    (minx, miny + 0.0009473562240600586, maxz - 0.0038556158542633057),
                    (minx, maxy, minz + 0.0038556158542633057),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.0038556158542633057),
                    (maxx, miny + 0.0009473562240600586, minz + 0.0038556158542633057),
                    (minx, maxy, maxz - 0.0038556158542633057),
                    (maxx, maxy, maxz - 0.0038556158542633057),
                    (maxx, maxy, minz + 0.0038556158542633057),
                    (maxx - 0.002014978788793087, maxy, maxz),
                    (minx + 0.0020150020718574524, maxy, minz),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, minz),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, minz),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.0038556158542633057),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.0038556158542633057),
                    (maxx - 0.002014978788793087, maxy, minz + 0.0038556158542633057),
                    (minx + 0.0020150020718574524, maxy, minz + 0.0038556158542633057),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.0038556158542633057),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.0038556158542633057),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, minz + 0.0038556158542633057),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, minz + 0.0038556158542633057),
                    (maxx - 0.002014978788793087, maxy, minz),
                    (minx + 0.0020150020718574524, maxy, maxz),
                    (minx + 0.007114947948139161, miny + 0.001102180453017354, maxz - 0.004768103361129761),
                    (minx + 0.0057074506767094135, miny + 0.001102180453017354, maxz - 0.005351103842258453),
                    (minx + 0.005124435992911458, miny + 0.001102176494896412, maxz - 0.006758600473403931),
                    (minx + 0.0057074506767094135, miny + 0.001102176494896412, maxz - 0.008166097104549408),
                    (minx + 0.007114947948139161, miny + 0.001102176494896412, maxz - 0.0087490975856781),
                    (maxx - 0.0074195414781570435, miny + 0.001102176494896412, maxz - 0.008166097104549408),
                    (maxx - 0.006836557062342763, miny + 0.001102176494896412, maxz - 0.006758600473403931),
                    (maxx - 0.0074195414781570435, miny + 0.001102180453017354, maxz - 0.005351103842258453),
                    (minx + 0.007114947948139161, miny + 0.0008257024455815554, maxz - 0.004768103361129761),
                    (minx + 0.0057074506767094135, miny + 0.0008257024455815554, maxz - 0.005351103842258453),
                    (minx + 0.005124435992911458, miny + 0.0008257024455815554, maxz - 0.006758600473403931),
                    (minx + 0.0057074506767094135, miny + 0.0008257024455815554, maxz - 0.008166097104549408),
                    (minx + 0.007114947948139161, miny + 0.0008257024455815554, maxz - 0.0087490975856781),
                    (maxx - 0.0074195414781570435, miny + 0.0008257024455815554, maxz - 0.008166097104549408),
                    (maxx - 0.006836557062342763, miny + 0.0008257024455815554, maxz - 0.006758600473403931),
                    (maxx - 0.0074195414781570435, miny + 0.0008257024455815554, maxz - 0.005351103842258453),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.0054146647453308105),
                    (minx + 0.006164627615362406, miny + 0.000937597593292594, maxz - 0.00580829381942749),
                    (minx + 0.0057710278779268265, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (minx + 0.006164627615362406, miny + 0.000937597593292594, maxz - 0.007708907127380371),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.008102551102638245),
                    (maxx - 0.007876764051616192, miny + 0.000937597593292594, maxz - 0.007708907127380371),
                    (maxx - 0.007483118446543813, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (maxx - 0.007876764051616192, miny + 0.000937597593292594, maxz - 0.00580829381942749),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.006059680134057999),
                    (minx + 0.006620732950977981, miny + 0.000937597593292594, maxz - 0.006264369934797287),
                    (minx + 0.006416012765839696, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (minx + 0.006620732950977981, miny + 0.000937597593292594, maxz - 0.0072528161108493805),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.0074575357139110565),
                    (minx + 0.0076091475784778595, miny + 0.000937597593292594, maxz - 0.0072528161108493805),
                    (minx + 0.007813852455001324, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (minx + 0.0076091475784778595, miny + 0.000937597593292594, maxz - 0.006264369934797287),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.006319437175989151),
                    (minx + 0.006804424105212092, miny + 0.000937597593292594, maxz - 0.0064480602741241455),
                    (minx + 0.00667576992418617, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (minx + 0.006804424105212092, miny + 0.000937597593292594, maxz - 0.007069140672683716),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, maxz - 0.00719776377081871),
                    (minx + 0.0074254871578887105, miny + 0.000937597593292594, maxz - 0.007069140672683716),
                    (minx + 0.007554110663477331, miny + 0.000937597593292594, maxz - 0.006758600473403931),
                    (minx + 0.0074254871578887105, miny + 0.000937597593292594, maxz - 0.0064480602741241455),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.0054146647453308105),
                    (minx + 0.006164627615362406, miny + 0.0008078569080680609, maxz - 0.00580829381942749),
                    (minx + 0.0057710278779268265, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (minx + 0.006164627615362406, miny + 0.0008078569080680609, maxz - 0.007708907127380371),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.008102551102638245),
                    (maxx - 0.007876764051616192, miny + 0.0008078569080680609, maxz - 0.007708907127380371),
                    (maxx - 0.007483118446543813, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (maxx - 0.007876764051616192, miny + 0.0008078569080680609, maxz - 0.00580829381942749),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.006059680134057999),
                    (minx + 0.006620732950977981, miny + 0.0008078569080680609, maxz - 0.006264369934797287),
                    (minx + 0.006416012765839696, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (minx + 0.006620732950977981, miny + 0.0008078569080680609, maxz - 0.0072528161108493805),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.0074575357139110565),
                    (minx + 0.0076091475784778595, miny + 0.0008078569080680609, maxz - 0.0072528161108493805),
                    (minx + 0.007813852455001324, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (minx + 0.0076091475784778595, miny + 0.0008078569080680609, maxz - 0.006264369934797287),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.006319437175989151),
                    (minx + 0.006804424105212092, miny + 0.0008078569080680609, maxz - 0.0064480602741241455),
                    (minx + 0.00667576992418617, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (minx + 0.006804424105212092, miny + 0.0008078569080680609, maxz - 0.007069140672683716),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, maxz - 0.00719776377081871),
                    (minx + 0.0074254871578887105, miny + 0.0008078569080680609, maxz - 0.007069140672683716),
                    (minx + 0.007554110663477331, miny + 0.0008078569080680609, maxz - 0.006758600473403931),
                    (minx + 0.0074254871578887105, miny + 0.0008078569080680609, maxz - 0.0064480602741241455),
                    (minx + 0.0074254871578887105, miny + 0.0008078569080680609, minz + 0.007765233516693115),
                    (minx + 0.007554110663477331, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (minx + 0.0074254871578887105, miny + 0.0008078569080680609, minz + 0.007144153118133545),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.007015526294708252),
                    (minx + 0.006804424105212092, miny + 0.0008078569080680609, minz + 0.007144153118133545),
                    (minx + 0.00667576992418617, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (minx + 0.006804424105212092, miny + 0.0008078569080680609, minz + 0.007765233516693115),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.007893860340118408),
                    (minx + 0.0076091475784778595, miny + 0.0008078569080680609, minz + 0.007948920130729675),
                    (minx + 0.007813852455001324, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (minx + 0.0076091475784778595, miny + 0.0008078569080680609, minz + 0.006960481405258179),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.006755754351615906),
                    (minx + 0.006620732950977981, miny + 0.0008078569080680609, minz + 0.006960481405258179),
                    (minx + 0.006416012765839696, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (minx + 0.006620732950977981, miny + 0.0008078569080680609, minz + 0.007948920130729675),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.00815361738204956),
                    (maxx - 0.007876764051616192, miny + 0.0008078569080680609, minz + 0.00840499997138977),
                    (maxx - 0.007483118446543813, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (maxx - 0.007876764051616192, miny + 0.0008078569080680609, minz + 0.00650438666343689),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.006110742688179016),
                    (minx + 0.006164627615362406, miny + 0.0008078569080680609, minz + 0.00650438666343689),
                    (minx + 0.0057710278779268265, miny + 0.0008078569080680609, minz + 0.00745469331741333),
                    (minx + 0.006164627615362406, miny + 0.0008078569080680609, minz + 0.00840499997138977),
                    (minx + 0.007114947948139161, miny + 0.0008078569080680609, minz + 0.00879862904548645),
                    (minx + 0.0074254871578887105, miny + 0.000937597593292594, minz + 0.007765233516693115),
                    (minx + 0.007554110663477331, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (minx + 0.0074254871578887105, miny + 0.000937597593292594, minz + 0.007144153118133545),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.007015526294708252),
                    (minx + 0.006804424105212092, miny + 0.000937597593292594, minz + 0.007144153118133545),
                    (minx + 0.00667576992418617, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (minx + 0.006804424105212092, miny + 0.000937597593292594, minz + 0.007765233516693115),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.007893860340118408),
                    (minx + 0.0076091475784778595, miny + 0.000937597593292594, minz + 0.007948920130729675),
                    (minx + 0.007813852455001324, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (minx + 0.0076091475784778595, miny + 0.000937597593292594, minz + 0.006960481405258179),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.006755754351615906),
                    (minx + 0.006620732950977981, miny + 0.000937597593292594, minz + 0.006960481405258179),
                    (minx + 0.006416012765839696, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (minx + 0.006620732950977981, miny + 0.000937597593292594, minz + 0.007948920130729675),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.00815361738204956),
                    (maxx - 0.007876764051616192, miny + 0.000937597593292594, minz + 0.00840499997138977),
                    (maxx - 0.007483118446543813, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (maxx - 0.007876764051616192, miny + 0.000937597593292594, minz + 0.00650438666343689),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.006110742688179016),
                    (minx + 0.006164627615362406, miny + 0.000937597593292594, minz + 0.00650438666343689),
                    (minx + 0.0057710278779268265, miny + 0.000937597593292594, minz + 0.00745469331741333),
                    (minx + 0.006164627615362406, miny + 0.000937597593292594, minz + 0.00840499997138977),
                    (minx + 0.007114947948139161, miny + 0.000937597593292594, minz + 0.00879862904548645),
                    (maxx - 0.0074195414781570435, miny + 0.0008257024455815554, minz + 0.008862189948558807),
                    (maxx - 0.006836557062342763, miny + 0.0008257024455815554, minz + 0.00745469331741333),
                    (maxx - 0.0074195414781570435, miny + 0.0008257024455815554, minz + 0.006047196686267853),
                    (minx + 0.007114947948139161, miny + 0.0008257024455815554, minz + 0.00546419620513916),
                    (minx + 0.0057074506767094135, miny + 0.0008257024455815554, minz + 0.006047196686267853),
                    (minx + 0.005124435992911458, miny + 0.0008257024455815554, minz + 0.00745469331741333),
                    (minx + 0.0057074506767094135, miny + 0.0008257024455815554, minz + 0.008862189948558807),
                    (minx + 0.007114947948139161, miny + 0.0008257024455815554, minz + 0.0094451904296875),
                    (maxx - 0.0074195414781570435, miny + 0.001102180453017354, minz + 0.008862189948558807),
                    (maxx - 0.006836557062342763, miny + 0.001102176494896412, minz + 0.00745469331741333),
                    (maxx - 0.0074195414781570435, miny + 0.001102176494896412, minz + 0.006047196686267853),
                    (minx + 0.007114947948139161, miny + 0.001102176494896412, minz + 0.00546419620513916),
                    (minx + 0.0057074506767094135, miny + 0.001102176494896412, minz + 0.006047196686267853),
                    (minx + 0.005124435992911458, miny + 0.001102176494896412, minz + 0.00745469331741333),
                    (minx + 0.0057074506767094135, miny + 0.001102180453017354, minz + 0.008862189948558807),
                    (minx + 0.007114947948139161, miny + 0.001102180453017354, minz + 0.0094451904296875),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.015039850026369095),
                    (maxx - 0.002014978788793087, maxy, minz + 0.015039850026369095),
                    (minx, miny + 0.0009473562240600586, minz + 0.015039850026369095),
                    (minx, miny + 0.0009473562240600586, maxz - 0.015039850026369095),
                    (minx, maxy, minz + 0.015039850026369095),
                    (maxx, maxy, maxz - 0.015039850026369095),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.015039850026369095),
                    (maxx, miny + 0.0009473562240600586, minz + 0.015039850026369095),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.015039850026369095),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, minz + 0.015039850026369095),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.015039850026369095),
                    (minx + 0.0020150020718574524, maxy, minz + 0.015039850026369095),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.015039850026369095),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, minz + 0.015039850026369095),
                    (maxx, maxy, minz + 0.015039850026369095),
                    (minx, maxy, maxz - 0.015039850026369095),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, maxz - 0.015039850026369095),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, minz + 0.015039850026369095),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, maxz - 0.015039850026369095),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, minz + 0.015039850026369095),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.020450454205274582),
                    (minx, miny + 0.0009473562240600586, maxz - 0.020450454205274582),
                    (minx, maxy, maxz - 0.020450454205274582),
                    (maxx, maxy, maxz - 0.020450454205274582),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.020450454205274582),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.020450454205274582),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.020450454205274582),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.020450454205274582),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, maxz - 0.020450454205274582),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, maxz - 0.020450454205274582),
                    (minx, miny + 0.0009473562240600586, maxz - 0.04870907962322235),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.04870907962322235),
                    (minx, maxy, maxz - 0.04870907962322235),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.04870907962322235),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.04870907962322235),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.04870907962322235),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.04870907962322235),
                    (maxx, maxy, maxz - 0.04870907962322235),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, maxz - 0.04870907962322235),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, maxz - 0.04870907962322235),
                    (maxx - 0.0027115284465253353, miny + 0.0009342432022094727, maxz - 0.020450454205274582),
                    (minx + 0.0027115517295897007, miny + 0.0009342432022094727, maxz - 0.020450454205274582),
                    (maxx - 0.0027115284465253353, miny + 0.0009342432022094727, maxz - 0.04870907962322235),
                    (minx + 0.0027115517295897007, miny + 0.0009342432022094727, maxz - 0.04870907962322235),
                    (minx, miny + 0.0009473562240600586, maxz - 0.026037774980068207),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.026037774980068207),
                    (minx, maxy, maxz - 0.026037774980068207),
                    (maxx, maxy, maxz - 0.026037774980068207),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.026037774980068207),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.026037774980068207),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.026037774980068207),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.026037774980068207),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, maxz - 0.026037774980068207),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, maxz - 0.026037774980068207),
                    (maxx - 0.0027115284465253353, miny + 0.0009342432022094727, maxz - 0.026037774980068207),
                    (minx + 0.0027115517295897007, miny + 0.0009342432022094727, maxz - 0.026037774980068207),
                    (minx, miny + 0.0009473562240600586, maxz - 0.03058292716741562),
                    (maxx - 0.002014978788793087, maxy, maxz - 0.03058292716741562),
                    (maxx, miny + 0.0009473562240600586, maxz - 0.03058292716741562),
                    (maxx - 0.002014978788793087, miny + 0.0009473562240600586, maxz - 0.03058292716741562),
                    (minx + 0.0020150020718574524, maxy, maxz - 0.03058292716741562),
                    (minx + 0.0020150020718574524, miny + 0.0009473562240600586, maxz - 0.03058292716741562),
                    (maxx, maxy, maxz - 0.03058292716741562),
                    (minx, maxy, maxz - 0.03058292716741562),
                    (maxx - 0.002014978788793087, maxy - 0.0017695352435112, maxz - 0.03058292716741562),
                    (minx + 0.0020150020718574524, maxy - 0.0017695352435112, maxz - 0.03058292716741562),
                    (maxx - 0.0027115284465253353, miny + 0.0009342432022094727, maxz - 0.03058292716741562),
                    (minx + 0.0027115517295897007, miny + 0.0009342432022094727, maxz - 0.03058292716741562),
                    (maxx - 0.004523299168795347, miny, maxz - 0.026820629835128784),
                    (minx + 0.004523322451859713, miny, maxz - 0.026820629835128784),
                    (maxx - 0.004523299168795347, miny, maxz - 0.02980007231235504),
                    (minx + 0.004523322451859713, miny, maxz - 0.02980007231235504)]

        # Faces
        myfaces = [(28, 8, 0, 20), (174, 167, 12, 15), (19, 4, 9, 26), (173, 162, 8, 28), (10, 25, 17, 1),
                (12, 29, 21, 3), (29, 28, 20, 21), (164, 171, 25, 10), (171, 161, 24, 25), (7, 18, 27, 11),
                (18, 19, 26, 27), (167, 169, 29, 12), (169, 173, 28, 29), (32, 40, 47, 39), (39, 47, 46, 38),
                (38, 46, 45, 37), (37, 45, 44, 36), (36, 44, 43, 35), (35, 43, 42, 34), (34, 42, 41, 33),
                (33, 41, 40, 32), (68, 92, 84, 60), (55, 63, 62, 54), (67, 91, 92, 68), (53, 61, 60, 52),
                (56, 80, 72, 48), (51, 59, 58, 50), (66, 90, 82, 58), (49, 57, 56, 48), (69, 93, 94, 70),
                (63, 71, 70, 62), (62, 86, 78, 54), (61, 69, 68, 60), (71, 95, 88, 64), (59, 67, 66, 58),
                (60, 84, 76, 52), (57, 65, 64, 56), (65, 66, 67, 68, 69, 70, 71, 64), (72, 80, 87, 79), (78, 86, 85, 77),
                (76, 84, 83, 75), (74, 82, 81, 73), (80, 88, 95, 87), (86, 94, 93, 85), (84, 92, 91, 83),
                (82, 90, 89, 81), (65, 89, 90, 66), (70, 94, 86, 62), (49, 73, 81, 57), (64, 88, 80, 56),
                (48, 55, 79, 72), (51, 75, 83, 59), (54, 53, 77, 78), (53, 77, 85, 61), (57, 81, 89, 65),
                (52, 51, 75, 76), (55, 79, 87, 63), (59, 83, 91, 67), (50, 49, 73, 74), (61, 85, 93, 69),
                (63, 87, 95, 71), (58, 82, 74, 50), (133, 109, 117, 141), (128, 104, 96, 120), (130, 106, 98, 122),
                (141, 142, 118, 117), (132, 108, 100, 124), (136, 112, 104, 128), (139, 140, 116, 115),
                (134, 110, 102, 126),
                (138, 114, 106, 130), (137, 138, 114, 113), (140, 116, 108, 132), (143, 136, 112, 119),
                (127, 103, 111, 135),
                (142, 118, 110, 134), (121, 97, 105, 129), (126, 102, 101, 125), (109, 101, 102, 110),
                (107, 99, 100, 108),
                (105, 97, 98, 106), (111, 103, 96, 104), (117, 109, 110, 118), (115, 107, 108, 116),
                (113, 105, 106, 114),
                (119, 111, 104, 112), (126, 125, 124, 123, 122, 121, 120, 127), (134, 126, 127, 135),
                (131, 107, 115, 139),
                (132, 124, 125, 133),
                (120, 96, 103, 127), (130, 122, 123, 131), (129, 105, 113, 137),
                (128, 120, 121, 129), (122, 98, 97, 121),
                (142, 134, 135, 143), (125, 101, 109, 133), (140, 132, 133, 141),
                (135, 111, 119, 143), (138, 130, 131, 139),
                (124, 100, 99, 123), (136, 128, 129, 137), (123, 99, 107, 131),
                (158, 150, 151, 159), (157, 149, 150, 158),
                (156, 148, 149, 157), (155, 147, 148, 156), (154, 146, 147, 155),
                (153, 145, 146, 154), (152, 144, 145, 153),
                (159, 151, 144, 152), (197, 193, 167, 174), (26, 9, 163, 172),
                (196, 190, 162, 173), (9, 13, 175, 163),
                (192, 195, 171, 164), (23, 22, 160, 170), (195, 191, 161, 171),
                (11, 27, 168, 166), (193, 194, 169, 167),
                (27, 26, 172, 168), (173, 169, 177, 179), (198, 199, 179, 177),
                (168, 172, 178, 176), (196, 173, 179, 199),
                (185, 168, 176, 188), (160, 165, 183, 180), (172, 163, 181, 187),
                (170, 160, 180, 186), (166, 168, 185, 184),
                (176, 178, 189, 188), (172, 187, 189, 178), (209, 185, 188, 212),
                (222, 218, 193, 197), (221, 216, 190, 196),
                (220, 217, 191, 195), (218, 219, 194, 193), (199, 198, 202, 203),
                (221, 196, 199, 225), (169, 194, 198, 177),
                (226, 227, 203, 202), (225, 199, 203, 227), (212, 188, 200, 214),
                (188, 189, 201, 200), (219, 209, 212, 224),
                (180, 183, 207, 205), (187, 181, 204, 211), (182, 186, 210, 206),
                (186, 180, 205, 210), (184, 185, 209, 208),
                (187, 211, 213, 189), (200, 201, 215, 214), (189, 213, 215, 201),
                (224, 212, 214, 226), (211, 204, 216, 221),
                (210, 205, 217, 220), (208, 209, 219, 218), (211, 221, 225, 213),
                (227, 226, 230, 231), (213, 225, 227, 215),
                (194, 219, 224, 198), (198, 224, 226, 202), (228, 229, 231, 230),
                (215, 227, 231, 229), (226, 214, 228, 230),
                (214, 215, 229, 228), (24, 15, 2, 30), (15, 12, 3, 2), (16, 6, 14, 22), (161, 174, 15, 24),
                (6, 7, 11, 14), (8, 10, 1, 0), (21, 30, 2, 3), (19, 31, 5, 4), (4, 5, 13, 9),
                (162, 164, 10, 8), (25, 24, 30, 17), (5, 31, 23, 13), (31, 16, 22, 23), (0, 1, 17, 20),
                (20, 17, 30, 21), (7, 6, 16, 18), (18, 16, 31, 19), (40, 72, 79, 47), (47, 79, 78, 46),
                (46, 78, 77, 45), (45, 77, 76, 44), (44, 76, 75, 43), (43, 75, 74, 42), (42, 74, 73, 41),
                (41, 73, 72, 40), (79, 55, 54, 78), (77, 53, 52, 76), (75, 51, 50, 74), (73, 49, 48, 72),
                (118, 142, 143, 119), (116, 140, 141, 117), (114, 138, 139, 115),
                (112, 136, 137, 113), (150, 118, 119, 151),
                (149, 117, 118, 150), (148, 116, 117, 149), (147, 115, 116, 148),
                (146, 114, 115, 147), (145, 113, 114, 146),
                (144, 112, 113, 145), (151, 119, 112, 144), (22, 14, 165, 160),
                (191, 197, 174, 161), (14, 11, 166, 165),
                (190, 192, 164, 162), (13, 23, 170, 175), (165, 166, 184, 183),
                (163, 175, 182, 181), (175, 170, 186, 182),
                (217, 222, 197, 191), (216, 223, 192, 190), (223, 220, 195, 192),
                (183, 184, 208, 207), (181, 182, 206, 204),
                (205, 207, 222, 217), (207, 208, 218, 222), (204, 206, 223, 216), (206, 210, 220, 223)]

        mesh = bpy.data.meshes.new(objname)
        myobject = bpy.data.objects.new(objname, mesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mesh.from_pydata(myvertex, [], myfaces)
        mesh.update(calc_edges=True)

        # Create materials
        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            plastic = create_diffuse_material("Plastic_Handle_material", False, 0.01, 0.01, 0.01, 0.082, 0.079, 0.02, 0.01)
            set_material(myobject, plastic)

        return myobject


# ------------------------------------------------------------------------------
# Create rectangular sill
#
# objName: Object name
# x: size x axis
# y: size y axis
# z: size z axis
# mat: material flag
# ------------------------------------------------------------------------------
    def create_sill(self,objname, x, y, z, mat):
        myvertex = [(-x / 2, 0, 0.0),
                    (-x / 2, y, 0.0),
                    (x / 2, y, 0.0),
                    (x / 2, 0, 0.0),
                    (-x / 2, 0, -z),
                    (-x / 2, y, -z),
                    (x / 2, y, -z),
                    (x / 2, 0, -z)]

        myfaces = [(0, 1, 2, 3), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (5, 6, 7, 4), (0, 4, 7, 3)]

        mesh = bpy.data.meshes.new(objname)
        myobject = bpy.data.objects.new(objname, mesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mesh.from_pydata(myvertex, [], myfaces)
        mesh.update(calc_edges=True)

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            mymat = create_diffuse_material("Sill_material", False, 0.8, 0.8, 0.8)
            set_material(myobject, mymat)

        return myobject


    # ------------------------------------------------------------------------------
    # Create blind box
    #
    # objName: Object name
    # x: size x axis
    # y: size y axis
    # z: size z axis
    # mat: material flag
    # ------------------------------------------------------------------------------
    def create_blind_box(self,objname, x, y, z):
        myvertex = [(-x / 2, 0, 0.0),
                    (-x / 2, y, 0.0),
                    (x / 2, y, 0.0),
                    (x / 2, 0, 0.0),
                    (-x / 2, 0, z),
                    (-x / 2, y, z),
                    (x / 2, y, z),
                    (x / 2, 0, z)]

        myfaces\
            = [(0, 1, 2, 3), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (5, 6, 7, 4), (0, 4, 7, 3)]

        mesh = bpy.data.meshes.new(objname)
        myobject = bpy.data.objects.new(objname, mesh)

        myobject.location = bpy.context.scene.cursor.location
        bpy.context.collection.objects.link(myobject)

        mesh.from_pydata(myvertex, [], myfaces)
        mesh.update(calc_edges=True)

        return myobject


    # ------------------------------------------------------------------------------
    # Create blind rails
    #
    # objName: Name for the new object
    # sX: Size in X axis
    # sZ: Size in Z axis
    # pX: position X axis
    # pY: position Y axis
    # pZ: position Z axis
    # mat: Flag for creating materials
    # matdata: Aluminum material
    # blind_rail: distance of the rail
    # ------------------------------------------------------------------------------
    def create_blind_rail(self,objname, sx, sz, px, py, pz, mat, matdata, blind_rail):
        myvertex = []
        myfaces = []
        sideb = 0.04
        space = 0.012  # blind is 10 mm thick
        thicka = 0.002  # aluminum thickness
        thickb = 0.002  # aluminum thickness

        for x in (-sx / 2, sx / 2):
            for z in (0, sz):
                myvertex.extend([(x, 0, z),
                                (x, blind_rail, z),
                                (x + sideb, blind_rail, z),
                                (x + sideb, blind_rail - thicka, z),
                                (x + thickb, blind_rail - thicka, z),
                                (x + thickb, blind_rail - thicka - space, z),
                                (x + sideb, blind_rail - thicka - space, z),
                                (x + sideb, blind_rail - thicka - space - thicka, z),
                                (x + thickb, blind_rail - thicka - space - thicka, z),
                                (x + thickb, 0, z)])

            # reverse
            thickb *= -1
            sideb *= -1

        # Faces
        myfaces.extend([(31, 30, 20, 21), (32, 31, 21, 22), (33, 32, 22, 23), (37, 36, 26, 27), (35, 34, 24, 25),
                        (26, 36, 35, 25), (37, 27, 28, 38), (33, 23, 24, 34), (39, 38, 28, 29), (37, 38, 35, 36),
                        (31, 32, 33, 34), (31, 34, 39, 30), (21, 24, 23, 22), (27, 26, 25, 28), (21, 20, 29, 24),
                        (11, 1, 0, 10), (12, 2, 1, 11), (13, 14, 4, 3), (12, 13, 3, 2), (17, 7, 6, 16),
                        (16, 6, 5, 15), (14, 15, 5, 4), (17, 18, 8, 7), (19, 9, 8, 18), (17, 16, 15, 18),
                        (11, 14, 13, 12), (11, 10, 19, 14), (7, 8, 5, 6), (2, 3, 4, 1), (1, 4, 9, 0)])

        mymesh = bpy.data.meshes.new(objname)
        myblind = bpy.data.objects.new(objname, mymesh)

        myblind.location[0] = px
        myblind.location[1] = py
        myblind.location[2] = pz
        bpy.context.collection.objects.link(myblind)

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            set_material(myblind, matdata)

        return myblind


    # ------------------------------------------------------------------------------
    # Create blind estructure
    #
    # objName: Name for the new object
    # sX: Size in X axis
    # sY: Size in Y axis
    # sZ: Size in Z axis
    # pX: position X axis
    # pY: position Y axis
    # pZ: position Z axis
    # mat: Flag for creating materials
    # blind_ratio: extension factor
    # ------------------------------------------------------------------------------
    def create_blind(self,objname, sx, sz, px, py, pz, mat, blind_ratio):
        myvertex = []
        myfaces = []
        v = 0
        h = 0.05
        railgap = 0.005
        # calculate total pieces
        pieces = int((sz * (blind_ratio / 100)) / h)
        if pieces * h < sz:
            pieces += 1

        z = h
        for p in range(pieces):
            for x in (-sx / 2, sx / 2):
                myvertex.extend([(x, 0, z),
                                (x, 0, z + h - railgap),
                                (x, 0.002, z + h - railgap),
                                (x, 0.002, z + h),
                                (x, 0.008, z + h),
                                (x, 0.008, z + h - railgap),
                                (x, 0.01, z + h - railgap),
                                (x, 0.01, z)])

            z -= h
            # Faces
            myfaces.extend([(v + 15, v + 7, v + 6, v + 14), (v + 7, v + 15, v + 8, v + 0),
                            (v + 9, v + 1, v + 0, v + 8),
                            (v + 10, v + 2, v + 1, v + 9), (v + 13, v + 14, v + 6, v + 5),
                            (v + 13, v + 5, v + 4, v + 12), (v + 10, v + 11, v + 3, v + 2),
                            (v + 4, v + 3, v + 11, v + 12)])
            v = len(myvertex)

        mymesh = bpy.data.meshes.new(objname)
        myblind = bpy.data.objects.new(objname, mymesh)

        myblind.location[0] = px
        myblind.location[1] = py
        myblind.location[2] = pz
        bpy.context.collection.objects.link(myblind)

        mymesh.from_pydata(myvertex, [], myfaces)
        mymesh.update(calc_edges=True)

        myblind.lock_location = (True, True, False)  # only Z axis

        if mat and bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE'}:
            mat = create_diffuse_material("Blind_plastic_material", False, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.15)
            set_material(myblind, mat)

        return myblind
        
# Default Window Usage
ObjectProp_window={
    'width':1.20,
    'depth':0.10,
    'height':1,
    'r':0,
    'external':True,
    'frame':0.01,
    'frame_L':0.06,
    'wf':0.05,
    'leafratio':0.50,
    'opentype':1,
    'handle':True,
    'sill':True,
    'sill_thickness':0.01,
    'sill_back':0.0,
    'sill_front':0.12,
    'blind':False,
    'blind_box':True,
    'blind_height':0.12,
    'blind_back':0.002,
    'blind_rail':0.10,
    'blind_ratio':20,
    'crt_mat':True}

''' 
INFO on Variable Usage 

width: FloatProperty(
            name='Width',
            min=0.20, max=50,
            default=1.20, precision=3,
            description='window width',
            update=update_object,
            )
    depth: FloatProperty(
            name='Depth',
            min=0.07, max=1,
            default=0.10, precision=3,
            description='window depth',
            update=update_object,
            )
    height: FloatProperty(
            name='Height',
            min=0.20, max=50,
            default=1, precision=3,
            description='window height',
            update=update_object,
            )
    r: FloatProperty(
            name='Rotation', min=0, max=360, default=0, precision=1,
            description='Window rotation',
            update=update_object,
            )

    external: BoolProperty(
            name="External frame",
            description="Create an external front frame",
            default=True,
            update=update_object,
            )
    frame: FloatProperty(
            name='External Frame',
            min=0.001, max=1,
            default=0.01, precision=3,
            description='External Frame size',
            update=update_object,
            )

    frame_L: FloatProperty(
            name='Frame',
            min=0.02, max=1,
            default=0.06, precision=3,
            description='Frame size',
            update=update_object,
            )
    wf: FloatProperty(
            name='WinFrame',
            min=0.001, max=1,
            default=0.05, precision=3,
            description='Window Frame size',
            update=update_object,
            )
    leafratio: FloatProperty(
            name='Leaf ratio',
            min=0.001, max=0.999,
            default=0.50,
            precision=3,
            description='Leaf thickness ratio',
            update=update_object,
            )
    opentype: EnumProperty(
            items=(
                ('1', "Rail window", ""),
                ('2', "Two leaf", ""),
                ('3', "Right leaf", ""),
                ('4', "Left leaf", "")),
            name="Type",
            description="Defines type of window",
            update=update_object,
            )
    handle: BoolProperty(
            name="Create handles",
            description="Create default handle to the leaf",
            default=True,
            update=update_object,
            )

    sill: BoolProperty(
            name="Sill",
            description="Add sill to window",
            default=True,
            update=update_object,
            )
    sill_thickness: FloatProperty(
            name='Thickness',
            min=0, max=50,
            default=0.01, precision=3,
            description='Sill thickness',
            update=update_object,
            )
    sill_back: FloatProperty(
            name='Back',
            min=0, max=10,
            default=0.0, precision=3,
            description='Extrusion in back side',
            update=update_object,
            )
    sill_front: FloatProperty(
            name='Front',
            min=0, max=10,
            default=0.12, precision=3,
            description='Extrusion in front side',
            update=update_object,
            )

    blind: BoolProperty(
            name="Blind",
            description="Create an external blind",
            default=False,
            update=update_object,
            )
    blind_box: BoolProperty(
            name="Blind box", description="Create a box over frame for blind",
            default=True,
            update=update_object,
            )
    blind_height: FloatProperty(
            name='Height',
            min=0.001, max=10,
            default=0.12, precision=3,
            description='Blind box height',
            update=update_object,
            )
    blind_back: FloatProperty(
            name='Back',
            min=0.001, max=10,
            default=0.002, precision=3,
            description='Extrusion in back side',
            update=update_object,
            )
    blind_rail: FloatProperty(
            name='Separation',
            min=0.001, max=10,
            default=0.10, precision=3,
            description='Separation from frame',
            update=update_object,
            )
    blind_ratio: IntProperty(
            name='Extend',
            min=0, max=100,
            default=20,
            description='% of extension (100 full extend)',
            update=update_object,
            )

    # Materials
    crt_mat: BoolProperty(
            name="Create default Cycles materials",
            description="Create default materials for Cycles render",
            default=True,
            update=update_object,
            )
'''

# Default Door Props 
ObjectProp_door={
    'frame_width': 1 ,  
    'frame_height': 2.1,
    'frame_thick': 0.18, 
    'frame_size': 0.08, 
    'crt_mat': True, 
    'factor': 0.5, 
    'r': 1, 
    'openside':2,
    'model': 3,
    'handle': 2 }

'''
----USAGE of Variables----

name='Frame width',
min=0.25, max=10,
default=1, precision=2,
description='Doorframe width', update=self.update_object,

name='Frame height',
min=0.25, max=10,
default=2.1, precision=2,
description='Doorframe height', update=self.update_object,

name='Frame thickness',
min=0.05, max=0.50,
default=0.08, precision=2,
description='Doorframe thickness', update=self.update_object,

name='Frame size',
min=0.05, max=0.25,
default=0.08, precision=2,
description='Doorframe size', update=self.update_object,

name="Crt Mat",
description="Create default materials for Cycles render",
default=True,
update=self.update_object,

name='Factor',
min=0.2, max=1,
default=0.5, precision=3, description='Door ratio',
update=self.update_object,
)   

name='Rotation', min=0, max=360,
default=0, precision=1,
description='Door rotation', update=self.update_object,
)

'name':"Open side",
'items':(
    ('1', "Right open", ""),
    ('2', "Left open", ""),
    ('3', "Both sides", ""),
    ),
'description':"Defines the direction for opening the door",
'update':'self.update_object'

'name':"Model",
'items':(
    ('1', "Model 01", ""),
    ('2', "Model 02", ""),
    ('3', "Model 03", ""),
    ('4', "Model 04", ""),
    ('5', "Model 05", "Glass"),
    ('6', "Model 06", "Glass"),
    ),
'description':"Door model",
'update':'self.update_object'

'name':"Handle",
'items':(
    ('1', "Handle 01", ""),
    ('2', "Handle 02", ""),
    ('3', "Handle 03", ""),
    ('4', "Handle 04", ""),
    ('0', "None", ""),
    ),
'description':"Handle model",
'update':'self.update_object'}
'''
'''
# Door Create
m = DoorMake(ObjectProperties_door,'Door1')
m.execute()
m.ObjectProp['frame_height'] =4
m.name ='Door_height'
m.execute()
#m.ObjectProp['frame_height']=4
#m.name = 'Door2'
#m.execute()

w = WindowMake(ObjectProp_window)
w.execute()
'''