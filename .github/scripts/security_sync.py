#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from packaging.version import Version
except ImportError:
    sys.exit("packaging package required: pip install packaging")


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def capture(command, cwd=None):
    return subprocess.run(
        command, cwd=cwd, check=True, text=True, capture_output=True
    ).stdout


def normalize_package(name):
    return name.strip().lower()


def alert_section(scope):
    # Dependabot scope: "runtime" -> [packages], "development" -> [dev-packages]
    return "[dev-packages]" if scope == "development" else "[packages]"


def update_pipfile(pipfile_path, package, patched, section):
    """Patch direct dep version, or append to the proper section.
    Returns True if the file was modified, False otherwise."""
    content = pipfile_path.read_text()
    pattern = re.compile(
        rf'^(\s*"?{re.escape(package)}"?\s*=\s*)"[^"]*"\s*$',
        re.IGNORECASE | re.MULTILINE,
    )
    if pattern.search(content):
        new_content = pattern.sub(rf'\g<1>">={patched}"', content)
        if new_content != content:
            pipfile_path.write_text(new_content)
            return True
        return False

    # Not a direct dep: append to the requested section so pipenv lock pulls it.
    section_re = re.compile(rf'^{re.escape(section)}\s*$', re.MULTILINE)
    m = section_re.search(content)
    if not m:
        # Section missing entirely; append at end.
        addition = f'\n{section}\n{package} = ">={patched}"\n'
        pipfile_path.write_text(content + addition)
    else:
        insert_at = m.end()
        new_content = (
            content[:insert_at]
            + f'\n{package} = ">={patched}"'
            + content[insert_at:]
        )
        pipfile_path.write_text(new_content)
    return True


def lock_version(lockfile_path, package):
    if not lockfile_path.exists():
        return None
    data = json.loads(lockfile_path.read_text())
    for group in ("default", "develop"):
        info = data.get(group, {}).get(package)
        if info and "version" in info:
            return info["version"].lstrip("=")
    return None


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
    parser.add_argument("--summary-out", required=True,
                        help="Path to write per-alert outcome JSON")
    args = parser.parse_args()

    citus_root = Path(args.citus_root)
    the_process_root = Path(args.the_process_root)

    alerts = json.loads(Path(args.alerts).read_text())

    # Deduplicate by package, keep highest patched version per package.
    targets = {}
    for alert in alerts:
        package = normalize_package(alert["dependency"]["package"]["name"])
        patched = (alert.get("security_vulnerability", {})
                        .get("first_patched_version") or {}).get("identifier")
        scope = alert.get("dependency", {}).get("scope", "runtime")
        if not patched:
            continue
        prev = targets.get(package)
        if prev is None or Version(patched) > Version(prev["patched"]):
            targets[package] = {"patched": patched, "scope": scope}

    if not targets:
        Path(args.summary_out).write_text(json.dumps({"addressed": [], "details": []}, indent=2))
        sys.exit("No actionable alerts (none had a first_patched_version); aborting before opening PRs.")

    pipfile_paths = [
        citus_root / "src/test/regress/Pipfile",
        citus_root / ".devcontainer/src/test/regress/Pipfile",
    ]
    lock_paths = [p.with_name("Pipfile.lock") for p in pipfile_paths]

    # Snapshot pre-state for each package.
    pre_versions = {pkg: [lock_version(lp, pkg) for lp in lock_paths]
                    for pkg in targets}

    for pkg, info in targets.items():
        section = alert_section(info["scope"])
        for pf in pipfile_paths:
            update_pipfile(pf, pkg, info["patched"], section)

    for pf in pipfile_paths:
        run(["pipenv", "lock"], cwd=pf.parent)

    # Evaluate post-state and classify each target.
    summary = []
    addressed = []
    for pkg, info in targets.items():
        post = [lock_version(lp, pkg) for lp in lock_paths]
        statuses = []
        for before, after in zip(pre_versions[pkg], post):
            if after is None:
                statuses.append("absent")
            elif Version(after) >= Version(info["patched"]):
                if before is None or Version(before) < Version(info["patched"]):
                    statuses.append("applied")
                else:
                    statuses.append("already-satisfied")
            else:
                statuses.append("not-fixed")
        if any(s == "applied" for s in statuses) and \
           all(s in ("applied", "already-satisfied") for s in statuses):
            overall = "addressed"
        elif all(s == "already-satisfied" for s in statuses):
            overall = "already-satisfied"
        else:
            overall = "failed"
        summary.append({
            "package": pkg, "patched": info["patched"],
            "scope": info["scope"], "statuses": statuses, "overall": overall,
        })
        if overall == "addressed":
            addressed.append(pkg)

    Path(args.summary_out).write_text(json.dumps({
        "addressed": addressed,
        "details": summary,
    }, indent=2))

    for s in summary:
        print(f"{s['overall']:20s} {s['package']} -> {s['patched']} ({s['scope']})")

    if not addressed:
        sys.exit("No alerts were addressed by this run; aborting before opening PRs.")

    base_requirements = capture(["pipenv", "requirements"], cwd=pipfile_paths[0].parent)
    dev_requirements = capture(["pipenv", "requirements", "--dev"], cwd=pipfile_paths[0].parent)
    citus_sha = capture(["git", "rev-parse", "--short", "HEAD"], cwd=citus_root).strip()
    write_requirements(the_process_root, base_requirements, dev_requirements,
                       f"citusdata/citus@{citus_sha}")


if __name__ == "__main__":
    main()
