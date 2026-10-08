import bpy
p=r'E:/Games_Develop/CozySettlement/Art/House_Cottage_A/Source/Roof/v018/House_Cottage_A.blend'
with bpy.data.libraries.load(p) as (a,b):print('MATERIALS',a.materials)
