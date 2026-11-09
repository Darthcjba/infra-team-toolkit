---
name: cjba-k8s-jsonnet
description: 'Create, review, modify, and explain Kubernetes infrastructure written with Grafana Tanka/Jsonnet using OneHQ/tanka-lib-k8-onehq. Use for constructor composition and application changes that preserve existing layouts and pinned library interfaces.'
---

# OneHQ Kubernetes Jsonnet

Use the OneHQ `tanka-lib-k8-onehq` abstractions accurately and conservatively. Prefer the library's existing helpers when they model the requested behavior; use native `k.libsonnet` constructors and Jsonnet patches for fields the OneHQ helper does not support.

## Source authority

For an application, inspect its dependency lock, import shims and resolved implementation first. That revision governs signatures, supported fields and return shapes. User-supplied source for that revision can establish the same authority. A different supplied revision or upstream main is not permission to upgrade the app.

If the resolved source is missing, use source from the exact locked revision when accessible. Otherwise identify the uncertainty and use bundled guidance provisionally; do not claim compatibility or successful rendering. Fetching or upgrading dependencies must stay within the task's scope. Consult upstream current behavior when the task requests it or when it helps investigate a discrepancy, keeping it distinct from the app's target revision.

For standalone examples without an application pin, use `references/library-source.md`, then its summaries in `references/api-reference.md` and `references/patterns.md`. These describe bundled snapshot `cb49c83a43cb04e05da5e820c6fe56faed32bf73`, not every OneHQ revision. `references/constructor-guide-reference.txt` is secondary and contains signatures from another revision. Never let it override resolved source.

Read `references/library-compatibility.md` when the app pin differs from the snapshot, scheduling inputs differ, or an example conflicts with the app. Constructor examples below describe the bundled shape unless confirmed against the consumer's implementation.

## Application tasks

Read `references/application-workflow.md` for repository analysis, changes or refactoring. Explicitly read the app's `AGENTS.md` and linked architecture guidance; do not assume Cline-specific paths are automatically loaded by another agent.

Locate the application standard at `docs/infra-team-toolkit/standards/app-infrastructure.md` from the consumer root, or `standards/app-infrastructure.md` from an available toolkit checkout. Map existing files to its responsibilities. If neither is available, use the responsibility summary in the workflow reference and the app's own guidance; do not install the toolkit merely to answer a constructor question.

Preserve existing layouts and supported entry points. Identify the canonical input, actual merge/derivation stages and intended consumers before editing. Standard proposals such as `prepareComponents`, `validatePrepared` or generic capability toggles are not callable APIs until the app implements them. Analysis-only requests remain read-only; a render command does not authorize delivery.

## Decide the task mode

### Create

Use this path when the user describes desired Kubernetes resources or behavior.

1. Identify every Kubernetes resource required and the relationships among them.
2. Find a matching OneHQ helper in the resolved implementation; use `references/api-reference.md` for bundled examples only when compatible.
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
2. Compare calls against the pinned implementation, using snapshot summaries only where compatible. Trace the requested input through dependent components before choosing the edit location.
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

Choose the interface from resolved source. Some consumers correctly use `serviceLevel: 'Basic'` with a `resources` map and three-argument helpers. The bundled snapshot uses `serviceLevel: { organization, mode, definitions }` and two-argument helpers. Both are revision-specific contracts; do not convert between them as incidental cleanup.

Read `references/library-compatibility.md` for both shapes and their signatures. Check name-to-policy matching and rendered affinity/tolerations; failure handling differs by revision. Deployment names containing `debug` can alter labels and replica counts, so verify Service selectors when names change.

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

For code requests, return:

1. The complete Jsonnet change or declaration.
2. A concise explanation of which `kone` helpers are used and why native patches are needed.
3. Any important caveat that affects rendered behavior.

For analysis, return findings and source references. For repository edits, summarize the changed locations, expected/actual differences and verification; provide complete snippets when requested. Keep proposed architecture separate from implemented behavior.

Do not dump rendered YAML by default.

When a repository/environment is available, run its applicable offline render and relationship checks even if the requested output is only Jsonnet. For a standalone snippet with no environment, state any validation limit that affects confidence. Use the existing commands rather than inventing an environment.

1. Determine the exact Tanka environment path and required ext vars/codes from the project.
2. Run the documented render/check commands when tools and dependencies are available. Capture raw manifests in memory or use the app's existing redaction mechanism; never publish Secret payloads or credential values.
3. Confirm that rendering produced manifests, not just a zero exit code. Headless `tk show` can refuse redirected output unless `--dangerous-allow-redirect` is supplied; use that flag only with controlled capture/redaction.
4. Verify intended image consumers, identities/selectors, namespaces, references, metadata, Pod specs, affinity/tolerations and native patch placement. Allow documented revision-derived Job names and update their dependent gates.
5. Report exact commands, actual results and unexecuted checks. Separate offline relationships from image contents, external-resource existence and runtime readiness.

Never claim code was rendered or validated unless it actually was.

## Review checklist

Before finalizing code, check:

- Native constructor + OneHQ helper composition is appropriate.
- Helper name and argument count match the resolved target source.
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
- Resource names match the resolved scheduling policy map or definitions.
- Secrets do not contain accidental plaintext where Kubernetes `data` is expected.
- Namespace is added only to namespaced resources.
- Existing project abstractions are reused rather than duplicated.
- Canonical shared changes reach all intended consumers; component-local overrides are described separately.
- Supported optional components and externally owned resources retain consistent references; no capability is inferred from an ignored input field.

## References

- Read `references/application-workflow.md` for file responsibilities, input tracing and application validation.
- Read `references/library-compatibility.md` when selecting guidance for an app pin that differs from the snapshot.
- Read `references/api-reference.md` for bundled helper signatures, inputs, return shapes and implementation behavior.
- Read `references/patterns.md` for bundled composition examples and common review failures.
- Read `references/library-source.md` for exact bundled behavior; inspect resolved consumer source first for application work.
- Read `references/constructor-guide-reference.txt` only for useful broader examples; reconcile its signatures against the target implementation.
