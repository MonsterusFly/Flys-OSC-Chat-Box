# Third-party licenses and attribution

This document applies to Fly's OSC Chat Box source and RPM packaging. The
project source is MIT-licensed (`LICENSE`), except for identified third-party
assets. Licenses of independently installed packages remain with those packages.

| Component | License | Distribution method | Upstream |
| --- | --- | --- | --- |
| Noto Color Emoji-derived 48 PNGs | OFL-1.1 (font glyph origin) | Bundled assets | https://github.com/googlefonts/noto-emoji |
| PySide6 / Qt | LGPL-3.0 or applicable GPL/commercial options | System dependency (RPM); PyPI dependency (user installer) | https://doc.qt.io/qtforpython-6/ |
| psutil | BSD-3-Clause | System dependency (RPM); PyPI dependency (user installer) | https://github.com/giampaolo/psutil |
| Pillow | MIT-CMU | System dependency (RPM); PyPI dependency (user installer) | https://github.com/python-pillow/Pillow |
| python-osc | Unlicense | Optional PyPI dependency; built-in OSC fallback in RPM | https://github.com/attwad/python-osc |
| playerctl | LGPL-3.0-or-later (verify installed distribution's metadata) | Optional system program, not bundled | https://github.com/altdesktop/playerctl |
| dbus-next | MIT | Historical development dependency; not in v1.2 requirements | https://github.com/altdesktop/python-dbus-next |

## Bundled Noto emoji graphics

The 48 PNGs at `assets/emoji/` were verified to match the rasterized glyph
output of `core/emoji_icons.py` using the installed NotoColorEmoji.ttf and
Pillow, pixel-for-pixel at 64x64. See `assets/emoji/NOTICE.txt` and the
complete `LICENSES/OFL-1.1.txt`. They are not covered by the app's MIT license.

Noto Emoji's upstream repo licenses **font files** under OFL-1.1 and its
separate image/tool resources mostly under Apache-2.0. Since these icons
were rasterized from the font, the font source is the applicable attribution
for our bundled output; no font file itself is included.

## PySide6 / Qt requirements

The RPM depends on Fedora-distributed `python3-pyside6` and dynamically uses
the installed Qt libraries; it does not bundle or modify Qt libraries. The
user-local installer downloads PySide6 via pip, rather than embedding wheels
in the source ZIP. For LGPL compliance, provide license information, do not
restrict replacement/debugging of the library, and keep the dependency
separate. Reassess if a self-contained executable is ever distributed.

## Attribution when bundling dependencies

The source and RPM packages do **not** vendor psutil, Pillow, playerctl,
PySide6, or their binaries. License notices for these libraries are shipped
by the corresponding distribution packages or PyPI wheels. If we later
ship a self-contained build, collect and include the full notices/licenses
for each exact wheel and its transitive dependencies.

## Outstanding pre-publication checks

- Confirm the exact Noto font revision used for asset generation in release
  metadata when reproducibility across systems matters.
- Audit any non-emoji art or custom icon added in later releases.
- Verify relevant licenses for actual packaged Fedora dependencies using
  `rpm -q --qf '%{LICENSE}\n' <package>` or Fedora package metadata.
- Finish functional/public security and accessibility review separately;
  license compliance alone does not certify the app for public release.

This is a technical license audit, not legal advice.
