# Step ① breakdown — the THREE-SECTION script (required output)

When the user gives an idea, the FIRST thing the skill produces is a structured
script in these three sections (Chinese headers preferred — this is the user's
standard format). Present it at the style gate ② for the user to adjust BEFORE any
paid step. The three sections also map 1:1 to the parts of the final prompts:
基础设定+氛围 → the first-frame prompt; 画面内容(分镜) → camera/blockout + the
director-shot video prompt.

---

## 【基础设定】 (Basic Setup)

- **One entry per subject/character** — full design: body/build, era/style,
  costume, materials, distinctive features, "气质". (e.g. "机器人清道夫: 身形修长的
  人形机器人, 1960年代原子朋克风格, 面部LED屏替五官显示像素表情(静态), 生棕色牛仔帽,
  黑色哑光高腰丹宁夹克, 黑色哑光皮手套, 牛仔腰带和枪套。")
- **场景 (Scene)**: era, location, situation, time of day, architecture style,
  environment props, and the intended mood/contrast.
- **声音 (Sound)**: soundtrack / ambient requirements (often "不需要配乐, 仅保留同期声").

## 【氛围与画质】 (Atmosphere & Quality)

- **风格核心 (Style core)**: genre keywords, realism level ("电影级质感、超写实、真人
  实景拍摄、杜绝游戏CG感"), tonal intent (e.g. 黑色幽默/史诗), the key contrast.
- **视觉主调 (Visual tone)**: film/lens look — anamorphic widescreen, camera/film
  stock, lens series, motion blur, etc.
- **色彩与影调 (Color & grading)**: palette, contrast, film grain, filter,
  lighting (natural daylight / volumetric), highlight & shadow handling.

## 【画面内容】 (Shot Content) — one or more 分镜

Each 分镜 (shot) is a block with a timecode and these fields:

- **分镜N + timecode** (e.g. `分镜一: 00:00-00:07`)
- **景别 (shot size)**: e.g. 史诗级大全景 / 上半身近景 / 地面特写。
- **构图 (composition)**: framing, leading lines, subject placement in frame,
  foreground/background layering.
- **运镜手法 (camera technique)**: e.g. 无人机高空俯拍、固定机位缓慢上摇、入画后跟拍、
  俯拍地面跟随。 **This drives the Blender white-model camera (start/end/lookAt/move).**
- **画面内容 (shot content)**: beat-by-beat description of what happens in the shot.

> v1 of this skill renders ONE shot per run. For a multi-shot script, pick the shot
> to produce (or run once per shot) — multi-shot stitching is a future extension.

---

## How the three sections feed the rest of the pipeline

1. **first-frame prompt** (step ③) = 【基础设定】(the subjects + scene) + 【氛围与画质】
   (style/visual/color), composed as one establishing image of the chosen shot.
2. **white-model previs** (step ④) = the chosen 分镜's 景别/构图/运镜手法 → room/exterior
   + blockout objects + camera start/end/lookAt/lens in the shot spec.
3. **director-shot video prompt** (step ⑤) = built from all three sections, written in
   the four-block director structure in `prompt-template.md` (参考规则 + proxy clause,
   动作顺序 from 画面内容, 技术规格 from 氛围与画质, 严格不要).

See `prompt-template.md` for the final video-prompt structure.
