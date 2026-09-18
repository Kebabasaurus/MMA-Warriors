"""Generate the proposed source-delivery manifest without staging any files."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "developer" / "delivery-manifest.json"
PYTHON_TREES = ("fight_moves", "fighter_portraits", "analysis", "tools")
PORTRAIT_FIXTURE_DIRS = (
    "top_51_100_current_2026_09_18",
    "top_101_200_current_2026_09_18",
    "top_201_300_current_2026_09_18",
    "top_301_400_current_2026_09_18",
)
ANALYSIS_DOCUMENTATION = (
    "README.md",
    "ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md",
)
ROOT_DELIVERY_NAMES = {
    ".gitattributes", ".gitignore", "LICENSE",
    "build-toolchain.json", "requirements-build.txt", "requirements.txt",
    "MMA Warriors.spec", "MMA Warriors Database Editor.spec",
}
EXCLUDED_PARTS = {
    ".git", ".venv", ".pytest_cache", "__pycache__", ".claude",
    ".codex-remote-attachments", ".agents", "build", "dist",
    "build_database_editor", "build_identity_editor", "build_identity_game",
    "output_database_editor", "output_identity_editor", "output_identity_game",
    "Saves", "Logs",
}
BINARY_SUFFIXES = {".png", ".ico", ".wav", ".gz", ".exe", ".zip"}


def canonical_content(path: Path) -> bytes:
    """Return checkout-independent bytes for the delivery identity."""
    content = path.read_bytes()
    if path.suffix.casefold() not in BINARY_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return content


def add_tree(files: set[Path], directory: Path, pattern: str = "*") -> None:
    if not directory.exists():
        return
    files.update(path for path in directory.rglob(pattern) if path.is_file())


def python_files() -> set[Path]:
    files = set(ROOT.glob("*.py"))
    for name in PYTHON_TREES:
        add_tree(files, ROOT / name, "*.py")
    return files


def referenced_analysis_json(sources: set[Path]) -> set[Path]:
    """Select named JSON fixtures, not the complete retained analysis history."""
    names = set()
    token = re.compile(r"[A-Za-z0-9_.-]+\.json")
    for path in sources:
        try:
            names.update(token.findall(path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    selected = set()
    analysis_root = ROOT / "analysis"
    forbidden = {"runtime", "runs", "ui_review_20260912"}
    for name in sorted(names):
        for path in analysis_root.rglob(name):
            if path.is_file() and not (set(path.relative_to(analysis_root).parts) & forbidden):
                selected.add(path)
    return selected


def collect_files() -> set[Path]:
    sources = python_files()
    files = set(sources)
    for path in ROOT.iterdir():
        if path.is_file() and (
            path.name in ROOT_DELIVERY_NAMES
            or path.suffix.casefold() in {".bat", ".md", ".txt"}
        ):
            files.add(path)
    add_tree(files, ROOT / "assets")
    add_tree(files, ROOT / "country_flags")
    default_universe = ROOT / "Databases" / "Default Universe.universe.json"
    if default_universe.is_file():
        files.add(default_universe)
    for path in (ROOT / "docs").glob("*.md"):
        files.add(path)
    add_tree(files, ROOT / "docs" / "developer", "*.md")
    add_tree(files, ROOT / "docs" / "developer", "*.json")
    files.discard(DEFAULT_MANIFEST)
    files.discard(ROOT / "active_universe.txt")
    # Documentation names historical evidence that is intentionally not a
    # delivery dependency. Only maintained executable/test source can select a
    # JSON fixture into the snapshot.
    files.update(referenced_analysis_json(sources))
    for relative in ANALYSIS_DOCUMENTATION:
        candidate = ROOT / "analysis" / relative
        if candidate.is_file():
            files.add(candidate)
    for directory in PORTRAIT_FIXTURE_DIRS:
        add_tree(files, ROOT / "analysis" / "portraits" / directory)
    return {
        path for path in files
        if path.is_file() and not (set(path.relative_to(ROOT).parts) & EXCLUDED_PARTS)
    }


def role_for(relative: Path) -> str:
    value = relative.as_posix()
    name = relative.name
    if value.startswith(("assets/", "country_flags/")):
        return "runtime_asset"
    if value == "Databases/Default Universe.universe.json":
        return "runtime_database"
    if value.startswith("analysis/portraits/"):
        return "test_fixture"
    if value.startswith("analysis/") and relative.suffix == ".json":
        return "test_fixture"
    if value.startswith("analysis/") and relative.suffix == ".py":
        return "test_support"
    if value.startswith("tools/"):
        return "developer_tool"
    if value.startswith("docs/") or relative.suffix == ".md":
        return "documentation"
    if name.endswith(("_test.py", "_regression_test.py")) or name in {
        "smoke_test.py", "stability_test.py", "database_editor_ui_audit.py",
    }:
        return "test"
    if relative.suffix == ".py":
        return "runtime_source"
    if relative.suffix in {".spec", ".bat"} or name.startswith("requirements") or name == "build-toolchain.json":
        return "build_configuration"
    return "project_configuration"


def build_manifest() -> dict:
    entries = []
    for path in sorted(collect_files(), key=lambda item: item.relative_to(ROOT).as_posix().casefold()):
        relative = path.relative_to(ROOT)
        content = canonical_content(path)
        entries.append({
            "path": relative.as_posix(),
            "role": role_for(relative),
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    aggregate = hashlib.sha256()
    for entry in entries:
        aggregate.update(f"{entry['path']}\0{entry['sha256']}\n".encode("utf-8"))
    return {
        "schema_version": 2,
        "content_normalization": "LF for text; raw bytes for binary assets",
        "generated_on": date.today().isoformat(),
        "purpose": "Proposed reviewable source delivery; no files are staged or released by this manifest.",
        "content_sha256": aggregate.hexdigest(),
        "file_count": len(entries),
        "files": entries,
        "exclusions": [
            {"pattern": "Saves/**", "reason": "User careers and recovery snapshots are private mutable runtime data."},
            {"pattern": "Logs/**", "reason": "Runtime logs may contain local paths and are not source dependencies."},
            {"pattern": "build*/**, dist/**, output*/**", "reason": "Generated packaging outputs are reproducible from source configuration."},
            {"pattern": "**/__pycache__/**, .pytest_cache/**, .venv/**", "reason": "Generated caches and local environments are not portable inputs."},
            {"pattern": ".git/**, .claude/**, .agents/**, .codex-remote-attachments/**", "reason": "VCS internals and local tool metadata are outside the product delivery."},
            {"pattern": "docs/archive/**", "reason": "Byte-preserved migration history is retained in the working repository but is not required to review or run current source."},
            {"pattern": "analysis/** except named source-bound fixtures", "reason": "Generated and historical analysis outputs are retained evidence, not blanket delivery inputs; only fixtures named by maintained source plus current portrait review fixtures are included."},
        ],
        "unresolved_ownership_decisions": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_manifest()
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"Wrote {payload['file_count']} files to {target}")
    print(f"Content SHA-256: {payload['content_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
