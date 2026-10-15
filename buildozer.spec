[app]

title = ایمنی پرتو
package.name = ndtsafedistance
package.domain = com.industrialradiographyiran

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf

version = 1.0

requirements = python3,kivy,arabic-reshaper,python-bidi

orientation = portrait

fullscreen = 0

android.permissions = INTERNET

# ----------------- تنظیمات آیکون و اسپلش (حل قطعی مشکل آیکون) -----------------
# آیکون کلاسیک (اندرویدهای قدیمی)
icon.filename = %(source.dir)s/logo.png

# آیکون تطبیقی جدید (اندروید 8 تا 14 - حیاتی برای گوشی‌های جدید)
icon.adaptive_foreground.filename = %(source.dir)s/logo.png
icon.adaptive_background.filename = %(source.dir)s/logo.png

# تصویر صفحه شروع (Splash Screen)
presplash.filename = %(source.dir)s/company_banner.png
# --------------------------------------------------------------------------

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
