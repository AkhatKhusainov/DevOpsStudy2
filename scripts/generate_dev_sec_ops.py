from __future__ import annotations

import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml


def run_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def collect_last_commits(limit: int) -> list[str]:
    output = run_command(["git", "rev-list", f"--max-count={limit}", "HEAD"])
    return output.splitlines() if output else []


def collect_image_signature(image_ref: str) -> dict[str, str]:
    digests_raw = run_command(
        ["docker", "image", "inspect", image_ref, "--format", "{{json .RepoDigests}}"]
    )
    image_id = run_command(["docker", "image", "inspect", image_ref, "--format", "{{.Id}}"])
    digests: list[str] = []

    if digests_raw:
        try:
            digests = json.loads(digests_raw)
        except json.JSONDecodeError:
            digests = []

    return {
        "ref": image_ref,
        "digest": digests[0] if digests else "unavailable",
        "image_id": image_id or "unavailable",
    }


def collect_coverage(coverage_xml: Path) -> str:
    if not coverage_xml.exists():
        return "n/a"

    root = ET.parse(coverage_xml).getroot()
    line_rate = float(root.attrib.get("line-rate", "0"))
    return f"{line_rate * 100:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dev_sec_ops.yml metadata.")
    parser.add_argument("--image-ref", default="wine-quality-mlops:local")
    parser.add_argument("--coverage-xml", default="coverage.xml")
    parser.add_argument("--output", default="dev_sec_ops.yml")
    parser.add_argument("--commit-limit", type=int, default=5)
    args = parser.parse_args()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "docker_image": collect_image_signature(args.image_ref),
        "git": {"last_5_commits": collect_last_commits(args.commit_limit)},
        "quality": {"test_coverage": collect_coverage(Path(args.coverage_xml))},
        "notes": [
            "Docker image digest may stay unavailable until the image is pushed to a registry.",
            "Commit hashes appear after the repository contains commits.",
        ],
    }

    output_path = Path(args.output)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
