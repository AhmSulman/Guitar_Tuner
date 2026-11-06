#!/usr/bin/env bash
# Verify 16 KB page-size compliance of a built APK or AAB.
#
#   check-16kb.sh <file.apk|file.aab>
#
# Checks, and fails the step on any miss:
#   1. Every ELF shared object in the package -- lib/, base/lib/, AND the ones
#      inside any tar in assets/ (p4a ships the Python bundle, i.e. numpy's and
#      Kivy's extension modules, in assets/private.tar) -- has every PT_LOAD
#      segment aligned to >= 16384. Play only scans lib/, but on a 16 KB device
#      a 4 KB-aligned extension module fails to dlopen at runtime.
#   2. APK: `zipalign -c -P 16` (uncompressed .so entries 16 KB-aligned in the zip).
#      AAB: bundletool turns the bundle into the split APKs Play would serve,
#      and each of those gets the same zipalign check.
#
# Writes a per-.so table to $GITHUB_STEP_SUMMARY when running in Actions.
set -euo pipefail

PKG="${1:?usage: check-16kb.sh <file.apk|file.aab>}"
BUNDLETOOL_VERSION="1.18.1"
SDK="${ANDROID_SDK_ROOT:-$HOME/.buildozer/android/platform/android-sdk}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"

WORK="$(mktemp -d)"
# Tarred files can come out read-only; make them writable so cleanup can't fail the step.
trap 'chmod -R u+w "$WORK" 2>/dev/null; rm -rf "$WORK" 2>/dev/null || true' EXIT

is_elf() { [ "$(head -c4 "$1" | od -An -tx1 | tr -d ' \n')" = "7f454c46" ]; }

echo "== Checking $PKG"
unzip -q "$PKG" -d "$WORK/pkg"

# Unpack every archive that can hold native code. p4a ships the Python bundle
# (stdlib extension modules, numpy, Kivy) as lib/<arch>/libpybundle.so, which
# is a TAR despite the name, and the app itself as assets/private.tar.
tars_found=0
while IFS= read -r t; do
  case "$t" in *.so) ! is_elf "$t" || continue ;; esac
  tar -tf "$t" >/dev/null 2>&1 || continue
  tars_found=$((tars_found + 1))
  dest="$WORK/tar_$tars_found"
  mkdir -p "$dest"
  echo "   unpacking $(realpath --relative-to="$WORK/pkg" "$t")"
  tar -xf "$t" -C "$dest"
  # p4a writes directory entries with tarfile.TarInfo defaults (mode 0644, no x),
  # so nothing can be traversed. Fix level by level: each pass makes the next
  # depth of directories visible to find.
  for _ in $(seq 64); do
    [ -n "$(find "$dest" -type d ! -perm -u=rwx -print -quit 2>/dev/null)" ] || break
    find "$dest" -type d ! -perm -u=rwx -exec chmod u+rwx {} + 2>/dev/null || true
  done
  chmod -R u+r "$dest"
  echo "     $(find "$dest" -type f | wc -l) files, $(find "$dest" -type f -name '*.so*' | wc -l) .so"
done < <(find "$WORK/pkg" -type f \( -name '*.tar' -o -name '*.tar.gz' -o -name '*.tgz' -o -name '*.so' \))

{
  echo "### 16 KB check: \`$(basename "$PKG")\`"
  echo
  echo "| Result | p_align | .so |"
  echo "|---|---|---|"
} >> "$SUMMARY"

total=0; failed=0; pyext=0
while IFS= read -r so; do
  # ELF only; archives named .so were unpacked above.
  is_elf "$so" || continue
  total=$((total + 1))
  case "$so" in *cpython-*.so) pyext=$((pyext + 1)) ;; esac
  rel="${so#"$WORK"/}"
  aligns="$(readelf -lW "$so" | awk '$1=="LOAD"{print $NF}' | sort -u | tr '\n' ' ')"
  ok=1
  for a in $aligns; do
    [ $((a)) -ge 16384 ] || ok=0
  done
  if [ "$ok" -eq 1 ]; then
    printf 'PASS  %-24s %s\n' "$aligns" "$rel"
    echo "| ✅ PASS | \`$aligns\` | \`$rel\` |" >> "$SUMMARY"
  else
    failed=$((failed + 1))
    printf 'FAIL  %-24s %s\n' "$aligns" "$rel"
    echo "| ❌ FAIL | \`$aligns\` | \`$rel\` |" >> "$SUMMARY"
  fi
done < <(find "$WORK/pkg" $(compgen -G "$WORK/tar_*" || true) -type f -name '*.so*' | sort)

echo "== ELF alignment: $((total - failed)) / $total pass ($pyext Python extension modules, from $tars_found archive(s) + zip)"
echo >> "$SUMMARY"
echo "**ELF alignment: $((total - failed)) / $total pass** ($pyext Python extension modules)" >> "$SUMMARY"
[ "$total" -gt 0 ] || { echo "::error::No ELF .so found in $PKG"; exit 1; }
# Guard against silently checking only lib/ again: numpy/Kivy must have been seen.
[ "$pyext" -gt 0 ] || { echo "::error::No Python extension modules (*cpython-*.so) found -- the Python bundle was not inspected"; exit 1; }

# zipalign with -P needs build-tools 35+. Take the newest installed.
ZIPALIGN="$(ls "$SDK"/build-tools/*/zipalign 2>/dev/null | sort -V | tail -1 || true)"
[ -n "$ZIPALIGN" ] || { echo "::error::zipalign not found under $SDK/build-tools"; exit 1; }
echo "== Using $ZIPALIGN"

zip_failed=0
zipcheck() {
  if "$ZIPALIGN" -c -P 16 4 "$1" >/dev/null 2>&1; then
    echo "PASS  zipalign -c -P 16  $(basename "$1")"
    echo "- ✅ zipalign -P 16: \`$(basename "$1")\`" >> "$SUMMARY"
  else
    zip_failed=1
    echo "FAIL  zipalign -c -P 16  $(basename "$1")"
    "$ZIPALIGN" -c -v -P 16 4 "$1" | grep -v '(OK' | head -40 || true
    echo "- ❌ zipalign -P 16: \`$(basename "$1")\`" >> "$SUMMARY"
  fi
}

echo >> "$SUMMARY"
case "$PKG" in
  *.apk)
    zipcheck "$PKG"
    ;;
  *.aab)
    jar="$WORK/bundletool.jar"
    curl -fsSL -o "$jar" \
      "https://github.com/google/bundletool/releases/download/${BUNDLETOOL_VERSION}/bundletool-all-${BUNDLETOOL_VERSION}.jar"
    # Signs with ~/.android/debug.keystore if present -- irrelevant to alignment.
    java -jar "$jar" build-apks --bundle="$PKG" --output="$WORK/out.apks"
    unzip -q "$WORK/out.apks" -d "$WORK/apks"
    while IFS= read -r a; do zipcheck "$a"; done < <(find "$WORK/apks" -name '*.apk' | sort)
    ;;
  *) echo "::error::Unknown package type: $PKG"; exit 1 ;;
esac

# Permissions. The store listing and the Data safety form promise microphone
# only and NO network access, so INTERNET appearing here is a failure.
perm_failed=0
AAPT2="$(ls "$SDK"/build-tools/*/aapt2 2>/dev/null | sort -V | tail -1 || true)"
case "$PKG" in
  *.apk) perm_apk="$PKG" ;;
  *.aab) perm_apk="$(find "$WORK/apks" -name 'base-master*.apk' | head -1)" ;;
esac
if [ -n "$AAPT2" ] && [ -n "${perm_apk:-}" ]; then
  perms="$("$AAPT2" dump permissions "$perm_apk" | grep -oE "name='[^']+'" | sed "s/name='//; s/'//" | sort -u)"
  echo "== Manifest permissions:"; echo "$perms" | sed 's/^/   /'
  { echo; echo "**Manifest permissions:**"; echo "$perms" | sed 's/^/- `/; s/$/`/'; } >> "$SUMMARY"
  if echo "$perms" | grep -qx 'android.permission.INTERNET'; then
    echo "::error::INTERNET permission present -- the listing and Data safety form claim no network access"
    perm_failed=1
  fi
else
  echo "::warning::aapt2 not found -- manifest permissions not checked"
fi

if [ "$failed" -ne 0 ] || [ "$zip_failed" -ne 0 ] || [ "$perm_failed" -ne 0 ]; then
  echo "::error::Package check failed for $PKG ($failed .so misaligned, zipalign failed=$zip_failed, INTERNET present=$perm_failed)"
  exit 1
fi
echo "== 16 KB check passed for $PKG"
