# Kubernetes component and dependency map

`scripts/map-kubernetes.py` reads rendered resources and generates an offline, interactive resource map. It works from the rendered output, so application directory layouts and constructor revisions can differ. It does not query a cluster, apply resources or install toolkit files.

## Generate a reference map

From the **toolkit checkout**, with the reference application beside it and its locked dependencies already available:

```sh
python3 -B scripts/map-kubernetes.py \
  --app ../agencieshq-e2e-infra \
  --environment environments/e2e-check \
  --infer-env-links \
  --output generated/kubernetes/e2e-check
```

For the PR example, use `--environment examples/prs/pr-xxx` and a different output directory. For another application, supply its actual root and Tanka environment/entry point. The tool uses `tk eval`, retaining raw output only in memory; rendering failures withhold raw output because it may include credentials. Use `--ext-str KEY=value` for required external variables; those values are not saved in map metadata. Tanka rendering requires the app's existing tools/dependencies. The mapper itself uses only Python 3.9+ standard-library modules.

At the inspected reference revision `4a494240abc9783c6faf47db6f0f8f05e441dd40`, both service and PR maps contain 36 rendered resources, two claim-template nodes and 10 unresolved references. With environment inference enabled, each has 155 relationships: 70 declared references, eight selector matches, three default-account links, 39 inferred links and 35 namespace-membership edges. Membership edges start hidden for readability. Search, filters, resource/edge inspection, neighborhood focus and zoom were checked in a headless browser.

The output directory must be outside the application checkout. `generated/` is ignored in this toolkit. Scripts and the HTML template are toolkit-owned and are not installed into consumers by the toolkit installer; run the command from the toolkit checkout even when reading an installed copy of this document.

For already-rendered **JSON**, no Tanka or particular layout is required:

```sh
python3 -B scripts/map-kubernetes.py \
  --input /path/to/rendered.json \
  --namespace staging \
  --output generated/kubernetes/imported
```

Accepted shapes are a single named Kubernetes object, a List/typed List, an array, or a nested Tanka resource map. `--input -` reads JSON from stdin. YAML parsing is not included. Duplicate identities and resources with only generated names are rejected rather than silently merged. Explicit resource namespaces win; otherwise `--namespace`, the selected Tanka environment's `spec.namespace`, or `default` supplies the fallback. Known cluster-scoped kinds and supplied cluster-scoped CRD definitions retain cluster scope. For unknown CRDs without their definition or a namespace, verify the scope assumption.

## Files and controls

| File | Purpose |
| --- | --- |
| `index.html` | Self-contained diagram; open locally, with no server, JavaScript package or CDN dependency |
| `graph.json` | Resource inventory, allowlisted attributes, typed relationships, evidence locations and coverage notes |
| `graph.mmd` | Mermaid `flowchart LR` export; namespace-membership edges are omitted for readability |

The diagram supports search by resource/kind/image, namespace/kind filters, zoom, neighborhood focus and toggles for unresolved references, inferred links and namespace membership. Select a resource to inspect attributes and direct connections, or an arrow to inspect evidence locations. Edges point from the referencing object to its dependency; selector and containment edges are labeled for their distinct meaning. They do not all represent traffic.

Resource details include identity, selected Argo wave/hook metadata, images, replicas, ports, resource requests/limits, probe types, environment variable **names**, mounts, storage, Secret/ConfigMap key names and RBAC rules as applicable. Arbitrary spec fields, annotations/status, Secret/ConfigMap payloads, literal environment values and commands/args are omitted. Input labels are used for selector matching without copying arbitrary label values into the output. Generated maps still expose infrastructure names, images and topology, so use the application's existing sharing rules.

## Relationship coverage and evidence

| Relationship | Extraction/evidence |
| --- | --- |
| Ingress → Service/resource, TLS Secret and IngressClass | Declared backend/class/TLS references |
| Service → Pod/workload template | Same-namespace label-selector match; a missing/empty Service selector creates no workload edge |
| Workload → ServiceAccount | Declared reference, or explicitly marked Kubernetes default-account behavior |
| Workload → Secret/ConfigMap/PVC | Environment references, envFrom, image-pull credentials, ordinary/projected volumes |
| RoleBinding/ClusterRoleBinding → role/account | Declared roleRef and ServiceAccount subjects; other subject types are counted but not expanded into named identity nodes |
| HPA → target; PDB/NetworkPolicy → selected workloads | Declared target or selector match; NetworkPolicy rule/peer traffic evaluation is not implemented |
| StatefulSet → Service and claim templates | Declared governing Service and separate template nodes; generated per-replica PVCs are not invented |
| PVC/PV/template → storage/claim | Declared StorageClass, bound volume or claim references |
| EndpointSlice → Service/target | Service-name association and declared endpoint targetRef |
| Child → owner; Namespace → members | Declared ownership and separate membership edges |
| Crunchy PostgresCluster → StorageClass | Schema-specific instance storage references; details include PostgreSQL version, instance sizing/storage and database names |
| Optional environment heuristics | Matched rendered Service DNS/Ingress hosts and init-container `JOB_NAME`/`NS` conventions; always marked inferred |

Relationship evidence is one of `reference`, `selector`, `default`, `inferred` or `membership`. Repeated references between the same objects/relation are grouped with their evidence locations. A node absent from the input is marked **unresolved**, not missing or broken. In the reference app, this includes operator-generated database credentials, certificate Secrets, cluster-provided classes and the default account.

`--infer-env-links` is opt-in. It compares literal URL hostnames to already-rendered Services/Ingresses and init Job names to already-rendered Jobs. It never exports URL values/userinfo/paths/queries or arbitrary external endpoints. A heuristic does not prove that a program makes that call or waits for that Job. Compiled frontend configuration and connections hidden in scripts, images or Secret/ConfigMap values remain unknown. Omit the flag for only references, selector matches, defaults and membership.

Sync waves are displayed as attributes, not converted into dependency edges. Operator-generated children are not expanded automatically. Unknown CRDs retain identity/owner coverage with an explicit coverage note. Add rendered operator children or a reviewed schema-specific extractor to map more of those relationships. This is a map of supported **declarations and heuristics**, not a complete runtime graph, health check or traffic/policy analysis.

Selector/default handling follows the Kubernetes documentation for [label selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/), [Services without selectors](https://kubernetes.io/docs/concepts/services-networking/service/#services-without-selectors) and [default ServiceAccounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/). PDB handling distinguishes `policy/v1` empty selectors from legacy `policy/v1beta1` semantics; see [the documented PDB selector behavior](https://v1-36.docs.kubernetes.io/docs/tasks/run-application/configure-pdb/).

## Validation

Run toolkit checks:

```sh
python3 -B scripts/check.py
python3 -B -m unittest discover -s tests -v
git diff --check
```

Graph tests cover namespace isolation, input forms, default/explicit account and role references, projected volumes, CronJob nesting, claim templates, selector semantics, duplicate identities, opt-in inference, payload omission and safe HTML embedding. The reference service/PR maps exercise the real rendered manifests; inspect browser controls separately from Python graph tests. A passing toolkit suite does not establish live cluster readiness or exhaustive custom-resource coverage.
