# Store screenshots

Finished Play listing screenshots go here. Scratch captures named `shot*.png` at the
repo root are gitignored.

## Requirements

| | |
|---|---|
| Count | 2–8 per form factor |
| Size | 320–3840 px per side |
| **Aspect ratio** | **no wider than 2:1** |
| Format | JPEG or 24-bit PNG, **no alpha** |
| Max size | 8 MB each |

A Pixel captures at 1080×2424, which is **2.24:1 and will be rejected**. Cropping the
status bar and gesture bar fixes the ratio and looks better anyway — 1080×2160 is exactly 2:1.

ImageMagick is not installed here, so use the bundled script — it uses Pillow, which is
already a project dependency, and it validates every Play constraint as it goes.

```bash
adb exec-out screencap -p > shot1.png
python store/crop_shots.py shot1.png shot2.png shot3.png shot4.png
```

It always lands on exactly 2:1 whatever you pass; `--top` and `--bottom` only shift
*which* rows get dropped. It also flattens alpha, since Play rejects it.

## What to shoot

1. Gauge mid-tune with real needle deflection — a centred needle looks like a mockup
2. Tuning spinner open, showing the list of 12
3. String row in an alt tuning, Drop C reads well
4. In-tune green state

Anything captured before v1.0.1 shows the gauge with its colour bands rotated 90° off the
needle, and must be retaken.
