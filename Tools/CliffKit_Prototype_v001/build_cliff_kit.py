"""TEMPORARY BLENDER 4.4+ AUTHORING TOOL — not Unity runtime code.
Usage: blender -b --python build_cliff_kit.py -- --out /some/dir --seed 20261009
Generates low-cost concept cliff meshes, hike ramps and boulders with authored LODs.
Produces .blend, FBX per archetype and LOD, machine-readable catalogue.
This is NOT an approved production release: review art, footprints, scale and nav.
"""
from __future__ import annotations
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy

DEFAULT_SEED = 20261009

ARCHETYPES = [
    dict(id='Cliff_Straight_A', kind='cliff',width=16,height=6.0,depth=5,profile='straight',grass=True),
    dict(id='Cliff_Straight_B', kind='cliff',width=12,height=8.0,depth=5,profile='straight',grass=True),
    dict(id='Cliff_Convex_A',kind='cliff',width=18,height=7.0,depth=5,profile='convex',grass=True),
    dict(id='Cliff_Concave_A',kind='cliff',width=18,height=7.0,depth=5,profile='concave',grass=True),
    dict(id='Cliff_Terrace_Low',kind='cliff',width=14,height=3.5,depth=6,profile='terrace',grass=True),
    dict(id='Cliff_Terrace_High',kind='cliff',width=16,height=10.0,depth=7,profile='terrace',grass=True),
    dict(id='Cliff_End_Left',kind='cliff',width=12,height=6.0,depth=5,profile='end_left',grass=True),
    dict(id='Cliff_End_Right',kind='cliff',width=12,height=6.0,depth=5,profile='end_right',grass=True),
    dict(id='Rock_Outcrop_Large',kind='rock',width=8,height=4.0,depth=6,profile='outcrop',grass=False),
    dict(id='Rock_Outcrop_Medium',kind='rock',width=4,height=2.4,depth=3,profile='outcrop',grass=False),
    dict(id='Rock_Boulder_Small',kind='rock',width=1.7,height=1.1,depth=1.4,profile='boulder',grass=False),
    dict(id='Rock_Boulder_Large',kind='rock',width=3.6,height=2.6,depth=3.2,profile='boulder',grass=False),
    dict(id='Ramp_Hike_A',kind='ramp',width=7,height=6.5,depth=24,profile='hike',grass=True),
    dict(id='Ramp_Hike_B',kind='ramp',width=9,height=9.0,depth=32,profile='hike',grass=True),
]


def argv():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'Output')
    ap.add_argument('--textures',type=Path,default=Path(__file__).resolve().parent/'Textures')
    ap.add_argument('--seed',type=int,default=DEFAULT_SEED)
    ap.add_argument('--no-fbx',action='store_true')
    ap.add_argument('--only',nargs='*',default=[])
    a=ap.parse_args(args)
    unknown=set(a.only)-{x['id'] for x in ARCHETYPES}
    if unknown:ap.error('Unknown asset ids: '+str(sorted(unknown)))
    return a


def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        if mat.name.startswith('LC_CliffKit_'): bpy.data.materials.remove(mat)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1.0


def load_image(folder,file_name,noncolor=False):
    p=folder/file_name
    if not p.is_file():raise FileNotFoundError(f'Missing authored texture {p}; run generate_textures.py first')
    im=bpy.data.images.load(str(p.resolve()),check_existing=True)
    if noncolor:im.colorspace_settings.name='Non-Color'
    return im


def tex(nodes,folder,file_name,noncolor=False):
    n=nodes.new('ShaderNodeTexImage')
    n.image=load_image(folder,file_name,noncolor)
    n.label=file_name
    n.extension='REPEAT'
    n.interpolation='Linear'
    return n


def make_material(name,folder,moss=False):
    m=bpy.data.materials.new(name='LC_CliffKit_'+name)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');out.location=(750,0)
    bsdf=nodes.new('ShaderNodeBsdfPrincipled');bsdf.location=(450,0)
    m.node_tree.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';uv.location=(-900,-200)
    bc=tex(nodes,folder,'BaseColor.png');bc.location=(-630,200)
    rough=tex(nodes,folder,'Roughness.png',True);rough.location=(-630,-50)
    normal=tex(nodes,folder,'Normal_OpenGL.png',True);normal.location=(-630,-310)
    for t in (bc,rough,normal):m.node_tree.links.new(uv.outputs['UV'],t.inputs['Vector'])
    m.node_tree.links.new(rough.outputs['Color'],bsdf.inputs['Roughness'])
    norm=nodes.new('ShaderNodeNormalMap');norm.location=(140,-260);norm.inputs['Strength'].default_value=.50
    m.node_tree.links.new(normal.outputs['Color'],norm.inputs['Color'])
    m.node_tree.links.new(norm.outputs['Normal'],bsdf.inputs['Normal'])
    if moss:
        mask=tex(nodes,folder,'MossMask.png',True);mask.location=(-650,-580)
        m.node_tree.links.new(uv.outputs['UV'],mask.inputs['Vector'])
        mossmix=nodes.new('ShaderNodeMixRGB');mossmix.blend_type='MIX';mossmix.location=(170,200)
        mossmix.inputs['Color2'].default_value=(.205,.285,.119,1)
        m.node_tree.links.new(bc.outputs['Color'],mossmix.inputs['Color1'])
        m.node_tree.links.new(mask.outputs['Color'],mossmix.inputs['Fac'])
        m.node_tree.links.new(mossmix.outputs['Color'],bsdf.inputs['Base Color'])
    else:m.node_tree.links.new(bc.outputs['Color'],bsdf.inputs['Base Color'])
    m.diffuse_color=(.6,.55,.45,1) if moss else (.32,.46,.19,1)
    m['PROTOTYPE_ONLY']=True
    return m


def geometry_object(name,verts,polygons,face_mats,materials,uv_mode):
    mesh=bpy.data.meshes.new(name+'_Mesh')
    mesh.from_pydata(verts,[],polygons)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    for mat in materials:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='UVMap')
    for polygon,matid in zip(mesh.polygons,face_mats):
        polygon.material_index=matid
        polygon.use_smooth=False # flat faceted stone; cap gets its own smooth surfaces later
        for loopidx in polygon.loop_indices:
            v=mesh.vertices[mesh.loops[loopidx].vertex_index].co
            if uv_mode=='ramp': u,vv=v.x/3.5,v.z/3.5
            elif matid==1: u,vv=v.x/3.5,v.z/3.5
            else:
                # cliff face XY; boulders/outcrops use a stable planar material sample
                u,vv=(v.x/3.5,v.y/3.5) if abs(polygon.normal.z)>abs(polygon.normal.x) else (v.z/3.5,v.y/3.5)
            layer.data[loopidx].uv=(u,vv)
    return ob


def cliff_mesh(cfg,lod,rng,materials):
    nx,ny,ncap=[(32,15,8),(15,8,4),(7,4,2)][lod]
    width=cfg['width'];height=cfg['height'];depth=cfg['depth'];profile=cfg['profile']
    jitter=rng.uniform(-.32,.32)
    # Reproducible large wave, shared at top between wall and grassy platform.
    def values(u):
        x=(u-.5)*width
        e=.11*math.sin(u*9.3+jitter)+.055*math.sin(u*24.7+jitter)
        h=height*(1+e)
        if profile=='end_left':h*=max(.07,min(1,(u+.02)/.30))
        if profile=='end_right':h*=max(.07,min(1,(1.02-u)/.30))
        bend=0
        if profile=='convex':bend=-2.0*math.sin(math.pi*u)
        if profile=='concave':bend=2.0*math.sin(math.pi*u)
        return x,h,bend
    verts=[];faces=[];mats=[]
    def append(v):verts.append(v);return len(verts)-1
    def face(indices,mat=0):faces.append(tuple(indices));mats.append(mat)
    front=[]
    for iy in range(ny+1):
        t=iy/ny;row=[]
        for ix in range(nx+1):
            u=ix/nx;x,h,bend=values(u)
            ripple=math.sin(u*41+3*t+2*jitter)*math.sin(t*21+u*7)*(.19/(1+lod*.35))
            y=h*t + (ripple if 0<t<1 else 0)
            z=bend+(t-.4)*.8+(.16*math.sin(15*u+11*t) if 0<t<1 else 0)
            if profile=='terrace':z+=.23*math.sin(t*21)
            row.append(append((x,y,z)))
        front.append(row)
    for iy in range(ny):
        for ix in range(nx):
            a=front[iy][ix];b=front[iy][ix+1];c=front[iy+1][ix+1];d=front[iy+1][ix]
            face((a,c,b));face((a,d,c))
    cap=[front[-1]]
    for iz in range(1,ncap+1):
        t=iz/ncap;row=[]
        for ix in range(nx+1):
            u=ix/nx;x,h,bend=values(u)
            z=bend+.6+depth*t
            y=h+.13*math.sin(math.pi*t)*math.sin(12*u+2.4*t+jitter)
            row.append(append((x,y,z)))
        cap.append(row)
    for iz in range(ncap):
        for ix in range(nx):
            a,b,c,d=cap[iz][ix],cap[iz][ix+1],cap[iz+1][ix+1],cap[iz+1][ix]
            face((a,c,b),1);face((a,d,c),1)
    # End caps and backside are context-only skirts; must be hidden by terrain in Unity.
    for ix in (0,nx):
        x,h,bend=values(ix/nx)
        low=front[0][ix];upper=front[-1][ix];back=cap[-1][ix]
        bottom_back=append((x,0,bend+.6+depth))
        face((low,upper,back));face((low,back,bottom_back))
    for ix in range(nx):
        a,b=cap[-1][ix],cap[-1][ix+1]
        va,vb=verts[a],verts[b]
        ac=append((va[0],0,va[2]));bc=append((vb[0],0,vb[2]))
        face((a,bc,b));face((a,ac,bc))
    return geometry_object(cfg['id']+'_LOD'+str(lod),verts,faces,mats,materials,'cliff')


def rock_mesh(cfg,lod,rng,materials):
    segments=[16,10,7][lod]
    w=cfg['width'];h=cfg['height'];d=cfg['depth']
    radial=[rng.uniform(.84,1.13) for _ in range(segments)]
    verts=[];faces=[];mats=[]
    for yscale,rscale in ((0,.78),(.45,1.0),(.8,.64)):
        for i in range(segments):
            t=i/segments*math.tau
            rad=radial[i]*rscale
            verts.append((math.cos(t)*w*.5*rad,h*yscale,math.sin(t)*d*.5*rad))
    verts.append((rng.uniform(-.09,.09)*w,h,rng.uniform(-.09,.09)*d))
    for layer in range(2):
        for i in range(segments):
            j=(i+1)%segments;a=layer*segments+i;b=layer*segments+j
            c=(layer+1)*segments+j;didx=(layer+1)*segments+i
            faces.extend(((a,c,b),(a,didx,c)));mats.extend((0,0))
    tip=3*segments
    for i in range(segments):
        faces.append((2*segments+(i+1)%segments,2*segments+i,tip));mats.append(0)
    # Closed bottom to avoid obvious missing underside when standalone boulders are moved.
    center=len(verts);verts.append((0,0,0))
    for i in range(segments):
        faces.append((center,i,(i+1)%segments));mats.append(0)
    return geometry_object(cfg['id']+'_LOD'+str(lod),verts,faces,mats,materials,'rock')


def ramp_mesh(cfg,lod,rng,materials):
    # Ascend along local +Z. Infantry grade ~15-16 deg; not gameplay navigation!
    nx,nz=[(12,32),(7,16),(4,8)][lod]
    w=cfg['width'];length=cfg['depth'];h=cfg['height']
    verts=[];faces=[];mats=[]
    for iz in range(nz+1):
        t=iz/nz
        for ix in range(nx+1):
            u=ix/nx
            x=(u-.5)*w;z=t*length
            lateral=max(0,1-abs(u-.5)*2)
            y=h*t + math.sin(t*7.7+u*6.1)*(.075+lod*.007)*lateral*math.sin(math.pi*t)
            verts.append((x,y,z))
    for iz in range(nz):
        for ix in range(nx):
            a=iz*(nx+1)+ix;b=a+1;c=b+nx+1;d=a+nx+1
            # Rock shows at edges; green path in the middle. Hard material border is concept-only.
            mat=1 if (ix+.5)/nx>.18 and (ix+.5)/nx<.82 else 0
            faces.extend(((a,c,b),(a,d,c)));mats.extend((mat,mat))
    for ix in (0,nx):
        start=ix;end=nz*(nx+1)+ix
        v1=verts[start];v2=verts[end]
        b1=len(verts);verts.append((v1[0],-0.25,v1[2]))
        b2=len(verts);verts.append((v2[0],-0.25,v2[2]))
        faces.extend(((start,end,b2),(start,b2,b1)));mats.extend((0,0))
    return geometry_object(cfg['id']+'_LOD'+str(lod),verts,faces,mats,materials,'ramp')


def clear_selection():bpy.ops.object.select_all(action='DESELECT')


def export_lod(root,mesh,path):
    # Does not modify mesh vertex coordinates or any shared Blender file.
    prev=root.location.copy();root.location=(0,0,0)
    bpy.context.view_layer.update()
    clear_selection()
    root.select_set(True);mesh.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'EMPTY','MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,
        bake_space_transform=False,add_leaf_bones=False,path_mode='STRIP',
        mesh_smooth_type='FACE',use_mesh_modifiers=True)
    root.location=prev
    bpy.context.view_layer.update()


def main():
    a=argv();a.out=a.out.resolve();a.textures=a.textures.resolve()
    a.out.mkdir(parents=True,exist_ok=True)
    for folder in ('Rock_Limestone_A','Rock_Limestone_B','GrassCap_A'):
        if not (a.textures/folder/'BaseColor.png').is_file():
            raise SystemExit('Missing texture folder. First run generate_textures.py: '+str(a.textures))
    reset_scene()
    mats=[make_material('RockA',a.textures/'Rock_Limestone_A',True),
          make_material('RockB',a.textures/'Rock_Limestone_B',True),
          make_material('GrassCap',a.textures/'GrassCap_A',False)]
    catalogue=[]
    for index,cfg in enumerate(ARCHETYPES):
        if a.only and cfg['id'] not in a.only:continue
        rng=random.Random(f"{a.seed}:{cfg['id']}")
        root=bpy.data.objects.new(cfg['id']+'_ROOT',None)
        bpy.context.collection.objects.link(root)
        root.empty_display_type='CUBE';root.empty_display_size=.4
        root.location=((index%4)*24,0,(index//4)*38)
        rock=mats[1] if cfg['kind']=='rock' and cfg['profile']=='boulder' else mats[0]
        material_set=[rock,mats[2]]
        meshes=[]
        for lod in range(3):
            # Use stable per-asset shape noise across LODs.
            lod_rng=random.Random(f"{a.seed}:{cfg['id']}:shape")
            mesh={'cliff':cliff_mesh,'rock':rock_mesh,'ramp':ramp_mesh}[cfg['kind']](cfg,lod,lod_rng,material_set)
            mesh.parent=root
            mesh['CliffKit_Asset']=cfg['id']
            mesh['CliffKit_LOD']=lod
            if lod>0:mesh.hide_render=True
            meshes.append(mesh)
        slope_degrees=math.degrees(math.atan2(cfg['height'],cfg['depth'])) if cfg['kind']=='ramp' else None
        entry={'id':cfg['id'],'kind':cfg['kind'],'profile':cfg['profile'],
               'width_m':cfg['width'],'height_m':cfg['height'],'depth_or_length_m':cfg['depth'],
               'upper_terrain_required':cfg['kind']=='cliff',
               'render_only_not_navigation':True,'hike_ramp_grade_degrees':slope_degrees,
               'lod_triangle_counts':[sum(len(p.vertices)-2 for p in m.data.polygons) for m in meshes],
               'lod_fbx':[f'{cfg["id"]}_LOD{lod}.fbx' for lod in range(3)]}
        for k,v in entry.items():
            if k in ('id','kind','profile','width_m','height_m','depth_or_length_m','upper_terrain_required','render_only_not_navigation'):
                root[k]=v
        catalogue.append(entry)
        if not a.no_fbx:
            for lod,mesh in enumerate(meshes):export_lod(root,mesh,a.out/entry['lod_fbx'][lod])
    clear_selection()
    # Keep the authoring .blend portable, independent of absolute texture paths.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out/'CliffKit_AUTHORING.blend'))
    (a.out/'ASSET_CATALOG.json').write_text(json.dumps({'version':'proto-v001','seed':a.seed,'unit':'m','renderer':'Built-in Unity (manual import material setup)',
       'warning':'TEMPORARY BUILD OUTPUT; no nav data, terrain alignment, production LOD approval, or Unity compile',
       'assets':catalogue},indent=2)+'\n',encoding='utf-8')
    print('CLIFF_KIT_DRAFT_BUILT',len(catalogue),'out=',a.out)

if __name__=='__main__':main()
