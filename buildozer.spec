[app]
title = Guitar Tuner
package.name = guitartuner
package.domain = com.ahmedsalman

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav

version = 1.0.0

# Requirements
requirements = python3,kivy==2.3.0,numpy,plyer

# Remove pyaudio for now
# If you need audio input, use plyer instead (much more reliable on Android)

orientation = portrait
fullscreen = 0

# Android settings
android.api = 34
android.minapi = 26
android.ndk = 25c
android.sdk = 34
android.archs = arm64-v8a, armeabi-v7a   # Better to include both

android.permissions = RECORD_AUDIO, INTERNET

# Microphone requirement
android.manifest.uses_feature = android.hardware.microphone:true

# Optional: Add icon and presplash later
# android.icon.filename = icon.png
# android.presplash.filename = presplash.png

[buildozer]
log_level = 2
android.skip_update = False
android.accept_sdk_license = True 