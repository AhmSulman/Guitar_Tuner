"""Turn device captures into Play phone screenshots: exactly 9:16, no alpha.

Play Console (Nov 2026) requires phone screenshots to be 16:9 or 9:16. The
old "no wider than 2:1" rule is gone. A Pixel captures at 1080x2424, so:

  1. crop to 2:1 by dropping the status bar and gesture bar (1080x2160), then
  2. pad the sides to 9:16 (1215x2160) by repeating each row's edge pixel, so
     full-width bars run on seamlessly and nothing in the UI is cut off.

This is how the published 1.0.3 set in store/screenshots/ was made.

    python store/crop_shots.py shot1.png shot2.png shot3.png shot4.png

Writes 01-<name>.png ... into store/screenshots/. Adjust the split with
--top / --bottom if the bars on your device are a different height; the script
always lands on exactly 2:1 before padding, and the output is always exactly 9:16.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
MAX_RATIO = 2.0          # crop target before padding (drops the system bars)
MIN_SIDE, MAX_SIDE = 320, 3840
MAX_BYTES = 8 * 1024 * 1024


def pad_to_9x16(im: Image.Image) -> Image.Image:
    """Make the image exactly 9:16 without cutting anything.

    Trim the height to a multiple of 16, then widen to h*9/16 by repeating the
    outermost pixel column on each side. Padding with each row's own edge
    colour, not a flat fill, keeps full-width bars seamless.
    """
    w, h = im.size
    h -= h % 16
    im = im.crop((0, 0, w, h))
    target = h * 9 // 16
    if target <= w:  # already 9:16 or wider: centre-crop the width instead
        left = (w - target) // 2
        return im.crop((left, 0, left + target, h))
    pad_l = (target - w) // 2
    pad_r = target - w - pad_l
    out = Image.new('RGB', (target, h))
    out.paste(im, (pad_l, 0))
    out.paste(im.crop((0, 0, 1, h)).resize((pad_l, h)), (0, 0))
    out.paste(im.crop((w - 1, 0, w, h)).resize((pad_r, h)), (pad_l + w, 0))
    return out


def crop_one(path: str, top: int, bottom: int, index: int, slug: str | None = None) -> str:
    im = Image.open(path)
    # Play rejects alpha; flatten onto black rather than letting it ride
    if im.mode in ('RGBA', 'LA', 'P'):
        flat = Image.new('RGB', im.size, (0, 0, 0))
        im = im.convert('RGBA')
        flat.paste(im, (0, 0), im)
        im = flat
    else:
        im = im.convert('RGB')

    w, h = im.size
    keep = int(w * MAX_RATIO)            # tallest height still within 2:1
    if h <= keep:
        print(f'{os.path.basename(path)}: already {w}x{h} ({h/w:.2f}:1) — no crop needed')
        box_top, box_bottom = 0, h
    else:
        box_top = min(top, h - keep)
        box_bottom = box_top + keep
        # honour --bottom where it fits, letting the top take the slack
        want_bottom = h - bottom
        if want_bottom < box_bottom and want_bottom - keep >= 0:
            box_bottom = want_bottom
            box_top = box_bottom - keep

    stem = slug or os.path.splitext(os.path.basename(path))[0]
    out_name = f'{index:02d}-{stem}.png'
    out = os.path.join(OUT_DIR, out_name)
    os.makedirs(OUT_DIR, exist_ok=True)
    cropped = pad_to_9x16(im.crop((0, box_top, w, box_bottom)))
    cropped.save(out, 'PNG', optimize=True)

    cw, ch = cropped.size
    size = os.path.getsize(out)
    problems = []
    if cw * 16 != ch * 9:
        problems.append(f'{cw}x{ch} is not exactly 9:16')
    if min(cw, ch) < MIN_SIDE:
        problems.append(f'short side {min(cw, ch)} under {MIN_SIDE}')
    if max(cw, ch) > MAX_SIDE:
        problems.append(f'long side {max(cw, ch)} over {MAX_SIDE}')
    if size > MAX_BYTES:
        problems.append(f'{size/1048576:.1f} MB over 8 MB')

    verdict = 'OK' if not problems else 'FAIL: ' + '; '.join(problems)
    print(f'{os.path.basename(path):<16} {w}x{h} -> {cw}x{ch}  '
          f'({ch/cw:.2f}:1)  {size/1024:>6.0f} KB  {verdict}')
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--top', type=int, default=150,
                    help='rows to drop from the top, the status bar (default 150)')
    ap.add_argument('--bottom', type=int, default=114,
                    help='rows to drop from the bottom, the gesture bar (default 114)')
    ap.add_argument('--name', action='append', default=None,
                    help='output slug per input, repeatable; falls back to the input name')
    ap.add_argument('--start', type=int, default=None,
                    help='first index; default continues past what is already in the dir')
    args = ap.parse_args()

    missing = [f for f in args.files if not os.path.exists(f)]
    if missing:
        print('not found: ' + ', '.join(missing), file=sys.stderr)
        return 1

    # Numbering used to restart at 1 every run, so a second invocation
    # overwrote nothing but collided: 01-shot1.png beside 01-shot5.png.
    if args.start is not None:
        start = args.start
    else:
        existing = [os.path.basename(f)[:2] for f in glob.glob(os.path.join(OUT_DIR, '*.png'))]
        used = [int(x) for x in existing if x.isdigit()]
        start = max(used) + 1 if used else 1

    names = args.name or []
    if names and len(names) != len(args.files):
        print(f'--name given {len(names)} times for {len(args.files)} files', file=sys.stderr)
        return 1

    print(f'{"file":<16} {"in":<10}    {"out":<10} {"ratio":<9} {"size":<10} verdict')
    print('-' * 78)
    for i, f in enumerate(args.files):
        slug = names[i] if names else None
        crop_one(f, args.top, args.bottom, start + i, slug)
    print(f'\nwritten to {OUT_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
