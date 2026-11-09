# Change review

## Outcome
Describe the requested behavior, actual targets, canonical input, intended consumers
and files changed. Separate guidance adoption from a functional resource change.

## Compatibility
Record app/toolkit/library revisions and the resolved implementation inspected.
List identity, selector, schema or dependency changes and migration requirements.
Explain merge/derivation and hidden-resource behavior relevant to this change.

## Evidence
Record exact commands, actual results and unexecuted checks. Exclude secret values,
raw manifests and private agent logs.

| Evidence | Result for this change |
| --- | --- |
| Guidance | Installed manifest revision; preview/check/audit mode used and its scope |
| Baseline | Existing check failures, duplicate env/selector overlap or other accepted gaps |
| Rendered differences | Intended image/name/gate changes; complete comparison of unrelated fields and targets |
| Relationships | Selectors, namespaces, Secret key/account/volume references and Job gates checked |
| Map, when useful | Artifact location, declared/inferred coverage and unresolved ownership limits |
| Agent, when used | Actual runtime/provider/model, guidance-loading evidence and command outcomes |
| External/runtime checks | What was checked and what remains unverified; separate delivery status |

A manifest audit checks recorded file consistency. Current-revision check compares
trusted selected toolkit content. Neither substitutes for app rendering and checks.

## Rollback
Identify the consumer adoption/change commit to revert, the previous pins and any
separate runtime rollback requirements. Record whether delivery was performed.
