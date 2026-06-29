"""Step ④ — render a WHITE-MODEL (gray clay) previs video from a shot spec.

    blender -b -P build_whitemodel.py -- --shot-spec spec.json --output previs.mp4

Pure gray geometry (no textures) so the model reads volume/depth at step ⑤; the
look comes from the first-frame image. Camera interpolates start->end while
tracking lookAt. Keep moves gentle. Room: X∈[-w/2,w/2], Y∈[0,depth], Z up.
"""
import argparse, json, math, os, sys
import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--shot-spec", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args(argv)


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for b in list(c):
            if b.users == 0:
                c.remove(b)


def gray(name, v, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (v, v, v, 1.0)
    p.inputs["Roughness"].default_value = rough
    return m


def quad(name, corners, mat):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.from_pydata([Vector(c) for c in corners], [], [(0, 1, 2, 3)]); me.update()
    o.data.materials.append(mat); return o


def _rot(o, deg):
    if deg:
        o.rotation_euler = (math.radians(deg[0]), math.radians(deg[1]), math.radians(deg[2]))


def box(name, size, center, mat, rot=None):
    bpy.ops.mesh.primitive_cube_add(location=center); o = bpy.context.object
    o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _rot(o, rot)
    o.data.materials.append(mat); return o


def rock(name, size, center, mat, rot=None):
    """Irregular boulder: an icosphere scaled non-uniformly (size = full extents)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5, location=center)
    o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _rot(o, rot)
    mod = o.modifiers.new("bevel", "BEVEL"); mod.width = min(size) * 0.08; mod.segments = 1
    o.data.materials.append(mat); return o


def build_room(room, wall_mat, floor_mat):
    w, d, h = room["width"], room["depth"], room["height"]
    x = w / 2.0
    quad("Far", [(-x, d, 0), (x, d, 0), (x, d, h), (-x, d, h)], wall_mat)
    quad("Left", [(-x, 0, 0), (-x, d, 0), (-x, d, h), (-x, 0, h)], wall_mat)
    quad("Right", [(x, d, 0), (x, 0, 0), (x, 0, h), (x, d, h)], wall_mat)
    quad("Near", [(x, 0, 0), (-x, 0, 0), (-x, 0, h), (x, 0, h)], wall_mat)
    quad("Ceil", [(-x, d, h), (x, d, h), (x, 0, h), (-x, 0, h)], wall_mat)
    quad("Floor", [(-x, 0, 0), (x, 0, 0), (x, d, 0), (-x, d, 0)], floor_mat)


def main():
    args = parse_args()
    spec = json.load(open(args.shot_spec, encoding="utf-8"))
    room = spec.get("room") or {"width": 5, "depth": 5, "height": 3}
    cam = spec.get("camera") or {}
    fps = int(cam.get("fps") or 24)
    dur = float(cam.get("durationSec") or 6)

    # interior (room) or exterior (open sky) — exterior when "room" is omitted.
    exterior = spec.get("room") is None

    clear()
    wall = gray("wall", 0.62)
    floor = gray("floor", 0.50)
    obj_mat = gray("obj", 0.58)
    if not exterior:
        build_room(room, wall, floor)
    elif spec.get("ground") is not None:
        g = float(spec["ground"]); s = 400.0
        quad("Ground", [(-s, -s, g), (s, -s, g), (s, s, g), (-s, s, g)], floor)

    # objects: box (default) or rock/sphere; optional rotationDeg [x,y,z]
    for i, ob in enumerate(spec.get("objects", [])):
        size = ob.get("size") or [0.5, 0.5, 0.5]
        pos = ob.get("position") or [0, 0, size[2] / 2]
        name = ob.get("name", f"obj_{i}")
        rotd = ob.get("rotationDeg")
        shape = ob.get("shape", "box")
        if shape in ("rock", "sphere"):
            rock(name, size, pos, obj_mat, rotd)
        else:
            box(name, size, pos, obj_mat, rotd)

    # animated SUBJECT (e.g. the dragon+rider): parts (positions RELATIVE to the
    # subject origin) parented to an empty that flies along subject.path. The camera
    # can then follow it (see cameraFollow below).
    subj_spec = spec.get("subject")
    subj = None
    if subj_spec:
        subj = bpy.data.objects.new("Subject", None)
        bpy.context.collection.objects.link(subj)
        for j, part in enumerate(subj_spec.get("parts", [])):
            psize = part.get("size") or [0.5, 0.5, 0.5]
            ppos = part.get("position") or [0, 0, 0]
            pnm = part.get("name", f"part_{j}")
            protd = part.get("rotationDeg")
            pshape = part.get("shape", "box")
            o = (rock if pshape in ("rock", "sphere") else box)(pnm, psize, ppos, obj_mat, protd)
            o.parent = subj  # direct parent: child world = subj * relative

    # lighting + world
    world = bpy.data.worlds.new("W"); bpy.context.scene.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    if exterior:
        # bright sky + a strong sun so masses cast shadows and read as 3D in air
        bg.inputs["Color"].default_value = (0.55, 0.62, 0.78, 1)
        bg.inputs["Strength"].default_value = 1.0
        sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 4.0
        so = bpy.data.objects.new("Sun", sun)
        so.rotation_euler = (math.radians(55), math.radians(15), math.radians(40))
        bpy.context.collection.objects.link(so)
    else:
        bg.inputs["Color"].default_value = (0.35, 0.36, 0.4, 1)
        bg.inputs["Strength"].default_value = 0.6
        key = bpy.data.lights.new("Key", "AREA"); key.energy = 400; key.size = 3
        ko = bpy.data.objects.new("Key", key)
        ko.location = (room["width"] * 0.4, room["depth"] * 0.3, room["height"] * 1.5)
        ko.rotation_euler = (math.radians(55), 0, math.radians(20))
        bpy.context.collection.objects.link(ko)
        top = bpy.data.lights.new("Top", "AREA"); top.energy = 200; top.size = 5
        to = bpy.data.objects.new("Top", top)
        to.location = (0, room["depth"] / 2, room["height"] + 1.5)
        bpy.context.collection.objects.link(to)

    _def_look = [0, 10, 2] if exterior else [0, room["depth"], room["height"] * 0.4]
    look = bpy.data.objects.new("Look", None)
    look.location = Vector(cam.get("lookAt", _def_look))
    bpy.context.collection.objects.link(look)
    follow = spec.get("cameraFollow")
    lens = (follow or {}).get("lensMm") or cam.get("lensMm") or 28
    cd = bpy.data.cameras.new("Cam"); cd.lens = float(lens)
    co = bpy.data.objects.new("Cam", cd); bpy.context.collection.objects.link(co)
    con = co.constraints.new("TRACK_TO"); con.target = look
    con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    bpy.context.scene.camera = co

    sc = bpy.context.scene
    f0, f1 = 1, max(2, int(dur * fps))
    sc.frame_start, sc.frame_end = f0, f1

    def fr_of(t):
        return int(round(f0 + (f1 - f0) * float(t)))

    kfs = cam.get("keyframes")
    if follow and subj is not None and subj_spec.get("path"):
        # FOLLOW mode: subject flies its path; camera rides at a fixed world offset
        # and looks at the subject (+ lookAtOffset). Subject stays framed while the
        # scenery streams past — e.g. a dragon climbing from a city's foot to its top.
        off = follow.get("offset", [0, -15, 3])
        loff = follow.get("lookAtOffset", [0, 0, 0])
        for k in subj_spec["path"]:
            fr = fr_of(k.get("t", 0))
            p = k["pos"]
            subj.location = Vector(p); subj.keyframe_insert("location", frame=fr)
            rd = k.get("rotationDeg")
            if rd:
                subj.rotation_euler = (math.radians(rd[0]), math.radians(rd[1]), math.radians(rd[2]))
                subj.keyframe_insert("rotation_euler", frame=fr)
            co.location = Vector((p[0] + off[0], p[1] + off[1], p[2] + off[2]))
            co.keyframe_insert("location", frame=fr)
            look.location = Vector((p[0] + loff[0], p[1] + loff[1], p[2] + loff[2]))
            look.keyframe_insert("location", frame=fr)
        anim_targets = (co, look, subj)
    elif kfs:
        # Multi-phase camera path (subject static): dash, crane, reveal, etc.
        for k in kfs:
            fr = fr_of(k.get("t", 0))
            co.location = Vector(k["pos"]); co.keyframe_insert("location", frame=fr)
            look.location = Vector(k.get("lookAt", _def_look)); look.keyframe_insert("location", frame=fr)
        anim_targets = (co, look)
    else:
        start = cam.get("start", [-1.4, 0.6, 1.6])
        end = cam.get("end", start)
        co.location = Vector(start); co.keyframe_insert("location", frame=f0)
        co.location = Vector(end); co.keyframe_insert("location", frame=f1)
        anim_targets = (co, look)
    # easing: "sine" eases through each waypoint (good for crane/reveal); "linear"
    # = constant speed, no slow-down at intermediate keyframes (a continuous charge).
    ease = "LINEAR" if str(cam.get("easing") or "sine").lower() == "linear" else "SINE"
    for obj in anim_targets:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = ease

    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.fps = fps
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.use_file_extension = False
    sc.render.filepath = args.output
    bpy.ops.render.render(animation=True)
    print("WHITEMODEL", args.output)


if __name__ == "__main__":
    main()
