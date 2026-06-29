# -*- coding: utf-8 -*-
"""Step ⑤ final-video adapter — REFERENCE implementation (Volcengine Ark reference-to-video).

    python generate_video.py --first-frame ff.jpg --previs previs.mp4 \
        --prompt "<videoPrompt>" --out final.mp4 [--duration 10] [--ratio 16:9] [--model <id>]

The skill is model-agnostic: this is just one adapter. The contract is
"first-frame image + reference video + prompt -> one video file". To use another
provider, call its API/CLI in place of this script with the same inputs.

This adapter hosts the first frame + white-model previs over a TEMPORARY cloudflared
tunnel (Ark fetches public URLs; it cannot reach localhost), submits the task, polls,
downloads the result, and tears the tunnel down. A provider that accepts file uploads
or already-public URLs would not need the tunnel. Only run AFTER showing the request
and getting explicit confirmation.
"""
import argparse, json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time
from _ark import read_key, clean_env, curl_json

TASKS = os.environ.get("ARK_VIDEO_ENDPOINT",
                       "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks")


def find_cloudflared(opt):
    here = os.path.dirname(__file__)
    cands = [opt, os.environ.get("CLOUDFLARED"),
             os.path.join(here, "bin", "cloudflared.exe"),
             os.path.join(here, "bin", "cloudflared"),
             shutil.which("cloudflared")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    if shutil.which("cloudflared"):
        return "cloudflared"
    return None


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-frame", required=True)
    ap.add_argument("--previs", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=int, default=10)
    ap.add_argument("--ratio", default="16:9")
    ap.add_argument("--model", default="doubao-seedance-2-0-mini-260615")
    ap.add_argument("--cloudflared", default=None)
    args = ap.parse_args()

    for f in (args.first_frame, args.previs):
        if not os.path.exists(f):
            raise SystemExit("missing input: " + f)
    cfd = find_cloudflared(args.cloudflared)
    if not cfd:
        raise SystemExit(
            "cloudflared not found. Provide --cloudflared <path>, set $CLOUDFLARED, "
            "or place it at scripts/bin/cloudflared(.exe). Get it from "
            "https://github.com/cloudflare/cloudflared/releases (this exposes the two "
            "local files publicly — a user-authorized step).")

    key = read_key()
    env = clean_env()
    serve = tempfile.mkdtemp(prefix="shot-serve-")
    # preserve source extensions so the served content-type matches the bytes
    ff_name = "first_frame" + (os.path.splitext(args.first_frame)[1] or ".jpg")
    pv_name = "previs" + (os.path.splitext(args.previs)[1] or ".mp4")
    shutil.copyfile(args.first_frame, os.path.join(serve, ff_name))
    shutil.copyfile(args.previs, os.path.join(serve, pv_name))
    port = free_port()

    http = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                            cwd=serve, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tunnel = subprocess.Popen([cfd, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")

    pub = {"url": None}

    def reader():
        for line in tunnel.stdout:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m and not pub["url"]:
                pub["url"] = m.group(0)

    threading.Thread(target=reader, daemon=True).start()

    try:
        for _ in range(60):
            if pub["url"]:
                break
            time.sleep(1)
        if not pub["url"]:
            raise SystemExit("tunnel did not come up")
        base = pub["url"]
        time.sleep(4)  # let the quick tunnel finish registering before first fetch
        # warm up / verify both files are publicly reachable. trycloudflare edges
        # throw transient TLS errors on first hits, so curl must --retry-all-errors.
        for name in (ff_name, pv_name):
            ok = False
            last = ""
            for _ in range(6):
                last = subprocess.run(
                    ["curl", "-s", "--ssl-no-revoke", "--retry", "6", "--retry-all-errors",
                     "--retry-delay", "3", "--connect-timeout", "15",
                     "-o", os.devnull, "-w", "%{http_code}", f"{base}/{name}"],
                    capture_output=True, text=True, env=env).stdout.strip()
                if last == "200":
                    ok = True
                    break
                time.sleep(3)
            if not ok:
                raise SystemExit(f"file not reachable via tunnel: {name} (last code {last})")

        body = {
            "model": args.model,
            "content": [
                {"type": "text", "text": args.prompt},
                {"type": "video_url", "video_url": {"url": f"{base}/{pv_name}"}, "role": "reference_video"},
                {"type": "image_url", "image_url": {"url": f"{base}/{ff_name}"}, "role": "reference_image"},
            ],
            "generate_audio": False, "ratio": args.ratio,
            "duration": min(10, args.duration), "watermark": False,
        }
        bf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(body, bf, ensure_ascii=False); bf.close()
        resp = curl_json(["-X", "POST", TASKS, "-H", "Content-Type: application/json",
                          "-H", "Authorization: Bearer " + key, "--data-binary", "@" + bf.name], env)
        os.unlink(bf.name)
        task = json.loads(resp).get("id")
        if not task:
            raise SystemExit("submit failed: " + resp[:600])
        print("TASK_ID " + task)

        for i in range(100):  # ~ up to ~20 min
            d = json.loads(curl_json(["-H", "Authorization: Bearer " + key, f"{TASKS}/{task}"], env))
            st = d.get("status")
            print(f"[{i}] {st}", flush=True)
            if st == "succeeded":
                url = (d.get("content") or {}).get("video_url")
                subprocess.run(["curl", "-s", "--ssl-no-revoke", "-o", args.out, url], env=env)
                sz = os.path.getsize(args.out) if os.path.exists(args.out) else 0
                print(f"VIDEO {args.out} {sz} bytes")
                break
            if st in ("failed", "cancelled"):
                raise SystemExit("generation " + st + ": " + json.dumps(d, ensure_ascii=False)[:600])
            time.sleep(12)
        else:
            raise SystemExit("timed out waiting for the task")
    finally:
        for proc in (tunnel, http):
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            shutil.rmtree(serve, ignore_errors=True)
        except Exception:
            pass
        print("TUNNEL_CLOSED")


if __name__ == "__main__":
    main()
