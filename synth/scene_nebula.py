# Pathway D (doc 661): a procedural emissive nebula as a volume in an empty scene; splats suit soft, glowing volumes.
# blender -b --factory-startup -P scene_nebula.py -- <out.blend> [seed]
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out, seed = argv[0], float(argv[1]) if len(argv) > 1 else 0.0
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0)); neb = bpy.context.object
neb.name = "nebula"; neb.scale = (2.4, 2.4, 1.8)
m = bpy.data.materials.new("nebula"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
N = nt.nodes.new; L = nt.links.new
tc = N("ShaderNodeTexCoord")
# Shape: a thick, torn shell. Noise warps the position, distance from the centre picks the shell, a second noise tears it.
warp = N("ShaderNodeTexNoise"); warp.noise_dimensions = "4D"; warp.inputs["Scale"].default_value = 1.6; warp.inputs["Detail"].default_value = 4.0
warp.inputs["W"].default_value = seed; L(tc.outputs["Object"], warp.inputs["Vector"])
wc = N("ShaderNodeVectorMath"); wc.operation = "SUBTRACT"; wc.inputs[1].default_value = (0.5, 0.5, 0.5); L(warp.outputs["Color"], wc.inputs[0])
ws = N("ShaderNodeVectorMath"); ws.operation = "SCALE"; ws.inputs["Scale"].default_value = 0.55; L(wc.outputs[0], ws.inputs[0])
p = N("ShaderNodeVectorMath"); p.operation = "ADD"; L(tc.outputs["Object"], p.inputs[0]); L(ws.outputs[0], p.inputs[1])
ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L(p.outputs[0], ln.inputs[0])
shell = N("ShaderNodeFloatCurve"); L(ln.outputs["Value"], shell.inputs["Value"])
c = shell.mapping.curves[0]; c.points[0].location = (0.0, 0.0); c.points[1].location = (1.0, 0.0)
c.points.new(0.4, 0.1); c.points.new(0.68, 1.0); c.points.new(0.85, 0.0); shell.mapping.update()
tear = N("ShaderNodeTexNoise"); tear.noise_dimensions = "4D"; tear.inputs["Scale"].default_value = 3.5; tear.inputs["Detail"].default_value = 10.0
tear.inputs["Roughness"].default_value = 0.65; tear.inputs["W"].default_value = seed + 7.3; L(p.outputs[0], tear.inputs["Vector"])
tr = N("ShaderNodeMapRange"); tr.inputs["From Min"].default_value = 0.55; tr.inputs["From Max"].default_value = 0.7; L(tear.outputs["Fac"], tr.inputs["Value"])
dens = N("ShaderNodeMath"); dens.operation = "MULTIPLY"; L(shell.outputs[0], dens.inputs[0]); L(tr.outputs[0], dens.inputs[1])
l0 = N("ShaderNodeVectorMath"); l0.operation = "LENGTH"; L(tc.outputs["Object"], l0.inputs[0])
fall = N("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.8; fall.inputs["From Max"].default_value = 0.98
fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0; L(l0.outputs["Value"], fall.inputs["Value"])   # nothing reaches the box
df = N("ShaderNodeMath"); df.operation = "MULTIPLY"; L(dens.outputs[0], df.inputs[0]); L(fall.outputs[0], df.inputs[1])
d2 = N("ShaderNodeMath"); d2.operation = "MULTIPLY"; d2.inputs[1].default_value = 2.5; L(df.outputs[0], d2.inputs[0])
# Colour: a third noise picks along magenta - teal - amber; hotter where denser.
hue = N("ShaderNodeTexNoise"); hue.noise_dimensions = "4D"; hue.inputs["Scale"].default_value = 0.45; hue.inputs["Detail"].default_value = 0.0; hue.inputs["W"].default_value = seed + 3.1
L(p.outputs[0], hue.inputs["Vector"])
ramp = N("ShaderNodeValToRGB"); L(hue.outputs["Fac"], ramp.inputs["Fac"]); e = ramp.color_ramp.elements
e[0].position, e[0].color = 0.38, (0.9, 0.1, 0.55, 1); e[1].position, e[1].color = 0.62, (1.0, 0.55, 0.1, 1)
mid = e.new(0.5); mid.color = (0.05, 0.6, 0.8, 1)
vol = N("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.04, 0.04, 0.06, 1)      # dark dust: the glow is emission
L(d2.outputs[0], vol.inputs["Density"]); L(ramp.outputs["Color"], vol.inputs["Emission Color"])
es = N("ShaderNodeMath"); es.operation = "MULTIPLY"; es.inputs[1].default_value = 3.0; L(d2.outputs[0], es.inputs[0])
L(es.outputs[0], vol.inputs["Emission Strength"])
mo = N("ShaderNodeOutputMaterial"); L(vol.outputs[0], mo.inputs["Volume"])
neb.data.materials.append(m)
sc = bpy.context.scene; sc.cycles.volume_bounces = 2
sc.view_settings.view_transform = "Standard"                                # keep the colours saturated
bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out)
