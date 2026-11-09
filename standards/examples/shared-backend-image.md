# Worked example: shared backend image

Status: Step 4 runnable example based on the [inspected reference application](../reference-applications/agencieshq-e2e-infra.md). `scripts/worked-shared-image.py` exercises the acceptance criteria below and produces a report containing only selected public image inputs, resource names and check results. The [recorded results](shared-backend-image.results.json) distinguish example checks from the full application suite. A separate [Cline CLI pilot](cline-pilot.md) records Step 5's actual input edit and independent review.

Other applications should use their actual canonical image input, consumers and commands. API/worker/Job names and the file layout below are specific to `agencieshq-e2e-infra`.

## Reproduce it

From the **toolkit checkout**, with the reference app beside it:

```sh
python3 -B scripts/worked-shared-image.py ../agencieshq-e2e-infra --validate-app
```

Replace the application argument with its actual path if necessary. The installer does not copy toolkit scripts into the consumer, so run this command from the toolkit checkout even when reading an installed copy of this document.

Prerequisites: Git, Python 3.10+, Tanka, the app's existing locked `vendor/` dependencies and Ruby for the full suite. The tool makes no registry, cluster or remote Git requests. On a fresh app checkout, install the app's documented dependencies separately with `jb install`, including access to the private OneHQ library.

The app must be clean at revision `4a494240abc9783c6faf47db6f0f8f05e441dd40`, with OneHQ locked to `10a46abb03c8a82ecc9479b036a74d5b79b00f4f`. The tool stops on another revision rather than silently asserting the same contract for different source. Review/update this example before supporting a newer reference revision or another application.

The command renders both targets with in-memory inputs and then runs `sh scripts/validate.sh` in a disposable local clone of the pinned application commit, with locally resolved dependencies copied in. The clone retains Git metadata required by the app's walkthrough. The application's generated files and fixture Git repositories remain in that clone, which is removed afterward. The original checkout must remain clean. To run only the worked-example checks, omit `--validate-app`; the report then marks the full application suite as unexecuted.

Progress goes to stderr; stdout is a JSON report. For a saved result:

```sh
python3 -B scripts/worked-shared-image.py ../agencieshq-e2e-infra --validate-app > /tmp/shared-backend-image.results.json
```

The report records app/library/toolkit revisions, whether the toolkit has uncommitted changes, the example script's SHA-256, tool versions, each case and the application test count. An uncommitted-toolkit result identifies the script by its checksum; it is not release evidence. Failures exit nonzero and withhold raw render/test output, which may contain credentials. If a failure needs investigation, reproduce the relevant check in an isolated workspace and redact diagnostics before sharing them.

## Scope and baseline

The primary application entry points are `environments/e2e-check/main.jsonnet` and `examples/prs/pr-xxx/main.jsonnet`. Their normal YAML commands, from the app root, are:

```sh
tk show environments/e2e-check
tk show examples/prs/pr-xxx
```

The example uses `tk eval` to keep comparisons structured: it first checks actual main output against the shared renderer with unchanged inputs. It also evaluates the values function to verify effective settings before resource construction. Full settings/manifests, including Secret data, stay in process memory and are never written into the report.

For manual YAML inspection, capture/redact Secret payloads and credential values before saving or sharing evidence. In headless tooling `tk show` requires `--dangerous-allow-redirect`; avoid treating its refusal to print redirected output as a successful manifest check. Record actual output availability as well as exit status.

At this revision each default target renders 36 resources. Their inputs are independent: changing service `images.json` does not update an existing PR snapshot. The example supplies each target's existing config and overrides and replaces only its backend image role in memory. It never edits either `images.json`.

## Intended input and propagation

The shared-change cases replace the selected target's canonical `images.json.backend` role with these synthetic selections:

- **Tag:** retain its repository, set `tag` to `toolkit-step4`, and omit any old digest.
- **Digest with tag:** retain its repository, use `sha256:` followed by 64 lowercase `a` characters, and include `tag: 'ignored-by-digest'` to verify digest precedence.

These references are offline probes, not images selected for deployment. An ordinary implementation of this change would edit the corresponding backend role in the target's existing `images.json`; the example injects the same input through the values function's real `versions` argument.

The adapter creates `repository:tag` or `repository@sha256:...` using the pinned helper's `image + tag` convention. A scoped override under `backend.deployment.cont.app` is a separate case: at this revision GoodJob keeps its original image. It cannot satisfy the shared-change acceptance case.

The actual trace is:

| Layer | Input or implemented behavior |
| --- | --- |
| Target image input | `environments/e2e-check/images.json` or `examples/prs/pr-xxx/images.json`, backend role |
| Environment entry point | `values.jsonnet` normally imports config, images, overrides and execution; the example passes equivalent inputs to the same shared function |
| Adapter | `lib/e2e/images.libsonnet` produces `image: repository + ':'` and `tag`, or `image: repository + '@'` and the digest |
| Component composition | `lib/e2e/values.libsonnet` combines defaults and overrides; backend/GoodJob use the canonical image, then Sidekiq and preparation/seed derive from backend settings |
| Resource construction | `lib/e2e/render.libsonnet` calls native Deployment constructors plus `kone.createDeploy`; `render-job.libsonnet` combines the native Job constructor with `kone.generateJob` |
| Container helper | The pinned `core/Container.libsonnet` uses `config.name` and concatenates `config.image + config.tag` for both regular and init containers |
| Verified output | Effective component settings and final Pod container images match the selected full image reference |

The script calls `tk eval lib/e2e/values.libsonnet` with `--tla-code` inputs, and `tk eval lib/e2e/render.libsonnet --tla-code values=...` with the actual values-function expression. Inspect `render()` in the toolkit script for the complete argument construction. Source anchors and pinned dependency details are in the [reference mapping](../reference-applications/agencieshq-e2e-infra.md).

| Consumer | Required result |
| --- | --- |
| `backend` API app container | Selected backend image |
| `goodjob` app container | Same selected backend image |
| `sidekiq` app container | Same selected backend image |
| `dbprepare` app container | Same selected backend image, retaining prepare command |
| `dbseed` app container | Same selected backend image, retaining seed command |
| Seed `backend-ready` init container | Same selected backend image, retaining readiness command |
| Frontend, search, websocket and Playwright containers | Their existing independent images |
| Database/tool/readiness containers using separate images | Existing images unless explicitly included in scope |

## Identity and relationship acceptance

For default main rendering with empty `execution.json`:

- Deployment, Service, Ingress, namespace, storage and credential identities stay unchanged.
- Deployment selectors and Pod labels stay unchanged; all eight Services still select their intended workloads.
- Prepare and seed Job names change with the backend-image hash. The runner name changes through its seed dependency. Their dependent references and revision-derived labels must follow those names.
- Seed checks the matching preparation Job; the runner checks the matching seed Job.
- Resource count, replicas, scheduling, waves, commands, probes, account/credential references and volume policy remain unchanged. Environment entries also stay unchanged except for image-derived run IDs and Job-name references.
- API/GoodJob/Sidekiq keep the shared tmp claim. Prepare/seed keep private tmp volumes.

The fixed execution-ID case uses `toolkit-step4`: main rendering has 37 resources and four Sync hooks. Changing the image with the same execution ID keeps that execution's Job names; a fresh ID is the supported mechanism for a fresh pipeline run. A completed Job with unchanged identity does not rerun on an unchanged sync.

The checker constructs the permitted image/Job-identity differences, then compares **every field of every resource**, including Secret payloads in memory. It also checks namespace consistency, eight intended Service/workload relationships, completion gates and shared/private tmp ownership. An extra replica, command, credential, metadata, image or volume change fails the example. Revision-derived Job labels, gate references and runner run-ID environment values are permitted only when they match the expected identities.

## Expected and recorded results

Each target has four cases:

| Case | Expected result |
| --- | --- |
| Canonical tag | Five app/Job consumers and seed readiness init use the new image; three Job names change; 36 resources |
| Canonical digest with tag | Same propagation/name changes; digest wins over tag; 36 resources |
| Backend-only negative control | Shared-change check rejects it because GoodJob stays on its baseline image; a narrower expected-difference check confirms that exact behavior |
| Fixed execution ID | Shared image propagates; 37 resources/four hooks; no Job names change for the same ID |

See the [recorded JSON report](shared-backend-image.results.json) for actual Job-name transitions, revisions/checksum, all eight case results and isolated application-suite results. The toolkit unit suite additionally exercises failures for partial worker updates, a stale seed-readiness image, bad selectors/gates, unrelated scaling/Secret changes and empty/failed render output.

The recorded run passes all eight example cases and all 107 application tests. It used Tanka 0.36.3 and Python 3.14.3 with the toolkit's uncommitted working tree identified in the report. Recheck revisions/checksums when reproducing the result; it is not a release or Cline-pilot record.

The optional full-suite stage runs this command in the temporary app copy:

```sh
sh scripts/validate.sh
```

Full-suite results are separate from direct image/relationship probes. Toolkit installer tests do not substitute for application checks. Image availability/content, external credentials, cluster APIs and runtime readiness remain separate checks; offline examples do not prove deployment success.

Step 4 supplies the executable procedure, expected differences and recorded results. The separate Step 5 record pins the toolkit installed in an isolated consumer checkout and compares Cline's actual scoped input edit against this acceptance contract. No deployment is part of either example.
