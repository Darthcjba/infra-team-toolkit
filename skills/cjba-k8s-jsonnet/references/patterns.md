# Jsonnet Patterns and Review Guide

## Contents

- Baseline renderer pattern
- Deployment + Service
- Job with unsupported fields
- CronJob with ServiceAccount
- StatefulSet + headless Service
- Secret and Service arrays
- HPA and PDB
- Scheduling
- Native-only resources
- Review failures to catch

## Baseline renderer pattern

```jsonnet
local k = import 'k.libsonnet';
local kone = import 'k8-onehq.libsonnet';
local values = import 'values.jsonnet';

local namespace = values.namespace;
local namespaced = { metadata+: { namespace: namespace } };

{
  backend:
    k.apps.v1.deployment.new('backend')
    + kone.createDeploy(values.backend, 'backend')
    + namespaced,
}
```

Prefer a shared namespace patch or the project's existing equivalent instead of repeating namespace literals.

## Deployment + Service

```jsonnet
local labels = { app: 'example', component: 'backend' };

{
  backend:
    k.apps.v1.deployment.new('example-backend')
    + kone.createDeploy(values.backend + { labels: labels }, 'example-backend')
    + namespaced,

  backendService:
    k.core.v1.service.new('example-backend-svc', labels, [
      { port: 80, targetPort: 3000, protocol: 'TCP' },
    ])
    + namespaced,
}
```

Keep Service selectors aligned with the effective Pod labels. Be careful with Deployment names containing `debug`, because the helper changes the `component` label.

## Job with unsupported fields

```jsonnet
{
  migrate:
    k.batch.v1.job.new('example-migrate')
    + kone.generateJob(values.migrate, 'example-migrate')
    + {
      spec+: {
        backoffLimit: 0,
        activeDeadlineSeconds: 1800,
        ttlSecondsAfterFinished: 3600,
      },
    }
    + namespaced,
}
```

Do not place those Job fields inside the values object expecting `generateJob` to copy them.

## CronJob with ServiceAccount

```jsonnet
{
  cleanup:
    k.batch.v1.cronJob.new('example-cleanup')
    + kone.generateCronJob(values.cleanup, 'example-cleanup')
    + {
      spec+: {
        concurrencyPolicy: 'Forbid',
        successfulJobsHistoryLimit: 1,
        failedJobsHistoryLimit: 1,
        jobTemplate+: {
          spec+: {
            backoffLimit: 0,
            template+: {
              spec+: {
                serviceAccountName: values.cleanup.saName,
              },
            },
          },
        },
      },
    }
    + namespaced,
}
```

`generateCronJob` does not consume `saName` in the bundled source.

## StatefulSet + headless Service

The helper uses `{ app: name }` for the StatefulSet selector and Pod labels.

```jsonnet
local name = 'example-search';

{
  search:
    k.apps.v1.statefulSet.new(name)
    + kone.createSS(values.search, name)
    + namespaced,

  searchHeadless:
    k.core.v1.service.new(name + '-headless', { app: name }, [
      { port: 9200, targetPort: 9200, protocol: 'TCP' },
    ])
    + {
      spec+: {
        clusterIP: 'None',
        publishNotReadyAddresses: true,
      },
    }
    + namespaced,
}
```

If `values.search.serviceName` differs from the headless Service name, the StatefulSet will point at the wrong governing Service.

## Secret and Service arrays

Because these helpers return arrays, map renderer patches over the elements:

```jsonnet
local generatedSecrets = kone.generateSecrets(values.secretBundle);
local generatedServices = kone.generateServices(values.serviceBundle);

{
  secrets: [s + namespaced for s in generatedSecrets],
  services: [s + namespaced for s in generatedServices],
}
```

Do not try `kone.generateSecrets(...) + namespaced`.

## HPA and PDB

```jsonnet
{
  backendHpa:
    k.autoscaling.v2.horizontalPodAutoscaler.new('example-backend-hpa')
    + kone.setHPA(values.backendHpa, 'example-backend')
    + namespaced,

  backendPdb:
    k.policy.v1.podDisruptionBudget.new('example-backend-pdb')
    + kone.setPDB({
      selector: { matchLabels: values.backend.labels },
      minAvailable: 1,
    }, 'example-backend')
    + namespaced,
}
```

## Scheduling

Bundled source uses `serviceLevel`, not the older `resources` scheduling map.

```jsonnet
local serviceLevel = {
  organization: 'onehq',
  mode: 'Basic',
  definitions: {
    backend: {
      Basic: 'spot',
      Standard: 'ondemand',
      matchExpressions: [
        { key: 'workload', operator: 'In', values: ['application'] },
      ],
      tolerations: [],
    },
  },
};

local backend = values.backend + { serviceLevel: serviceLevel };
```

The resource name passed to `createDeploy`, `generateJob`, etc. must contain a matching definition key such as `backend`. If no definition key matches, the source returns empty scheduling expressions/tolerations rather than falling back to another entry.

## Native-only resources

Use `k` directly when there is no OneHQ helper:

```jsonnet
{
  account:
    k.core.v1.serviceAccount.new('example-account')
    + namespaced,

  jobReader:
    k.rbac.v1.role.new('example-job-reader')
    + {
      rules: [{
        apiGroups: ['batch'],
        resources: ['jobs'],
        verbs: ['get', 'list', 'watch'],
      }],
    }
    + namespaced,
}
```

For an operator CRD with no typed `k` constructor, use a plain object with the correct `apiVersion`, `kind`, `metadata`, and `spec`.

## Review failures to catch

### Wrong: treating container collections as arrays

```jsonnet
cont: [values.backend]
```

Correct:

```jsonnet
cont: { backend: values.backend }
```

### Wrong: assuming helper copies unsupported Job fields

```jsonnet
values.job + { backoffLimit: 0 }
```

`generateJob` ignores `backoffLimit`. Patch the generated Job `spec`.

### Wrong: expecting CronJob `saName` to work

Patch the nested Pod spec manually.

### Wrong: stale service-level call

```jsonnet
kone.fetchServiceLevel(name, resources, serviceLevel)
```

Bundled source signature:

```jsonnet
kone.fetchServiceLevel(name, serviceLevel)
```

### Wrong: Secret alias under a `secrets-` name

For a secret named `secrets-app`, this mapping:

```jsonnet
['secrets-app', { DATABASE_PASSWORD: 'password' }]
```

renders a reference to Secret key `DATABASE_PASSWORD`, not `password`.

### Wrong: assuming ConfigMap alias mapping is honored

The config-map helper always uses the environment variable name as the ConfigMap key.

### Wrong: adding namespace to cluster-scoped resources

Do not apply `namespaced` to Namespace, ClusterRole, ClusterRoleBinding, PersistentVolume, StorageClass, or other cluster-scoped kinds.

### Wrong: fabricating validation

If `tk show` cannot be executed against the actual environment, return Jsonnet and explain that the manifest was not rendered. Do not manufacture a YAML result and call it validated.
