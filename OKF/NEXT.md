# Next — punch list, roughly in order

## Immediate
1. **Build the CI debug APK and run these fixes on the Pixel.** Open/close 10× including an
   immediate close; `adb logcat` must be clean of `Fatal signal`. The shutdown fix is the one
   change that can only be proven on device.
2. Play Console assets — icon, feature graphic, ≥2 screenshots, privacy policy URL, data-safety
   questionnaire. None of this is code.
3. Confirm the 4 keystore secrets are actually in GitHub → Settings → Secrets → Actions.
4. Tag and submit.

## Then (see the approved plan for detail)
- **Phase 2 — port, don't write.** `Roots_And_Weed/okf/audio_analysis.py` already
  has this: `_chroma_from_magnitude` + `detect_key` (Krumhansl-Schmuckler, Pearson correlation,
  with relative major/minor disambiguation). Pure numpy, no librosa, 38 tests passing, verified
  2026-08-23 to name A Minor correctly against its relative C Major. Port it rather than
  reimplementing; the remaining new work is weighting it by the active tuning as a prior.
- **Phase 3:** bridge `pitch.py` into Octave_LiveWire_maui via pythonnet (Windows first).
  Ring buffer, no Python in the audio hot path. Then wire detected key → `BassBot`, which is
  currently hardcoded to E minor (`RootMidi = 40`).

## Don't re-litigate (locked decisions)
- **The tuner stays a tuner.** No metronome, no drums. That belongs in LiveWire where
  `MasterClock` and `Sequencer` already exist and are correct.
- Note name and cents must share one reference point. See CLAUDE.md "Tuning resolution".
- `app.current_tuning` is the single owner of tuning state; `apply_tuning()` is the only writer.
- Shutdown order is stop → join → release. Never release under a live `read()`.
- `drum_kit/` is gitignored, not deleted — the tuner does not ship audio assets.
