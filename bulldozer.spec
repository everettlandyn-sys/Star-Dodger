
[app]

title = Star Dodger

package.name = stardodger

package.domain = org.everettlandyn

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy

orientation = portrait

fullscreen = 1

[buildozer]

log_level = 2

warn_on_root = 1

[app:android]

android.permissions =

android.api = 35

android.minapi = 23

android.archs = arm64-v8a

android.accept_sdk_license = True
