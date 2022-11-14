import os
import random
import config
import FloorplanToSTL as stl

direct = '/home/ubuntu/dev/Floorplan_2/MinkowskiEngine/CubiCasa5k/data/cubicasa5k/'
choose_frm = [] 
choose_frm += [direct+'colorful/'+i for i in os.listdir(direct + 'colorful')]
choose_frm += [direct+'high_quality_architectural/'+i for i in os.listdir(direct + 'high_quality_architectural')]
choose_frm += [direct+'high_quality/'+i for i in os.listdir(direct + 'high_quality')]

#Trial 1 seed 10
#Trial 2 seed 11
#Trial 3 seed 12
#Trial 4 seed 13
#Trial 5 seed 14s
#Trail 6 seed 15 no Annotation Training_Data_4
#Trail 7 seed 16 Blocky Annotation
#Trail 8 seed 17 Blocky Annotation
#Trail 9 seed 18 Blocky Annotation
#Trail 10 seed 19 Blocky Annotation
# 83 -> /home/ubuntu/dev/Floorplan_2/MinkowskiEngine/CubiCasa5k/data/cubicasa5k/high_quality_architectural/10006/F1_scaled.png
# Latest /home/ubuntu/dev/Floorplan_2/MinkowskiEngine/CubiCasa5k/data/cubicasa5k/high_quality_architectural/24/F1_scaled.png

random.seed(25)
chosen = random.sample(choose_frm, 1)

complete = 0
for j,i in enumerate(chosen):
    if j + 1 >complete:
        img_path = i + '/F1_scaled.png'
        svg_path = i + '/model.svg'
        print(img_path)
        try:
            stl.createFloorPlanPointCloud_svg(image_path = img_path, target_path = config.target_path,svg_path = svg_path, calc_an = True)
        except Exception as e:
            print(e)
        with open("Completion_log_.txt" , 'w') as f:
            f.write("Finished "+str(j+1)+" FloorPlan")
            f.write('\n')

            
            
