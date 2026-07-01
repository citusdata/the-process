#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from packaging.specifiers import SpecifierSet
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


def bump_lower_bound(spec, patched):
    """Raise a Pipfile version specifier's lower bound to >= patched while
    preserving any existing upper bound / exclusion clauses, so a security
    bump never silently widens the maintainer's intended range.

    Returns (new_spec, conflict). conflict is True when the patched version is
    excluded by an existing upper bound or exclusion (e.g. patched 6.6.1 against
    an existing "<6.6.0"); the caller then leaves the file unchanged so the run
    fails loudly with a clear verdict instead of relaxing the cap.
    """
    spec = (spec or "").strip()
    patched_v = Version(patched)
    if spec in ("", "*"):
        return f">={patched}", False

    clauses = [c.strip() for c in spec.split(",") if c.strip()]
    lower, upper, exact = [], [], []
    for c in clauses:
        if c.startswith("=="):
            exact.append(c)
        elif c.startswith((">=", ">")):
            lower.append(c)
        else:
            # <, <=, !=, ~=, or anything else: a ceiling/exclusion to preserve.
            upper.append(c)

    # A patched version blocked by a preserved ceiling/exclusion is a real
    # conflict the maintainer must resolve; signal it rather than widening.
    guard = SpecifierSet(",".join(upper)) if upper else SpecifierSet("")
    if patched_v not in guard:
        return None, True

    if exact:
        # Maintainer pinned exactly: keep that discipline, bumping the pin to
        # the patched release (never downgrade if it is already higher).
        pinned = Version(exact[0][2:])
        if pinned >= patched_v:
            return spec, False
        return f"=={patched}", False

    # Keep the highest existing floor so we never lower an already-stricter one.
    existing_floor = None
    for c in lower:
        v = Version(re.sub(r"^[>=]+", "", c))
        if existing_floor is None or v > existing_floor:
            existing_floor = v
    floor = patched_v if existing_floor is None or patched_v > existing_floor \
        else existing_floor
    return ",".join([f">={floor}"] + upper), False


def update_pipfile(pipfile_path, package, patched, section):
    """Patch direct dep version, or append to the proper section.
    Returns True if the file was modified, False otherwise."""
    content = pipfile_path.read_text()
    pattern = re.compile(
        rf'^(\s*"?{re.escape(package)}"?\s*=\s*)"([^"]*)"\s*$',
        re.IGNORECASE | re.MULTILINE,
    )
    m = pattern.search(content)
    if m:
        new_spec, conflict = bump_lower_bound(m.group(2), patched)
        if conflict:
            print(
                f"WARNING: {package} {patched} is excluded by its existing "
                f'constraint "{m.group(2)}" in {pipfile_path}; leaving '
                "unchanged (it will be reported as not-fixed).",
                file=sys.stderr,
            )
            return False
        new_content = content[:m.start(2)] + new_spec + content[m.end(2):]
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alerts", required=True)
    parser.add_argument("--citus-root", required=True)
    parser.add_argument("--summary-out", required=True,
                        help="Path to write per-alert outcome JSON")
    args = parser.parse_args()

    citus_root = Path(args.citus_root)

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
        # No alert carries a first_patched_version yet: upstream has not shipped a
        # fix. There is genuinely nothing to do, so exit cleanly (a green, no-op
        # run) rather than failing loudly every week until upstream patches.
        print("No actionable alerts (none had a first_patched_version); nothing to sync.")
        return

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

    # Lock each regress tree. The two trees are usually byte-identical, so an
    # identical post-edit Pipfile is locked once and its resolved lock copied to
    # the twin rather than re-running the slow, network-bound resolver. A lock
    # failure (e.g. an unresolvable constraint such as a transitive cap blocking
    # the patched range) is not a crash: record it so the affected targets are
    # classified as not-fixed and the run fails loudly with a clean verdict.
    lock_failed = []
    locked = {}  # post-edit Pipfile hash -> its Pipfile.lock path, or None if the lock failed
    for pf, lp in zip(pipfile_paths, lock_paths):
        digest = hashlib.sha256(pf.read_bytes()).hexdigest()
        if digest in locked:
            twin = locked[digest]
            if twin is None:
                lock_failed.append(lp)        # same input already failed to resolve
            else:
                shutil.copyfile(twin, lp)     # identical input -> identical lock
            continue
        try:
            run(["pipenv", "lock"], cwd=pf.parent)
            locked[digest] = lp
        except subprocess.CalledProcessError as exc:
            print(f"pipenv lock failed in {pf.parent}: {exc}", file=sys.stderr)
            lock_failed.append(lp)
            locked[digest] = None

    # Evaluate post-state and classify each target.
    summary = []
    addressed = []
    for pkg, info in targets.items():
        post = [lock_version(lp, pkg) for lp in lock_paths]
        statuses = []
        for lp, before, after in zip(lock_paths, pre_versions[pkg], post):
            if lp in lock_failed:
                statuses.append("not-fixed")
            elif after is None:
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

    # Fail loudly only when a fixable alert could not be resolved (e.g. a blocked
    # constraint or a failed lock). An all "already-satisfied" run, or a run that
    # addressed everything, is a success: the workflow's own git-diff guard
    # prevents an empty PR when nothing actually changed.
    failed = [s["package"] for s in summary if s["overall"] == "failed"]
    if failed:
        sys.exit(
            "Could not resolve the following package(s); failing before opening "
            "PRs: " + ", ".join(failed)
        )


if __name__ == "__main__":
    main()
