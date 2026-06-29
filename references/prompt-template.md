# White-model-reference prompt — DIRECTOR SHOT VERSION (the required structure)

When the final video uses a Blender **white-model** video as `reference_video`, a thin
descriptive prompt is NOT enough. The prompt MUST be written like a director's shot
note with the four blocks below. This is what stops the gray blocks / low-poly facets
from bleeding into the result and what makes the references actually obeyed.

The `videoPrompt` you send to Seedance is ONE long string containing all four blocks.

---

## ① 参考规则 — label every reference and pin its ROLE

State, per reference, exactly what it is for (and what it is NOT for):

- **@首帧图 (reference_image)** = first frame + visual baseline + FINAL style. The
  final image must match its <concrete anchors: subject look, palette, materials,
  film grain, motion blur, genre texture>. List the anchors explicitly.
- **@角色图 (optional second reference_image)** = ONLY the character/subject design
  (costume, silhouette, vibe). Do **not** treat it as the first-frame composition.
- **@白膜视频 (reference_video)** = ONLY shot scheduling / composition / motion path /
  rhythm. Read it like a normal previs: strictly follow the **camera motion, the
  subject's position in frame, subject scale relationships, foreground/midground/
  background spatial layering, motion direction, action order, and overall pacing** —
  but do NOT mechanically hit second-marks.

- **CRITICAL proxy clause (never omit):** Do NOT reproduce the video's viewport/UI,
  gray-clay material, wireframe, low-poly facets, placeholder boxes, temp lighting,
  placeholder textures, preview quality, grid lines, or any software interface. Every
  blockout shape only marks a subject's **position / timing / orientation** — render
  the REAL thing in the first-frame's style, never a geometric block. Give a legend:
  e.g. "the central winged block = the dragon + rider; the faceted blocks = weathered
  floating rocks — render as real craggy rock, not polygons."

## ② 动作顺序 — beat by beat

Number the beats in order; tie each to the references ("opens on @首帧图 …", "camera
then follows @白膜视频's path …"). Be specific about what enters/happens when, and
state hard limits inline (e.g. "only one rider and one horse — no second rider").

## ③ 技术规格

Duration (~Ns), one continuous shot if wanted, ratio, fps, genre, camera handling
(handheld chase / smooth tracking / crane), motion blur, film grain, real FX (dust,
gunfire, debris), etc.

## ④ 严格不要 — strict avoid list

Composition errors (e.g. subject's body in the first frame when it shouldn't be),
extra subjects (second rider/horse/crowd), modern objects, locked-off camera, camera
pull-back, pull-out ending, **gray-model look, 3D-preview look, Blender UI elements,
low-poly/geometric blocks**, plastic feel, limb/neck distortion, etc.

---

## Worked example (western train chase — the canonical reference)

> ① 参考规则:@图片1作为首帧/画面基准/最终风格,最终须与其红色火车、荒野铁路、蓝天、
> 烟尘、胶片颗粒、运动模糊、复古西部片质感一致。@图片2仅作牛仔造型参考(黑宽檐帽、深色
> 外套、探身举枪姿态),不作第一帧构图。@视频1仅作镜头调度/构图/运动路径/节奏参考,严格
> 参考镜头运动、主体画面位置、主体比例、前/中/远景层次、运动方向、动作先后与节奏,但不
> 机械卡秒。不要参考@视频1的视口界面/灰模材质/线框/低模形状/临时灯光/占位贴图/预览画质/
> 网格/UI;视频中蓝块只代表牛仔身体出现的位置和时机,绿块只代表远处唯一骑马追逐者的位置
> 和运动方向,不生成几何方块。
> ② 动作顺序:开头以@图片1空火车画面开始,牛仔不露出;先有子弹击中红色车厢,火花弹痕白烟;
> 随后牛仔从车窗后探身(造型参考@图片2)举枪瞄远处,镜头贴火车侧面高速跟拍,按@视频1路径
> 移动。镜头随后按@视频1甩向远处铁轨旁唯一骑马追逐者(全片只一马一骑手,无第二骑手/马队);
> 骑手被击中清楚落马、马继续前冲尘土扬起。镜头继续按@视频1掠过铁路尘土与远山,再甩回火车
> 侧面,最后沿车厢向前推进逼近牛仔与红色车窗,保持贴车厢高速运动感。
> ③ 约10秒,一镜到底,4:3,60fps,西部动作片,手持追车镜头,强运动模糊,胶片颗粒,真实烟尘枪火。
> ④ 严格不要:第一帧出现牛仔身体、多个骑手、两匹马、马队、现代物体、固定机位、镜头后退、
> 结尾拉远、灰模风格、3D预览风格、Blender界面元素、低模几何块。
