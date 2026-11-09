#!/usr/bin/env python3
"""Offline, revision-specific HQAdmin compatibility assessment; never deploys."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP_REVISION = '79c5225d25ebd8b93b9bc10a92ba4dfd46ed55e0'
TARGETS = ('default', 'hqadmin-staging', 'hqadmin-production')
DEPLOYMENTS = ('backendDeploy', 'backendDebugDeploy', 'goodjobDeploy', 'goodjobMasterDeploy')
NEW_TAG = 'toolkit-validation'


class AssessmentError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise AssessmentError(message)


def run(command, app, input_text=None):
    return subprocess.run(command, cwd=app, input=input_text, text=True, capture_output=True)


def render(app, target):
    result = run(['tk', 'eval', 'environments/' + target], app)
    require(result.returncode == 0, 'Render failed; raw diagnostics withheld because they may contain credentials')
    try:
        value = json.loads(result.stdout)
    except ValueError:
        raise AssessmentError('Render did not return valid JSON; raw output withheld') from None
    require(isinstance(value, dict), 'Unexpected render shape')
    require(len(value) == (0 if target == 'default' else 37), 'Unexpected baseline resource count')
    return value


def pod(resource):
    return resource['spec']['template']['spec']


def expected_change(before, tag):
    """Allow five images, migration identity/label/container and four Job gates only."""
    expected = deepcopy(before)
    old_name = before['migrateDBJob']['metadata']['name']
    old_image = pod(before['backendDeploy'])['containers'][0]['image']
    old_tag = old_image.rsplit(':', 1)[1]
    require(old_name.endswith('-' + old_tag), 'Migration name does not follow the inspected tag contract')
    new_name = old_name[:-len(old_tag)] + tag
    new_image = old_image.rsplit(':', 1)[0] + ':' + tag
    for key in DEPLOYMENTS + ('migrateDBJob',):
        containers = pod(expected[key])['containers']
        require(len(containers) == 1 and containers[0]['image'] == old_image,
                'Unexpected backend image consumers')
        containers[0]['image'] = new_image
    migration = expected['migrateDBJob']
    migration['metadata']['name'] = new_name
    migration['spec']['template']['metadata']['labels']['job'] = new_name
    pod(migration)['containers'][0]['name'] = new_name
    for key in DEPLOYMENTS:
        gates = [e for c in pod(expected[key])['initContainers'] if c['name'] == 'wait-for-migrate'
                 for e in c['env'] if e['name'] == 'JOB_NAME']
        require(len(gates) == 1 and gates[0]['value'] == old_name, 'Unexpected migration gate')
        gates[0]['value'] = new_name
    return expected


def verify_change(before, after, tag):
    require(after == expected_change(before, tag),
            'Rendered change differs from the image/name/gate allowlist; raw resources withheld')


def relationships(value, namespace, mapper):
    graph = mapper.Graph(value, namespace, True).build()
    require(not graph['notes'], 'Unexpected unmatched Service selector')
    expected_services = {'backendSvc': ('backendDeploy', 'migrateDBJob'), 'frontendSvc': ('frontendDeploy',),
                         'elastic_svc': ('elasticSS',), 'search_svc': ('searchDeploy',), 'wSocket_svc': ('wSocketDeploy',)}
    for service, workloads in expected_services.items():
        selected = [r['metadata']['name'] for r in value.values() if mapper.pod_template(r) is not None
                    and all(mapper.pod_template(r)[0].get('labels', {}).get(k) == v
                            for k, v in value[service]['spec']['selector'].items())]
        require(sorted(selected) == sorted(value[w]['metadata']['name'] for w in workloads), 'Unexpected Service/Pod selection')
    by_name = {(r['kind'], r['metadata']['name']): r for r in value.values()}
    secret_checks = 0
    for resource in value.values():
        require(resource['metadata'].get('namespace', namespace) == namespace, 'Unexpected resource namespace')
        if resource['kind'] == 'Deployment':
            require(resource['spec']['selector']['matchLabels'] == resource['spec']['template']['metadata']['labels'],
                    'Deployment selector differs from its Pod labels')
        template = mapper.pod_template(resource)
        if template:
            _, spec = template
            volume_names = {v['name'] for v in spec.get('volumes', [])}
            for c in spec.get('containers', []) + spec.get('initContainers', []):
                require(len({e['name'] for e in c.get('env', [])}) == len(c.get('env', [])), 'Duplicate environment names')
                require(all(v['name'] in volume_names for v in c.get('volumeMounts', [])
                            if resource['kind'] != 'StatefulSet'), 'Container mount has no volume')
                for e in c.get('env', []):
                    ref = e.get('valueFrom', {}).get('secretKeyRef')
                    if ref and ('Secret', ref['name']) in by_name:
                        secret = by_name['Secret', ref['name']]
                        require(ref['key'] in {**secret.get('data', {}), **secret.get('stringData', {})},
                                'App-created Secret lacks a referenced key')
                        secret_checks += 1
        if resource['kind'] == 'Ingress':
            for rule in resource['spec']['rules']:
                for path in rule['http']['paths']:
                    backend = path['backend']['service']
                    require(('Service', backend['name']) in by_name, 'Ingress Service is not rendered')
                    ports = by_name['Service', backend['name']]['spec']['ports']
                    require(any(p.get('port') == backend['port'].get('number') for p in ports), 'Ingress port mismatch')
        if resource['kind'] == 'HorizontalPodAutoscaler':
            ref = resource['spec']['scaleTargetRef']
            require((ref['kind'], ref['name']) in by_name, 'HPA target is not rendered')
        if resource['kind'] == 'RoleBinding':
            require(('Role', resource['roleRef']['name']) in by_name, 'RoleBinding role is not rendered')
    return {'graph': graph['summary'], 'service_selections': len(expected_services),
            'baseline_service_overlap': {'backendSvc': ['backendDeploy', 'migrateDBJob']},
            'app_secret_key_references_checked': secret_checks,
            'unresolved': [{k: n[k] for k in ('kind', 'namespace', 'name')}
                           for n in graph['nodes'] if n['state'] == 'unresolved']}


def assess(app):
    require(run(['git', 'rev-parse', '--show-toplevel'], app).stdout.strip() == str(app), 'Expected an application Git root')
    require(run(['git', 'rev-parse', 'HEAD'], app).stdout.strip() == APP_REVISION, 'Requires the documented HQAdmin baseline revision')
    status = run(['git', 'status', '--porcelain', '--untracked-files=no'], app)
    require(status.returncode == 0 and not status.stdout, 'Tracked application files must be unchanged')
    lock = json.loads((app / 'jsonnetfile.lock.json').read_text())
    recorded_lock = json.loads((ROOT / 'standards/examples/hqadmin-dependencies.lock.json').read_text())
    require(lock == recorded_lock, 'Resolved dependency lock differs from the recorded assessment')
    require((app / 'vendor/github.com/OneHQ/tanka-lib-k8-onehq/main.libsonnet').is_file(), 'Resolve the recorded dependencies first')
    spec = importlib.util.spec_from_file_location('kubernetes_mapper', ROOT / 'scripts/map-kubernetes.py')
    mapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapper)
    baseline = {target: render(app, target) for target in TARGETS}
    report = {'application_revision': APP_REVISION, 'dependency_lock': lock,
              'toolkit_revision': run(['git', 'rev-parse', 'HEAD'], ROOT).stdout.strip(),
              'assessment_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'targets': {t: relationships(baseline[t], t.replace('hqadmin-', 'iamhq-'), mapper)
                          for t in TARGETS if t != 'default'}}
    manifest_path = app / '.infra-team-toolkit.json'
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        for name, checksum in manifest['files'].items():
            path = (app / name).resolve()
            require(path.is_relative_to(app), 'Managed file escapes the application root')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == checksum, 'Installed toolkit checksum mismatch')
        report['installed_toolkit'] = {'revision': manifest['revision'], 'verified_files': len(manifest['files'])}
    with tempfile.TemporaryDirectory(prefix='toolkit-hqadmin-') as tmp:
        clone = Path(tmp) / 'app'
        result = run(['git', 'clone', '--no-hardlinks', '--quiet', str(app), str(clone)], ROOT)
        require(result.returncode == 0, 'Could not create isolated validation clone')
        require(run(['git', 'remote', 'remove', 'origin'], clone).returncode == 0, 'Could not detach validation remote')
        shutil.copytree(app / 'vendor', clone / 'vendor', symlinks=True)
        shutil.copy2(app / 'jsonnetfile.lock.json', clone / 'jsonnetfile.lock.json')
        require(all(render(clone, t) == baseline[t] for t in TARGETS), 'Installed context changes baseline output')
        version_file = clone / 'environments/hqadmin-staging/staging-version.json'
        original = version_file.read_text()
        version = json.loads(original)
        version['backend'] = NEW_TAG
        version_file.write_text(json.dumps(version, indent=2) + '\n')
        changed = render(clone, 'hqadmin-staging')
        verify_change(baseline['hqadmin-staging'], changed, NEW_TAG)
        relationships(changed, 'iamhq-staging', mapper)
        require(render(clone, 'hqadmin-production') == baseline['hqadmin-production'], 'Staging change affects production')
        require(render(clone, 'default') == {}, 'Default entry point changed')
        diff_files = run(['git', 'diff', '--name-only'], clone).stdout.splitlines()
        require(diff_files == ['environments/hqadmin-staging/staging-version.json'], 'Unexpected application file changes')
        require(run(['git', 'diff', '--check'], clone).returncode == 0, 'Functional diff has whitespace errors')
        report['shared_image'] = {'status': 'passed', 'tag': NEW_TAG, 'changed_files': diff_files,
                                  'image_consumers': list(DEPLOYMENTS) + ['migrateDBJob'],
                                  'migration_identity_and_four_gates_follow': True,
                                  'unrelated_fields_identical': True, 'production_identical': True,
                                  'default_identical': True}
        version_file.write_text(original)
        values_file = clone / 'environments/hqadmin-staging/staging-values.jsonnet'
        source = values_file.read_text()
        require(source.count('tag: tags.backend,') == 2, 'Unexpected component tag declarations')
        values_file.write_text(source.replace('tag: tags.backend,', "tag: 'toolkit-component-only',", 1))
        negative = render(clone, 'hqadmin-staging')
        expected = deepcopy(baseline['hqadmin-staging'])
        for key in DEPLOYMENTS:
            container = pod(expected[key])['containers'][0]
            container['image'] = container['image'].rsplit(':', 1)[0] + ':toolkit-component-only'
        require(negative == expected, 'Component-only control has unexpected propagation')
        values_file.write_text(source)
        report['component_only_control'] = {'status': 'passed', 'deployments_follow': list(DEPLOYMENTS),
                                             'migration_and_gates_keep_canonical_tag': True}
        fmt = run(['tk', 'fmt', '--test', 'lib', 'environments'], clone)
        report['existing_format_check'] = {'exit_code': fmt.returncode, 'raw_output_withheld': True}
        syntax = Counter()
        for target in TARGETS[1:]:
            for resource in baseline[target].values():
                template = mapper.pod_template(resource)
                if not template:
                    continue
                for c in template[1].get('containers', []) + template[1].get('initContainers', []):
                    command = c.get('command', [])
                    if len(command) == 3 and command[0] in ('sh', '/bin/sh', 'bash', '/bin/bash') and command[1] == '-c':
                        result = run([command[0], '-n'], clone, command[2])
                        require(result.returncode == 0, 'Embedded shell syntax check failed; raw command withheld')
                        syntax[target] += 1
        report['embedded_shell_syntax'] = dict(syntax)
    report['status'] = 'scoped_compatibility_passed_with_baseline_gaps'
    report['limits'] = ['Fresh resolution of declared refs, not a recovered production dependency lock',
                        'Existing formatting result reported separately from scoped acceptance',
                        'No Kubernetes schema, cluster, registry, AVP resolution, runtime or Cline run',
                        'Unresolved references require ownership/existence verification outside this offline assessment']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path, help='baseline Git root with recorded lock and vendor dependencies already installed')
    args = parser.parse_args()
    try:
        report = assess(args.app.resolve())
    except AssessmentError as error:
        print('Assessment failed: ' + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        print('Assessment failed: inspect paths, dependencies and expected source shape; raw output withheld', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
