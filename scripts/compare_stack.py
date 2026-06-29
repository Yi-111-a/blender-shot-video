# -*- coding: utf-8 -*-
"""Make a comparison video: the white-model previs on TOP, the final video on the
BOTTOM, stacked vertically into one mp4. Handy for review / presentation.

    python compare_stack.py --top previs.mp4 --bottom final.mp4 --out compare.mp4
        [--width 1280] [--fps 24] [--no-labels]

Uses OpenCV only (no ffmpeg). Frames are matched by the shorter clip's length.
"""
import argparse
import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", required=True, help="white-model previs (drawn on top)")
    ap.add_argument("--bottom", required=True, help="final generated video (drawn below)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--no-labels", action="store_true")
    args = ap.parse_args()

    top = cv2.VideoCapture(args.top)
    bot = cv2.VideoCapture(args.bottom)
    if not top.isOpened() or not bot.isOpened():
        raise SystemExit("could not open one of the inputs")

    W = args.width

    def panel_h(cap):
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 16
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 9
        return max(1, int(round(W * h / w)))

    th, bh = panel_h(top), panel_h(bot)
    n = int(min(top.get(cv2.CAP_PROP_FRAME_COUNT), bot.get(cv2.CAP_PROP_FRAME_COUNT)))
    out = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, th + bh))

    def label(img, text):
        if args.no_labels:
            return img
        cv2.rectangle(img, (0, 0), (260, 40), (0, 0, 0), -1)
        cv2.putText(img, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return img

    written = 0
    for _ in range(n):
        ok1, f1 = top.read()
        ok2, f2 = bot.read()
        if not (ok1 and ok2):
            break
        f1 = label(cv2.resize(f1, (W, th)), "WHITE-MODEL (previs)")
        f2 = label(cv2.resize(f2, (W, bh)), "FINAL (generated)")
        out.write(cv2.vconcat([f1, f2]))
        written += 1

    top.release(); bot.release(); out.release()
    print(f"COMPARE {args.out}  {written} frames  {W}x{th + bh}")


if __name__ == "__main__":
    main()
