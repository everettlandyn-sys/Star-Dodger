[app]
title = Star Dodger
package.name = stardodger
package.domain = org.everettlandyn
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
# Avoid the CPython 3.14 Android wheel that p4a currently rejects with host pip.
requirements = python3,kivy,charset-normalizer==2.1.1
orientation = portrait
fullscreen = 1
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
