"""Task 1380: stage 10 as stage 09 dried in place (a recolour of the aligned 09 splat; same pose and height).
Green (leaves, stem) -> straw/tan brown; reds and browns -> darker, desaturated umber; a little per-splat variation.
Usage: dry.py in.ply out.ply"""
import sys, numpy as np, colorsys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "hero"))
import plyload
sp = plyload.load(sys.argv[1]); c = sp["color"]; rng = np.random.default_rng(10)
r, g, b = c.T; lum = c @ [0.3, 0.59, 0.11]
green = (g > r * 1.05) & (g > b)
dry_leaf = np.stack([0.42, 0.33, 0.20], 0)[None] * (0.55 + 0.9 * lum[:, None]) * (0.85 + 0.3 * rng.random((len(c), 1)))
umber = np.stack([0.30, 0.20, 0.13], 0)[None] * (0.5 + 1.1 * lum[:, None]) * (0.85 + 0.3 * rng.random((len(c), 1)))
out = np.where(green[:, None], dry_leaf, 0.35 * c * [0.9, 0.75, 0.6] + 0.65 * umber)
sp["color"] = np.clip(out * 1.2, 0, 1)
plyload.save(sys.argv[2], sp)
print("green", int(green.sum()), "of", len(c))
