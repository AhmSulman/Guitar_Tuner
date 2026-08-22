# Guitar Tuner — Project Guide for Claude Code

## What this project is

A precision multiplatform guitar tuner built with **Kivy** (Python), targeting:
- **Windows** — run directly with `python main.py`
- **Android Pixel 10** — built via GitHub Actions CI → Buildozer → `.apk`

Features: YIN pitch detection, 12 guitar tunings, real-time mic signal bar,
semi-circular gauge with animated needle, median-filtered pitch smoothing, string selector.

---

## File map

| File | Purpose |
|------|---------|
| `main.py` | `GuitarTunerApp` + `RootLayout` — all UI, permission handling, audio pipeline |
| `gauge.py` | `TunerGauge` — custom Kivy canvas widget with animated needle |
| `pitch.py` | `detect_pitch()` — YIN + FFT autocorrelation; `freq_to_note()` |
| `tunings.py` | `TUNINGS` dict (12 tunings), `find_closest_string()`, `note_to_freq()` |
| `audio_input.py` | `AudioInput` factory — `_SounddeviceInput` (Windows) / `_AndroidAudioInput` (Android) |
| `settings.py` | Plain-JSON cache at `tuner_cache.json` — last tuning, locked string, launch count |
| `test_tuner.py` | Regression tests — `python -m unittest test_tuner` (stdlib only, no pytest) |
| `requirements.txt` | Desktop deps: `kivy==2.3.1`, `numpy`, `sounddevice` |
| `buildozer.spec` | Android APK config — API 34, arm64-v8a, p4a pin, permissions |
| `.github/workflows/build-apk.yml` | CI: ubuntu-22.04, Python 3.10, buildozer — produces APK artifact |

---

## Running on Windows

Requires **Python 3.12 or 3.13**.

```bash
pip install -r requirements.txt
python main.py
```

`sounddevice` requires PortAudio. On Windows it bundles its own — no extra install needed.

---

## Building the Android APK

The APK is built automatically by **GitHub Actions** on every push to `main`.
Download the `GuitarTuner-APK` artifact from the Actions run (retained 30 days).

To build locally (Linux / WSL2 only — Buildozer does not run natively on Windows):

```bash
sudo apt install -y python3-pip build-essential git unzip openjdk-17-jdk
pip install buildozer cython
buildozer android debug
# Output: bin/guitartuner-1.0.0-arm64-v8a-debug.apk
```

Deploy to device:
```bash
adb install bin/guitartuner-1.0.0-arm64-v8a-debug.apk
```

---

## Key design decisions

### Audio backends — platform split

`audio_input.py` exposes a single `AudioInput(on_audio_ready)` factory that returns the
right backend:

| Platform                | Class                | Mechanism                                              |
|-------------------------|----------------------|--------------------------------------------------------|
| Windows / macOS / Linux | `_SounddeviceInput`  | `sounddevice.InputStream` callback — real-time float32 |
| Android                 | `_AndroidAudioInput` | `android.media.AudioRecord` via jnius — raw int16 PCM  |

**Why not plyer on Android?** plyer's Android audio backend records AMR_NB format,
not WAV. `wave.open()` silently fails on AMR files — no audio data ever arrives.
`android.media.AudioRecord` streams raw PCM directly, no file I/O.

**Critical jnius gotcha — bytearray copy-back:**
Do NOT pass a Python `bytearray` to `AudioRecord.read()`. jnius creates a temporary
Java `byte[]` from it, Java fills it, but jnius never copies the data back to Python.
All samples stay zero, RMS = 0, silence gate fires, no pitch detected — no crash.

**Correct approach:** create the buffer via `java.lang.reflect.Array.newInstance(Short.TYPE, n)`.
This lives in JVM memory. `read(short_arr, 0, n)` fills it in-place; `short_arr[i]`
reads straight from JVM — no copy-back needed.

```python
Array = autoclass('java.lang.reflect.Array')
Short = autoclass('java.lang.Short')
short_arr = Array.newInstance(Short.TYPE, chunk_frames)
n = self._recorder.read(short_arr, 0, chunk_frames)
samples = np.array([short_arr[i] for i in range(n)], dtype=np.float32) / 32768.0
```

### p4a version pinning — CRITICAL

`pip install python-for-android==X` in CI is **completely ignored**. Buildozer always
clones p4a fresh from GitHub at build time. The only way to pin the version is:

```ini
# buildozer.spec
p4a.branch = v2024.01.21
```

**Why v2024.01.21?** This tag uses Python 3.11.5 + numpy 1.22.3 + pyjnius 1.6.1,
all compatible with Kivy 2.3.0. p4a master (Python 3.14+) breaks Kivy 2.3.0's
Cython C code (`_PyInterpreterState_GetConfig` API changed in Python 3.13+).

### Android permissions

`RECORD_AUDIO` is declared in `buildozer.spec` (manifest) **and** requested at
runtime in `main.py::on_start()` via `android.permissions.request_permissions`.
`AudioRecord.getState()` returns `STATE_UNINITIALIZED` (0) if the permission was
not yet granted — the `start()` method checks this and logs clearly.

### Pitch detection — YIN algorithm

`pitch.py::detect_pitch()` uses the YIN difference function accelerated with FFT
autocorrelation (O(N log N) vs O(N²)). Threshold = 0.20 (lower = stricter).
Parabolic interpolation gives sub-sample period accuracy.
Silence gate at RMS < 0.005 prevents spurious readings.

`MIN_FREQ` is **35 Hz**, not 50. At 50 Hz there was only 465 cents of headroom above
Drop C / Open C's low C2 (65.4 Hz), so a slack low string being brought up to pitch read
as silence — the app went blind during the exact retune the user was performing. The cost
is ~0.3 ms per call on a 250 ms budget.

### UI threading model

`AudioInput` callback fires on the **audio thread**. Any UI mutation is marshalled
to the Kivy main thread via `Clock.schedule_once(lambda dt: ..., 0)` in `main.py`.
Never touch widgets directly from `_on_raw_audio`.

### Shutdown ordering — CRITICAL

`AudioRecord.release()` frees the native object. If the audio thread is still blocked
inside `read()` when that happens, you get a **use-after-free — SIGSEGV with no Python
traceback**. The order in `stop()` is load-bearing:

1. set `_stop_event`
2. `recorder.stop()` — unblocks a pending `read()`, does *not* free anything
3. `thread.join()` — wait for `_record_loop` to actually exit
4. only now `recorder.release()`

`GuitarTunerApp` also carries a `_shutting_down` flag and keeps the `Clock` handle for
the deferred `_start_audio`. Closing inside the 400 ms start delay used to run `on_stop`
with `self._audio is None`, then start audio against a torn-down root — an orphan stream
nothing ever stopped.

### Pitch smoothing

`main.py` keeps a `deque(maxlen=5)` of recent valid frequencies and reports
`np.median()`. This kills one-off spikes without adding latency.

### Gauge geometry

- `cents = 0` → needle at 90° (straight up)
- `cents = -50` (flat) → needle at 210° (lower left)
- `cents = +50` (sharp) → needle at −30°/330° (lower right)
- Formula: `angle = 90 − cents × 2.4`
- Animation: exponential smoothing driven by a 30 Hz `Clock` interval

### Tuning resolution — one reference point

The note name and the cents reading must come from the **same** reference, or the display
contradicts itself. The original bug: in Open C, a perfectly in-tune E2 was named `E2` by
`freq_to_note` (nearest chromatic note) but measured against G2 by `find_closest_string`
(nearest string), so the gauge read **"E2 · Flat −50¢"** with the A-string lit.

The contract now:

- `find_closest_string()` returns `string_idx = -1` when the pitch is more than
  `MAX_STRING_CENTS` (150) from every string of the tuning. Callers must render that as
  "not near any string" — never draw a needle against a string the player isn't near.
- When a string *is* resolved, the displayed note comes from
  `get_string_notes(tuning)[str_idx]`, not from `freq_to_note`.
- `freq_to_note` is only for the chromatic readout in `LiveFrequencyBar`, and takes
  `prefer_flats` so flat-spelled tunings (Half Step Down) don't show `Eb2` on the button
  and `D#2` on the gauge.
- Cents are returned **unclipped**. Clamp only for display. Lock mode needs the true
  distance — retuning E2 down to C2 must read "Sharp — 400¢", not a clamped 100.

### Settings cache

`settings.py` is a plain stdlib-`json` cache at `tuner_cache.json`, next to `main.py` —
deliberately *not* a platform data dir, because nothing sensitive is stored. It holds the
last tuning, the locked string, a launch counter and a last-opened stamp.

Every operation is total: missing file, corrupt JSON, a non-dict payload, a wrong-typed
value, or an unwritable path all fall back to `DEFAULTS` rather than raising. `load()`
coerces each value to the type of its default, so no caller has to guard against a
hand-edited file. Treat it as a cache — p4a re-extracts the app directory on update, so it
can legitimately vanish.

### Tuning state has one owner

`app.current_tuning` owns it. `RootLayout.apply_tuning(name, selected)` is the only thing
that writes the spinner text, the six button labels and the lock selection. `_applying`
guards the spinner-change callback from re-entering. Anything that mutates those three
independently will desync them — that is what made persistence non-trivial.

### Adding a new tuning

Append to `TUNINGS` dict in `tunings.py`. Key = display name, value = list of 6
note strings (low → high), e.g. `'Nashville': ['E3','A3','D4','G4','B3','E4']`.

---

## Known limitations / TODOs

- Buildozer must run on Linux/WSL2 — APK builds go through GitHub Actions CI
- Chunking is 3 × 0.25 s with 2/3 overlap, plus a 5-frame median in `main.py`, so
  effective latency is ~1.25–2 s. Fine for tuning, too slow for any timing feature
- `_AndroidAudioInput` reads 11 025 shorts per chunk via a Python loop — ~10–20 ms overhead on Pixel 10, acceptable for a 250 ms chunk
- No capo support — add semitone transposition to `find_closest_string()`
- No strobe tuner mode — future enhancement
