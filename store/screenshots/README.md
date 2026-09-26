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

```bash
adb exec-out screencap -p > shot1.png
magick shot1.png -gravity north -chop 0x120 -gravity south -chop 0x144 store/screenshots/01-gauge.png
```

## What to shoot

1. Gauge mid-tune with real needle deflection — a centred needle looks like a mockup
2. Tuning spinner open, showing the list of 12
3. String row in an alt tuning, Drop C reads well
4. In-tune green state

Anything captured before v1.0.1 shows the gauge with its colour bands rotated 90° off the
needle, and must be retaken.
