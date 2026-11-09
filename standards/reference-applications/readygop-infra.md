# ReadyGOP reference assessment

Status: scoped offline compatibility assessment of `Darthcjba/readygop-infra`
commit `dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35`. The isolated checkout received
toolkit `63fae878f790d8ce3e0bf9f04c4cc3600a3d63a2` (21 managed files, install/check
passed). See the [repeatable procedure](../examples/readygop-validation.md),
[reviewer](https://github.com/Darthcjba/infra-team-toolkit/blob/733d9a2f5c7a9a1647c43926f2e760f2e5bdf095/scripts/validate-readygop.py) and
[sanitized results](../examples/readygop-validation.results.json).

The original checkout was clean and stayed unchanged, including its existing
ignored lock/vendor bytes. No repository/parent `AGENTS.md` was found. Root README,
PGSync README/ARCHITECTURE, toolkit rules, standard and Jsonnet skill guidance were
read explicitly. The PGSync architecture files match across environments; their
implementation differences were inspected separately. No Cline task, deployment,
workload execution, dependency download or upgrade occurred. Toolkit maintenance
ownership is Darthcjba; Git remote ownership alone does not establish runtime ownership.

## Existing file responsibilities

Links below pin the inspected application revision. The large host values files
and smaller reusable subsystem coexist; neither needs a directory migration.

| Responsibility | Actual files and source references |
| --- | --- |
| Environment entry points and host resource composition | [Staging main][st-main], imports at lines 1–8, host object plus `pgsyncResources(values, k, kone)` at line 973; [production main][prod-main] has its own visibility/policy choices |
| Host defaults, target policy and module integration | [Staging values][st-values] and [production values][prod-values]; direct self-imports, local PGSync input objects, host defaults and final `+ pgsyncValues` |
| Image roles | [Staging versions][st-versions] and [production versions][prod-versions]: `rails`, `react`, `search`, `websocket`, `pgsyncCore`, `pgsyncHash` |
| Other environment inputs | `*-s3.json` in each target; production also imports `production-hpa.json` for HPA/Git-update jobs; many endpoints/namespace choices remain in host values |
| Destination | Target `spec.json` supplies `readygop-staging` or `readygop-production` namespace/API server; default main is an empty scaffold |
| Native/library imports | [`lib/k.libsonnet`][k-import], [`lib/k8s-onehq.libsonnet`][onehq-import], [`lib/kyverno.libsonnet`][kyverno-import] |
| Dependency declarations and local resolution | [`jsonnetfile.json`][dependencies]; lock/vendor are [ignored][ignore] but were present locally and copied unchanged |
| PGSync public composition | [`pgsync/pgsync-values.libsonnet`][composition]: `new`, `postgres`, `redis`, `elasticsearch`; maps host settings into normalized configuration/components |
| Infrastructure requirements | [`config/postgres.libsonnet`][postgres], [`config/redis.libsonnet`][redis], [`config/elasticsearch.libsonnet`][elastic] overlay host infrastructure |
| Runtime adapter and shared settings | [`config/pgsync.libsonnet`][config], `lib/common.libsonnet`; `enabled` is normalized to true, not exposed as a forwarded global toggle |
| Names and ordering references | [`lib/names.libsonnet`][names] and [production counterpart][prod-names]; component outputs supply names to later components |
| Runtime behavior and commands | `pgsync/components/` permissions, templates, full/selective reindex, finalization, producer, consumer, full rebuild; see [composition imports][composition] |
| PGSync resource construction | [Staging resources][resources] and [production resources][prod-resources]; native objects plus OneHQ/native patches; both CronJob nesting and field visibility matter |
| Index settings | Module-local `pgsync/indexes.settings.json`, imported by composition; sibling root index/target JSON files do not automatically configure this import |
| Architecture guidance | [`pgsync/README.md`][pg-readme] and [`ARCHITECTURE.md`][architecture]; development boundaries and intended invariants must be checked against actual output |
| Local scripts and validation | `environments/readygop-staging/scripts/extract.sh`; no tracked test suite/CI validation procedure. Root README is scaffold guidance, mentioning 1.28 while native imports use 1.35 |

## Dependency authority

This application uses the newer object-shaped scheduling interface. Its **existing
local** ignored lock resolved the declarations below; the original vendor directory
was copied to the isolated checkout without network access. The result records a
vendor tree SHA256; source/copy fingerprints matched before and after validation.

| Dependency | Local locked revision |
| --- | --- |
| OneHQ/tanka-lib-k8-onehq, requested v1.0.20 | `dbfcec9face86abac6b131c9cc0c7dd2c303d967` |
| grafana/jsonnet-libs, ksonnet-util | `74c55e5f503a1f84eb939f7c421e366d04f25961` |
| jsonnet-libs/docsonnet, doc-util | `bf6f08ae02a51c48bdcec4629b1c1a5a62c6f803` |
| jsonnet-libs/k8s-libsonnet, 1.35 | `18e7a26f0699cb8b006494f40b93ddd06d33b299` |
| jsonnet-libs/kyverno-libsonnet, 1.9 | `901e8ef1f22469dbe506f68c8a5a105766793dfb` |

The [recorded lock](../examples/readygop-dependencies.lock.json) reproduces these
refs. Local lock/vendor provenance does not independently establish either the
deployed baseline or byte identity with upstream. This differs from HQAdmin's
fresh resolution: ReadyGOP already had an implementation available to inspect.

Resolved [ServiceLevel][service-level] and [Tolerations][tolerations] accept
`(name, serviceLevel)`, reading `organization`, `mode` and `definitions`.
`getAffinity(name, values)` reads `values.serviceLevel`. Name substring matching
still selects policy. Preserve this interface rather than copying the older
three-argument consumers' scheduling inputs.

The resolved [container constructor][containers] concatenates `image + tag`, prunes
empty fields and supports lifecycle/readiness/liveness fields.
[`containerPatch`][container-patch] retains the base image/init containers/scheduling
and changes the named container's identity, command, resources/mounts, appending env;
it also supports explicit lifecycle/probe patches. The [Deployment helper][deployment]
supports termination grace and name-driven debug policy. These are inspected
v1.0.20 behaviors, not permission to upgrade other apps or assume every field is supported.

## Actual rendering and merge flow

1. Main imports native/OneHQ/Kyverno shims, the environment's values and PGSync
   renderer, and self-imports as `here` for derived workload patches.
2. Values import versions/S3 (and production HPA settings), self-import as `here`,
   and declare `pgsyncDatabase`, `pgsyncRedis`, `pgsyncElasticsearch` and pipeline
   access settings. Their public module functions expose infrastructure overlays.
3. Host DB settings combine with `pgsync.postgres(...)`: append users, adjust the
   selected instance, add logical replication/WAL parameters and slot handling.
   Redis overlays optional replica/resources/command/storage settings. Elastic
   overlays derive three-node discovery, labels, headless/client Services and PVC
   names from one topology configuration and assert at least three replicas.
4. `pgsync.new(...)` normalizes host runtime inputs, imports **module-local** index
   settings, composes components and feeds generated names into downstream gates,
   rollout settings and rebuild settings. Host integration still reads Redis host/
   port from `here.redis`; the normalized components do not import host values.
5. Host defaults form a large object, then `+ pgsyncValues` replaces same-named
   top-level legacy PGSync settings with the module's effective settings. Some
   production legacy fields refer to `tags.pgsync`, which is absent from the version
   JSON; those overridden/unforced fields do not establish the active image contract.
6. Main constructs host resources and combines the PGSync renderer's object with
   `+`. Jsonnet field visibility determines which declarations manifest. Evaluation
   produces Secrets/placeholders without AVP resolution. Namespace fallback comes
   from spec; selected resources also carry explicit namespaces, including Argo RBAC
   in `argocd-onehq`. Do not force every object into the application's default namespace.

There is no `std.mergePatch` or external-variable stage in the inspected Jsonnet.
Ordinary `+` replaces fields; `+:` preserves nested host fields or appends arrays
through inheritance. PostgreSQL overlays explicitly transform matching instances;
Elastic replaces its runtime env array rather than merging entries by name.
Do not generalize these mechanisms into a universal deep merge.

## Emitted capabilities and environment differences

| Observed output | Staging | Production |
| --- | --- | --- |
| Actual Kubernetes resource count | 82 | 81 |
| Rails-family Deployments | API and GoodJob master | API, debug, GoodJob worker and master |
| Other host workloads | React/search/WebSocket, Redis/Elastic, host maintenance/extraction jobs | React/search/WebSocket, PgHero for both DBs, Redis/Elastic, HPA Git-update CronJobs |
| PGSync producer / consumer | 1 / 2 replicas | 1 / 2 replicas |
| Reindex Job name | `job-pgsync-reindex-readygop-staging` | `pgsync-reindex-readygop-production` |
| Full rebuild scaffolding | Account/Role/binding/CronJob emitted | Same declarations hidden with `::`, not emitted |
| Selective reindex template | Suspended CronJob, `Forbid`, explicit required target placeholder | Same |
| Monitoring/exporter declarations in staging main | Hidden with `::`, not emitted | Not assumed from staging source |

Staging also hides ordinary GoodJob, Rails debug, PgHero and Sidekiq declarations.
Production hides Sidekiq and DB-rebuild declarations. A hidden field can still be
referenced and evaluated internally; it is not equivalent to deleting all its
dependents. Inventory rendered resources rather than counting source declarations.

The only PGSync subtree file differences between targets are resource visibility
in `resources.libsonnet` and the reindex name in `lib/names.libsonnet`. Preserve
both differences; producer/consumer gates follow each environment's actual name.

The module component sets full-rebuild `cronJob.suspend: true`, but its renderer
overrides the emitted staging CronJob to **false**, with schedule `0 4 * * 0` and
`concurrencyPolicy: Forbid`. Rendering does not execute this workflow. Its embedded
commands stop/restart workloads, delete selected Elastic PVCs and recreate Jobs;
those are delivery/maintenance operations, not validation commands. No cross-workflow
lock was verified; `Forbid` is not evidence that distinct/manual operations are serialized.

## Image propagation and accepted differences

Each probe edits one actual environment version file in a temporary clone; all
other fields, hidden-resource visibility and the opposite/default target output
compare equal to baseline.

| Canonical role | Staging consumers | Production consumers | Allowed extra changes |
| --- | --- | --- | --- |
| `rails` | API, GoodJob master, migration Job | API, debug, GoodJob worker/master, migration Job | Migration metadata name, Pod `job` label and container name; two/four `JOB_NAME` completion gates |
| `pgsyncCore` | Producer, consumer, reindex Job, selective CronJob's `run-selective-reindex` init container | Same four locations | None; identities and gates stay fixed |

Rails images derive as `readygop/readygop:<rails>`. Migration names derive as
`db-migrate-<rails>` and require a DNS-compatible tag within Kubernetes name limits;
no digest adapter is implemented. PGSync derives
`docker.io/readygop/pgsync:readygop-<pgsyncHash>-core-<pgsyncCore>`.
The reviewer tests `pgsyncCore` independently of Rails, preserving `pgsyncHash`.
It does not claim every version field or arbitrary override has been tested.

PGSync names are namespace-derived rather than image-derived. Its templates,
reindex and finalize Jobs have sync waves -1/0/1, without an observed Argo hook
annotation in this baseline. Delivery must explicitly handle recreation/reruns of
fixed-name Jobs; the offline image test does not validate that operational process.

## Relationship checks and baseline gaps

Seven staging and nine production Services select their expected workload (the
two Elastic Services both select Elastic). Rails Service selects API only; the
HQAdmin API/migration overlap is absent here. Deployment selectors, Ingress backend
names/ports, HPA targets, namespace-aware Role bindings, app-created Secret key
references and mounts/claim templates pass the scoped checks.

The following baseline gaps remain unchanged:

- GoodJob master has two `IS_GOOD_JOB` env entries in staging and three in production,
  from array-appending inheritance. Values are omitted from evidence. Additional
  unexpected duplicates fail the reviewer; this known exception is recorded explicitly.
- Adding `enabled: false` to the host's `pgsync.new({...})` call leaves output equal:
  the adapter sets `enabled: true` and the public composition does not forward it.
- Overriding only `pgsyncReindex.enabled: false` removes the reindex Job but leaves
  producer/consumer and their gate targets unchanged. This is a negative control,
  not a supported system-wide disable operation. Selective/full-rebuild components
  also have their own construction/visibility choices.
- Baseline `tk fmt --test lib environments` exits 16. No formatting cleanup was made.
  There is no tracked app test suite. Nonexecuting shell syntax checks pass for
  59 staging and 36 production embedded shell instances, plus `extract.sh`.
- The ignored lock makes local reproduction possible but does not make Git-only
  deployments deterministic; moving dependency refs remain in declarations.

Maps have 13 staging and 16 production unresolved identities. These include
Crunchy-generated main/worker DB user Secrets, default/pipeline accounts, storage
classes, Ingress classes, a referenced ClusterRole, the external Argo namespace
and production PgHero TLS Secrets. Their names/references are recorded; live
existence, keys and ownership were not queried. Credential/ConfigMap payloads and
literal env values are excluded from maps/results.

The existing mapper required no ReadyGOP adapter. It records 97/99 nodes and
222/230 relationships with inference, including two claim templates per target.
Kyverno Policy internals and operator children remain generic/unexpanded. It does
not model SQL, complete maintenance command dependencies or observed traffic.
Inferred Job gates only link matching rendered targets; a missing inferred edge
cannot certify a safe partial disable, hence the separate negative control.

## Reusable mechanisms, configurable policy and next slice

**Implemented mechanisms worth reusing:** a public subsystem composition root;
explicit host infrastructure overlays; normalized runtime adapters; centralized
names passed between components; native patches for fields the pinned library
does not forward; actual-render visibility checks; independent canonical image
roles; full-object comparison and namespace-aware relationships. This assessment
adds evidence, not a new application schema or constructor interface.

**Keep application-specific:** namespace/endpoints, image repositories/roles,
worker visibility, module copies/name compatibility, replicas/budgets/placement,
DB replication/backup settings, three-node Elastic/PVC sizing, rebuild schedules,
selective targets, account/RBAC policies, Kyverno admission rules, Git-updating HPA
jobs and external delivery/secret resolution. PGSync requirements are not defaults
for an app without PGSync.

**Proposed next slice:** establish the deployed lock/vendor and delivery process,
then review duplicate env handling and intended rebuild suspend policy as separate
changes with explicit expected output. Add app-owned relationship/visibility tests
before attempting a coordinated PGSync disable API or module deduplication. No
such fixes, restructuring, CODEOWNERS or access changes were made here. Tekton
remains the separate next planned toolkit domain, not validated by these CronJobs.

[st-main]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/main.jsonnet
[prod-main]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-production/main.jsonnet
[st-values]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/staging-values.jsonnet
[prod-values]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-production/production-values.jsonnet
[st-versions]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/staging-version.json
[prod-versions]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-production/production-version.json
[k-import]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/lib/k.libsonnet
[onehq-import]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/lib/k8s-onehq.libsonnet
[kyverno-import]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/lib/kyverno.libsonnet
[dependencies]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/jsonnetfile.json
[ignore]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/.gitignore
[composition]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/pgsync-values.libsonnet
[postgres]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/config/postgres.libsonnet
[redis]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/config/redis.libsonnet
[elastic]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/config/elasticsearch.libsonnet
[config]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/config/pgsync.libsonnet
[names]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/lib/names.libsonnet
[prod-names]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-production/pgsync/lib/names.libsonnet
[resources]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/resources.libsonnet
[prod-resources]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-production/pgsync/resources.libsonnet
[pg-readme]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/README.md
[architecture]: https://github.com/Darthcjba/readygop-infra/blob/dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35/environments/readygop-staging/pgsync/ARCHITECTURE.md
[service-level]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/dbfcec9face86abac6b131c9cc0c7dd2c303d967/core/ServiceLevel.libsonnet
[tolerations]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/dbfcec9face86abac6b131c9cc0c7dd2c303d967/tradetools/Tolerations.libsonnet
[containers]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/dbfcec9face86abac6b131c9cc0c7dd2c303d967/core/Container.libsonnet
[container-patch]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/dbfcec9face86abac6b131c9cc0c7dd2c303d967/tradetools/ContainerPatch.libsonnet
[deployment]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/dbfcec9face86abac6b131c9cc0c7dd2c303d967/apps/Deployment.libsonnet
