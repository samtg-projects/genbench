"""Minimal numpy gaussian-splat renderer for look development (ticket 1077).

Splats: pos (N,3), axes (N,3,3) rows = unit axes, scale (N,3), color (N,3) in 0..1, opacity (N,).
Render is front-to-back alpha compositing, fully vectorised: every splat emits a
fixed window of fragments, fragments are stably sorted by pixel (splats are
pre-sorted by depth), and transmittance is a segmented cumprod in log space.
"""
import numpy as np


def look_at(eye, target, up=(0, 1, 0)):
    eye, target, up = map(lambda v: np.asarray(v, float), (eye, target, up))
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    # camera looks down +z in view space, y down in image
    R = np.stack([r, -u, f])
    return R, -R @ eye


def project(sp, R, t, f_px, W, H):
    p = sp["pos"] @ R.T + t
    z = p[:, 2]
    keep = z > 0.05
    x = f_px * p[:, 0] / z + W / 2
    y = f_px * p[:, 1] / z + H / 2
    # 3D covariance: sum_i s_i^2 a_i a_i^T, rotated to view
    A = sp["axes"] * sp["scale"][:, :, None]          # (N,3,3) scaled axes
    S3 = np.einsum("nki,nkj->nij", A, A)
    S3 = R @ S3 @ R.T
    J = np.zeros((len(z), 2, 3))
    J[:, 0, 0] = f_px / z
    J[:, 0, 2] = -f_px * p[:, 0] / z**2
    J[:, 1, 1] = f_px / z
    J[:, 1, 2] = -f_px * p[:, 1] / z**2
    S2 = J @ S3 @ J.transpose(0, 2, 1)
    return x, y, z, S2, keep


def render(sp, R, t, f_px, W, H, bg, hard=False, min_px=0.0, win=None,
           alpha_cut=1.0 / 255):
    x, y, z, S2, keep = project(sp, R, t, f_px, W, H)
    S2 = S2 + np.eye(2) * (min_px ** 2)      # dilation: splats never vanish below a pixel
    col, op = sp["color"], sp["opacity"]
    kk = sp.get("k")                     # per-splat falloff: 0 = gaussian, 1 = stroke (super-gaussian)
    # cull off-screen and sort front to back
    rad = 3.0 * np.sqrt(np.maximum(S2[:, 0, 0], S2[:, 1, 1]))
    keep &= (x + rad > 0) & (x - rad < W) & (y + rad > 0) & (y - rad < H)
    idx = np.nonzero(keep)[0]
    idx = idx[np.argsort(z[idx], kind="stable")]
    x, y, S2, col, op, rad = x[idx], y[idx], S2[idx], col[idx], op[idx], rad[idx]
    if kk is not None:
        kk = kk[idx]

    det = S2[:, 0, 0] * S2[:, 1, 1] - S2[:, 0, 1] ** 2
    ia = S2[:, 1, 1] / det
    ib = -S2[:, 0, 1] / det
    ic = S2[:, 0, 0] / det

    out = np.empty((H * W, 3))
    out[:] = bg
    acc_col = np.zeros((H * W, 3))
    T_final = np.ones(H * W)

    # bucket by footprint so small splats use small windows
    cap = win or 64
    r_int = np.ceil(np.clip(rad, 1, cap)).astype(int)
    frags = []
    for r in np.unique(r_int):
        sel = np.nonzero(r_int == r)[0]
        o = np.arange(-r, r + 1)
        ox, oy = np.meshgrid(o, o)
        ox, oy = ox.ravel(), oy.ravel()
        px = np.floor(x[sel])[:, None] + ox[None]
        py = np.floor(y[sel])[:, None] + oy[None]
        dx = px + 0.5 - x[sel][:, None]
        dy = py + 0.5 - y[sel][:, None]
        m = ia[sel, None] * dx * dx + 2 * ib[sel, None] * dx * dy + ic[sel, None] * dy * dy
        if hard == "mix":
            k = kk[sel, None]
            a = op[sel, None] * np.exp(-0.5 * m ** (1 + k))
        elif hard == "stroke":
            a = op[sel, None] * np.exp(-0.5 * m * m)     # super-gaussian: flat core, crisp edge
        elif hard:
            a = np.where(m < 1.0, op[sel, None], 0.0)   # hard-edged "pixel" splat
        else:
            a = op[sel, None] * np.exp(-0.5 * m)
        ok = (a >= alpha_cut) & (px >= 0) & (px < W) & (py >= 0) & (py < H)
        rows, cols_ = np.nonzero(ok)
        frags.append((sel[rows], (py[ok] * W + px[ok]).astype(np.int64),
                      np.minimum(a[ok], 0.995)))
    s = np.concatenate([f[0] for f in frags])
    pix = np.concatenate([f[1] for f in frags])
    a = np.concatenate([f[2] for f in frags])
    # order: by pixel, then by depth rank (splat index is already depth order)
    order = np.lexsort((s, pix))
    s, pix, a = s[order], pix[order], a[order]
    la = np.log1p(-a)
    cs = np.cumsum(la)
    start = np.r_[0, np.nonzero(np.diff(pix))[0] + 1]
    seg_id = np.repeat(np.arange(len(start)), np.diff(np.r_[start, len(pix)]))
    before = np.r_[0.0, cs[:-1]] - np.r_[0.0, cs][start][seg_id]
    T = np.exp(before)                 # transmittance before this fragment
    w = a * T
    np.add.at(acc_col, pix, col[s] * w[:, None])
    end = np.r_[start[1:], len(pix)] - 1
    T_final[pix[start]] = np.exp(cs[end] - np.r_[0.0, cs][start])
    out = acc_col + T_final[:, None] * np.asarray(bg)[None]
    alpha = 1 - T_final
    return out.reshape(H, W, 3), alpha.reshape(H, W)


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - 0.5


def palette_snap(img, pal, dither=0.08):
    H, W, _ = img.shape
    pal = np.asarray(pal, float)
    th = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
    v = img + th * dither
    d = ((v[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)]


def hexpal(*hs):
    return [tuple(int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)) for h in hs]


def ramp_snap(sp, ramps):
    """Band each splat's lit colour into its material ramp (dark->light), per splat."""
    out = sp["color"].copy()
    lum = sp["color"] @ [0.3, 0.59, 0.11]
    blum = np.maximum(sp["base"] @ [0.3, 0.59, 0.11], 1e-3)
    shade = np.clip(lum / blum, 0, 1.6) / 1.6
    for mid, ramp in ramps.items():
        sel = sp["mat"] == mid
        ramp = np.asarray(ramp, float)
        k = np.clip((shade[sel] * len(ramp)).astype(int), 0, len(ramp) - 1)
        out[sel] = ramp[k]
    return out


def finish_pixel(img, alpha, pal, bg, dither=0.04):
    """Unpremultiply, palette-snap the covered pixels, flat background elsewhere."""
    a = alpha[..., None]
    fg = (img - (1 - a) * np.asarray(bg)) / np.maximum(a, 1e-3)
    snapped = palette_snap(np.clip(fg, 0, 1), pal, dither)
    return np.where(a > 0.5, snapped, np.asarray(bg))
