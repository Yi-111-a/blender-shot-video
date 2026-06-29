# -*- coding: utf-8 -*-
"""Step ③ first-frame adapter — REFERENCE implementation (Volcengine Ark text-to-image).

    python gen_firstframe.py --prompt "<text>" --out frame.jpg [--size 2560x1440] [--model <id>]

The skill is model-agnostic: this is just one adapter. The contract is
"prompt -> one image file". To use another provider, call its API/CLI instead and
write the image to --out. Only run AFTER showing the request and getting explicit
confirmation. (Ark `size` must be >= 3,686,400 px, e.g. 2560x1440 or 1920x1920.)
"""
import argparse, json, os, subprocess, tempfile
from _ark import read_key, clean_env, curl_json

ENDPOINT = os.environ.get("ARK_IMAGE_ENDPOINT",
                          "https://ark.cn-beijing.volces.com/api/v3/images/generations")
DEFAULT_MODEL = "doubao-seedream-5-0-260128"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="2560x1440")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    key = read_key()
    body = {
        "model": args.model, "prompt": args.prompt, "size": args.size,
        "response_format": "url", "watermark": False,
    }
    bf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(body, bf, ensure_ascii=False); bf.close()
    out = curl_json(["-X", "POST", ENDPOINT,
                     "-H", "Content-Type: application/json",
                     "-H", "Authorization: Bearer " + key,
                     "--data-binary", "@" + bf.name])
    os.unlink(bf.name)
    try:
        data = json.loads(out)
        url = data["data"][0]["url"]
    except Exception:
        raise SystemExit("first-frame generation failed: " + out[:600])
    subprocess.run(["curl", "-s", "--ssl-no-revoke", "-o", args.out, url], env=clean_env())
    sz = os.path.getsize(args.out) if os.path.exists(args.out) else 0
    print(f"FIRST_FRAME {args.out} {sz} bytes")
    print("URL_24H " + url)


if __name__ == "__main__":
    main()
