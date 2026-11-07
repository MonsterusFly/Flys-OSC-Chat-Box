#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
command -v rpmbuild >/dev/null || { echo 'Install rpm-build (Fedora: sudo dnf install rpm-build)' >&2; exit 1; }
mkdir -p "$ROOT/dist" "$ROOT/.rpmbuild/BUILD" "$ROOT/.rpmbuild/BUILDROOT" "$ROOT/.rpmbuild/RPMS" "$ROOT/.rpmbuild/SOURCES" "$ROOT/.rpmbuild/SPECS" "$ROOT/.rpmbuild/SRPMS"
rpmbuild -bb "$ROOT/packaging/fedora/flys-osc-chat-box.spec" \
  --define "_sourcedir $ROOT" \
  --define "_rpmdir $ROOT/dist" \
  --define "_topdir $ROOT/.rpmbuild"
find "$ROOT/dist" -type f -name '*.rpm' -print
