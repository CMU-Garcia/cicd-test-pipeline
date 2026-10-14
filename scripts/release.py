"""Shared release commands: both CI providers use exactly the same implementation."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def wheel_metadata(wheel: Path):
    with ZipFile(wheel) as archive:
        metadata_paths = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_paths) != 1:
            raise ValueError("wheel must contain exactly one package metadata file")
        metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
    if metadata["Name"] != "cicd-demo":
        raise ValueError("expected a cicd-demo wheel")
    return metadata


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify_release(artifact_dir: Path):
    manifest = json.loads((artifact_dir / "release.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported release manifest schema")
    filename = manifest["wheel"]
    if not isinstance(filename, str) or "/" in filename or "\\" in filename:
        raise ValueError("wheel must be a filename inside the artifact directory")
    wheels = list(artifact_dir.glob("*.whl"))
    if len(wheels) != 1 or wheels[0].name != filename:
        raise ValueError("artifact must contain exactly the wheel named in release.json")
    wheel = wheels[0]
    if sha256(wheel) != manifest["sha256"]:
        raise ValueError("wheel checksum does not match release.json")
    if wheel_metadata(wheel)["Version"] != manifest["version"]:
        raise ValueError("wheel version does not match release.json")
    return wheel, manifest


def build_release(output_dir: Path) -> None:
    # Build via a temporary sdist: its clean extraction cannot reuse stale build/lib files.
    with tempfile.TemporaryDirectory(prefix="cicd-build-") as temporary:
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", temporary, str(ROOT)],
            check=True,
        )
        wheels = list(Path(temporary).glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError("build must produce exactly one wheel")
        wheel = wheels[0]
        metadata = wheel_metadata(wheel)
        commit = os.environ.get("RELEASE_COMMIT")
        if not commit:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
            )
            commit = result.stdout.strip() if result.returncode == 0 else "uncommitted"
        manifest = {
            "schema_version": 1,
            "wheel": wheel.name,
            "version": metadata["Version"],
            "commit": commit,
            "sha256": sha256(wheel),
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        # Replace generated wheels only; do not recursively delete a user-supplied directory.
        for previous in output_dir.glob("*.whl"):
            previous.unlink()
        shutil.copy2(wheel, output_dir / wheel.name)
        (output_dir / "release.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(manifest, indent=2))


def deploy_release(artifact_dir: Path, target: Path) -> None:
    wheel, manifest = verify_release(artifact_dir)
    if target.exists():
        raise ValueError(f"target already exists: {target}; choose a new release directory")
    venv.EnvBuilder(with_pip=True).create(target)
    python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    # No editable install, no source checkout, no dependency downloads in deployment.
    subprocess.run(
        [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/smoke_test.py"),
            "--python",
            str(python),
            "--expected-version",
            manifest["version"],
        ],
        check=True,
    )
    (target / "installed-release.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Installed and smoke-tested {wheel.name} in {target}")
    print(f'Run: "{python}" -I -m cicd_demo --port 8000')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build a wheel and its release manifest")
    build.add_argument("--output-dir", type=Path, default=Path("dist"))
    verify = commands.add_parser("verify", help="check wheel identity, version and checksum")
    verify.add_argument("--artifact-dir", type=Path, default=Path("dist"))
    deploy = commands.add_parser("deploy", help="install and smoke-test a wheel in a fresh venv")
    deploy.add_argument("--artifact-dir", type=Path, default=Path("dist"))
    deploy.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build_release(args.output_dir.resolve())
        elif args.command == "verify":
            _, manifest = verify_release(args.artifact_dir.resolve())
            print(json.dumps(manifest, indent=2))
        else:
            deploy_release(args.artifact_dir.resolve(), args.target.resolve())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release failed: {error}\n")


if __name__ == "__main__":
    main()
