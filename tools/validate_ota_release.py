#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from mobile_protocol_validation.ota_release import (
    load_json_object,
    validate_all_action_pins,
    validate_candidate_run_metadata,
    validate_release_inputs,
    validate_release_workflow,
    write_validated_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    inputs = subparsers.add_parser("inputs")
    inputs.add_argument("--release-version", required=True)
    inputs.add_argument("--artifact-run-id", required=True)
    inputs.add_argument("--channel", required=True)
    inputs.add_argument("--github-output", type=Path, required=True)

    candidate = subparsers.add_parser("candidate")
    candidate.add_argument("--metadata", type=Path, required=True)
    candidate.add_argument("--artifact-run-id", required=True)
    candidate.add_argument("--repository", required=True)
    candidate.add_argument("--github-output", type=Path, required=True)

    scaffold = subparsers.add_parser("scaffold")
    scaffold.add_argument(
        "--workflow",
        type=Path,
        default=Path(".github/workflows/firmware-release.yml"),
    )
    scaffold.add_argument(
        "--workflow-directory",
        type=Path,
        default=Path(".github/workflows"),
    )

    args = parser.parse_args()
    if args.command == "inputs":
        validated = validate_release_inputs(
            args.release_version,
            args.artifact_run_id,
            args.channel,
        )
        write_validated_outputs(validated, args.github_output)
    elif args.command == "candidate":
        validated = validate_candidate_run_metadata(
            load_json_object(args.metadata),
            args.artifact_run_id,
            args.repository,
        )
        args.github_output.write_text(f"head_sha={validated.head_sha}\n")
    else:
        validate_release_workflow(args.workflow)
        validate_all_action_pins(args.workflow_directory)
        print("OTA release scaffold validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
