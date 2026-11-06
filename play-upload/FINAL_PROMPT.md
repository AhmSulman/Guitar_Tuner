The `v1.0.2` tag run succeeded. My Play Console tab (Guitar Tuner, com.ahmedsalman.guitartuner) is open.

Repo: https://github.com/AhmSulman/Guitar_Tuner (local: C:\dev\Guitar_Tuner)
Run: <link to the green `v1.0.2` tag run: Actions → "Build Guitar Tuner APK" → the run for tag v1.0.2>
Bundle: play-upload/build/guitartuner-1.0.2-arm64-v8a-release.aab  (version name: 1.0.2, versionCode: 102610002)
  (staged with `python store/stage_play_upload.py --aab <downloaded GuitarTuner-AAB-signed file>`)

Do this in order. Stop before any irreversible click (Upload, Save, Next, Roll out, Submit) and ask me first.

1. VERIFY THE BUILD before anything goes to Play. Run these locally (Java 17 is installed):
   - `java -jar bundletool.jar dump manifest --bundle=<aab>`. Confirm the package is com.ahmedsalman.guitartuner,
     versionCode 102610002 (> 102610001), versionName 1.0.2, and targetSdkVersion 36.
   - Confirm it's an .aab and not the GuitarTuner-AAB-unsigned PR artifact. That one is unsigned and 102610001.
   - `keytool -printcert -jarfile <aab>`: give me the SHA-1. I'll compare it to Play Console → Test and release →
     App integrity → Upload key certificate. If it doesn't match, STOP. Don't upload. Go to the
     upload-key reset checklist instead.
   - List every uses-permission in the manifest and flag anything beyond RECORD_AUDIO
     (INTERNET would contradict the listing, the privacy policy and declarations.md).
   - Confirm the tag run's "Verify 16 KB page alignment (signed AAB)" step passed, including the Python
     extension modules from libpybundle.so and zipalign -P 16 on the split APKs.

2. AUDIT play-upload/ against play-upload/README.md
   - Re-run `python store/stage_play_upload.py` and show its table (text lengths, image sizes/alpha, count).
   - Check the privacy policy URL in policy/privacy_policy_url.txt still returns 200 publicly and has the microphone section.
   - Report anything missing or invalid as a short table.

3. INTERNAL TESTING DRAFT (release 5, currently empty)
   - Tell me exactly which file to drop into "Upload". You can't upload files for me, so I'll do it.
   - After I upload, check that Play's processing shows no errors or warnings. Then fill in the release name `1.0.2`
     and the en-US notes from listing/release_notes.txt, and wait for my OK before Next / Roll out.

4. FILL THE STORE LISTING + APP CONTENT forms from play-upload/listing, play-upload/graphics and
   play-upload/declarations.md. Show me each form's answers before saving. Trader status and the
   public contact email are my decisions. Ask me, don't pick.

5. Finish with what's still blocking production (closed test: 12 testers × 14 days) and the next
   3 actions for me.
