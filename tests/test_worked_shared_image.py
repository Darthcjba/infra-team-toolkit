"""Exercise the worked example's rejection of partial and unrelated changes."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('worked_image', Path(__file__).resolve().parents[1] / 'scripts/worked-shared-image.py')
EXAMPLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXAMPLE)


def fixture():
    resources = {'namespace': {'kind': 'Namespace', 'metadata': {'name': 'reference-ns'}},
                 'rwm-pvc': {'kind': 'PersistentVolumeClaim', 'metadata': {'name': 'shared-tmp', 'namespace': 'reference-ns'}},
                 'credential': {'kind': 'Secret', 'metadata': {'name': 'credential', 'namespace': 'reference-ns'},
                                'data': {'TOKEN': 'private-fixture-value'}}}
    workloads = ('backend', 'goodjob', 'sidekiq', 'frontend', 'search', 'webSocket', 'redisStatefulSet', 'elasticStatefulSet')
    for name in (*workloads, *EXAMPLE.JOBS):
        job = name in EXAMPLE.JOBS
        resources[name] = {
            'kind': 'Job' if job else ('StatefulSet' if name.endswith('StatefulSet') else 'Deployment'),
            'metadata': {'name': name, 'namespace': 'reference-ns'},
            'spec': {'replicas': 1, 'template': {'metadata': {'labels': {'app': name}},
                     'spec': {'containers': [{'name': name, 'image': 'example.invalid/backend:before', 'env': []}],
                              'initContainers': [], 'volumes': []}}},
        }
    for name, stage in [('dbprepare', 'prepare'), ('dbseed', 'seed'), ('e2eRunner', 'runner')]:
        resources[name]['metadata']['name'] = 'ref-' + stage + '-fixed-run'
        if name != 'e2eRunner':
            resources[name]['spec']['template']['metadata']['labels']['job'] = resources[name]['metadata']['name']
    for name in EXAMPLE.CONSUMERS:
        EXAMPLE.pod(resources[name])['volumes'] = [
            {'name': 'tmp', 'persistentVolumeClaim': {'claimName': 'shared-tmp'}} if name in EXAMPLE.CONSUMERS[:3]
            else {'name': 'tmp', 'emptyDir': {}}
        ]
    EXAMPLE.pod(resources['dbseed'])['initContainers'] = [
        {'name': 'prepare-ready', 'image': 'example.invalid/kubectl:test',
         'env': [{'name': 'JOB_NAME', 'value': 'ref-prepare-fixed-run'}]},
        {'name': 'backend-ready', 'image': 'example.invalid/backend:before'},
    ]
    EXAMPLE.pod(resources['e2eRunner'])['initContainers'] = [
        {'name': 'dbseed-ready', 'env': [{'name': 'JOB_NAME', 'value': 'ref-seed-fixed-run'}]},
    ]
    EXAMPLE.pod(resources['e2eRunner'])['containers'] = [
        {'name': group, 'image': 'example.invalid/runner:test', 'env': [{'name': 'E2E_RUN_ID', 'value': 'fixed-run'}]}
        for group in ('group-1', 'group-2')
    ]
    for name, workload in EXAMPLE.SERVICES.items():
        resources[name] = {'kind': 'Service', 'metadata': {'name': name, 'namespace': 'reference-ns'},
                           'spec': {'selector': {'app': workload}}}
    return resources


class WorkedImageContracts(unittest.TestCase):
    def setUp(self):
        self.before = fixture()
        self.after = deepcopy(self.before)
        self.image = 'example.invalid/backend:after'
        for name in EXAMPLE.CONSUMERS:
            EXAMPLE.app_container(self.after[name])['image'] = self.image
        EXAMPLE.named_container(self.after['dbseed'], 'initContainers', 'backend-ready')['image'] = self.image

    def check(self):
        return EXAMPLE.verify_change(self.before, self.after, self.image, 'ref', execution_id='fixed-run')

    def test_shared_update_with_fixed_execution_preserves_identity_and_does_not_mutate_baseline(self):
        original = deepcopy(self.before)
        self.assertEqual(self.check(), {})
        self.assertEqual(self.before, original)

    def test_partial_worker_update_is_rejected(self):
        EXAMPLE.app_container(self.after['goodjob'])['image'] = 'example.invalid/backend:before'
        with self.assertRaises(EXAMPLE.ExampleError):
            self.check()

    def test_seed_readiness_image_is_required(self):
        EXAMPLE.named_container(self.after['dbseed'], 'initContainers', 'backend-ready')['image'] = 'example.invalid/backend:before'
        with self.assertRaises(EXAMPLE.ExampleError):
            self.check()

    def test_unrelated_scaling_change_is_rejected(self):
        self.after['backend']['spec']['replicas'] = 3
        with self.assertRaises(EXAMPLE.ExampleError):
            self.check()

    def test_secret_difference_is_rejected_without_disclosing_values(self):
        self.after['credential']['data']['TOKEN'] = 'another-private-value'
        with self.assertRaises(EXAMPLE.ExampleError) as error:
            self.check()
        self.assertNotIn('private-fixture-value', str(error.exception))
        self.assertNotIn('another-private-value', str(error.exception))

    def test_bad_service_selector_is_rejected_even_if_baseline_has_same_error(self):
        for data in (self.before, self.after):
            data['backendService']['spec']['selector'] = {'app': 'goodjob'}
        with self.assertRaises(EXAMPLE.ExampleError):
            self.check()

    def test_broken_seed_gate_is_rejected(self):
        EXAMPLE.named_container(self.after['dbseed'], 'initContainers', 'prepare-ready')['env'][0]['value'] = 'another-job'
        with self.assertRaises(EXAMPLE.ExampleError):
            self.check()

    def test_image_derived_jobs_cannot_retain_fixed_execution_names(self):
        with self.assertRaises(EXAMPLE.ExampleError):
            EXAMPLE.verify_change(self.before, self.after, self.image, 'ref')

    def test_failed_renderer_does_not_disclose_stdout_or_stderr(self):
        failed = subprocess.CompletedProcess(['tk'], 1, stdout='private-output', stderr='private-error')
        with patch.object(EXAMPLE.subprocess, 'run', return_value=failed), self.assertRaises(EXAMPLE.ExampleError) as error:
            EXAMPLE.capture(['tk', 'eval', 'main.jsonnet'], Path('.'))
        self.assertNotIn('private-output', str(error.exception))
        self.assertNotIn('private-error', str(error.exception))

    def test_empty_renderer_output_cannot_count_as_success(self):
        empty = subprocess.CompletedProcess(['tk'], 0, stdout='', stderr='')
        with patch.object(EXAMPLE.subprocess, 'run', return_value=empty), self.assertRaises(EXAMPLE.ExampleError):
            EXAMPLE.evaluate(Path('.'), ['main.jsonnet'])
