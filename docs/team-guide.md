# infra-team-toolkit: team guide

Use this guide to adopt the toolkit in an infrastructure repository, make scoped changes with Cline, inspect resource maps and review the results. It is written for engineers who have not read the project conversation.

Owner and sole toolkit maintainer: **Darthcjba**. This guide does not change repository access, review ownership or application delivery permissions. See [governance](../GOVERNANCE.md) and [contributing](../CONTRIBUTING.md) for maintenance decisions.

**Current evidence:** one Tanka/Jsonnet application, one shared-backend-image worked example and one Cline CLI pilot have passed. Existing application layouts remain supported through a file-responsibility mapping. A second application assessment, a release, a VS Code extension pilot and a separate Tekton procedure remain pending. The reference application's sizes, names, capabilities and directory structure are examples, not defaults for every app.

## Contents

- [What the toolkit provides](#what-the-toolkit-provides)
- [Prerequisites](#prerequisites)
- [One-time application onboarding](#one-time-application-onboarding)
- [Set up Cline](#set-up-cline)
- [Everyday change workflow](#everyday-change-workflow)
- [Practice with the worked example](#practice-with-the-worked-example)
- [Generate a Kubernetes resource map](#generate-a-kubernetes-resource-map)
- [Review and share evidence](#review-and-share-evidence)
- [Upgrade and rollback](#upgrade-and-rollback)
- [Troubleshooting](#troubleshooting)
- [Maintaining this guide](#maintaining-this-guide)

## What the toolkit provides

| Part | How you use it |
| --- | --- |
| `rules/` | Cross-project instructions about source authority, change scope and validation |
| `skills/cjba-k8s-jsonnet/` | Constructor guidance, application workflow and revision compatibility references |
| `standards/` | Responsibility boundaries, reference mappings and acceptance/evidence records |
| `templates/` | Starting points for application context, a change review and the recorded pilot task |
| `scripts/install.py` | Conservative installation and installed-file checksum checks |
| `scripts/worked-shared-image.py` | Reference-specific worked-change checks, with optional isolated app validation |
| `scripts/map-kubernetes.py` | An offline diagram with attributes and typed resource relationships |

The OneHQ constructor library is a separate, application-pinned dependency. Toolkit installation does not install binaries or dependencies, authenticate Cline, edit `AGENTS.md`, deploy infrastructure or configure GitHub permissions. Scripts/templates stay in the toolkit checkout; the installer copies only rules, the Jsonnet skill and standards into the app.

## Prerequisites

Before onboarding, obtain the application repository, its owner-supported render/check commands and a reviewed toolkit commit available to your team. Ask Darthcjba for the revision to adopt. Local development commits must be published or otherwise made available by the owner before another teammate can fetch them; no release tag is currently implied.

The toolkit repository is `https://github.com/Darthcjba/infra-team-toolkit.git`. Clone it using your own authorized Git access, then select the owner-provided reviewed commit. Record `git rev-parse HEAD`; do not silently follow a moving branch for an installed consumer.

| Tool/access | Needed for |
| --- | --- |
| Git and Python 3.9+ | Toolkit setup, installer and mapping tools; no third-party Python packages |
| App-documented Tanka (`tk`) and jsonnet-bundler (`jb`) | Rendering and locked dependencies for Tanka apps |
| Access to the private OneHQ library, where required | Installing the application's existing dependency lock |
| Python 3.10+ and Ruby | The reference app's full validation; other apps define their own prerequisites |
| Approved Cline runtime and your own approved provider/account | Agent-assisted tasks; not required for using the map or installer |

Keep two checkouts: the toolkit and the application. This guide's command examples assume sibling folders named `infra-team-toolkit/` and `app-infra/`. Substitute your actual application path. Run commands from the stated working directory; do not copy a reference environment name into another app without checking it.

For the recorded reference app, a fresh checkout uses `jb install` from the app root. Keep the lockfile intact. The toolkit does not guess a new Kubernetes/OneHQ version or upgrade it during adoption.

## One-time application onboarding

### 1. Establish the existing baseline

From the **application root**, read its `AGENTS.md` and architecture notes. Locate the actual entry points, defaults, environment inputs, composition, metadata, scripts and checks. If guidance is missing, inspect source before filling it in.

Run the app's existing offline render/check commands and record the target, required variables, dependency revision and known limitations. Preserve the known-correct resource output. Different layouts do not require a directory migration.

Create a focused application branch for adoption. Keep this installation separate from a functional image/resource change so reviewers can distinguish the two.

### 2. Check and install the pinned toolkit

From the **clean, reviewed toolkit checkout**:

```sh
git status --short
git rev-parse HEAD
python3 -B scripts/check.py
python3 -B scripts/install.py ../app-infra
python3 -B scripts/install.py ../app-infra --check
```

The installer refuses a dirty toolkit checkout. The application argument must be the application's Git working-tree root. It checks all destinations before writing and refuses conflicting content and symlink destinations; it has no force-overwrite option.

Review these installed paths in the application:

| Application path | Meaning |
| --- | --- |
| `.clinerules/infra-team-toolkit-*.md` | Managed shared rules |
| `.cline/skills/cjba-k8s-jsonnet/` | Managed skill and references |
| `docs/infra-team-toolkit/standards/` | Managed standards/examples |
| `.infra-team-toolkit.json` | Exact toolkit revision and managed-file hashes |

The managed-file count depends on the selected revision. A successful `--check` verifies that revision's expected files; it does not validate the app's Kubernetes resources.

### 3. Complete application context

Manually merge [templates/AGENTS.md](../templates/AGENTS.md) into the application's existing guidance. Preserve existing instructions. Replace every placeholder with actual paths and commands before relying on the file.

At minimum, document:

- Owner, baseline revision/targets and file-to-responsibility map.
- Locked library imports, supported helper interfaces and required tools.
- Canonical shared inputs, intended consumers and merge/derivation stages.
- Array/null semantics, supported capabilities and known override limitations.
- Stable identities, selectors, generated/external credentials/accounts/storage and expected revision-derived Job names.
- Metadata/native patch locations, script side effects, exact offline checks and the separate delivery process.

The [application contract](../standards/app-infrastructure.md) explains those responsibilities. The [reference mapping](../standards/reference-applications/agencieshq-e2e-infra.md) shows a completed mapping without requiring its layout. Read guidance explicitly when changing agents; Codex and other tools do not necessarily auto-load Cline-specific paths.

### 4. Review and commit adoption

From the **application root**:

```sh
git status --short
git diff --stat
git diff --check
```

Review newly added/untracked guidance too, since an unstaged `git diff` does not display new files. Confirm the manifest pin/checksums, rerun appropriate app checks, then commit the adoption through the app's existing workflow. Keep secret payloads, raw render output, credentials and local provider settings out of that commit.

The supplied source snapshot contains inherited whitespace. If an adoption-wide whitespace check flags that exact preserved file, verify its checksum and record the exception. Do not reformat the snapshot just to make a copied-file check quiet. Functional task diffs still need their own normal checks.

## Set up Cline

Use your own approved account and model. Never copy another engineer's authentication state. The tested CLI setup was Cline **3.0.74**, provider `openai-codex`, requested model `gpt-6.1-sol`, medium effort; that is a historical test configuration, not a permanent “latest” alias or a requirement for every teammate.

Use the [official Cline CLI installation instructions](https://github.com/cline/cline/blob/main/apps/cli/README.md) for your platform and record `cline --version`. A runtime/model upgrade should record its actual versions and rerun a representative scoped task. App-library pins are independent of the agent runtime.

### CLI authentication for an isolated pilot

From the **toolkit root**, prepare private state outside both Git checkouts:

```sh
CLINE_PRIVATE_DIR="$(dirname "$PWD")/cline-private"
CLINE_CONFIG_DIR="$CLINE_PRIVATE_DIR/config"
CLINE_DATA_DIR="$CLINE_CONFIG_DIR/data"
mkdir -p "$CLINE_PRIVATE_DIR"
chmod 700 "$CLINE_PRIVATE_DIR"

cline auth openai-codex --config "$CLINE_CONFIG_DIR" --data-dir "$CLINE_DATA_DIR"
```

Complete the interactive ChatGPT browser authorization yourself. Keep tokens and raw logs in private local state, outside the app's Git root. For another approved provider, use its supported authentication flow instead. No API key belongs in a prompt, screenshot, shared command line or repository.

In the tested CLI, adding a model flag to `auth` selected API-key quick setup and failed. Authenticate first; select the model when starting the task. The [pilot record](../standards/examples/cline-pilot.md) documents this and other version-specific findings.

### Verify guidance loading

Open only the intended app/workspace. Ensure its installed rules and `cjba-k8s-jsonnet` skill are available. Ask Cline to read the app context and relevant toolkit guidance explicitly; inspect its task/tool evidence rather than assuming installation means loading succeeded. The recorded CLI pilot invoked Cline's native skill tool and referenced the installed rules, standard and pinned sources.

The VS Code extension remains an unpiloted surface here. If your team uses it, perform a separate smoke test for rule/skill discovery, provider setup, tool approvals and the same scoped acceptance case. Do not label it tested based only on the CLI result.

## Everyday change workflow

### Start with a read-only inspection

Use this as a first-session prompt:

```text
Read this app's AGENTS.md, installed toolkit rules, application standard and
cjba-k8s-jsonnet skill. Inspect the dependency lock and resolved imports.
Explain the actual render flow, canonical inputs, merge stages, affected
consumers and exact offline checks. Identify missing inputs and known gaps.
Analysis only: do not edit, upgrade dependencies or deploy anything.
Do not expose Secret payloads or literal credential values.
```

Confirm the reported paths and commands before using them for an edit. The app's locked implementation governs signatures. For example, the reference app correctly uses `serviceLevel: 'Basic'` plus a `resources` map even though the bundled snapshot has a different scheduling shape.

### Request one concrete change

Give Cline the intended outcome, affected targets, scope boundaries and expected evidence. Adapt this prompt in the task interface; replace the bracketed descriptions before submitting it:

```text
Use this app's installed infra-team-toolkit to implement [specific outcome]
for [actual targets]. Preserve the existing layout and pinned interfaces.

Identify the canonical input and intended consumers before editing. Keep
unrelated identities, selectors, images and policy unchanged. Explain any
intentional revision-derived name/reference changes.

Render the affected targets, run their documented offline checks and verify
the resource relationships relevant to the change. Report exact commands,
actual results and unexecuted checks. Do not publish raw manifests or secrets.

This task authorizes the scoped code/input change and offline validation.
Follow the app's separate delivery process for any later deployment task.
```

For a shared image, change its canonical role rather than only one workload override. Include API, workers and Jobs that actually exist in that app. The reference app's backend-only override leaves GoodJob unchanged; other apps need their own propagation check. For unsupported helper fields, use appropriate native patches rather than inventing arguments or capability toggles.

### Verify and review

From the **application root**, inspect the actual file diff and run the app-specific commands recorded in `AGENTS.md`. Check the resulting images, Service/Pod selectors, namespaces, names/references, metadata, accounts and storage. Optional-component checks apply only to implemented interfaces. Distinguish intentional Job fingerprint changes from unintended identity changes.

Use existing native constructors, OneHQ helpers and metadata functions. Keep target-specific policy with the app's existing values/profiles. For `std.mergePatch`, arrays replace and `null` deletes; later overrides may not regenerate earlier derivations. Preserve required env entries when replacing arrays and verify the rendered result.

An agent's statement that tests passed is not enough: inspect command results and independently review the source/output differences. A successful render does not establish image contents, external-resource availability or readiness. Toolkit checks do not substitute for app checks. Deployment remains the app's separate procedure.

## Practice with the worked example

For the documented clean reference revision and already-resolved dependencies, run from the **toolkit root**:

```sh
python3 -B scripts/worked-shared-image.py ../agencieshq-e2e-infra --validate-app
```

The [walkthrough](../standards/examples/shared-backend-image.md) pins the reference app/library revisions and explains every layer. It checks canonical tag and digest propagation, a backend-only negative control and fixed execution IDs across service/PR targets. The full app suite runs in a disposable local clone with Git metadata and copied dependencies.

This command probes in-memory inputs. It deliberately requires the documented clean reference revision; do **not** use it as proof that a real edited consumer diff is correct. Review that actual diff and before/after output separately, using the app's checks and the walkthrough's relationship contract.

To repeat the real agent exercise, create a separate local app clone, remove its remote, copy dependencies and complete/commit adoption before the task. Use [templates/cline-shared-image-pilot.md](../templates/cline-shared-image-pilot.md). Its synthetic `toolkit-pilot` image is an offline exercise and must not be deployed.

For a headless CLI task, the following launcher runs from the **toolkit root**. It assumes the sibling `app-infra/` is that disposable, adopted clone and authentication above has completed. Use auto-approval only for this explicitly bounded offline exercise. A separate clone isolates Git changes but is not a filesystem/network sandbox; choose your approved interactive/tool-approval workflow for other work.

```python
from pathlib import Path
import subprocess

app = Path('../app-infra').resolve()
private = Path('../cline-private').resolve()
private.mkdir(mode=0o700, exist_ok=True)
prompt = Path('templates/cline-shared-image-pilot.md').read_text()
command = [
    'cline', '--cwd', str(app),
    '--config', str(private / 'config'),
    '--data-dir', str(private / 'config/data'),
    '--provider', 'openai-codex', '--model', 'gpt-6.1-sol',
    '--thinking', 'medium', '--json', '--auto-approve', 'true',
    '--retries', '2', '--timeout', '600', prompt,
]
with (private / 'events.ndjson').open('w') as output, \
     (private / 'stderr.log').open('w') as errors:
    (private / 'events.ndjson').chmod(0o600)
    (private / 'stderr.log').chmod(0o600)
    result = subprocess.run(command, stdout=output, stderr=errors, timeout=900)
    result.check_returncode()
```

Save that block as a local Python launcher outside the app root and run it with Python from the toolkit root. Use the versions/account chosen for your pilot; the shown pair reproduces the recorded invocation. The prompt is an explicit positional argument because piped stdin was rejected in the recorded CLI JSON run. Raw events may include source/tool output; share a sanitized review, not those raw files.

The [pilot protocol](../standards/examples/cline-pilot.md) and [result](../standards/examples/cline-pilot.results.json) show the expected one-file edit, intended consumers, independent comparison and exceptions. That pilot retained 36 resources per target, left PR output unchanged and passed 107 app tests. Those counts apply to the recorded revision, not every consumer.

## Generate a Kubernetes resource map

From the **toolkit root**, using the app's actual entry point:

```sh
python3 -B scripts/map-kubernetes.py \
  --app ../app-infra \
  --environment environments/example \
  --output generated/kubernetes/example
```

Replace `environments/example` with a real entry point. Open `generated/kubernetes/example/index.html` locally. The output directory must be outside the application checkout. Search, filter, zoom, select a resource for attributes and follow arrows for evidence. Keep all three files together for the HTML download links to work:

- `index.html`: self-contained interactive diagram, with no server/CDN dependency.
- `graph.json`: inventory, attributes and typed relationship evidence.
- `graph.mmd`: Mermaid export for documentation/review.

Add `--infer-env-links` to show possible endpoint/Job links inferred from matching environment conventions. They remain distinct from declared references and selector matches. Unresolved nodes mean absent from the input, not necessarily missing from the cluster. Sync waves are attributes, not dependency edges. Operator children and unknown CRD internals are not automatically expanded.

For rendered JSON from another app, use `--input /path/to/rendered.json`; `--input -` accepts stdin. YAML is not parsed. `--namespace` supplies a fallback when needed. See [coverage and controls](../standards/kubernetes-map.md) before treating the diagram as complete. It describes declarations/heuristics rather than observed traffic, readiness or complete NetworkPolicy behavior.

The mapper omits Secret/ConfigMap payloads, literal env values and commands. Maps still contain infrastructure names, images and topology. Share them using the application's existing data-sharing rules, alongside a sanitized source diff and validation summary.

## Review and share evidence

Use [templates/change-review.md](../templates/change-review.md). A teammate should be able to establish:

| Evidence | Record |
| --- | --- |
| Provenance | Toolkit revision from the manifest, app/library revisions, Cline runtime/provider/model where used |
| Scope | Actual environment/instance, intended behavior and changed input/files |
| Compatibility | Stable identities/selectors and supported interfaces; deliberate migration/name changes |
| Verification | Exact commands, actual results, relationship checks and expected/actual resource differences |
| Limits | Missing tools/inputs, skipped checks, external dependencies and runtime facts not established |
| Recovery | Consumer commit to revert and any separate operational rollback requirements |

Share the guide/templates and reviewed commits rather than the owner's local pilot directory or credentials. Keep raw manifests, resolved Secrets, OAuth/API tokens, kubeconfigs and raw agent logs out of published evidence. Follow the app's review/delivery process; the toolkit does not grant access or perform rollout.

## Upgrade and rollback

For an upgrade, work on a separate consumer branch. Record the current manifest revision and use that **old pinned toolkit checkout** to establish existing managed-file drift. Checking with a newer toolkit HEAD tests the newer expected payload, not the old installation.

1. Select the new owner-reviewed toolkit revision and read its changelog/compatibility notes.
2. Review files listed in the old `.infra-team-toolkit.json`, including any local edits. Preserve/reconcile those edits deliberately.
3. After review, remove only the old managed files listed in that manifest and the old manifest itself so the conservative installer can create replacements. Preserve application-owned `AGENTS.md`, inputs, entry points and other files.
4. Install/check from the clean new toolkit checkout, review the complete diff, update application context if needed, and run the app's checks before committing.

There is no force-overwrite switch. Do not delete entire `.clinerules`, `.cline` or `docs` trees; they may contain unrelated application content. For rollback, revert the consumer adoption/upgrade commit, including its manifest and relevant manual context edits. Selecting an older toolkit checkout alone does not restore installed consumer files. Runtime changes use the application's separate rollback process.

## Troubleshooting

| Symptom | Check/action |
| --- | --- |
| Installer/check refuses a dirty toolkit | Review/commit toolkit changes or use a clean checkout at the desired pin; do not discard work just to make status clean |
| Conflicting destination or symlink refusal | Inspect the reported paths and ownership; preserve/reconcile content using the documented upgrade process, without a force overwrite |
| Installed check fails after changing toolkit branches | Compare with the manifest's installed revision before interpreting this as corruption |
| Agent uses the snapshot's wrong helper shape | Inspect lock/imports/resolved code; read the skill's compatibility reference and preserve the app's implemented API |
| A shared image misses a worker/Job | Trace the canonical role and derivation order; distinguish it from a component-only override |
| `enabled: false` or a Secret/account rename does not propagate | Confirm actual app support; new fields do not implement capabilities, and earlier derivations may keep old references |
| `tk show` exits zero but emits no captured manifests | Confirm real output; headless redirect capture can need `--dangerous-allow-redirect`, with controlled redaction |
| Cline OAuth asks for an API key | On the tested CLI, omit the model flag from `auth openai-codex`; choose the model at task launch |
| CLI JSON mode rejects piped input | Pass the task as an explicit positional argument, as in the launcher above |
| A long validation command hits a tool timeout | Distinguish command limits from the overall task timeout; use the runtime's supported long-running/polling mechanism and obtain the final result |
| Adoption diff flags the supplied source snapshot's whitespace | Verify byte identity/checksum and record the inherited exception; do not silently rewrite the snapshot |
| Map contains unresolved or inferred links | Inspect evidence and external/operator ownership; this is not a runtime discovery or missing-resource verdict |
| Worked example refuses an edited/new app revision | It is a pinned reference probe; use actual consumer checks/diff review, or deliberately update the reference contract |
| Model or account access differs from the pilot | Use the approved setup supported by your account/client and record it; do not substitute an unapproved provider or misreport an unexecuted task |

## Maintaining this guide

Darthcjba maintains the toolkit and guide. When changing installer paths, commands, runtime guidance or accepted behavior, update this guide and the linked detailed procedure/evidence in the same review. Run toolkit checks per [CONTRIBUTING.md](../CONTRIBUTING.md); application behavior still needs representative app validation.

Before broader adoption, assess a second application with a different layout and record a scoped result. Keep future architecture and pipeline work clearly separate from implemented features. See [README.md](../README.md) for current status and the detailed standards for the source contract.
