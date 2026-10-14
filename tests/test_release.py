"""Failure cases that matter when promoting a wheel between environments."""

import hashlib
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

spec = importlib.util.spec_from_file_location(
    "release", Path(__file__).parents[1] / "scripts/release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


@pytest.fixture
def artifact(tmp_path):
    wheel = tmp_path / "cicd_demo-0.1.0-py3-none-any.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr("cicd_demo-0.1.0.dist-info/METADATA", "Name: cicd-demo\nVersion: 0.1.0\n")
    manifest = {
        "schema_version": 1,
        "wheel": wheel.name,
        "version": "0.1.0",
        "commit": "test-commit",
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
    }
    (tmp_path / "release.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path, wheel, manifest


def test_release_preserves_identity(artifact):
    directory, wheel, manifest = artifact
    assert release.verify_release(directory) == (wheel, manifest)


def test_modified_wheel_is_rejected(artifact):
    directory, wheel, _ = artifact
    with wheel.open("ab") as output:
        output.write(b"modified after build")
    with pytest.raises(ValueError, match="checksum"):
        release.verify_release(directory)


def test_multiple_wheels_are_rejected(artifact):
    directory, _, _ = artifact
    (directory / "other.whl").write_bytes(b"wrong release")
    with pytest.raises(ValueError, match="exactly"):
        release.verify_release(directory)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("wheel", "../outside.whl", "filename"),
        ("wheel", "..\\outside.whl", "filename"),
        ("version", "0.2.0", "version"),
        ("schema_version", 2, "schema"),
    ],
)
def test_invalid_manifest_is_rejected(artifact, field, value, message):
    directory, _, manifest = artifact
    manifest[field] = value
    (directory / "release.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        release.verify_release(directory)


def test_deploy_refuses_to_overwrite_existing_environment(artifact):
    directory, _, _ = artifact
    target = directory / "existing"
    target.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        release.deploy_release(directory, target)
