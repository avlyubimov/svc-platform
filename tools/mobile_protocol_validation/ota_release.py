from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

CORE_VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
STABLE_VERSION_PATTERN = re.compile(rf"^{CORE_VERSION}$")
BETA_VERSION_PATTERN = re.compile(rf"^{CORE_VERSION}-beta\.(?:0|[1-9][0-9]*)$")
TEST_VERSION_PATTERN = re.compile(rf"^{CORE_VERSION}-test\.(?:0|[1-9][0-9]*)$")
RUN_ID_PATTERN = re.compile(r"^[0-9]+$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ACTION_REF_PATTERN = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
ALLOWED_CHANNELS = {"dev", "beta", "stable"}
ALLOWED_CANDIDATE_WORKFLOW = ".github/workflows/firmware-candidates.yml"
SIGNATURE_ALGORITHM = "rsa-pss-sha256"


class OTAReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class ReleaseInputs:
    release_version: str
    artifact_run_id: str
    channel: str
    release_tag: str


@dataclass(frozen=True)
class CandidateRun:
    run_id: int
    head_sha: str
    workflow_path: str


def validate_release_inputs(
    release_version: str,
    artifact_run_id: str,
    channel: str,
) -> ReleaseInputs:
    if channel not in ALLOWED_CHANNELS:
        raise OTAReleaseError("channel must be dev, beta, or stable")
    pattern = {
        "stable": STABLE_VERSION_PATTERN,
        "beta": BETA_VERSION_PATTERN,
        "dev": TEST_VERSION_PATTERN,
    }[channel]
    if not pattern.fullmatch(release_version):
        expected = {
            "stable": "MAJOR.MINOR.PATCH",
            "beta": "MAJOR.MINOR.PATCH-beta.N",
            "dev": "MAJOR.MINOR.PATCH-test.N",
        }[channel]
        raise OTAReleaseError(
            f"release_version does not match {channel} format {expected}"
        )
    if not RUN_ID_PATTERN.fullmatch(artifact_run_id):
        raise OTAReleaseError("artifact_run_id must contain digits only")
    return ReleaseInputs(
        release_version=release_version,
        artifact_run_id=artifact_run_id,
        channel=channel,
        release_tag=f"svc-v{release_version}",
    )


def validate_tag_version_channel(
    release_tag: str,
    release_version: str,
    channel: str,
) -> None:
    inputs = validate_release_inputs(release_version, "1", channel)
    if release_tag != inputs.release_tag:
        raise OTAReleaseError(
            f"release tag mismatch: expected {inputs.release_tag}, got {release_tag}"
        )


def validate_candidate_run_metadata(
    metadata: Mapping[str, object],
    expected_run_id: str,
    expected_repository: str,
    allowed_workflow: str = ALLOWED_CANDIDATE_WORKFLOW,
) -> CandidateRun:
    if not RUN_ID_PATTERN.fullmatch(expected_run_id):
        raise OTAReleaseError("artifact_run_id must contain digits only")
    if metadata.get("id") != int(expected_run_id):
        raise OTAReleaseError("artifact run id does not match API response")
    if metadata.get("status") != "completed" or metadata.get("conclusion") != "success":
        raise OTAReleaseError("artifact run must be completed successfully")
    if metadata.get("path") != allowed_workflow:
        raise OTAReleaseError("artifact run used a non-allowlisted workflow")

    repository = metadata.get("repository")
    head_repository = metadata.get("head_repository")
    if not isinstance(repository, Mapping) or not isinstance(head_repository, Mapping):
        raise OTAReleaseError("artifact run repository metadata is missing")
    if repository.get("full_name") != expected_repository:
        raise OTAReleaseError("artifact run belongs to another repository")
    if head_repository.get("full_name") != expected_repository:
        raise OTAReleaseError("artifact run was created from a fork")
    if head_repository.get("fork") is True:
        raise OTAReleaseError("artifact run was created from a fork")

    head_sha = metadata.get("head_sha")
    if not isinstance(head_sha, str) or not SHA_PATTERN.fullmatch(head_sha):
        raise OTAReleaseError("artifact run head SHA is invalid")
    return CandidateRun(
        run_id=int(expected_run_id),
        head_sha=head_sha,
        workflow_path=allowed_workflow,
    )


def load_private_key_from_environment(
    environment: Mapping[str, str] | None = None,
) -> rsa.RSAPrivateKey:
    values = os.environ if environment is None else environment
    encoded_key = values.get("OTA_PROD_SIGNING_KEY_B64", "")
    password = values.get("OTA_PROD_SIGNING_KEY_PASSWORD", "")
    if not encoded_key:
        raise OTAReleaseError("OTA_PROD_SIGNING_KEY_B64 is required")
    if not password:
        raise OTAReleaseError("OTA_PROD_SIGNING_KEY_PASSWORD is required")
    try:
        key_data = base64.b64decode(encoded_key, validate=True)
        private_key = serialization.load_pem_private_key(
            key_data,
            password=password.encode("utf-8"),
        )
    except (ValueError, TypeError) as error:
        raise OTAReleaseError("production signing key could not be loaded") from error
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise OTAReleaseError("production signing key must be RSA")
    if private_key.key_size < 3072:
        raise OTAReleaseError("production signing key must be at least 3072 bits")
    return private_key


def sign_detached(data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    return private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=hashes.SHA256.digest_size,
        ),
        hashes.SHA256(),
    )


def verify_detached(
    data: bytes,
    signature: bytes,
    public_key: rsa.RSAPublicKey,
) -> bool:
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=hashes.SHA256.digest_size,
            ),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def public_key_fingerprint(public_key: rsa.RSAPublicKey) -> str:
    public_der = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(public_der).hexdigest()


def require_expected_public_key_fingerprint(
    public_key: rsa.RSAPublicKey,
    expected_fingerprint: str,
) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_fingerprint):
        raise OTAReleaseError("OTA_PROD_PUBLIC_KEY_SHA256 must be 64 lowercase hex digits")
    actual = public_key_fingerprint(public_key)
    if actual != expected_fingerprint:
        raise OTAReleaseError(
            f"production public-key fingerprint mismatch: expected {expected_fingerprint}, got {actual}"
        )


def validate_release_workflow(path: Path) -> None:
    workflow_text = path.read_text()
    workflow = yaml.safe_load(workflow_text)
    if not isinstance(workflow, dict):
        raise OTAReleaseError("release workflow must be a mapping")
    permissions = workflow.get("permissions")
    expected_permissions = {
        "contents": "write",
        "actions": "read",
        "id-token": "write",
        "attestations": "write",
    }
    if permissions != expected_permissions:
        raise OTAReleaseError("release workflow permissions are incomplete")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        raise OTAReleaseError("release workflow jobs are missing")
    signing_job = jobs.get("sign-review")
    if not isinstance(signing_job, dict):
        raise OTAReleaseError("sign-review job is missing")
    if signing_job.get("environment") != "firmware-production":
        raise OTAReleaseError("sign-review job requires firmware-production environment")
    if "env" in signing_job:
        raise OTAReleaseError("sign-review job must not expose secrets through job env")

    secret_names = {
        "OTA_PROD_SIGNING_KEY_B64",
        "OTA_PROD_SIGNING_KEY_PASSWORD",
    }
    secret_steps = []
    for step in signing_job.get("steps", []):
        if not isinstance(step, dict):
            continue
        env = step.get("env", {})
        if isinstance(env, dict) and secret_names.intersection(env):
            secret_steps.append(step)
    if len(secret_steps) != 1:
        raise OTAReleaseError("production secrets must be scoped to one signing step")
    secret_env = secret_steps[0].get("env")
    if not isinstance(secret_env, dict) or not secret_names.issubset(secret_env):
        raise OTAReleaseError("both production signing secrets are required")

    if "gh release" in workflow_text or "publish_draft" in workflow_text:
        raise OTAReleaseError("review workflow must never create a GitHub Release")
    if "gh attestation verify" not in workflow_text:
        raise OTAReleaseError("candidate artifact attestations are not verified")
    if "merge-base --is-ancestor" not in workflow_text:
        raise OTAReleaseError("candidate commit ancestry is not verified")


def validate_all_action_pins(workflow_directory: Path) -> None:
    for workflow_path in sorted(workflow_directory.glob("*.yml")):
        workflow = yaml.safe_load(workflow_path.read_text())
        jobs = workflow.get("jobs", {}) if isinstance(workflow, dict) else {}
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps", []):
                if not isinstance(step, dict) or "uses" not in step:
                    continue
                action = step["uses"]
                if not isinstance(action, str) or not ACTION_REF_PATTERN.fullmatch(
                    action
                ):
                    raise OTAReleaseError(
                        f"{workflow_path}: action is not pinned to a full SHA: {action}"
                    )


def write_validated_outputs(
    inputs: ReleaseInputs,
    output_path: Path,
) -> None:
    output_path.write_text(
        "\n".join(
            (
                f"release_version={inputs.release_version}",
                f"artifact_run_id={inputs.artifact_run_id}",
                f"channel={inputs.channel}",
                f"release_tag={inputs.release_tag}",
            )
        )
        + "\n"
    )


def load_json_object(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise OTAReleaseError(f"{path} must contain a JSON object")
    return value
