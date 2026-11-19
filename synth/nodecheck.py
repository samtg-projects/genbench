import bpy
m = bpy.data.materials["nebula"]
for n in m.node_tree.nodes:
    if n.type == "PRINCIPLED_VOLUME":
        for i in n.inputs:
            if i.is_linked: print("IN", i.name, "<-", i.links[0].from_node.type, i.links[0].from_socket.name)
    if n.type == "VALTORGB":
        print("RAMP", [(round(e.position,2), tuple(round(c,2) for c in e.color)) for e in n.color_ramp.elements])
print("VIEW", bpy.context.scene.view_settings.view_transform)
