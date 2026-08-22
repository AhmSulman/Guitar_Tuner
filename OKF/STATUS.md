# Status — what's actually built (2026-08-23)

## Working now
- Kivy tuner, Windows + Android. YIN pitch detection (`pitch.py`), 12 tunings, animated gauge.
- **Clean shutdown.** `audio_input.py::stop()` now stops → joins → releases, in that order.
  Previously `release()` ran while the audio thread was blocked in `read()` — a use-after-free
  (SIGSEGV, no traceback). That was the "crashes when closing" report.
- **Persistence.** `settings.py` writes a plain-JSON `tuner_cache.json` in the project root:
  last tuning, locked string, launch count, last-opened stamp. Restores across restarts —
  verified over three real process runs. Nothing sensitive is stored. Missing, corrupt,
  wrong-typed or unwritable all fall back to defaults instead of blocking startup.
- **Tuning resolution fixed.** `find_closest_string` returns -1 beyond `MAX_STRING_CENTS` (150)
  instead of snapping to a distant string. Note name now comes from the tuning, not from
  `freq_to_note`, so the two can no longer disagree. Cents are unclipped.
- **Flat spellings.** `freq_to_note(prefer_flats=True)` — Half Step Down no longer shows `Eb2`
  on the button and `D#2` on the gauge.
- `MIN_FREQ` 50 → 35 Hz so the app can see a slack low string during a retune into Drop C.
- 13 regression tests, stdlib unittest: `python -m unittest test_tuner`.

## Investigated and found NOT broken
- The `TUNINGS` table. All 12 entries are musically correct — the "wrongly initialized
  tunings" symptom was entirely the resolution logic above.

## Known-not-done
- Android build of these fixes not yet run on device — CI APK + `adb logcat` check outstanding.
- Play Console assets: icon, feature graphic, screenshots, privacy policy, data-safety form.
- Keystore secrets may still not be in GitHub Settings → Secrets → Actions (unverified).
