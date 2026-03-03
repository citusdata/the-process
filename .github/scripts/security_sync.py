#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
from pathlib import Path


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def capture(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout


def normalize_package(name):
    return name.strip().lower()


def update_pipfile(pipfile_path, patched_versions):
    content = pipfile_path.read_text()
    original_content = content

    for package in ("cryptography", "werkzeug"):
        patched = patched_versions.get(package)
        if not patched:
            continue

        pattern = re.compile(
            rf'^(\s*"?{re.escape(package)}"?\s*=\s*)"[^"]*"\s*$',
            re.IGNORECASE | re.MULTILINE,
        )

        def replacement(match):
            return f'{match.group(1)}"=={patched}"'

        content = pattern.sub(replacement, content)

    if content != original_content:
        pipfile_path.write_text(content)


def write_requirements(the_process_root, base_requirements, dev_requirements, citus_sha):
    base_header = (
        f"# generated from Citus's Pipfile.lock (in src/test/regress) as of {citus_sha}\n"
        "# using `pipenv requirements > requirements.txt`, so as to avoid the\n"
        "# need for pipenv/pyenv in this image\n\n"
    )
    dev_header = (
        f"# generated from Citus's Pipfile.lock (in src/test/regress) as of {citus_sha}\n"
        "# using `pipenv requirements --dev > requirements.txt`, so as to avoid the\n"
        "# need for pipenv/pyenv in this image\n\n"
    )

    base_targets = [
        the_process_root / "circleci/images/citusupgradetester/files/etc/requirements.txt",
        the_process_root / "circleci/images/failtester/files/etc/requirements.txt",
        the_process_root / "circleci/images/pgupgradetester/files/etc/requirements.txt",
    ]
    for target in base_targets:
        target.write_text(base_header + base_requirements)

    dev_target = the_process_root / "circleci/images/stylechecker/files/etc/requirements.txt"
    dev_target.write_text(dev_header + dev_requirements)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alerts", required=True)
    parser.add_argument("--citus-root", required=True)
    parser.add_argument("--the-process-root", required=True)
    args = parser.parse_args()

    citus_root = Path(args.citus_root)
    the_process_root = Path(args.the_process_root)

    alerts = json.loads(Path(args.alerts).read_text())
    patched_versions = {}
    for alert in alerts:
        package = normalize_package(alert["dependency"]["package"]["name"])
        patched = (alert.get("security_vulnerability", {}).get("first_patched_version") or {}).get("identifier")
        if patched:
            patched_versions[package] = patched

    update_pipfile(citus_root / "src/test/regress/Pipfile", patched_versions)
    update_pipfile(citus_root / ".devcontainer/src/test/regress/Pipfile", patched_versions)

    run(["pipenv", "lock"], cwd=citus_root / "src/test/regress")
    run(["pipenv", "lock"], cwd=citus_root / ".devcontainer/src/test/regress")

    base_requirements = capture(["pipenv", "requirements"], cwd=citus_root / "src/test/regress")
    dev_requirements = capture(["pipenv", "requirements", "--dev"], cwd=citus_root / "src/test/regress")

    citus_sha = capture(["git", "rev-parse", "--short", "HEAD"], cwd=citus_root).strip()
    write_requirements(the_process_root, base_requirements, dev_requirements, f"citusdata/citus@{citus_sha}")


if __name__ == "__main__":
    main()
