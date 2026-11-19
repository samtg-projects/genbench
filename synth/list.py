import bpy
from mathutils import Vector
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        print("OBJ", o.name, len(o.data.polygons), tuple(round(v, 3) for v in (hi - lo)), tuple(round(v, 2) for v in (lo + hi) / 2))
