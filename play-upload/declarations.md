# App content declarations — Guitar Tuner

Answers for **Policy → App content** in Play Console. They're based on what the app does:
- one permission, `RECORD_AUDIO`
- no `INTERNET` (CI fails the build if it appears)
- no SDKs beyond Kivy and NumPy
- no accounts, ads or purchases

**If the app ever gains a permission or an SDK, re-check this file before the release that adds it,
and update the privacy policy first. The policy promises exactly that.**

---

## Privacy policy
`https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html`

## App access (sign-in details)
**All functionality in my app is available without any access restrictions.**
There's no login, no paywall and no region gate.

## Ads
**No, my app does not contain ads.**

## Content rating (IARC questionnaire)
- Email: your developer contact email.
- Category: the utility / productivity / "all other app types" option. **Not** a game, and **not** social or communication.
- Every question gets **No**:
  - violence, blood or gore
  - sexual content or nudity
  - profanity or crude humour
  - drugs, alcohol or tobacco
  - gambling, real or simulated
  - users can interact or exchange content
  - shares the user's location
  - digital purchases
  - unrestricted internet access
- Expected rating: **Everyone / PEGI 3 / USK 0 / ClassInd L**.

## Target audience and content
- Target age groups: **13–15, 16–17, 18 and over**.
- Leave **5 and under, 6–8, 9–12 unticked**. Any under-13 band brings in the Families policy (teacher-approved program checks, Families ad and SDK rules). The app isn't designed for children, even though children can use it. The privacy policy says the same thing ("general-audience utility … not directed at children").
- "Could your store listing unintentionally appeal to children?" **No.**

## Data safety
| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **No** |

Why that's accurate:
- **Microphone audio** is analysed in memory for a fraction of a second and discarded. It's never stored or transmitted, and the OS blocks transmission anyway because there's no `INTERNET` permission. Google defines "collection" as data sent off the device, so on-device-only processing doesn't count.
- **`tuner_cache.json`** (tuning, locked string, launch count, last-opened time) stays in app-private storage. It never leaves the device and contains no identifiers.

Resulting label: **"No data collected · No data shared with third parties"**. The security-practices questions (encryption in transit, deletion requests) aren't asked once you answer No.

## Government apps
**No.**

## Financial features
**My app doesn't provide any financial features.**

## Health
**My app does not have any health features.**

## News apps
**No.**

## Advertising ID
**No.** The app doesn't use the advertising ID. There's no `com.google.android.gms.permission.AD_ID` and no ads or analytics SDK.

## Permissions declarations
None required. `RECORD_AUDIO` isn't a restricted permission. There's no SMS or call log access, no background location, no all-files access, no foreground service, and no exact alarms.

---

## Trader status (EU Digital Services Act) — your decision

Play asks whether you're a **trader**, meaning someone acting for purposes relating to a trade, business, craft or profession.

| | Non-trader | Trader |
|---|---|---|
| Fits when | Personal, free app: no ads, no in-app purchases, no business behind it | You monetise or distribute as a business |
| Published on the listing | Nothing extra. EU users see "not a trader" and that consumer-protection law may not apply | Your **address, phone, email** and verification status |
| This app today | Free, no ads, no IAP, open source | — |

**Recommendation: non-trader**, given how the app is distributed today. This is a legal self-declaration
about your own situation, though, so it's your answer to give, not mine. If you later add paid
features or publish under a business, change it then.
