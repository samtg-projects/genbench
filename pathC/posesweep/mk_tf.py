# Task 1357: analytic turntable poses for a generated video (no COLMAP). Camera on a circle round the origin,
# angle = i * TURN / (n-1), elevation drifting EL0 -> EL1, looking at the origin, z up; nerfstudio/Brush transforms.json.
import json, math, sys, os
d, n, turn, el0, el1 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
W = 704; fov = math.radians(40); f = (W / 2) / math.tan(fov / 2); R = 3.0
def look(c):
    fwd = [-x for x in c]; l = math.sqrt(sum(x * x for x in fwd)); fwd = [x / l for x in fwd]
    up = [0, 0, 1]; rt = [fwd[1] * up[2] - fwd[2] * up[1], fwd[2] * up[0] - fwd[0] * up[2], fwd[0] * up[1] - fwd[1] * up[0]]
    l = math.sqrt(sum(x * x for x in rt)); rt = [x / l for x in rt]
    u = [rt[1] * fwd[2] - rt[2] * fwd[1], rt[2] * fwd[0] - rt[0] * fwd[2], rt[0] * fwd[1] - rt[1] * fwd[0]]
    # OpenGL camera: x right, y up, looking down -z
    return [[rt[0], u[0], -fwd[0], c[0]], [rt[1], u[1], -fwd[1], c[1]], [rt[2], u[2], -fwd[2], c[2]], [0, 0, 0, 1]]
fr = []
for i in range(n):
    t = i / (n - 1); a = math.radians(turn * t); e = math.radians(el0 + (el1 - el0) * t)
    c = [R * math.cos(e) * math.cos(a), R * math.cos(e) * math.sin(a), R * math.sin(e)]
    fr.append({"file_path": f"images/f_{i + 1:03d}.png", "transform_matrix": look(c)})
json.dump({"camera_angle_x": fov, "fl_x": f, "fl_y": f, "cx": W / 2, "cy": W / 2, "w": W, "h": W, "camera_model": "OPENCV",
           "frames": fr, "synthetic": {"analytic_turntable": True, "turn_deg": turn, "elev": [el0, el1], "radius": R}},
          open(os.path.join(d, "transforms.json"), "w"), indent=1)
print("wrote", d, n, turn)
