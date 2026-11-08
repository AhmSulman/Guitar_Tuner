#!/usr/bin/env bash
# Pre-seed p4a's download cache with the source tarballs that p4a can only
# fetch from GitHub Releases, so a GitHub Releases outage can't break the build.
#
# On 2026-11-08 every github.com/<org>/<repo>/releases/download/... URL returned
# HTTP 504 for hours (githubstatus.com still said "operational"). openssl.org
# only 301-redirects to OpenSSL's GitHub release, so it failed too. p4a's other
# sources (CPython, libffi, kivy, pyjnius) are github.com/.../archive/ tarballs,
# served by a different service, and kept working.
#
# p4a skips a recipe's download when packages/<recipe>/<file> exists together
# with packages/<recipe>/.mark-<file> (see Recipe.download in pythonforandroid).
# For each file this script tries the upstream URL first, then official or
# distro mirrors, and accepts a download ONLY if its SHA-256 matches the pinned
# value. Each pin was confirmed against at least two independent sources:
#   openssl      OpenSSL's published .sha256, Alpine distfiles, MacPorts distfiles
#   sdl2*        libsdl.org, MacPorts distfiles (SDL2_image also the GitHub asset)
#
# If every URL for a file fails, it warns and leaves the file to p4a.
#
# BUMPING p4a? These versions must match the recipes in the pinned p4a tag
# (p4a.branch in buildozer.spec). A version mismatch is harmless: p4a ignores
# files it doesn't expect and downloads its own.
set -uo pipefail

PKG_DIR="${1:-.buildozer/android/platform/build-arm64-v8a/packages}"

# recipe | file | sha256 | urls (space-separated, tried in order)
SOURCES=(
  "openssl|openssl-3.3.1.tar.gz|777cd596284c883375a2a7a11bf5d2786fc5413255efab20c50d6ffe6d020b7e|https://github.com/openssl/openssl/releases/download/openssl-3.3.1/openssl-3.3.1.tar.gz https://distfiles.alpinelinux.org/distfiles/v3.20/openssl-3.3.1.tar.gz https://distfiles.macports.org/openssl3/openssl-3.3.1.tar.gz"
  "sdl2|SDL2-2.30.11.tar.gz|8b8d4aef2038533da814965220f88f77d60dfa0f32685f80ead65e501337da7f|https://github.com/libsdl-org/SDL/releases/download/release-2.30.11/SDL2-2.30.11.tar.gz https://www.libsdl.org/release/SDL2-2.30.11.tar.gz https://distfiles.macports.org/libsdl2/SDL2-2.30.11.tar.gz"
  "sdl2_image|SDL2_image-2.8.2.tar.gz|8f486bbfbcf8464dd58c9e5d93394ab0255ce68b51c5a966a918244820a76ddc|https://github.com/libsdl-org/SDL_image/releases/download/release-2.8.2/SDL2_image-2.8.2.tar.gz https://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.8.2.tar.gz https://distfiles.macports.org/libsdl2_image/SDL2_image-2.8.2.tar.gz"
  "sdl2_mixer|SDL2_mixer-2.6.3.tar.gz|7a6ba86a478648ce617e3a5e9277181bc67f7ce9876605eea6affd4a0d6eea8f|https://github.com/libsdl-org/SDL_mixer/releases/download/release-2.6.3/SDL2_mixer-2.6.3.tar.gz https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.6.3.tar.gz https://distfiles.macports.org/libsdl2_mixer/SDL2_mixer-2.6.3.tar.gz"
  "sdl2_ttf|SDL2_ttf-2.22.0.tar.gz|d48cbd1ce475b9e178206bf3b72d56b66d84d44f64ac05803328396234d67723|https://github.com/libsdl-org/SDL_ttf/releases/download/release-2.22.0/SDL2_ttf-2.22.0.tar.gz https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.22.0.tar.gz https://distfiles.macports.org/libsdl2_ttf/SDL2_ttf-2.22.0.tar.gz"
)

missing=0
for entry in "${SOURCES[@]}"; do
  IFS='|' read -r recipe file sha urls <<<"$entry"
  dir="$PKG_DIR/$recipe"
  dest="$dir/$file"
  mkdir -p "$dir"

  if [ -s "$dest" ] && [ -e "$dir/.mark-$file" ] \
     && [ "$(sha256sum "$dest" | cut -d' ' -f1)" = "$sha" ]; then
    echo "cached   $recipe  $file"
    continue
  fi

  ok=0
  for url in $urls; do
    tmp="$dest.part"
    if curl -fsSL --retry 2 --retry-delay 5 --connect-timeout 20 --max-time 300 -o "$tmp" "$url"; then
      got="$(sha256sum "$tmp" | cut -d' ' -f1)"
      if [ "$got" = "$sha" ]; then
        mv "$tmp" "$dest"
        : > "$dir/.mark-$file"
        echo "fetched  $recipe  $file  <- $url"
        ok=1
        break
      fi
      echo "::warning::$file from $url has sha256 $got, expected $sha. Rejected."
    else
      echo "         $recipe  $file  unavailable from $url"
    fi
    rm -f "$tmp"
  done

  if [ "$ok" -eq 0 ]; then
    echo "::warning::Could not pre-fetch $file from any source; p4a will try its own URL"
    missing=$((missing + 1))
  fi
done

echo "== pre-fetch done: $((${#SOURCES[@]} - missing)) / ${#SOURCES[@]} sources ready"
exit 0
