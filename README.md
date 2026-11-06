# infra-team-toolkit

Shared working conventions for infrastructure projects using Cline, Tanka and Jsonnet. Owner and sole maintainer: **@Darthcjba**. Initial scaffold; not yet a released or application-validated toolkit.

## Responsibilities

| Location | Owns | Current owner |
| --- | --- | --- |
| `rules/` | Short cross-project instructions | @Darthcjba |
| `skills/` | Jsonnet guidance and future domain procedures | @Darthcjba |
| `standards/` | Application boundaries, examples and migration targets | @Darthcjba |
| `templates/` | Consumer documentation starting points | @Darthcjba |
| `scripts/` | Installation and setup checks | @Darthcjba |
| `README.md` | Setup, usage, ownership and upgrades | @Darthcjba |

See [governance](GOVERNANCE.md), [contributing](CONTRIBUTING.md), and [CODEOWNERS](.github/CODEOWNERS). GitHub permissions are configured separately; these files do not change access or visibility.

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

[Cline rules](https://docs.cline.bot/customization/cline-rules) and [skills](https://docs.cline.bot/customization/skills) describe discovery. Toolkit guidance supplements the actual app source; it does not implement the proposed architecture automatically.

## Validate and release

```bash
python3 scripts/check.py
python3 -m unittest discover -s tests -v
git diff --check
```

The owner reviews changes, updates CHANGELOG.md, merges, and tags a release when ready. Start with one app and one reproducible change; test a second app before broader adoption. Toolkit tests do not validate Kubernetes manifests or production readiness.

## Upgrade and rollback

Pin a reviewed toolkit revision. Run check mode to find drift. Follow [scripts/README.md](scripts/README.md) for deliberate replacement of managed files; preserve application-owned files. Review and commit the resulting consumer diff. Roll back by reverting the consumer adoption commit, including its manifest. Runtime changes require the app's own rollback process.

## Scope

The OneHQ constructor library remains a separate dependency. This repository ships reusable guidance and tooling. Pipelines and other platform domains can grow as separate skills without forcing app schemas onto every task.
