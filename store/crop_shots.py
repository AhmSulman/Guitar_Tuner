"""Crop device captures to Play's 2:1 aspect limit.

A Pixel captures at 1080x2424, which is 2.24:1. Play rejects anything wider
than 2:1, so 264 rows have to go. Removing the status bar and the gesture bar
is exactly what you want to remove anyway.

    python store/crop_shots.py shot1.png shot2.png shot3.png shot4.png

Writes 01-<name>.png ... into store/screenshots/. Adjust the split with
--top / --bottom if the bars on your device are a different height; the script
always lands on exactly 2:1 regardless, by absorbing the remainder at the bottom.
"""
from __future__ import annotations

import argparse
import os
import sys

from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
MAX_RATIO = 2.0          # Play's hard limit
MIN_SIDE, MAX_SIDE = 320, 3840
MAX_BYTES = 8 * 1024 * 1024


def crop_one(path: str, top: int, bottom: int, index: int) -> str:
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

    out_name = f'{index:02d}-{os.path.splitext(os.path.basename(path))[0]}.png'
    out = os.path.join(OUT_DIR, out_name)
    os.makedirs(OUT_DIR, exist_ok=True)
    cropped = im.crop((0, box_top, w, box_bottom))
    cropped.save(out, 'PNG', optimize=True)

    cw, ch = cropped.size
    size = os.path.getsize(out)
    problems = []
    if ch / cw > MAX_RATIO + 1e-6:
        problems.append(f'ratio {ch/cw:.2f}:1 still over {MAX_RATIO}:1')
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
    args = ap.parse_args()

    missing = [f for f in args.files if not os.path.exists(f)]
    if missing:
        print('not found: ' + ', '.join(missing), file=sys.stderr)
        return 1

    print(f'{"file":<16} {"in":<10}    {"out":<10} {"ratio":<9} {"size":<10} verdict')
    print('-' * 78)
    for i, f in enumerate(args.files, start=1):
        crop_one(f, args.top, args.bottom, i)
    print(f'\nwritten to {OUT_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
