#!/usr/bin/env python3
"""Map rendered Kubernetes JSON to a self-contained HTML diagram, JSON and Mermaid."""
import argparse
from collections import Counter
import html
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

CLUSTER_KINDS = {
    'Namespace', 'Node', 'PersistentVolume', 'StorageClass', 'ClusterRole', 'ClusterRoleBinding',
    'CustomResourceDefinition', 'APIService', 'IngressClass', 'PriorityClass', 'RuntimeClass',
    'CSIDriver', 'CSINode', 'VolumeAttachment', 'MutatingWebhookConfiguration',
    'ValidatingWebhookConfiguration', 'ClusterIssuer', 'GatewayClass',
}
TEMPLATED = {'Deployment', 'StatefulSet', 'DaemonSet', 'ReplicaSet', 'ReplicationController', 'Job'}


class MapError(Exception):
    pass


def group(api_version):
    return api_version.split('/')[0] if '/' in api_version else ''


def resources(value, path='input'):
    """Accept single objects, Lists, arrays and nested Tanka resource maps."""
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from resources(child, f'{path}[{index}]')
    elif isinstance(value, dict):
        if value.get('apiVersion') and value.get('kind'):
            if value['kind'] == 'List' or (value['kind'].endswith('List') and 'items' in value):
                yield from resources(value.get('items', []), path + '.items')
            else:
                if not value.get('metadata', {}).get('name'):
                    raise MapError('A resource has no metadata.name; generated names cannot be mapped offline')
                yield path, value
        else:
            for key, child in value.items():
                yield from resources(child, path + '.' + key)


def pod_template(resource):
    kind, spec = resource['kind'], resource.get('spec', {})
    if kind == 'Pod':
        return resource.get('metadata', {}), spec
    if kind in TEMPLATED:
        template = spec.get('template', {})
        return template.get('metadata', {}), template.get('spec', {})
    if kind == 'CronJob':
        template = spec.get('jobTemplate', {}).get('spec', {}).get('template', {})
        return template.get('metadata', {}), template.get('spec', {})
    return None


def matches(labels, selector):
    if not isinstance(selector, dict):
        return False
    if any(labels.get(k) != v for k, v in selector.get('matchLabels', {}).items()):
        return False
    for expr in selector.get('matchExpressions', []):
        key, operator, values = expr.get('key'), expr.get('operator'), expr.get('values', [])
        if operator == 'In' and (key not in labels or labels[key] not in values):
            return False
        if operator == 'NotIn' and key in labels and labels[key] in values:
            return False
        if operator == 'Exists' and key not in labels:
            return False
        if operator == 'DoesNotExist' and key in labels:
            return False
        if operator not in ('In', 'NotIn', 'Exists', 'DoesNotExist'):
            return False
    return True


def pick(value, *keys):
    return {key: value[key] for key in keys if key in value}


def claim_summary(spec):
    return {**pick(spec, 'accessModes', 'storageClassName', 'volumeMode'),
            'requested_storage': spec.get('resources', {}).get('requests', {}).get('storage')}


def summarize(resource):
    """Use an allowlist; never serialize arbitrary spec/metadata/data values."""
    kind, spec = resource['kind'], resource.get('spec', {})
    summary = {}
    annotations = resource.get('metadata', {}).get('annotations', {})
    if 'argocd.argoproj.io/sync-wave' in annotations:
        summary['sync_wave'] = annotations['argocd.argoproj.io/sync-wave']
    if 'argocd.argoproj.io/hook' in annotations:
        summary['argo_hook'] = annotations['argocd.argoproj.io/hook']
    template = pod_template(resource)
    if template is not None:
        _, pod = template
        summary.update(pick(spec, 'replicas', 'schedule', 'parallelism', 'completions', 'backoffLimit', 'activeDeadlineSeconds', 'ttlSecondsAfterFinished'))
        if kind == 'CronJob':
            summary.update(pick(spec.get('jobTemplate', {}).get('spec', {}), 'backoffLimit', 'activeDeadlineSeconds', 'ttlSecondsAfterFinished'))
        summary['service_account'] = pod.get('serviceAccountName') or pod.get('serviceAccount') or 'default'
        summary.update(pick(pod, 'restartPolicy', 'automountServiceAccountToken', 'terminationGracePeriodSeconds'))
        summary['containers'] = []
        for collection in ('initContainers', 'containers', 'ephemeralContainers'):
            for container in pod.get(collection, []):
                item = {**pick(container, 'name', 'image'), 'role': collection,
                        'ports': [pick(p, 'name', 'containerPort', 'protocol') for p in container.get('ports', [])],
                        'resources': pick(container.get('resources', {}), 'requests', 'limits'),
                        'environment_names': sorted(e['name'] for e in container.get('env', []) if 'name' in e),
                        'probes': {probe: next((t for t in ('httpGet', 'tcpSocket', 'exec', 'grpc') if t in container[probe]), 'unspecified')
                                   for probe in ('startupProbe', 'livenessProbe', 'readinessProbe') if isinstance(container.get(probe), dict)},
                        'volume_mounts': [pick(v, 'name', 'mountPath', 'readOnly') for v in container.get('volumeMounts', [])]}
                summary['containers'].append(item)
        summary['volumes'] = [{'name': v.get('name'), 'sources': sorted(k for k in v if k != 'name')} for v in pod.get('volumes', [])]
    elif kind == 'Service':
        summary = {**pick(spec, 'type', 'clusterIP', 'externalName'),
                   'ports': [pick(p, 'name', 'port', 'targetPort', 'protocol', 'nodePort') for p in spec.get('ports', [])],
                   **summary}
    elif kind == 'Ingress':
        summary.update(pick(spec, 'ingressClassName'))
        summary['hosts'] = sorted({rule['host'] for rule in spec.get('rules', []) if rule.get('host')})
        summary['paths'] = [pick(p, 'path', 'pathType') for rule in spec.get('rules', []) for p in rule.get('http', {}).get('paths', [])]
    elif kind in ('Secret', 'ConfigMap'):
        summary.update(pick(resource, 'type', 'immutable'))
        summary['keys'] = sorted(set(resource.get('data', {})) | set(resource.get('stringData', {})) | set(resource.get('binaryData', {})))
        summary['payload'] = 'omitted'
    elif kind == 'PersistentVolumeClaim':
        summary.update(claim_summary(spec))
    elif kind == 'StorageClass':
        summary.update(pick(resource, 'provisioner', 'reclaimPolicy', 'volumeBindingMode', 'allowVolumeExpansion'))
    elif kind in ('HorizontalPodAutoscaler', 'PodDisruptionBudget'):
        summary.update(pick(spec, 'minReplicas', 'maxReplicas', 'minAvailable', 'maxUnavailable'))
    elif kind == 'NetworkPolicy':
        summary.update(pick(spec, 'policyTypes'))
        summary['rule_counts'] = {direction: len(spec.get(direction, [])) for direction in ('ingress', 'egress')}
        summary['coverage'] = 'selected workloads only; no traffic-allowance evaluation'
    elif kind in ('Role', 'ClusterRole'):
        summary['rules'] = [pick(rule, 'apiGroups', 'resources', 'verbs', 'resourceNames', 'nonResourceURLs') for rule in resource.get('rules', [])]
    elif kind == 'PostgresCluster' and group(resource['apiVersion']) == 'postgres-operator.crunchydata.com':
        summary.update(pick(spec, 'postgresVersion', 'image'))
        summary['instances'] = [{**pick(i, 'name', 'replicas', 'resources'), 'storage': claim_summary(i.get('dataVolumeClaimSpec', {}))}
                                for i in spec.get('instances', [])]
        summary['databases'] = sorted({db for user in spec.get('users', []) for db in user.get('databases', [])})
    elif kind not in ('Namespace', 'ServiceAccount', 'RoleBinding', 'ClusterRoleBinding', 'PersistentVolume'):
        summary['coverage'] = 'identity and declared ownership only; no schema-specific extractor'
    return summary


class Graph:
    def __init__(self, value, namespace='default', infer_env=False):
        self.documents = list(resources(value))
        if not self.documents:
            raise MapError('No named Kubernetes resources found in the JSON input')
        self.namespace, self.infer_env = namespace, infer_env
        self.cluster_kinds = set(CLUSTER_KINDS)
        self.cluster_crds = set()
        for _, resource in self.documents:
            if resource['kind'] == 'CustomResourceDefinition' and resource.get('spec', {}).get('scope') == 'Cluster':
                self.cluster_crds.add((resource['spec']['group'], resource['spec']['names']['kind']))
        self.nodes, self.raw, self.edges, self.notes = {}, {}, {}, []
        for source, resource in self.documents:
            node_id = self.identity(resource['kind'], resource['metadata'].get('namespace') or namespace, resource['metadata']['name'], group(resource['apiVersion']))
            if node_id in self.nodes:
                raise MapError('Duplicate Kubernetes identity in input')
            self.nodes[node_id] = {'id': node_id, 'kind': resource['kind'], 'apiVersion': resource['apiVersion'],
                                   'namespace': '' if self.cluster_scoped(resource['kind'], group(resource['apiVersion'])) else resource['metadata'].get('namespace') or namespace,
                                   'name': resource['metadata']['name'], 'state': 'rendered', 'source': source,
                                   'attributes': summarize(resource)}
            self.raw[node_id] = resource

    def cluster_scoped(self, kind, api_group):
        return kind in self.cluster_kinds or (api_group, kind) in self.cluster_crds

    def identity(self, kind, namespace, name, api_group=''):
        return '|'.join([api_group, kind, '' if self.cluster_scoped(kind, api_group) else namespace, name])

    def link(self, source, kind, name, relation, location, namespace=None, api_group='', evidence='reference'):
        if not name:
            return
        namespace = self.nodes[source]['namespace'] if namespace is None else namespace
        target = self.identity(kind, namespace, name, api_group)
        if target not in self.nodes:
            self.nodes[target] = {'id': target, 'kind': kind, 'apiVersion': None, 'apiGroup': api_group,
                                  'namespace': '' if self.cluster_scoped(kind, api_group) else namespace, 'name': name,
                                  'state': 'unresolved', 'attributes': {'coverage': 'not in input; may be external, default, operator-generated or missing'}}
        self.edge(source, target, relation, location, evidence)

    def edge(self, source, target, relation, location, evidence='reference'):
        key = (source, target, relation, evidence)
        edge = self.edges.setdefault(key, {'source': source, 'target': target, 'relation': relation, 'evidence': evidence, 'locations': []})
        if location not in edge['locations']:
            edge['locations'].append(location)

    def pod_links(self, node_id, pod):
        account = pod.get('serviceAccountName') or pod.get('serviceAccount')
        self.link(node_id, 'ServiceAccount', account or 'default', 'uses account', 'spec.serviceAccountName', evidence='reference' if account else 'default')
        for secret in pod.get('imagePullSecrets', []):
            self.link(node_id, 'Secret', secret.get('name'), 'pulls image with', 'imagePullSecrets')
        for collection in ('initContainers', 'containers', 'ephemeralContainers'):
            for container in pod.get(collection, []):
                location = collection + '/' + container.get('name', '?')
                for env in container.get('env', []):
                    for field, kind in [('secretKeyRef', 'Secret'), ('configMapKeyRef', 'ConfigMap')]:
                        ref = env.get('valueFrom', {}).get(field, {})
                        self.link(node_id, kind, ref.get('name'), 'reads environment from', location + '/env/' + env.get('name', '?'))
                for env_from in container.get('envFrom', []):
                    for field, kind in [('secretRef', 'Secret'), ('configMapRef', 'ConfigMap')]:
                        self.link(node_id, kind, env_from.get(field, {}).get('name'), 'reads environment from', location + '/envFrom')
                if self.infer_env:
                    self.env_links(node_id, container, location, collection == 'initContainers')
        for volume in pod.get('volumes', []):
            location = 'volumes/' + volume.get('name', '?')
            self.link(node_id, 'PersistentVolumeClaim', volume.get('persistentVolumeClaim', {}).get('claimName'), 'mounts claim', location)
            self.link(node_id, 'Secret', volume.get('secret', {}).get('secretName'), 'mounts Secret', location)
            self.link(node_id, 'ConfigMap', volume.get('configMap', {}).get('name'), 'mounts ConfigMap', location)
            for projection in volume.get('projected', {}).get('sources', []):
                self.link(node_id, 'Secret', projection.get('secret', {}).get('name'), 'projects Secret', location)
                self.link(node_id, 'ConfigMap', projection.get('configMap', {}).get('name'), 'projects ConfigMap', location)

    def env_links(self, node_id, container, location, init):
        # Inspect literals only in memory. Emit matched object identities and env names,
        # never URL values, userinfo, paths, queries, commands or arbitrary external hosts.
        env = {e['name']: e['value'] for e in container.get('env', []) if isinstance(e.get('value'), str) and 'name' in e}
        namespace = self.nodes[node_id]['namespace']
        if init and 'JOB_NAME' in env:
            target = self.identity('Job', env.get('NS', namespace), env['JOB_NAME'], 'batch')
            if target in self.raw:
                self.edge(node_id, target, 'possible Job gate', location + '/env/JOB_NAME', 'inferred')
        for name, value in env.items():
            try:
                host = urlsplit(value).hostname if '://' in value else None
            except ValueError:
                continue
            if not host:
                continue
            for target, resource in self.raw.items():
                node = self.nodes[target]
                if resource['kind'] == 'Service':
                    service, ns = node['name'], node['namespace']
                    names = {f'{service}.{ns}', f'{service}.{ns}.svc', f'{service}.{ns}.svc.cluster.local'}
                    if ns == namespace:
                        names.add(service)
                    matched = host in names
                elif resource['kind'] == 'Ingress':
                    matched = host in {r.get('host') for r in resource.get('spec', {}).get('rules', [])}
                else:
                    continue
                if matched:
                    self.edge(node_id, target, 'possible endpoint', location + '/env/' + name, 'inferred')

    def build(self):
        workloads = {i: pod_template(r) for i, r in self.raw.items() if pod_template(r) is not None}
        for node_id, resource in self.raw.items():
            node, spec = self.nodes[node_id], resource.get('spec', {})
            kind, namespace = node['kind'], node['namespace']
            if namespace:
                ns_id = self.identity('Namespace', '', namespace)
                if ns_id not in self.nodes:
                    self.nodes[ns_id] = {'id': ns_id, 'kind': 'Namespace', 'apiVersion': 'v1', 'namespace': '', 'name': namespace,
                                         'state': 'unresolved', 'attributes': {'coverage': 'namespace not included in input'}}
                self.edge(ns_id, node_id, 'contains', 'metadata.namespace', 'membership')
            for owner in resource.get('metadata', {}).get('ownerReferences', []):
                self.link(node_id, owner['kind'], owner['name'], 'owned by', 'metadata.ownerReferences', api_group=group(owner['apiVersion']))
            if node_id in workloads:
                self.pod_links(node_id, workloads[node_id][1])
            if kind == 'Service' and spec.get('selector'):
                selected = []
                for target, (meta, _) in workloads.items():
                    if self.nodes[target]['namespace'] == namespace and matches(meta.get('labels', {}), {'matchLabels': spec['selector']}):
                        self.edge(node_id, target, 'selects workload', 'spec.selector', 'selector')
                        selected.append(target)
                if not selected:
                    self.notes.append({'node': node_id, 'message': 'Service selector matches no workload in input; this is not proof of a missing live endpoint'})
            elif kind == 'Ingress':
                backends = [spec.get('defaultBackend', {})] + [p.get('backend', {}) for r in spec.get('rules', []) for p in r.get('http', {}).get('paths', [])]
                for backend in backends:
                    self.link(node_id, 'Service', backend.get('service', {}).get('name') or backend.get('serviceName'), 'routes to', 'spec.backends')
                    ref = backend.get('resource', {})
                    if ref:
                        self.link(node_id, ref['kind'], ref['name'], 'routes to resource', 'spec.backends.resource', api_group=ref.get('apiGroup', ''))
                for tls in spec.get('tls', []):
                    self.link(node_id, 'Secret', tls.get('secretName'), 'uses TLS', 'spec.tls')
                self.link(node_id, 'IngressClass', spec.get('ingressClassName'), 'uses IngressClass', 'spec.ingressClassName', api_group='networking.k8s.io')
            elif kind == 'EndpointSlice':
                self.link(node_id, 'Service', resource.get('metadata', {}).get('labels', {}).get('kubernetes.io/service-name'), 'endpoints for', 'metadata.labels.service-name')
                for endpoint in resource.get('endpoints', []):
                    ref = endpoint.get('targetRef', {})
                    if ref:
                        self.link(node_id, ref.get('kind', 'Pod'), ref.get('name'), 'endpoint target', 'endpoints.targetRef', namespace=ref.get('namespace', namespace), api_group=group(ref.get('apiVersion', 'v1')))
            elif kind in ('RoleBinding', 'ClusterRoleBinding'):
                ref = resource.get('roleRef', {})
                self.link(node_id, ref.get('kind', 'Role'), ref.get('name'), 'binds role', 'roleRef', api_group=ref.get('apiGroup', 'rbac.authorization.k8s.io'))
                for subject in resource.get('subjects', []):
                    if subject.get('kind') == 'ServiceAccount':
                        self.link(node_id, 'ServiceAccount', subject.get('name'), 'binds account', 'subjects', namespace=subject.get('namespace') or namespace)
                self.nodes[node_id]['attributes']['other_subject_count'] = sum(s.get('kind') != 'ServiceAccount' for s in resource.get('subjects', []))
            elif kind == 'ServiceAccount':
                for field in ('secrets', 'imagePullSecrets'):
                    for ref in resource.get(field, []):
                        self.link(node_id, 'Secret', ref.get('name'), 'references Secret', field)
            elif kind == 'HorizontalPodAutoscaler':
                ref = spec.get('scaleTargetRef', {})
                if ref:
                    self.link(node_id, ref['kind'], ref['name'], 'scales', 'spec.scaleTargetRef', api_group=group(ref.get('apiVersion', 'apps/v1')))
            elif kind in ('PodDisruptionBudget', 'NetworkPolicy'):
                selector = spec.get('selector') if kind == 'PodDisruptionBudget' else spec.get('podSelector')
                # Legacy policy/v1beta1 PDB empty selectors select nothing.
                eligible = selector is not None and not (kind == 'PodDisruptionBudget' and resource['apiVersion'] == 'policy/v1beta1' and selector == {})
                if eligible:
                    for target, (meta, _) in workloads.items():
                        if self.nodes[target]['namespace'] == namespace and matches(meta.get('labels', {}), selector):
                            self.edge(node_id, target, 'selects for policy', 'spec.selector', 'selector')
            elif kind == 'StatefulSet':
                self.link(node_id, 'Service', spec.get('serviceName'), 'governed by Service', 'spec.serviceName')
                for claim in spec.get('volumeClaimTemplates', []):
                    name = claim['metadata']['name']
                    template_id = self.identity('PersistentVolumeClaimTemplate', namespace, node['name'] + '/' + name)
                    self.nodes[template_id] = {'id': template_id, 'kind': 'PersistentVolumeClaimTemplate', 'apiVersion': 'v1',
                                              'namespace': namespace, 'name': name + ' (' + node['name'] + ')', 'state': 'template',
                                              'attributes': claim_summary(claim.get('spec', {}))}
                    self.edge(node_id, template_id, 'declares claim template', 'spec.volumeClaimTemplates')
                    self.link(template_id, 'StorageClass', claim.get('spec', {}).get('storageClassName'), 'uses StorageClass', 'spec.storageClassName', api_group='storage.k8s.io')
            elif kind == 'PersistentVolumeClaim':
                self.link(node_id, 'StorageClass', spec.get('storageClassName'), 'uses StorageClass', 'spec.storageClassName', api_group='storage.k8s.io')
                self.link(node_id, 'PersistentVolume', spec.get('volumeName'), 'bound to volume', 'spec.volumeName')
            elif kind == 'PersistentVolume':
                ref = spec.get('claimRef', {})
                self.link(node_id, 'PersistentVolumeClaim', ref.get('name'), 'claimed by', 'spec.claimRef', namespace=ref.get('namespace', self.namespace))
                self.link(node_id, 'StorageClass', spec.get('storageClassName'), 'uses StorageClass', 'spec.storageClassName', api_group='storage.k8s.io')
            elif kind == 'PostgresCluster' and group(resource['apiVersion']) == 'postgres-operator.crunchydata.com':
                for instance in spec.get('instances', []):
                    self.link(node_id, 'StorageClass', instance.get('dataVolumeClaimSpec', {}).get('storageClassName'), 'uses StorageClass', 'spec.instances.dataVolumeClaimSpec', api_group='storage.k8s.io')
        edges = sorted(self.edges.values(), key=lambda e: (e['source'], e['target'], e['relation'], e['evidence']))
        for edge in edges:
            edge['locations'].sort()
        nodes = sorted(self.nodes.values(), key=lambda n: n['id'])
        return {'schema_version': 1, 'nodes': nodes, 'edges': edges, 'notes': self.notes,
                'summary': {'resources': len(self.raw), 'nodes': len(nodes), 'relationships': len(edges),
                            'unresolved': sum(n['state'] == 'unresolved' for n in nodes),
                            'templates': sum(n['state'] == 'template' for n in nodes),
                            'kinds': dict(sorted(Counter(r['kind'] for r in self.raw.values()).items()))},
                'scope': {'inferred_environment_links': self.infer_env,
                          'meaning': 'Rendered declarations, selector matches and optional heuristics; not observed traffic or runtime readiness',
                          'omitted': ['Secret/ConfigMap payloads', 'literal environment values', 'commands/args', 'arbitrary annotations/status'],
                          'limits': ['Unknown CRDs have generic identity/ownership coverage only',
                                     'Operator-generated children and external systems are not expanded automatically',
                                     'NetworkPolicy edges show selected workloads, not a full traffic-allowance analysis',
                                     'Unresolved means absent from input, not necessarily absent from the cluster']}}


def mermaid(graph):
    names = {node['id']: f'n{index}' for index, node in enumerate(graph['nodes'])}
    lines = ['flowchart LR']
    for node in graph['nodes']:
        label = html.escape(node['kind'] + ': ' + node['name'], quote=True).replace('\n', ' ')
        lines.append(f'  {names[node["id"]]}["{label}"]')
    for edge in graph['edges']:
        if edge['evidence'] == 'membership':
            continue
        arrow = '-.->' if edge['evidence'] in ('inferred', 'default') else '-->'
        lines.append(f'  {names[edge["source"]]} {arrow}|"{edge["relation"]}"| {names[edge["target"]]}')
    return '\n'.join(lines) + '\n'


def write_map(graph, output):
    output.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(graph, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (Path(__file__).parent / 'templates/kubernetes-map.html').read_text()
    (output / 'index.html').write_text(template.replace('__GRAPH_JSON__', encoded))
    (output / 'graph.json').write_text(json.dumps(graph, indent=2) + '\n')
    (output / 'graph.mmd').write_text(mermaid(graph))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path, help='rendered JSON (resource, List, array or Tanka map); - for stdin')
    source.add_argument('--app', type=Path, help='Tanka application root; render with tk eval, never apply')
    parser.add_argument('--environment', help='environment/entry point relative to --app')
    parser.add_argument('--ext-str', action='append', default=[], help='KEY=value passed to Tanka; values are never recorded in graph metadata')
    parser.add_argument('--namespace', help='namespace for objects without one; otherwise use Tanka spec.namespace, then default')
    parser.add_argument('--infer-env-links', action='store_true', help='mark matched Service/Ingress URLs and init JOB_NAME conventions as inferred links')
    parser.add_argument('--output', type=Path, required=True, help='directory for index.html, graph.json and graph.mmd')
    args = parser.parse_args()
    try:
        if args.app:
            app = args.app.resolve()
            if not args.environment or not (app / args.environment).resolve().is_relative_to(app):
                raise MapError('--environment must select an entry point within --app')
            if args.output.resolve().is_relative_to(app):
                raise MapError('Choose an output directory outside the application checkout')
            command = ['tk', 'eval', args.environment]
            for ext in args.ext_str:
                command += ['--ext-str', ext]
            result = subprocess.run(command, cwd=app, text=True, capture_output=True)
            if result.returncode:
                raise MapError('Tanka rendering failed; raw output withheld because it may contain credentials')
            value = json.loads(result.stdout)
            entrypoint = app / args.environment
            spec_path = (entrypoint if entrypoint.is_dir() else entrypoint.parent) / 'spec.json'
            spec_namespace = json.loads(spec_path.read_text()).get('spec', {}).get('namespace') if spec_path.is_file() else None
            namespace = args.namespace or spec_namespace or 'default'
            revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=app, text=True, capture_output=True)
            provenance = {'mode': 'tanka', 'entry_point': args.environment, 'namespace_fallback': namespace}
            if revision.returncode == 0:
                provenance['app_revision'] = revision.stdout.strip()
        else:
            if args.environment or args.ext_str:
                raise MapError('--environment and --ext-str require --app')
            if str(args.input) != '-' and args.input.resolve() in {args.output.resolve() / name for name in ('index.html', 'graph.json', 'graph.mmd')}:
                raise MapError('Output would overwrite the input; choose a different output directory')
            value = json.loads(sys.stdin.read() if str(args.input) == '-' else args.input.read_text())
            namespace = args.namespace or 'default'
            provenance = {'mode': 'json', 'namespace_fallback': namespace}
        graph = Graph(value, namespace, args.infer_env_links).build()
        graph['source'] = provenance
        write_map(graph, args.output)
    except MapError as error:
        print('Map failed: ' + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print('Map failed: check the JSON shape, resource fields, tools and paths; raw input/output withheld', file=sys.stderr)
        return 1
    print(json.dumps({'output': str(args.output), **graph['summary']}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
