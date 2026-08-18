"""Verify the recorded offline packaging toolchain without changing the environment."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from importlib import metadata
from pathlib import Path


def _version(value: object) -> str:
    return str(value).strip()


def verify_toolchain(root: Path) -> list[str]:
    metadata_path = root / "build-toolchain.json"
    requirements_path = root / "requirements-build.txt"
    errors: list[str] = []

    try:
        recorded = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"Missing recorded toolchain metadata: {metadata_path}"]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Could not read recorded toolchain metadata {metadata_path}: {exc}"]
    if not isinstance(recorded, dict):
        return [f"Recorded toolchain metadata must be a JSON object: {metadata_path}"]

    python_record = recorded.get("python", {})
    if not isinstance(python_record, dict):
        errors.append("Recorded toolchain metadata has an invalid python section")
        python_record = {}
    expected_implementation = _version(python_record.get("implementation", ""))
    actual_implementation = _version(sys.implementation.name)
    if actual_implementation != expected_implementation:
        errors.append(
            f"Python implementation mismatch: expected {expected_implementation}, "
            f"found {actual_implementation}"
        )

    actual_python = ".".join(str(part) for part in sys.version_info[:3])
    expected_python = _version(python_record.get("version", ""))
    if actual_python != expected_python:
        errors.append(f"Python version mismatch: expected {expected_python}, found {actual_python}")

    expected_architecture = _version(python_record.get("architecture", ""))
    actual_architecture = platform.architecture()[0]
    if actual_architecture != expected_architecture:
        errors.append(
            f"Python architecture mismatch: expected {expected_architecture}, "
            f"found {actual_architecture}"
        )

    packages = recorded.get("packages", {})
    if not isinstance(packages, dict):
        errors.append("Recorded toolchain metadata has an invalid packages section")
        packages = {}
    for package_name, expected_version_value in packages.items():
        expected_version = _version(expected_version_value)
        try:
            actual_version = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            errors.append(f"Missing required build package: {package_name}=={expected_version}")
            continue
        if actual_version != expected_version:
            errors.append(
                f"Build package mismatch: expected {package_name}=={expected_version}, "
                f"found {package_name}=={actual_version}"
            )

    try:
        requirement_lines = requirements_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"Missing build requirements lock file: {requirements_path}")
    except OSError as exc:
        errors.append(f"Could not read build requirements lock file {requirements_path}: {exc}")
    else:
        locked_requirements = {
            line.split("==", 1)[0].strip().lower(): line.split("==", 1)[1].strip()
            for line in requirement_lines
            if line.strip() and not line.lstrip().startswith("#") and "==" in line
        }
        for package_name, expected_version_value in packages.items():
            expected_version = _version(expected_version_value)
            locked_version = locked_requirements.get(package_name.lower())
            if locked_version != expected_version:
                errors.append(
                    f"Build lock mismatch: requirements-build.txt must contain "
                    f"{package_name}=={expected_version}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = verify_toolchain(root)
    if errors:
        print("Build toolchain verification failed:")
        for error in errors:
            print(f"  - {error}")
        print("No packages were installed. Re-run with the recorded environment after resolving the mismatch.")
        return 1

    print(
        "Build toolchain verified: "
        f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}, "
        f"PyInstaller {metadata.version('PyInstaller')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
