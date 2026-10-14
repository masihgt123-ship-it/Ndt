[app]
title = NDT Gamma Radiation Calculator
package.name = ndtgamma
package.domain = org.ndtgamma
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = *.ttf

version = 1.0
requirements = python3,kivy==2.3.0,pillow

orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
android.accept_sdk_license = True
