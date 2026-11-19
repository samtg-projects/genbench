import bpy
m = bpy.data.materials["nebula"]; nt = m.node_tree
v = [n for n in nt.nodes if n.type == "PRINCIPLED_VOLUME"][0]
for l in list(v.inputs["Emission Color"].links): nt.links.remove(l)
v.inputs["Emission Color"].default_value = (1, 0, 0, 1)
for i in v.inputs: 
    if not i.is_linked and hasattr(i, "default_value"): print("DEF", i.name, getattr(i.default_value, "__len__", None) and tuple(i.default_value) or i.default_value)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath.replace("ntest", "nred"))
