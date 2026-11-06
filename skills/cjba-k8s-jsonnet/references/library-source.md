# Bundled OneHQ Library Source Snapshot

This file contains the exact text of the source files from the user-supplied `tanka-lib-k8-onehq-main.zip` snapshot used to create this skill. Treat these implementations as authoritative for the bundled revision. The ZIP archive identifies snapshot commit `cb49c83a43cb04e05da5e820c6fe56faed32bf73`.

## Contents

- README.md
- main.libsonnet
- values-example.jsonnet
- apps/Deployment.libsonnet
- apps/StatefulSet.libsonnet
- autoscaling/HorizontalPodAutoscaler.libsonnet
- batch/CronJob.libsonnet
- batch/Job.libsonnet
- core/Container.libsonnet
- core/PersistentVolumeClaim.libsonnet
- core/PodDisruptionBudget.libsonnet
- core/Secret.libsonnet
- core/Service.libsonnet
- core/ServiceLevel.libsonnet
- networking.k8s.io/Ingress.libsonnet
- tradetools/Affinity.libsonnet
- tradetools/ContainerPatch.libsonnet
- tradetools/EnvironmentVariables.libsonnet
- tradetools/Tolerations.libsonnet
- tradetools/VolumeClaimTemplate.libsonnet
- tradetools/VolumeMounts.libsonnet
- tradetools/Volumes.libsonnet
- tradetools/crunchy.libsonnet


## `README.md`

```jsonnet
# tanka-lib-k8-onehq
## Project to deploy kubernetes resources with Jsonnet Tanka.
Through the following links you can access the official documentation of the Jsonnet libraries and also a tutorial to learn Tanka.  
* [Jsonnet Standard Library.](https://jsonnet.org/ref/stdlib.html)
* [Grafana Tanka Tutorial.](https://tanka.dev/tutorial/overview/)  
  
## How to import the library tanka-lib-k8-onehq  
The first step is to create a new project where we will import the necessary libraries. To do this, follow these steps:  
  
 1. **Create a directory for your project.**
```bash
mkdir onehq-example-project && cd onehq-example-project
```  
2. **Initialize new Tanka project.**  
```bash
tk init --k8s=1.28  
```  
> [!NOTE]  
> --k8s=1.28 (kubernetes version handle by the cluster)  
  
  3. **Add a new environment to a Tanka project.**  
```bash  
tk env add environments/onehq-example-staging  
```  
4. **Defines the URL of the Kubernetes cluster server associated with the environment.**  
  
```bash  
tk env set environments/onehq-example-staging/ --server=https://api.crc.testing:6443  
``` 
5. **Sets the default namespace for resources created in this environment.**  
```bash  
tk env set environments/onehq-example-staging/ --namespace=onehq-example-staging  
```  
6. **Import k8s-libsonnet library.**  
```bash  
jb install github.com/jsonnet-libs/k8s-libsonnet/1.28@main github.com/grafana/jsonnet-libs/ksonnet-util  
```  
7. **Import tanka-lib-k8-onehq library.**  
```bash  
jb install github.com/OneHQ/tanka-lib-k8-onehq@main  
```  
8. **Create the file `k8-onehq.libsonnet` in the _lib/_ with the following content**  
```bash  
import 'github.com/OneHQ/tanka-lib-k8-onehq/main.libsonnet'  
```  
  

With these steps, we have successfully installed the necessary libraries for our project. Now, we just need to define the resources we want to deploy in `main.jsonnet` along with our `values` file. For this tutorial, I will define a **Deployment**, a **StatefulSet**, and a **CronJob**.  
  

The following `main.jsonnet` file is an example of how we can define resources.  

```bash  
# K8s resources libsonnet.
local k = import 'k.libsonnet';
local k8 = import 'k8-onehq.libsonnet';
# values
local values = import 'staging-values.jsonnet';

{

  deploy: k.apps.v1.deployment.new(name='onehq-example-deploy-staging', replicas=2, podLabels={}, containers=[]) + k8.createDeploy(values.rails, 'onehq-example-staging '),
  cj: k.batch.v1.cronJob.new(name='onehq-example-cj-staging', schedule=[], containers=[]) + k8.generateCronJob(values.rails),
  ss: k.apps.v1.statefulSet.new(name='onehq-example-ss-staging', replicas=2, containers=[], volumeClaims=[], podLabels={}) + k8.createSS(values.cj, 'onehq-example-staging'),

}  
```  
In the root of the project, you will find the `values-example.jsonnet` file, which you can use as a reference to define the values for the Deployment, StatefulSet, and CronJob.  

You can run `tk show` to view the Kubernetes configuration generated from the Jsonnet files in the project without applying any changes to the cluster.  
```bash  
tk show environments/onehq-example-staging/  
```  
You can run `tk apply` to apply the generated configuration. This will deploy the resources defined in your files to the cluster.  
```bash 
tk apply environments/onehq-example-staging/  
```  
You can run `tk diff` to compare the current state of the resources. This allows you to see the differences before applying any changes.  
```bash  
tk diff environments/onehq-example-staging/
```

## `main.libsonnet`

```jsonnet
(import 'github.com/OneHQ/tanka-lib-k8-onehq/apps/Deployment.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/apps/StatefulSet.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/autoscaling/HorizontalPodAutoscaler.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/batch/CronJob.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/batch/Job.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Container.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/PersistentVolumeClaim.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Secret.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Service.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/networking.k8s.io/Ingress.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/EnvironmentVariables.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/VolumeMounts.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/VolumeClaimTemplate.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/crunchy.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/ContainerPatch.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/PodDisruptionBudget.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet') + (import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet')
```

## `values-example.jsonnet`

```jsonnet
# Example of a values in your project.
local tags = import 'staging-version.json'; // Contains the version of the image
local value = import 'staging-values.jsonnet'; // Call the same file so you can reuse values. For example the enviroments
{
  rails: {
    saName: 'sa-name',
    serviceName: 'serviceName',
    saRole: 'sarole',
    schedule: '*/1 * * * *',  # For cronjobs
    labels: {
        app: 'app-name',
      },
    restartPolicy: 'OnFailure',
    registrySecretName: 'registry-secret-name',
    dockerHubSecret: '', #in case the registry is DockerHub
    initC: {
      dbReady: {
        name: "db-ready-check",
        image: "postgres:16",
        command: ['/bin/sh', '-c', 
                  'until pg_isready -h $PGHOST -p $PGPORT -d $PGDATABASE -U $PGUSER; do
                      echo "Waiting for database readiness...";
                      sleep 5;
                    done'
                  ],
        resources: {},
        volumeMounts: [
          {
            name: 'example-env-secrets',
            mountPath: '/etc/secrets',
            readOnly: true,
          },
        ],
        env: {
          secretRefs: [
            [value.rails.cont.backend.env.railsUserSecretName, value.rails.cont.backend.env.railsUserSecrets],
          ],
          configMaps: [
            [value.rails.cont.backend.env.railsconfigMapsName, value.rails.cont.backend.env.railsconfigMaps],
          ],

          railsSecretName: 'main-db-pguser',
          railsSecrets: {
            PGUSER: 'user',
          },

          railsconfigMapsName: 'redis-url',
          railsconfigMaps: {
            REDIS_URL: 'redis-url',
          },
          keyvalue: [
            ['RAILS_ENV', 'development'],
            ['DBNAME', 'db-name'],
          ],

        },
      },
  },

  volumes: [
    {
      name: 'example-env-secrets',
      secret: {
        secretName: 'example-env-secrets',
      },
    },
  ],

  volumeClaimTemplates: [
    {
      name: 'example-volumeClaimTemplate',
      accessModes: ["ReadWriteOnce"],
      storageClassName: "storage-class-name",
      storage: "1Gi",
    },
  ],
  
  cont: {
    sidekiqDeploy: {
        name: "db-ready-check",
        image: "postgres:16",
        command: ['/bin/sh', '-c', 
                  'until pg_isready -h $PGHOST -p $PGPORT -d $PGDATABASE -U $PGUSER; do
                      echo "Waiting for database readiness...";
                      sleep 5;
                    done'
                  ],
        ports:
          {
            containerPort: 8080,
            protocol: "TCP",
          },
        resources: {},
        volumeMounts: [],
        env: {
          secretRefs: [
            [self.railsSecretName, self.railsSecrets],
          ],

          configMaps: [
            [self.railsconfigMapsName, self.railsconfigMaps],
          ],
          
          railsSecretName: 'main-db-pguser-maindb-admin-staging',
          railsSecrets: {
            PGUSER: 'user',
          },

          railsconfigMapsName: 'redis-url',
          railsconfigMaps: {
            REDIS_URL: 'redis-url',
          },
          keyvalue: [
            ['RAILS_ENV', 'development'],
            ['DBNAME', 'db-name'],
          ],
        },
    },
  },
 },
}
```

## `apps/Deployment.libsonnet`

```jsonnet
local k = import 'k.libsonnet';
local Containers = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Container.libsonnet';
local setvol = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet';
local Affinity = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet';
local ServiceLevel = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet';
local Tolerations = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet';

local createDeploy(values, name) =
  // ---------- helpers -------------------------------------------------------
  local isDebug = std.length(std.findSubstr("debug", name)) > 0;
  // Copy `values.labels` and, only for debug deployments, override `component`
  // without mutating the original object.
  local effectiveLabels =
    if isDebug
    then values.labels { component: values.labels.component + "-debug" }
    else values.labels;
  // --------------------------------------------------------------------------
{
  spec+: {
    selector: {
      matchLabels: effectiveLabels,
    },
    replicas: if isDebug then 1 else values.replicas,
    template: {
      metadata: { labels:  effectiveLabels },
      spec+: {
        serviceAccountName: values.saName,
        serviceAccount: values.saName,
        volumes: setvol.setvol(values.volumes),
      }
      + (if std.objectHas(values, "registrySecretName") then {
          imagePullSecrets: [k.core.v1.localObjectReference.withName(values.registrySecretName)],
      } else {})
      + Containers.generateContainers(values.initC, values.cont).spec.template.spec
      + (if std.objectHas(values, "serviceLevel") then 
          { tolerations: Tolerations.getTolerations(name, values.serviceLevel) }
        else {})
      + (if std.objectHas(values, "serviceLevel") then {
          affinity: Affinity.getAffinity(name, values),
      } else {})
      + (if std.objectHas(values, "terminationGracePeriodSeconds") then { 
          terminationGracePeriodSeconds: values.terminationGracePeriodSeconds 
      } else {})
    }
  }
  + (if std.objectHas(values, 'strategy') then {
      strategy: values.strategy,
  } else {}),
};

{
  createDeploy: createDeploy,
}
```

## `apps/StatefulSet.libsonnet`

```jsonnet
local k = import 'k.libsonnet';
local Containers = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Container.libsonnet';
local setvol = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet';
local vclaim = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/VolumeClaimTemplate.libsonnet';
local Affinity = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet';
local ServiceLevel = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet';
local Tolerations = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet';

local createSS(values, name) = {
  spec+: {
    selector: {
      matchLabels: {app: name},
    },
    replicas: values.replicas,
    serviceName: values.serviceName,
    template: {
      metadata: { labels: {app: name} },
      spec+: {
        serviceAccountName: values.saName,
        serviceAccount: values.saName,
        volumes: setvol.setvol(values.volumes),
      } 
      + (if std.objectHas(values, "registrySecretName") then {
          imagePullSecrets: [k.core.v1.localObjectReference.withName(values.registrySecretName)],
      } else {})
      + Containers.generateContainers(values.initC, values.cont).spec.template.spec
      + (if std.objectHas(values, "serviceLevel") then 
          { tolerations: Tolerations.getTolerations(name, values.serviceLevel) }
        else {})
      + (if std.objectHas(values, "serviceLevel") then {
          affinity: Affinity.getAffinity(name, values),
      } else {})
    },
    volumeClaimTemplates: vclaim.generateVolumeClaimTemplates(values.volumeClaimTemplates),
  },
};

{
  createSS: createSS,
}
```

## `autoscaling/HorizontalPodAutoscaler.libsonnet`

```jsonnet
local setHPA(values, name) = {
  spec+: {
    scaleTargetRef: {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      name: name,
    },
    minReplicas: values.minReplicas,
    maxReplicas: values.maxReplicas,
    metrics: values.metrics,
    behavior: values.behavior,
  },
};

{
    setHPA: setHPA,
}
```

## `batch/CronJob.libsonnet`

```jsonnet
local k = import 'k.libsonnet';
local Containers = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Container.libsonnet';
local setvol = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet';
local Affinity = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet';
local ServiceLevel = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet';
local Tolerations = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet';

local generateCronJob(values, name) = {
    spec+: {
        schedule: values.schedule,
        jobTemplate: {
            spec: {
                template: {
                    metadata: {
                        labels: values.labels,
                    },
                    spec+: {
                        restartPolicy: values.restartPolicy,
                        volumes: setvol.setvol(values.volumes),
                    } 
                    + (if std.objectHas(values, "registrySecretName") then {
                        imagePullSecrets: [k.core.v1.localObjectReference.withName(values.registrySecretName)],
                    } else {})
                    + Containers.generateContainers(values.initC, values.cont).spec.template.spec
                    + (if std.objectHas(values, "serviceLevel") then
                        { tolerations: Tolerations.getTolerations(name, values.serviceLevel) }
                    else {})
                    + (if std.objectHas(values, "serviceLevel") then {
                        affinity: Affinity.getAffinity(name, values),
                    } else {})
                },
            },
        },
    },
};

{
    generateCronJob: generateCronJob,
}
```

## `batch/Job.libsonnet`

```jsonnet
local k = import 'k.libsonnet';
local Containers = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/Container.libsonnet';
local setvol = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet';
local Affinity = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet';
local ServiceLevel = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet';
local Tolerations = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet';

local generateJob(values, name) = {
    spec+: {
        template: {
            metadata: {
                labels: values.labels,
            },
            spec+: {
                restartPolicy: values.restartPolicy,
                volumes: setvol.setvol(values.volumes),
            }
            + (if std.objectHas(values, "saName") then {
                serviceAccountName: values.saName,
            } else {})
            + (if std.objectHas(values, "registrySecretName") then {
                imagePullSecrets: [k.core.v1.localObjectReference.withName(values.registrySecretName)],
            } else {}) 
            + Containers.generateContainers(values.initC, values.cont).spec.template.spec
            + (if std.objectHas(values, "serviceLevel") then
                { tolerations: Tolerations.getTolerations(name, values.serviceLevel) }
              else {})
            + (if std.objectHas(values, "serviceLevel") then {
                affinity: Affinity.getAffinity(name, values),
            } else {})
        },
    },
};

{
    generateJob: generateJob,
}
```

## `core/Container.libsonnet`

```jsonnet
local k = import 'k.libsonnet';
local envVar = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/EnvironmentVariables.libsonnet';
local volM = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/VolumeMounts.libsonnet';
local vol = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Volumes.libsonnet';

local ContainerInception(ci) = std.map(function(config)
  std.prune(
    k.core.v1.container.new(config.name, config.image + config.tag) + {
      env+: envVar.setenv(config.env),
      command: config.command,
      resources: config.resources,
      volumeMounts+: volM.setvolM(config.volumeMounts),
    } +
    (if std.objectHas(config, 'ports') then {
      ports: [
        {
          containerPort: config.ports.containerPort,
        } + (if std.objectHas(config.ports, 'protocol') then { protocol: config.ports.protocol } else {}),
      ]
    } else {}) +
    (if std.objectHas(config, 'lifecycle') then { lifecycle: config.lifecycle } else {}) +
    (if std.objectHas(config, 'readinessProbe') then { readinessProbe: config.readinessProbe } else {}) +
    (if std.objectHas(config, 'livenessProbe') then { livenessProbe: config.livenessProbe } else {})
  ),
  std.objectValues(ci)
);

local generateContainers(init, cont) = {
  spec+: {
    template+: {
      spec+: {
        initContainers: ContainerInception(init),
        containers: ContainerInception(cont),
      }
    }
  }
};

{
  generateContainers: generateContainers,
  ContainerInception: ContainerInception,
}
```

## `core/PersistentVolumeClaim.libsonnet`

```jsonnet
local createPVC(values) = {
    spec+: {
      accessModes: values.accessModes,
      resources: {
        requests: {
          storage: values.storageSize,
        },
      },
      storageClassName: values.storageClass,
    },
};
{
    createPVC: createPVC,
}
```

## `core/PodDisruptionBudget.libsonnet`

```jsonnet
local setPDB(values, name) = {
  spec+: {
    selector: values.selector,
  }
  + (if std.objectHas(values, "minAvailable") then 
       { minAvailable: values.minAvailable } 
     else {})
  + (if std.objectHas(values, "maxUnavailable") then 
       { maxUnavailable: values.maxUnavailable } 
     else {})
};

{
  setPDB: setPDB,
}
```

## `core/Secret.libsonnet`

```jsonnet
local k = import 'k.libsonnet';

local generateSecrets(values) = std.map(function(secret)
  k.core.v1.secret.new(
    name=secret.name,
    data=secret.data,
    type=secret.type,
  ),
  values.secrets,
);

{
  generateSecrets: generateSecrets,
}
```

## `core/Service.libsonnet`

```jsonnet
local k = import 'k.libsonnet';

local generateServices(values) = std.map(function(service)
  k.core.v1.service.new(
    name=service.name,
    selector=service.selector,
    ports=service.ports
  ),
  values.services
);

{
  generateServices: generateServices,
}
```

## `core/ServiceLevel.libsonnet`

```jsonnet
local Nodes = {
  spot: [
    { 
      key: "preemptible", 
      values: ["true"], 
      operator: "In", 
    }
  ],

  ondemand: [
    { 
      key: "preemptible", 
      values: ["false"], 
      operator: "In",
    }
  ],

  generateNodesType: function(type, values)
    local base =
      if type == "ondemand" then self.ondemand
      else self.spot;

    base + [
      {
        key: "organization",
        values: [values.organization],
        operator: "In",
      }
    ]

};

local fetchServiceLevel(name, serviceLevel) =
  local matchkey = std.filter(
    function(k)
      std.length(std.findSubstr(k, name)) > 0,
    std.objectFields(serviceLevel.definitions)
  );

  local key = if std.length(matchkey) > 0 then matchkey[0] else null;

  if key != null && std.objectHas(serviceLevel.definitions, key) then
    local def = serviceLevel.definitions[key];
    local sl = def[serviceLevel.mode];

    local extraMatchExpressions =
      if std.objectHas(def, "matchExpressions") then def.matchExpressions
      else [];

    if sl == "spot" || sl == "ondemand" then
      Nodes.generateNodesType(sl, serviceLevel) + extraMatchExpressions
    else
      []
  else
    [];


{
  fetchServiceLevel: fetchServiceLevel,
}
```

## `networking.k8s.io/Ingress.libsonnet`

```jsonnet
local set_hosts(host, svc_name, port) = {
    host: host,
    http: {
      paths: [
        {
          path: '/',
          pathType: 'Prefix',
          backend: {
            service: {
              name: svc_name,
              port: {
                number: port,
              }
            },
          },
        },
      ],
    },
};

local createIngress(hosts, svc_name, port, class, tls, annotations) = {
  metadata+: {
    annotations: annotations,
    labels:{
      ingressClassName: class,
    },
  },
  spec+: {
    ingressClassName: class,
    rules: std.flattenArrays([
      std.map(function(key)
        set_hosts(key, svc_name, port),
        hosts,
      ),
    ]),
  }
  + (if tls != null && std.length(tls) > 0 then { tls: tls } else {})
};

{
    createIngress: createIngress,
    set_hosts: set_hosts,
}
```

## `tradetools/Affinity.libsonnet`

```jsonnet
local ServiceLevel = import 'github.com/OneHQ/tanka-lib-k8-onehq/core/ServiceLevel.libsonnet';

local getAffinity(name, values) = {
  nodeAffinity: {
    requiredDuringSchedulingIgnoredDuringExecution: {
      nodeSelectorTerms: [{
        matchExpressions: ServiceLevel.fetchServiceLevel(name, values.serviceLevel)
      }]
    }
  }
};

{
  getAffinity: getAffinity,
}
```

## `tradetools/ContainerPatch.libsonnet`

```jsonnet
local containerPatch = function(
  newDeployName,
  newLabels,
  source_containerName,
  newValues,
  baseDeployment)
baseDeployment + {
  metadata+: {
    name: newDeployName,
  },
  spec+: {
    selector+: {
      matchLabels: newLabels,
    },
    template+: {
      metadata+: {
        labels: newLabels,
      },
      spec+: {
        containers: std.map(
          function(c)
            if c.name == source_containerName then
              std.prune(
                c + {
                  name: newDeployName,
                  command: newValues.command,
                  resources: newValues.resources,
                  env+: newValues.env,
                  volumeMounts: newValues.volumeMounts,
                } + (if std.objectHas(newValues, 'lifecycle') then { lifecycle: newValues.lifecycle } else {}) +
                (if std.objectHas(newValues, 'readinessProbe') then { readinessProbe: newValues.readinessProbe } else {}) +
                (if std.objectHas(newValues, 'livenessProbe') then { livenessProbe: newValues.livenessProbe } else {})
              )
            else c,
          baseDeployment.spec.template.spec.containers
        ),
      },
    },
  },
};

{
    containerPatch: containerPatch,
}
```

## `tradetools/EnvironmentVariables.libsonnet`

```jsonnet
local k = import 'k.libsonnet';

local setenv(values) = std.flattenArrays([
    if std.length(values.secretRefs) > 0 then
        std.flattenArrays(std.map(function(secretItem)
            if std.length(std.objectFields(secretItem[1])) > 0 then
                std.map(function(key)
                    if std.startsWith(secretItem[0], 'secrets-') then
                        k.core.v1.envVar.fromSecretRef(key, secretItem[0], key)
                    else 
                        k.core.v1.envVar.fromSecretRef(key, secretItem[0], secretItem[1][key]),
                std.objectFields(secretItem[1])
                )
            else [],
            values.secretRefs
        ))
    else [],
    if std.length(values.configMaps) > 0 then
        std.flattenArrays(std.map(function(configMapItem)
            if std.length(std.objectFields(configMapItem[1])) > 0 then
                std.map(function(key)
                  k.core.v1.envVar.withName(key) +
                  k.core.v1.envVar.valueFrom.configMapKeyRef.withName(configMapItem[0]) +
                  k.core.v1.envVar.valueFrom.configMapKeyRef.withKey(key),
                  std.objectFields(configMapItem[1]))
            else [],
            values.configMaps
        ))
    else [],
    if std.length(values.keyvalue) > 0 then
        std.map(function(item)
            k.core.v1.envVar.withName(item[0]) + k.core.v1.envVar.withValue(item[1]),
            values.keyvalue
        )
    else [],
]);

{
    setenv: setenv,
}
```

## `tradetools/Tolerations.libsonnet`

```jsonnet
local Tolerations= {
  spot: [
    { 
      key: "preemptibleNode", 
      value: "true", 
      operator: "Equal", 
      effect: "NoSchedule" 
    }
  ],

  ondemand: [
    { 
      key: "preemptibleNode", 
      value: "false", 
      operator: "Equal", 
      effect: "NoSchedule" 
    }
  ],

  generateToleration: function(type, values)
    local base =
      if type == "ondemand" then self.ondemand
      else self.spot;

    base + [
      {
        key: "organization", 
        value: values.organization, 
        operator: "Equal", 
        effect: "NoSchedule" 
      }
    ]
};

local getTolerations(name, serviceLevel) =
  local matchkey = std.filter(
    function(k)
      std.length(std.findSubstr(k, name)) > 0,
    std.objectFields(serviceLevel.definitions)
  );

  local key = if std.length(matchkey) > 0 then matchkey[0] else null;

  local tolerations =
    if key != null && std.objectHas(serviceLevel.definitions, key) then
      local def = serviceLevel.definitions[key];
      local sl = def[serviceLevel.mode];

      local extraTolerations =
        if std.objectHas(def, "tolerations") then def.tolerations
        else [];

      if sl == "spot" || sl == "ondemand" then
        Tolerations.generateToleration(sl, serviceLevel) + extraTolerations
      else
        []
    else
      [];

  tolerations;

{
  getTolerations: getTolerations,
}
```

## `tradetools/VolumeClaimTemplate.libsonnet`

```jsonnet
local generateVolumeClaimTemplates(vclaim) =
  if std.length(vclaim) == 0 then []
  else std.map(
    function(key)
      {
        metadata: { name: key.name},
        spec: {
          accessModes: key.accessModes,
          storageClassName: key.storageClassName,
          resources: {
            requests: {
              storage: key.storage,
            },
          },
        },
      },
    vclaim
  );

{
  generateVolumeClaimTemplates: generateVolumeClaimTemplates,
}
```

## `tradetools/VolumeMounts.libsonnet`

```jsonnet
local k = import 'k.libsonnet';

local setvolM(volm) = std.map(
  function(key)
    local base = k.core.v1.volumeMount.new(
      name=key.name,
      mountPath=key.mountPath,
      readOnly=key.readOnly
    );
    if std.objectHas(key, 'subPath')
    then base + k.core.v1.volumeMount.withSubPath(key.subPath)
    else base,
  volm
);

{
  setvolM: setvolM,
}
```

## `tradetools/Volumes.libsonnet`

```jsonnet
local k = import 'k.libsonnet';

local setvol(vol) =
  if std.length(vol) == 0 then []
  else std.map(
    function(key)
      {
        name: key.name,
      } +
      if std.objectHas(key, 'claimName') then
        { persistentVolumeClaim: { claimName: key.claimName } }
      else if std.objectHas(key, 'emptyDir') then
        { emptyDir: key.emptyDir }
      else if std.objectHas(key, 'secret') then
        { secret: key.secret }
      else if std.objectHas(key, 'configMap') then
        { configMap: key.configMap }
      else {},
    vol
  );

{
  setvol: setvol,
}
```

## `tradetools/crunchy.libsonnet`

```jsonnet
local Affinity = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Affinity.libsonnet';
local Tolerations = import 'github.com/OneHQ/tanka-lib-k8-onehq/tradetools/Tolerations.libsonnet';

local crunchydb(name, config) = {
  apiVersion: "postgres-operator.crunchydata.com/v1beta1",
  kind: "PostgresCluster",
  metadata: {
    name: config.clusterName,
    annotations: config.annotations,
  },
  spec: {
    postgresVersion: config.postgresVersion,
    users: config.users,
    dataSource: config.dataSource + (
      if std.objectHas(config.dataSource, 'pgbackrest') then {
        pgbackrest+: config.dataSource.pgbackrest + {
          affinity+: 
            if std.objectHas(config.dataSource, 'pgbackrest') && std.objectHas(config.dataSource.pgbackrest, 'affinity') then
              std.mergePatch(config.dataSource.pgbackrest.affinity, Affinity.getAffinity(name, config))
            else
              Affinity.getAffinity(name, config),
          tolerations+: 
            if std.objectHas(config.dataSource, 'pgbackrest') && std.objectHas(config.dataSource.pgbackrest, 'tolerations') then
              config.dataSource.pgbackrest.tolerations + Tolerations.getTolerations(name, config.serviceLevel)
            else
              Tolerations.getTolerations(name, config.serviceLevel),
        }
    } else {}),
    instances: [
        {
            name: i.name,
            replicas: i.replicas,
            resources: i.resources,
            dataVolumeClaimSpec: i.dataVolumeClaimSpec,
            affinity:
              if std.objectHas(i, 'affinity') &&
                 std.objectHas(i.affinity, 'nodeAffinity') &&
                 std.objectHas(i.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution, 'nodeSelectorTerms')
              then
                local affinity1 = Affinity.getAffinity(name, { serviceLevel: i.serviceLevel });
                local affinity2 = i.affinity;

                local terms1 = affinity1.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms;
                local terms2 = affinity2.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms;

                local combinedMatchExpressions =
                  std.flattenArrays([t.matchExpressions for t in terms1] + [t.matchExpressions for t in terms2]);

                local combinedNodeAffinity = {
                  requiredDuringSchedulingIgnoredDuringExecution: {
                    nodeSelectorTerms: [
                      { matchExpressions: combinedMatchExpressions }
                    ]
                  }
                };
                std.mergePatch(i.affinity, {
                  nodeAffinity: combinedNodeAffinity,
                })
              else if std.objectHas(i, 'affinity') then
                std.mergePatch(i.affinity, Affinity.getAffinity(name, {
                  serviceLevel: i.serviceLevel,
                }))
              else
                Affinity.getAffinity(name, {
                  serviceLevel: i.serviceLevel,
                }),
            tolerations:
              if std.objectHas(i, 'tolerations') then
                i.tolerations + Tolerations.getTolerations(name, i.serviceLevel)
              else
                Tolerations.getTolerations(name, i.serviceLevel),
          }
        for i in config.instances
    ],
    patroni: config.patroni,
    backups: config.backups + (
      if std.objectHas(config.backups, 'pgbackrest') then {
        pgbackrest: config.backups.pgbackrest + {
          repoHost: {
            affinity: 
              if std.objectHas(config.backups.pgbackrest, 'repoHost') && std.objectHas(config.backups.pgbackrest.repoHost, 'affinity') then
                std.mergePatch(config.backups.pgbackrest.repoHost.affinity, Affinity.getAffinity(name, config))
              else
                Affinity.getAffinity(name, config),
            tolerations: 
              if std.objectHas(config.backups.pgbackrest, 'repoHost') && std.objectHas(config.backups.pgbackrest.repoHost, 'tolerations') then
                config.backups.pgbackrest.repoHost.tolerations + Tolerations.getTolerations(name, config.serviceLevel)
              else
                Tolerations.getTolerations(name, config.serviceLevel),
         },
         jobs: {
            affinity: 
              if std.objectHas(config.backups, 'jobs') && std.objectHas(config.backups.jobs, 'affinity') then
                std.mergePatch(config.backups.jobs.affinity, Affinity.getAffinity(name, config))
              else
                Affinity.getAffinity(name, config),
            tolerations: 
              if std.objectHas(config.backups, 'jobs') && std.objectHas(config.backups.jobs, 'tolerations') then
                config.backups.jobs.tolerations + Tolerations.getTolerations(name, config.serviceLevel)
              else
                Tolerations.getTolerations(name, config.serviceLevel),
         },
        },
      } else {}),
    proxy: config.proxy + (
      if std.objectHas(config.proxy, 'pgBouncer') then {
        pgBouncer: config.proxy.pgBouncer + {
          affinity: 
            if std.objectHas(config.proxy.pgBouncer, 'affinity') then
              std.mergePatch(config.proxy.pgBouncer.affinity, Affinity.getAffinity(name, config))
            else
              Affinity.getAffinity(name, config),
          tolerations:
             if std.objectHas(config.proxy.pgBouncer, 'tolerations') then
               config.proxy.pgBouncer.tolerations + Tolerations.getTolerations(name, config.serviceLevel)
            else
              Tolerations.getTolerations(name, config.serviceLevel),
        },
      } else {}),
  },
};

{
    crunchydb: crunchydb,
}
```
