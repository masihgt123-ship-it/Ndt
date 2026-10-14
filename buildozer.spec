[app]
title = NDT Gamma Pro
package.name = ndtgamma
package.domain = org.ndt
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,kv,atlas
version = 1.0.0
requirements = python3,kivy,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0

android.archs = arm64-v8a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.permissions = INTERNET
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
