#!/usr/bin/env python3
"""Quality gate for the portfolio index.

This repository is an index, not code, so the gate checks the things
that actually go wrong in an index:

1. The required files and sections are present.
2. Every repository it links to is actually linked with a real URL, and
   every linked URL looks like one of the repositories in this account.
   An index that links to a repo that was renamed or made private is
   worse than no index.
3. No application-specific material. The index is public and is read
   by people evaluating the work, not by anyone assessing an
   application. Application drafts, essay text, and notes about a
   specific employer's hiring process do not belong here, and a
   reviewer who finds them learns something about the applicant's
   process that they were not meant to learn.
4. No employer-specific framing. The index has to work for any
   reader, so it cannot name a specific company as the audience.
5. No secrets, no personal identifiers, no absolute developer paths.
   The secret scan reads ``git ls-files``, so a reader's virtual
   environment is never mistaken for published content.
6. Every linked repository is described with all four beats: what was
   built, what was measured, what was found, what was not done. A
   description missing the "not done" beat is an inflated claim, and
   an inflated claim discounts the other three.

7. Control-coverage figures quoted from the CRM repository match the
   figure that repository derives from its own table.

The gate is standard-library only and exits 0 green, 1 red.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"

REQUIRED_FILES = ["README.md", "LICENSE", ".gitignore"]

REQUIRED_SECTIONS = [
    "## How to read these",
    "## 1.",
    "## 2.",
    "## 3.",
    "## 4.",
    "## The through-line",
    "## Background",
    "## Contact",
    "## License",
]

# The four beats every repository description must carry.
REQUIRED_BEATS = [
    "**What I built.**",
    "**What I measured.**",
    "**What I found.**",
    "**What I did not do.**",
]

# A linked repository must be one of these. A link to anything else is
# either a typo or a mistake.
EXPECTED_REPOS = {
    "civic-reach-case-study",
    "charlotte-311-call-line",
    "charlotte-municipal-crm",
    "sovereign-legal-ai",
}

# Employers and application surfaces that must not appear in a public
# portfolio index. The index is read by anyone; the application
# materials are not.
#
# These are matched case-insensitively. The list is deliberately
# generic rather than naming any particular employer: a gate that
# names one company in its source tells a reader that the index was
# built for that one company, which is exactly the thing the index is
# supposed to avoid.
FORBIDDEN_TERMS = [
    "research resident",
    "greenhouse",
    "job application",
    "cover letter",
    "why do you want to work",
    "recruiter",
    "fellows program",
    "candidate-ai guidance",
    "the residency",
]

# Secret and personal-data shapes.
SECRET_PATTERNS = [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"AIza[0-9A-Za-z_\-]{35}",
    r"xox[baprs]-[A-Za-z0-9\-]{10,}",
    r'"private_key"\s*:\s*"[^"]+"',
]

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b\d{3}\.\d{2}\.\d{4}\b",
    r"\(\d{3}\)\s?\d{3}-\d{4}",
    r"\b\d{3}-\d{3}-\d{4}\b",
]

EMAIL_PATTERN = r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "localhost")


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def gate_g1_required_files() -> tuple[bool, str]:
    """G1: required files present."""
    missing = [name for name in REQUIRED_FILES if not (REPO_ROOT / name).exists()]
    if missing:
        return False, f"missing files: {missing}"
    return True, f"{len(REQUIRED_FILES)} required files present"


def gate_g2_readme_sections() -> tuple[bool, str]:
    """G2: the required sections are present and ordered."""
    text = _readme_text()
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing:
        return False, f"missing sections: {missing[:4]}"
    positions = [text.index(s) for s in REQUIRED_SECTIONS]
    if positions != sorted(positions):
        return False, "sections are out of order"
    return True, f"{len(REQUIRED_SECTIONS)} sections present and ordered"


def gate_g3_links() -> tuple[bool, str]:
    """G3: every linked repo is expected, and every expected repo is linked."""
    text = _readme_text()
    linked = set(re.findall(r"github\.com/JacobKrez/([A-Za-z0-9._-]+)", text))
    linked.discard("JacobKrez")
    unexpected = linked - EXPECTED_REPOS
    if unexpected:
        return False, f"unexpected links: {sorted(unexpected)}"
    missing = EXPECTED_REPOS - linked
    if missing:
        return False, f"not linked: {sorted(missing)}"
    return True, f"{len(linked)} repositories linked, all expected"


def gate_g4_four_beats() -> tuple[bool, str]:
    """G4: every repository description carries all four beats."""
    text = _readme_text()
    for beat in REQUIRED_BEATS:
        count = text.count(beat)
        if count < len(EXPECTED_REPOS):
            return False, f"'{beat}' appears {count}x, expected >= {len(EXPECTED_REPOS)}"
    return True, f"all 4 beats present for {len(EXPECTED_REPOS)} repositories"


def gate_g5_no_application_material() -> tuple[bool, str]:
    """G5: no employer-specific or application-specific content."""
    text = _readme_text().lower()
    hits = [term for term in FORBIDDEN_TERMS if term in text]
    if hits:
        return False, f"application/employer-specific terms: {hits[:3]}"
    return True, "no application-specific framing"


def _repo_files() -> list[Path]:
    """Files that belong to the repository.

    ``git ls-files`` in a checkout, so a reader's virtual environment or
    scratch directory is never scanned, whatever it is named. In a source
    archive with no ``.git``, walk the tree and skip cache directories and
    any directory holding a ``pyvenv.cfg``.
    """
    if (REPO_ROOT / ".git").exists():
        try:
            listed = subprocess.run(
                ["git", "ls-files", "-z"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
            ).stdout.decode("utf-8")
            return [REPO_ROOT / name for name in listed.split("\0") if name]
        except (OSError, subprocess.CalledProcessError):
            pass
    venvs = [cfg.parent for cfg in REPO_ROOT.rglob("pyvenv.cfg")]
    return [
        path
        for path in REPO_ROOT.rglob("*")
        if not any(
            part in {".git", "__pycache__", ".pytest_cache"}
            for part in path.relative_to(REPO_ROOT).parts
        )
        and not any(venv in path.parents for venv in venvs)
    ]


def gate_g6_no_secrets() -> tuple[bool, str]:
    """G6: no secrets in any tracked file."""
    hits = []
    for path in _repo_files():
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pyc", ".png", ".jpg", ".wav", ".pdf", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text):
                hits.append(f"{path.relative_to(REPO_ROOT)}")
                break
    if hits:
        return False, f"secret-like content in: {hits[:3]}"
    return True, "no secret patterns"


def gate_g7_no_personal_data() -> tuple[bool, str]:
    """G7: no personal identifiers and no absolute developer paths."""
    text = _readme_text()
    for pattern in PII_PATTERNS:
        if re.search(pattern, text):
            return False, f"personal-data shape matched: {pattern}"
    for match in re.findall(EMAIL_PATTERN, text):
        if not any(domain in match for domain in ALLOWED_EMAIL_DOMAINS):
            return False, f"non-example email: {match}"
    if "/Users/" in text or "C:\\Users\\" in text:
        return False, "absolute developer path"
    return True, "no personal data, no absolute paths"


# The control-coverage figures the CRM repository derives from its NIST
# family table (its gate check G10): 171 of 214, 79.9 percent. The index
# cannot import that table, so the figures are pinned here; change both
# together. The retracted figures (174 of 232, about 75 percent, 58
# remaining) may appear only in a sentence that says they were claimed.
CRM_COVERAGE_NUMBERS = {"171", "214", "79.9", "80"}
CRM_RETRACTED_NUMBERS = {"174", "232", "75", "58"}


def gate_g8_published_figures() -> tuple[bool, str]:
    """G8: control-coverage figures in the index match the CRM table.

    In every sentence about controls or coverage, each number (other than
    the catalog name "800-53 Rev 5") must be a figure the CRM table
    produces, or a retracted figure reported as a past claim.
    """
    text = " ".join(_readme_text().split())
    bad = []
    for sentence in re.split(r"(?<=[.!?;])\s+", text):
        lower = sentence.lower()
        if "controls" not in lower and "coverage" not in lower:
            continue
        sentence = re.sub(r"800-53( Rev\.? ?5)?", " ", sentence)
        for number in re.findall(r"\b\d+(?:\.\d+)?\b", sentence):
            if number in CRM_COVERAGE_NUMBERS:
                continue
            if number in CRM_RETRACTED_NUMBERS and "claimed" in lower:
                continue
            bad.append(number)
    if bad:
        return False, f"coverage figures not from the CRM table: {bad[:4]}"
    return True, "control coverage matches the CRM table (171 of 214)"


GATES = [
    ("G1", "required files", gate_g1_required_files),
    ("G2", "readme sections", gate_g2_readme_sections),
    ("G3", "repository links", gate_g3_links),
    ("G4", "four beats per repo", gate_g4_four_beats),
    ("G5", "no application material", gate_g5_no_application_material),
    ("G6", "no secrets", gate_g6_no_secrets),
    ("G7", "no personal data", gate_g7_no_personal_data),
    ("G8", "published figures", gate_g8_published_figures),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 scripts/gate.py",
        description="Run the portfolio quality gate. Exit 0 green, 1 red.",
    )
    parser.add_argument("--quiet", action="store_true", help="One-line summary.")
    parser.add_argument("--only", help="Run a single gate by id, e.g. G3.")
    args = parser.parse_args(argv)

    selected = [g for g in GATES if not args.only or g[0] == args.only.upper()]
    if not selected:
        print(f"no such gate: {args.only}", file=sys.stderr)
        return 2

    results = []
    for gate_id, label, fn in selected:
        try:
            passed, detail = fn()
        except Exception as exc:  # pragma: no cover
            passed, detail = False, f"gate errored: {exc}"
        results.append((gate_id, label, passed, detail))

    failed = [r for r in results if not r[2]]

    if args.quiet:
        status = "PASS" if not failed else "FAIL"
        print(f"gate {status}: {len(results) - len(failed)}/{len(results)} gates passed")
        return 0 if not failed else 1

    print()
    print("=" * 72)
    print("Portfolio index -- quality gate")
    print("=" * 72)
    print()
    print(f"{'id':<5}{'gate':<32}{'status':<9}detail")
    print("-" * 72)
    for gate_id, label, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        print(f"{gate_id:<5}{label:<32}{status:<9}{detail}")
    print("-" * 72)
    print()
    if failed:
        print(f"RESULT: FAIL ({len(failed)} of {len(results)} gates failed)")
        return 1
    print("RESULT: PASS (all gates green)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
