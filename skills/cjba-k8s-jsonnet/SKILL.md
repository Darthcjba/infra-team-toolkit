---
name: cjba-k8s-jsonnet
description: 'Create, review, refactor, and explain Kubernetes infrastructure written with Grafana Tanka/Jsonnet using OneHQ/tanka-lib-k8-onehq, FURTHER DEV: FOLLOW STANDARD FOR INFRA AS CODE REPO'
---





# Lima Kubernetes Jsonnet

Use the OneHQ `tanka-lib-k8-onehq` abstractions accurately and conservatively. Prefer the library's existing helpers when they model the requested behavior; use native `k.libsonnet` constructors and Jsonnet patches for fields the OneHQ helper does not support.

## Source authority

Use sources in this order:

1. Current source supplied by the user in the conversation, or the live OneHQ GitHub repository when a GitHub connector is connected and a freshness check is useful.
2. `references/library-source.md`, which is the bundled source snapshot used to build this skill.
3. `references/api-reference.md` and `references/patterns.md`, which summarize the bundled snapshot.
4. `references/constructor-guide-reference.txt` only as a secondary reference.

Never let the constructor guide override actual library source. The supplied guide was written against a different revision and contains some stale signatures, especially around service-level scheduling.

When live GitHub access is available, consult `https://github.com/OneHQ/tanka-lib-k8-onehq.git` when the user asks for the latest/current behavior, when an existing project pins a different revision, or when source behavior appears inconsistent with the bundled snapshot. Do not require GitHub for ordinary use. If live source is unavailable, work from the bundled snapshot and say so only when the version distinction matters.

## Decide the task mode

### Create

Use this path when the user describes desired Kubernetes resources or behavior.

1. Identify every Kubernetes resource required and the relationships among them.
2. Check `references/api-reference.md` for a matching OneHQ helper.
3. Start native resources with `k.<api>.<version>.<kind>.new(...)` when a typed constructor exists.
4. Add the OneHQ helper patch, usually with `+ kone.<helper>(...)`.
5. Add namespace, annotations, labels, sync-wave, AVP/Vault metadata, and unsupported native fields as renderer-level patches.
6. Use `k` directly for resource kinds with no OneHQ helper. Use a plain object for CRDs without a typed constructor.
7. Keep values reusable when the caller is using a values file; do not move environment-specific values into constructors without a reason.
8. Check helper-specific required fields before returning code.
9. Return Jsonnet plus a short explanation of the helpers and native patches used.
10. Render Kubernetes YAML only when the user explicitly asks or validation is possible against an available Tanka environment.

### Review or modify

Use this path when the user provides existing Jsonnet/Tanka code.

1. Preserve the existing architecture and naming unless the user asks for redesign.
2. Compare helper calls against `references/api-reference.md` and, when needed, the exact implementation in `references/library-source.md`.
3. Identify the smallest concrete problem before proposing changes.
4. Do not replace library helpers with raw Kubernetes objects merely because raw YAML would be easier.
5. Do not invent helper parameters. If a field is unsupported, patch the generated native resource at the correct Kubernetes path.
6. Return complete replacement snippets when the user asks for code, not pseudo-code.
7. Explain any behavioral consequence that is non-obvious, such as selector changes, array-returning helpers, or scheduling behavior.

## Core composition rule

Most OneHQ resource helpers are patches, not complete resources. Compose them with the native constructor:

```jsonnet
local k = import 'k.libsonnet';
local kone = import 'k8-onehq.libsonnet';

k.apps.v1.deployment.new('example-app')
+ kone.createDeploy(values.app, 'example-app')
+ { metadata+: { namespace: values.namespace } }
```

Exceptions include helpers that return complete resources or arrays. Verify the return shape before composing:

- `kone.generateSecrets(...)` returns an array of Secret resources.
- `kone.generateServices(...)` returns an array of Service resources.
- `kone.crunchydb(...)` returns a complete `PostgresCluster` custom resource.
- Supporting helpers such as `setenv`, `setvol`, `setvolM`, `ContainerInception`, `getAffinity`, and `getTolerations` return fragments or arrays, not top-level resources.

## Prefer native patches over fake library features

When a helper does not expose a Kubernetes field, add a native patch instead of pretending the helper accepts it.

Typical examples:

```jsonnet
k.batch.v1.job.new('migrate')
+ kone.generateJob(values.migrate, 'migrate')
+ {
  spec+: {
    backoffLimit: 0,
    activeDeadlineSeconds: 1800,
  },
}
```

Use this pattern for unsupported fields such as Job retry/deadline settings, CronJob history/concurrency settings, container `startupProbe`, `args`, `imagePullPolicy`, `securityContext`, multiple named ports, advanced volume sources, Service type/clusterIP settings, and additional Ingress paths.

## Containers

Pass workload containers as objects, not arrays:

```jsonnet
cont: {
  backend: {
    name: 'backend',
    image: 'onehq/backend:',
    tag: 'sha-123',
    command: ['bundle', 'exec', 'puma'],
    env: { secretRefs: [], configMaps: [], keyvalue: [] },
    resources: {},
    volumeMounts: [],
  },
},
```

The object key is only the Jsonnet container collection key. `config.name` becomes the rendered Kubernetes container name. The image is produced by concatenating `config.image + config.tag`, so include `:` or `@` in `image` as appropriate.

Do not add `kone.generateContainers(...)` again to Deployment, StatefulSet, Job, or CronJob helpers; they already invoke it.

## Scheduling

Use the bundled source's current scheduling shape, not the older constructor-guide signature.

A `serviceLevel` object contains at least:

```jsonnet
serviceLevel: {
  organization: 'onehq',
  mode: 'Basic',
  definitions: {
    backend: {
      Basic: 'spot',
      Standard: 'ondemand',
      matchExpressions: [],
      tolerations: [],
    },
  },
},
```

`fetchServiceLevel(name, serviceLevel)` and `getTolerations(name, serviceLevel)` select a definition whose key occurs in the resource name. `getAffinity(name, values)` reads `values.serviceLevel`. Keep names and definition keys aligned or scheduling can render with empty match expressions/tolerations.

Do not use the stale pattern `resources: scheduling` to drive affinity for this bundled revision.

## Environment variables and secrets

Use `kone.setenv` inputs in this shape:

```jsonnet
env: {
  secretRefs: [
    ['main-db-pguser-app', { PGUSER: 'user', PGPASSWORD: 'password' }],
  ],
  configMaps: [
    ['app-config', { RAILS_ENV: 'RAILS_ENV' }],
  ],
  keyvalue: [
    ['LOG_LEVEL', 'info'],
  ],
},
```

For secret names beginning with `secrets-`, the implementation ignores the mapped secret-key value and uses the environment variable name as the Secret key. ConfigMap mappings also use the environment variable name as the ConfigMap key. Do not rely on aliases there.

`generateSecrets` expects `data` values already encoded as Kubernetes Secret `data`, normally base64. Do not describe base64 as encryption.

## Volumes

Use OneHQ volume settings only for supported sources: `claimName`, `emptyDir`, `secret`, or `configMap`. The implementation chooses the first recognized source in that order. Use native patches for projected, downwardAPI, hostPath, CSI, or other volume types.

StatefulSet volume claim template fields differ from standalone PVC helper fields. Consult `references/api-reference.md` before reusing the same object between them.

## Namespaces, annotations, and Argo CD/Vault metadata

Keep cross-cutting metadata in the renderer when practical. Reuse local helpers such as an existing `anno(vaultPath, syncOrder)` rather than repeating annotation objects on every resource.

Example:

```jsonnet
local anno(vaultPath=null, syncOrder=null) = {
  metadata+: {
    annotations+: {}
    + (if vaultPath != null then { 'avp.kubernetes.io/path': vaultPath } else {})
    + (if syncOrder != null then { 'argocd.argoproj.io/sync-wave': std.toString(syncOrder) } else {}),
  },
};
```

Do not force this exact helper into projects that already have a different equivalent abstraction.

## Output format

By default, return:

1. The complete Jsonnet change or declaration.
2. A concise explanation of which `kone` helpers are used and why native patches are needed.
3. Any important caveat that affects rendered behavior.

Do not dump rendered YAML by default.

When the user explicitly asks for rendered YAML, or when an accessible repository/environment makes validation possible:

1. Determine the exact Tanka environment path and required ext vars/codes from the project.
2. Run `tk show <environment> ...` if execution tools and dependencies are available.
3. Report validation errors rather than inventing output.
4. If `tk show` succeeds, use the rendered manifests to verify selectors, namespaces, pod specs, affinity/tolerations, and native patch placement.

Never claim code was rendered or validated unless it actually was.

## Review checklist

Before finalizing code, check:

- Native constructor + OneHQ helper composition is appropriate.
- Helper name and argument count match the current source.
- Required values exist.
- Array-returning helpers are handled as arrays.
- Container definitions are objects and have distinct `name` fields.
- `image + tag` concatenation produces a valid image reference.
- Deployment selectors match Pod labels.
- StatefulSet Services select `{ app: <statefulset-name> }` when using the helper defaults.
- CronJob ServiceAccount is patched manually if needed.
- Unsupported Job/CronJob/container/Service/Ingress fields are native patches.
- Environment variable alias behavior is understood.
- Volume source is supported or explicitly patched.
- `serviceLevel.definitions` can match the resource name.
- Secrets do not contain accidental plaintext where Kubernetes `data` is expected.
- Namespace is added only to namespaced resources.
- Existing project abstractions are reused rather than duplicated.

## References

- Read `references/api-reference.md` for helper signatures, required/optional inputs, return shapes, and important implementation behavior.
- Read `references/patterns.md` for composition examples and common review failures.
- Read `references/library-source.md` when exact behavior matters or a summary is insufficient.
- Read `references/constructor-guide-reference.txt` only when useful for broader constructor examples; reconcile it against the bundled source before trusting a signature.
