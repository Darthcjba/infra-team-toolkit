# Scripts

Requires Python 3.9+ and Git. No third-party Python packages.

For application setup and the full workflow around these commands, read the [team guide](../docs/team-guide.md). Scripts run from the toolkit checkout; the installer does not copy them into consumers.

- `python3 scripts/check.py`: check required content, owner/skill metadata and authored local file links in source and installed standards. Checks remain active under Python `-O`. Fenced examples, immutable skill-reference archive, heading fragments and external URL availability are outside the file-link check.
- `python3 scripts/install.py /path/to/app --dry-run`: preflight the current clean committed payload, report conflicts/symlinks and list Create/Keep paths without writing.
- `python3 scripts/install.py /path/to/app`: copy rules, skills and standards into a Git consumer and write a checksum manifest. Requires a clean, committed toolkit checkout. Refuses differing destination files and symlink destinations before writing.
- `python3 scripts/install.py /path/to/app --check`: compare an installed consumer against this toolkit checkout. Does not write.
- `python3 scripts/install.py /path/to/app --verify-installed`: audit the consumer's recorded revision/file hashes independently of this checkout's HEAD or cleanliness. Works with historical manifests. Rejects invalid managed paths/checksums and manifest/managed symlinks. Checks listed bytes only, not manifest authenticity, unlisted content, dependencies or app/runtime correctness.
- `python3 scripts/worked-shared-image.py /path/to/agencieshq-e2e-infra`: run the Step 4 shared-image example against the clean documented reference revision using in-memory inputs; print a report without raw manifests. Requires Tanka and the app's locked dependencies. Add `--validate-app` to run the full offline app suite in a disposable local clone with copied dependencies (Python 3.10+ and Ruby required). See [the walkthrough](../standards/examples/shared-backend-image.md) for the exact revision, synthetic inputs and expected results. This script is reference-specific and is not installed into consumers.
- `python3 scripts/validate-hqadmin.py /path/to/isolated-hqadmin`: run the [second-application assessment](../standards/examples/hqadmin-validation.md) against its recorded app revision and dependency lock/vendor. Checks an actual staging image edit in a temporary clone, exact rendered differences, unchanged production output, relationships and shell syntax. Reports the existing formatting failure separately; no external lookups or Cline invocation. It does not install guidance, fetch dependencies or modify the supplied app. This is another app-specific acceptance case, not a generic validator.
- `python3 scripts/validate-readygop.py /path/to/isolated-readygop`: run the [third-application assessment](../standards/examples/readygop-validation.md) against its recorded app revision and local dependency baseline. Separately probes Rails/PGSync roles in both targets, complete rendered differences, visibility, gates and ignored/partial disable controls. Records baseline duplicate env/formatting and shell syntax separately. No dependency fetch, deployment, workload execution, Cline task or edit to the supplied app; this acceptance case is also app-specific.
- `python3 scripts/map-kubernetes.py --app /path/to/app --environment environments/example --output generated/kubernetes/example`: render and map resource identities, allowlisted attributes and supported references to HTML/JSON/Mermaid. Or use `--input rendered.json` for existing JSON. Add `--infer-env-links` for explicitly inferred endpoint/Job links. See [coverage and controls](../standards/kubernetes-map.md). Uses the standard library and a bundled HTML template; scripts/templates are not installed into consumers.

Installation does not edit AGENTS.md, install binaries, fetch dependencies, authenticate Cline or modify GitHub permissions. Templates are copied manually after review.

Choose one installer mode per command. Preview/install/`--check` require a clean
committed toolkit. `--verify-installed` needs only the installed manifest and a Git
consumer root; it neither fetches the old revision nor writes files.

For an upgrade, first use `--verify-installed` on a separate consumer branch and
review any local managed-file changes. For trusted historical payload comparison,
also use the old selected toolkit pin's `--check`. Remove only the reviewed old
managed files/manifest, preserving app-owned content; preview/install/check from the
new reviewed pin and inspect the full diff. Follow [the team procedure](../docs/team-guide.md#upgrade-and-rollback).
There is no force-overwrite mode or automatic upgrade/removal. Current-revision
check verifies this checkout's expected files; old manifest entries account for
files retired by a newer release.
