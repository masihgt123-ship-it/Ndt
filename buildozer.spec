[app]

title = NDT Safe Distance
package.name = ndtsafedistance
package.domain = com.industrialradiographyiran

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,kv,atlas

version = 1.0

requirements = python3,kivy,arabic-reshaper,python-bidi

orientation = portrait

fullscreen = 0

android.permissions = INTERNET

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/company_banner.png

android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.accept_sdk_license = True

android.archs = arm64-v8a

android.allow_backup = True

android.logcat_filters = *:S python:D

[buildozer]

log_level = 2
warn_on_root = 1
