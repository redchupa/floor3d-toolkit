"""Block accidental commits of personal data.

Run as ``python scripts/check_secrets.py``; exits non-zero when a forbidden
pattern is found in tracked source files. Excludes:

- this script itself (it has to define the patterns)
- CLAUDE.md (intentionally references forbidden patterns as policy text)
- the security section of README.md / docs / .gitignore (also policy text)

Patterns extend the list in PLAN.md §7.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tuples of (regex, label). Add patterns here, not inline elsewhere.
FORBIDDEN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"192\.168\.\d+\.\d+"), "private IPv4 192.168.x.x"),
    (re.compile(r"10\.0\.\d+\.\d+"), "private IPv4 10.0.x.x"),
    (re.compile(r"redchupa\.com"), "personal domain"),
    (re.compile(r"ha\.redchupa"), "personal HA URL"),
    (re.compile(r"\bjerry\b", re.IGNORECASE), "family name"),
    (re.compile(r"하린"), "family name"),
    (re.compile(r"예린"), "family name"),
    (re.compile(r"제리"), "family name"),
    (re.compile(r"WooRin"), "family name"),
    (re.compile(r"AIza[0-9A-Za-z_-]{20,}"), "Google API key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "OpenAI / Anthropic-style key"),
    (re.compile(r"C:\\\\Users\\\\redchupa"), "Windows user path"),
)

# Files whose entire job is documenting these patterns.
EXEMPT_FILES = {
    "scripts/check_secrets.py",
    "CLAUDE.md",
    "DEV_NOTES.md",
    "PLAN.md",
    ".gitignore",
}

# Directories never scanned.
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".venv",
    "venv",
    "node_modules",
    ".tox",
    "htmlcov",
}

# Extensions worth scanning. Binary 3D assets are blocked by .gitignore;
# this is a belt-and-braces text scan.
INCLUDED_EXTS = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".txt",
    ".json",
}


def iter_files() -> list[Path]:
    out: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in INCLUDED_EXTS:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXEMPT_FILES:
            continue
        out.append(path)
    return out


def main() -> int:
    failures: list[tuple[str, str, int, str]] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, label in FORBIDDEN:
                if pattern.search(line):
                    failures.append(
                        (
                            path.relative_to(ROOT).as_posix(),
                            label,
                            line_no,
                            line.strip()[:120],
                        )
                    )

    if failures:
        print("Forbidden patterns found:", file=sys.stderr)
        for rel, label, line_no, snippet in failures:
            print(f"  {rel}:{line_no}  [{label}]  {snippet}", file=sys.stderr)
        return 1
    print("OK - no forbidden patterns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
