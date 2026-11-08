"""Stage play-upload/ from the real sources, and validate it against Play's limits.

    python store/stage_play_upload.py               # stage + validate
    python store/stage_play_upload.py --aab X.aab   # also copy the bundle into build/

play-upload/ holds COPIES. Edit the sources, then re-run this script:

    listing/title.txt              <- buildozer.spec  `title`
    listing/short_description.txt  <- store/listing.md, first block under "Short description"
    listing/full_description.txt   <- store/listing.md, first block under "Full description"
    listing/release_notes.txt      <- store/release-notes.md, first block under "For the closed test"
    graphics/icon-512.png          <- icon.png
    graphics/feature-1024x500.png  <- store/feature-graphic.png
    graphics/phone/NN.png          <- store/screenshots/*.png, in order
    policy/privacy_policy.md       <- docs/privacy-policy.html, converted
    policy/privacy_policy_url.txt  <- the GitHub Pages URL

Stdlib only (Pillow is not installed on every machine this runs on).
Exits 1 if anything breaks a Play limit.
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "play-upload"
POLICY_URL = "https://ahmsulman.github.io/Guitar_Tuner/privacy-policy.html"

problems: list[str] = []
rows: list[tuple[str, str, str]] = []


def check(item: str, ok: bool, detail: str) -> None:
    rows.append(("OK " if ok else "BAD", item, detail))
    if not ok:
        problems.append(f"{item}: {detail}")


def first_block_after(md: str, heading: str) -> str:
    """Body of the first ``` fence that follows a heading containing `heading`."""
    at = md.find(heading)
    if at < 0:
        raise SystemExit(f"heading {heading!r} not found")
    m = re.search(r"```[^\n]*\n(.*?)\n```", md[at:], re.S)
    if not m:
        raise SystemExit(f"no code block after {heading!r}")
    return m.group(1).strip()


def unwrap(text: str) -> str:
    """Join hard-wrapped lines within each paragraph. Play shows every newline."""
    paras = re.split(r"\n\s*\n", text.strip())
    return "\n\n".join(" ".join(l.strip() for l in p.splitlines()) for p in paras)


def png_info(path: Path) -> tuple[int, int, bool]:
    data = path.read_bytes()[:26]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    w, h, _bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return w, h, color_type in (4, 6)  # 4 = grey+alpha, 6 = RGBA


def html_policy_to_md(src: str) -> str:
    body = re.search(r"<main>(.*)</main>", src, re.S).group(1)
    body = re.sub(r"<footer>(.*?)</footer>", r"\n---\n\n\1\n", body, flags=re.S)

    def table(m: re.Match) -> str:
        out = []
        for i, tr in enumerate(re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S)):
            cells = [c.strip() for c in re.findall(r"<t[hd]>(.*?)</t[hd]>", tr, re.S)]
            out.append("| " + " | ".join(cells) + " |")
            if i == 0:
                out.append("|" + "---|" * len(cells))
        return "\n" + "\n".join(out) + "\n"

    body = re.sub(r"<table>(.*?)</table>", table, body, flags=re.S)
    for tag, md in (("h1", "# "), ("h2", "## ")):
        body = re.sub(rf"<{tag}>(.*?)</{tag}>", lambda m, md=md: f"\n{md}{m.group(1)}\n", body)
    body = re.sub(r"<li>(.*?)</li>", r"- \1", body, flags=re.S)
    body = re.sub(r"</?(strong)>", "**", body)
    body = re.sub(r"</?(em)>", "*", body)
    body = re.sub(r"</?code>", "`", body)
    body = re.sub(r'<a href="([^"]+)">(.*?)</a>', r"[\2](\1)", body, flags=re.S)
    body = re.sub(r"</?(p|ul|div)[^>]*>", "\n", body)
    body = html.unescape(body)
    body = "\n".join(l.strip() for l in body.splitlines())
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aab", type=Path, help="signed .aab to copy into play-upload/build/")
    args = ap.parse_args()

    for sub in ("listing", "graphics/phone", "policy", "build"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    # ---- Text ---------------------------------------------------------------
    spec = (ROOT / "buildozer.spec").read_text(encoding="utf-8")
    title = re.search(r"^title\s*=\s*(.+)$", spec, re.M).group(1).strip()
    version = re.search(r"^version\s*=\s*(.+)$", spec, re.M).group(1).strip()
    listing = (ROOT / "store/listing.md").read_text(encoding="utf-8")
    notes_md = (ROOT / "store/release-notes.md").read_text(encoding="utf-8")

    texts = {
        "title.txt": (title, 30),
        "short_description.txt": (first_block_after(listing, "## Short description"), 80),
        "full_description.txt": (first_block_after(listing, "## Full description"), 4000),
    }
    notes = unwrap(first_block_after(notes_md, "## For the closed test"))
    for name, (text, limit) in texts.items():
        (OUT / "listing" / name).write_text(text + "\n", encoding="utf-8")
        check(f"listing/{name}", len(text) <= limit, f"{len(text)} / {limit} chars")
    # Play counts the notes text, not the language tags around it.
    (OUT / "listing/release_notes.txt").write_text(f"<en-US>\n{notes}\n</en-US>\n", encoding="utf-8")
    check("listing/release_notes.txt", len(notes) <= 500, f"{len(notes)} / 500 chars (en-US)")

    # ---- Graphics -------------------------------------------------------------
    icon = OUT / "graphics/icon-512.png"
    shutil.copyfile(ROOT / "icon.png", icon)
    w, h, _ = png_info(icon)
    size = icon.stat().st_size
    check("graphics/icon-512.png", (w, h) == (512, 512) and size <= 1_000_000,
          f"{w}x{h}, {size / 1e6:.2f} MB (32-bit PNG with alpha is allowed)")

    feat = OUT / "graphics/feature-1024x500.png"
    shutil.copyfile(ROOT / "store/feature-graphic.png", feat)
    w, h, alpha = png_info(feat)
    check("graphics/feature-1024x500.png", (w, h) == (1024, 500) and not alpha,
          f"{w}x{h}, {'HAS ALPHA' if alpha else 'no alpha'}")

    for old in (OUT / "graphics/phone").glob("*.png"):
        old.unlink()
    shots = sorted((ROOT / "store/screenshots").glob("*.png"))
    check("graphics/phone (count)", 2 <= len(shots) <= 8, f"{len(shots)} screenshots (2-8)")
    for i, src in enumerate(shots, 1):
        dst = OUT / f"graphics/phone/{i:02d}.png"
        shutil.copyfile(src, dst)
        w, h, alpha = png_info(dst)
        ratio = max(w, h) / min(w, h)
        # Play now requires exactly 16:9 or 9:16; the old "up to 2:1" rule is gone.
        ok = 320 <= min(w, h) and max(w, h) <= 3840 and min(w, h) * 16 == max(w, h) * 9 and not alpha \
            and dst.stat().st_size <= 8_000_000
        check(f"graphics/phone/{dst.name}", ok,
              f"{w}x{h} ({ratio:.2f}:1), {'HAS ALPHA' if alpha else 'no alpha'}  <- {src.name}")

    # ---- Policy ---------------------------------------------------------------
    policy_html = (ROOT / "docs/privacy-policy.html").read_text(encoding="utf-8")
    policy_md = html_policy_to_md(policy_html)
    (OUT / "policy/privacy_policy.md").write_text(policy_md, encoding="utf-8")
    (OUT / "policy/privacy_policy_url.txt").write_text(POLICY_URL + "\n", encoding="utf-8")
    check("policy/privacy_policy.md", "RECORD_AUDIO" in policy_md and "microphone" in policy_md.lower(),
          "mentions microphone + RECORD_AUDIO" if "RECORD_AUDIO" in policy_md else "NO MICROPHONE SECTION")

    # ---- Bundle ---------------------------------------------------------------
    if args.aab:
        if args.aab.suffix != ".aab":
            check("build/", False, f"{args.aab.name} is not an .aab")
        else:
            for old in (OUT / "build").glob("*.aab"):
                old.unlink()
            shutil.copyfile(args.aab, OUT / "build" / args.aab.name)
            check("build/", True, f"{args.aab.name} copied -- verify package, versionCode, signer next")
    else:
        have = list((OUT / "build").glob("*.aab"))
        check("build/", bool(have),
              have[0].name if have else
              f"EMPTY -- needs the signed v{version} AAB from the tag run (re-run with --aab)")

    width = max(len(r[1]) for r in rows)
    for status, item, detail in rows:
        print(f"{status}  {item:<{width}}  {detail}")
    print(f"\nversion in buildozer.spec: {version}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nAll staged items are within Play's limits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
