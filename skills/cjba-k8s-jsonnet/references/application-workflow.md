# Application workflow

Use for repository analysis, modifications and refactoring. A standalone constructor explanation needs only the relevant implementation/examples. Preserve the task's scope: inspecting or rendering an app does not imply changing it, installing toolkit files or deploying resources.

## Establish the consumer context

Read the repository's `AGENTS.md`, linked architecture notes, dependency locks and existing render instructions. Locate the toolkit standard from the consumer root at `docs/infra-team-toolkit/standards/app-infrastructure.md`, or from a toolkit checkout at `standards/app-infrastructure.md`. Resolve these paths from the appropriate root, not relative to the skill reference directory.

If the standard is unavailable, follow the app's guidance and use this summary. Different layouts are supported, and one file can own several responsibilities:

| Responsibility | Find in the actual app |
| --- | --- |
| Shared mechanisms | Pinned native/OneHQ constructors and import shims |
| Defaults | Common component settings, resources and environment values |
| Target choices | Environment/profile/overlay inputs for identity, images, placement and integrations |
| Composition | Component graph, shared consumers, derivations and supported capabilities |
| Rendering | Resource construction, metadata helpers and native patches |
| Scripts | Embedded workload commands, local checks/generators and separate delivery tools |
| Validation | Exact commands, expected differences and rendered relationship checks |

Record actual entry points, instance selection, external variables and available tools. Identify scripts that write files or change external state before invoking them. A working layout does not require migration to the reference app's directories. Follow existing merge conventions; do not introduce a new schema or library upgrade to satisfy the standard.

## Trace the requested change

Locate its canonical input and list the consumers intended to change. Distinguish a shared image update from a single component's override. Trace imports/functions and the real evaluation stages through settings into rendered resources; a later override may not regenerate an earlier derived value.

For `std.mergePatch`, objects merge recursively, arrays replace and `null` deletes. Object `+` and fields using `+:`, `self` or `super` have different inheritance behavior. Inspect the app's existing array/env update mechanism before replacing entries; preserve required names without duplicates. Do not assume merge-by-name support.

For an identity/Secret/account/storage change, trace references as well as declarations. Distinguish app-created resources, operator-generated resources and external dependencies. A name change can require coordinated edits when the current app does not derive all references from one input. Do not advertise that operation as supported until the rendered relationships establish it.

Capabilities are application-specific. An ignored `enabled: false` field does not disable a component, and deleting a settings object with `null` may simply break rendering. Apply optional-component and dependent-HPA checks only when those resources and an implemented interface exist. Proposed `prepareComponents`, `validatePrepared` and account-reuse inputs remain proposals unless found in source.

The reference app illustrates these distinctions: canonical backend image selection reaches API, GoodJob, Sidekiq, prepare and seed; a backend-only image override leaves GoodJob unchanged. Its broader mapping is available at `docs/infra-team-toolkit/standards/reference-applications/agencieshq-e2e-infra.md` after toolkit installation, or `standards/reference-applications/agencieshq-e2e-infra.md` in the toolkit checkout. Recheck the actual app revision rather than generalizing its behavior to every consumer.

## Place the implementation

Use existing input/profile locations for target choices, existing component modules for dependencies and existing renderer/native patches for unsupported fields. Verify helper signatures and return shapes against the locked implementation before borrowing an example. Read [library-compatibility.md](library-compatibility.md) if its interface differs from the bundled snapshot.

Reuse annotation helpers and preserve their override precedence. Keep resource metadata separate from Pod-template metadata; retain wave zero and omit absent optional inputs. Keep wave numbers with the app's policy owner. Workload patches must target the intended container by its effective identity, preserving sidecars and init-container behavior. Jobs need their own probe/restart/deadline/retention policy.

Preserve stable names and selectors unless the requested change includes migration. Check helper name matching for scheduling/debug behavior. When Job names intentionally fingerprint images or execution IDs, compare against that contract rather than requiring every resource name to stay fixed.

## Render and verify

Use the app's documented commands for the affected targets. Capture a baseline and declare expected changes. If the task is read-only, keep probes in memory or an authorized isolated workspace; do not invoke generators that write into the consumer. Do not run delivery coordinators as validation.

Verify relationships from actual output:

- Intended shared consumers receive the image; unrelated images remain unchanged.
- Services select intended Pod labels, including after helper-applied label changes.
- Namespaces, Ingress backends/ports, volume references and Job completion gates agree.
- Secret keys and account/RBAC references agree with declared app/operator/external ownership.
- Metadata, placement and container policy appear at their correct native paths.
- Supported disabled components leave no orphaned dependents.

For `tk show`, confirm real manifest output. Headless capture can require `--dangerous-allow-redirect`; raw manifests must stay out of published evidence when they contain Secret payloads. Use the app's redaction mechanism or summarize captured output without exposing credential values.

Run existing checks appropriate to the change and report exact commands, results and validation limits. Offline rendering does not prove cluster schema compatibility, external-resource existence, image contents or runtime readiness. Report missing tools/inputs accurately; do not replace unexecuted checks with claims of success.

Return findings for analysis tasks, or the scoped change with source locations and expected/actual differences for implementation tasks. Keep future architecture and unsupported operations separate from implemented behavior. Deployment follows the application's delivery process and the user's authorized scope; sync waves alone neither stop existing consumers nor provide an exclusive lock.
