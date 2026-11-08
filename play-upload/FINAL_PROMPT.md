# Release prompt for Claude in Chrome (Guitar Tuner, any version after 1.0.3)

> Fill in the version and versionCode, then paste everything below the line into the Claude
> extension, in the Chrome window where Play Console is open. Do steps 1–5 of
> `play-upload/README.md` first, so the signed AAB is already verified in `play-upload/build/`.

---

You're working in my Google Play Console in this Chrome window. App: **Guitar Tuner**, package
**com.ahmedsalman.guitartuner**. Goal: publish version **<VERSION>** (versionCode **<CODE>**) to
internal testing, then to the closed test.

## Rules
1. **Ask before every irreversible click:** Save, Next, Upload, Publish, Roll out, Send for review, Remove, Discard, Delete. One OK covers one click. Before each one, show me what will be submitted.
2. You can't access files on my disk. Tell me which upload box to use, and I'll drop the file in.
3. Never type or invent email addresses.
4. **STOP and tell me** if anything differs from this prompt: package, versionCode, permissions, any **error** on a review page, or a form you don't recognise.
5. Don't touch: App signing, pricing, Monetize, Advanced settings, Production, Open testing, and the old empty closed track "guitartuner-1.0.1-arm64-v8a-release".

## Expected facts
| | |
|---|---|
| Bundle | `play-upload/build/guitartuner-<VERSION>-arm64-v8a-release.aab` (signed) |
| Version name / code | **<VERSION> / <CODE>**. It must be higher than every previous code (latest released: 10003) |
| Permission | `android.permission.RECORD_AUDIO` only |
| Upload key SHA-1 | `37:83:10:AF:58:C0:12:4F:77:50:D7:BE:FA:2C:4E:88:AF:0E:85:80` |
| Expected review warnings | only "no deobfuscation file" and "no native debug symbols", both harmless. **Any error = STOP** |

## Step 1: Internal testing
Test and release → Testing → Internal testing → **Create new release**. Tell me when the upload box is showing, and I'll drop in the bundle.
After processing, check that the bundle row says **<CODE> (<VERSION>)**. Release name `<VERSION>`; paste the notes I give you, inside `<en-US>…</en-US>`.
Next → show me every error and warning → **Save and publish** (my OK).

## Step 2: Closed testing
Testing → Closed testing → **Alpha** → Create new release → **Add from library** → tick **only <CODE>** → same name and notes → Next → show me the warnings → Save (my OK).

## Step 3: Send for review
Publishing overview → list every change in "Changes not yet sent for review" → **Send changes for review** (my OK).

## Finish
Tell me the internal release status, the closed release status, and the text shown in Publishing overview.
