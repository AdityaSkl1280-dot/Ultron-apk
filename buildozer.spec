[app]
title = Ultron AI
package.name = ultronai
package.domain = org.ultron.ai
source.dir = .
source.include_exts = py,png,jpg,json
version = 1.0

requirements = python3,kivy,requests,edge-tts,pyjnius,android,certifi,yt-dlp

orientation = all
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE,CALL_PHONE,READ_PHONE_STATE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a

services = ultroncore:service/main.py:foreground:sticky

[buildozer]
log_level = 2
warn_on_root = 1
