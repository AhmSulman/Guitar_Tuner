[app]
# App metadata
title = Guitar Tuner
package.name = guitartuner
package.domain = com.ahmedsalman

# Entry point
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav

version = 1.0.1

# Dependencies
requirements = python3,kivy==2.3.1,numpy

# Orientation
orientation = portrait
fullscreen = 0

# Android settings
# API 36 (Android 16) — Google Play has required this for ALL new submissions and
# updates since 2026-08-31. API 35 is rejected. p4a does not validate the upper
# bound (MIN_TARGET_API = 30; nothing checks above RECOMMENDED_TARGET_API), so a
# target above its recommendation builds fine as long as the SDK platform resolves.
android.api = 36
android.minapi = 26
# NDK 28b: 16 KB page alignment is the DEFAULT from r28 onward. Google Play has
# required 16 KB support for anything targeting Android 15+ since 2025-11-01, and
# we target 36 — so this is a hard blocker, not a warning. Under NDK 25c every
# .so came out p_align=4096; the requirement is 16384.
# p4a v2024.01.21 declares MAX_NDK_VERSION = 25 but only *warns* above it, so a
# newer NDK is accepted. Whether every recipe still compiles is what the build
# proves.
android.ndk = 28c
android.archs = arm64-v8a

# Google Play requires signed .aab (not .apk) for release submissions
android.release_artifact = aab

# Permissions
android.permissions = RECORD_AUDIO

# Microphone hardware requirement
android.manifest.uses_feature = android.hardware.microphone

# Launcher icon. NOTE the option name: buildozer reads `icon.filename`, NOT
# `android.icon.filename` — the android.* form is silently ignored and you ship
# p4a's default Kivy logo instead. Verified by extracting base/res/mipmap/icon.png
# from a built AAB; check it there rather than trusting the build to be green.
icon.filename = icon.png

# Adaptive icon (API 26+). android.minapi is 26, so EVERY target device uses
# these two layers and the legacy icon above is effectively a fallback that
# never fires. Foreground is the badge at 66% on transparency — adaptive icons
# are a 108dp canvas with only the centre 66dp guaranteed visible, so art any
# larger gets clipped by the launcher's circle or squircle mask.
icon.adaptive_foreground.filename = icon_fg.png
icon.adaptive_background.filename = icon_bg.png

# Optional: add when you have one
# presplash.filename = presplash.png

# Gradle & Activity
android.activity_class_name = org.kivy.android.PythonActivity

# p4a v2026.05.09 (the latest tagged release, not master) — required for the
# 16 KB page-size work. The previous pin, v2024.01.21, bundles an SDL2 that calls
# ALooper_pollAll, which NDK r28 turned into a hard error:
#   SDL_androidsensor.c:164: error: 'ALooper_pollAll' is unavailable: obsoleted
# So the NDK could not move without the pin moving too. This release recommends
# NDK 28c, which is why the two are matched above.
# The old pin's comment warned that p4a *master* ships Python 3.14 and breaks
# Kivy 2.3.0's Cython. This is a tagged release rather than master, and Kivy is
# bumped to 2.3.1 alongside — which also closes the long-standing gap where
# requirements.txt tested 2.3.1 on desktop while Android shipped 2.3.0.
p4a.branch = v2026.05.09

# Accept SDK licenses (must be in [app] section — [buildozer] section is ignored)
android.accept_sdk_license = True

[buildozer]
log_level = 2
android.skip_update = False