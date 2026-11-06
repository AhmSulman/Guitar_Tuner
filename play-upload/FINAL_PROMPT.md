# Publish Guitar Tuner 1.0.2 — prompt for Claude in Chrome

> Paste everything below the line into the Claude extension, in the Chrome window where Play Console is open.
> The listing text below is a copy of `play-upload/listing/`. If `store/listing.md` changes, re-run
> `python store/stage_play_upload.py` and update the blocks here to match.

---

You're working in my Google Play Console in this Chrome window. App: **Guitar Tuner**, package
**com.ahmedsalman.guitartuner**. This is a personal developer account, so the app needs a closed test with
12+ testers for 14 days before it can go to production. Today's goal is to get **internal testing live**
and the **closed test sent for review**. Everything you need is in this message. Don't use other sources.

## Rules: these override everything below

1. **Ask before every irreversible click.** That means Save, Next, Submit, Apply, Upload, Roll out,
   Send for review, Discard, Delete, Start, or anything that sends something to Google. Before each one,
   show me exactly what will be submitted. One OK covers one click.
2. **You can't access files on my disk.** When a file is needed, tell me the exact path below and which
   upload box it goes in. I'll drop it in, then you continue.
3. **Never type, copy or invent email addresses.** The tester list comes only from the CSV I upload. For
   any email field (contact, content-rating, feedback), ask me.
4. **STOP and tell me** if anything differs from this prompt: a different version code, package name or
   permission, any error or warning after processing, a field this prompt doesn't cover, or a form whose
   questions don't match. Don't work around it.
5. **My decisions. Ask, don't pick:** trader status, every email address, the countries for the closed test,
   and whether to turn on managed publishing.
6. **Don't touch:** App signing settings, pricing (the app is free), Monetize, Advanced settings,
   Production, or Open testing.

## Expected facts: check against these

| | Expected |
|---|---|
| Package | com.ahmedsalman.guitartuner |
| Bundle | `C:\dev\Guitar_Tuner\play-upload\build\guitartuner-1.0.2-arm64-v8a-release.aab` (signed) |
| Version name / code | **1.0.2 / 102610002** |
| Already in the library | 1.0.1 / 102610001 (Oct 6). **Never add, reuse or promote it** |
| Permission Play should list | `android.permission.RECORD_AUDIO` only |
| Target / min SDK | 36 / 26 (Android 8.0+) |
| Privacy policy | https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html |

---

## Step 0: Look around (read-only, change nothing)
Report back, then wait for me:
1. **Dashboard:** list every open item under "Set up your app" and the testing checklist.
2. **Test and release → App integrity → App signing:** the **Upload key certificate SHA-1**, exactly as shown.
   I'll compare it with the bundle's signature. **No bundle gets uploaded until I say "SHA-1 matches".**
3. **Publishing overview:** is managed publishing on or off? Are there any pending changes?
4. **Testing → Internal testing** and **Closed testing:** which tracks exist, and their status and releases.
5. Any existing **email lists**, by name and count only.

## Step 1: App content (Policy → App content)
For each form: fill it in, **show me every answer**, then Save/Submit on my OK.

| Form | Answer |
|---|---|
| Privacy policy | `https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html` |
| App access | **All functionality is available without any access restrictions** |
| Ads | **No, my app does not contain ads** |
| Content rating | Email: **ask me.** Category: the utility / productivity / "all other app types" option. Not a game, and not social or communication. Answer **No** to every content question: violence, blood, sexual content, profanity, crude humour, drugs/alcohol/tobacco, gambling (real or simulated), users interacting or sharing content, sharing location, digital purchases, unrestricted internet access. **Show me the calculated ratings before you apply them.** Expected: Everyone / PEGI 3 / USK 0 |
| Target audience | Tick **13–15, 16–17, 18 and over** only. **No** under-13 bands. "Could your store listing unintentionally appeal to children?" **No** |
| Data safety | "Does your app collect or share any of the required user data types?" **No.** Reason, if a field asks: the app processes microphone audio in memory on the device only, never stores or sends it, and has no INTERNET permission. **Show me the preview label before you submit.** Expected: "No data collected · No data shared" |
| Advertising ID | **No**, the app does not use an advertising ID |
| Government apps | **No** |
| Financial features | **My app doesn't provide any financial features** |
| Health | **My app does not have any health features** |
| News apps | **No** |
| Anything else listed | STOP and show me the questions |

**Trader status (EU DSA):** this may sit under the app or under the account settings. **Ask me.** Don't answer it.

## Step 2: Store settings (Grow → Store presence → Store settings)
- App category: **Apps → Music & Audio**
- Tags: **Music & audio tools**, plus **Utilities** if it's offered. Show me the tag list before saving.
- Contact email: **ask me.** Phone: leave blank. Website: leave blank.
- Save on my OK.

## Step 3: Main store listing (Grow → Store presence → Main store listing, en-US)
Paste exactly:

**App name**
```
Guitar Tuner
```
**Short description**
```
Precision guitar tuner. 12 tunings, works offline, no ads, no tracking.
```
**Full description**
```
A precision guitar tuner that does one job properly.

Guitar Tuner listens through your microphone and shows you exactly how far off you are, in cents, on a smooth analogue-style needle. No sign-up, no ads, no tracking, and no internet connection required — ever.

WHY IT'S DIFFERENT

Most free tuners want an account, show you ads, or quietly send your usage somewhere. This one does none of that. It has no internet permission at all, which means Android itself prevents it from transmitting anything. Your playing never leaves your phone — it is never recorded, never saved, and never uploaded.

12 TUNINGS, ALL FREE

• Standard — E A D G B E
• Drop D — D A D G B E
• Double Drop D — D A D G B D
• Drop C — C G C F A D
• DADGAD — D A D G A D
• Open G — D G D G B D
• Open D — D A D F# A D
• Open E — E B E G# B E
• Open A — E A E A C# E
• Open C — C G C G C E
• Half Step Down — Eb Ab Db Gb Bb Eb
• Full Step Down — D G C F A D

No paywall on alternate tunings. They are all there from the first launch.

BUILT FOR ACTUAL TUNING

• Auto-detect finds the nearest string and lights it up as you play
• Tap any string to lock onto it — essential when you are retuning a long way, like dropping E down to C
• Honest readings. If you are nowhere near a string in the current tuning, it says so instead of pretending you are 50 cents flat
• Remembers your tuning and locked string between sessions
• Clear signal meter so you know it is hearing you

HOW TO USE IT

1. Pick your tuning from the dropdown
2. Play a string
3. Turn the peg until the needle centres and it reads In Tune

For a big retune, tap the target string first so the tuner follows that string all the way down rather than jumping to whichever is closest.

PERMISSIONS

Microphone only, and only while the app is open. That is what a tuner does. There is no other permission, and there is no network access.

Works on phones and tablets running Android 8.0 and above.
```
**Graphics.** Tell me each upload box as you reach it, and I'll drop the file in:
- App icon: `C:\dev\Guitar_Tuner\play-upload\graphics\icon-512.png`
- Feature graphic: `C:\dev\Guitar_Tuner\play-upload\graphics\feature-1024x500.png`
- Phone screenshots, in this order: `C:\dev\Guitar_Tuner\play-upload\graphics\phone\01.png`, `02.png`, `03.png`, `04.png`, `05.png`
- Video, tablet, Chromebook and TV assets: leave empty.

Show me the full listing, then Save on my OK.

## Step 4: Tester list
Create an email list called **Guitar Tuner testers** (from the Testers tab of Internal testing, or under Settings → Email lists).
- Choose **Upload CSV file**. I'll upload `C:\dev\Guitar_Tuner\private\testers.csv` (19 addresses, one per line, no header).
- Tell me how many addresses Play accepted. Expect **19**. Report any rejected ones by count. Don't read out addresses.
- Save on my OK.

## Step 5: Internal testing release
**Wait until I say "SHA-1 matches"** (see Step 0) before asking for the bundle.
1. **Testing → Internal testing → Testers:** tick **Guitar Tuner testers**. Save on my OK.
2. **Releases → Create new release.** If Play asks about Play App Signing, STOP and ask me.
3. Tell me when the App bundles upload box is showing. I'll upload the bundle from the Expected facts table.
4. After processing, report the version code and name (must be **102610002 / 1.0.2**), and **every** error and warning, word for word. Anything unexpected: STOP.
5. Release name: `1.0.2`
6. Release notes: paste exactly, tags included:
```
<en-US>
First test build. Thanks for installing.

Point your phone's mic at a guitar and tune. Pick a tuning from the dropdown — 12 are included, from Standard to Drop C and DADGAD. Tap a string to lock onto it when you're retuning a long way.

Please leave it installed for the full two weeks, even if you don't open it again. If anything looks wrong, just reply to the email that invited you.
</en-US>
```
7. **Next** (my OK), then show me the review page, including any warnings. Then **Save and roll out to Internal testing** (my OK).
8. Give me the internal-test **join link** from the Testers tab.

## Step 6: Closed testing
1. **Testing → Closed testing:** use the existing closed track, or create one named **Closed test** (my OK).
2. **Countries / regions:** ask me for the list. It must include Pakistan and the United Kingdom. Save on my OK.
3. **Testers:** tick **Guitar Tuner testers**. For "Feedback URL or email address", **ask me**. Save on my OK.
4. **Create new release → Add from library →** pick **1.0.2 (102610002)**. **Not** 1.0.1. Then the same release name `1.0.2` and the same notes as Step 5.
5. Next, then show me the review page and every warning. Save (my OK).
6. If managed publishing is on, or Play shows **"Send changes for review"** (on the release page or Publishing overview), list exactly which changes it will send, and click only on my OK.
7. Give me the closed-test **opt-in URL**. I'll send it to testers myself.

## Finish
Give me:
- a table of **Done / Waiting on Google / Blocked**, covering every Dashboard setup item and both tracks
- anything Play still marks as required
- the earliest date the closed-test requirement can be met: the first day **12+ testers are opted in**, plus **14 consecutive days**. If the review is still pending, say "review date + 14 days, at the earliest".
- my next 3 actions
