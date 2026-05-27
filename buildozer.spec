[app]

title = Arkanoid Roguelite
package.name = arkanoidroguelite
package.domain = com.chpomob
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,ogg,mp3
version = 1.0.1
requirements = python3,pygame

orientation = landscape
fullscreen = 1
android.permissions = VIBRATE
android.minapi = 21
android.api = 34
android.wakelock = 1
android.immersive_mode = 1
android.native_events = 1
android.entrypoint = src/main.py

[buildozer]
log_level = 2
