[app]

# App metadata
title = Arkanoid Roguelite
package.name = arkanoidroguelite
package.domain = com.chpomob
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,ogg,mp3
version = 1.0.1
requirements = python3==3.12.7,hostpython3==3.12.7,pygame-ce,cython

# Orientation: portrait or landscape
orientation = landscape

# Fullscreen immersive mode
fullscreen = 1

# Android permissions
android.permissions = VIBRATE

# Min / target SDK
android.minapi = 21
android.api = 34
android.ndk = 27
android.sdk = 34

# App icon placeholder (48x48 PNG)
# icon = icon.png
# presplash = splash.png

# Hide the status bar
android.wakelock = 1
android.immersive_mode = 1

# Input: use SDL touch
android.native_events = 1

# Python bundle
android.entrypoint = src/main.py

[buildozer]

# Log level (debug/info/warning/error)
log_level = 2

# Cross-compiler archs
archs = arm64-v8a

# Docker image (saves environment hell)
docker_image = kivy/buildozer:latest
