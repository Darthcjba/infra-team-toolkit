# Toolkit review after three application assessments

Reviewed baseline: `733d9a2` on `docs/application-standard`. This review applies the
E2E, HQAdmin and ReadyGOP findings to toolkit usability and maintenance. The owner
has deferred Tekton and constructor-library changes until a later session.
No application source, dependency pin, supplied skill archive or GitHub setting
is changed by this review.

## Findings and completed improvements

| Finding at the reviewed baseline | Implemented change | Practical effect |
| --- | --- | --- |
| README mixed project history with onboarding and did not present a complete first-use sequence | Feature/output table and seven-step README workflow, linked to the detailed team guide | A teammate can prepare, inspect, preview/install, establish context, change, map and maintain an app without the conversation |
| Installation wrote managed files without a review-only preview command | `scripts/install.py APP --dry-run`, using the same complete preflight as install | Inspect planned Create/Keep paths and conflicts before any files are written |
| Checking an older installation required its old clean toolkit checkout | `scripts/install.py APP --verify-installed` | Verify recorded managed-file bytes using the current verifier even if the current toolkit differs or is dirty |
| A manifest-driven audit needs bounded paths and explicit trust limits | Schema/revision/hash validation, managed-path constraints, escape/symlink refusal; documentation distinguishes consistency from authenticity | Old manifest compatibility without reading arbitrary paths or claiming independent trust in a modified manifest |
| Six authored installed-document links pointed to scripts/templates excluded from the payload | Pin those links to the commits that introduced the reviewed case tools/templates | The installed copies no longer contain those missing relative targets; scripts/templates remain toolkit-owned |
| Documentation link health had only ad hoc inspection | Structural checker now validates authored local file links and installed-standard file targets | Future source/consumer link regressions fail an offline check |
| Structural checks used Python asserts, which optimization can disable | Explicit validation failures and a `python -O` rejection test | Required structure checks remain active under optimized Python |
| Validation checkouts could be mistaken for required toolkit/app structure | Document separate checkouts, automatically cleaned reference probe clones and optional retained agent-pilot folders | No full application copy or permanent per-app validation folder is required in the toolkit |
| Multiple apps exposed different merge, hidden-resource and capability behavior | Preserve the responsibility-based standard and app-specific case boundaries; explain expected outcomes and baseline exceptions | Shared conventions remain reusable without imposing E2E/PGSync layout or policy on every consumer |

`--check` keeps its existing meaning: exact comparison against the current clean
toolkit revision. `--verify-installed` checks only entries in the consumer manifest.
It neither authenticates that manifest nor detects arbitrary unlisted content.
Adoption acceptance and trusted source comparison still use `--check` at the
selected toolkit revision. None of these modes validates Kubernetes output.

Pinned remote links need those commits to be published or otherwise made available
to teammates. Offline link checks verify local file targets and package boundaries;
they do not check network availability or heading anchors. The supplied skill
reference archive is preserved and excluded from authored-document link rewriting.

## Optimization decisions

The baseline install payload contained **25 managed files totaling 253,047 bytes**
before its manifest. Skill material contributed 106,171 of those bytes and the
standards/evidence 145,305; rules contributed the rest. This is a measured package
size, not a runtime performance benchmark. No full app repositories, vendors,
generated maps, tests, scripts, private logs or team-guide copy are in that payload.

The highest-value optimization here is a simpler operating path: preview before
adoption, audit without recovering old checkouts, and read the README before the
historical evidence. Splitting a roughly 253 KB payload into multiple installation
profiles would add upgrade/configuration complexity without a demonstrated need.
The reviewed payload boundary remains compatible.

| Candidate | Decision and condition for revisiting |
| --- | --- |
| Share clone/render/hash helpers across the app-specific case scripts | Deferred until the constructor update establishes its source/acceptance contract. Current cases encode deliberately different resource, identity and namespace expectations; preserve their recorded fingerprints/results rather than refactoring them incidentally |
| Cache repeated app renders or clone dependencies less often | No demonstrated bottleneck in this review. If larger cases become slow, measure clone/render time first and cache only immutable baselines keyed by app/input/dependency identity; changed probes must still render independently |
| Install a smaller core-only reference profile | Keep the current payload. Revisit if measured package/context cost becomes material; account for documentation links, manifest schema and old managed-file removal before adding a profile |
| Expand mapper coverage for more CRDs, commands or live traffic | Defer to an actual consumer requirement with source/schema and tests. Current supported declarations, heuristics and unknown-CRD limits stay explicit |
| Automatic replacement/upgrades | Keep deliberate managed-file reconciliation. New preview/audit commands reduce uncertainty without silently overwriting consumer changes |
| CI and release automation | Recommended when the owner publishes/selects the initial release: run the documented offline structure/link and unit checks. No workflow, remote publication or release tag is added by this review |
| New library interfaces or Tekton procedure | Deferred by the owner. Resume with [the library-update procedure](team-guide.md#after-the-constructor-library-changes), then scope pipeline work separately |

## Verification and remaining limits

All 54 tests in the expanded unit suite pass. They exercise preflight without writes, conflicts, installed
drift, missing files, path escapes, malformed manifests, managed/manifest symlinks,
source-independent audit, missing source/installed links, fenced documentation
examples and structural validation under optimized Python. Existing mapper/image
contract tests remain in the same suite.

Read-only checks against the retained pilot/assessment installations exercise
older manifest pins (15 files at `e7824ee`, 17 at `e93dffd`, 21 at `63fae87`)
without changing their managed files. The new installer is
also smoke-tested in a disposable Git consumer: preview leaves it empty, install
and both checks pass, and a simulated edit is detected. No new permanent app
checkout is needed for that test.

Application renders and the historical Cline task are not rerun for these changes:
no constructor guidance, application renderer, mapper or app-specific acceptance
logic changed. The existing case evidence keeps its original pins/limits. New
library behavior needs fresh representative app/agent evidence; historical tests
are not a substitute. Release publication and extension/pipeline/runtime checks
remain outstanding as documented in the [README](../README.md).
