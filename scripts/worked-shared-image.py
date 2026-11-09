#!/usr/bin/env python3
"""Reproduce the reference app's shared-image change without editing or deploying it."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP_REVISION = '4a494240abc9783c6faf47db6f0f8f05e441dd40'
LIBRARY_REVISION = '10a46abb03c8a82ecc9479b036a74d5b79b00f4f'
TARGETS = ('environments/e2e-check', 'examples/prs/pr-xxx')
CONSUMERS = ('backend', 'goodjob', 'sidekiq', 'dbprepare', 'dbseed')
JOBS = ('dbprepare', 'dbseed', 'e2eRunner')
SERVICES = {
    'backendService': 'backend', 'frontendService': 'frontend',
    'searchService': 'search', 'webSocketService': 'webSocket',
    'redisService': 'redisStatefulSet', 'redisHeadless': 'redisStatefulSet',
    'elasticService': 'elasticStatefulSet', 'elasticHeadless': 'elasticStatefulSet',
}


class ExampleError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ExampleError(message)


def capture(command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    # Raw render/test errors can contain Secret values. Never include them in diagnostics.
    require(result.returncode == 0, f'{command[0]} command failed; raw output withheld')
    return result


def git(app, *arguments):
    return capture(['git', *arguments], app).stdout.strip()


def evaluate(app, command):
    result = capture(['tk', 'eval', *command], app)
    try:
        data = json.loads(result.stdout)
    except ValueError:
        raise ExampleError('tk eval produced no valid JSON; raw output withheld') from None
    require(isinstance(data, dict) and bool(data), 'tk eval produced no resource/settings map')
    return data


def render(app, target, selection=None, scoped=False, execution=None):
    prefix = '../../' + target + '/'
    settings = 'import ' + json.dumps(prefix + 'config.json')
    original = 'import ' + json.dumps(prefix + 'images.json')
    versions = original
    overrides = '(import ' + json.dumps(prefix + 'overrides.jsonnet') + ')'
    if selection is not None:
        if scoped:
            overrides += ' + ' + json.dumps({
                'backend': {'deployment': {'cont': {'app': {'tag': selection['tag']}}}},
            })
        else:
            versions = '(local original = ' + original + '; original { backend: ' + json.dumps(selection) + ' })'
    execution_code = json.dumps(execution or {})
    args = []
    for key, value in [('settings', settings), ('versions', versions), ('overrides', overrides), ('execution', execution_code)]:
        args += ['--tla-code', key + '=' + value]
    effective = evaluate(app, ['lib/e2e/values.libsonnet', *args])
    expression = '(import "values.libsonnet")(' + ','.join([settings, versions, overrides, execution_code]) + ')'
    resources = evaluate(app, ['lib/e2e/render.libsonnet', '--tla-code', 'values=' + expression])
    return effective, resources


def pod(resource):
    return resource['spec']['template']['spec']


def app_container(resource):
    containers = pod(resource)['containers']
    require(len(containers) == 1, 'reference app container contract changed')
    return containers[0]


def named_container(resource, collection, name):
    matches = [c for c in pod(resource).get(collection, []) if c['name'] == name]
    require(len(matches) == 1, 'reference init-container contract changed')
    return matches[0]


def env_entry(container, name):
    matches = [e for e in container.get('env', []) if e['name'] == name]
    require(len(matches) == 1, 'required environment entry missing or duplicated')
    return matches[0]


def fingerprint(value):
    return hashlib.md5(value.encode()).hexdigest()[:12]


def verify_relationships(resources):
    namespace = resources['namespace']['metadata']['name']
    workloads = {key: r['spec']['template']['metadata']['labels']
                 for key, r in resources.items() if r['kind'] in ('Deployment', 'StatefulSet')}
    services = {key for key, r in resources.items() if r['kind'] == 'Service'}
    require(services == set(SERVICES), 'reference Service inventory changed')
    for key, intended in SERVICES.items():
        selector = resources[key]['spec']['selector']
        matches = [name for name, labels in workloads.items()
                   if all(labels.get(k) == v for k, v in selector.items())]
        require(matches == [intended], 'Service no longer selects its intended workload: ' + key)
    for key, resource in resources.items():
        if resource['kind'] != 'Namespace':
            require(resource['metadata'].get('namespace') == namespace, 'resource namespace mismatch: ' + key)
    prepare_gate = named_container(resources['dbseed'], 'initContainers', 'prepare-ready')
    seed_gate = named_container(resources['e2eRunner'], 'initContainers', 'dbseed-ready')
    require(env_entry(prepare_gate, 'JOB_NAME')['value'] == resources['dbprepare']['metadata']['name'], 'seed points to wrong prepare Job')
    require(env_entry(seed_gate, 'JOB_NAME')['value'] == resources['dbseed']['metadata']['name'], 'runner points to wrong seed Job')
    claim = resources['rwm-pvc']['metadata']['name']
    for key in ('backend', 'goodjob', 'sidekiq', 'dbprepare', 'dbseed'):
        tmp = [v for v in pod(resources[key])['volumes'] if v['name'] == 'tmp']
        expected = {'name': 'tmp', 'persistentVolumeClaim': {'claimName': claim}} if key in CONSUMERS[:3] else {'name': 'tmp', 'emptyDir': {}}
        require(tmp == [expected], 'tmp volume ownership changed: ' + key)


def verify_change(before, after, image, prefix, execution_id=None, consumers=CONSUMERS):
    """Allow only selected images and documented Job-identity/reference changes."""
    require(set(before) == set(after), 'resource inventory changed')
    expected = deepcopy(before)
    for key in consumers:
        app_container(expected[key])['image'] = image
    named_container(expected['dbseed'], 'initContainers', 'backend-ready')['image'] = image
    backend_id = execution_id or fingerprint(image)
    prepare_name = prefix + '-prepare-' + backend_id
    seed_name = prefix + '-seed-' + backend_id
    runner_image = pod(before['e2eRunner'])['containers'][0]['image']
    frontend_image = app_container(before['frontend'])['image']
    runner_id = execution_id or fingerprint(seed_name + runner_image + frontend_image)
    for key, stage, run_id in [('dbprepare', 'prepare', backend_id), ('dbseed', 'seed', backend_id), ('e2eRunner', 'runner', runner_id)]:
        name = prefix + '-' + stage + '-' + run_id
        expected[key]['metadata']['name'] = name
        if key != 'e2eRunner':
            expected[key]['spec']['template']['metadata']['labels']['job'] = name
    env_entry(named_container(expected['dbseed'], 'initContainers', 'prepare-ready'), 'JOB_NAME')['value'] = prepare_name
    env_entry(named_container(expected['e2eRunner'], 'initContainers', 'dbseed-ready'), 'JOB_NAME')['value'] = seed_name
    for container in pod(expected['e2eRunner'])['containers']:
        env_entry(container, 'E2E_RUN_ID')['value'] = runner_id
    # Compare full objects, including Secret payloads in memory. Diagnostics expose no values.
    changed_unexpectedly = [key for key in expected if expected[key] != after[key]]
    require(not changed_unexpectedly, 'unexpected changes outside image/Job contract: ' + ', '.join(changed_unexpectedly))
    verify_relationships(after)
    return {key: {'before': before[key]['metadata']['name'], 'after': after[key]['metadata']['name']}
            for key in JOBS if before[key]['metadata']['name'] != after[key]['metadata']['name']}


def verify_stages(effective, resources, image, consumers=CONSUMERS):
    for key in consumers:
        settings = effective[key]['deployment' if key in CONSUMERS[:3] else 'job']['cont']['app']
        require(settings['image'] + settings['tag'] == image, 'effective image mismatch: ' + key)
        require(app_container(resources[key])['image'] == image, 'rendered image mismatch: ' + key)
    require(named_container(resources['dbseed'], 'initContainers', 'backend-ready')['image'] == image, 'seed readiness image mismatch')


def validate_application(app):
    # The walkthrough needs Git metadata. A local clone retains the exact commit
    # while all generated walkthroughs and fixture repositories stay disposable.
    with tempfile.TemporaryDirectory(prefix='toolkit-shared-image-') as temporary:
        destination = Path(temporary) / 'app'
        capture(['git', 'clone', '--no-hardlinks', '--no-checkout', str(app), str(destination)], app)
        capture(['git', 'checkout', '--detach', APP_REVISION], destination)
        shutil.copytree(app / 'vendor', destination / 'vendor')
        result = subprocess.run(['sh', 'scripts/validate.sh'], cwd=destination,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), text=True, capture_output=True)
        require(result.returncode == 0, 'isolated application validation failed; raw output withheld')
        match = re.search(r'Ran (\d+) tests?\b', result.stdout + result.stderr)
        require(match is not None, 'application validation did not report a test count')
        return {'command': 'sh scripts/validate.sh', 'workspace': 'temporary local clone of pinned commit and copied local vendor',
                'tests': int(match.group(1)), 'status': 'passed'}


def example(app, validate_app=False):
    require(git(app, 'rev-parse', '--show-toplevel') == str(app), 'argument must be the application Git root')
    require(git(app, 'rev-parse', 'HEAD') == APP_REVISION, 'reference revision differs; review/update the example contract before running')
    require(not git(app, 'status', '--porcelain'), 'reference application must have a clean working tree')
    lock = json.loads((app / 'jsonnetfile.lock.json').read_text())
    onehq = [d for d in lock['dependencies'] if d['source']['git']['remote'] == 'https://github.com/OneHQ/tanka-lib-k8-onehq.git']
    require(len(onehq) == 1 and onehq[0]['version'] == LIBRARY_REVISION, 'reference OneHQ lock differs')
    cases = []
    for target in TARGETS:
        config = json.loads((app / target / 'config.json').read_text())
        versions = json.loads((app / target / 'images.json').read_text())
        require(json.loads((app / target / 'execution.json').read_text()) == {}, 'default execution input must be empty')
        _, baseline = render(app, target)
        require(baseline == evaluate(app, [target + '/main.jsonnet']), 'shared renderer differs from actual main entry point')
        require(len(baseline) == 36, 'reference baseline resource count changed')
        verify_relationships(baseline)
        repository = versions['backend']['repository']
        selections = [('tag', {'repository': repository, 'tag': 'toolkit-step4'}),
                      ('digest-with-tag', {'repository': repository, 'tag': 'ignored-by-digest', 'digest': 'sha256:' + 'a' * 64})]
        for name, selection in selections:
            effective, changed = render(app, target, selection)
            image = repository + ('@' + selection['digest'] if 'digest' in selection else ':' + selection['tag'])
            require(image != app_container(baseline['backend'])['image'], 'example image must differ from baseline')
            verify_stages(effective, changed, image)
            renamed = verify_change(baseline, changed, image, config['resourcePrefix'])
            require(set(renamed) == set(JOBS), 'expected three revision-derived Job names to change')
            cases.append({'target': target, 'case': name, 'selected_backend': selection, 'resources': len(changed),
                          'image_consumers': list(CONSUMERS) + ['dbseed/init:backend-ready'],
                          'renamed_jobs': renamed, 'all_other_fields_unchanged': True, 'status': 'passed'})
        # A deliberate negative control: a backend-only override is not a shared update.
        _, scoped = render(app, target, {'tag': 'toolkit-step4'}, scoped=True)
        image = repository + ':toolkit-step4'
        try:
            verify_change(baseline, scoped, image, config['resourcePrefix'])
        except ExampleError:
            pass
        else:
            raise ExampleError('shared-image check unexpectedly accepted backend-only override')
        require(app_container(scoped['goodjob'])['image'] == app_container(baseline['goodjob'])['image'], 'negative-control GoodJob behavior changed')
        verify_change(baseline, scoped, image, config['resourcePrefix'], consumers=tuple(c for c in CONSUMERS if c != 'goodjob'))
        cases.append({'target': target, 'case': 'backend-only-control', 'shared_change_check': 'rejected as intended',
                      'goodjob': 'retains baseline image', 'status': 'passed'})
        execution = {'id': 'toolkit-step4'}
        _, pipeline_before = render(app, target, execution=execution)
        effective, pipeline_after = render(app, target, selections[0][1], execution=execution)
        verify_stages(effective, pipeline_after, image)
        renamed = verify_change(pipeline_before, pipeline_after, image, config['resourcePrefix'], execution_id=execution['id'])
        require(len(pipeline_after) == 37 and not renamed, 'fixed execution ID changed Job names or resource count')
        hooks = sorted(k for k, r in pipeline_after.items() if r['metadata'].get('annotations', {}).get('argocd.argoproj.io/hook') == 'Sync')
        require(hooks == sorted((*JOBS, 'stopDbConsumers')), 'pipeline hook inventory changed')
        cases.append({'target': target, 'case': 'fixed-execution-id', 'resources': 37, 'execution_id': execution['id'],
                      'hooks': hooks, 'renamed_jobs': renamed, 'all_other_fields_unchanged': True, 'status': 'passed'})
        print('PASS: ' + target + ' (tag, digest, backend-only control, fixed execution ID)', file=sys.stderr)
    validation = validate_application(app) if validate_app else {'status': 'not run; add --validate-app'}
    require(not git(app, 'status', '--porcelain'), 'application working tree changed during checks')
    tk_version = capture(['tk', '--version'], app)
    match = re.search(r'tk version ([^\s]+)', tk_version.stdout + tk_version.stderr)
    return {'example': 'shared-backend-image', 'status': 'passed', 'app_revision': APP_REVISION,
            'onehq_revision': LIBRARY_REVISION, 'toolkit_revision': git(ROOT, 'rev-parse', 'HEAD'),
            'toolkit_working_tree_dirty': bool(git(ROOT, 'status', '--porcelain')),
            'example_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'tanka_version': match.group(1) if match else 'unreported', 'python_version': sys.version.split()[0],
            'cases': cases, 'checks': ['actual main matches composed baseline', 'effective and rendered images',
                                     'eight intended Service relationships', 'Job completion gates', 'namespaces',
                                     'shared/private tmp volumes', 'full resource equality outside permitted differences'],
            'application_validation': validation, 'application_working_tree': 'clean before and after',
            'limits': ['synthetic image references; not registry/image-content verification',
                       'local resolved dependencies; no cluster or runtime checks', 'not a Cline pilot']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application', type=Path, help='clean checkout of the documented reference revision with vendor/ installed')
    parser.add_argument('--validate-app', action='store_true', help='also run the full offline app suite in a disposable source/dependency copy')
    args = parser.parse_args()
    try:
        report = example(args.application.resolve(), args.validate_app)
    except ExampleError as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        # Keep unexpected input/parser errors from exposing any captured values.
        print('FAIL: reference example could not complete; no raw render/test output is printed. Check the documented revision, inputs, dependencies and contracts.', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2) + '\n', end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
