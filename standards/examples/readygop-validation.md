# ReadyGOP third-application validation

ReadyGOP passed the scoped offline compatibility assessment with its existing
host/module layout intact. The [source mapping](../reference-applications/readygop-infra.md)
separates implemented behavior, baseline gaps and proposed follow-ups. This extends
coverage to a third app, a newer scheduling interface and a modular PGSync subsystem;
it is not another Cline pilot, deployment test or Tekton procedure.

## Recorded evidence

| Item | Observed result |
| --- | --- |
| App revision | `dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35` |
| Installed toolkit payload | `63fae878f790d8ce3e0bf9f04c4cc3600a3d63a2`; 21 managed files installed and checked from a clean toolkit checkout |
| Dependencies | Existing ignored local lock/vendor copied unchanged; no network or upgrade. Declared OneHQ v1.0.20 resolves locally to `dbfcec9face86abac6b131c9cc0c7dd2c303d967` |
| Reviewer | [Executable assessment](../../scripts/validate-readygop.py), added during this task; SHA256 and vendor fingerprint in [results](readygop-validation.results.json) |
| Tools | Tanka 0.36.3, jsonnet-bundler 0.6.0 available; Python 3 tooling. The run did not invoke jb or fetch dependencies |
| Baseline | Staging 82 resources; production 81; default 0; installed-context output equals a clean clone with the same copied dependencies |
| Rails probes | Staging API/master/migration; production API/debug/worker/master/migration. Image, migration identity/Pod job label/container name and two/four gates follow |
| PGSync probes | Each environment's producer, consumer, reindex Job and selective CronJob init image follow `pgsyncCore`; other names/gates stay fixed |
| Difference review | One actual version-file role edit per probe; full object equality elsewhere; opposite/default target output stays identical; functional whitespace checks pass |
| Negative controls | Global `pgsync.new` enabled=false is ignored. Disabling only reindex removes its Job but retains producer/consumer gates; this is not a safe global disable |
| Relationships | Seven/nine Service selections, Pod selectors, Ingress ports, HPA targets, namespace-aware Role bindings, app-created Secret keys and volume/claim-template mounts checked |
| Known env exception | Master `IS_GOOD_JOB` occurs twice in staging and three times in production; preserved and explicitly recorded, values omitted |
| Existing formatting | `tk fmt --test lib environments` exits 16 at baseline, left untouched |
| Shell syntax | 59 staging and 36 production embedded shell instances pass nonexecuting shell parsing; local extract.sh also passes bash -n |
| Maps with inference | Staging: 97 nodes / 222 relationships / 13 unresolved. Production: 99 / 230 / 16. Two claim templates each |
| Original checkout | Tracked state/HEAD and ignored lock/vendor fingerprints unchanged; no adoption, functional edit, deployment or housekeeping fix in the source checkout |

The result's `toolkit_revision` identifies the checkout HEAD during the assessment;
the new reviewer is additionally fingerprinted because it was being implemented.
The installed manifest identifies the actual tested payload. Secrets, raw manifests,
literal env values and embedded commands are not included in evidence. Package/tree
checksums are integrity metadata, not credential values.

## Repeat with the existing local dependency baseline

Use Git, Python 3.9+ and Tanka. From a reviewed **toolkit root**, replace the source
path and choose a new disposable directory:

```sh
TOOLKIT_ROOT="$PWD"
READYGOP_SOURCE=/path/to/readygop-infra
READYGOP_ASSESSMENT_DIR="$(dirname "$PWD")/readygop-toolkit-assessment"

git clone --no-hardlinks "$READYGOP_SOURCE" "$READYGOP_ASSESSMENT_DIR/app"
git -C "$READYGOP_ASSESSMENT_DIR/app" checkout --detach dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35
git -C "$READYGOP_ASSESSMENT_DIR/app" remote remove origin
cp "$READYGOP_SOURCE/jsonnetfile.lock.json" "$READYGOP_ASSESSMENT_DIR/app/jsonnetfile.lock.json"
cp -R "$READYGOP_SOURCE/vendor" "$READYGOP_ASSESSMENT_DIR/app/vendor"
```

The last two commands require the original local ignored dependencies. Copy them
only into the disposable app; do not edit the original. Preserve any dependency
symlinks using your platform's copy tool. The reviewer requires the recorded
[lock](readygop-dependencies.lock.json) and prints the actual vendor fingerprint.
Compare it with [the historical result](readygop-validation.results.json) to establish
byte-level reproduction; a matching lock alone does not certify arbitrary vendor bytes.

If those local dependencies are unavailable, copy the recorded lock into the
disposable clone and run `jb install` **there** instead. That requires network/library
access and creates a fresh implementation: compare its fingerprint and relevant
source before claiming it reproduces the recorded local baseline. Do not silently
substitute another app's vendor or use `jb update`.

To repeat installation, use a **clean committed toolkit checkout**:

```sh
python3 -B scripts/install.py "$READYGOP_ASSESSMENT_DIR/app"
python3 -B scripts/install.py "$READYGOP_ASSESSMENT_DIR/app" --check
```

Record the actual revision/count for a newer toolkit. Fill application `AGENTS.md`
manually from [the template](../../templates/AGENTS.md), preserving existing
instructions and linking the app's PGSync architecture. The recorded isolated
checkout has completed context. Neither the installer nor the reviewer edits the
original app's guidance.

Run from the **toolkit root**:

```sh
python3 -B scripts/validate-readygop.py "$READYGOP_ASSESSMENT_DIR/app"
```

The reviewer requires the baseline commit and unchanged tracked files. It checks
installed-file hashes when a manifest exists (manifest consistency, not independent
trust), captures baseline objects in memory, and probes in another temporary local
clone with no remote. Each environment's Rails and PGSync core edits run separately,
with source restored between probes. It also exercises the ignored-global/partial-
disable negative controls, then records baseline formatting and nonexecuting shell
syntax. It does not execute SQL, CLI/Git commands embedded in workloads, or extraction.

Successful scoped status is `scoped_compatibility_passed_with_baseline_gaps`.
Formatting failure and duplicate env entries remain explicit exceptions. Rejection
tests protect missed production workers, accidental hidden-worker activation,
stale debug gates, missed selective init images, unintended fixed Job renames,
Secret disclosure/differences and empty/failed render output.

Exact render commands, from the **isolated app root**, require no ext vars:

```text
tk eval environments/default
tk eval environments/readygop-staging
tk eval environments/readygop-production
tk fmt --test lib environments
```

The reviewer captures raw output privately in memory; direct eval output includes
Secret data/placeholders and must not be published. No AVP lookup or cluster access
is needed for these local renders. The renderer's success does not establish image
contents, API/schema compatibility, external resources or readiness.

## Generate resource maps

From the **toolkit root** against the unchanged isolated baseline:

```sh
python3 -B scripts/map-kubernetes.py --app "$READYGOP_ASSESSMENT_DIR/app" \
  --environment environments/readygop-staging --infer-env-links \
  --output generated/kubernetes/readygop-staging
python3 -B scripts/map-kubernetes.py --app "$READYGOP_ASSESSMENT_DIR/app" \
  --environment environments/readygop-production --infer-env-links \
  --output generated/kubernetes/readygop-production
```

Open `index.html`; keep its JSON/Mermaid siblings for downloads. These files stay
outside the app and are ignored by Git. The existing mapper is unchanged. It maps
actual output, not hidden source declarations, live traffic or all command/CRD
dependencies. Inferred links and unresolved objects retain their documented limits.

## Operational facts and unexecuted work

The emitted staging full-rebuild CronJob overrides its component's suspended value
to false. Production hides that CronJob and its account/RBAC. This was recorded,
not changed. Selective reindex remains suspended and needs its target placeholder
replaced by the existing execution mechanism before any runtime use.

The original app has no tracked test suite. Dependency deployment provenance,
duplicate env reconciliation, rebuild suspend intent, coordinated disable behavior,
AVP/Argo delivery and fixed-name Job rerun handling remain separate follow-ups.
No image pulls, schema/cluster queries, workload execution, Git pushes, access
changes or Cline runs were performed. These app CronJobs do not complete Step 6's
separate Tekton procedure.
