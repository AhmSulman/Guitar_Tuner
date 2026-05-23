[app]

# App metadata
title           = Guitar Tuner
package.name    = guitartuner
package.domain  = com.ahmedsalman

# Entry point
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav
version         = 1.0.0

# Dependencies (pip-installable names for python-for-android)
requirements = python3==3.11.0,kivy==2.3.0,numpy,pyaudio,hostpython3==3.11.0

# Optional: pre-compiled wheels directory
#p4a.local_recipes = ./p4a_recipes

# Orientation
orientation = portrait

# Android settings
android.api             = 34
android.minapi          = 26
android.ndk             = 25c
android.sdk             = 34
android.archs           = arm64-v8a

# Required permissions
android.permissions     = RECORD_AUDIO,INTERNET
# Declare microphone hardware required (prevents install on mic-less devices)
android.manifest.uses_feature = android.hardware.microphone

# Fullscreen — no system bar (optional; set to 0 for status bar)
fullscreen = 0

# App icon & presplash (place icon.png and presplash.png in project root)
# android.presplash.filename = presplash.png
# android.icon.filename       = icon.png

# Gradle
android.gradle_dependencies =

# Activity class (default)
android.activity_class_name = org.kivy.android.PythonActivity

# Enable hardware acceleration
android.meta_data = android:hardwareAccelerated=true

# Target specific OpenGL ES version
android.opengl_es_version = 2

# Python-for-android branch
p4a.branch = master

# Extra Java dirs (none needed)
android.add_jars =

# Logcat filters during buildozer run
android.logcat_filters = *:S python:D

# Build directory
android.release_artifact = apk

[buildozer]

# Build logs
log_level = 2

# Warn on .apk missing in dist
warn_on_root = 1

# Use global buildozer home cache
android.skip_update = False

# If you hit SSL errors, set:
# android.accept_sdk_license = True
