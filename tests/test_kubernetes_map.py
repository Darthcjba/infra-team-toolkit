"""Check graph semantics, namespace isolation, inference boundaries and payload omission."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('kubernetes_map', Path(__file__).resolve().parents[1] / 'scripts/map-kubernetes.py')
MAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAP)


def obj(kind, name, namespace='test', api='v1', **fields):
    return {'apiVersion': api, 'kind': kind, 'metadata': {'name': name, 'namespace': namespace}, **fields}


def workload(name, namespace='test', labels=None, containers=None, kind='Deployment'):
    return obj(kind, name, namespace, 'apps/v1' if kind != 'Job' else 'batch/v1', spec={
        'replicas': 2, 'template': {'metadata': {'labels': labels or {'app': name}},
        'spec': {'containers': containers or [{'name': 'app', 'image': 'example.invalid/app:test'}]}}})


def edges(graph, relation):
    nodes = {n['id']: n for n in graph['nodes']}
    return [(nodes[e['source']]['name'], nodes[e['target']]['name'], e['evidence'])
            for e in graph['edges'] if e['relation'] == relation]


class ResourceMapContracts(unittest.TestCase):
    def test_nested_tanka_maps_and_lists_are_normalized_without_descending_into_resources(self):
        secret = obj('Secret', 'secret', data={'looks_like_resource': obj('ConfigMap', 'not-a-resource')})
        value = {'nested': {'one': workload('api')}, 'two': {'apiVersion': 'v1', 'kind': 'List', 'items': [secret]}}
        graph = MAP.Graph(value).build()
        self.assertEqual(graph['summary']['resources'], 2)
        self.assertNotIn('not-a-resource', [n['name'] for n in graph['nodes']])

    def test_service_selectors_do_not_cross_namespace_and_empty_selectors_do_not_match_all(self):
        graph = MAP.Graph([workload('api'), workload('other', 'elsewhere', {'app': 'api'}),
                           obj('Service', 'svc', spec={'selector': {'app': 'api'}}),
                           obj('Service', 'external', spec={'selector': {}})]).build()
        self.assertEqual(edges(graph, 'selects workload'), [('svc', 'api', 'selector')])

    def test_references_resolve_within_namespace_and_cluster_role_stays_cluster_scoped(self):
        api = workload('api', containers=[{'name': 'app', 'image': 'example.invalid/app:test',
                         'env': [{'name': 'TOKEN', 'valueFrom': {'secretKeyRef': {'name': 'shared', 'key': 'token'}}}]}])
        binding = obj('RoleBinding', 'readers', api='rbac.authorization.k8s.io/v1',
                      roleRef={'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'ClusterRole', 'name': 'read'},
                      subjects=[{'kind': 'ServiceAccount', 'name': 'runner', 'namespace': 'other'}])
        graph = MAP.Graph([api, obj('Secret', 'shared'), obj('Secret', 'shared', 'other'), binding,
                           obj('ClusterRole', 'read', namespace='', api='rbac.authorization.k8s.io/v1')]).build()
        secret_edge = next(e for e in graph['edges'] if e['relation'] == 'reads environment from')
        nodes = {n['id']: n for n in graph['nodes']}
        self.assertEqual(nodes[secret_edge['target']]['namespace'], 'test')
        self.assertEqual(nodes[next(e['target'] for e in graph['edges'] if e['relation'] == 'binds role')]['state'], 'rendered')
        self.assertIn(('api', 'default', 'default'), edges(graph, 'uses account'))
        self.assertEqual(nodes[next(e['target'] for e in graph['edges'] if e['relation'] == 'binds account')]['namespace'], 'other')

    def test_secret_configmap_env_command_and_annotation_values_are_not_exported(self):
        marker = 'private-value-do-not-export'
        api = workload('api', containers=[{'name': 'app', 'image': 'example.invalid/app:test',
                         'env': [{'name': 'TOKEN', 'value': marker}], 'command': [marker], 'args': [marker],
                         'readinessProbe': {'exec': {'command': [marker]}}}])
        api['metadata']['annotations'] = {'custom': marker, 'kubectl.kubernetes.io/last-applied-configuration': marker}
        graph = MAP.Graph([api, obj('Secret', 'creds', data={'encoded': marker}, stringData={'token': marker}),
                           obj('ConfigMap', 'config', data={'config.ini': marker})]).build()
        self.assertNotIn(marker, json.dumps(graph))
        with tempfile.TemporaryDirectory() as tmp:
            MAP.write_map(graph, Path(tmp))
            for path in Path(tmp).iterdir():
                self.assertNotIn(marker, path.read_text())

    def test_inference_is_opt_in_and_does_not_export_url_credentials_or_queries(self):
        api = workload('api', containers=[{'name': 'app', 'image': 'image:test',
                         'env': [{'name': 'REDIS_URL', 'value': 'redis://private:password@redis.test.svc.cluster.local:6379/0?token=secret'},
                                 {'name': 'OTHER', 'value': 'https://unknown.private.example/secret'}]}])
        gate = workload('test-job', kind='Job')
        gate['spec']['template']['spec']['initContainers'] = [{'name': 'wait', 'image': 'tool:test',
                         'env': [{'name': 'JOB_NAME', 'value': 'prepare'}, {'name': 'NS', 'value': 'test'}]}]
        docs = [api, gate, workload('prepare', kind='Job'), obj('Service', 'redis', spec={})]
        self.assertEqual(edges(MAP.Graph(docs).build(), 'possible endpoint'), [])
        graph = MAP.Graph(docs, infer_env=True).build()
        self.assertEqual(edges(graph, 'possible endpoint'), [('api', 'redis', 'inferred')])
        self.assertEqual(edges(graph, 'possible Job gate'), [('test-job', 'prepare', 'inferred')])
        for marker in ['password', 'token=secret', 'unknown.private.example']:
            self.assertNotIn(marker, json.dumps(graph))

    def test_cronjobs_use_nested_pod_spec_and_projected_sources(self):
        cron = obj('CronJob', 'nightly', api='batch/v1', spec={'schedule': '0 0 * * *', 'jobTemplate': {'spec': {'template': {
            'spec': {'serviceAccountName': 'runner', 'containers': [{'name': 'task', 'image': 'task:test'}],
                     'volumes': [{'name': 'projected', 'projected': {'sources': [{'secret': {'name': 'credentials'}}, {'configMap': {'name': 'settings'}}]}}]}}}}})
        graph = MAP.Graph(cron).build()
        self.assertIn(('nightly', 'runner', 'reference'), edges(graph, 'uses account'))
        self.assertIn(('nightly', 'credentials', 'reference'), edges(graph, 'projects Secret'))
        self.assertIn(('nightly', 'settings', 'reference'), edges(graph, 'projects ConfigMap'))

    def test_stateful_claim_templates_are_distinct_from_actual_claims(self):
        stateful = workload('db', kind='StatefulSet')
        stateful['spec']['volumeClaimTemplates'] = [{'metadata': {'name': 'data'}, 'spec': {'storageClassName': 'fast', 'resources': {'requests': {'storage': '8Gi'}}}}]
        graph = MAP.Graph(stateful).build()
        template = next(n for n in graph['nodes'] if n['state'] == 'template')
        self.assertEqual(template['attributes']['requested_storage'], '8Gi')
        self.assertFalse(any(n['kind'] == 'PersistentVolumeClaim' for n in graph['nodes']))
        self.assertEqual(edges(graph, 'uses StorageClass'), [('data (db)', 'fast', 'reference')])

    def test_set_selector_semantics_and_policy_versions(self):
        self.assertTrue(MAP.matches({}, {'matchExpressions': [{'key': 'tier', 'operator': 'NotIn', 'values': ['db']}]}))
        self.assertFalse(MAP.matches({}, {'matchExpressions': [{'key': 'tier', 'operator': 'In', 'values': ['api']}]}))
        modern = obj('PodDisruptionBudget', 'modern', api='policy/v1', spec={'selector': {}})
        legacy = obj('PodDisruptionBudget', 'legacy', api='policy/v1beta1', spec={'selector': {}})
        graph = MAP.Graph([workload('api'), modern, legacy]).build()
        self.assertEqual(edges(graph, 'selects for policy'), [('modern', 'api', 'selector')])

    def test_custom_cluster_scope_uses_crd_group_and_does_not_collapse_other_group(self):
        crd = obj('CustomResourceDefinition', 'widgets.example.one', namespace='', api='apiextensions.k8s.io/v1',
                  spec={'group': 'example.one', 'scope': 'Cluster', 'names': {'kind': 'Widget'}})
        graph = MAP.Graph([crd, obj('Widget', 'widget', api='example.one/v1'), obj('Widget', 'widget', api='example.two/v1')]).build()
        widgets = [n for n in graph['nodes'] if n['kind'] == 'Widget']
        self.assertEqual({n['namespace'] for n in widgets}, {'', 'test'})

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaises(MAP.MapError):
            MAP.Graph([workload('api'), workload('api')])

    def test_html_data_cannot_close_script_or_create_markup(self):
        hostile = '</script><img src=x onerror=alert(1)>'
        graph = MAP.Graph(obj('ConfigMap', hostile)).build()
        with tempfile.TemporaryDirectory() as tmp:
            MAP.write_map(graph, Path(tmp))
            text = (Path(tmp) / 'index.html').read_text()
            self.assertNotIn(hostile, text)
            self.assertIn('\\u003c/script\\u003e', text)

    def test_cli_uses_tanka_namespace_fallback_without_recording_external_variable_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app, output = root / 'app', root / 'map'
            env = app / 'environments/demo'
            env.mkdir(parents=True)
            (env / 'spec.json').write_text(json.dumps({'spec': {'namespace': 'production'}}))
            api, service = workload('api'), obj('Service', 'api-service', spec={'selector': {'app': 'api'}})
            for value in (api, service):
                value['metadata'].pop('namespace')
            def run(command, **kwargs):
                return subprocess.CompletedProcess(command, 0 if command[0] == 'tk' else 1,
                    stdout=json.dumps([api, service]) if command[0] == 'tk' else '', stderr='')
            args = ['map-kubernetes.py', '--app', str(app), '--environment', 'environments/demo',
                    '--output', str(output), '--ext-str', 'TOKEN=private-external-value']
            with patch.object(MAP.sys, 'argv', args), patch.object(MAP.subprocess, 'run', side_effect=run), redirect_stdout(io.StringIO()):
                self.assertEqual(MAP.main(), 0)
            graph = json.loads((output / 'graph.json').read_text())
            self.assertEqual(graph['source']['namespace_fallback'], 'production')
            self.assertEqual(edges(graph, 'selects workload'), [('api-service', 'api', 'selector')])
            self.assertNotIn('private-external-value', json.dumps(graph))

    def test_cli_does_not_overwrite_supplied_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'graph.json'
            original = json.dumps(obj('ConfigMap', 'config'))
            source.write_text(original)
            args = ['map-kubernetes.py', '--input', str(source), '--output', str(root)]
            with patch.object(MAP.sys, 'argv', args), redirect_stderr(io.StringIO()):
                self.assertEqual(MAP.main(), 1)
            self.assertEqual(source.read_text(), original)
