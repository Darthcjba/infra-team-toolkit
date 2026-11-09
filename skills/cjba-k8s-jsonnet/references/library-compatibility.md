# OneHQ library compatibility

Read when a consumer pin differs from the bundled snapshot or a constructor example conflicts with working app settings. This records two inspected interfaces, not an exhaustive version matrix. Inspect the actual resolved source before applying either example to another revision.

## Select the target implementation

For an existing app, identify the lock revision and follow import shims to resolved code. Source from that exact revision takes precedence over the bundled API/pattern summaries and the separately supplied constructor guide. If only upstream source is available, resolve the locked commit rather than assuming main matches it. If the implementation cannot be obtained within scope, label provisional assumptions and unverified behavior.

An explicitly requested upgrade is a separate compatibility change: compare interfaces, adapt inputs and validate output. Do not change a dependency just because a snapshot example uses a different shape.

## Known scheduling interfaces

| Contract | Reference app pin | Bundled snapshot |
| --- | --- | --- |
| Revision | `10a46abb03c8a82ecc9479b036a74d5b79b00f4f` (requested `v1.0.14_3`) | `cb49c83a43cb04e05da5e820c6fe56faed32bf73` (archive-identified) |
| Inputs | `serviceLevel: 'Basic'` and `resources` map | `serviceLevel` object with `organization`, `mode`, `definitions` |
| `fetchServiceLevel` | `(name, resources, serviceLevel)` | `(name, serviceLevel)` |
| `getTolerations` | `(name, resources, serviceLevel)` | `(name, serviceLevel)` |
| `getAffinity` | `(name, values)`, reading `values.resources` and `values.serviceLevel` | `(name, values)`, reading `values.serviceLevel` |
| Policy selection | Matching resource-map key within the resource name | Matching definition key within the resource name |

Reference-pin workload fragment:

```jsonnet
{
  serviceLevel: 'Basic',
  resources: {
    backend: { Basic: 'spot', Standard: 'ondemand' },
  },
}
```

For that revision, direct calls use `kone.fetchServiceLevel(name, settings.resources, settings.serviceLevel)` and `kone.getTolerations(name, settings.resources, settings.serviceLevel)`. The workload helper already invokes scheduling when configured; do not add a second layer automatically.

Bundled-snapshot workload fragment:

```jsonnet
{
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
}
```

Here direct calls use `kone.fetchServiceLevel(name, settings.serviceLevel)` and `kone.getTolerations(name, settings.serviceLevel)`. The API/pattern references describe this snapshot. Calling the reference-pin interface "stale" only makes sense relative to this snapshot; it is a valid API for the pinned reference application.

These are fragments for the scheduling fields, not complete workloads. Keep the app's existing policy values and required constructor settings. Check matching names and the generated affinity/tolerations; unmatched-name handling differs, so do not assume a safe fallback. Both inspected Deployment implementations also react to `debug` in names by altering labels and replica counts. Render Service selectors against effective Pod labels.

## Verify other constructor behavior

Check supported fields as well as argument counts. A field documented for one revision may be ignored by another. Inspect helper code before relying on Deployment strategy, Job retry/deadline options, CronJob accounts, container fields or storage settings. Patch unsupported native fields at the right resource path and verify output; do not invent a helper argument.

Both inspected container implementations accept object collections with explicit `name` fields and concatenate `image + tag`. Their environment helper uses same-name keys under `secrets-` Secret names and ConfigMap mappings. Verify those details again for other revisions. A correct helper call does not guarantee application overrides propagate through already-derived settings; inspect composition too.

Reference-pin source anchors: [ServiceLevel](https://github.com/OneHQ/tanka-lib-k8-onehq/blob/10a46abb03c8a82ecc9479b036a74d5b79b00f4f/core/ServiceLevel.libsonnet), [Tolerations](https://github.com/OneHQ/tanka-lib-k8-onehq/blob/10a46abb03c8a82ecc9479b036a74d5b79b00f4f/tradetools/Tolerations.libsonnet), [Affinity](https://github.com/OneHQ/tanka-lib-k8-onehq/blob/10a46abb03c8a82ecc9479b036a74d5b79b00f4f/tradetools/Affinity.libsonnet), [Deployment](https://github.com/OneHQ/tanka-lib-k8-onehq/blob/10a46abb03c8a82ecc9479b036a74d5b79b00f4f/apps/Deployment.libsonnet). Bundled evidence remains in [library-source.md](library-source.md), with summaries in [api-reference.md](api-reference.md) and [patterns.md](patterns.md). The archive identifies the bundled commit; this skill update does not independently verify it against upstream.
