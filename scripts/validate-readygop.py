#!/usr/bin/env python3
"""Revision-specific ReadyGOP offline assessment; all probes use a temporary clone."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'dac3d3a1aa316aa21ab9a0344aaaef5e28e55e35'
COUNTS = {'default': 0, 'staging': 82, 'production': 81}
RAILS = {'staging': ('railsDeploy', 'goodjobMasterDeploy'),
         'production': ('railsDeploy', 'railsDebug', 'goodjobDeploy', 'goodjobMasterDeploy')}
PGSYNC = ('pgsyncProducerDeploy', 'pgsyncConsumerDeploy', 'pgsyncReindexJob')
TAG = 'toolkit-validation'


class AssessmentError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise AssessmentError(message)


def run(command, app, input_text=None):
    return subprocess.run(command, cwd=app, input=input_text, text=True, capture_output=True)


def render(app, env, count=None):
    target = 'default' if env == 'default' else 'readygop-' + env
    result = run(['tk', 'eval', 'environments/' + target], app)
    require(result.returncode == 0, 'Render failed; raw output and diagnostics withheld')
    try:
        value = json.loads(result.stdout)
    except ValueError:
        raise AssessmentError('Render is not valid JSON; raw output withheld') from None
    require(isinstance(value, dict), 'Unexpected render shape')
    actual = sum(isinstance(r, dict) and bool(r.get('kind')) for r in value.values())
    require(actual == (COUNTS[env] if count is None else count), 'Unexpected emitted resource count')
    return value


def pod(resource):
    spec = resource['spec']
    if resource['kind'] == 'CronJob':
        spec = spec['jobTemplate']['spec']
    return spec['template']['spec']


def one_container(resource):
    containers = pod(resource)['containers']
    require(len(containers) == 1, 'Unexpected application container count')
    return containers[0]


def expected_rails(before, env, tag):
    expected = deepcopy(before)
    old_image = one_container(before['railsDeploy'])['image']
    old_tag = old_image.rsplit(':', 1)[1]
    old_name = before['migrateDBJob']['metadata']['name']
    require(old_name == 'db-migrate-' + old_tag, 'Unexpected migration identity contract')
    new_name = 'db-migrate-' + tag
    for key in RAILS[env] + ('migrateDBJob',):
        container = one_container(expected[key])
        require(container['image'] == old_image, 'Unexpected Rails image consumer')
        container['image'] = old_image.rsplit(':', 1)[0] + ':' + tag
    job = expected['migrateDBJob']
    job['metadata']['name'] = new_name
    job['spec']['template']['metadata']['labels']['job'] = new_name
    one_container(job)['name'] = new_name
    for key in RAILS[env]:
        gates = [e for c in pod(expected[key])['initContainers'] if c['name'] == 'wait-for-migrate'
                 for e in c.get('env', []) if e['name'] == 'JOB_NAME']
        require(len(gates) == 1 and gates[0]['value'] == old_name, 'Unexpected migration gate')
        gates[0]['value'] = new_name
    return expected


def expected_pgsync(before, tag):
    expected = deepcopy(before)
    old_image = one_container(before['pgsyncReindexJob'])['image']
    require('-core-' in old_image, 'Unexpected PGSync image contract')
    new_image = old_image.rsplit('-core-', 1)[0] + '-core-' + tag
    for key in PGSYNC:
        container = one_container(expected[key])
        require(container['image'] == old_image, 'Unexpected PGSync image consumer')
        container['image'] = new_image
    selected = [c for c in pod(expected['pgsyncSelectiveReindexCronJob'])['initContainers']
                if c['name'] == 'run-selective-reindex']
    require(len(selected) == 1 and selected[0]['image'] == old_image, 'Unexpected selective reindex container')
    selected[0]['image'] = new_image
    return expected


def verify_change(before, after, role, env, tag):
    require(role in ('rails', 'pgsyncCore'), 'Unsupported assessment image role')
    expected = expected_rails(before, env, tag) if role == 'rails' else expected_pgsync(before, tag)
    require(after == expected, 'Rendered difference exceeds the scoped image/identity/gate contract; raw values withheld')


def vendor_fingerprint(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_file() and not {'.git', '.tmp'}.intersection(relative.parts):
            digest.update(str(relative).encode() + b'\0' + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def relationships(value, env, mapper):
    namespace = 'readygop-' + env
    graph = mapper.Graph(value, namespace, True).build()
    require(not graph['notes'], 'Unexpected unmatched Service selection')
    objects = {key: r for key, r in value.items() if isinstance(r, dict) and r.get('kind')}
    by_id = {(r['kind'], r['metadata'].get('namespace', namespace), r['metadata']['name']): r for r in objects.values()}
    services = {'rails_svc': 'railsDeploy', 'react_svc': 'reactDeployment', 'redisService': 'redisSS',
                'elastic_svc': 'elasticSS', 'elasticHeadless_svc': 'elasticSS',
                'search_svc': 'searchDeploy', 'wSocket_svc': 'wSocketDeploy'}
    if env == 'production':
        services.update({'pgHero_svc': 'pgHeroDeploy', 'pgHeroGJ_svc': 'pgHeroGJDeploy'})
    for service, workload in services.items():
        selected = [key for key, r in objects.items() if mapper.pod_template(r) is not None
                    and all(mapper.pod_template(r)[0].get('labels', {}).get(k) == v
                            for k, v in objects[service]['spec']['selector'].items())]
        require(selected == [workload], 'Unexpected Service/Pod selection')
    duplicates, secret_checks = [], 0
    for key, resource in objects.items():
        ns = resource['metadata'].get('namespace', namespace)
        template = mapper.pod_template(resource)
        if template:
            metadata, spec = template
            if resource['kind'] == 'Deployment':
                require(all(metadata.get('labels', {}).get(k) == v for k, v in resource['spec']['selector']['matchLabels'].items()),
                        'Deployment selector does not match its Pod')
            volumes = {v['name'] for v in spec.get('volumes', [])}
            volumes.update(c['metadata']['name'] for c in resource['spec'].get('volumeClaimTemplates', []))
            for c in spec.get('containers', []) + spec.get('initContainers', []):
                for name, count in Counter(e['name'] for e in c.get('env', [])).items():
                    if count > 1:
                        duplicates.append({'resource': key, 'container': c['name'], 'env_name': name, 'count': count})
                require(all(m['name'] in volumes for m in c.get('volumeMounts', [])), 'Container mount has no declared volume or claim template')
                for e in c.get('env', []):
                    ref = e.get('valueFrom', {}).get('secretKeyRef')
                    if ref and ('Secret', ns, ref['name']) in by_id:
                        secret = by_id['Secret', ns, ref['name']]
                        require(ref['key'] in {**secret.get('data', {}), **secret.get('stringData', {})}, 'App-created Secret lacks a referenced key')
                        secret_checks += 1
        if resource['kind'] == 'Ingress':
            for rule in resource['spec']['rules']:
                for path in rule['http']['paths']:
                    backend = path['backend']['service']
                    service = by_id.get(('Service', ns, backend['name']))
                    require(service is not None, 'Ingress Service is not rendered')
                    require(any(p['port'] == backend['port'].get('number') for p in service['spec']['ports']), 'Ingress backend port mismatch')
        if resource['kind'] == 'HorizontalPodAutoscaler':
            target = resource['spec']['scaleTargetRef']
            require((target['kind'], ns, target['name']) in by_id, 'HPA target is not rendered')
        if resource['kind'] == 'RoleBinding' and resource['roleRef']['kind'] == 'Role':
            require(('Role', ns, resource['roleRef']['name']) in by_id, 'RoleBinding Role is not rendered in its namespace')
    require(duplicates == [{'resource': 'goodjobMasterDeploy', 'container': 'readygop-goodjob-master-' + env,
                            'env_name': 'IS_GOOD_JOB', 'count': 2 if env == 'staging' else 3}], 'Duplicate environment entries differ from the recorded baseline gap')
    job_name = value['pgsyncReindexJob']['metadata']['name']
    for key in PGSYNC[:2]:
        gates = [e['value'] for c in pod(value[key])['initContainers'] for e in c.get('env', []) if e['name'] == 'JOB_NAME']
        require(gates == [job_name], 'PGSync Deployment gate does not follow the rendered reindex Job')
    return {'graph': graph['summary'], 'service_selections': len(services), 'duplicate_environment_entries': duplicates,
            'app_secret_key_references_checked': secret_checks,
            'unresolved': [{k: n[k] for k in ('kind', 'namespace', 'name')} for n in graph['nodes'] if n['state'] == 'unresolved']}


def assess(app):
    require(run(['git', 'rev-parse', '--show-toplevel'], app).stdout.strip() == str(app), 'Expected an application Git root')
    require(run(['git', 'rev-parse', 'HEAD'], app).stdout.strip() == REVISION, 'Requires the documented ReadyGOP baseline revision')
    status = run(['git', 'status', '--porcelain', '--untracked-files=no'], app)
    require(status.returncode == 0 and not status.stdout, 'Tracked application files must be unchanged')
    lock = json.loads((app / 'jsonnetfile.lock.json').read_text())
    require(lock == json.loads((ROOT / 'standards/examples/readygop-dependencies.lock.json').read_text()), 'Dependency lock differs from the recorded local baseline')
    require((app / 'vendor/github.com/OneHQ/tanka-lib-k8-onehq/main.libsonnet').is_file(), 'Resolve the recorded dependencies first')
    spec = importlib.util.spec_from_file_location('mapper', ROOT / 'scripts/map-kubernetes.py')
    mapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapper)
    baseline = {env: render(app, env) for env in COUNTS}
    report = {'application_revision': REVISION, 'dependency_origin': 'existing local ignored lock and vendor; copied without network or upgrade',
              'dependency_lock': lock, 'vendor_sha256': vendor_fingerprint(app / 'vendor'),
              'toolkit_revision': run(['git', 'rev-parse', 'HEAD'], ROOT).stdout.strip(),
              'assessment_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'targets': {env: relationships(baseline[env], env, mapper) for env in ('staging', 'production')}}
    manifest = app / '.infra-team-toolkit.json'
    if manifest.is_file():
        payload = json.loads(manifest.read_text())
        for name, checksum in payload['files'].items():
            path = (app / name).resolve()
            require(path.is_relative_to(app), 'Managed file escapes application root')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == checksum, 'Installed toolkit checksum mismatch')
        report['installed_toolkit'] = {'revision': payload['revision'], 'verified_files': len(payload['files'])}
    with tempfile.TemporaryDirectory(prefix='toolkit-readygop-') as tmp:
        clone = Path(tmp) / 'app'
        require(run(['git', 'clone', '--no-hardlinks', '--quiet', str(app), str(clone)], ROOT).returncode == 0, 'Could not create isolated clone')
        require(run(['git', 'remote', 'remove', 'origin'], clone).returncode == 0, 'Could not detach validation remote')
        shutil.copytree(app / 'vendor', clone / 'vendor', symlinks=True)
        shutil.copy2(app / 'jsonnetfile.lock.json', clone / 'jsonnetfile.lock.json')
        require(all(render(clone, env) == baseline[env] for env in COUNTS), 'Installed guidance changes baseline output')
        report['image_probes'], report['capability_controls'] = {}, {}
        for env in ('staging', 'production'):
            other = 'production' if env == 'staging' else 'staging'
            version_file = clone / 'environments' / ('readygop-' + env) / (env + '-version.json')
            original = version_file.read_text()
            for role in ('rails', 'pgsyncCore'):
                pattern = r'("' + role + r'"\s*:\s*)"[^"\\]*"'
                changed_text, count = re.subn(pattern, lambda m: m.group(1) + json.dumps(TAG), original)
                require(count == 1, 'Unexpected canonical version input')
                version_file.write_text(changed_text)
                after = render(clone, env)
                verify_change(baseline[env], after, role, env, TAG)
                relationships(after, env, mapper)
                require(render(clone, other) == baseline[other] and render(clone, 'default') == {}, 'Image change affects an unrelated target')
                require(run(['git', 'diff', '--name-only'], clone).stdout.splitlines() == [str(version_file.relative_to(clone))], 'Unexpected source changes')
                require(run(['git', 'diff', '--check'], clone).returncode == 0, 'Functional diff whitespace failure')
                report['image_probes'][env + '/' + role] = {'status': 'passed', 'changed_file': str(version_file.relative_to(clone)),
                    'image_consumers': list(RAILS[env]) + ['migrateDBJob'] if role == 'rails' else list(PGSYNC) + ['pgsyncSelectiveReindexCronJob/init/run-selective-reindex'],
                    'unrelated_fields_and_other_targets_identical': True}
                version_file.write_text(original)
            values_file = version_file.parent / (env + '-values.jsonnet')
            source = values_file.read_text()
            require(source.count('pgsync.new({') == 1, 'Unexpected PGSync composition call')
            values_file.write_text(source.replace('pgsync.new({', 'pgsync.new({ enabled: false,', 1))
            require(render(clone, env) == baseline[env], 'Global enabled control differs from recorded ignored-input behavior')
            values_file.write_text(source + '\n+ { pgsyncReindex+: { enabled: false } }\n')
            partial = render(clone, env, COUNTS[env] - 1)
            expected = deepcopy(baseline[env])
            expected['pgsyncReindexJob'] = {}
            require(partial == expected, 'Partial reindex-disable control differs from recorded behavior')
            values_file.write_text(source)
            report['capability_controls'][env] = {'global_enabled_false_ignored': True,
                'component_disable_removes_only_reindex_job': True,
                'producer_and_consumer_keep_gate_to_absent_job': True}
        require(not run(['git', 'status', '--porcelain', '--untracked-files=no'], clone).stdout, 'Probe did not restore its temporary source')
        fmt = run(['tk', 'fmt', '--test', 'lib', 'environments'], clone)
        report['baseline_format'] = {'exit_code': fmt.returncode, 'raw_output_withheld': True}
        syntax, failures = Counter(), []
        for env in ('staging', 'production'):
            for key, resource in baseline[env].items():
                template = mapper.pod_template(resource) if resource.get('kind') else None
                if not template:
                    continue
                for c in template[1].get('containers', []) + template[1].get('initContainers', []):
                    command = c.get('command', [])
                    if len(command) == 3 and command[0] in ('sh', '/bin/sh', 'bash', '/bin/bash') and command[1] == '-c':
                        result = run([command[0], '-n'], clone, command[2])
                        syntax[env] += 1
                        if result.returncode:
                            failures.append({'target': env, 'resource': key, 'container': c['name'], 'exit_code': result.returncode})
        local_shell = run(['bash', '-n', 'environments/readygop-staging/scripts/extract.sh'], clone)
        report['baseline_shell_syntax'] = {'instances_checked': dict(syntax), 'failures': failures,
                                          'local_extract_script_exit_code': local_shell.returncode}
    report['status'] = 'scoped_compatibility_passed_with_baseline_gaps'
    report['limits'] = ['Local lock/vendor provenance does not establish the deployed dependency baseline or upstream byte identity',
                        'Existing duplicate env, ignored/partial disable behavior and formatting are recorded separately',
                        'No deployment, workload execution, AVP resolution, external-resource/registry/schema checks or Cline run',
                        'Graph inference is partial; hidden fields and custom policy/operator behavior are not a runtime graph']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path, help='unchanged baseline Git root with recorded lock and resolved vendor')
    args = parser.parse_args()
    try:
        report = assess(args.app.resolve())
    except AssessmentError as error:
        print('Assessment failed: ' + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        print('Assessment failed: inspect tools, paths and expected source shape; raw input/output withheld', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
