[app]
# App metadata
title = Guitar Tuner
package.name = guitartuner
package.domain = com.ahmedsalman

# Entry point
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav

version = 1.0.0

# Dependencies
requirements = python3,kivy==2.3.0,numpy

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
android.ndk = 25c
android.archs = arm64-v8a

# Google Play requires signed .aab (not .apk) for release submissions
android.release_artifact = aab

# Permissions
android.permissions = RECORD_AUDIO

# Microphone hardware requirement
android.manifest.uses_feature = android.hardware.microphone

# Optional: Add these later when you have the files
# android.icon.filename = icon.png
# android.presplash.filename = presplash.png

# Gradle & Activity
android.activity_class_name = org.kivy.android.PythonActivity

# Pin p4a to v2024.01.21 — uses Python 3.11.5, compatible with Kivy 2.3.0.
# p4a master uses Python 3.14 which breaks Kivy 2.3.0's Cython C code.
p4a.branch = v2024.01.21

# Accept SDK licenses (must be in [app] section — [buildozer] section is ignored)
android.accept_sdk_license = True

[buildozer]
log_level = 2
android.skip_update = False