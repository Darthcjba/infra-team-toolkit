# HQAdmin second-application validation

The responsibility-based standard works with HQAdmin's existing per-environment
values/render files. This scoped offline assessment passed; it also recorded
baseline gaps. See the [source mapping](../reference-applications/hqadmin-infra.md)
for implemented behavior, source links, external ownership and proposed follow-ups.
This is a second application assessment, not a second Cline pilot or production approval.

## Recorded evidence

| Item | Observed result |
| --- | --- |
| Application | OneHQ/hqadmin-infra `79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0` |
| Installed toolkit payload | `e93dffdbb7e8c1687c11a45c53a929db01f0a8d9`; 17 managed files installed and `--check` verified while that toolkit checkout was clean |
| Assessment tooling | [Reviewer](https://github.com/Darthcjba/infra-team-toolkit/blob/63fae878f790d8ce3e0bf9f04c4cc3600a3d63a2/scripts/validate-hqadmin.py), added during this assessment; its SHA256 is in the [result](hqadmin-validation.results.json) |
| Resolved dependencies | Fresh [recorded lock](hqadmin-dependencies.lock.json), including declared OneHQ v1.0.14 resolving to `c34a0d696426e3a178fdb8587625f3100f8d46c2`; no production lock was available |
| Runtime | Tanka 0.36.3, jsonnet-bundler 0.6.0; Python 3 used for tooling |
| Baseline renders | Staging 37 resources; production 37; default scaffold 0 |
| Guidance installation | Installed and clean-clone resource objects compare equal in all three targets; no dependency/layout changes |
| Actual scoped edit | Only `environments/hqadmin-staging/staging-version.json.backend`, to synthetic tag `toolkit-validation`, inside a temporary clone |
| Shared consumers | API, debug, GoodJob worker, GoodJob master and migration Job all follow |
| Expected identity changes | Migration metadata name, Pod job label and container name; four inherited `JOB_NAME` gates follow |
| Full comparison | Every unrelated rendered field equals baseline; production/default remain identical; functional diff whitespace check passed |
| Component-only control | API-local tag edit propagates to all four Deployments but leaves migration image/identity/gates on the canonical tag |
| Relationships | Deployment selectors, five Service selections (including a documented baseline overlap), Ingress ports, HPA targets, binding Roles, app-created Secret keys and non-StatefulSet mounts checked |
| Embedded scripts | 20 shell command instances per target pass `sh -n`/`bash -n`, without executing them |
| Existing formatting | `tk fmt --test lib environments` exits 16 for both main/values pairs; existing baseline failure, left untouched |
| Maps | Each: 37 resources, 53 nodes, 129 relationships with inference, 1 claim template, 15 unresolved identities |
| Source checkout | Clean before/after; no files, dependencies, ownership, housekeeping or external state changed |

The JSON result contains no raw manifests, Secret payloads, credential values,
literal environment values or workload commands. The dependency lock's integrity
checksums are public package metadata. The reviewer captures raw render/error
streams in memory and emits fixed diagnostics on failure.

## Repeat the assessment

Use a reviewed toolkit checkout containing these files. Git, Python 3.9+, Tanka and
jsonnet-bundler must already be installed. The first dependency download requires
network access and access to OneHQ's library. Work only in a new disposable directory.
From the **toolkit root**, replace the source path:

```sh
TOOLKIT_ROOT="$PWD"
HQADMIN_SOURCE=/path/to/hqadmin-infra
HQADMIN_ASSESSMENT_DIR="$(dirname "$PWD")/hqadmin-toolkit-assessment"

git clone --no-hardlinks "$HQADMIN_SOURCE" "$HQADMIN_ASSESSMENT_DIR/app"
git -C "$HQADMIN_ASSESSMENT_DIR/app" checkout --detach 79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0
git -C "$HQADMIN_ASSESSMENT_DIR/app" remote remove origin
cp standards/examples/hqadmin-dependencies.lock.json "$HQADMIN_ASSESSMENT_DIR/app/jsonnetfile.lock.json"
cd "$HQADMIN_ASSESSMENT_DIR/app"
jb install
cd "$TOOLKIT_ROOT"
```

That lock deliberately reproduces this assessment's dependency resolution. It
does not assert or change production dependency provenance. Do not run `jb update`
or borrow the first reference app's vendor directory to make HQAdmin render.

Installation is optional for repeating the render probes, but required to repeat
the adoption check. From a **clean committed toolkit checkout**:

```sh
python3 -B scripts/install.py "$HQADMIN_ASSESSMENT_DIR/app"
python3 -B scripts/install.py "$HQADMIN_ASSESSMENT_DIR/app" --check
```

Record the revision actually installed; a newer toolkit revision can have more
managed files than the historical 17 above. Complete application context manually
using [the template](https://github.com/Darthcjba/infra-team-toolkit/blob/63fae878f790d8ce3e0bf9f04c4cc3600a3d63a2/templates/AGENTS.md) and the source mapping. Do not
replace source application instructions. The recorded isolated checkout has a
filled `AGENTS.md`; the installer itself does not create it.

Run from the **toolkit root**:

```sh
python3 -B scripts/validate-hqadmin.py "$HQADMIN_ASSESSMENT_DIR/app"
```

The script requires the inspected app commit, unchanged tracked files, recorded
dependency lock and resolved vendor directory. Untracked installed guidance may
be present. When a manifest exists, it verifies each managed file's checksum and
records that installed revision. Hash agreement verifies manifest consistency,
not independent trust in an arbitrary manifest.

It captures the three baseline renders, creates another disposable local clone
with Git metadata/no remote, copies dependencies, and compares complete objects
before the change. It edits the real staging version input in that temporary
clone, checks the full expected difference and relationships, and verifies production
and default are unchanged. It restores the input before the component-only control,
then runs baseline formatting and nonexecuting shell syntax checks. Temporary
files are removed automatically. The supplied app and original source are not edited.

The success status is `scoped_compatibility_passed_with_baseline_gaps`. It does
not mean every check passed: the baseline formatting exit code is recorded
separately. Rejection tests cover missed worker images, stale gates, partial Job
identity updates, unrelated policy/Secret changes, empty output and raw error privacy.

Raw renders from the exact commands below contain Secret data/placeholders; use
controlled capture rather than publishing terminal output:

```text
# Working directory: isolated HQAdmin app root. No ext vars are required.
tk eval environments/default
tk eval environments/hqadmin-staging
tk eval environments/hqadmin-production

# Existing format check; expected to fail at this app revision.
tk fmt --test lib environments
```

There is no application test suite to invoke. Jsonnet evaluation requires neither
AVP authorization nor live cluster access. AVP resolution and the Argo plugin's
runtime configuration remain separate delivery inputs and were not exercised.

## Generate the diagrams

From the **toolkit root**, against the unchanged isolated baseline:

```sh
python3 -B scripts/map-kubernetes.py --app "$HQADMIN_ASSESSMENT_DIR/app" \
  --environment environments/hqadmin-staging --infer-env-links \
  --output generated/kubernetes/hqadmin-staging
python3 -B scripts/map-kubernetes.py --app "$HQADMIN_ASSESSMENT_DIR/app" \
  --environment environments/hqadmin-production --infer-env-links \
  --output generated/kubernetes/hqadmin-production
```

Open each output's `index.html`. JSON/Mermaid siblings provide exports. Generated
files are ignored and stay outside the application. The diagrams use the existing
mapper unchanged; no HQAdmin-specific schema adapter was needed. `--infer-env-links`
marks four migration gates and other matching endpoint conventions as inferred,
not observed traffic. Without that option only declared/default/selector/membership
relationships are shown. Namespace comes from each target's Tanka spec.

## Limits and follow-up

The backend Service matches migration Pod labels as well as API labels. Preserve
and flag this existing overlap during a compatibility exercise; review any fix
separately with intended selector/Pod changes and cluster evidence.

Ignored locks and moving dependency refs limit production reproducibility.
Redis configuration, pull credentials and accounts have unresolved ownership;
other unresolved references are expected operator/external/default resources.
An unresolved graph node means absent from this input, not absent from the cluster.

No Kubernetes schema validation, image existence/content checks, AVP secret
resolution, external-resource lookup, workload execution, Argo sync or deployment
was performed. No Cline run was performed for HQAdmin; the earlier CLI pilot remains
evidence for its original app and task only. The separate Tekton procedure is pending.
