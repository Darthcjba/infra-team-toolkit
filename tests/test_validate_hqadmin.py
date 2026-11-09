"""Protect the second-app assessment from partial updates and secret disclosure."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('hqadmin', Path(__file__).resolve().parents[1] / 'scripts/validate-hqadmin.py')
HQ = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HQ)


def baseline():
    result = {'secret': {'data': {'TOKEN': 'private-before'}}}
    job_name = 'ns-hqadmin-v4-db-migrate-before'
    for key in HQ.DEPLOYMENTS + ('migrateDBJob',):
        result[key] = {'metadata': {'name': job_name if key == 'migrateDBJob' else key},
                       'spec': {'replicas': 1, 'template': {
                           'metadata': {'labels': {'job': job_name}},
                           'spec': {'containers': [{'name': job_name if key == 'migrateDBJob' else key,
                                                    'image': 'example.invalid/hqadmin:before'}],
                                    'initContainers': [{'name': 'wait-for-migrate',
                                                        'env': [{'name': 'JOB_NAME', 'value': job_name}]}]}}}}
    return result


class HQAdminAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.before = baseline()
        self.after = HQ.expected_change(self.before, 'after')

    def check(self):
        HQ.verify_change(self.before, self.after, 'after')

    def test_worker_kept_on_old_image_is_rejected(self):
        HQ.pod(self.after['goodjobMasterDeploy'])['containers'][0]['image'] = 'example.invalid/hqadmin:before'
        with self.assertRaises(HQ.AssessmentError):
            self.check()

    def test_stale_job_gate_is_rejected(self):
        HQ.pod(self.after['backendDebugDeploy'])['initContainers'][0]['env'][0]['value'] = 'old-job'
        with self.assertRaises(HQ.AssessmentError):
            self.check()

    def test_migration_container_must_follow_job_identity(self):
        HQ.pod(self.after['migrateDBJob'])['containers'][0]['name'] = HQ.pod(self.before['migrateDBJob'])['containers'][0]['name']
        with self.assertRaises(HQ.AssessmentError):
            self.check()

    def test_unrelated_policy_change_is_rejected(self):
        self.after['backendDeploy']['spec']['replicas'] = 5
        with self.assertRaises(HQ.AssessmentError):
            self.check()

    def test_secret_change_is_rejected_without_values(self):
        self.after['secret']['data']['TOKEN'] = 'private-after'
        with self.assertRaises(HQ.AssessmentError) as error:
            self.check()
        self.assertNotIn('private-before', str(error.exception))
        self.assertNotIn('private-after', str(error.exception))

    def test_failed_render_hides_both_output_streams(self):
        failed = subprocess.CompletedProcess(['tk'], 1, stdout='private-stdout', stderr='private-stderr')
        with patch.object(HQ.subprocess, 'run', return_value=failed), self.assertRaises(HQ.AssessmentError) as error:
            HQ.render(Path('.'), 'hqadmin-staging')
        self.assertNotIn('private-stdout', str(error.exception))
        self.assertNotIn('private-stderr', str(error.exception))

    def test_empty_successful_render_is_rejected(self):
        empty = subprocess.CompletedProcess(['tk'], 0, stdout='{}', stderr='')
        with patch.object(HQ.subprocess, 'run', return_value=empty), self.assertRaises(HQ.AssessmentError):
            HQ.render(Path('.'), 'hqadmin-staging')


if __name__ == '__main__':
    unittest.main()
