# Application infrastructure contract

Status: Step 2 convention, informed by inspection of `agencieshq-e2e-infra`. The [reference mapping](reference-applications/agencieshq-e2e-infra.md) records implemented behavior and known limitations. The [shared image worked example](examples/shared-backend-image.md) exercises the change/relationship contract with executable checks and recorded results. A Cline pilot and a second application assessment remain pending.

## Compatibility and adoption

This standard defines responsibilities and rendered behavior. It does not require a directory layout, input schema, new Jsonnet API or library upgrade. Existing applications with different structures remain supported: map their actual files and commands to the responsibilities below. One file may serve several responsibilities, and a responsibility may span several files.

Start from the application's established render flow and known-correct resource baseline. Preserve production identities, selectors, references, workload behavior and delivery procedures. A layout difference alone is not a reason to reorganize a repository. Capture intentional changes separately from output-preserving refactoring; revision-derived Job names may legitimately change with their inputs.

Adoption begins with documentation and reproducible rendering. Record supported operations, unsupported operations and known gaps. A documented gap is not proof that an operation is safe, and a successful default render does not establish that every override works. Restrict a scoped change to supported paths or implement and validate that operation explicitly. Broader adoption requires evidence from another application; the reference app's E2E choices are not universal defaults.

Read repository `AGENTS.md` instructions and linked architecture documentation explicitly. Do not assume another agent loads `.clinerules/` or `.cline/skills/`. The application's dependency lock and resolved implementation govern constructor signatures; bundled guidance is supplementary. Do not copy a different scheduling interface from a skill snapshot into a pinned consumer.

## Responsibility boundaries

| Boundary | Responsibility | Placement in an existing application |
| --- | --- | --- |
| Shared library | Generic constructors, resource patches and reusable mechanisms | Pinned dependency and existing import shims |
| Defaults | Reusable component settings, default budgets and common environment settings | Existing values, base files or component modules |
| Environment inputs | Images, namespaces, endpoints, placement and integration choices | Existing environment values, profiles, overlays or external inputs |
| Application composition | Component graph, supported capabilities and dependency derivation | Existing composition functions, imports or entry point |
| Renderer | Native constructors, OneHQ helpers, metadata and unsupported native fields | Existing render functions or resource declarations |
| Scripts | Workload commands, local tooling and delivery operations with explicit purposes | Existing embedded scripts and tool directories |
| Validation | Input checks, rendered relationships and expected differences | Existing tests/checks and documented commands |

Use these boundaries when adding or changing code. Extract a shared mechanism only when its behavior is understood and reusable; keep application composition and environment policy in the consumer. Existing combined files can retain their layout when a scoped change is clearer there.

## Consumer record

Document the following in the application's `AGENTS.md` or linked architecture notes. Use actual paths and commands, completing `templates/AGENTS.md` from the toolkit checkout before adoption. The installer does not copy that template automatically.

| Record | Required information |
| --- | --- |
| Ownership and baseline | Application owner, inspected app/toolkit revisions, baseline target and evidence limits |
| File map | Existing files responsible for the boundaries above; supported variations and exceptions |
| Entry points | Actual Tanka environments, additional Jsonnet entry points, profiles and instance selection |
| Source authority | Dependency locks, resolved import paths, relevant helper signatures and tool prerequisites |
| Inputs and merging | Defaults, environment overrides, external variables, precedence and array/null behavior |
| Components | Resource graph, shared image consumers, optional components and unsupported capabilities |
| Identity and references | Names, selectors, namespaces, container identities and generated/external dependencies |
| Policy | Resource/Pod metadata, scheduling, probes, storage, accounts and workload-specific native patches |
| Scripts and delivery | What renders, generates files, builds, applies, syncs or otherwise changes external state |
| Verification | Exact offline commands, expected changes, relationship checks and runtime prerequisites |

## Inputs, defaults and merge semantics

Keep shared defaults reusable and put target-specific choices in the application's existing inputs. Identify the canonical input for each shared value, including an image consumed by several components. Describe a component-local override separately from a shared update.

Document the actual merge stages and when derived values are evaluated. Do not assume later overrides regenerate earlier references. For each supported shared change, establish whether downstream consumers inherit it, override it intentionally or require coordinated changes.

No merge operator is mandated. When the app uses `std.mergePatch`, document that objects merge recursively, arrays replace and `null` deletes fields. Object `+`, field `+:`, `self` and `super` have different inheritance behavior; describe the parts that affect the consumer. Preserve required environment entries when replacing arrays, avoiding duplicate variable names. Use an existing merge-by-name mechanism where available; do not invent a helper that the app has not implemented.

Inputs unsupported by the pinned library need native patches or explicit rejection. Document unsupported fields that are silently ignored today. Adding `enabled`, `existingServiceAccount` or a policy object does not implement those capabilities.

## Composition, identity and capabilities

List emitted resources and their dependencies, including workers, preparation Jobs, storage, Services, credentials and accounts. State which components always exist and which can be disabled through a supported interface. Do not introduce toggles merely to satisfy the standard.

Preserve stable identities and selectors for unrelated changes. When identity changes are supported, propagate names and namespaces through workload references, Services, Ingresses, bindings, credentials, storage and completion gates. Classify dependencies as app-created, operator-generated or externally supplied; offline validation must account for that ownership instead of requiring every reference to appear as a rendered object.

Check helper behavior tied to names, including scheduling substring matches and debug handling. A syntactically valid name can still change labels, replica counts or placement. Use the rendered result to establish that Services select the intended Pods.

For new or deliberately refactored derivation logic, resolve supported effective identity/runtime inputs before constructing their dependents. Existing applications can retain their composition stages while documenting safe change paths and gaps. Introducing a general preparation layer requires its own implementation and compatibility checks.

## Resource construction, metadata and workload policy

Inspect the pinned implementation and reuse native constructors plus OneHQ patches where supported. Verify whether a helper returns a patch, complete object or array. Keep OneHQ container inputs in their implemented shape; the container collection key and the rendered `config.name` are distinct. Check the library's actual image concatenation and environment-key alias behavior.

Patch unsupported Kubernetes fields at their native paths. Do not assume an extra input field reaches the output. Apply container policy to the intended app container, preserving distinct init-container and sidecar behavior. Keep Job-specific restart, retry, deadline, probe and retention choices explicit rather than copying an entire Deployment policy blindly.

Reuse existing metadata helpers for Vault paths and sync waves. Keep policy values with their current component/profile owner and distinguish resource metadata from Pod-template metadata. Optional arguments must remain absent when omitted, numeric wave zero must survive as `"0"`, and annotation override precedence must be documented. Application-specific wave numbers remain configurable.

ServiceAccount creation and use are separate concerns when the app supports reuse of an existing account. Do not generate an account just because a workload references it. Otherwise record that reuse is unsupported until implemented. Apply the same ownership discipline to Secrets and storage. Never include secret payloads or resolved credential values in review evidence; base64 is not encryption.

## Scripts, rendering and delivery

Distinguish scripts embedded in workloads, local render/check tools, file generators and delivery coordinators. Record required interpreter/image support and external inputs. Reuse established scripts rather than embedding divergent copies of the same command in several resource declarations.

Document an exact render command for each supported entry point, its working directory, dependencies, external variables and expected output. Separate UI build-time configuration from runtime environment values where the app requires it. A successful render does not verify image contents or external-resource availability.

Rendering and validation must not deploy. Describe delivery procedures separately, including coordination, ordering, reset requirements and retention where applicable. Argo sync waves do not by themselves stop existing consumers or provide an exclusive lock. This application standard does not define a Tekton procedure.

## Validation and change evidence

Before a change, capture the affected targets and a sanitized baseline with the existing commands. For a scoped change, declare expected differences and compare resources by kind, namespace and name, allowing documented revision-derived identities. Check relationships as well as successful evaluation:

- Intended image consumers receive the selected image; unrelated consumers retain theirs.
- Namespaces, selectors, Pod labels, Ingress backends and referenced ports agree.
- Secret keys, ConfigMaps, accounts/RBAC and volumes match their app-created or declared external owners.
- Supported optional components leave no orphaned dependents when disabled.
- Resource and Pod metadata, placement and container policy reach the intended targets.
- Job identities, ordering and completion gates agree; retries and retention remain intentional.

Run existing checks appropriate to the change. Report commands, results and skipped/blocked checks accurately. Keep generated raw manifests and resolved Secrets out of published evidence. Separate offline relationships from cluster schema/API support, registry/image verification, external-resource existence and runtime readiness. Toolkit structural/installer tests do not prove application correctness.

Known unsupported operations are useful negative cases for later work, not capabilities the standard claims to provide. Scope acceptance cases to components present in that application; an app without a worker or HPA need not gain one.

## Proposed architecture and later acceptance cases

The conceptual sequence is: merge inputs, resolve supported capabilities/identity/runtime, inspect effective settings, render and validate relationships. Functions such as `prepareComponents` and `validatePrepared` are proposals until a consumer implements them. No new module name, directory or public API is required by this document.

If a future change introduces that layer, preserve existing entry points through a compatibility adapter and compare baseline output before migrating consumers. Acceptance cases include disabled workers removing dependent HPAs where present; reused accounts retaining Pod references without account creation; renamed app containers receiving policy without changing sidecars; and matching Service selectors. These cases require implementation evidence for each claimed capability.

Skill alignment (Step 3) and the worked change (Step 4) apply this contract. A Cline pilot (Step 5) and a separate pipeline procedure (Step 6) remain later steps. Documentation alone does not establish a successful consumer pilot or production rollout.
