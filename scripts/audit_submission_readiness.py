#!/usr/bin/env python3
"""Fail-closed audit for the anonymous TRUSTMORE paper submission artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAGE_LIMITS = {"full": (8, 9), "short": (4, 6), "demo": (4, 6)}
FORBIDDEN_IDENTITY_FRAGMENTS = (
    "1unarz",
    "lunarzdev",
    "/home/lunarz",
    "crane_explanation_fidelity.git",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def parse_pdfinfo(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values


def unembedded_fonts(text: str) -> tuple[int, list[str]]:
    lines = text.splitlines()
    divider = next((index for index, line in enumerate(lines) if line.startswith("---")), None)
    if divider is None:
        raise ValueError("pdffonts output has no table divider")
    fonts: list[str] = []
    missing: list[str] = []
    for line in lines[divider + 1 :]:
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) < 6:
            raise ValueError(f"cannot parse pdffonts row: {line}")
        fonts.append(fields[0])
        # The final five fields are emb, sub, uni, object number, generation number.
        if fields[-5].lower() != "yes":
            missing.append(fields[0])
    return len(fonts), missing


def pending_markers(source: str) -> int:
    return len(re.findall(r"\\pending\s*\{", source))


def audit(
    *, source: Path, bibliography: Path, pdf: Path, category: str
) -> dict[str, Any]:
    if category not in PAGE_LIMITS:
        raise ValueError(f"unsupported category: {category}")
    for path in (source, bibliography, pdf):
        if not path.is_file():
            raise ValueError(f"missing submission input: {path}")

    source_text = source.read_text(encoding="utf-8")
    bibliography_text = bibliography.read_text(encoding="utf-8")
    combined_source = source_text + "\n" + bibliography_text
    problems: list[str] = []
    checks: dict[str, Any] = {}

    pending = pending_markers(source_text)
    checks["unresolved_pending_markers"] = pending
    if pending:
        problems.append(f"manuscript contains {pending} unresolved \\pending markers")

    anonymous_author = bool(
        re.search(r"\\author\s*\{\s*Anonymous submission\s*\}", source_text)
    )
    checks["anonymous_author_line"] = anonymous_author
    if not anonymous_author:
        problems.append("manuscript author line is not exactly Anonymous submission")
    if re.search(r"\\thanks\s*\{", source_text):
        problems.append("manuscript contains an author footnote/thanks block")
    leaked_fragments = [
        fragment for fragment in FORBIDDEN_IDENTITY_FRAGMENTS if fragment.lower() in combined_source.lower()
    ]
    checks["forbidden_identity_fragments"] = leaked_fragments
    if leaked_fragments:
        problems.append(f"source contains identifying repository/path fragments: {leaked_fragments}")

    info_result = run_command(["pdfinfo", str(pdf)])
    if info_result.returncode:
        raise ValueError(f"pdfinfo failed: {info_result.stderr.strip()}")
    info = parse_pdfinfo(info_result.stdout)
    try:
        pages = int(info["Pages"])
    except (KeyError, ValueError) as error:
        raise ValueError("pdfinfo did not provide an integer page count") from error
    minimum, maximum = PAGE_LIMITS[category]
    checks["category"] = category
    checks["accepted_page_range"] = [minimum, maximum]
    checks["pages"] = pages
    if not minimum <= pages <= maximum:
        problems.append(
            f"{category} paper has {pages} pages; accepted range is {minimum}-{maximum} including references"
        )
    page_size = info.get("Page size", "")
    checks["page_size"] = page_size
    if "612 x 792 pts" not in page_size or "letter" not in page_size.lower():
        problems.append(f"PDF is not letter size: {page_size!r}")
    metadata_author = info.get("Author", "").strip()
    checks["pdf_metadata_author"] = metadata_author or None
    if metadata_author and metadata_author.lower() not in {"anonymous", "anonymous submission"}:
        problems.append("PDF metadata contains a non-anonymous author")

    fonts_result = run_command(["pdffonts", str(pdf)])
    if fonts_result.returncode:
        raise ValueError(f"pdffonts failed: {fonts_result.stderr.strip()}")
    font_count, missing_fonts = unembedded_fonts(fonts_result.stdout)
    checks["font_count"] = font_count
    checks["unembedded_fonts"] = missing_fonts
    if not font_count:
        problems.append("PDF contains no detected fonts")
    if missing_fonts:
        problems.append(f"PDF contains unembedded fonts: {missing_fonts}")

    newest_source = max(source.stat().st_mtime_ns, bibliography.stat().st_mtime_ns)
    checks["pdf_not_older_than_sources"] = pdf.stat().st_mtime_ns >= newest_source
    if not checks["pdf_not_older_than_sources"]:
        problems.append("PDF is older than main.tex or references.bib; rebuild before audit")

    traceability = run_command(
        ["python", str(ROOT / "scripts/audit_paper_numeric_traceability.py")]
    )
    checks["numeric_traceability_passed"] = traceability.returncode == 0
    if traceability.returncode:
        detail = traceability.stderr.strip() or traceability.stdout.strip()
        problems.append(f"numeric traceability audit failed: {detail}")

    return {
        "schema": "crane-trustmore-submission-readiness/v1",
        "status": "PASS" if not problems else "FAIL",
        "source": str(source),
        "source_sha256": digest(source),
        "bibliography": str(bibliography),
        "bibliography_sha256": digest(bibliography),
        "pdf": str(pdf),
        "pdf_sha256": digest(pdf),
        "checks": checks,
        "problems": problems,
        "submission_or_publication_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, choices=sorted(PAGE_LIMITS))
    parser.add_argument("--source", type=Path, default=ROOT / "paper/main.tex")
    parser.add_argument("--bibliography", type=Path, default=ROOT / "paper/references.bib")
    parser.add_argument("--pdf", type=Path, default=ROOT / "output/pdf/main.pdf")
    args = parser.parse_args()
    try:
        report = audit(
            source=args.source.resolve(strict=True),
            bibliography=args.bibliography.resolve(strict=True),
            pdf=args.pdf.resolve(strict=True),
            category=args.category,
        )
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
