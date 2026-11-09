# tanka-lib-k8-onehq API Reference

This reference describes bundled snapshot `cb49c83a43cb04e05da5e820c6fe56faed32bf73`. It is authoritative over the separately supplied constructor guide for that snapshot; a consumer's locked/resolved implementation takes precedence for application work. Read [library-compatibility.md](library-compatibility.md) before applying these signatures to another revision. In particular, the reference app correctly uses an older scheduling interface.

## Contents

- Resource helpers
- Supporting helpers
- Scheduling shape
- Return-shape summary

## Resource helpers

### `createDeploy(values, name)`

Source: `apps/Deployment.libsonnet`

Compose with `k.apps.v1.deployment.new(name)`.

Required values:
- `labels`
- `replicas`
- `saName`
- `volumes`
- `initC`
- `cont`

Optional values:
- `registrySecretName`
- `serviceLevel`
- `terminationGracePeriodSeconds`
- `strategy`

Behavior:
- Sets selector and Pod labels from `values.labels`.
- If `name` contains `debug`, forces one replica and appends `-debug` to `labels.component`.
- Sets both `serviceAccountName` and legacy `serviceAccount`.
- Generates volumes and containers.
- Adds affinity/tolerations when `serviceLevel` exists.
- Copies `strategy` directly when supplied.

### `createSS(values, name)`

Source: `apps/StatefulSet.libsonnet`

Compose with `k.apps.v1.statefulSet.new(name)`.

Required values:
- `replicas`
- `serviceName`
- `saName`
- `volumes`
- `initC`
- `cont`
- `volumeClaimTemplates`

Optional values:
- `registrySecretName`
- `serviceLevel`

Behavior:
- Selector and Pod labels are always `{ app: name }`; `values.labels` is not used.
- Sets both `serviceAccountName` and legacy `serviceAccount`.
- Generates volume claim templates with `generateVolumeClaimTemplates`.

### `generateJob(values, name)`

Source: `batch/Job.libsonnet`

Compose with `k.batch.v1.job.new(name)`.

Required values:
- `labels`
- `restartPolicy`
- `volumes`
- `initC`
- `cont`

Optional values:
- `saName`
- `registrySecretName`
- `serviceLevel`

Not copied by the helper: `backoffLimit`, `activeDeadlineSeconds`, `completions`, `parallelism`, `ttlSecondsAfterFinished`. Add these to the native Job `spec`.

### `generateCronJob(values, name)`

Source: `batch/CronJob.libsonnet`

Compose with `k.batch.v1.cronJob.new(name)`.

Required values:
- `schedule`
- `labels`
- `restartPolicy`
- `volumes`
- `initC`
- `cont`

Optional values:
- `registrySecretName`
- `serviceLevel`

Important:
- This helper does not use `saName`. Patch `spec.jobTemplate.spec.template.spec.serviceAccountName` when needed.
- Add concurrency/history settings under CronJob `spec`.
- Add retry/deadline settings under `spec.jobTemplate.spec`.

### `setHPA(values, name)`

Source: `autoscaling/HorizontalPodAutoscaler.libsonnet`

Compose with `k.autoscaling.v2.horizontalPodAutoscaler.new(hpaName)`.

Required values:
- `minReplicas`
- `maxReplicas`
- `metrics`
- `behavior`

Behavior:
- Targets an `apps/v1` Deployment named by the second argument.
- Patch `scaleTargetRef` if the target is not a Deployment.

### `createPVC(values)`

Source: `core/PersistentVolumeClaim.libsonnet`

Compose with `k.core.v1.persistentVolumeClaim.new(name)`.

Required values:
- `accessModes`
- `storageSize`
- `storageClass`

### `generateSecrets(values)`

Source: `core/Secret.libsonnet`

Required:

```jsonnet
{
  secrets: [
    { name: '...', data: { KEY: '<base64>' }, type: 'Opaque' },
  ],
}
```

Returns an array of complete Secret resources. Namespace/annotations must be mapped onto each array element.

### `generateServices(values)`

Source: `core/Service.libsonnet`

Required:

```jsonnet
{
  services: [
    { name: '...', selector: {...}, ports: [...] },
  ],
}
```

Returns an array of complete Service resources. Patch Service fields such as `type`, `clusterIP`, or `publishNotReadyAddresses` after generation.

### `createIngress(hosts, svc_name, port, class, tls, annotations)`

Source: `networking.k8s.io/Ingress.libsonnet`

Compose with `k.networking.v1.ingress.new(name)`.

Behavior:
- `hosts` is an array of host strings.
- Adds one `/` Prefix path per host, all targeting the same Service/port.
- Sets `metadata.annotations`, a metadata label named `ingressClassName`, and `spec.ingressClassName`.
- Adds TLS only when a non-empty array is provided.
- Patch `spec.rules` natively for additional paths such as `/gql`.

### `setPDB(values, name)`

Source: `core/PodDisruptionBudget.libsonnet`

Compose with `k.policy.v1.podDisruptionBudget.new(name)`.

Required:
- `selector`

Optional:
- `minAvailable`
- `maxUnavailable`

The `name` parameter is not used by the implementation. Prefer one of `minAvailable` or `maxUnavailable`, not both.

### `crunchydb(name, config)`

Source: `tradetools/crunchy.libsonnet`

Returns a complete `postgres-operator.crunchydata.com/v1beta1` `PostgresCluster` object.

Important config fields used directly:
- `clusterName`
- `annotations`
- `postgresVersion`
- `users`
- `dataSource`
- `instances`
- `patroni`
- `backups`
- `proxy`
- `serviceLevel`

Each instance uses:
- `name`
- `replicas`
- `resources`
- `dataVolumeClaimSpec`
- `serviceLevel`
- optional `affinity`
- optional `tolerations`

Behavior:
- `metadata.name` is `config.clusterName`.
- The first `name` argument is used for service-level matching.
- Adds scheduling to instances, pgBackRest restore settings, repoHost/jobs, and pgBouncer when those sections are present.
- Merges or appends caller-provided affinity/tolerations in several paths; inspect exact source before complex scheduling edits.

## Supporting helpers

### `ContainerInception(containerObject)`

Source: `core/Container.libsonnet`

Input is an object whose values are container configs.

Required per config:
- `name`
- `image`
- `tag`
- `env`
- `command`
- `resources`
- `volumeMounts`

Optional:
- `ports` as one object with `containerPort` and optional `protocol`
- `lifecycle`
- `readinessProbe`
- `livenessProbe`

Behavior:
- Renders `image` as `config.image + config.tag`.
- Returns an array using `std.objectValues(containerObject)`.
- Applies `std.prune`.
- Use a native patch for `args`, `startupProbe`, `imagePullPolicy`, `securityContext`, or multiple/named ports.

### `generateContainers(init, cont)`

Returns a nested workload fragment containing `initContainers` and `containers`. Deployment/StatefulSet/Job/CronJob helpers already call it.

### `setenv(values)`

Source: `tradetools/EnvironmentVariables.libsonnet`

Required arrays:
- `secretRefs`
- `configMaps`
- `keyvalue`

Shapes:

```jsonnet
secretRefs: [['secret-name', { ENV_NAME: 'secret-key' }]],
configMaps: [['config-name', { ENV_NAME: 'ignored-value' }]],
keyvalue: [['ENV_NAME', 'literal-value']],
```

Special behavior:
- Secret names beginning `secrets-` use `ENV_NAME` as the Secret key and ignore the mapped value.
- ConfigMap entries always use `ENV_NAME` as the ConfigMap key and ignore mapped values.
- Sources are concatenated; duplicate environment variable names are not deduplicated.

### `setvolM(volumeMounts)`

Source: `tradetools/VolumeMounts.libsonnet`

Required per item:
- `name`
- `mountPath`
- `readOnly`

Optional:
- `subPath`

### `setvol(volumes)`

Source: `tradetools/Volumes.libsonnet`

Required per item:
- `name`
- one supported source

Supported source keys, checked in this order:
1. `claimName`
2. `emptyDir`
3. `secret`
4. `configMap`

When more than one is present, the first recognized source wins.

### `generateVolumeClaimTemplates(claims)`

Source: `tradetools/VolumeClaimTemplate.libsonnet`

Required per item:
- `name`
- `accessModes`
- `storageClassName`
- `storage`

These field names differ from `createPVC`, which expects `storageClass` and `storageSize`.

### `fetchServiceLevel(name, serviceLevel)`

Source: `core/ServiceLevel.libsonnet`

Current bundled signature is two arguments.

Expected `serviceLevel` shape:

```jsonnet
{
  organization: 'onehq',
  mode: 'Basic',
  definitions: {
    backend: {
      Basic: 'spot',
      Standard: 'ondemand',
      matchExpressions: [],  // optional
      tolerations: [],       // consumed by getTolerations
    },
  },
}
```

It finds definition keys occurring as substrings of `name`. If the selected mode maps to `spot` or `ondemand`, it returns node match expressions for `preemptible` plus `organization`, followed by optional definition `matchExpressions`. Otherwise it returns `[]`.

### `getAffinity(name, values)`

Source: `tradetools/Affinity.libsonnet`

Requires `values.serviceLevel`. Returns `nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution` using `fetchServiceLevel(name, values.serviceLevel)`.

### `getTolerations(name, serviceLevel)`

Source: `tradetools/Tolerations.libsonnet`

Uses the same definition-name matching and mode lookup. Returns base tolerations for `preemptibleNode` and `organization`, plus optional definition `tolerations`.

### `containerPatch(newDeployName, newLabels, source_containerName, newValues, baseDeployment)`

Source: `tradetools/ContainerPatch.libsonnet`

Clones/patches a Deployment:
- changes Deployment name
- changes selector and Pod labels
- finds the matching source container
- renames it to `newDeployName`
- replaces command/resources/volumeMounts
- appends `newValues.env` to existing env
- optionally replaces lifecycle/readinessProbe/livenessProbe
- keeps the source image

`newValues.env` and `newValues.volumeMounts` are already-rendered Kubernetes arrays, not OneHQ env/volume settings.

## Return-shape summary

Complete resource or resource array:
- `generateSecrets` -> Secret[]
- `generateServices` -> Service[]
- `crunchydb` -> PostgresCluster

Resource patch:
- `createDeploy`
- `createSS`
- `generateJob`
- `generateCronJob`
- `setHPA`
- `createPVC`
- `createIngress`
- `setPDB`

Supporting fragment/array:
- `ContainerInception`
- `generateContainers`
- `setenv`
- `setvolM`
- `setvol`
- `generateVolumeClaimTemplates`
- `fetchServiceLevel`
- `getAffinity`
- `getTolerations`
- `containerPatch`
