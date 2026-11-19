# Task 1357 (1): fit each video frame's camera azimuth and elevation against a trained splat, then write a dataset on the fitted poses.
# Point renderer (as thumbnail_cpu, model loaded once), both images blurred, MSE. Per frame: azimuth grid +-40 deg, elevation grid,
# then fine passes. Fitted curves are median-smoothed (window 7) so one ambiguous frame can't jump.
#   fitpose.py <src_dataset> <ply> <out_dataset>
import sys, json, math, os, shutil, numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
src, ply, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); S = 128; R = 3.0
sys.path.insert(0, str(Path.home() / "projects/nerfstudio-api")); import thumbnail_cpu as tc
c = tc._read_ply_float_columns(ply, ["x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2", "opacity", "scale_0", "scale_1", "scale_2"])
op = 1 / (1 + np.exp(-c["opacity"])); keep = op > 0.05
P = np.stack([c["x"], c["y"], c["z"]], -1)[keep].astype(np.float64)
COL = np.clip(0.5 + 0.28209479 * np.stack([c["f_dc_0"], c["f_dc_1"], c["f_dc_2"]], -1), 0, 1)[keep]
SC = np.exp(np.stack([c["scale_0"], c["scale_1"], c["scale_2"]], -1)).mean(1)[keep]
t = json.load(open(src / "transforms.json")); f = t["fl_x"] * S / t["w"]; n = len(t["frames"])
blur = lambda a: np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), float) / 255
def look(az, el):
    a, e = math.radians(az), math.radians(el); cpos = np.array([R * math.cos(e) * math.cos(a), R * math.cos(e) * math.sin(a), R * math.sin(e)])
    fw = -cpos / np.linalg.norm(cpos); rt = np.cross(fw, [0, 0, 1.]); rt /= np.linalg.norm(rt); u = np.cross(rt, fw)
    m = np.eye(4); m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = rt, u, -fw, cpos; return m
def render(az, el):
    m = look(az, el); Rc = np.stack([m[:3, 0], -m[:3, 1], -m[:3, 2]])            # OpenCV rows: right, down, forward
    cam = (P - m[:3, 3]) @ Rc.T; z = cam[:, 2]; v = z > 1e-3
    cam, z, col, sc = cam[v], z[v], COL[v], SC[v]
    ui = np.round(f * cam[:, 0] / z + S / 2).astype(int); vi = np.round(f * cam[:, 1] / z + S / 2).astype(int)
    rad = np.clip(np.round(f * sc / z), 0, 1).astype(int); U, V, C, Z = [ui], [vi], [col], [z]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        mm = rad >= 1; U.append(ui[mm] + dx); V.append(vi[mm] + dy); C.append(col[mm]); Z.append(z[mm])
    U, V, C, Z = map(np.concatenate, (U, V, C, Z)); ok = (U >= 0) & (U < S) & (V >= 0) & (V < S)
    o = np.argsort(-Z[ok]); img = np.zeros((S, S, 3)); img[V[ok][o], U[ok][o]] = C[ok][o]; return blur(img)
def ana(k):
    m = np.array(t["frames"][k]["transform_matrix"]); p = m[:3, 3]
    return math.degrees(math.atan2(p[1], p[0])), math.degrees(math.asin(p[2] / np.linalg.norm(p)))
fit = []
for k in range(n):
    gt = blur(np.asarray(Image.open(src / t["frames"][k]["file_path"]).convert("RGB").resize((S, S)), float) / 255)
    a0, e0 = ana(k); err = lambda a, e: ((render(a, e) - gt) ** 2).mean()
    a = min(np.arange(a0 - 40, a0 + 40.1, 2.5), key=lambda x: err(x, e0))
    e = min(np.arange(-10, 60.1, 5), key=lambda x: err(a, x))
    a = min(np.arange(a - 5, a + 5.1, 1), key=lambda x: err(x, e))
    e = min(np.arange(e - 4, e + 4.1, 1), key=lambda x: err(a, x))
    fit.append((k, a0, e0, a, e, err(a0, e0), err(a, e)))
    if k % 10 == 0: print(f"frame {k + 1}: analytic ({a0:.1f}, {e0:.1f}) -> fit ({a:.1f}, {e:.1f})  mse {fit[-1][5]:.4f} -> {fit[-1][6]:.4f}", flush=True)
F = np.array(fit); med = lambda x: np.array([np.median(x[max(0, i - 3):i + 4]) for i in range(len(x))])
az, el = med(F[:, 3]), med(F[:, 4])
out.mkdir(parents=True, exist_ok=True); (out / "images").mkdir(exist_ok=True)
for fr in t["frames"]:
    d = out / fr["file_path"]
    if not d.exists(): os.link(src / fr["file_path"], d)
shutil.copy(src / "init.ply", out / "init.ply")
t2 = dict(t); t2["frames"] = [{"file_path": fr["file_path"], "transform_matrix": look(az[i], el[i]).tolist()} for i, fr in enumerate(t["frames"])]
t2["synthetic"] = dict(t.get("synthetic", {}), fitted_from=str(ply), fit="per-frame az/el, median-7")
json.dump(t2, open(out / "transforms.json", "w"), indent=1)
np.savetxt(out / "fit.csv", np.column_stack([F, az, el]), delimiter=",", fmt="%.4f",
           header="k,az_analytic,el_analytic,az_fit,el_fit,mse_analytic,mse_fit,az_smoothed,el_smoothed")
print(f"turn: analytic {F[-1,1]-F[0,1]:.1f} deg, fitted {az[-1]-az[0]:.1f}; elevation fitted {el[0]:.1f} -> {el[-1]:.1f}; "
      f"mean mse {F[:,5].mean():.4f} -> {F[:,6].mean():.4f}; az steps <0: {(np.diff(az) < 0).sum()}", flush=True)
