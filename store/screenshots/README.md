# Store screenshots

Finished Play listing screenshots go here. Scratch captures named `shot*.png` at the
repo root are gitignored.

## Requirements (Play Console, Nov 2026)

| | |
|---|---|
| Count | 2–8 per form factor |
| Size | 320–3840 px per side |
| **Aspect ratio** | **exactly 16:9 or 9:16**. The older "no wider than 2:1" rule is gone |
| Format | JPEG or 24-bit PNG, **no alpha** |
| Max size | 8 MB each |

A Pixel captures at 1080×2424, which is neither. Use the bundled script, which needs
Pillow (`pip install pillow`):

```bash
adb exec-out screencap -p > shot1.png
python store/crop_shots.py shot1.png shot2.png shot3.png shot4.png
```

What it does to each capture:
1. **Crops to 1080×2160** by dropping the status bar and gesture bar. `--top` and `--bottom`
   only change *which* rows get dropped.
2. **Pads the sides to exactly 9:16 (1215×2160)** by repeating each row's edge pixel. Full-width
   bars run on seamlessly, and nothing in the UI is cut off.
3. Flattens alpha and checks every Play limit as it goes.

`python store/stage_play_upload.py` re-checks the set, and **fails anything that isn't exactly 9:16**.

## What to shoot

1. Gauge mid-tune with real needle deflection. A centred needle looks like a mockup
2. Tuning spinner open, showing the list of 12
3. String row in an alt tuning. Drop C reads well
4. In-tune green state

---

## Current set (published with 1.0.3, Nov 2026)

| File | Shows |
|---|---|
| `01-in-tune.png` | G2, green needle straight up, IN TUNE |
| `02-flat.png` | C2 at -30.9c, red needle swung left |
| `03-sharp.png` | C2 at +20.9c, orange needle swung right |
| `04-nearly-there.png` | C3 at +9.1c, yellow, closing in |
| `05-twelve-tunings.png` | Spinner open, all 12 tunings |

All are **1215×2160, exactly 9:16**, RGB with no alpha. These are the exact files on the Play listing.

The order puts the payoff first, then both directions of error, then the tuning list.
The flat and sharp pair matters: with only sharp captures, the left half of the gauge
never appeared working.
