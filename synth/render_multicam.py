# Ticket 1114 proof: render a CC0 flower from N cameras on a sphere and write a nerfstudio/Brush transforms.json.
# blender -b <asset.blend> -P render_multicam.py -- <out_dir> <n_views> <res> <samples>
import bpy, sys, os, math, json
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
out, N, RES, SPP = argv[0], int(argv[1]), int(argv[2]), int(argv[3])
os.makedirs(os.path.join(out, "images"), exist_ok=True)
scene = bpy.context.scene

# One plant from the asset file: KEEP names it; every other mesh is hidden from the render.
keep = os.environ.get("KEEP")
for o in scene.objects:
    if o.type == "MESH" and keep and o.name != keep:
        o.hide_render = True; o.hide_set(True)
# Bounds of the kept mesh(es), in world space.
pts = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == "MESH" and not o.hide_render for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, radius = (lo + hi) / 2, (hi - lo).length / 2

# Remove any cameras or lights the asset file brought; light with a sky + sun, seen by the camera as flat grey.
for o in [o for o in scene.objects if o.type in ("CAMERA", "LIGHT")]:
    bpy.data.objects.remove(o, do_unlink=True)
world = bpy.data.worlds.new("synth") if scene.world is None else scene.world
scene.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky")
bg_light = nt.nodes.new("ShaderNodeBackground"); bg_light.inputs[1].default_value = 0.6
bg_cam = nt.nodes.new("ShaderNodeBackground"); bg_cam.inputs[0].default_value = (*[float(os.environ.get("BG", "0.18"))] * 3, 1)   # BG=0 for emissive scenes; bg_cam.inputs[1].default_value = 1.0
lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader"); wo = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(sky.outputs[0], bg_light.inputs[0]); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(bg_light.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], wo.inputs[0])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = float(os.environ.get("SUN", "3.0")); sun.rotation_euler = (math.radians(40), 0, math.radians(30))

scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
dev = os.environ.get("DEVICE", "GPU")                                  # DEVICE=CPU for quick unclaimed test frames
prefs.compute_device_type = "METAL" if dev == "GPU" else "NONE"; prefs.get_devices()
for d in prefs.devices: d.use = True
scene.cycles.device = dev; scene.cycles.samples = SPP; scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = RES; scene.render.resolution_percentage = 100
# TRANSPARENT=1 renders the background as alpha 0, so the trainer learns no backdrop.
transparent = os.environ.get("TRANSPARENT") == "1"
scene.render.film_transparent = transparent
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"

cam_data = bpy.data.cameras.new("cam"); cam_data.lens_unit = "FOV"; cam_data.angle = math.radians(40)
cam = bpy.data.objects.new("cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
dist = radius / math.sin(cam_data.angle / 2) * float(os.environ.get("DIST", "0.75"))

frames = []
golden = math.pi * (3 - math.sqrt(5))
for i in range(N):
    # Fibonacci directions over elevations -15..75 degrees: a capture rig can't see under the ground either.
    zmin, zmax = (math.sin(math.radians(float(a))) for a in os.environ.get("ELEV", "-15,75").split(","))
    z = zmin + (zmax - zmin) * (i + 0.5) / N
    r = math.sqrt(1 - z * z); th = golden * i
    d = Vector((r * math.cos(th), r * math.sin(th), z))
    cam.location = center + d * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    name = f"images/r_{i:03d}.png"
    scene.render.filepath = os.path.join(out, name)
    bpy.ops.render.render(write_still=True)
    frames.append({"file_path": name, "transform_matrix": [list(row) for row in cam.matrix_world]})

f = (RES / 2) / math.tan(cam_data.angle / 2)
json.dump({"camera_angle_x": cam_data.angle, "fl_x": f, "fl_y": f, "cx": RES / 2, "cy": RES / 2, "w": RES, "h": RES,
           "camera_model": "OPENCV", "frames": frames,
           "synthetic": {"asset": bpy.data.filepath, "center": list(center), "radius": radius, "views": N, "spp": SPP, "object": keep, "dist": dist, "transparent": transparent, "elev": os.environ.get("ELEV", "-15,75"), "bg": os.environ.get("BG", "0.18")}},
          open(os.path.join(out, "transforms.json"), "w"), indent=1)
print("WROTE", len(frames), "views; radius", radius)
