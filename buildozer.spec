[app]

title = شرکت رادیوگرافی صنعتی ایران
package.name = ndtsafedistance
package.domain = com.industrialradiographyiran

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer

version = 1.0

requirements = python3,kivy==2.3.1,arabic-reshaper==3.0.0,python-bidi==0.4.2,six==1.17.0

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/company_banner.png

android.api = 34
android.minapi = 23
android.ndk = 25b
android.accept_sdk_license = True

android.archs = arm64-v8a
android.allow_backup = False
android.logcat_filters = *:S python:D

[buildozer]

log_level = 2
warn_on_root = 1
