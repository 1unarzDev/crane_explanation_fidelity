import importlib.util
from pathlib import Path
import subprocess


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_submission_readiness.py"
SPEC = importlib.util.spec_from_file_location("audit_submission_readiness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def inputs(tmp_path: Path, source_text: str):
    source = tmp_path / "main.tex"
    bibliography = tmp_path / "references.bib"
    pdf = tmp_path / "main.pdf"
    source.write_text(source_text)
    bibliography.write_text("@article{safe, title={Safe}}")
    pdf.write_bytes(b"synthetic pdf placeholder")
    return source, bibliography, pdf


def command_runner(*, pages=8, embedded=True, traceability=True, author=""):
    def run(command):
        if command[0] == "pdfinfo":
            author_line = f"Author: {author}\n" if author else ""
            return completed(
                f"{author_line}Pages: {pages}\nPage size: 612 x 792 pts (letter)\n"
            )
        if command[0] == "pdffonts":
            value = "yes" if embedded else "no"
            return completed(
                "name type encoding emb sub uni object ID\n"
                "-----------------------------------------\n"
                f"ABC+Font Type1 Builtin {value} yes yes 4 0\n"
            )
        if command[0] == "python":
            return completed(returncode=0 if traceability else 1, stderr="trace failure")
        raise AssertionError(command)
    return run


def test_passes_anonymous_full_paper_with_embedded_fonts(tmp_path, monkeypatch):
    source, bibliography, pdf = inputs(
        tmp_path, "\\documentclass{IEEEtran}\n\\author{Anonymous submission}\n"
    )
    monkeypatch.setattr(MODULE, "run_command", command_runner())
    result = MODULE.audit(
        source=source, bibliography=bibliography, pdf=pdf, category="full"
    )
    assert result["status"] == "PASS"
    assert result["checks"]["pages"] == 8
    assert result["submission_or_publication_performed"] is False


def test_reports_page_pending_identity_font_metadata_and_traceability_failures(
    tmp_path, monkeypatch
):
    source, bibliography, pdf = inputs(
        tmp_path,
        "\\author{Named Person}\n\\thanks{University}\n"
        "\\pending{results}\n/home/lunarz/crane_explanation_fidelity.git\n",
    )
    monkeypatch.setattr(
        MODULE,
        "run_command",
        command_runner(pages=7, embedded=False, traceability=False, author="Named Person"),
    )
    result = MODULE.audit(
        source=source, bibliography=bibliography, pdf=pdf, category="full"
    )
    assert result["status"] == "FAIL"
    assert result["checks"]["unresolved_pending_markers"] == 1
    assert result["checks"]["unembedded_fonts"] == ["ABC+Font"]
    assert len(result["problems"]) >= 7


def test_short_and_demo_categories_accept_only_four_to_six_pages(tmp_path, monkeypatch):
    source, bibliography, pdf = inputs(tmp_path, "\\author{Anonymous submission}\n")
    monkeypatch.setattr(MODULE, "run_command", command_runner(pages=6))
    assert MODULE.audit(source=source, bibliography=bibliography, pdf=pdf, category="short")["status"] == "PASS"
    assert MODULE.audit(source=source, bibliography=bibliography, pdf=pdf, category="demo")["status"] == "PASS"

    monkeypatch.setattr(MODULE, "run_command", command_runner(pages=7))
    assert MODULE.audit(source=source, bibliography=bibliography, pdf=pdf, category="short")["status"] == "FAIL"
