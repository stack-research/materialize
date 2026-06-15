"""materialize — build a cold, isolated, audited workspace from a phased read-manifest.

A red-team's coldness must hold by CONSTRUCTION, not by instruction. An attacker told
"please don't read the design thread" is the same weakness a lab refuses everywhere else:
a control enforced by request, not structure. The fix is absence, not permission — the
attacker cannot read `.substrate/threads/` because the thread is not in its filesystem.

This tool takes a phased read-manifest + a source repo and produces a curated, **non-git**
sandbox workspace containing EXACTLY the declared-readable surface — nothing else. Two
disciplines, both load-bearing:

  * Whitelist by intent — only `read` paths are copied (absence by construction).
  * Fail-closed tripwire — a denylist (.git, the design thread, findings) is scanned for
    AFTER the copy; any hit aborts and removes the workspace. A fat-fingered `read = ["."]`
    cannot silently leak the answer key. (The M-1 lesson: enforce coldness in code.)

The workspace's `MATERIALIZE_AUDIT.json` is the committed, auditable record of exactly what
the attacker could read in this phase — "declare your reads" made physical.

  uv run --no-project python materialize.py --manifest manifests/construct-m3.toml \
      --phase phase_a --dest /tmp/materialize-cm3-a
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import time
import tomllib
from pathlib import Path

# Never present in a cold workspace, whatever the manifest says. Component matches
# (".git", ".substrate") and filename globs ("*FINDINGS*"). Extended per-manifest.
DEFAULT_FORBIDDEN = [".git", ".substrate", "*FINDINGS*", "*_FINDINGS.md"]
SKIP_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache"}
AUDIT_NAME = "MATERIALIZE_AUDIT.json"
BRIEF_NAME = "REDTEAM_BRIEF.md"
_PLACED = {AUDIT_NAME, BRIEF_NAME}


def load_manifest(path: str | Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _is_forbidden(rel: Path, forbidden: list[str]) -> bool:
    parts = set(rel.parts)
    for pat in forbidden:
        if pat in parts:
            return True
        if fnmatch.fnmatch(rel.name, pat) or fnmatch.fnmatch(str(rel), pat):
            return True
    return False


def _iter_files(src_root: Path, entry: str):
    """Yield (abs_path, rel_to_src_root) for the regular files under `entry` (a file or a
    dir). Symlinks are NEVER followed (escape risk); caches/pyc are skipped."""
    base = src_root / entry
    if base.is_symlink():
        return
    if base.is_file():
        yield base, Path(entry)
        return
    if not base.is_dir():
        raise SystemExit(f"read entry not found: {entry}")
    for root, dirs, files in os.walk(base, followlinks=False):
        rootp = Path(root)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (rootp / d).is_symlink()]
        for fn in files:
            p = rootp / fn
            if p.is_symlink() or fn.endswith(".pyc") or fn == ".DS_Store":
                continue
            yield p, p.relative_to(src_root)


def verify_workspace(dest: Path, forbidden: list[str]) -> list[str]:
    """Re-scan a materialized workspace; return any forbidden paths present (should be [])."""
    leaked = []
    for root, dirs, files in os.walk(dest):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fn in files:
            rel = (Path(root) / fn).relative_to(dest)
            if rel.name in _PLACED:
                continue
            if _is_forbidden(rel, forbidden):
                leaked.append(str(rel))
    return leaked


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(manifest: dict, phase: str, source_root: str | Path,
                dest: str | Path, *, force: bool = False) -> dict:
    src = Path(source_root).resolve()
    if phase not in manifest.get("phases", {}):
        raise SystemExit(f"no such phase {phase!r}; have {sorted(manifest.get('phases', {}))}")
    ph = manifest["phases"][phase]
    forbidden = DEFAULT_FORBIDDEN + list(manifest.get("forbidden", []))
    dest = Path(dest).resolve()
    if dest.exists():
        if not force:
            raise SystemExit(f"dest exists: {dest} (use --force to overwrite)")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    def _abort(msg: str):
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit(f"TRIPWIRE — {msg} — workspace removed (coldness leak refused)")

    copied: list[Path] = []
    for entry in ph.get("read", []):
        abs_entry = (src / entry).resolve()
        if abs_entry != src and src not in abs_entry.parents:
            _abort(f"read entry escapes source_root: {entry}")
        for abspath, rel in _iter_files(src, entry):
            if _is_forbidden(rel, forbidden):
                _abort(f"forbidden path in read set: {rel}")
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(abspath, out)
            copied.append(rel)

    # The ROE brief, placed as the attacker's standing instruction.
    brief_rel = manifest.get("brief")
    brief_placed = False
    if brief_rel:
        bsrc = src / brief_rel
        if bsrc.is_file():
            shutil.copy2(bsrc, dest / BRIEF_NAME)
            brief_placed = True

    # Empty writable dirs for the attacker's fixtures + ledgers.
    for w in ph.get("writable", []):
        (dest / w).mkdir(parents=True, exist_ok=True)

    # Defense in depth: re-scan the materialized tree.
    leaked = verify_workspace(dest, forbidden)
    if leaked:
        _abort(f"post-copy scan found forbidden paths: {leaked}")

    audit = {
        "tool": "materialize", "schema": "v0",
        "manifest": manifest.get("name", "?"), "phase": phase,
        "phase_description": ph.get("description", ""),
        "source_root": str(src),
        "materialized_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "read": ph.get("read", []), "writable": ph.get("writable", []),
        "brief": BRIEF_NAME if brief_placed else None,
        "forbidden_checked": forbidden,
        "file_count": len(copied),
        "files": [{"path": str(r), "sha256": _sha(dest / r)} for r in sorted(copied)],
    }
    (dest / AUDIT_NAME).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return audit


def main() -> int:
    p = argparse.ArgumentParser(description="Materialize a cold attacker workspace.")
    p.add_argument("--manifest", required=True, help="phase manifest (TOML)")
    p.add_argument("--phase", required=True, help="phase name (e.g. phase_a)")
    p.add_argument("--source", default=None, help="source repo root (overrides manifest.source_root)")
    p.add_argument("--dest", required=True, help="workspace dir to create")
    p.add_argument("--force", action="store_true", help="overwrite an existing dest")
    args = p.parse_args()

    manifest = load_manifest(args.manifest)
    source = args.source or manifest.get("source_root")
    if not source:
        print("no source_root (pass --source or set it in the manifest)", file=sys.stderr)
        return 1
    audit = materialize(manifest, args.phase, source, args.dest, force=args.force)
    print(f"materialized {audit['manifest']}/{audit['phase']} -> {args.dest}")
    print(f"  {audit['file_count']} files readable; brief={audit['brief']}; "
          f"writable={audit['writable']}")
    print(f"  audit: {Path(args.dest) / AUDIT_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
