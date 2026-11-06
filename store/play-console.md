# Play Console — every form, pre-answered

Answers for each Play Console page that has to be filled in before the first closed-test
release can be sent for review. Each answer is based on what the app actually does: one
permission (`RECORD_AUDIO`), no `INTERNET`, no SDKs, no accounts.

If the permissions ever change, re-check the **Data safety** and **Ads** sections first.

---

## Assets checklist

| Asset | File | Play requirement | Status |
|---|---|---|---|
| App icon | `icon.png` | 512×512, 32-bit PNG, ≤1 MB | ✅ 512×512 RGBA, 0.39 MB |
| Feature graphic | `store/feature-graphic.png` | 1024×500, JPEG or 24-bit PNG, no alpha | ✅ 1024×500 RGB |
| Phone screenshots | `store/screenshots/01–05` | 2–8, ≤2:1, no alpha | ✅ 5 × 1080×2160 RGB |
| Short description | `store/listing.md` | ≤80 chars | ✅ 70 chars |
| Full description | `store/listing.md` | ≤4000 chars | ✅ ~1,900 chars |
| Release notes | `store/release-notes.md` | ≤500 chars | ✅ 382 chars (closed-test version) |
| Privacy policy URL | `docs/privacy-policy.html` | Public, non-PDF | ✅ https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html (HTTP 200) |

Tablet screenshots are optional. Leave them empty rather than upload stretched phone shots.

---

## Store settings

- **App category:** Music & Audio
- **Tags:** Music & audio tools, Utilities (pick at most 5. Only these two really fit)
- **Contact email:** required, and shown publicly on the listing. Use an address you're happy to have public.
- **Website:** optional. `https://github.com/AhmSulman/Guitar_Tuner` is fine, or leave it blank.

---

## App content (Policy → App content)

### Privacy policy
`https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html`

### Ads
**No, my app does not contain ads.**

### App access
**All functionality is available without any access restrictions.** There's no login and nothing is gated.

### Content rating (IARC questionnaire)
- Category: the **utility / productivity / "all other app types"** option. Not a game, and not social or communication.
- Every content question: **No**. That covers violence, sexuality, language, controlled substances, gambling, user interaction/communication, sharing location, and digital purchases.
- Expected result: **Everyone / PEGI 3 / USK 0**.

### Target audience and content
- Age groups: **13–15, 16–17, 18 and over**.
- **Don't** tick any age band under 13. Including children brings in the Families policy and teacher-approved requirements. The app isn't designed for children, even though children can use it.
- "Could your store listing unintentionally appeal to children?": **No**.

### Data safety
The microphone audio is processed **only on the device**, held in memory for a fraction of a second, and never stored or sent. Google's definition of "collected" means sent off the device, so on-device-only processing doesn't count. The same goes for `tuner_cache.json` (last tuning, locked string), which stays on the device.

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **No** |
| Is all of the user data collected by your app encrypted in transit? | *(not asked once you answer No above)* |
| Do you provide a way for users to request that their data is deleted? | *(not asked)* |

The resulting listing label reads: **"No data collected · No data shared with third parties."**

### Government apps
**No.**

### Financial features
**My app doesn't provide any financial features.**

### Health
**My app does not have any health features.**

### News app
**No.**

### Advertising ID
**No**, the app does not use an advertising ID. There's no `AD_ID` permission and no ads SDK.

### Permissions declarations
None needed. `RECORD_AUDIO` isn't a restricted permission (unlike SMS, call log, location in the background, or all-files access). There's no foreground service, so no foreground-service declaration either.

---

## Release (Testing → Closed testing)

1. **Create track** (or use the default *Alpha* closed track). Name it e.g. "Closed test".
2. **Testers** tab: add an email list containing all 12+ tester Google accounts. Use the roster in `private/`, which is gitignored.
3. **Countries/regions**: add every country your testers are in. If you skip this, they can't install the app.
4. **Create new release**: upload `guitartuner-1.0.2-arm64-v8a-release.aab` from the `GuitarTuner-AAB-signed` artifact of the `v1.0.2` tag run. Play will show version code **102610002**.
5. Release name: `1.0.2`. Release notes: the closed-test block from `store/release-notes.md`.
6. **Review release → Start rollout to Closed testing.**
7. Copy the **opt-in URL** from the Testers tab into `store/tester-invite.md`'s template, and send it to the testers.

### The 14-day clock (personal developer accounts created after Nov 2023)
- It starts when **12 testers are opted in**, not when you upload. It needs **14 consecutive days** with at least 12 opted in.
- A tester who opts out resets the count, so recruiting extras was the right call.
- The first review of a closed-test release can take a few days. Testers can't install until it's approved.
- After the 14 days, **Dashboard → Apply for production**. Google asks about the test (how many testers, what feedback you got, what you changed), then reviews it, which typically takes about 7 days. Only then can you roll out to production.

---

## Signing: check before the first upload

The AAB is signed in CI with the keystore in GitHub Secrets. Play only accepts it if that key matches the **upload key** registered under **Test and release → App integrity → App signing**.

- If an earlier draft (version code 102610001) was uploaded, the upload key is already registered, and the CI key must match it.
- If Play rejects the upload with *"signed with the wrong key"*, the secret holds a different keystore. `generate-keystore.yml` ran twice, on 6 Jul and 17 Sep. Use the upload-key reset in the main checklist.
