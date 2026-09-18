"""Validate and optionally copy the hashed MMA Warriors source delivery."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import py_compile
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "developer" / "delivery-manifest.json"
BINARY_SUFFIXES = {".png", ".ico", ".wav", ".gz", ".exe", ".zip"}


def canonical_content(path: Path) -> bytes:
    """Match the manifest's checkout-independent content identity."""
    content = path.read_bytes()
    if path.suffix.casefold() not in BINARY_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return content


def load_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2 or not isinstance(payload.get("files"), list):
        raise ValueError("Unsupported or malformed delivery manifest.")
    return payload


def validate_hashes(base: Path, payload: dict) -> None:
    seen = set()
    aggregate = hashlib.sha256()
    for entry in payload["files"]:
        relative = str(entry.get("path", ""))
        candidate = (base / relative).resolve()
        if not relative or relative in seen or base.resolve() not in candidate.parents:
            raise ValueError(f"Unsafe or duplicate manifest path: {relative!r}")
        seen.add(relative)
        if not candidate.is_file():
            raise FileNotFoundError(f"Missing delivery file: {relative}")
        content = canonical_content(candidate)
        actual = hashlib.sha256(content).hexdigest()
        if actual != entry.get("sha256"):
            raise ValueError(f"Hash mismatch: {relative}")
        if len(content) != entry.get("bytes"):
            raise ValueError(f"Size mismatch: {relative}")
        aggregate.update(f"{relative}\0{actual}\n".encode("utf-8"))
    if aggregate.hexdigest() != payload.get("content_sha256"):
        raise ValueError("Aggregate delivery hash mismatch.")
    if len(seen) != payload.get("file_count"):
        raise ValueError("Manifest file count does not match its entries.")


def local_modules(base: Path, paths: set[str]) -> set[str]:
    modules = set()
    for value in paths:
        path = Path(value)
        if path.suffix != ".py":
            continue
        parts = list(path.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            modules.add(".".join(parts))
    return modules


def validate_import_graph(base: Path, payload: dict) -> None:
    paths = {entry["path"] for entry in payload["files"]}
    modules = local_modules(base, paths)
    top_levels = {module.split(".", 1)[0] for module in modules}
    missing = set()
    for value in sorted(paths):
        if not value.endswith(".py"):
            continue
        tree = ast.parse((base / value).read_text(encoding="utf-8"), filename=value)
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                if name.split(".", 1)[0] not in top_levels:
                    continue
                if not any(name == module or name.startswith(module + ".") or module.startswith(name + ".") for module in modules):
                    missing.add((value, name))
    if missing:
        details = ", ".join(f"{source} -> {module}" for source, module in sorted(missing))
        raise ValueError(f"Unresolved local imports: {details}")


def registered_suites(base: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    runner = base / "run_regression_suite.py"
    tree = ast.parse(runner.read_text(encoding="utf-8"), filename=str(runner))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SUITES" for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Could not locate the static SUITES manifest.")


def validate_registered_inputs(base: Path, payload: dict) -> None:
    paths = {entry["path"] for entry in payload["files"]}
    for script, arguments in registered_suites(base):
        normalized = Path(script).as_posix()
        if normalized not in paths:
            raise ValueError(f"Registered suite script is absent: {normalized}")
        for argument in arguments:
            candidate = base / argument
            if candidate.is_file() and Path(argument).as_posix() not in paths:
                raise ValueError(f"Registered suite fixture is absent: {argument}")


def validate_runtime_assets(base: Path, payload: dict) -> None:
    paths = {entry["path"] for entry in payload["files"]}
    required = {
        "main.py", "MMA Warriors.spec", "MMA Warriors Database Editor.spec",
        "assets/app_icon.ico", "Databases/Default Universe.universe.json",
        "analysis/README.md",
        "analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md",
        "tools/update_delivery_manifest.py", "tools/validate_delivery_manifest.py",
    }
    missing = required - paths
    if missing:
        raise ValueError("Required delivery inputs absent: " + ", ".join(sorted(missing)))
    if not any(path.startswith("country_flags/") and path.endswith(".png") for path in paths):
        raise ValueError("No country flag assets are included.")
    spec = (base / "MMA Warriors.spec").read_text(encoding="utf-8")
    for fragment in ("PROJECT_ROOT / 'main.py'", "PROJECT_ROOT / 'assets'", "PROJECT_ROOT / 'country_flags'", "excludes=[]"):
        if fragment not in spec:
            raise ValueError(f"Authoritative game spec is missing {fragment!r}.")


def compile_python(base: Path, payload: dict) -> None:
    for entry in payload["files"]:
        if entry["path"].endswith(".py"):
            py_compile.compile(str(base / entry["path"]), doraise=True)


def copy_snapshot(source: Path, target: Path, manifest_path: Path, payload: dict) -> None:
    source = source.resolve()
    target = target.resolve()
    if target == source or source in target.parents or target in source.parents:
        raise ValueError("Snapshot destination must be outside the repository.")
    if target.exists():
        raise FileExistsError("Snapshot destination already exists; use a new unique directory.")
    target.mkdir(parents=True)
    for entry in payload["files"]:
        destination = target / entry["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / entry["path"], destination)
    control_copy = target / "docs" / "developer" / manifest_path.name
    control_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, control_copy)
    validate_hashes(target, payload)
    validate_import_graph(target, payload)
    validate_registered_inputs(target, payload)
    validate_runtime_assets(target, payload)
    compile_python(target, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    payload = load_manifest(manifest_path)
    validate_hashes(ROOT, payload)
    validate_import_graph(ROOT, payload)
    validate_registered_inputs(ROOT, payload)
    validate_runtime_assets(ROOT, payload)
    if args.copy_to:
        copy_snapshot(ROOT, args.copy_to, manifest_path, payload)
        print(f"Validated copied snapshot: {args.copy_to.resolve()}")
    else:
        compile_python(ROOT, payload)
        print("Validated manifest in the current working tree.")
    print(f"Files: {payload['file_count']} | Content SHA-256: {payload['content_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError, py_compile.PyCompileError) as exc:
        print(f"DELIVERY MANIFEST INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
