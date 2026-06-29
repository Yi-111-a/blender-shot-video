# -*- coding: utf-8 -*-
"""Shared Ark helpers for the blender-shot-video skill: read the key, build a
proxy-clean env (a local proxy chokes the calls on Windows), run curl."""
import os, subprocess

# studio/.env relative to the 短剧 workspace; override with ARK_ENV.
_DEF_ENV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "studio", ".env"
)


def read_key():
    if os.environ.get("ARK_API_KEY"):
        return os.environ["ARK_API_KEY"]
    env_path = os.environ.get("ARK_ENV", _DEF_ENV)
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("ARK_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ARK_API_KEY not found (set env or studio/.env)")


def clean_env():
    e = dict(os.environ)
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        e.pop(k, None)
    e["NO_PROXY"] = "*"
    return e


def curl_json(args, env=None):
    p = subprocess.run(
        ["curl", "-s", "--ssl-no-revoke", "--retry", "3", "--retry-all-errors"] + args,
        capture_output=True, text=True, encoding="utf-8", env=env or clean_env(),
    )
    return p.stdout
