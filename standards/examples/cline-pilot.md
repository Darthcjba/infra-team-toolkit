# Cline pilot: shared backend image

Status: **passed for this scoped CLI task**, recorded on 2026-11-09. See the [sanitized result](cline-pilot.results.json) and the reusable prompt at `templates/cline-shared-image-pilot.md` in the toolkit checkout. This is one application/input-change pilot; a release, a second application and a separate pipeline procedure remain later work.

## Pinned setup

| Item | Recorded value |
| --- | --- |
| Installed toolkit | `e7824eecc7fe615da1c5ea4e8625a8261a14c03f` |
| Application source | `4a494240abc9783c6faf47db6f0f8f05e441dd40` |
| Isolated adoption commit | `b855b60a088f3f9bd4f954109d0132bc70c955a7` |
| OneHQ library | `10a46abb03c8a82ecc9479b036a74d5b79b00f4f` |
| Cline CLI | `3.0.74`, then-current stable npm version; platform package and binary checksum in the result |
| Provider/sign-in | `openai-codex`, official ChatGPT OAuth; credentials excluded |
| Requested model/effort | `gpt-6.1-sol`, medium; passed explicitly to Cline, which completed successfully |

The toolkit was reviewed, checked and committed before installation. A local clone of the reference app received copied locked dependencies, 15 managed toolkit files and a completed app-specific `AGENTS.md`. The clone's remote was removed. The installer and its check mode verified the pinned payload, then adoption files were committed locally before the task. The original application checkout was unchanged throughout.

The supplied library snapshot and constructor guide remained byte-for-byte unchanged. The full adoption diff reports whitespace already present in that snapshot; this is recorded as an inherited exception rather than silently reformatting the snapshot. The later one-file task diff passed its whitespace check.

## Task and observed behavior

The task asked Cline to update the persistent service's shared backend image to the synthetic offline reference `docker.io/onehq/agencieshq:toolkit-pilot`, preserving independent PR inputs and unrelated resources. It required explicit guidance/source inspection, the pinned constructor interface, shared-consumer checks, actual offline validation, accurate reporting and no deployment, push, dependency migration or delegation.

Cline invoked the native `skills` tool for `cjba-k8s-jsonnet`. Its tool inputs referenced `AGENTS.md`, all three installed rules, the application standard, the lockfile, composition source and resolved OneHQ library. It used one agent and produced exactly this source change:

```diff
--- a/environments/e2e-check/images.json
+++ b/environments/e2e-check/images.json
@@
-    "tag": "5.11.1"
+    "tag": "toolkit-pilot"
```

The task change is left uncommitted in the isolated clone for review. No production image pin was changed in the original repository. This sample image was not checked in a registry and must not be deployed.

## Independent acceptance review

The review used the worked example's actual values/renderer functions and full-resource difference contract, not just Cline's conclusion:

- Only the canonical service image file changed; other image roles and the installed guidance/checksums stayed intact.
- API, GoodJob, Sidekiq, prepare, seed and the seed's backend-readiness init received the selected image.
- The service retained 36 resources and all eight intended Service/workload matches.
- Stable identities, namespaces, metadata, resource budgets, probes, credentials/account references and storage policy remained unchanged.
- Prepare, seed and runner names changed as expected; their labels, completion gates and runner run-ID values followed.
- The PR example retained 36 resources and its complete rendered output matched the original baseline.
- Cline tool-output evidence showed **107 application tests passed**, with the test count and `OK` marker in a successful command result. The task process exited zero after approximately 276 seconds.

Raw resource objects, including Secrets, were compared in memory and were not included in the public result. Raw agent/tool logs and authentication state remain private. The result records structured observations and exceptions; it does not reproduce arbitrary model/tool output.

## Reproduce the protocol

1. Choose a reviewed toolkit commit and a separate local reference-app clone at the recorded source revision. Copy its already-resolved `vendor/` dependencies and remove the clone's remote. Keep authentication state and logs outside the app Git root.
2. From the clean toolkit checkout at the chosen pin, run `python3 scripts/install.py /path/to/pilot-app`, then the same command with `--check`. Complete/merge `templates/AGENTS.md` using actual paths and commands. Commit the adoption baseline locally.
3. Install/pin the intended Cline version using its [official CLI instructions](https://github.com/cline/cline/blob/main/apps/cli/README.md). Authenticate using `cline auth openai-codex` with explicit isolated `--config` and `--data-dir` paths. Complete the interactive browser authorization; do not put tokens or keys in the prompt or repository.
4. Confirm model access for the chosen account/client. The recorded model follows the [official OpenAI model guidance](https://learn.chatgpt.com/docs/models?surface=cli); availability can differ by account and client. Re-resolve and record versions for a new pilot rather than floating silently to “latest”.
5. Give Cline the reusable task as an **explicit positional prompt argument**, using the isolated app as `--cwd`. The recorded run used `--provider openai-codex --model gpt-6.1-sol --thinking medium --json --auto-approve true --retries 2 --timeout 600`, with isolated state. The task authorizes only the scoped offline change. Capture raw stdout/stderr privately, not as published artifacts.
6. Inspect the actual Git diff, render both service/PR entry points and independently apply the [shared image acceptance checks](shared-backend-image.md). Verify managed-file hashes against the installed manifest's pin. Check the agent's test results against tool evidence and record skipped/failed checks accurately.

Do not use `scripts/worked-shared-image.py` as a substitute for reviewing Cline's real edit: that script's synthetic-input probes can pass without inspecting a consumer change, and it deliberately requires a clean reference revision. Use its `verify_change`/relationship contract or an equivalent independent comparison on before/after outputs. Verification against a later toolkit HEAD is also different from verifying the manifest's installed revision.

## Operational findings and limits

- On CLI 3.0.74, passing a model flag to `auth` selected API-key quick setup and failed. OAuth succeeded with `auth openai-codex` alone; select the model when starting the task.
- This run rejected piped stdin in JSON mode despite the broader CLI documentation describing piping. Passing the prompt explicitly worked.
- One command-layer invocation timed out after 30 seconds. Cline recovered and obtained the successful full-suite result; the process-level 600-second timeout is distinct from individual command limits.
- The runtime/model choice belongs to this pilot. It does not change the toolkit's consumer library requirements or model policy for other applications.
- This validates one CLI tag update. VS Code extension behavior, registry/image contents, external cluster dependencies, runtime readiness and other app layouts were not tested here. Do not generalize “passed” into production readiness or broad adoption.

The next adoption check should use a second application with a different layout and a similarly scoped change. Additional domains, including Tekton, need their own real source example and acceptance contract.
