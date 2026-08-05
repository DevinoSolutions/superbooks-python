#!/usr/bin/env python3
"""Fail the build if implementation vocabulary reaches published output.

The tool documentation in this package is generated, and generated text can
carry database, storage, and infrastructure detail that belongs in an
implementation rather than in a published SDK. This checks for that vocabulary
in both the source tree and the built distributions.

Both are checked because they differ: Python compiles docstrings into bytecode
and the wheel copies source verbatim, so a clean source tree does not by itself
mean a clean artifact.

Patterns are generic classes — SQL and full-text-search vocabulary, storage
vendor names, license identifiers, local filesystem shapes, credential shapes.
Each carries an invented sample proving it detects something, so a pattern
cannot be added without demonstrating that it works.

Usage::

    python scripts/leak_scan.py                 # source; also dist/ if present
    python scripts/leak_scan.py --require-dist  # fail if dist/ is missing

Exit status is 1 on any finding, reported as distinct matches per class.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# This file and its test quote every pattern verbatim, so both are skipped.
#
# Anchored to exact repo-relative paths, optionally prefixed by a distribution
# directory (`<name>-<version>/...`) as they appear inside an sdist. A suffix
# match would also skip an unrelated file whose path merely ended the same way.
SELF_EXCLUDED = ("scripts/leak_scan.py", "tests/test_leak_scan.py")
_DIST_PREFIX = re.compile(r"^[A-Za-z0-9._-]+-\d[A-Za-z0-9._-]*/")


def _is_self(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    candidates = {normalized, _DIST_PREFIX.sub("", normalized, count=1)}
    return any(candidate in SELF_EXCLUDED for candidate in candidates)


# Fallback only, for when git is unavailable (e.g. an unpacked sdist).
# The real source pass walks git-tracked files — see `_tracked_files`.
FALLBACK_GLOBS = ("src/**/*.py", "scripts/*.py", "tests/*.py", "*.md", "*.toml")

# Binary formats with no readable prose. `.pyc` is deliberately NOT listed:
# docstrings are compiled into bytecode, so it is decoded and scanned too.
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2")


def _tracked_files() -> list[str]:
    """Every git-tracked file — the full set that publication exposes.

    Scoping to the package directory would leave tests, workflows, packaging
    metadata, and scripts unexamined, all of which are published too.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [path for path in result.stdout.split("\0") if path]


@dataclass(frozen=True)
class Pattern:
    """One leak class, with proof that it detects something.

    `sample` is required and is always an INVENTED string, never text copied
    from any real document. The test suite asserts every pattern matches its
    own sample and none of its `not_samples`, so a pattern cannot be added
    without demonstrating detection, and one that silently stops matching is
    caught rather than passing forever.

    Two lessons are encoded below. A matcher keyed to a term of art misses the
    same idea written as prose, so paraphrases are pinned alongside canonical
    spellings. And a matcher that flags legitimate public text gets deleted by
    the next maintainer, so known-good strings are pinned as `not_samples`
    rather than left to chance.
    """

    name: str
    regex: re.Pattern[str]
    sample: str
    not_samples: tuple[str, ...] = ()


PATTERNS: list[Pattern] = [
    Pattern(
        # Relational mechanics: referential actions, nullability side effects,
        # and case-insensitive matching operators.
        "sql-internals",
        re.compile(
            r"\bILIKE\b|\bCASCADE[- ]?DELETES?\b|\bON DELETE\b"
            r"|\bSETS? NULL\b|\bforeign key\b|\bFK\b",
            re.I,
        ),
        sample="child rows are removed ON DELETE CASCADE from the parent",
        not_samples=(
            "case-insensitive substring match on the name",
            "deleting a record also removes the things attached to it",
        ),
    ),
    Pattern(
        # Full-text-search engine internals.
        "fts-internals",
        re.compile(r"to_tsquery|tsquery|tsvector|ts_rank(_cd)?|\bfts_\w+", re.I),
        sample="results are ordered by ts_rank_cd over the tsvector",
    ),
    Pattern(
        # MUST stay word-bounded and case-sensitive. Unbounded and
        # case-insensitive, these three letters match ordinary words such as
        # "bridging", "engine", "imagine", "logging" and "plugin", one of which
        # appears in this package.
        "index-type",
        re.compile(r"\bGIN\b|\bGiST\b|\bB-?tree index\b"),
        sample="lookups are served by a GIN index on that column",
        not_samples=("bridging", "engine", "imagine", "logging", "plugin"),
    ),
    Pattern(
        # Fuzzy matching, in both the term-of-art form and the
        # tuning-constant form a paraphrase would use.
        "fuzzy-internals",
        re.compile(
            r"pg_trgm|trigram"
            r"|\d+(\.\d+)?\s*%?[\s-]*similarity"
            r"|similarity\s+(threshold|score)\s*(of\s*)?[\d.]+",
            re.I,
        ),
        sample="matched with a 40%-similarity trigram comparison",
        # A documented relevance score is public API, not implementation
        # detail; flagging it would get this pattern deleted.
        not_samples=(
            "Minimum relevance score (0-1) for a row to be returned.",
            "it handles typos and partial matches",
        ),
    ),
    Pattern(
        # Query-language prefix syntax. MUST keep the leading \w and the
        # trailing negative lookahead: a bare colon-asterisk also matches
        # markdown bold labels such as `**Note:**`.
        "query-syntax",
        re.compile(r"\w:\*(?!\*)"),
        sample="terms are combined as `alpha:* & beta:*` before ranking",
        not_samples=("**Note:** see below", "**Requires:** 3.10+", "**Docs:**"),
    ),
    Pattern(
        # Object-storage vendors. A watchlist of well-known vendor names
        # reveals nothing about which one is in use.
        "storage-vendor",
        re.compile(
            r"\bS3\b|\bGCS\b|Google Cloud Storage|Azure Blob"
            r"|\bB2\b|Backblaze|Cloudflare R2",
            re.I,
        ),
        sample="the object is removed from the S3 bucket as well",
    ),
    Pattern(
        # Copyleft license identifiers, as ordinary dependency hygiene for an
        # MIT-licensed package.
        "license-contamination",
        re.compile(r"\bAGPL\b|\bAffero\b|\bL?GPL(v[23])?\b"),
        sample="portions are distributed under the AGPL",
        not_samples=("MIT License", "licensed under MIT"),
    ),
    Pattern(
        # Local filesystem shapes: home directories, cloud-sync folders, and
        # absolute paths that would reveal a machine's layout.
        "local-path",
        re.compile(
            r"[A-Za-z]:[\\/]Users[\\/]|OneDrive|/home/[a-z][a-z0-9_-]*/"
            r"|[A-Za-z]:[\\/][A-Za-z0-9._-]+[\\/][A-Za-z0-9._-]+[\\/]",
            re.I,
        ),
        sample=r"saved to C:\Users\example\Documents\output",
        not_samples=("src/superbooks/_generated", "./dist/", "~/.config"),
    ),
    Pattern(
        # Credential shape: the API key format this SDK accepts. Documentation
        # placeholders are short and obviously fake; a full-length key is not.
        "credential-shape",
        re.compile(r"\bsb_[0-9a-f]{32,}\b", re.I),
        sample="sb_" + "0" * 64,
        not_samples=("sb_test_xxx", "sb_your_api_key_here", "Bearer sb_..."),
    ),
    Pattern(
        # Unshipped-work admissions.
        "roadmap-admission",
        re.compile(r"Phase \d+ (TODO|WIP)|\bnot yet implemented\b", re.I),
        sample="cleanup is deferred (Phase 4 TODO)",
    ),
    Pattern(
        # Pagination described in terms of its storage-layer implementation
        # rather than as an opaque token.
        "offset-cursor",
        re.compile(
            r"stringified (row )?offset|offset-based cursor"
            r"|cursor is (a|the) (row )?offset",
            re.I,
        ),
        sample="pass the cursor, which is a stringified row offset",
        not_samples=("Pagination cursor from the previous page's `cursor`.",),
    ),
]


@dataclass(frozen=True)
class Finding:
    pattern: str
    matched: str
    where: str
    context: str


def _scan_text(where: str, text: str) -> list[Finding]:
    """Every match, not just the first.

    Reporting one exemplar per class per file is correct as pass/fail and
    unhelpful to whoever has to fix it: a single field can carry two separate
    matches, and a first-match report means fixing one, re-running, and only
    then discovering the next.
    """
    out: list[Finding] = []
    for entry in PATTERNS:
        for match in entry.regex.finditer(text):
            start = max(0, match.start() - 60)
            context = text[start : match.end() + 60].replace("\n", " ")
            out.append(Finding(entry.name, match.group(), where, context))
    return out


def format_findings(findings: list[Finding]) -> list[str]:
    """Group by class, then collapse repeats of the same literal.

    One string can appear several times because a surface holds several copies
    of the same text. Reporting the raw occurrence count invites reading it as
    that many separate problems.
    """
    lines: list[str] = []
    by_pattern: dict[str, list[Finding]] = {}
    for finding in findings:
        by_pattern.setdefault(finding.pattern, []).append(finding)

    for pattern in sorted(by_pattern):
        by_literal: dict[str, list[Finding]] = {}
        for finding in by_pattern[pattern]:
            by_literal.setdefault(finding.matched, []).append(finding)

        lines.append(f"  [{pattern}] {len(by_literal)} distinct match(es)")
        for literal in sorted(by_literal):
            hits = by_literal[literal]
            places = sorted({hit.where for hit in hits})
            where = places[0]
            if places[1:]:
                where += f" (+{len(places) - 1} more file(s))"
            lines.append(f"    {literal!r} — {len(hits)} occurrence(s) in {where}")
            lines.append(f"        …{hits[0].context}…")
    return lines


def source_files() -> list[str]:
    """Repo-relative paths the source pass will scan."""
    tracked = _tracked_files()
    if not tracked:
        tracked = sorted(
            path.relative_to(REPO_ROOT).as_posix()
            for glob in FALLBACK_GLOBS
            for path in REPO_ROOT.glob(glob)
            if path.is_file()
        )
    return [
        rel
        for rel in tracked
        if not _is_self(rel) and not rel.lower().endswith(SKIP_SUFFIXES)
    ]


def scan_source() -> list[Finding]:
    findings: list[Finding] = []
    for rel in source_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        findings += _scan_text(rel, path.read_bytes().decode("utf-8", "ignore"))
    return findings


def scan_dist() -> tuple[list[Finding], int]:
    """Scan every member of the built wheel and sdist, not only .py files.

    Packaging metadata is generated from the README, so it is a real carrier;
    checking only source files would miss it. Compiled bytecode is decoded the
    same way, since docstrings survive into it.
    """
    findings: list[Finding] = []
    members = 0
    dist = REPO_ROOT / "dist"
    if not dist.is_dir():
        return findings, members

    for wheel in sorted(dist.glob("*.whl")):
        with zipfile.ZipFile(wheel) as zf:
            for name in zf.namelist():
                if _is_self(name):
                    continue
                members += 1
                text = zf.read(name).decode("utf-8", "ignore")
                findings += _scan_text(f"{wheel.name}::{name}", text)

    for sdist in sorted(dist.glob("*.tar.gz")):
        with tarfile.open(sdist) as tf:
            for member in tf.getmembers():
                if not member.isfile() or _is_self(member.name):
                    continue
                handle = tf.extractfile(member)
                if handle is None:
                    continue
                members += 1
                text = handle.read().decode("utf-8", "ignore")
                findings += _scan_text(f"{sdist.name}::{member.name}", text)

    return findings, members


def stale_dist_warning() -> str | None:
    """Warn when dist/ is older than the sources it was built from.

    A scan of stale artifacts reports on something other than the current tree,
    and a warning at the moment of the mistake is worth more than a note in a
    document nobody rereads.
    """
    dist = REPO_ROOT / "dist"
    artifacts = [*dist.glob("*.whl"), *dist.glob("*.tar.gz")] if dist.is_dir() else []
    if not artifacts:
        return None

    built = min(path.stat().st_mtime for path in artifacts)
    watched = [REPO_ROOT / "sdk-manifest.json", *(REPO_ROOT / "src").rglob("*.py")]
    newer = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in watched
        if path.is_file() and path.stat().st_mtime > built
    ]
    if not newer:
        return None
    listed = ", ".join(sorted(newer)[:3])
    more = f" (+{len(newer) - 3} more)" if len(newer) > 3 else ""
    return (
        f"dist/ is OLDER than {len(newer)} source file(s): {listed}{more}. "
        "The artifacts being scanned are not built from the current tree — "
        "rebuild before trusting this result."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-dist",
        action="store_true",
        help="fail if dist/ is absent (use in the release workflow)",
    )
    args = parser.parse_args()

    stale = stale_dist_warning()
    if stale:
        print(f"leak-scan: WARNING — {stale}", file=sys.stderr)

    findings = scan_source()
    dist_findings, dist_members = scan_dist()
    findings += dist_findings

    if args.require_dist and dist_members == 0:
        print(
            "leak-scan: --require-dist was given but dist/ holds no artifacts. "
            "Build before scanning, or the release would ship unscanned.",
            file=sys.stderr,
        )
        return 1

    if findings:
        distinct = len({(f.pattern, f.matched) for f in findings})
        print(
            f"leak-scan: {distinct} distinct match(es) across "
            f"{len(findings)} occurrence(s):\n",
            file=sys.stderr,
        )
        for line in format_findings(findings):
            print(line, file=sys.stderr)
        print(
            "\nIf a match is legitimate, tighten the pattern or reword the "
            "text — do not delete the pattern.",
            file=sys.stderr,
        )
        return 1

    scanned = "source" + (f" + {dist_members} artifact members" if dist_members else "")
    print(f"leak-scan: clean ({scanned}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
