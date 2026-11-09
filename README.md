# infra-team-toolkit

Shared working conventions for infrastructure projects using Cline, Tanka and Jsonnet. Owner and sole maintainer: **@Darthcjba**. Development toolkit; one scoped Cline CLI pilot and a second application's offline compatibility assessment have passed. Release review remains pending.

**Start here:** the [team guide](docs/team-guide.md) covers prerequisites, application onboarding, Cline setup, daily changes, worked examples, resource maps, review evidence, upgrades and troubleshooting. Share it from a reviewed toolkit checkout; teammates do not need the project conversation.

## Responsibilities

| Location | Owns | Current owner |
| --- | --- | --- |
| `rules/` | Short cross-project instructions | @Darthcjba |
| `skills/` | Jsonnet guidance and future domain procedures | @Darthcjba |
| `standards/` | Application boundaries, examples and migration targets | @Darthcjba |
| `templates/` | Consumer documentation starting points | @Darthcjba |
| `scripts/` | Installation and setup checks | @Darthcjba |
| `docs/` | Team onboarding and usage guide | @Darthcjba |
| `README.md` | Setup, usage, ownership and upgrades | @Darthcjba |

See [governance](GOVERNANCE.md), [contributing](CONTRIBUTING.md), and [CODEOWNERS](.github/CODEOWNERS). GitHub permissions are configured separately; these files do not change access or visibility.

## Application standard and compatibility

The [application contract](standards/app-infrastructure.md) defines responsibilities and validation expectations while preserving existing consumer layouts and pinned APIs. Map the application's actual files to those responsibilities; working production resources do not need a directory migration to adopt the toolkit.

The [reference mapping](standards/reference-applications/agencieshq-e2e-infra.md) distinguishes observed behavior from gaps. Step 1 inspection and Step 2 standard definition are documented. The [Jsonnet skill](skills/cjba-k8s-jsonnet/SKILL.md) follows the standard with explicit pinned-source precedence and revision-specific constructor guidance (Step 3). Its bundled library-source snapshot and supplied constructor guide remain unchanged. The [shared image worked example](standards/examples/shared-backend-image.md) provides executable checks, expected differences and recorded results (Step 4). The [Cline CLI pilot](standards/examples/cline-pilot.md) records the installed toolkit pin, one-file change and independent acceptance review (Step 5). The [HQAdmin assessment](standards/examples/hqadmin-validation.md) validates a second layout with a different OneHQ revision, unchanged production output and explicit dependency/selector/external-resource gaps. It is offline evidence; Cline was not run on that app. The separate pipeline procedure (Step 6) remains pending.

Run the example from this checkout against the documented clean reference revision with its locked dependencies available:

```bash
python3 -B scripts/worked-shared-image.py /path/to/agencieshq-e2e-infra --validate-app
```

It compares synthetic image changes in memory and runs the optional application suite in a temporary copy. It does not edit or deploy the reference application. This is a reference-specific acceptance test; other applications retain their own paths, inputs and supported capabilities.

## Explore rendered resources

The [Kubernetes map](standards/kubernetes-map.md) generates an interactive offline diagram with resource attributes and typed connections, plus JSON and Mermaid exports. It accepts existing rendered JSON or renders a selected Tanka entry point. Optional environment-derived links are marked as inferred, and Secret payloads/literal environment values are omitted.

```bash
python3 -B scripts/map-kubernetes.py --app /path/to/app-infra \
  --environment environments/example --output generated/kubernetes/example
```

Open `generated/kubernetes/example/index.html`. The output stays outside the application checkout; no cluster connection or deployment is performed.

## Install in one application

Prerequisites: Git, Python 3.9+, a clean committed toolkit checkout and an existing application Git working tree. Use a reviewed toolkit commit or release. Replace the example path below.

```bash
python3 scripts/check.py
python3 scripts/install.py /absolute/path/to/app-infra
python3 scripts/install.py /absolute/path/to/app-infra --check
```

The installer creates `.clinerules/infra-team-toolkit-*.md`, `.cline/skills/cjba-k8s-jsonnet/`, `docs/infra-team-toolkit/standards/`, and `.infra-team-toolkit.json`. Conflicting existing content is left untouched. Review and commit these files in the application repository.

Manually merge [templates/AGENTS.md](templates/AGENTS.md) into the application's existing guidance, filling every placeholder with actual paths and commands. Install the app's documented Tanka/Jsonnet dependencies separately. No versions are guessed here.

## Use with Cline

Open the app as a single-folder workspace. Configure your approved model provider with your own credentials. Enable the installed rules and Jsonnet skill in Cline. Start by asking it to identify the pinned library revision, explain the render flow and list the exact validation command without editing. Then try one scoped change and inspect the rendered differences.

For a CLI pilot, use a separate checkout and pinned runtime, keep authentication/logs outside the repository, and use [the recorded protocol](standards/examples/cline-pilot.md) with [the task template](templates/cline-shared-image-pilot.md). CLI validation does not establish that the VS Code extension has been piloted.

[Cline rules](https://docs.cline.bot/customization/cline-rules) and [skills](https://docs.cline.bot/customization/skills) describe discovery. Toolkit guidance supplements the actual app source; it does not implement the proposed architecture automatically.

## Validate and release

```bash
python3 scripts/check.py
python3 -m unittest discover -s tests -v
git diff --check
```

The owner reviews changes, updates CHANGELOG.md, merges, and tags a release when ready. Two application layouts have scoped evidence; review their recorded limits and establish each consumer's baseline before broader adoption. Toolkit tests do not validate Kubernetes manifests or production readiness.

## Upgrade and rollback

Pin a reviewed toolkit revision. Run check mode to find drift. Follow [scripts/README.md](scripts/README.md) for deliberate replacement of managed files; preserve application-owned files. Review and commit the resulting consumer diff. Roll back by reverting the consumer adoption commit, including its manifest. Runtime changes require the app's own rollback process.

## Scope

The OneHQ constructor library remains a separate dependency. This repository ships reusable guidance and tooling. Pipelines and other platform domains can grow as separate skills without forcing app schemas onto every task.
