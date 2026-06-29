# blender-shot-video

**English** | [中文](README.zh-CN.md)

Turn a one-line idea into a short cinematic video shot with a **camera you actually
control** — use Blender to lock the camera move and composition with a gray
**white-model**, then let any AI video model "paint" the final shot from a first-frame
image + that previs.

> **Why this exists.** Text-to-video alone gives you no real control over the camera,
> and reference-to-video on a *textured* previs makes walls "look like a flat image"
> and produces artifacts (e.g. a neck snapping 180°). The fix: drive the model with a
> **plain gray blockout** (it reads volume/depth, not a flat picture) + a strong first
> frame for the look. The blockout is free to iterate; you only pay once the move is right.

## Example: blockout → final

The same shot, white-model previs on top, generated result on the bottom — identical
camera, composition, and subject placement. The gray boxes become a real Elden-Ring
sky-city; the dragon+rider stay framed throughout.

![white-model (top) vs final generated (bottom) — early](examples/example-compare-1.jpg)
![white-model (top) vs final generated (bottom) — later](examples/example-compare-2.jpg)

*(Top = `build_whitemodel.py` previs. Bottom = the AI video generated from it +
the first-frame image. Built with `compare_stack.py`.)*

## Pipeline

```
text idea
  ① breakdown   (free)   → 3-section script: 基础设定 / 氛围与画质 / 画面内容(分镜)
  ② style gate  (ASK)    → user confirms style + camera + layout
  ③ first frame (PAID*)  → 1 establishing image (any text-to-image, OR user-supplied)
  ④ white-model (free)   → Blender gray previs with the planned camera move
  ⑤ generate    (PAID)   → final video = first frame + white-model previs + prompt
  ⑥ comparison  (free)   → stacked white-model/final video for review
```
`*` ③ is free when the user supplies their own first frame.

**The core idea:** ④ gives the model three things at ⑤ — the **first frame** (look
anchor), the **white-model previs** (camera + motion + spatial guide), and a
**director-shot prompt**. The white model is plain gray geometry on purpose.

## Quick start

Invoke it in Claude Code: `/blender-shot-video` + a sentence (e.g. *"a knight on a
dragon charging up toward a giant broken sky-city"*). The agent walks the pipeline,
stops at the human gates (② style, ④ white-model review) and before every paid call.

Manual use of the scripts:
```bash
# ④ white-model previs from a shot spec (see references/shot-spec.example.json)
blender -b -P scripts/build_whitemodel.py -- --shot-spec shot.json --output previs.mp4

# ③ first frame (Ark adapter; or supply your own image and skip this)
python scripts/gen_firstframe.py --prompt "<firstFramePrompt>" --out ff.jpg

# ⑤ final video (Ark adapter)
python scripts/generate_video.py --first-frame ff.jpg --previs previs.mp4 \
    --prompt "<videoPrompt>" --out final.mp4 --duration 10 --ratio 16:9

# ⑥ comparison (white-model on top, final on bottom)
python scripts/compare_stack.py --top previs.mp4 --bottom final.mp4 --out compare.mp4
```

## Model-agnostic

The fixed, free core is ①②④ (breakdown → white-model). The model calls in ③/⑤ are
**pluggable adapters** — a Volcengine Ark / Seedance implementation is bundled as a
reference; swap in any provider, keeping the same contract:

| step | contract (in → out) | bundled adapter |
|---|---|---|
| ③ | prompt → 1 image | `scripts/gen_firstframe.py` (`--model`, `$ARK_IMAGE_ENDPOINT`) |
| ⑤ | first-frame + reference video + prompt → 1 video | `scripts/generate_video.py` (`--model`, `$ARK_VIDEO_ENDPOINT`) |

## Camera moves the white-model supports

- **Simple** — `start`/`end`/`lookAt` (push-in, pan, rise).
- **Multi-phase** — `camera.keyframes` (e.g. dash forward, then crane low→high to reveal).
- **Follow a moving subject** — an animated `subject` (e.g. a dragon flying a `path`)
  with `cameraFollow` so the camera rides behind it and keeps it framed.
- `easing`: `sine` (ease through waypoints) or `linear` (constant-speed charge).
- Interior box rooms (`room`) or open sky (omit `room`); blockout `objects` as boxes
  or irregular `rock`s.

## Layout

```
SKILL.md                         agent-facing operating instructions (the contract)
README.md                        this file
references/
  script-breakdown-template.md   ① three-section script format
  prompt-template.md             ⑤ director-shot prompt structure (incl. proxy clause)
  shot-spec.example.json         a worked shot spec
scripts/
  build_whitemodel.py            ④ Blender gray previs (camera + animated subject)
  gen_firstframe.py              ③ first-frame adapter (Ark text-to-image)
  generate_video.py              ⑤ final-video adapter (Ark r2v + cloudflared hosting)
  compare_stack.py               ⑥ stack white-model/final into a comparison video
  _ark.py                        shared key/curl helpers
examples/                        the comparison stills above
```

## Dependencies

- **Blender** (④) — `$BLENDER_EXECUTABLE` or a known path; uses its bundled `bpy`.
- **System Python** for ③/⑤/⑥, plus **`curl`** (③/⑤) and **`opencv-python`** (⑥).
- **cloudflared** only for the bundled Ark video adapter (many video models fetch
  public URLs and can't reach `localhost`; ⑤ tunnels the two local files and tears it
  down afterwards). Not committed — drop it at `scripts/bin/` or set `$CLOUDFLARED`.
- **API key** for the bundled Ark adapters: set `ARK_API_KEY` (env var). Replace the
  adapters to use a different provider's auth.

## House rules (baked into SKILL.md)

- **White model is a proxy** — the ⑤ prompt must tell the model NOT to reproduce the
  gray/low-poly/block look; each shape only marks a subject's position/orientation.
- **Review the white-model before paying** for ⑤ (mandatory gate).
- **Show the request and get explicit confirmation before any paid call.**
- Keep camera moves controlled; route a followed subject around (not through) dense
  geometry to avoid clipping.
