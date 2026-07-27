#!/usr/bin/env python3
"""Version bookkeeping for a release.

The version lives in exactly two files — `pyproject.toml` and
`src/igntui/__init__.py` — and everything else reads `__version__` at runtime.
They drift silently: nothing at build time compares them, so a mismatch first
shows up as a release on PyPI labelled with the wrong number.

    release_version.py current             what this checkout says
    release_version.py assert-consistent   both files agree (CI runs this)
    release_version.py status              local vs what is actually on PyPI
    release_version.py check 0.2.0         would this be a legal next version?
    release_version.py apply 0.2.0         write it to both files + changelog
    release_version.py notes 0.2.0         changelog section, for a release body
    release_version.py verify 0.2.0        wait until PyPI really serves it

`check` is separate from `apply` so a bad version is rejected before anything
has been written.
"""

import argparse
import datetime
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
INIT_PY = ROOT / "src" / "igntui" / "__init__.py"
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
REPO = "https://github.com/MKAbuMattar/igntui"
PYPI_JSON = "https://pypi.org/pypi/igntui/json"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
INIT_RE = re.compile(r'^(__version__ = ")([^"]+)(")$', re.MULTILINE)
# Anchored to the [project] table's own version, not any dependency pin.
PYPROJECT_RE = re.compile(r'^(version = ")([^"]+)(")$', re.MULTILINE)


def parse(version: str) -> tuple[int, int, int]:
    match = SEMVER.match(version)
    if not match:
        raise SystemExit(f"error: {version!r} is not MAJOR.MINOR.PATCH")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def _read(path: pathlib.Path, pattern: re.Pattern[str]) -> str:
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"error: no version line found in {path}")
    return match.group(2)


def current() -> str:
    return _read(INIT_PY, INIT_RE)


def assert_consistent() -> None:
    """Both files must carry the same version. This is the CI gate."""
    pkg = current()
    proj = _read(PYPROJECT, PYPROJECT_RE)
    if pkg != proj:
        raise SystemExit(
            f"error: {INIT_PY.relative_to(ROOT)} says {pkg!r} but "
            f"{PYPROJECT.name} says {proj!r}. Reconcile them before releasing."
        )
    print(f"both say {pkg}")


def check(version: str) -> None:
    """Is `version` a legal target? Idempotent: already-there is not an error."""
    new = parse(version)
    here = current()
    old = parse(here)

    if new < old:
        raise SystemExit(
            f"error: {version} is older than the current {here}.\n"
            f"       Pick a version above {here}."
        )

    assert_consistent()
    print(f"ready: already at {version}" if new == old else f"bump: {here} -> {version}")


def _sub(path: pathlib.Path, pattern: re.Pattern[str], version: str) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, count = pattern.subn(rf"\g<1>{version}\g<3>", text, count=1)
    if count != 1:
        raise SystemExit(f"error: expected exactly one version line in {path}")
    path.write_text(new_text, encoding="utf-8")


def apply(version: str) -> None:
    check(version)

    if current() == version:
        print(f"nothing to do, already at {version}")
        return

    _sub(INIT_PY, INIT_RE, version)
    _sub(PYPROJECT, PYPROJECT_RE, version)

    text = CHANGELOG.read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()

    # Leave an empty Unreleased behind so the next change has somewhere to go.
    if "## [Unreleased]" not in text:
        raise SystemExit("error: CHANGELOG.md has no '## [Unreleased]' heading")
    text = text.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{version}] — {today}",
        1,
    )
    text = text.rstrip("\n") + f"\n[{version}]: {REPO}/releases/tag/v{version}\n"
    CHANGELOG.write_text(text, encoding="utf-8")

    print(f"bumped to {version} in {INIT_PY.name}, {PYPROJECT.name}, {CHANGELOG.name}")


def notes(version: str) -> None:
    """Print this version's changelog section, for a GitHub Release body."""
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    body = (match.group(1).strip() if match else "").strip()
    print(body or f"Release {version}.")


def published() -> str | None:
    """What PyPI is serving right now, or None if it cannot be reached."""
    try:
        with urllib.request.urlopen(PYPI_JSON, timeout=5) as response:
            return str(json.loads(response.read().decode())["info"]["version"])
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        return None


def status() -> None:
    local = current()
    live = published()

    print(f"  this checkout : {local}")
    print(f"  on PyPI       : {live or 'unreachable'}")

    if live is None:
        print("\n  Could not reach PyPI — offline, or the request timed out.")
    elif live == local:
        print(f"\n  In step. v{local} is the published release.")
    elif parse(local) > parse(live):
        print(f"\n  Unreleased: v{local} is staged here, PyPI still serves v{live}.")
    else:
        print(f"\n  Behind. PyPI has v{live}; this checkout is v{local}.")


def assert_at(version: str) -> None:
    """Hard gate before publishing: the tree must already be at `version`."""
    here = current()
    if here != version:
        raise SystemExit(
            f"error: refusing to publish. The branch asks for {version} but this tree is at {here}."
        )
    assert_consistent()


def verify(version: str, attempts: int = 10, delay: float = 6.0) -> None:
    """Block until PyPI serves `version`, so a no-op upload cannot pass.

    An upload succeeds well before the CDN catches up, so a single immediate
    check reports the old version and looks like a failed release.
    """
    for attempt in range(1, attempts + 1):
        live = published()
        if live == version:
            print(f"PyPI is serving {version}")
            return
        print(f"  attempt {attempt}/{attempts}: PyPI has {live or 'no answer'}", flush=True)
        if attempt < attempts:
            time.sleep(delay)

    raise SystemExit(
        f"error: PyPI never served {version} after {attempts} attempts.\n"
        f"       The upload may have failed silently — check the publish step."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("current")
    sub.add_parser("status")
    sub.add_parser("assert-consistent")
    for name in ("check", "apply", "notes", "verify", "assert"):
        sub.add_parser(name).add_argument("version")

    args = parser.parse_args()
    if args.command == "current":
        print(current())
    elif args.command == "status":
        status()
    elif args.command == "assert-consistent":
        assert_consistent()
    else:
        {
            "check": check,
            "apply": apply,
            "notes": notes,
            "verify": verify,
            "assert": assert_at,
        }[args.command](args.version)


if __name__ == "__main__":
    sys.exit(main())
