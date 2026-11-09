# Reference application: agencieshq-e2e-infra

Status: observed application behavior from Step 1, used to define the Step 2 standard. This is a reference mapping, not a required layout or a production-readiness certification. Other applications may map the same responsibilities to different files and schemas.

Application revision: `4a494240abc9783c6faf47db6f0f8f05e441dd40`. Toolkit revision during inspection: `d96bdca70e3daad457fc7f5d0239083fa37af009`. Toolkit owner and sole maintainer: `Darthcjba`. Source links below pin the inspected application revision. Recheck them when the app changes.

No application `AGENTS.md` was found during inspection. Toolkit guidance was read explicitly; Cline-specific discovery was not assumed. No application files or deployment state were changed. See the [general contract](../app-infrastructure.md) and [shared image worked example](../examples/shared-backend-image.md).

## Responsibility map

| Responsibility | Actual application paths and source |
| --- | --- |
| Persistent entry point | [`environments/e2e-check/main.jsonnet`][main] calls the shared renderer with [`values.jsonnet`][env-values] |
| Target inputs | `config.json`, `images.json`, `overrides.jsonnet`, `execution.json` beside the entry point; [`spec.json`][spec] supplies the Tanka destination |
| PR layout | [`examples/prs/pr-xxx/`][example] is renderable outside Argo discovery; generated targets belong under `environments/prs/pr-*` |
| Identity/endpoints | [`lib/e2e/target.libsonnet`][target] merges identity defaults and derives public/internal endpoints |
| Image adaptation | [`lib/e2e/images.libsonnet`][images] resolves five roles into OneHQ's `image + tag` shape |
| Defaults and composition | [`lib/e2e/values.libsonnet`][values] combines component modules under `lib/e2e/values/` and applies staged overrides |
| API and workers | [`values/backend.libsonnet`][backend], [`values/backend-common.libsonnet`][backend-common] and [`values/sidekiq.libsonnet`][sidekiq] supply component settings |
| Jobs and execution | [`values/jobs.libsonnet`][jobs], [`values/runner.libsonnet`][runner] and [`run.libsonnet`][run] derive prepare/seed/test settings and dependencies |
| Resource construction | [`render.libsonnet`][render], [`render-job.libsonnet`][render-job] and [`statefulset.libsonnet`][statefulset] compose constructors and native patches |
| Cross-cutting policy | [`annotations.libsonnet`][annotations], [`order.libsonnet`][order], `resources.libsonnet` and `probes.libsonnet` |
| Credentials | [`secrets.libsonnet`][secrets] declares Secret shapes/Vault paths and key mappings; payload values are intentionally omitted here |
| Local tooling | [`scripts/render-run.py`][render-run] renders a Kubernetes List; `create-pr.py` creates/updates target files; `mock-render.py` generates redacted walkthrough artifacts |
| Delivery | [`scripts/run-pipeline.py`][pipeline] verifies image pins, coordinates a Lease, publishes Git changes and requests/waits for Argo hooks; `argocd/` holds registration templates |
| Validation | [`scripts/validate.sh`][validate] runs formatting, Python contracts and embedded-script syntax checks; [`tests/test_render.py`][tests] checks baseline resources and relationships |

## Dependency authority

[`jsonnetfile.json`][dependencies] requests OneHQ `v1.0.14_3`; the [lock][lock] pins the revisions below. `lib/k.libsonnet` imports `github.com/jsonnet-libs/k8s-libsonnet/1.35/main.libsonnet`, while `lib/k8-onehq.libsonnet` imports `github.com/OneHQ/tanka-lib-k8-onehq/main.libsonnet`.

| Dependency | Locked revision |
| --- | --- |
| OneHQ/tanka-lib-k8-onehq | `10a46abb03c8a82ecc9479b036a74d5b79b00f4f` |
| grafana/jsonnet-libs, ksonnet-util | `9a2e846669f8512b32cdb6c80104e0586744aff9` |
| jsonnet-libs/docsonnet, doc-util | `bf6f08ae02a51c48bdcec4629b1c1a5a62c6f803` |
| jsonnet-libs/k8s-libsonnet, 1.35 | `18e7a26f0699cb8b006494f40b93ddd06d33b299` |

The app uses a `resources` scheduling map with `serviceLevel: 'Basic'`. Its pinned `fetchServiceLevel` and `getTolerations` helpers accept `(name, resources, serviceLevel)`; `getAffinity(name, values)` reads those settings from `values`. The skill's bundled snapshot `cb49c83a43cb04e05da5e820c6fe56faed32bf73` uses a different interface with `mode` and `definitions`; that shape must not replace the app's working inputs silently.

## Implemented rendering and merge flow

1. Environment `values.jsonnet` passes its four inputs to the shared values function. `target.libsonnet` merges identity defaults; `images.libsonnet` validates and adapts image roles.
2. Shared PVC overrides resolve before components derive volume references.
3. Component objects combine with `+`, then `std.mergePatch(base, overrides)` produces application settings. GoodJob is already part of this base.
4. Sidekiq derives from the effective backend; its own override then applies.
5. Preparation derives from the backend; its override resolves before seed derives its preparation gate. Seed overrides resolve before the runner derives its seed gate.
6. An execution ID adds a shutdown hook and additional Role rules. Hidden fields carry config/images/versions/overrides for explicit-run rendering.
7. `render.libsonnet` emits native constructors plus OneHQ patches, resource annotations and native additions.

`std.mergePatch` recursively merges objects, replaces arrays and deletes fields with `null`. The environment's commented [`withEnv` example][overrides] preserves default environment entries while replacing matching names. Later overrides do not universally recompute earlier derivations. PR targets have their own inputs and do not import service overrides; image snapshots also remain independent after target creation.

The default main output has 36 resources: six Deployments, two StatefulSets, one PostgresCluster, three Jobs, eight Services, four Ingresses, four Secrets, three ServiceAccounts, one Role, one RoleBinding, one Namespace, one ConfigMap and one standalone PVC. A pipeline execution ID adds the shutdown Job, producing 37. These counts describe this revision, not a requirement for other apps.

## Supported paths and limitations

| Operation | Observed behavior |
| --- | --- |
| Change canonical `images.json.backend` | API, GoodJob, Sidekiq, prepare, seed and the seed's backend-readiness init container receive the image |
| Override only backend container image | API, Sidekiq and Jobs follow; GoodJob retains the original image |
| Override shared PVC name | Persistent API/worker volume references follow; prepare/seed keep private `emptyDir` tmp |
| Override preparation name | Seed completion gate follows it |
| Override backend Vault path | Renderer uses it without replacing the Secret data |
| Override backend Secret name | Existing consumer references can retain the original name |
| Add a backend Secret key through environment overrides | Secret gains the key, but derived backend environment references do not gain it automatically |
| Rename registry Secret or Job ServiceAccount | Independently declared references can remain stale, including workload/account binding relationships |
| Set `sidekiq.enabled: false` | Field is ignored; Sidekiq still renders |
| Delete Sidekiq using `null` | Rendering fails on the missing component |
| Include `debug` in resource prefix | Pinned Deployment helper changes labels/replicas; application Services lose their intended matches |

The app has no general capability resolver or `prepareComponents`/`validatePrepared` API. It emits no HPA, PDB or NetworkPolicy. A namespace isolation label alone does not declare a NetworkPolicy. Existing-account reuse is not a documented general interface. Known gaps above must not be advertised as supported shared changes.

Most application identities derive from `resourcePrefix`; endpoints derive from `hostPrefix`, `domain` and optional host overrides. Namespace-scoped constants remain for the database, some credentials/RBAC and the shared tmp claim. The Crunchy operator supplies `main-db-pguser-main-db-e2e-user` and `main-db-pguser-postgres`; those Secrets are not directly emitted by this renderer.

Backend environment references derive from the original Secret declaration's keys and exclude keys supplied literally. The pinned library uses same-name keys for Secret names beginning with `secrets-` and supports aliases for other Secret names. ConfigMap mappings use same-name keys. The runner follows only the backend's factory-key configuration rather than the entire backend environment. No secret values are included in this record.

## Metadata, workload and execution policy

`anno(vaultPath=null, syncOrder=null)` omits blank inputs, retains numeric zero as `"0"` and patches resource metadata. Explicit annotations applied afterward win; Pod-template annotations are a separate concern. Waves belong to `order.libsonnet`: namespace `-10`, credentials/RBAC `-6`, dependencies `-4/-3`, prepare `-2`, API/workers/shared tmp `-1`, frontend `0`, search `1`, websocket `2`, seed `3`, runner `4`. Pipeline shutdown is at `-3`.

API replicas default to one with one Puma process to protect a process-local factory mutex. GoodJob and Sidekiq have distinct commands/resources; Sidekiq readiness checks its local worker's Redis heartbeat. Prepare/seed reuse the backend image/env/mounts with private tmp and without Deployment probes. StatefulSet patches add fields unsupported by the library, including security settings and startup probes. Frontend ingress preserves a `/gql` route to the backend; React endpoints require build-time configuration.

Default preparation/seed names hash the effective backend image. The runner name also depends on seed identity, runner image and frontend image. Names do not fingerprint every script/config change. Explicit-run entry points use `RUN_ID`, add labels and a 24-hour TTL. Pipeline execution IDs instead produce four Sync hooks: stop consumers, prepare, seed and runner; application rollout falls between prepare and seed. Sync waves alone neither stop existing database consumers nor provide a lock.

The app's README execution-contract paragraph says coordination/scaling is absent, but the inspected coordinator and shutdown hook implement it. Source takes precedence for this discrepancy; this toolkit change does not edit that application documentation or execute delivery.

## Commands and required inputs

Run from the application root. Prerequisites are Tanka, locked dependencies, Python 3.10+ for tooling and Ruby for script checks. A fresh checkout uses `jb install` with private OneHQ library access.

```sh
tk show environments/e2e-check
tk show examples/prs/pr-xxx
tk eval environments/e2e-check/build-profile.jsonnet
tk eval examples/prs/pr-xxx/build-profile.jsonnet
tk eval environments/e2e-check/prepare.jsonnet --ext-str RUN_ID=reference-check
tk eval environments/e2e-check/test.jsonnet --ext-str RUN_ID=reference-check
python3 scripts/render-run.py environments/e2e-check prepare reference-check
python3 scripts/render-run.py environments/e2e-check test reference-check
sh scripts/validate.sh
```

Main and build-profile rendering require no external variables. Explicit runs require a 1–20-character DNS-label `RUN_ID`; test rendering also rejects an unresolved runner-image placeholder. The checked-in PR example permits image placeholders for main inspection. Headless capture of `tk show` requires `--dangerous-allow-redirect`; raw output can contain Secret payloads and must not be published.

Runtime prerequisites include the Crunchy operator/generated credentials, appropriate storage classes, ingress/certificate services, configured Vault/plugin delivery and built images containing the expected commands. Rendering does not verify those resources or image contents. The coordinator additionally requires Git/registry/Kubernetes access; it is not a validation command.

## Evidence and next scope

Step 1 ran service/PR renders, build profiles, service explicit runs, tag/digest image-propagation probes, reference/selector checks, formatting, embedded shell/Ruby syntax, toolkit structure checks and Git whitespace checks. Tools included Tanka 0.36.3 and jsonnet-bundler 0.6.0. Checks used locally resolved dependencies; no cluster/registry verification or Cline pilot occurred.

The complete application suite and walkthrough generator were inspected but not run in that analysis-only task because they create temporary/generated files. The suite contains relationship, isolation, storage, annotation, image, worker/Job lifecycle and mocked coordinator checks. Passing the probes does not imply the full suite passed. Read-only probes reproduced the limitations listed above. Step 4 subsequently runs the full suite in a disposable local clone; its result is recorded separately in the [worked-example report](../examples/shared-backend-image.results.json).

Reusable mechanisms: thin entry points, pinned shims, image adaptation, staged Job dependencies, native construction plus OneHQ patches, optional annotation helpers and rendered relationship tests. Keep E2E database layout, test partitioning, concurrency constraints, commands, endpoints, waves, storage/budgets and delivery coordination configurable in their application context. Assess another app before treating this layout or its capabilities as broadly representative.

[main]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/environments/e2e-check/main.jsonnet
[env-values]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/environments/e2e-check/values.jsonnet
[spec]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/environments/e2e-check/spec.json
[example]: https://github.com/OneHQ/agencieshq-e2e-infra/tree/4a494240abc9783c6faf47db6f0f8f05e441dd40/examples/prs/pr-xxx
[target]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/target.libsonnet
[images]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/images.libsonnet
[values]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values.libsonnet
[backend]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values/backend.libsonnet
[backend-common]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values/backend-common.libsonnet
[sidekiq]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values/sidekiq.libsonnet
[jobs]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values/jobs.libsonnet
[runner]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/values/runner.libsonnet
[run]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/run.libsonnet
[render]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/render.libsonnet
[render-job]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/render-job.libsonnet
[statefulset]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/statefulset.libsonnet
[annotations]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/annotations.libsonnet
[order]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/order.libsonnet
[secrets]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/lib/e2e/secrets.libsonnet
[render-run]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/scripts/render-run.py
[pipeline]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/scripts/run-pipeline.py
[validate]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/scripts/validate.sh
[tests]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/tests/test_render.py
[dependencies]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/jsonnetfile.json
[lock]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/jsonnetfile.lock.json
[overrides]: https://github.com/OneHQ/agencieshq-e2e-infra/blob/4a494240abc9783c6faf47db6f0f8f05e441dd40/environments/e2e-check/overrides.jsonnet
