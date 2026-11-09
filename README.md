# infra-team-toolkit

Shared instructions and offline tools for infrastructure engineering with Cline,
Tanka and Jsonnet. Owner and sole maintainer: **@Darthcjba**.

The toolkit helps an engineer or agent understand an existing app, use its pinned
OneHQ constructors, make one scoped change and produce reviewable resource evidence.
Applications keep their existing layout and delivery process. OneHQ/tanka-lib-k8-onehq
remains a separate application dependency.

**Status:** development toolkit with evidence from three applications and one Cline
CLI pilot. A release remains pending. Tekton and library-update work are deferred
until the owner resumes them. Read the [team guide](docs/team-guide.md) for the full
workflow and the [review findings](docs/toolkit-review.md) for improvements and limits.

## What it provides

| Feature | What you get |
| --- | --- |
| [Rules](rules/10-source-authority.md) and [Jsonnet skill](skills/cjba-k8s-jsonnet/SKILL.md) | Consistent source precedence, constructor use, change scope and validation instructions |
| [Application standard](standards/app-infrastructure.md) and [context template](templates/AGENTS.md) | A map of actual files, canonical inputs, dependencies and checks without reorganizing the app |
| [Installer](scripts/install.py) and manifest | A pinned guidance installation, preview, conflict protection and managed-file drift checks |
| [Kubernetes mapper](standards/kubernetes-map.md) | Interactive HTML resource inspection, typed relationships, JSON and Mermaid exports |
| [Reference cases](#reference-evidence) | Reproducible, app-specific image/relationship acceptance checks and documented gaps |
| [Team guide](docs/team-guide.md) and [review template](templates/change-review.md) | A repeatable onboarding, change, verification and upgrade process |

Rendering and review stay offline. Image contents, external resources, schema/API
support and runtime readiness need the application's own checks. Deployment remains
its existing delivery procedure. Toolkit tests alone establish neither app correctness
nor production readiness.

## Start using it

### 1. Prepare the two checkouts

Obtain a reviewed toolkit commit and the application Git checkout. The owner must
publish or otherwise share that commit before teammates can fetch it; local commits
are not a release. You need Git and Python 3.9+. Rendering also needs the app's Tanka
and resolved Jsonnet dependencies; Cline work needs your approved runtime/account.

Keep the toolkit and application as separate checkouts. Application copies, vendor
directories, pilot credentials and raw logs belong outside this toolkit repository.
The reference case scripts create temporary clones for their edit probes.

### 2. Establish the application's baseline

Read its `AGENTS.md`, architecture, entry points, dependency lock/imports and existing
validation commands. Record which library implementation is actually resolved.
Map responsibilities using [the standard](standards/app-infrastructure.md), then
capture the existing offline output privately. Missing locks, hidden resources,
external ownership and known check failures belong in that baseline record.

### 3. Preview and install guidance

From the **clean toolkit root**, replace the application path:

```sh
APP_ROOT=/absolute/path/to/app-infra
python3 -B scripts/check.py
python3 -B scripts/install.py "$APP_ROOT" --dry-run
python3 -B scripts/install.py "$APP_ROOT"
python3 -B scripts/install.py "$APP_ROOT" --check
```

Preview lists planned paths without writing. Installation preflights all targets
and refuses conflicting content/symlinks. It creates:

| Installed path | Purpose |
| --- | --- |
| `.clinerules/infra-team-toolkit-*.md` | Shared rules |
| `.cline/skills/cjba-k8s-jsonnet/` | Skill and constructor/workflow references |
| `docs/infra-team-toolkit/standards/` | Contract, selected reference mappings and evidence |
| `.infra-team-toolkit.json` | Exact toolkit revision and managed-file SHA256 hashes |

Scripts, templates, the team guide, application repositories and generated maps
stay in the toolkit/work area. Installation does not fetch dependencies, configure
Cline, edit application `AGENTS.md` or change GitHub access.

### 4. Complete app context and verify agent discovery

Merge [templates/AGENTS.md](templates/AGENTS.md) into the app's instructions, preserving
existing guidance and replacing every placeholder. Include actual paths, canonical
image inputs, supported operations, external dependencies and exact offline commands.

Open the app in Cline and enable the installed rules/skill using your approved
configuration. Use the [read-only inspection prompt](docs/team-guide.md#start-with-a-read-only-inspection)
first. Verify that it reads the guidance and pinned source. Other agents, including
Codex, must read Cline-specific guidance explicitly. Review/commit adoption separately
from a functional resource change.

### 5. Make and review one change

Use the [scoped-change prompt](docs/team-guide.md#request-one-concrete-change), naming
the target and intended consumers. Follow the app's canonical input and render/check
commands. Compare complete resource objects as well as images, identities, selectors,
references, metadata and policy. Keep known baseline gaps distinct from new changes.

Record commands, results, limits and rollback in [the review template](templates/change-review.md).
The [Cline procedure](docs/team-guide.md#set-up-cline) documents the tested CLI setup;
VS Code extension use still needs its own smoke test.

### 6. Inspect a resource map

From the **toolkit root**, replace the environment with the app's actual entry point:

```sh
python3 -B scripts/map-kubernetes.py --app "$APP_ROOT" \
  --environment environments/example --output generated/kubernetes/example
```

Open `generated/kubernetes/example/index.html`; keep `graph.json` and `graph.mmd`
beside it. No server is needed. Add `--infer-env-links` for explicitly inferred
endpoint/Job links. Existing rendered JSON works with `--input /path/to/rendered.json`.
Output stays outside the application. See [coverage and controls](standards/kubernetes-map.md):
unresolved objects are absent from the input, and the diagram describes supported
declarations/heuristics rather than a complete runtime graph.

### 7. Check drift and manage upgrades

From any toolkit checkout containing this verifier:

```sh
python3 -B scripts/install.py "$APP_ROOT" --verify-installed
```

This checks the app's recorded managed-file hashes without requiring its old toolkit
checkout or a clean current toolkit. It checks manifest consistency; it does not
authenticate a modified manifest, discover unlisted files or validate Kubernetes output.

`--check` instead compares against the **current clean toolkit revision**. Use that
for adoption acceptance or comparison with a selected revision. For upgrades, first
verify the existing installation, select the new reviewed toolkit revision and follow
[the deliberate replacement/rollback procedure](docs/team-guide.md#upgrade-and-rollback).
There is no force overwrite or automatic removal of application-owned files.

## Reference evidence

These cases require their documented app revisions and dependencies. They are
regression examples, not generic validators for arbitrary apps or edited revisions.
Run commands from the **toolkit root**:

| Case | Procedure and command | Evidence scope |
| --- | --- | --- |
| Agencies E2E | [Worked example](standards/examples/shared-backend-image.md); `python3 -B scripts/worked-shared-image.py /path/to/agencieshq-e2e-infra --validate-app` | Shared image/gates, optional 107-test app suite; [one Cline CLI pilot](standards/examples/cline-pilot.md) |
| HQAdmin | [Assessment](standards/examples/hqadmin-validation.md); `python3 -B scripts/validate-hqadmin.py /path/to/isolated-hqadmin` | Different layout, shared image, unchanged production output; fresh dependency-resolution and selector gaps recorded |
| ReadyGOP | [Assessment](standards/examples/readygop-validation.md); `python3 -B scripts/validate-readygop.py /path/to/isolated-readygop` | Newer pinned interface, Rails/PGSync roles, visibility and negative disable controls; existing env/policy gaps recorded |

The supplied library snapshot remains byte-preserved. An application's resolved
implementation takes precedence. Future library upgrades need a separate compatibility
review and new evidence; historical passing results retain their original scope.

## Maintain the toolkit

```sh
python3 -B scripts/check.py
python3 -B -m unittest discover -s tests -v
git diff --check
```

Checks cover structure, skill references, authored local file links and installed
documentation links; they do not query external URLs. See [scripts](scripts/README.md),
[review findings](docs/toolkit-review.md), [contributing](CONTRIBUTING.md),
[governance](GOVERNANCE.md) and [ownership](.github/CODEOWNERS). Darthcjba reviews,
publishes and tags releases when ready. Repository access is configured separately.
