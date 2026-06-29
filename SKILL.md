---
name: blender-shot-video
description: Turn a text idea into one short cinematic video shot with a CONTROLLABLE camera. Break the idea into a shot spec, obtain ONE first-frame image (any text-to-image model, or user-supplied), render a Blender WHITE-MODEL previs with the planned camera move, then generate the final video with any image+reference-video model (first frame as the look anchor + white-model video as the camera/motion guide + prompt). Model-agnostic: a Volcengine Ark / Seedance adapter is bundled as one reference implementation, but any provider can be plugged in. Use when the user wants a short AI video shot with controllable camera/composition. Single shot per run (multi-shot is a future extension).
---

# Blender Shot → Video

Pipeline (one continuous shot per run):

```
text idea
  ① breakdown   (you, free)      → shot spec JSON (scene, camera move, room, duration, style)
  ② style gate  (ASK the user)   → confirm style + camera + layout
  ③ first frame (PAID, confirm)  → 1 image  (any text-to-image model, OR user-supplied)
  ④ white-model (Blender, free)  → gray previs video (scripts/build_whitemodel.py)
  ⑤ generate    (PAID, confirm)  → final video (any image+reference-video model)
```

The generation model gets THREE things at step ⑤: the first-frame image (look
anchor), the white-model previs (camera + spatial/motion guide), and the prompt.
White model = plain gray geometry so the model reads volume/depth (do NOT texture
the walls — that made them look flat before).

**Model-agnostic.** ④ (Blender white-model) is the fixed, free core of this skill.
Steps ③ and ⑤ are just "call a model": ③ = any text-to-image (or the user drops in
their own image — then ③ is free/skipped); ⑤ = any model that accepts an image +
a reference video + a prompt. A Volcengine Ark / Seedance adapter is bundled under
`scripts/` as ONE reference implementation; swap it for any other provider — keep the
director-shot prompt and the white-model contract the same. See **Providers** below.

## Hard rules

- **Never call a paid model without showing the exact request/payload and getting an
  explicit "确认/confirm" first.** Applies to ③ and ⑤ whatever the provider.
- Keep camera moves **gentle** (slow push-in / pan / slight rise). Avoid fast 360°
  orbits and whip moves — they cause limb/neck flips at the model layer.
- One first frame and one white-model video per run. One output video.
- The ARK key is read from `studio/.env` (`ARK_API_KEY`) or the env var; never print
  it, never write it to a file.

## Step ① — breakdown (you, the agent)

**First, decompose the user's idea into the THREE-SECTION script** — 【基础设定】
【氛围与画质】【画面内容(分镜)】 — per `references/script-breakdown-template.md`.
This is the user's standard format and the human-readable artifact they approve at ②.
Each 分镜 carries 景别 / 构图 / 运镜手法 / 画面内容.

Then derive the machine-readable **shot spec** JSON for the chosen 分镜
(see `references/shot-spec.example.json`):
- `style`: one line (e.g. "film noir, rainy night, cold blue × warm amber, ultra-real cinematic").
- `firstFramePrompt`: a rich text-to-image prompt for the establishing first frame
  (style + scene + framing). This defines the look.
- `videoPrompt`: the final-video prompt. It MUST be written in the **director shot
  version** structure — see `references/prompt-template.md` (four blocks: ① 参考规则
  with explicit per-reference roles + the CRITICAL proxy clause, ② beat-by-beat 动作
  顺序, ③ 技术规格, ④ 严格不要). A thin one-line prompt is not acceptable here: it lets
  the white-model's gray/low-poly/block look bleed into the result and the references
  go ignored. Always include the proxy clause ("the video is a proxy — do NOT render
  its gray material / low-poly facets / placeholder blocks / UI; each shape only marks
  a subject's position/timing/orientation; render the real thing") and a legend of
  what each blockout shape represents.
- `room`: `{width, depth, height}` metres for an INTERIOR (box room is built).
  Convention: X∈[-w/2,w/2], Y∈[0,depth] (Y=0 near, Y=depth far), Z up.
  **Omit `room` for an EXTERIOR/sky scene** (no walls; bright sky + sun). Optionally
  add `ground: <z>` for a distant ground plane.
- `objects`: `[{name, size:[w,d,h], position:[x,y,z(center)], shape, rotationDeg}]`
  gray blockout solids. `shape`: `box` (default) or `rock`/`sphere` (irregular
  boulder/ellipsoid — good for floating rocks). `rotationDeg`: `[x,y,z]` optional.
  Build a creature/vehicle from a few boxes (body + wings + rider).
- `camera`: `{lensMm, durationSec, fps, easing}` + ONE motion mode below. The camera
  always TRACK-TO's a look target. `easing`: `"sine"` (default; eases through each
  waypoint — good for crane/reveal) or `"linear"` (constant speed, no slow-down at
  intermediate points — a continuous charge, no "go-pause-go").
  Three motion modes (pick one):
  1. **Simple** — `start:[x,y,z]`, `end:[x,y,z]`, `lookAt:[x,y,z]`: interpolate
     start→end while looking at a fixed point. (push-in / pan / rise.)
  2. **Multi-phase** — `keyframes:[{t,pos,lookAt}, ...]` (t in 0..1): scripted move,
     e.g. dash forward then crane low→high to reveal. (Subject is static.)
  3. **Follow a moving subject** — set top-level `cameraFollow` (below); the camera
     rides at a fixed offset from the animated `subject` and looks at it.
- `subject` (optional, an ANIMATED hero like the dragon+rider):
  `{parts:[{name,size,position(RELATIVE to subject origin),shape,rotationDeg}],
  path:[{t,pos,rotationDeg}]}`. Build the creature from a few parts (body+wings+
  rider); it flies along `path` (t in 0..1) and the parts move with it.
- `cameraFollow` (optional, use WITH `subject`): `{offset:[x,y,z], lookAtOffset:[x,y,z],
  lensMm}`. Camera position = subject + offset; look target = subject + lookAtOffset.
  Keeps the subject framed (e.g. behind-the-dragon, wings framing) while the scenery
  streams past. To avoid clipping, route the subject OUTSIDE dense geometry (e.g. down
  a city's face, not through its towers) and keep `offset` far enough back.

## Step ② — style gate (ASK)

Show the user the full **three-section script** (基础设定 / 氛围与画质 / 画面内容) plus
the proposed camera move and blockout layout. Use AskUserQuestion to let them adjust
style / subjects / shot details. Fold their choices back into the script + shot spec.

## Step ③ — first frame (PAID, or user-supplied)

Goal: ONE establishing image that locks the look. Two ways:
- **User supplies an image** → just use it (free; skip generation). Best when they
  already have the exact frame they want.
- **Generate** with ANY text-to-image model from the `firstFramePrompt` (基础设定 +
  氛围与画质). Show the request first and wait for confirmation.
  - Bundled Ark adapter: `python scripts/gen_firstframe.py --prompt "<firstFramePrompt>"
    --out <abs>.jpg [--size 2560x1440] [--model <id>]`. To use a different provider,
    call its API/CLI instead — the only contract is "prompt → one image file".

Review the image with the user before proceeding.

## Step ④ — white-model previs (Blender, free)

Write the shot spec to a JSON file, then:
`blender -b -P scripts/build_whitemodel.py -- --shot-spec <spec>.json --output <previs>.mp4`
(Resolve Blender via `studio/server/blender/cliBlenderBridge.js` portable path, or
the env `BLENDER_EXECUTABLE`; on Windows clear proxy: `HTTP_PROXY= HTTPS_PROXY= NO_PROXY='*'`.)

**MANDATORY REVIEW GATE — do NOT skip:** present the white-model previs to the user
(the .mp4 path + a few extracted frames) and get their **explicit approval** of the
camera move + blockout layout BEFORE step ⑤. The white model is the free, controllable
part — iterate the camera/objects in the spec and re-render until the user signs off.
Never run the paid step ⑤ on an unreviewed white model.

## Step ⑤ — generate (PAID)

The model gets: first-frame image (look anchor) + white-model previs (camera/motion
guide) + the `videoPrompt`. Use ANY model that accepts image + reference-video + text.

Before sending, CHECK the `videoPrompt` has all four director-shot blocks (esp. the
proxy clause + block legend). If it is thin, rewrite it per `references/prompt-template.md`.

1. Show the request (model, prompt, which file is the look anchor, which is the
   motion/camera guide, ratio, duration ≤10) and wait for confirmation.
2. Generate with your chosen provider. Bundled Ark adapter:
   `python scripts/generate_video.py --first-frame <ff> --previs <previs>.mp4
     --prompt "<videoPrompt>" --out <final>.mp4 [--duration 10] [--ratio 16:9] [--model <id>]`
3. Review with the user. To revise: tweak `videoPrompt` / camera and re-run ④–⑤.

## Step ⑥ — comparison (presentation, free)

When showing the final result, ALSO build a stacked comparison — white-model previs
on top, final video on bottom — so the user sees how the blockout drove the shot:
`python scripts/compare_stack.py --top <previs>.mp4 --bottom <final>.mp4 --out <compare>.mp4`
(OpenCV only, no ffmpeg; labels each panel.) Present this alongside the final.

## Providers / adapters (model-agnostic)

The skill's fixed core is steps ①②④ (breakdown → white-model previs). The model
calls in ③/⑤ are pluggable — swap freely, keep the same inputs/outputs:

| step | contract (in → out) | bundled reference adapter |
|---|---|---|
| ③ | text prompt → 1 image file | `scripts/gen_firstframe.py` (Ark text-to-image, `--model`) |
| ⑤ | first-frame image + reference video + prompt → 1 video file | `scripts/generate_video.py` (Ark reference-to-video, `--model`) |

To use a different model/provider: call its API/CLI/SDK in place of the bundled
script, passing the same first frame + white-model previs + director-shot prompt.
Notes for whatever provider you use:
- Many video models fetch **public URLs** and cannot reach `localhost`; the bundled
  `generate_video.py` solves this with a temporary cloudflared tunnel (auto torn
  down). A provider that takes file uploads or already-hosted URLs won't need it.
- Mind the provider's input constraints (e.g. min reference-video resolution); the
  1280×720 white-model previs is a safe default.

## Dependencies

- **Blender** (④): resolve via `$BLENDER_EXECUTABLE` or the portable path; renders
  with its own bundled Python (`bpy`).
- **System Python** for ③/⑤/⑥ scripts, plus **`curl`** (③/⑤) and **`opencv-python`**
  (`cv2`, used by ⑥ `compare_stack.py`). `pip install opencv-python` if missing.
- **cloudflared** only for the bundled Ark video adapter (see below).

## Notes / future extensions

- Default models are just defaults — override per call (`--model`) or replace the
  adapter entirely.
- Multi-shot (a storyboard of several shots sharing one style + stitching) is a
  future extension — keep v1 to a single shot.
- cloudflared (only needed by the bundled Ark video adapter): resolved via
  `--cloudflared`, `$CLOUDFLARED`, PATH, or `scripts/bin/cloudflared(.exe)`.
