# Citus Release Lifecycle

This runbook documents how version data flows across `citusdata` repositories, the active release policies, and the four maintainer procedures.

## 1. Data Flows

Each piece of release metadata has one source of truth and moves in one direction:

| # | Data | Source of truth | Downstream target | Mechanism |
|---|---|---|---|---|
| 1 | CI PostgreSQL versions, image suffix, stylechecker tools | `the-process`: root `versions.json` (one per active branch) | `citus`: `.github/ci-versions.json` and `.devcontainer` | `build-test-images.yml` pushes images and sends `citus-ci-images-ready` `repository_dispatch`; `citus` opens one sync PR per branch whose `the_process_branch` matches `line` |
| 2 | Citus release version (`vX.Y.Z`) | `citus`: git tag `vX.Y.Z` | `packaging` (`all-citus` -> packagecloud, `pgxn-citus` -> PGXN) -> `docker` (Docker Hub) | One manual `citus-release.yml` dispatch on `packaging@develop`, followed by merge-triggered publishing and `docker` dispatch |
| 3 | Docker PostgreSQL base versions | `docker`: `pkgvars` | `docker`: `Dockerfile`s | Internal to `citusdata/docker` |
| 4 | Packaging helper scripts (`v0.8.x`) | `tools`: git tag | `packaging@develop` and `docker@master` `.github/actions/setup-tools/action.yml` | Two one-line PRs |

`the-process` does not track Citus minor branch names (`release-14.3`, `release-13.2`, etc.). Each Citus branch declares its own `the_process_branch` in `.github/ci-versions.json`.

A weekly drift check in `citusdata/citus` inspects the outputs of Flows 1, 2, and 4 and opens a single issue when an automated sync PR is left unmerged.

### Contract 1 (`the-process` -> `citus`)

- Every active `the-process` branch (`master`, `release-14`, `release-13`, `release-12`) stores its PG matrix, default PG major, upgrade test majors, `upgrade_from` Citus tags, and `style_checker_tools_version` in root `versions.json`.
- After all release images finish pushing (`RELEASE=1`), `notify_citus` verifies `versions.json` `.line == github.ref_name` (so scratch branches such as `release-13-image` never dispatch) and emits `event_type: citus-ci-images-ready` with payload `{"line": "<line>", "sha": "<github.sha>", "tag_suffix": "<RELEASE=1 make -s print-tag-suffix>"}`.

## 2. Release Policies

- **Docker:** Publish Docker Hub updates only on `X.Y.0` of the active Docker release line, unless explicitly forced for a catch-up or security rebuild. Policy lives in `citusdata/docker`.
- **PGXN:** Publish stable Citus releases only, strictly forward-only. Never publish a backport from an older minor/major line over a newer PGXN version, and never publish pre-releases.
- **Package channels:** `community` carries GA packages; `community-nightlies` carries nightly builds.
- **packagecloud:** Primary GA distribution channel, published from `citusdata/packaging` (`all-citus`) after the pre-GA container install test passes.
- **PMC (packages.microsoft.com):** Deferred pending external Microsoft team decisions on package signing, ownership, and repository mapping.

## 3. Maintainer Flows

### Flow A: PostgreSQL minor release bump

1. Open and merge a PR updating `postgres_ci` in `versions.json` on each affected `the-process` branch (`master`, `release-14`, `release-13`, `release-12`).
2. Wait for `build-test-images.yml` to push the `-v<short-sha>` images and dispatch `citus-ci-images-ready` to `citusdata/citus`.
3. `citusdata/citus` automatically opens or updates one CI sync PR for each Citus branch whose `the_process_branch` matches `line`.
4. **Compatibility PR sequencing:** When a PostgreSQL minor release requires Citus code or test adjustments (such as `citusdata/citus#8977` on `release-13.2` or `citusdata/citus#8974` on `release-12.1`), either merge the compatibility PR first and re-run CI on the sync PR, or push the compatibility commits directly onto the sync PR branch before merging. Never merge a broken sync PR.
5. If Docker Hub base images also need the new PostgreSQL minor version, update `pkgvars` in `citusdata/docker` independently (Flow 3).

### Flow B: Citus release (`vX.Y.Z`)

1. Create and push the `vX.Y.Z` git tag on `citusdata/citus`.
2. Run `citus-release.yml` on `citusdata/packaging@develop` for `vX.Y.Z`.
3. Review and merge the `all-citus` PR (runs pre-GA package install tests, then publishes to packagecloud `community`). If eligible under the forward-only stable PGXN policy, review and merge the `pgxn-citus` PR.
4. Merging `all-citus` dispatches to `citusdata/docker`, which evaluates its own release policy, opens the Dockerfile update PR when eligible (or forced), and tags/publishes `vX.Y.Z` to Docker Hub upon merge.

### Flow C: Simultaneous PostgreSQL minor bump and Citus release

1. Complete Flow A first so Citus CI validates and merges against the new PostgreSQL minor images before tagging.
2. Tag `vX.Y.Z` on `citusdata/citus` and run Flow B. Because Flow 1 (`the-process` -> `citus`) and Flow 2 (`citus` -> `packaging` -> `docker`) are decoupled, they do not race.
3. If Docker Hub base images also move to the new PostgreSQL minor version, update `pkgvars` in `citusdata/docker` (Flow 3) before or alongside the Docker PR.

### Flow D: Manual checklist (PG major change or new Citus release line)

**Adding or removing a PostgreSQL major version:**
1. On the target `the-process` branch, update `versions.json` (`postgres_ci`, `default_pg_major`, `upgrade_test_pg`, `upgrade_from`) and any major-specific Dockerfile rules (such as PGDG apt components or `wal2json`).
2. Test the `-dev-<short-sha>` images on a draft Citus PR, then merge to `the-process` so `citus-ci-images-ready` opens the sync PR.
3. Adjust any major-specific matrices or version guards in `citusdata/citus`, and update `packaging` and `docker` `pkgvars` when packaging support for that major changes.

**Starting a new Citus release line (example: `release-15` / `release-15.0`):**
1. Branch `release-15` in `citusdata/the-process` from `master`.
2. Immediately update `versions.json` on `release-15` to set `"line": "release-15"`, supported `postgres_ci` majors, `upgrade_test_pg`, and `upgrade_from`. Until `"line"` equals `github.ref_name`, `notify_citus` stays silent and will not emit a `master` dispatch.
3. Branch `release-15.0` in `citusdata/citus` and set `"the_process_branch": "release-15"` in `.github/ci-versions.json`.
4. Confirm the next `the-process@release-15` image build dispatches and opens a sync PR targeting `release-15.0`.
5. Update the active Docker line policy in `citusdata/docker` when `15.0.0` becomes the active Docker release line.
