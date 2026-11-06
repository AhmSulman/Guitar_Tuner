# play-upload/ — Guitar Tuner → Google Play

Package: `com.ahmedsalman.guitartuner`
Last bundle in Play library: **v1.0.1, versionCode 102610001** (Oct 6, 2026)
Next bundle: **v1.0.2, versionCode 102610002**
Console status (Nov 6, 2026): the internal-test draft is empty, all 11 setup tasks are open, and the closed test hasn't started.

---

## How this folder works

Only `README.md`, `FINAL_PROMPT.md` and `declarations.md` are committed. Everything else
is a **generated copy**: it's gitignored like `upload/`, so it can never drift from its source.

```bash
python store/stage_play_upload.py                     # (re)build listing/, graphics/, policy/ and validate
python store/stage_play_upload.py --aab path/to.aab   # also drop the signed bundle into build/
```

The script exits non-zero if anything breaks a Play limit. To change a listing, edit the
**source** and re-run it:

```
play-upload/
├── README.md                  ← this checklist                         (committed)
├── FINAL_PROMPT.md            ← paste to Claude after the tag run goes green (committed)
├── declarations.md            ← answers for every App content form      (committed)
├── build/
│   └── guitartuner-1.0.2-arm64-v8a-release.aab  ← GuitarTuner-AAB-signed artifact of the v1.0.2 tag run
├── listing/
│   ├── title.txt              ← buildozer.spec `title`                       12 / 30
│   ├── short_description.txt  ← store/listing.md                             71 / 80
│   ├── full_description.txt   ← store/listing.md                          1932 / 4000
│   └── release_notes.txt      ← store/release-notes.md, in <en-US> … </en-US>  386 / 500
├── graphics/
│   ├── icon-512.png           ← icon.png                       512×512 RGBA, 0.39 MB
│   ├── feature-1024x500.png   ← store/feature-graphic.png      1024×500 RGB, no alpha
│   └── phone/01.png … 05.png  ← store/screenshots/              5 × 1080×2160 RGB
└── policy/
    ├── privacy_policy.md      ← docs/privacy-policy.html, converted
    └── privacy_policy_url.txt ← https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html
```

> Never put the keystore or passwords here. They live in GitHub Secrets only. `*.keystore`, `*.jks`
> and `*.aab` are gitignored, and this repo is **public**.

---

## 1. Build

How to get the bundle (you do this, in order):
1. Merge **#14** (16 KB toolchain), then **#13** (version 1.0.2).
2. Tag `v1.0.2` on main and push the tag. The `release` job builds the **signed** AAB and runs the 16 KB
   and permission checks on it.
3. Download the `GuitarTuner-AAB-signed` artifact, then run `python store/stage_play_upload.py --aab <file>`.

The `GuitarTuner-AAB-unsigned` artifact from PR CI **can't be uploaded**: it's unsigned and still
version 1.0.1 (102610001, a duplicate).

- [ ] Output is an `.aab`
- [ ] `package` = `com.ahmedsalman.guitartuner`
- [ ] versionCode is **102610002** (> 102610001)
- [ ] Signed with the **same upload key** as the Oct 6 bundle
- [x] targetSdk **36**, which meets Play's current minimum
- [ ] `RECORD_AUDIO` is the only dangerous permission. CI fails if `INTERNET` appears. `WAKE_LOCK` would only appear if `android.wakelock` were set (it isn't).
- [x] 16 KB page size: all 12 `lib/` libraries pass and `zipalign -P 16` passes (PR #14 CI). The Python bundle check is pending the current run.

## 2. Store listing (Grow → Store presence → Main store listing)

- [x] App name: `Guitar Tuner` (12/30)
- [x] Short description (71/80)
- [x] Full description (1932/4000)
- [x] App icon 512×512
- [x] Feature graphic 1024×500
- [x] Phone screenshots: 5. These are 1:2 (1080×2160). Play accepts up to 2:1, so 9:16 isn't required.
- [ ] Category: **Music & Audio**. Tags: Music & audio tools, Utilities.
- [ ] Contact email (required, **shown publicly**). The privacy policy already lists one, so use the same address for consistency.

## 3. App content (Policy → App content)

All answers are in **`declarations.md`**.

| Task | Answer |
|---|---|
| Privacy policy | URL above (HTTP 200, has a microphone section) |
| App access / sign-in | All functionality available without special access |
| Ads | No |
| Content rating | IARC: utility, all **No** → Everyone / PEGI 3 |
| Target audience | 13–15, 16–17, 18+ (no under-13 bands) |
| Data safety | No data collected, no data shared |
| Government apps | No |
| Financial features | None |
| Health | None |
| Advertising ID | No |
| Trader status (EU DSA) | **Your call.** See declarations.md |

## 4. Testing path to production (personal-account rules)

- [ ] **Internal testing:** add the .aab, then the name `1.0.2`, the notes from `listing/release_notes.txt`, and your own email as a tester. Roll out.
- [ ] **Closed testing:** pick countries, then get **≥ 12 testers opted in for 14 consecutive days**. The opt-in link goes into `store/tester-invite.md`.
- [ ] **Apply for production** and answer Google's questions about the closed test.

---

### Done when

All boxes are ticked, internal is live on your phone, and the 14-day closed-test clock is running.
