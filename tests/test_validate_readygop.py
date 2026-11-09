"""Reject missed consumers, hidden-resource activation and unsafe review output."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('readygop', Path(__file__).resolve().parents[1] / 'scripts/validate-readygop.py')
RG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RG)


def workload(kind, name, image):
    template = {'metadata': {'labels': {'job': 'db-migrate-before'}}, 'spec': {
        'containers': [{'name': name, 'image': image}],
        'initContainers': [{'name': 'wait-for-migrate', 'env': [{'name': 'JOB_NAME', 'value': 'db-migrate-before'}]}]}}
    spec = {'template': template}
    if kind == 'CronJob':
        spec = {'jobTemplate': {'spec': spec}}
    return {'kind': kind, 'metadata': {'name': name}, 'spec': spec}


def baseline(env):
    value = {k: workload('Deployment', k, 'example.invalid/rails:before') for k in RG.RAILS[env]}
    value['migrateDBJob'] = workload('Job', 'db-migrate-before', 'example.invalid/rails:before')
    for key in RG.PGSYNC:
        value[key] = workload('Job' if key.endswith('Job') else 'Deployment', key,
                              'example.invalid/pgsync:readygop-fixed-core-0.0.3')
    value['pgsyncSelectiveReindexCronJob'] = workload('CronJob', 'selective', 'example.invalid/cli:fixed')
    RG.pod(value['pgsyncSelectiveReindexCronJob'])['initContainers'] = [
        {'name': 'run-selective-reindex', 'image': 'example.invalid/pgsync:readygop-fixed-core-0.0.3'}]
    value['secret'] = {'kind': 'Secret', 'data': {'TOKEN': 'private-before'}}
    return value


class ReadyGOPAssessmentTests(unittest.TestCase):
    def test_production_worker_kept_on_old_image_is_rejected(self):
        before = baseline('production')
        after = RG.expected_rails(before, 'production', 'after')
        RG.one_container(after['goodjobDeploy'])['image'] = 'example.invalid/rails:before'
        with self.assertRaises(RG.AssessmentError):
            RG.verify_change(before, after, 'rails', 'production', 'after')

    def test_staging_hidden_worker_activation_is_rejected(self):
        before = baseline('staging')
        after = RG.expected_rails(before, 'staging', 'after')
        after['goodjobDeploy'] = deepcopy(after['goodjobMasterDeploy'])
        with self.assertRaises(RG.AssessmentError):
            RG.verify_change(before, after, 'rails', 'staging', 'after')

    def test_stale_production_debug_gate_is_rejected(self):
        before = baseline('production')
        after = RG.expected_rails(before, 'production', 'after')
        RG.pod(after['railsDebug'])['initContainers'][0]['env'][0]['value'] = 'db-migrate-before'
        with self.assertRaises(RG.AssessmentError):
            RG.verify_change(before, after, 'rails', 'production', 'after')

    def test_selective_reindex_init_image_must_follow_pgsync(self):
        before = baseline('staging')
        after = RG.expected_pgsync(before, 'after')
        RG.pod(after['pgsyncSelectiveReindexCronJob'])['initContainers'][0]['image'] = 'example.invalid/pgsync:readygop-fixed-core-0.0.3'
        with self.assertRaises(RG.AssessmentError):
            RG.verify_change(before, after, 'pgsyncCore', 'staging', 'after')

    def test_pgsync_fixed_job_name_cannot_change_in_image_probe(self):
        before = baseline('production')
        after = RG.expected_pgsync(before, 'after')
        after['pgsyncReindexJob']['metadata']['name'] = 'another-name'
        with self.assertRaises(RG.AssessmentError):
            RG.verify_change(before, after, 'pgsyncCore', 'production', 'after')

    def test_secret_change_rejected_without_values(self):
        before = baseline('staging')
        after = RG.expected_pgsync(before, 'after')
        after['secret']['data']['TOKEN'] = 'private-after'
        with self.assertRaises(RG.AssessmentError) as error:
            RG.verify_change(before, after, 'pgsyncCore', 'staging', 'after')
        self.assertNotIn('private-before', str(error.exception))
        self.assertNotIn('private-after', str(error.exception))

    def test_failed_render_hides_both_output_streams(self):
        failed = subprocess.CompletedProcess(['tk'], 1, stdout='private-stdout', stderr='private-stderr')
        with patch.object(RG.subprocess, 'run', return_value=failed), self.assertRaises(RG.AssessmentError) as error:
            RG.render(Path('.'), 'staging')
        self.assertNotIn('private-stdout', str(error.exception))
        self.assertNotIn('private-stderr', str(error.exception))

    def test_empty_successful_output_is_rejected(self):
        empty = subprocess.CompletedProcess(['tk'], 0, stdout='{}', stderr='')
        with patch.object(RG.subprocess, 'run', return_value=empty), self.assertRaises(RG.AssessmentError):
            RG.render(Path('.'), 'production')


if __name__ == '__main__':
    unittest.main()
