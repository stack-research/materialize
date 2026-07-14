"""materialize smoke — coldness by construction, fail-closed.

Proves the spine: a whitelist `read` set copies only the declared surface; the brief and
empty writable dirs are placed; the audit manifest is emitted; and a misconfigured manifest
that would leak the design thread / findings is REFUSED (tripwire) with the workspace
removed. Stdlib only.

Run: uv run --no-project python -m tests.test_materialize   (from the materialize dir)
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from materialize import materialize, resolve_source, verify_workspace  # noqa: E402


def _fake_repo() -> pathlib.Path:
    """A source repo with code (readable), a design thread + findings (must never leak),
    git history (must never copy), and a brief."""
    root = pathlib.Path(tempfile.mkdtemp()) / "sut"
    (root / "harness").mkdir(parents=True)
    (root / "harness" / "runner.py").write_text("def select_offers(): ...\n")
    (root / "harness" / "__pycache__").mkdir()
    (root / "harness" / "__pycache__" / "runner.pyc").write_text("bytecode")
    (root / "notes").mkdir()
    (root / "notes" / "SPEC.md").write_text("the spec (phase B only)\n")
    (root / "notes" / "M2_FINDINGS.md").write_text("THE ANSWER KEY — must never leak\n")
    (root / ".substrate" / "threads").mkdir(parents=True)
    (root / ".substrate" / "threads" / "t5.md").write_text("the design debate — must never leak\n")
    (root / ".git").mkdir()
    (root / ".git" / "COMMIT_EDITMSG").write_text("thread-5: spec v0.1\n")
    (root / "brief.md").write_text("rules of engagement\n")
    return root


def _manifest(root: pathlib.Path) -> dict:
    return {
        "name": "fake", "source_root": str(root), "brief": "brief.md",
        "phases": {
            "phase_a": {"description": "code only", "read": ["harness"], "writable": ["runs/out"]},
            "leaky": {"description": "fat-fingered", "read": ["."], "writable": []},
            "leaky_notes": {"description": "reads all of notes", "read": ["notes"], "writable": []},
        },
    }


def test_phase_a_copies_only_the_surface():
    root = _fake_repo()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    audit = materialize(_manifest(root), "phase_a", root, dest)

    assert (dest / "harness" / "runner.py").is_file()
    assert (dest / "REDTEAM_BRIEF.md").read_text() == "rules of engagement\n"
    assert (dest / "runs" / "out").is_dir()                  # empty writable dir placed
    # withheld material absent BY CONSTRUCTION
    assert not (dest / "notes").exists()
    assert not (dest / ".substrate").exists()
    assert not (dest / ".git").exists()
    assert not (dest / "harness" / "__pycache__").exists()   # caches pruned
    # audit record is the auditable "what could be read"
    assert audit["file_count"] == 1 and audit["files"][0]["path"] == "harness/runner.py"
    assert verify_workspace(dest, ["*FINDINGS*", ".substrate", ".git"]) == []
    print("ok  phase A: only the declared surface present; thread/findings/git absent; audit emitted")


def test_tripwire_refuses_a_leaky_manifest():
    root = _fake_repo()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    # read = ["."] would sweep in .substrate + findings + .git -> must abort + clean up
    try:
        materialize(_manifest(root), "leaky", root, dest)
        raise AssertionError("a read=['.'] manifest should have tripped the wire")
    except SystemExit as e:
        assert "TRIPWIRE" in str(e), e
    assert not dest.exists(), "workspace must be removed on a tripwire abort"
    print("ok  tripwire: read=['.'] (sweeps .substrate/findings) refused, workspace removed")


def test_tripwire_catches_findings_under_notes():
    root = _fake_repo()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    try:
        materialize(_manifest(root), "leaky_notes", root, dest)
        raise AssertionError("read=['notes'] sweeps M2_FINDINGS.md -> should trip")
    except SystemExit as e:
        assert "TRIPWIRE" in str(e) and "FINDINGS" in str(e).upper(), e
    assert not dest.exists()
    print("ok  tripwire: a findings file in the read set is caught (the answer-key backstop)")


def test_explicit_spec_read_is_allowed_phase_b():
    """A targeted read of one notes file (the spec) is allowed; the blanket findings/thread
    denylist does not over-block legitimate Phase-B reads."""
    root = _fake_repo()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    m = _manifest(root)
    m["phases"]["phase_b"] = {"description": "spec", "read": ["harness", "notes/SPEC.md"], "writable": []}
    materialize(m, "phase_b", root, dest)
    assert (dest / "notes" / "SPEC.md").is_file()
    assert not (dest / "notes" / "M2_FINDINGS.md").exists()  # the sibling findings did NOT come along
    print("ok  phase B: an explicit spec read lands; the sibling findings file stays out")


def test_missing_declared_brief_is_refused():
    """A manifest that declares a brief which does not exist is a misconfiguration —
    refuse and remove the workspace rather than seat an occupant with no rules."""
    root = _fake_repo()
    (root / "brief.md").unlink()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    try:
        materialize(_manifest(root), "phase_a", root, dest)
        raise AssertionError("a missing declared brief should abort")
    except SystemExit as e:
        assert "brief" in str(e), e
    assert not dest.exists(), "workspace must be removed when the declared brief is missing"
    print("ok  missing declared brief: refused, workspace removed")


def test_verify_flags_a_planted_forbidden_dir():
    """Defense in depth: verify_workspace reports a forbidden dir that appears in a
    workspace after materialization (e.g. a stray .git), not just forbidden files."""
    root = _fake_repo()
    dest = pathlib.Path(tempfile.mkdtemp()) / "ws"
    materialize(_manifest(root), "phase_a", root, dest)
    (dest / ".git").mkdir()
    assert ".git" in verify_workspace(dest, [".git"])
    print("ok  verify: a planted .git dir is flagged, not silently skipped")


def test_resolve_source_is_manifest_relative():
    """A relative source_root resolves against the manifest file, so committed
    manifests carry no machine-specific absolute paths; --source overrides."""
    base = pathlib.Path(tempfile.mkdtemp())
    mpath = base / "manifests" / "sut.toml"
    assert resolve_source({"source_root": "../../sut"}, mpath) == (base.parent / "sut").resolve()
    assert resolve_source({"source_root": "ignored"}, mpath, override=str(base)) == base.resolve()
    try:
        resolve_source({}, mpath)
        raise AssertionError("no source_root and no --source should abort")
    except SystemExit:
        pass
    print("ok  resolve_source: manifest-relative, --source override, fails without either")


if __name__ == "__main__":
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f))
    for _, fn in tests:
        fn()
    print(f"\nALL {len(tests)} MATERIALIZE TESTS PASS")
