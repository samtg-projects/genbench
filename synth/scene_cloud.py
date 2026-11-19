# Pathway D (task 1357's sibling, doc 661): build a procedural cumulus cloud as a volume in an empty scene and save it.
# blender -b --factory-startup -P scene_cloud.py -- <out.blend> [seed]
import bpy, sys, math
argv = sys.argv[sys.argv.index("--") + 1:]
out, seed = argv[0], float(argv[1]) if len(argv) > 1 else 0.0
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0)); cloud = bpy.context.object
cloud.name = "cloud"; cloud.scale = (3.0, 2.0, 1.6)
m = bpy.data.materials.new("cloud"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
N = nt.nodes.new; L = nt.links.new
tc = N("ShaderNodeTexCoord")
# A flattened-bottom cumulus: noise-perturbed distance from a few lobes, cut flat underneath.
mp = N("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 1.25)
L(tc.outputs["Object"], mp.inputs["Vector"])
noise = N("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"; noise.inputs["Scale"].default_value = 2.8; noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.62; noise.inputs["W"].default_value = seed
L(mp.outputs["Vector"], noise.inputs["Vector"])
lobes = []
for c in [(-0.35, 0, -0.05, 0.45), (0.25, 0.1, 0.05, 0.5), (0.0, -0.15, 0.32, 0.42), (0.55, -0.1, -0.15, 0.34), (-0.6, 0.15, -0.2, 0.3), (0.2, 0.2, 0.45, 0.28), (-0.25, -0.1, 0.4, 0.3)]:
    sub = N("ShaderNodeVectorMath"); sub.operation = "DISTANCE"; sub.inputs[1].default_value = c[:3]
    L(mp.outputs["Vector"], sub.inputs[0])
    d = N("ShaderNodeMath"); d.operation = "SUBTRACT"; d.inputs[1].default_value = c[3]; L(sub.outputs["Value"], d.inputs[0])
    lobes.append(d)
mn = lobes[0]
for d in lobes[1:]:
    s = N("ShaderNodeMath"); s.operation = "SMOOTH_MIN"; s.inputs[2].default_value = 0.25
    L(mn.outputs[0], s.inputs[0]); L(d.outputs[0], s.inputs[1]); mn = s
pert = N("ShaderNodeMath"); pert.operation = "MULTIPLY_ADD"; pert.inputs[1].default_value = 0.9; pert.inputs[2].default_value = -0.45
L(noise.outputs["Fac"], pert.inputs[0])
sd = N("ShaderNodeMath"); sd.operation = "SUBTRACT"; L(mn.outputs[0], sd.inputs[0]); L(pert.outputs[0], sd.inputs[1])
dens = N("ShaderNodeMapRange"); dens.inputs["From Min"].default_value = 0.0; dens.inputs["From Max"].default_value = -0.3
dens.inputs["To Min"].default_value = 0.0; dens.inputs["To Max"].default_value = 10.0; L(sd.outputs[0], dens.inputs["Value"])
sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
base = N("ShaderNodeMapRange"); base.inputs["From Min"].default_value = -0.42; base.inputs["From Max"].default_value = -0.30
L(sep.outputs["Z"], base.inputs["Value"])                                    # flat cloud base
mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; L(dens.outputs[0], mul.inputs[0]); L(base.outputs[0], mul.inputs[1])
vol = N("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (1, 1, 1, 1); vol.inputs["Anisotropy"].default_value = 0.6
L(mul.outputs[0], vol.inputs["Density"])
mo = N("ShaderNodeOutputMaterial"); L(vol.outputs[0], mo.inputs["Volume"])
cloud.data.materials.append(m)
sc = bpy.context.scene; sc.cycles.volume_bounces = 4
bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out)
