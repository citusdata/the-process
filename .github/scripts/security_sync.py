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


def lock_keep_resolvable(pipfile_path, pristine_text, targets, order):
    """Lock pipfile_path, keeping as many security bumps as pipenv can resolve.

    Fast path: apply every bump and lock once (the common, all-resolvable case --
    same cost as before). If that lock fails, confirm the un-bumped baseline still
    resolves (otherwise the failure is environmental -- re-raise so the run fails
    loudly), then re-add the bumps one at a time and drop any single bump that
    makes the tree unresolvable (e.g. a transitive cap that excludes the patched
    range). This stops one genuinely unfixable alert from poisoning the whole
    batch. On return pipfile_path holds exactly the kept subset with a matching
    Pipfile.lock; an all-dropped tree is restored to its committed lock (no churn).
    Returns the set of dropped ("blocked") packages.
    """
    lockfile = pipfile_path.with_name("Pipfile.lock")
    pristine_lock = lockfile.read_text() if lockfile.exists() else None

    def apply(subset):
        pipfile_path.write_text(pristine_text)
        for pkg in subset:
            update_pipfile(pipfile_path, pkg, targets[pkg]["patched"],
                           alert_section(targets[pkg]["scope"]))

    def lock():
        run(["pipenv", "lock"], cwd=pipfile_path.parent)

    apply(order)
    try:
        lock()
        return set()
    except subprocess.CalledProcessError:
        pass

    apply([])
    lock()  # baseline must resolve; a failure here is environmental -> re-raise
    kept, dropped = [], set()
    for pkg in order:
        apply(kept + [pkg])
        try:
            lock()
            kept.append(pkg)
        except subprocess.CalledProcessError:
            dropped.add(pkg)
    if not kept:
        apply([])
        if pristine_lock is not None:
            lockfile.write_text(pristine_lock)  # nothing resolved -> no lock churn
    elif dropped:
        apply(kept)  # strip the last failed trial's bump; lock already matches kept
    return dropped


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

    # Snapshot the pristine Pipfile so the resolver can re-derive any subset of
    # the bumps from a clean baseline.
    pristine = {pf: pf.read_text() for pf in pipfile_paths}
    order = list(targets)

    # Lock each regress tree, keeping as many bumps as pipenv can resolve. The two
    # trees are usually byte-identical, so an identical baseline is resolved once
    # and its Pipfile + lock copied to the twin rather than re-running the slow,
    # network-bound resolver. A bump pipenv cannot resolve (e.g. a transitive cap
    # excluding the patched range) is dropped and marked "blocked" -- it does not
    # poison the rest of the batch. A baseline that will not resolve at all is an
    # environment failure: it raises and is recorded as a hard lock failure.
    blocked = {}      # lockfile path -> set of packages dropped to make it resolve
    lock_failed = []  # lockfile paths whose baseline would not resolve
    resolved = {}     # pristine Pipfile hash -> (Pipfile, Pipfile.lock, dropped) or None
    for pf, lp in zip(pipfile_paths, lock_paths):
        digest = hashlib.sha256(pristine[pf].encode()).hexdigest()
        if digest in resolved:
            prior = resolved[digest]
            if prior is None:
                lock_failed.append(lp)          # same baseline already failed
            else:
                src_pf, src_lp, dropped = prior
                shutil.copyfile(src_pf, pf)     # identical baseline -> identical result
                shutil.copyfile(src_lp, lp)
                if dropped:
                    blocked[lp] = dropped
            continue
        try:
            dropped = lock_keep_resolvable(pf, pristine[pf], targets, order)
            resolved[digest] = (pf, lp, dropped)
            if dropped:
                blocked[lp] = dropped
        except subprocess.CalledProcessError as exc:
            print(f"pipenv lock failed in {pf.parent}: {exc}", file=sys.stderr)
            lock_failed.append(lp)
            resolved[digest] = None

    # Evaluate post-state and classify each target.
    summary = []
    addressed = []
    for pkg, info in targets.items():
        post = [lock_version(lp, pkg) for lp in lock_paths]
        statuses = []
        for lp, before, after in zip(lock_paths, pre_versions[pkg], post):
            if lp in lock_failed:
                statuses.append("not-fixed")
            elif pkg in blocked.get(lp, set()):
                statuses.append("blocked")
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
        elif all(s in ("blocked", "already-satisfied") for s in statuses):
            overall = "blocked"
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
        "blocked": [s["package"] for s in summary if s["overall"] == "blocked"],
        "details": summary,
    }, indent=2))

    for s in summary:
        print(f"{s['overall']:20s} {s['package']} -> {s['patched']} ({s['scope']})")

    # Fail loudly only on a hard lock failure (bad environment) or an unexpected
    # classification. Packages pipenv cannot resolve are "blocked", not "failed":
    # they are reported but do not sink the run, so the resolvable subset still
    # opens PRs. An all "already-satisfied" run, or one that addressed everything,
    # is a success; the workflow's own git-diff guard prevents an empty PR when
    # nothing actually changed.
    failed = [s["package"] for s in summary if s["overall"] == "failed"]
    if failed:
        sys.exit(
            "Could not resolve the following package(s); failing before opening "
            "PRs: " + ", ".join(failed)
        )


if __name__ == "__main__":
    main()
