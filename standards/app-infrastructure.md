# Application infrastructure contract

Status: initial toolkit convention. Existing application schemas remain authoritative. This document does not introduce a new constructor API.

| Boundary | Responsibility |
| --- | --- |
| Shared library | Generic resource helpers and reusable mechanisms |
| Application composition | Components, dependencies and supported capabilities |
| Environment values/profiles | Images, namespaces, domains, placement and integration choices |
| Renderer | Native constructors, library patches and cross-cutting metadata |
| Validation | Rendered identity, references and behavior checks |

Each consumer must document its actual paths, merge semantics, supported profiles, pinned dependencies and exact render commands in AGENTS.md or linked architecture documentation. Keep templates with unresolved placeholders out of executable setup.

## Worked change: shared image

Locate the existing canonical image input. Change it there, then render the affected profiles with the repository's documented command. Verify all intended consumers (such as backend, worker and preparation Job) receive the new image, and selectors/names remain unchanged. A backend-only override is a different change and must not be described as updating every consumer.

## Worked change: metadata

Reuse an existing annotation helper for Vault paths and Argo CD sync waves. Supply policy values from the application profile. Check wave zero is retained as the string `0`, omitted values stay absent, and resource metadata is not confused with pod-template metadata.

## Migration target, not implemented API

The research proposes merge inputs, resolve capabilities/identity/runtime, inspect prepared values, then render and check relationships. Implement and test those boundaries behind a compatibility adapter before changing consumers. Functions such as prepareComponents and validatePrepared are conceptual until the app provides them.

## Acceptance cases

Disabled workers remove dependent HPAs; existing ServiceAccounts retain pod references without creating accounts; renamed app containers still receive policy without touching sidecars; Service selectors match pod labels. Check external dependencies separately from offline relationships.
