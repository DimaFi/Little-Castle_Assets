import bpy
bpy.ops.wm.open_mainfile(filepath=r'E:/Games_Develop/CozySettlement/Art/House_Cottage_A/Source/Yard/v011/Modules/SM_StoneWall_A/SM_StoneWall_A.blend')
for o in bpy.data.objects:
 if o.type=='MESH': print(o.name,len(o.data.vertices),len(o.data.polygons),list(o.dimensions),[(m.type,getattr(m,'segments',0)) for m in o.modifiers])
