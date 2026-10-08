import bpy,json
p=r'E:/Games_Develop/CozySettlement/Art/House_Cottage_A/Source/Openings/v007/House_Cottage_A.blend'
bpy.ops.wm.open_mainfile(filepath=p)
for o in bpy.data.objects:
 if o.type=='MESH' and ('Shared' in o.name or 'Foundation' in o.name or 'Beam' in o.name or 'Block' in o.name):
  print(o.name, len(o.data.vertices), list(o.dimensions), [(m.name,m.type) for m in o.modifiers])
