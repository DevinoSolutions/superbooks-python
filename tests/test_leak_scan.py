"""The leak scanner must catch real matches, not merely pass.

A gate that has only ever gone green is untested. Coverage is derived from
`leak_scan.PATTERNS` itself rather than a parallel list, so every pattern must
prove it matches its own sample and rejects its known false positives. A
parallel list drifts out of step and leaves patterns silently unexercised.

Every string here is invented for the test. Nothing is copied from generated
documentation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import leak_scan  # noqa: E402


def scan(text: str) -> list[str]:
    """Findings rendered as `[pattern] 'matched'`, for readable assertions."""
    return [
        f"[{f.pattern}] {f.matched!r}" for f in leak_scan._scan_text("test-input", text)
    ]


# --- Every pattern must prove it detects something ----------------------------

ALL_PATTERNS = [(p.name, p) for p in leak_scan.PATTERNS]


@pytest.mark.parametrize(("name", "pattern"), ALL_PATTERNS)
def test_every_pattern_matches_its_own_sample(
    name: str, pattern: leak_scan.Pattern
) -> None:
    assert pattern.regex.search(pattern.sample), (
        f"pattern {name!r} does not match its own sample {pattern.sample!r} — "
        "the pattern is broken, or the sample does not demonstrate it"
    )


@pytest.mark.parametrize(("name", "pattern"), ALL_PATTERNS)
def test_sample_is_detected_end_to_end(name: str, pattern: leak_scan.Pattern) -> None:
    """The sample must survive the real scan path, attributed to its class."""
    assert any(f"[{name}]" in f for f in scan(pattern.sample))


@pytest.mark.parametrize(("name", "pattern"), ALL_PATTERNS)
def test_pattern_rejects_its_not_samples(name: str, pattern: leak_scan.Pattern) -> None:
    for text in pattern.not_samples:
        assert not pattern.regex.search(text), (
            f"pattern {name!r} false-positives on {text!r} — tighten it"
        )


def test_every_pattern_declares_a_sample() -> None:
    # The dataclass makes `sample` required; this guards against a later
    # refactor giving it a default and reopening the untested-pattern hole.
    for pattern in leak_scan.PATTERNS:
        assert pattern.sample.strip(), f"{pattern.name} has an empty sample"


def test_pattern_names_are_unique() -> None:
    names = [p.name for p in leak_scan.PATTERNS]
    assert len(names) == len(set(names))


# --- Prose forms, not just canonical spellings --------------------------------
#
# A matcher keyed to a term of art misses the same idea written as prose. These
# are invented paraphrases of the kinds of phrasing a generated description
# could plausibly use.

PARAPHRASES = [
    ("sql-internals", "the link is cleared and SETS NULL on the parent column"),
    ("sql-internals", "joined with ILIKE against the supplied text"),
    ("fuzzy-internals", "rows above 0.5 similarity are returned"),
    ("fuzzy-internals", "uses pg_trgm for fuzzy comparison"),
    ("fts-internals", "tokens are looked up in the tsvector column"),
    ("query-syntax", "expands to alpha:* before the lookup"),
    ("storage-vendor", "uploaded to Backblaze and mirrored"),
    ("offset-cursor", "the cursor is a row offset, not a key"),
    ("roadmap-admission", "the sweep is not yet implemented"),
]


@pytest.mark.parametrize(("expected", "text"), PARAPHRASES)
def test_prose_paraphrases_are_detected(expected: str, text: str) -> None:
    findings = scan(text)
    assert findings, f"paraphrase went undetected: {text!r}"
    assert any(f"[{expected}]" in f for f in findings), (
        f"{text!r} matched, but not as {expected}: {findings}"
    )


def test_ordinary_prose_produces_nothing() -> None:
    for text in [
        "Case-insensitive substring match on the document name only.",
        "Pagination cursor from the previous page's `cursor`.",
        "Returns one page of results, newest first.",
        "Confirm with the user before calling this tool.",
    ]:
        assert scan(text) == [], f"ordinary prose false-positives: {text!r}"


# --- Reporting: every distinct match, duplicates collapsed --------------------


def test_all_distinct_matches_in_one_string_are_found() -> None:
    findings = leak_scan._scan_text("f", "uses pg_trgm and a 40%-similarity pass")
    matched = {f.matched for f in findings if f.pattern == "fuzzy-internals"}
    assert len(matched) == 2


def test_report_collapses_repeats_of_the_same_literal() -> None:
    findings = [
        leak_scan.Finding("fuzzy-internals", "pg_trgm", where, "ctx")
        for where in ("a.json", "b.py", "c.py")
    ]
    report = "\n".join(leak_scan.format_findings(findings))
    assert "1 distinct match(es)" in report
    assert "3 occurrence(s)" in report


def test_report_counts_distinct_literals_not_occurrences() -> None:
    findings = [
        leak_scan.Finding("fuzzy-internals", "pg_trgm", "a.py", "ctx"),
        leak_scan.Finding("fuzzy-internals", "pg_trgm", "b.py", "ctx"),
        leak_scan.Finding("fuzzy-internals", "trigram", "a.py", "ctx"),
    ]
    report = "\n".join(leak_scan.format_findings(findings))
    assert "2 distinct match(es)" in report
    assert "'pg_trgm'" in report
    assert "'trigram'" in report


def test_report_is_empty_for_no_findings() -> None:
    assert leak_scan.format_findings([]) == []


# --- Self-exclusion is anchored, not suffix-matched ---------------------------
#
# This file and the scanner quote every pattern verbatim, so both are skipped.
# The exclusion is anchored to exact repo-relative paths, optionally behind a
# distribution directory as they appear inside an sdist.

EXCLUDED_PATHS = [
    "scripts/leak_scan.py",
    "tests/test_leak_scan.py",
    "superbooks-0.1.0/scripts/leak_scan.py",
    "superbooks-0.1.0/tests/test_leak_scan.py",
    r"superbooks-0.1.0\scripts\leak_scan.py",
    "./scripts/leak_scan.py",
]


@pytest.mark.parametrize("path", EXCLUDED_PATHS)
def test_self_exclusion_matches_anchored_paths(path: str) -> None:
    assert leak_scan._is_self(path), f"{path} should be self-excluded"


# A suffix match would wrongly skip all of these.
NOT_EXCLUDED_PATHS = [
    "src/superbooks/_generated/_sync.py",
    "superbooks-0.1.0/src/superbooks/_generated/_sync.py",
    "README.md",
    "tests/test_protocol.py",
    "vendor/other/scripts/leak_scan.py",
    "docs/tests/test_leak_scan.py",
    "my_leak_scan.py",
]


@pytest.mark.parametrize("path", NOT_EXCLUDED_PATHS)
def test_self_exclusion_does_not_swallow_other_files(path: str) -> None:
    assert not leak_scan._is_self(path), f"{path} must still be scanned"


# --- Source scope is the whole repository -------------------------------------


def test_source_scope_covers_published_files_outside_the_package() -> None:
    scanned = set(leak_scan.source_files())
    for path in [
        "pyproject.toml",
        "scripts/codegen.py",
        "tests/conftest.py",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        "README.md",
        "RELEASING.md",
        "sdk-manifest.json",
        "src/superbooks/_generated/_sync.py",
    ]:
        assert path in scanned, f"{path} is published but not scanned"


def test_source_scope_matches_tracked_files_minus_self() -> None:
    tracked = set(leak_scan._tracked_files())
    if not tracked:
        pytest.skip("git not available")
    unscanned = tracked - set(leak_scan.source_files())
    assert all(leak_scan._is_self(p) for p in unscanned), (
        f"tracked but unscanned for no stated reason: {sorted(unscanned)}"
    )


def test_compiled_bytecode_is_not_skipped() -> None:
    # Docstrings are compiled into .pyc, so the scanner must read it.
    assert not any(s == ".pyc" for s in leak_scan.SKIP_SUFFIXES)


# --- Stale-dist warning -------------------------------------------------------


def _fake_repo(tmp_path: Path, dist_older: bool) -> Path:
    (tmp_path / "dist").mkdir()
    (tmp_path / "src").mkdir()
    manifest = tmp_path / "sdk-manifest.json"
    wheel = tmp_path / "dist" / "pkg-0.1.0-py3-none-any.whl"

    if dist_older:
        wheel.write_bytes(b"x")
        os.utime(wheel, (1_000, 1_000))
        manifest.write_text("{}")
        os.utime(manifest, (2_000, 2_000))
    else:
        manifest.write_text("{}")
        os.utime(manifest, (1_000, 1_000))
        wheel.write_bytes(b"x")
        os.utime(wheel, (2_000, 2_000))
    return tmp_path


def test_stale_dist_warning_fires_when_dist_predates_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(leak_scan, "REPO_ROOT", _fake_repo(tmp_path, dist_older=True))
    warning = leak_scan.stale_dist_warning()
    assert warning is not None
    assert "sdk-manifest.json" in warning


def test_stale_dist_warning_silent_when_dist_is_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(leak_scan, "REPO_ROOT", _fake_repo(tmp_path, dist_older=False))
    assert leak_scan.stale_dist_warning() is None


def test_stale_dist_warning_silent_without_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(leak_scan, "REPO_ROOT", tmp_path)
    assert leak_scan.stale_dist_warning() is None


# --- The repository itself must be clean --------------------------------------


def test_repository_source_is_clean() -> None:
    findings = leak_scan.scan_source()
    rendered = "\n".join(leak_scan.format_findings(findings))
    assert findings == [], f"leak-scan found matches in committed source:\n{rendered}"
