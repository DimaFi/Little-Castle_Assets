"""Fixed bridge site, metres / Unity Y-up. Pure data, independent of Blender.

Local +Z = road; local +X = river downstream. Translation and yaw only.
The generator samples these same functions in world space for every chunk.
"""
import math

ASSET_ID = 'ENV_Bridge_Stone_A'
VERSION = 'v001'
HALF_LENGTH = 5.4
HALF_WIDTH = 1.8
WATER_Y = -1.30
SEED = 8102026

def smooth(a, b, v):
    t = max(0., min(1., (v-a)/(b-a)))
    return t*t*(3-2*t)

def deck_height(z):
    return 1.05 * math.cos(math.pi * min(HALF_LENGTH, abs(z)) / (2*HALF_LENGTH))**2

def channel_half_width(x):
    # Straight protected crossing, quiet meander outside bridge footprint.
    return 2.95 + .16 * smooth(2.1, 6.0, abs(x)) * math.sin(x*.8)

def terrain_height(x, z):
    d = abs(z)
    shore = channel_half_width(x)
    bed = -1.88 + .06*math.cos(x*.7)*math.cos(z*1.4)
    bank = -.18 + .18*smooth(shore+.25, 5.4, d)
    h = bed*(1-smooth(shore-.9, shore+1.4, d)) + bank*smooth(shore-.9, shore+1.4, d)
    # Both approach sockets and the central road corridor meet Y=0 exactly.
    road = (1-smooth(1.35, 2.0, abs(x)))*smooth(4.5, 5.4, d)
    return h*(1-road)

def stamp_weight(x, z):
    # Core 10 x 13 m, support 14 x 16 m; smooth first derivative at boundaries.
    return (1-smooth(5., 7., abs(x)))*(1-smooth(6.5, 8., abs(z)))

def sample_world(wx, wz, origin_x=0, origin_z=0, yaw=0, base_y=0):
    a=math.radians(yaw); c=math.cos(a); s=math.sin(a)
    dx=wx-origin_x; dz=wz-origin_z
    x=c*dx-s*dz; z=s*dx+c*dz
    return base_y+terrain_height(x,z), stamp_weight(x,z)

def contract():
    return dict(schema_version=1, asset_id=ASSET_ID, version=VERSION,
        units='metres', coordinates='Unity Y-up; road +Z; river +X',
        pivot='centre of crossing, Y=approach grade', scale=[1,1,1],
        bridge_length=10.8, bridge_width=3.78, structural_width=3.6, clear_walk_width=2.86,
        arch_opening_width=6.5, water_y=WATER_Y, deck_crown_y=1.05,
        deck_profile='1.05*cos(pi*clamp(abs(z),0,5.4)/10.8)^2',
        road_sockets=[dict(id='RoadSouth',position=[0,0,-5.4],outward=[0,0,-1]),
                      dict(id='RoadNorth',position=[0,0,5.4],outward=[0,0,1])],
        river_sockets=[dict(id='RiverIn',position=[-7,WATER_Y,0],outward=[-1,0,0]),
                       dict(id='RiverOut',position=[7,WATER_Y,0],outward=[1,0,0])],
        reserve_half_extents_xz=[7,8], protected_core_half_extents_xz=[5,6.5],
        collision='Static simplified deck mesh + side blocker meshes; not convex whole bridge',
        decoration_seed=SEED, fixed_dressing=True, accepts_nonuniform_scale=False,
        integration_status='Prepared asset/data contract. Unity generator NOT wired.',
        terrain_rule='Sample target height/weight in world coordinates, blend once after river carving and before slopes/navigation/scatter. Reserve complete support rectangle. Reconcile river water and road elevation at outer sockets; do not overlay two water surfaces.',
        placement_rule='Macro plan chooses compatible crossing, translation/yaw/base elevation only. Bend road and river to perpendicular sockets. Reject overlapping stamps, waterfalls, extreme grades and insufficient room. Never stretch the mesh to requiredSpan.',
        persistence='Store stableId, archetypeId, contractVersion, origin, yaw, baseElevation. Dressing stays fixed independently of world seed. Streaming ownership belongs to one stable site ID; terrain samples across all touched chunks.',
        world_presence='Generator integration must guarantee at least one compatible crossing per finite map or explicitly retry the deterministic macro plan. Asset preparation alone does not enforce this.',
        height_grid=dict(min_x=-7,min_z=-8,step=.5,nx=29,nz=33,
            heights=[[round(terrain_height(-7+i*.5,-8+j*.5),6) for i in range(29)] for j in range(33)],
            weights=[[round(stamp_weight(-7+i*.5,-8+j*.5),6) for i in range(29)] for j in range(33)]))

def validate():
    for z in [-5.4,5.4]:
        assert abs(deck_height(z))<1e-8
        assert abs(terrain_height(0,z))<1e-8
    for a in range(-16,17):
        assert stamp_weight(7,a*.5)==0
        assert stamp_weight(-7,a*.5)==0
    for a in range(-14,15):
        assert stamp_weight(a*.5,8)==0
        assert stamp_weight(a*.5,-8)==0
    # Reconstruct points from two independent chunk-local coordinates, including negatives.
    for yaw in [0,37,90,180,270]:
        for edge in [-32,0,32]:
            for k in range(-16,17):
                left=sample_world((edge-32)+32,k*.5,-17,-9,yaw,4.25)
                right=sample_world(edge+0,k*.5,-17,-9,yaw,4.25)
                assert left==right
    return dict(endpoints_match=True,zero_weight_outer_border=True,
                negative_coordinates_and_yaw_seams=True,deterministic=True)

if __name__=='__main__':
    print(validate())
