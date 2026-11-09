# HQAdmin reference assessment

Status: implemented source inspection and scoped offline compatibility validation
of application commit `79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0`. The installed
toolkit payload was `e93dffdbb7e8c1687c11a45c53a929db01f0a8d9`; the
[assessment procedure](../examples/hqadmin-validation.md),
[executable reviewer](../../scripts/validate-hqadmin.py) and
[sanitized result](../examples/hqadmin-validation.results.json) accompany this record.
The reviewer was added during this assessment; its SHA256 is in the result.

The original checkout was clean and remained unchanged. No application or parent
`AGENTS.md` was found. Toolkit rules, standard and Jsonnet skill/workflow/compatibility
guidance were read explicitly. Installation and probes used disposable local clones;
there was no Cline invocation, dependency upgrade in the source checkout or deployment.
The toolkit owner is Darthcjba; application ownership is not established by these files.

## File responsibilities and entry points

Source links pin the inspected app revision. This layout meets responsibility
boundaries without adopting the first reference application's component directories.

| Responsibility | Existing implementation and source |
| --- | --- |
| Resource composition and rendering | Per-environment [`main.jsonnet`][st-main] and [production counterpart][prod-main], lines 26–242; native constructors plus OneHQ patches, no shared app renderer |
| Defaults, derivation, commands and policy | [`staging-values.jsonnet`][st-values] and [`production-values.jsonnet`][prod-values]; each combines these responsibilities in one object |
| Canonical versions and identity | [`staging-version.json`][st-versions] and [production versions][prod-versions]; fields `name`, `environment`, `backend`, `frontend`, `websocket`, `searchapi` |
| Integration inputs | `*-registry.json` supplies image repository/registry credential placeholder; `host-config.json` supplies hosts; `*-s3.json` supplies backup destination settings beside each target |
| Destination and namespace fallback | [`staging spec.json`][st-spec] and [production spec][prod-spec]; intended namespaces are `iamhq-staging` and `iamhq-production` |
| Library imports | [`lib/k.libsonnet`][native-import] and [`lib/k8-onehq.libsonnet`][onehq-import] select native k8s-libsonnet 1.35 and OneHQ main respectively |
| Dependency declarations | [`jsonnetfile.json`][dependencies]; lock and vendor are [ignored][ignore], so there is no committed resolved dependency authority |
| Metadata and native policy patches | Both main files: `anno` lines 12–24, resource-specific waves, Elastic readiness patch lines 182–199 |
| Delivery registration | [Staging][st-argo] and [production Argo Application][prod-argo] use `tk-avp-plugin`, `TANKA_PATH`, branch `main`, and `CreateNamespace=true` |
| Empty scaffold | [`environments/default/main.jsonnet`][default] evaluates to `{}`; it is not a representative application render |
| Existing validation | No README, AGENTS, test suite, validation script or CI workflow in the tracked baseline; Tanka evaluation and formatting commands are available independently |

## Dependency authority and evidence limit

The application declares OneHQ **v1.0.14**, unlike the first reference app's
v1.0.14_3. No vendor directory or ignored lock existed in the original checkout.
`jb install` ran only in the isolated clone. Its freshly resolved
[lock](../examples/hqadmin-dependencies.lock.json) records:

| Dependency | Resolved revision for this assessment |
| --- | --- |
| OneHQ/tanka-lib-k8-onehq, requested v1.0.14 | `c34a0d696426e3a178fdb8587625f3100f8d46c2` |
| grafana/jsonnet-libs, ksonnet-util, requested master | `1abcc571e0882164a917e848ae2d9426188bf016` |
| jsonnet-libs/docsonnet, doc-util, requested master | `bf6f08ae02a51c48bdcec4629b1c1a5a62c6f803` |
| jsonnet-libs/k8s-libsonnet, 1.35, requested main | `f66023fcddc92e89c3e81bd49c1f528a984505ef` |

These revisions reproduce the assessed render, **not a recovered production
baseline**. Moving branch refs and an ignored lock prevent establishing which
native library revision the delivery system currently uses. Production comparison
requires its actual lock/vendor provenance or an approved sanitized output baseline.

Resolved OneHQ source retains `serviceLevel: 'Basic'`/`'Premium'` plus a `resources`
map; `fetchServiceLevel(name, resource, serviceLevel)` and
`getTolerations(name, resource, serviceLevel)` take three arguments, while
`getAffinity(name, values)` reads both fields. Do not copy the bundled snapshot's
object-shaped scheduling interface into this app.

Relevant resolved sources at this assessment's OneHQ revision:
[Deployment][deploy-helper], [Container][container-helper],
[containerPatch][patch-helper], [Job][job-helper], [environment variables][env-helper].
Container generation concatenates `image + tag`. `containerPatch` inherits the
base Pod, then changes its resource identity, labels and named container's
name/command/resources/mounts, appending environment entries. It does not rebuild
scheduling under the new worker name and does not take an image override field.

## Actual render and merge flow

1. Tanka selects the environment's `main.jsonnet` and resolves the two import shims.
   Main imports its corresponding values file and self-imports as `here`.
2. Values import versions, registry, hosts and S3 inputs, and self-import as `here`.
   `ns` derives from version `name + '-' + environment`. Defaults and target
   choices coexist; there is no common base/overlay function or `std.mergePatch` stage.
3. Main constructs the backend Deployment with `createDeploy`. GoodJob is a
   `containerPatch` of `here.backendDeploy`; master is a second patch of
   `here.goodjobDeploy`. Debug constructs another Deployment using backend settings.
4. The migration Job independently reads `tags.backend`; its name, Pod `job` label
   and container name include the tag. API, debug and both workers inherit an init
   gate whose `JOB_NAME` follows that migration identity.
5. Permission Job, GoodJob PostgresCluster, credentials, RBAC, Elastic, search,
   WebSocket, frontend, Services, Ingresses and API/frontend HPAs are always emitted.
6. `tk eval` manifests the resource object without a cluster connection or AVP
   lookup. Main does not add namespace metadata to all resources; Tanka spec and
   Argo destination supply the environment namespace. The mapper uses spec fallback.
   Argo's separately configured plugin resolves Vault placeholders during delivery;
   the plugin implementation and its full runtime inputs are outside this repository.

Self-imports and Jsonnet's lazy fields express references. Object `+` replaces
fields at the right-hand side; explicitly additive fields such as `env+` append
arrays rather than merge entries by name. Master settings derive from GoodJob
cont plus `ENABLE_CRON`; the second container patch appends that env to its inherited
container. There is no general environment override, capability toggle or
preparation API. Deleting fields or adding `enabled: false` is not a supported
disable operation. Values include GoodJob HPA settings, but main emits only the
backend and frontend HPAs.

## Shared backend image and identities

Changing only `staging-version.json.backend` from the baseline tag to the synthetic
`toolkit-validation` changes exactly these resources/fields:

| Consumer | Expected, independently compared effect |
| --- | --- |
| API `backendDeploy` | Main container image and migration gate `JOB_NAME` |
| Debug `backendDebugDeploy` | Main container image and migration gate `JOB_NAME` |
| GoodJob `goodjobDeploy` | Inherited main image and migration gate `JOB_NAME` |
| GoodJob master `goodjobMasterDeploy` | Inherited main image and migration gate `JOB_NAME` |
| `migrateDBJob` | Main image; Job metadata name, Pod `job` label and container name include the new tag |

All remaining fields compare equal, including Secret data, scheduling, replicas,
selectors, other images and policy. Resource count stays 37. Production and the
empty default target compare equal to their baselines. The separate permission Job
keeps `postgres:17`; there are no E2E seed, runner or Sidekiq resources here.

A component-only control replacing just the API container's `tags.backend` use
changes all four Deployment images through inheritance, **but leaves migration
image/name and the gates on the canonical tag**. This differs from the first app's
GoodJob propagation. Both layouts require tracing their real graph.

Tags become Kubernetes Job and container names directly. This path requires a
DNS-compatible tag within those name length limits; arbitrary OCI tags/digests do
not automatically satisfy that contract. There is no digest adapter or image-hash
Job naming mechanism here. Names of all unrelated resources remain stable.

## Metadata, policy and relationships

- `anno` omits empty/null optional arguments and preserves numeric wave zero.
  Its additive annotations follow normal Jsonnet composition; a later explicit
  same-key annotation would win. Resource metadata is separate from Pod metadata.
- Waves include -5 for permissions scaffolding/backend account/S3 config, -4 for
  GoodJob DB, -3 for permissions Job/backend Secrets, -2 for migration/Elastic/pull
  Secret, and -1 for API/workers. Other resources can use default wave zero.
  Waves do not establish successful Job reruns, stop existing consumers or lock DB work.
- At this baseline API, debug and workers render one replica in both environments;
  production API HPA permits 3–15, frontend HPA 3–6. Staging HPAs are 1–1.
  Production frontend renders three replicas. Argo ignores selected replica fields,
  as declared in its application YAML. Preserve this existing policy during image work.
- Worker/master inherit API init containers, account, image pull reference and
  scheduling. Their patched resource budgets/commands are distinct. Debug changes
  the Pod component label and forces one replica through the resolved helper.
- Only Elastic receives the app's native readiness probe patch. The resolved
  general container constructor does not forward arbitrary probe fields; its port
  field is `ports`, while Elastic's values contain singular `port`, which is not
  emitted as container ports. Jobs render no explicit backoff/deadline/TTL settings.
- Four Services select only their expected workload. The **backend Service also
  matches migration Pod labels**, since the Job shares all labels in that selector.
  This is an observed baseline overlap, not a new behavior or a statement about live
  endpoints. The assessment records it explicitly; remediation needs a separate change.
- Deployment selectors match their Pod labels. Ingress Service names/ports, HPA
  targets, binding Roles, app-created Secret key references and non-StatefulSet
  mount/volume relationships pass the scoped checks. External reference existence
  and StatefulSet-generated PVC instances are outside these assertions.

## External and operator-owned dependencies

Main's Namespace declaration is commented; Argo requests namespace creation.
GoodJob credential names derive from the declared PostgresCluster/user and are
expected operator children, not app-created Secrets. Main database superuser
credentials are external to this render. Registry, backend, DB-settings, Elastic,
search and S3 Secret resources are app-created; their payloads are omitted here.

Each map has 15 unresolved identities: namespace, Redis ConfigMap, external main-DB
Secret, ECR pull Secret, two GoodJob operator credential Secrets, four TLS Secrets,
pipeline `build-bot` account in another namespace, default account, Elastic account,
IngressClass and storage class. Classification is not proof of live existence.
The Redis ConfigMap and Elastic account have references but no declaration or
proven owner in this checkout. Redis itself is not rendered. Operator children,
external DB/Redis/backup endpoints and the full Crunchy CRD internals are not
expanded by the map.

## Reuse, configuration and next slice

**Reusable implemented mechanisms:** responsibility mapping for combined files;
pinned implementation precedence; inherited worker construction; shared-role image
tracing with full-object comparisons; exact gate/name propagation; annotation
helper; native patches for unsupported fields; existing generic map with both
declared and explicitly inferred relationships. No core toolkit schema/constructor
change was needed for this second layout.

**Keep configurable:** per-environment versions/hosts/registry/S3 settings, namespace
identity, scheduling/resource budgets, worker/master commands, debug workload,
external main DB/Redis ownership, Postgres backup policy, waves, migration naming,
account/pull credential choices and Argo delivery. Do not impose the first app's E2E
storage, shutdown hooks, execution IDs, worker choices or directory structure.

**Proposed, not implemented:** a follow-up should establish the delivery system's
actual dependency baseline and external resource ownership, then review the
API/migration Service-label overlap as its own output-changing change. If accepted,
add app-owned baseline/relationship checks without reorganizing the app. No lock,
selector, policy, Secret or housekeeping fix was applied to the source repository.
The broader project can next define the separate Tekton procedure using a real
Pipeline/Task; this assessment is not pipeline or second-app Cline evidence.

[st-main]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-staging/main.jsonnet
[prod-main]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-production/main.jsonnet
[st-values]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-staging/staging-values.jsonnet
[prod-values]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-production/production-values.jsonnet
[st-versions]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-staging/staging-version.json
[prod-versions]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-production/production-version.json
[st-spec]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-staging/spec.json
[prod-spec]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/hqadmin-production/spec.json
[native-import]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/lib/k.libsonnet
[onehq-import]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/lib/k8-onehq.libsonnet
[dependencies]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/jsonnetfile.json
[ignore]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/.gitignore
[default]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/environments/default/main.jsonnet
[st-argo]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/hqadmin-staging-argocdapp.yaml
[prod-argo]: https://github.com/OneHQ/hqadmin-infra/blob/79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0/hqadmin-production-argocdapp.yaml
[deploy-helper]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/c34a0d696426e3a178fdb8587625f3100f8d46c2/apps/Deployment.libsonnet
[container-helper]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/c34a0d696426e3a178fdb8587625f3100f8d46c2/core/Container.libsonnet
[patch-helper]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/c34a0d696426e3a178fdb8587625f3100f8d46c2/tradetools/ContainerPatch.libsonnet
[job-helper]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/c34a0d696426e3a178fdb8587625f3100f8d46c2/batch/Job.libsonnet
[env-helper]: https://github.com/OneHQ/tanka-lib-k8-onehq/blob/c34a0d696426e3a178fdb8587625f3100f8d46c2/tradetools/EnvironmentVariables.libsonnet
