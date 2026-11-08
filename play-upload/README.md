# play-upload/ — Guitar Tuner → Google Play

Package: `com.ahmedsalman.guitartuner`

## Status (8 Nov 2026)

| | |
|---|---|
| Released | **1.0.3, versionCode 10003** (tag `v1.0.3`). **Live on internal testing** and checked on a Pixel |
| Closed test | Alpha track, 1.0.3, countries **Canada, Pakistan, UAE, UK**, testers = email list "testers". **Sent for Google review on 8 Nov** |
| App content, store listing, store settings | All submitted (see `store/play-console.md`) |
| Burned version codes | `102610001` (1.0.1) and `102610002` (1.0.2): uploaded, never released, never reusable |
| Next milestone | Closed test approved → 12+ testers opted in for 14 consecutive days → apply for production |

---

## How this folder works

Only `README.md`, `FINAL_PROMPT.md` and `declarations.md` are committed. Everything else is a
**generated or downloaded copy**, gitignored like `upload/`, so it can never drift from its source:

```bash
python store/stage_play_upload.py                     # (re)build listing/, graphics/, policy/ and validate
python store/stage_play_upload.py --aab path/to.aab   # also drop the signed bundle into build/
```

```
play-upload/
├── README.md · FINAL_PROMPT.md · declarations.md      (committed)
├── build/       ← signed .aab + VERIFIED.txt           (gitignored)
├── listing/     ← title, short/full description, release_notes  ← store/listing.md, store/release-notes.md
├── graphics/    ← icon-512, feature-1024x500, phone/01–05 (9:16)  ← icon.png, store/
└── policy/      ← privacy_policy.md + URL               ← docs/privacy-policy.html
```

The tester roster and call sheet live in `private/` (gitignored). **This repo is public:** never put
tester emails, the keystore or passwords here.

---

## Next release: the checklist

1. **Bump both** in `buildozer.spec`: `version = 1.0.4` **and** `android.numeric_version = 10004`
   (`major*10000 + minor*100 + patch`). CI fails a versionCode above 1,000,000, and Play rejects a reused one.
2. Update the notes in `store/release-notes.md` (≤500 chars).
3. PR → green CI (16 KB, permissions, versionCode checks) → merge.
4. Tag `v1.0.4` on main and push it. The `release` job builds the **signed** AAB and re-runs every check on it.
5. Download `GuitarTuner-AAB-signed` → `python store/stage_play_upload.py --aab <file>` → verify:
   - `bundletool dump manifest`: versionCode, versionName, targetSdk, `RECORD_AUDIO` only
   - `keytool -printcert -jarfile`: SHA-1 `37:83:10:AF:…:85:80` (the registered upload key)
6. Play Console: Internal testing → Create new release → upload the AAB (it's ~29 MB, so drag it in) →
   name + notes → review (expect only the 2 harmless warnings: deobfuscation, native debug symbols) → publish.
7. Closed testing → Alpha → Create new release → **Add from library** → same versionCode → name + notes → save →
   Publishing overview → **Send changes for review**.

`FINAL_PROMPT.md` is a ready-made prompt for Claude in Chrome to do steps 6–7 with you.

---

## Testing path to production (personal-account rules)

- [x] Internal testing: 1.0.3 live, installed and smoke-tested on a Pixel
- [x] Closed testing: release, countries and testers set up, sent for review
- [ ] Closed test approved → send the opt-in link `https://play.google.com/apps/testing/com.ahmedsalman.guitartuner`
- [ ] **≥ 12 testers opted in for 14 consecutive days.** Recruit extras: one drop-out can push you below 12
- [ ] Apply for production (Dashboard) and answer Google's questions about the test
